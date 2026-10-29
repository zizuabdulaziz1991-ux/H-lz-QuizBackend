from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .exceptions import QuizError
from .models import Category, QuizSession
from .serializers import AnswerSerializer, CategorySerializer, CreateSessionSerializer, SubmitNameSerializer
from .throttles import SessionCreateThrottle


def _bad_input(serializer):
    raise QuizError("validation_error", str(serializer.errors), 400)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class SessionMixin:
    def get_session(self, request, pk):
        try:
            session = QuizSession.objects.select_related("category").get(pk=pk)
        except (QuizSession.DoesNotExist, ValidationError, ValueError):
            raise QuizError("invalid_token", "Geçersiz oturum.", 401)
        if not services.verify_token(session, request.headers.get("X-Session-Token")):
            raise QuizError("invalid_token", "Geçersiz oturum anahtarı.", 401)
        return session


class CategoryListView(APIView):
    def get(self, request):
        cats = Category.objects.filter(is_active=True).annotate(
            question_count=Count("questions", filter=Q(questions__is_active=True))
        )
        return Response(CategorySerializer(cats, many=True).data)


class ConfigView(APIView):
    def get(self, request):
        return Response(
            {
                "time_limit_ms": settings.QUIZ_TIME_LIMIT_MS,
                "question_count": settings.QUIZ_QUESTION_COUNT,
                "min_app_version": settings.QUIZ_MIN_APP_VERSION,
                "base_points": settings.QUIZ_BASE_POINTS,
                "max_speed_bonus": settings.QUIZ_MAX_SPEED_BONUS,
            }
        )


class SessionCreateView(APIView):
    throttle_classes = [SessionCreateThrottle]

    def post(self, request):
        s = CreateSessionSerializer(data=request.data)
        if not s.is_valid():
            _bad_input(s)
        client_type = request.headers.get("X-Client", "web")
        services.check_app_version(client_type, request.headers.get("X-App-Version"))
        session, token = services.start_session(s.validated_data["category"], client_type)
        return Response({"session_id": str(session.id), "session_token": token}, status=201)


class QuestionView(SessionMixin, APIView):
    def get(self, request, pk):
        session = self.get_session(request, pk)
        sq, choices, expires_at, now = services.get_current_question(session)
        return Response(
            {
                "question_id": sq.question_id,
                "position": sq.position,
                "total": settings.QUIZ_QUESTION_COUNT,
                "text": sq.question.text,
                "choices": [{"id": c.id, "text": c.text} for c in choices],
                "time_limit_ms": settings.QUIZ_TIME_LIMIT_MS,
                "expires_at": _iso(expires_at),
                "server_time": _iso(now),
            }
        )


class AnswerView(SessionMixin, APIView):
    def post(self, request, pk):
        session = self.get_session(request, pk)
        s = AnswerSerializer(data=request.data)
        if not s.is_valid():
            _bad_input(s)
        return Response(services.submit_answer(session, **s.validated_data))


class ResultView(SessionMixin, APIView):
    def get(self, request, pk):
        return Response(services.get_result(self.get_session(request, pk)))


class SubmitNameView(SessionMixin, APIView):
    def post(self, request, pk):
        session = self.get_session(request, pk)
        s = SubmitNameSerializer(data=request.data)
        if not s.is_valid():
            _bad_input(s)
        return Response(services.submit_name(session, s.validated_data["player_name"]))
