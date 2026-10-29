from django import forms
from django.contrib import admin

from .models import Category, Choice, Question, QuizSession


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color", "is_active")
    prepopulated_fields = {"slug": ("name",)}


class ChoiceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        forms_ = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if len(forms_) != 4:
            raise forms.ValidationError("Her soru için tam 4 şık gerekli.")
        if sum(1 for f in forms_ if f.cleaned_data.get("is_correct")) != 1:
            raise forms.ValidationError("Tam olarak bir şık doğru olmalı.")


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet
    extra = 4
    max_num = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "category", "difficulty", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("text",)
    inlines = [ChoiceInline]


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "player_name", "total_score", "status", "is_hidden", "finished_at")
    list_filter = ("category", "status", "is_hidden", "client_type")
    search_fields = ("player_name",)
    actions = ["hide_from_leaderboard"]

    @admin.action(description="Skor tablosundan gizle")
    def hide_from_leaderboard(self, request, queryset):
        queryset.update(is_hidden=True)
