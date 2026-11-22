from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("knowledge/articles", views.ArticleViewSet, basename="article")

urlpatterns = [
    path("assistant/ask/", views.AskView.as_view()),
    path("assistant/search/", views.SearchView.as_view()),
    path("assistant/queries/<int:pk>/feedback/", views.FeedbackView.as_view()),
    path("", include(router.urls)),
]
