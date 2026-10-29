import hashlib
import hmac
import random
import re
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .exceptions import QuizError
from .models import Category, Choice, QuizSession, SessionQuestion

NAME_RE = re.compile(r"^[\w .\-]+$")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(session: QuizSession, token: str | None) -> bool:
    return bool(token) and hmac.compare_digest(session.token_hash, _hash(token))


def _version_tuple(v: str) -> tuple:
    return tuple(int(p) for p in re.findall(r"\d+", v or "")[:3])


def check_app_version(client_type: str, app_version: str | None):
    """Mobil istemcilerde minimum sürüm altındaki uygulamaları güncellemeye yönlendirir (HTTP 426)."""
    if client_type not in ("ios", "android") or not app_version:
        return
    if _version_tuple(app_version) < _version_tuple(settings.QUIZ_MIN_APP_VERSION):
        raise QuizError("upgrade_required", "Lütfen uygulamayı güncelleyin.", 426)


def calculate_points(is_correct: bool, elapsed_ms: int) -> int:
    if not is_correct:
        return 0
    limit = settings.QUIZ_TIME_LIMIT_MS
    elapsed = max(0, min(elapsed_ms, limit))
    bonus = settings.QUIZ_MAX_SPEED_BONUS * (limit - elapsed) / limit
    return settings.QUIZ_BASE_POINTS + round(bonus)


@transaction.atomic
def start_session(category_slug: str, client_type: str):
    try:
        category = Category.objects.get(slug=category_slug, is_active=True)
    except Category.DoesNotExist:
        raise QuizError("invalid_category", "Kategori bulunamadı.", 404)
    count = settings.QUIZ_QUESTION_COUNT
    ids = list(
        category.questions.filter(is_active=True)
        .annotate(n=Count("choices"), c=Count("choices", filter=Q(choices__is_correct=True)))
        .filter(n=4, c=1)
        .values_list("id", flat=True)
    )
    if len(ids) < count:
        raise QuizError("not_enough_questions", "Bu kategoride yeterli soru yok.", 503)
    if client_type not in QuizSession.Client.values:
        client_type = QuizSession.Client.WEB
    token = secrets.token_urlsafe(32)
    session = QuizSession.objects.create(category=category, token_hash=_hash(token), client_type=client_type)
    SessionQuestion.objects.bulk_create(
        SessionQuestion(session=session, question_id=qid, position=i)
        for i, qid in enumerate(random.sample(ids, count), start=1)
    )
    return session, token


def _deadline(sq: SessionQuestion):
    return sq.served_at + timedelta(milliseconds=settings.QUIZ_TIME_LIMIT_MS)


def _finalize_if_done(session: QuizSession):
    if session.questions.filter(answered_at__isnull=True).exists():
        return
    session.total_score = sum(session.questions.values_list("points", flat=True))
    session.correct_count = session.questions.filter(is_correct=True).count()
    session.status = QuizSession.Status.FINISHED
    session.finished_at = timezone.now()
    session.save(update_fields=["total_score", "correct_count", "status", "finished_at"])


def _close_expired(session: QuizSession, sq: SessionQuestion, now):
    """Süresi geçmiş, cevapsız soruyu boş geç."""
    sq.answered_at = now
    sq.time_taken_ms = settings.QUIZ_TIME_LIMIT_MS
    sq.save(update_fields=["answered_at", "time_taken_ms"])
    _finalize_if_done(session)


def _check_active(session: QuizSession):
    if session.status != QuizSession.Status.IN_PROGRESS:
        raise QuizError("session_finished", "Oturum tamamlanmış.", 409)


@transaction.atomic
def get_current_question(session: QuizSession):
    session = QuizSession.objects.select_for_update().get(pk=session.pk)
    _check_active(session)
    now = timezone.now()
    grace = timedelta(milliseconds=settings.QUIZ_NETWORK_TOLERANCE_MS)
    while True:
        sq = (
            session.questions.select_related("question")
            .filter(answered_at__isnull=True)
            .order_by("position")
            .first()
        )
        if sq is None:
            _finalize_if_done(session)
            raise QuizError("session_finished", "Oturum tamamlanmış.", 409)
        if sq.served_at is None:
            sq.served_at = now
            sq.save(update_fields=["served_at"])
            break
        if now > _deadline(sq) + grace:
            _close_expired(session, sq, now)
            if session.status != QuizSession.Status.IN_PROGRESS:
                raise QuizError("session_finished", "Oturum tamamlanmış.", 409)
            continue
        break
    choices = list(sq.question.choices.all())
    random.Random(sq.pk).shuffle(choices)  # sabit tohum: tekrar GET aynı sıralamayı verir
    return sq, choices, _deadline(sq), now


