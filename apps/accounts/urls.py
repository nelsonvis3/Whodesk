from django.urls import path

from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/login/", views.LoginView.as_view()),
    path("auth/logout/", views.LogoutView.as_view()),
    path("auth/token/", views.ThrottledTokenObtainView.as_view()),
    path("auth/token/refresh/", views.ThrottledTokenRefreshView.as_view()),
    path("users/me/", views.MeView.as_view()),
    path("users/staff/", views.StaffUsersView.as_view()),
]
