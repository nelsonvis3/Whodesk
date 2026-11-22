from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("tickets", views.TicketViewSet, basename="ticket")

urlpatterns = [
    path("health/", views.health),
    path("categories/", views.CategoryList.as_view()),
    path("", include(router.urls)),
]
