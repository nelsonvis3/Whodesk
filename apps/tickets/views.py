from django.db import connection
from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import IsAgentOrAdmin

from . import selectors, services
from .filters import TicketFilter
from .models import Category, Status, Ticket
from .serializers import (
    AssignSerializer,
    CategorySerializer,
    CommentCreateSerializer,
    CommentSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketEventSerializer,
    TicketListSerializer,
    TicketUpdateSerializer,
    TransitionSerializer,
)


class TicketViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "post", "patch", "head", "options"]  # sin PUT ni DELETE
    filterset_class = TicketFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "id"]
    throttle_scope = None  # las acciones de IA definen su propio scope

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # generación del esquema OpenAPI
            return Ticket.objects.none()
        return selectors.tickets_visible_to(self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return TicketListSerializer
        if self.action == "create":
            return TicketCreateSerializer
        if self.action == "partial_update":
            return TicketUpdateSerializer
        return TicketDetailSerializer

    def _ticket(self, pk):
        # 404 también para tickets ajenos: no se revela que existen.
        return get_object_or_404(self.get_queryset(), pk=pk)

    def _detail(self, ticket):
        ticket = self.get_queryset().get(pk=ticket.pk)
        return Response(TicketDetailSerializer(ticket, context={"request": self.request}).data)

    @extend_schema(request=TicketCreateSerializer, responses={201: TicketDetailSerializer})
    def create(self, request, *args, **kwargs):
        ser = TicketCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ticket = services.create_ticket(request.user, **ser.validated_data)
        resp = self._detail(ticket)
        resp.status_code = status.HTTP_201_CREATED
        return resp

    @extend_schema(request=TicketUpdateSerializer, responses=TicketDetailSerializer)
    def partial_update(self, request, *args, **kwargs):
        ticket = self._ticket(kwargs["pk"])
        ser = TicketUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        services.update_ticket(request.user, ticket.pk, data=ser.validated_data)
        return self._detail(ticket)

    @extend_schema(request=TransitionSerializer, responses=TicketDetailSerializer)
    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        ticket = self._ticket(pk)
        ser = TransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.transition_ticket(
            request.user, ticket.pk, ser.validated_data["status"], ser.validated_data["resolution_note"]
        )
        return self._detail(ticket)

    @extend_schema(request=AssignSerializer, responses=TicketDetailSerializer)
    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        ticket = self._ticket(pk)
        ser = AssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.assign_ticket(request.user, ticket.pk, ser.validated_data["assigned_to"])
        return self._detail(ticket)

    @extend_schema(request=CommentCreateSerializer, responses=CommentSerializer(many=True))
    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        ticket = self._ticket(pk)
        if request.method == "POST":
            ser = CommentCreateSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            comment = services.add_comment(
                request.user,
                ticket.pk,
                body=ser.validated_data["body"],
                internal=ser.validated_data["is_internal"],
            )
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        qs = selectors.comments_visible_to(request.user, ticket)
        return Response(CommentSerializer(qs, many=True).data)

    @extend_schema(responses=TicketEventSerializer(many=True))
    @action(detail=True, methods=["get"])
    def events(self, request, pk=None):
        ticket = self._ticket(pk)
        qs = selectors.events_visible_to(request.user, ticket)
        return Response(TicketEventSerializer(qs, many=True).data)

    @extend_schema(responses=dict)
    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = selectors.tickets_visible_to(request.user)
        counts = dict(qs.order_by().values_list("status").annotate(c=Count("id")))
        data = {"by_status": {s: counts.get(s, 0) for s in Status.values}}
        if request.user.role != Role.CUSTOMER:
            active = qs.exclude(status__in=[Status.RESOLVED, Status.CLOSED])
            data["unassigned"] = active.filter(assigned_to__isnull=True).count()
            data["mine"] = active.filter(assigned_to=request.user).count()
        return Response(data)

    @extend_schema(request=None, responses=dict)
    @action(
        detail=True,
        methods=["post"],
        url_path="suggest-reply",
        permission_classes=[IsAgentOrAdmin],
        throttle_scope="assistant",
    )
    def suggest_reply(self, request, pk=None):
        from apps.knowledge import services as kb  # import tardío: evita dependencia circular

        ticket = self._ticket(pk)
        return Response(kb.suggest_reply(request.user, ticket))


class CategoryList(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


@extend_schema(responses=dict)
@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def health(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:  # noqa: BLE001 - cualquier fallo de base significa "degradado"
        return Response(
            {"status": "degraded", "database": "error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    return Response({"status": "ok", "database": "ok"})
