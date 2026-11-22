from rest_framework import serializers

from apps.accounts.models import Role
from apps.accounts.serializers import UserMiniSerializer

from . import services
from .models import Category, Comment, Priority, Ticket, TicketEvent


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class TicketListSerializer(serializers.ModelSerializer):
    created_by = UserMiniSerializer(read_only=True)
    assigned_to = UserMiniSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "status",
            "priority",
            "category",
            "created_by",
            "assigned_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TicketDetailSerializer(TicketListSerializer):
    allowed_transitions = serializers.SerializerMethodField()

    class Meta(TicketListSerializer.Meta):
        fields = TicketListSerializer.Meta.fields + [
            "description",
            "resolution_note",
            "resolved_at",
            "allowed_transitions",
        ]
        read_only_fields = fields

    def get_allowed_transitions(self, obj) -> list[str]:
        # El frontend solo muestra estos botones: la regla vive únicamente en el backend.
        return services.allowed_transitions(self.context["request"].user, obj)


class TicketCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    priority = serializers.ChoiceField(choices=Priority.choices, default=Priority.MEDIUM)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )

    def validate_title(self, v):
        if not v.strip():
            raise serializers.ValidationError("El título no puede estar vacío.")
        return v

    def validate_description(self, v):
        if not v.strip():
            raise serializers.ValidationError("La descripción no puede estar vacía.")
        return v


class TicketUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False)
    priority = serializers.ChoiceField(choices=Priority.choices, required=False)
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )


class TransitionSerializer(serializers.Serializer):
    status = serializers.CharField()
    resolution_note = serializers.CharField(required=False, allow_blank=True, default="")


class AssignSerializer(serializers.Serializer):
    assigned_to = serializers.IntegerField(allow_null=True)


class CommentSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "body", "is_internal", "created_at"]
        read_only_fields = fields


class CommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField()
    is_internal = serializers.BooleanField(default=False)


class TicketEventSerializer(serializers.ModelSerializer):
    actor = UserMiniSerializer(read_only=True)

    class Meta:
        model = TicketEvent
        fields = ["id", "actor", "event_type", "from_value", "to_value", "created_at"]
        read_only_fields = fields


def is_customer(user) -> bool:
    return user.role == Role.CUSTOMER
