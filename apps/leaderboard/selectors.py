from django.db.models import Q

from apps.quiz.models import QuizSession


def _board(category):
    return QuizSession.objects.filter(
        category=category, status="finished", player_name__isnull=False, is_hidden=False
    )


def top(category, limit=10):
    limit = max(1, min(limit, 50))
    return list(_board(category).order_by("-total_score", "finished_at")[:limit])


def rank_of(session):
    ahead = _board(session.category).filter(
        Q(total_score__gt=session.total_score)
        | Q(total_score=session.total_score, finished_at__lt=session.finished_at)
    )
    return ahead.count() + 1
