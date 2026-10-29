from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.CategoryListView.as_view()),
    path("config/", views.ConfigView.as_view()),
    path("sessions/", views.SessionCreateView.as_view()),
    path("sessions/<str:pk>/question/", views.QuestionView.as_view()),
    path("sessions/<str:pk>/answer/", views.AnswerView.as_view()),
    path("sessions/<str:pk>/result/", views.ResultView.as_view()),
    path("sessions/<str:pk>/submit-name/", views.SubmitNameView.as_view()),
]
