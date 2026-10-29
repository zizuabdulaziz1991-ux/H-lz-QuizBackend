from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.quiz import services
from apps.quiz.models import QuizSession, SessionQuestion

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def questions():
    call_command("import_questions", "data/questions.json")


def start(client, category="tarih"):
    r = client.post("/api/v1/sessions/", {"category": category}, format="json")
    assert r.status_code == 201, r.data
    return r.data["session_id"], {"HTTP_X_SESSION_TOKEN": r.data["session_token"]}


def play(client, sid, h, pick_correct=True):
    while True:
        r = client.get(f"/api/v1/sessions/{sid}/question/", **h)
        if r.status_code == 409:
            return
        q = r.data
        sq = SessionQuestion.objects.get(session_id=sid, question_id=q["question_id"])
        correct = sq.question.choices.get(is_correct=True)
        wrong = sq.question.choices.filter(is_correct=False).first()
        cid = (correct if pick_correct else wrong).id
        a = client.post(
            f"/api/v1/sessions/{sid}/answer/", {"question_id": q["question_id"], "choice_id": cid}, format="json", **h
        )
        assert a.status_code == 200, a.data
        if a.data["finished"]:
            return


def test_categories_and_config(client, questions):
    r = client.get("/api/v1/categories/")
    assert len(r.data) == 5 and all(c["question_count"] == 20 for c in r.data)
    assert client.get("/api/v1/config/").data["question_count"] == 20


def test_not_enough_questions(client):
    r = client.post("/api/v1/sessions/", {"category": "tarih"}, format="json")
    assert r.status_code == 503 and r.data["error"]["code"] == "not_enough_questions"


def test_question_hides_answer(client, questions):
    sid, h = start(client)
    q = client.get(f"/api/v1/sessions/{sid}/question/", **h).data
    assert q["position"] == 1 and len(q["choices"]) == 4
    assert all("is_correct" not in c for c in q["choices"])


def test_token_required(client, questions):
    sid, _ = start(client)
    r = client.get(f"/api/v1/sessions/{sid}/question/")
    assert r.status_code == 401 and r.data["error"]["code"] == "invalid_token"
    assert client.get("/api/v1/sessions/not-a-uuid/question/").status_code == 401


def test_full_flow_and_leaderboard(client, questions):
    sid, h = start(client)
    play(client, sid, h)
    res = client.get(f"/api/v1/sessions/{sid}/result/", **h).data
    assert res["correct_count"] == 20 and 2000 <= res["total_score"] <= 3000
    r = client.post(f"/api/v1/sessions/{sid}/submit-name/", {"player_name": "Ali"}, format="json", **h)
    assert r.status_code == 200 and r.data["rank"] == 1
    again = client.post(f"/api/v1/sessions/{sid}/submit-name/", {"player_name": "Veli"}, format="json", **h)
    assert again.status_code == 409
    lb = client.get("/api/v1/leaderboard/?category=tarih").data
    assert lb["entries"][0]["player_name"] == "Ali"


def test_invalid_name(client, questions):
    sid, h = start(client)
    play(client, sid, h)
    r = client.post(f"/api/v1/sessions/{sid}/submit-name/", {"player_name": "a"}, format="json", **h)
    assert r.status_code == 400 and r.data["error"]["code"] == "invalid_name"


def test_double_answer_rejected(client, questions):
    sid, h = start(client)
    q = client.get(f"/api/v1/sessions/{sid}/question/", **h).data
    body = {"question_id": q["question_id"], "choice_id": q["choices"][0]["id"]}
    assert client.post(f"/api/v1/sessions/{sid}/answer/", body, format="json", **h).status_code == 200
    r = client.post(f"/api/v1/sessions/{sid}/answer/", body, format="json", **h)
    assert r.status_code == 409 and r.data["error"]["code"] == "already_answered"


def test_late_answer_scores_zero(client, questions):
    sid, h = start(client)
    q = client.get(f"/api/v1/sessions/{sid}/question/", **h).data
    SessionQuestion.objects.filter(session_id=sid, position=1).update(
        served_at=timezone.now() - timedelta(seconds=10)
    )
    correct = SessionQuestion.objects.get(session_id=sid, position=1).question.choices.get(is_correct=True)
    r = client.post(
        f"/api/v1/sessions/{sid}/answer/",
        {"question_id": q["question_id"], "choice_id": correct.id},
        format="json",
        **h,
    )
    assert r.data["points"] == 0 and r.data["timed_out"] and not r.data["is_correct"]


def test_expired_question_is_skipped(client, questions):
    sid, h = start(client)
    client.get(f"/api/v1/sessions/{sid}/question/", **h)
    SessionQuestion.objects.filter(session_id=sid, position=1).update(
        served_at=timezone.now() - timedelta(seconds=10)
    )
    q2 = client.get(f"/api/v1/sessions/{sid}/question/", **h).data
    assert q2["position"] == 2


def test_cannot_skip_ahead(client, questions):
    sid, h = start(client)
    client.get(f"/api/v1/sessions/{sid}/question/", **h)
    other = SessionQuestion.objects.get(session_id=sid, position=2)
    r = client.post(
        f"/api/v1/sessions/{sid}/answer/", {"question_id": other.question_id, "choice_id": None}, format="json", **h
    )
    assert r.status_code == 409


def test_points_formula():
    assert services.calculate_points(True, 0) == 150
    assert services.calculate_points(True, 5000) == 100
    assert services.calculate_points(True, 2500) == 125
    assert services.calculate_points(False, 0) == 0


def test_expire_stale_sessions(client, questions):
    sid, _ = start(client)
    QuizSession.objects.filter(pk=sid).update(started_at=timezone.now() - timedelta(hours=25))
    assert services.expire_stale_sessions() == 1


def test_old_mobile_version_rejected(client, questions, settings):
    settings.QUIZ_MIN_APP_VERSION = "1.2.0"
    r = client.post(
        "/api/v1/sessions/", {"category": "tarih"}, format="json", HTTP_X_CLIENT="ios", HTTP_X_APP_VERSION="1.1.9"
    )
    assert r.status_code == 426 and r.data["error"]["code"] == "upgrade_required"
    ok = client.post(
        "/api/v1/sessions/", {"category": "tarih"}, format="json", HTTP_X_CLIENT="android", HTTP_X_APP_VERSION="1.2.0"
    )
    assert ok.status_code == 201


def test_healthz(client):
    assert client.get("/healthz").status_code == 200
