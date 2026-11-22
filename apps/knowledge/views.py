from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.accounts.permissions import IsAdminRole

from . import services
from .models import KnowledgeArticle
from .serializers import ArticleListSerializer, ArticleSerializer, FeedbackSerializer, QuestionSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    """Lectura: cualquier usuario autenticado (los clientes solo ven artículos públicos). Escritura: admin."""

    search_fields = ["title", "body"]
    ordering_fields = ["title", "updated_at"]
    filterset_fields = ["is_public", "is_active"]
    throttle_scope = None

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return super().get_permissions()
        return [IsAdminRole()]

    def get_queryset(self):
        qs = KnowledgeArticle.objects.all()
        if getattr(self, "swagger_fake_view", False):  # generación del esquema OpenAPI
            return qs.none()
        role = self.request.user.role
        if role == Role.CUSTOMER:
            return qs.filter(is_public=True, is_active=True)
        if role == Role.AGENT:
            return qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        return ArticleListSerializer if self.action == "list" else ArticleSerializer


class AskView(APIView):
    throttle_scope = "assistant"

    @extend_schema(request=QuestionSerializer, responses=dict)
    def post(self, request):
        ser = QuestionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return Response(services.ask_assistant(request.user, ser.validated_data["question"]))


class SearchView(APIView):
    throttle_scope = "assistant"

    @extend_schema(responses=dict)
    def get(self, request):
        return Response(
            {"results": services.search_articles(request.user, request.query_params.get("q", ""))}
        )


class FeedbackView(APIView):
    @extend_schema(request=FeedbackSerializer, responses={204: None})
    def post(self, request, pk):
        ser = FeedbackSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.record_feedback(request.user, pk, ser.validated_data["value"])
        return Response(status=status.HTTP_204_NO_CONTENT)
