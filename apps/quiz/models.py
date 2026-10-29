import uuid

from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q


class Category(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#6C5CE7")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["id"]

    def __str__(self):
        return self.name


class Question(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    difficulty = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["category", "is_active"])]

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["question"], condition=Q(is_correct=True), name="one_correct_choice_per_question"
            )
        ]

    def __str__(self):
        return self.text


class QuizSession(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress"
        FINISHED = "finished"
        EXPIRED = "expired"

    class Client(models.TextChoices):
        WEB = "web"
        IOS = "ios"
        ANDROID = "android"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=64, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="sessions")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    total_score = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveSmallIntegerField(default=0)
    player_name = models.CharField(max_length=20, null=True, blank=True, validators=[MinLengthValidator(2)])
    name_submitted_at = models.DateTimeField(null=True, blank=True)
    client_type = models.CharField(max_length=10, choices=Client.choices, default=Client.WEB)
    is_hidden = models.BooleanField(default=False, help_text="Skor tablosundan gizle")

    class Meta:
        indexes = [
            models.Index(
                fields=["category", "-total_score", "finished_at"],
                name="leaderboard_idx",
                condition=Q(player_name__isnull=False),
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(client_type__in=["web", "ios", "android"]), name="valid_client_type"
            )
        ]


class SessionQuestion(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="questions")
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField()
    served_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    selected_choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL)
    is_correct = models.BooleanField(default=False)
    time_taken_ms = models.PositiveIntegerField(null=True, blank=True)
    points = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["session", "position"], name="uniq_session_position")]