@transaction.atomic
def submit_answer(session: QuizSession, question_id: int, choice_id: int | None):
    session = QuizSession.objects.select_for_update().get(pk=session.pk)
    _check_active(session)
    sq = (
        session.questions.select_related("question")
        .filter(answered_at__isnull=True, served_at__isnull=False)
        .order_by("position")
        .first()
    )
    if sq is None or sq.question_id != question_id:
        if session.questions.filter(question_id=question_id, answered_at__isnull=False).exists():
            raise QuizError("already_answered", "Bu soru zaten cevaplandı.", 409)
        raise QuizError("invalid_question", "Bu soru şu an cevaplanamaz.", 409)

    now = timezone.now()
    elapsed_ms = int((now - sq.served_at).total_seconds() * 1000)
    limit = settings.QUIZ_TIME_LIMIT_MS
    timed_out = elapsed_ms > limit + settings.QUIZ_NETWORK_TOLERANCE_MS
    correct = sq.question.choices.get(is_correct=True)

    selected = None
    if choice_id is not None and not timed_out:
        try:
            selected = sq.question.choices.get(pk=choice_id)
        except Choice.DoesNotExist:
            raise QuizError("invalid_choice", "Geçersiz şık.", 400)

    is_correct = bool(selected and selected.pk == correct.pk)
    sq.answered_at = now
    sq.selected_choice = selected
    sq.is_correct = is_correct
    sq.time_taken_ms = min(elapsed_ms, limit)
    sq.points = calculate_points(is_correct, elapsed_ms)
    sq.save()
    _finalize_if_done(session)
    return {
        "is_correct": is_correct,
        "correct_choice_id": correct.pk,
        "points": sq.points,
        "timed_out": selected is None,
        "finished": session.status == QuizSession.Status.FINISHED,
    }


def get_result(session: QuizSession):
    if session.status != QuizSession.Status.FINISHED:
        raise QuizError("session_not_finished", "Quiz henüz bitmedi.", 409)
    avg = session.questions.aggregate(a=Avg("time_taken_ms"))["a"] or 0
    return {
        "total_score": session.total_score,
        "correct_count": session.correct_count,
        "total": session.questions.count(),
        "average_time_ms": round(avg),
    }


def validate_name(name: str) -> str:
    name = (name or "").strip()
    if not 2 <= len(name) <= 20 or not NAME_RE.match(name):
        raise QuizError("invalid_name", "Takma ad 2-20 karakter olmalı ve geçerli karakterler içermeli.")
    lowered = name.lower()
    if any(w and w.lower() in lowered for w in settings.QUIZ_BLOCKED_NAME_WORDS):
        raise QuizError("invalid_name", "Bu takma ad kullanılamaz.")
    return name


@transaction.atomic
def submit_name(session: QuizSession, name: str):
    from apps.leaderboard.selectors import rank_of

    session = QuizSession.objects.select_for_update().get(pk=session.pk)
    if session.status != QuizSession.Status.FINISHED:
        raise QuizError("session_not_finished", "Quiz henüz bitmedi.", 409)
    if session.player_name:
        raise QuizError("name_already_submitted", "İsim zaten gönderildi.", 409)
    session.player_name = validate_name(name)
    session.name_submitted_at = timezone.now()
    session.save(update_fields=["player_name", "name_submitted_at"])
    return {"player_name": session.player_name, "rank": rank_of(session)}


def expire_stale_sessions(hours: int = 24) -> int:
    cutoff = timezone.now() - timedelta(hours=hours)
    return QuizSession.objects.filter(status="in_progress", started_at__lt=cutoff).update(status="expired")
