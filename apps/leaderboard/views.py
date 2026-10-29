from rest_framework.response import Response
from rest_framework.views import APIView

from apps.quiz.exceptions import QuizError
from apps.quiz.models import Category

from . import selectors


class LeaderboardView(APIView):
    def get(self, request):
        slug = request.query_params.get("category")
        try:
            category = Category.objects.get(slug=slug, is_active=True)
        except Category.DoesNotExist:
            raise QuizError("invalid_category", "Kategori bulunamadı.", 404)
        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            raise QuizError("validation_error", "limit sayı olmalı.")
        rows = selectors.top(category, limit)
        return Response(
            {
                "category": category.slug,
                "entries": [
                    {
                        "rank": i,
                        "player_name": r.player_name,
                        "total_score": r.total_score,
                        "correct_count": r.correct_count,
                        "session_id": str(r.id),
                    }
                    for i, r in enumerate(rows, start=1)
                ],
            }
        )
