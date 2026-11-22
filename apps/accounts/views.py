import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Role, User
from .permissions import IsAgentOrAdmin
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserMiniSerializer,
    UserSerializer,
)

log = logging.getLogger(__name__)


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(request=LoginSerializer, responses=UserSerializer)
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = authenticate(
            request, username=ser.validated_data["email"].lower(), password=ser.validated_data["password"]
        )
        if user is None:
            return Response(
                {"detail": "Email o contraseña incorrectos."}, status=status.HTTP_401_UNAUTHORIZED
            )
        login(request, user)
        return Response(UserSerializer(user).data)


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(request=PasswordResetRequestSerializer, responses={202: dict})
    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        form = PasswordResetForm({"email": ser.validated_data["email"]})
        if form.is_valid():
            for user in form.get_users(form.cleaned_data["email"]):
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                query = urlencode({"uid": uid, "token": token})
                reset_url = f"{request.build_absolute_uri('/')}#/reset-password?{query}"
                message = (
                    "Recibimos una solicitud para restablecer la contraseña de tu cuenta de Whodesk.\n\n"
                    "Abrí este enlace para elegir una contraseña nueva (vence en 30 minutos y se usa "
                    f"una sola vez):\n"
                    f"{reset_url}\n\n"
                    "Si no pediste este cambio, podés ignorar este mensaje."
                )
                try:
                    send_mail(
                        "Restablecé tu contraseña de Whodesk",
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception:
                    # La misma respuesta para cuentas existentes y desconocidas evita revelar usuarios.
                    log.exception("No se pudo enviar un correo de restablecimiento de contraseña.")

        return Response(
            {
                "detail": (
                    "Si existe una cuenta asociada a ese correo, se enviará un enlace "
                    "para restablecer la contraseña."
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    @extend_schema(request=PasswordResetConfirmSerializer, responses={204: None})
    def post(self, request):
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class StaffUsersView(generics.ListAPIView):
    """Agentes y administradores (para el selector de asignación). Solo personal."""

    permission_classes = [IsAgentOrAdmin]
    serializer_class = UserMiniSerializer
    pagination_class = None

    def get_queryset(self):
        return User.objects.filter(role__in=[Role.AGENT, Role.ADMIN], is_active=True)


class ThrottledTokenObtainView(TokenObtainPairView):
    throttle_scope = "auth"


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth"
