from django.conf import settings
from django.db import models


class Status(models.TextChoices):
    OPEN = "open", "Abierto"
    IN_PROGRESS = "in_progress", "En progreso"
    WAITING_CUSTOMER = "waiting_customer", "Esperando al cliente"
    RESOLVED = "resolved", "Resuelto"
    CLOSED = "closed", "Cerrado"


class Priority(models.TextChoices):
    LOW = "low", "Baja"
    MEDIUM = "medium", "Media"
    HIGH = "high", "Alta"
    URGENT = "urgent", "Urgente"


class EventType(models.TextChoices):
    CREATED = "created", "Ticket creado"
    STATUS_CHANGED = "status_changed", "Cambio de estado"
    ASSIGNED = "assigned", "Asignación"
    PRIORITY_CHANGED = "priority_changed", "Cambio de prioridad"
    CATEGORY_CHANGED = "category_changed", "Cambio de categoría"
    COMMENTED = "commented", "Comentario"


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Ticket(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM, db_index=True
    )
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets"
    )
    # PROTECT: no se puede borrar un usuario y perder la autoría de sus tickets.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tickets_created"
    )
    # SET_NULL: si un agente se va, el ticket queda sin asignar en lugar de desaparecer.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets_assigned",
    )
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"#{self.pk} {self.title}"


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="comments")
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class TicketEvent(models.Model):
    """Historial de auditoría: solo se inserta, nunca se edita ni se borra desde la API."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="ticket_events"
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    from_value = models.CharField(max_length=120, blank=True)
    to_value = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
