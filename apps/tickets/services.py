"""Casos de uso. Cada operación es atómica: el cambio y su TicketEvent se guardan juntos o no se guardan."""

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, User

from .exceptions import BusinessValidationError, InvalidTransition, NotAllowed
from .models import Category, Comment, EventType, Priority, Status, Ticket, TicketEvent

OWNER = "customer_owner"
STAFF = {Role.AGENT, Role.ADMIN}

# Tabla de transiciones: estado actual -> {estado destino: quiénes pueden}
TRANSITIONS = {
    Status.OPEN: {
        Status.IN_PROGRESS: {Role.AGENT, Role.ADMIN},
        Status.CLOSED: {OWNER, Role.AGENT, Role.ADMIN},
    },
    Status.IN_PROGRESS: {
        Status.WAITING_CUSTOMER: {Role.AGENT, Role.ADMIN},
        Status.RESOLVED: {Role.AGENT, Role.ADMIN},
    },
    Status.WAITING_CUSTOMER: {
        Status.IN_PROGRESS: {OWNER, Role.AGENT, Role.ADMIN},
    },
    Status.RESOLVED: {
        Status.CLOSED: {OWNER, Role.AGENT, Role.ADMIN},
        Status.IN_PROGRESS: {OWNER, Role.AGENT, Role.ADMIN},
    },
    Status.CLOSED: {},
}


def _actor_keys(actor: User, ticket: Ticket) -> set:
    keys = {actor.role}
    if actor.role == Role.CUSTOMER and ticket.created_by_id == actor.id:
        keys.add(OWNER)
    return keys


def allowed_transitions(actor: User, ticket: Ticket) -> list[str]:
    keys = _actor_keys(actor, ticket)
    return [to for to, who in TRANSITIONS.get(ticket.status, {}).items() if keys & who]


def _event(ticket, actor, event_type, from_value="", to_value=""):
    return TicketEvent.objects.create(
        ticket=ticket, actor=actor, event_type=event_type, from_value=str(from_value), to_value=str(to_value)
    )


@transaction.atomic
def create_ticket(actor: User, *, title, description, priority=Priority.MEDIUM, category=None) -> Ticket:
    ticket = Ticket.objects.create(
        created_by=actor,
        title=title.strip(),
        description=description.strip(),
        priority=priority,
        category=category,
    )
    _event(ticket, actor, EventType.CREATED, to_value=Status.OPEN)
    return ticket


@transaction.atomic
def update_ticket(actor: User, ticket_id: int, *, data: dict) -> Ticket:
    """Clientes: título/descripción de su ticket abierto. Personal: prioridad y categoría."""
    ticket = Ticket.objects.select_for_update().get(pk=ticket_id)
    staff = actor.role in STAFF
    if not staff:
        if ticket.created_by_id != actor.id:
            raise NotAllowed("No podés editar este ticket.")
        if ticket.status != Status.OPEN:
            raise NotAllowed("Solo se puede editar un ticket mientras está abierto.")
        allowed = {"title", "description"}
    else:
        allowed = {"priority", "category"}
        if actor.role == Role.ADMIN:
            allowed |= {"title", "description"}
    forbidden = set(data) - allowed
    if forbidden:
        raise NotAllowed(f"No podés modificar: {', '.join(sorted(forbidden))}.")

    if "priority" in data and data["priority"] != ticket.priority:
        _event(ticket, actor, EventType.PRIORITY_CHANGED, ticket.priority, data["priority"])
        ticket.priority = data["priority"]
    if "category" in data:
        new = data["category"]
        if (new.pk if new else None) != ticket.category_id:
            _event(
                ticket,
                actor,
                EventType.CATEGORY_CHANGED,
                ticket.category.name if ticket.category else "",
                new.name if new else "",
            )
            ticket.category = new
    for f in ("title", "description"):
        if f in data:
            setattr(ticket, f, data[f].strip())
    ticket.save()
    return ticket


@transaction.atomic
def assign_ticket(actor: User, ticket_id: int, agent_id) -> Ticket:
    if actor.role not in STAFF:
        raise NotAllowed("Solo agentes y administradores pueden asignar tickets.")
    ticket = Ticket.objects.select_for_update().get(pk=ticket_id)
    if ticket.status == Status.CLOSED:
        raise InvalidTransition("No se puede asignar un ticket cerrado.")
    target = None
    if agent_id is not None:
        try:
            target = User.objects.get(pk=agent_id, is_active=True, role__in=list(STAFF))
        except User.DoesNotExist:
            raise BusinessValidationError("El usuario elegido no es un agente activo.") from None
    if (target.pk if target else None) == ticket.assigned_to_id:
        return ticket
    _event(
        ticket,
        actor,
        EventType.ASSIGNED,
        ticket.assigned_to.full_name if ticket.assigned_to else "",
        target.full_name if target else "",
    )
    ticket.assigned_to = target
    ticket.save()
    return ticket


@transaction.atomic
def transition_ticket(actor: User, ticket_id: int, to_status: str, note: str = "") -> Ticket:
    # select_for_update bloquea la fila: dos agentes no pueden transicionar a la vez el mismo ticket.
    ticket = Ticket.objects.select_for_update().get(pk=ticket_id)
    if to_status not in Status.values:
        raise BusinessValidationError("Estado inexistente.")
    if to_status not in TRANSITIONS.get(ticket.status, {}):
        raise InvalidTransition(f"No se puede pasar de «{ticket.status}» a «{to_status}».")
    if to_status not in allowed_transitions(actor, ticket):
        raise NotAllowed("No tenés permiso para esta transición.")

    note = (note or "").strip()
    if to_status == Status.RESOLVED and not note:
        raise BusinessValidationError("Para resolver un ticket hay que escribir una nota de resolución.")

    old = ticket.status
    # Al tomar un ticket abierto sin asignar, queda asignado a quien lo toma.
    if (
        old == Status.OPEN
        and to_status == Status.IN_PROGRESS
        and actor.role in STAFF
        and ticket.assigned_to_id is None
    ):
        ticket.assigned_to = actor
        _event(ticket, actor, EventType.ASSIGNED, "", actor.full_name)

    ticket.status = to_status
    if to_status == Status.RESOLVED:
        ticket.resolution_note = note
        ticket.resolved_at = timezone.now()
    elif old == Status.RESOLVED and to_status == Status.IN_PROGRESS:
        ticket.resolved_at = None  # reapertura: se limpia la fecha, se conserva la nota anterior
    ticket.save()
    _event(ticket, actor, EventType.STATUS_CHANGED, old, to_status)
    return ticket


@transaction.atomic
def add_comment(actor: User, ticket_id: int, *, body: str, internal: bool = False) -> Comment:
    ticket = Ticket.objects.select_for_update().get(pk=ticket_id)
    body = (body or "").strip()
    if not body:
        raise BusinessValidationError("El comentario no puede estar vacío.")
    if internal and actor.role not in STAFF:
        raise NotAllowed("Solo el personal puede dejar notas internas.")
    if ticket.status == Status.CLOSED:
        raise InvalidTransition("El ticket está cerrado: reabrilo o creá uno nuevo.")
    comment = Comment.objects.create(ticket=ticket, author=actor, body=body, is_internal=internal)
    _event(ticket, actor, EventType.COMMENTED, to_value="internal" if internal else "public")
    # Si el cliente responde mientras esperábamos su respuesta, el ticket vuelve a estar en progreso.
    if actor.role == Role.CUSTOMER and ticket.status == Status.WAITING_CUSTOMER:
        ticket.status = Status.IN_PROGRESS
        ticket.save()
        _event(ticket, actor, EventType.STATUS_CHANGED, Status.WAITING_CUSTOMER, Status.IN_PROGRESS)
    else:
        ticket.save(update_fields=["updated_at"])
    return comment


def category_by_id(pk):
    return Category.objects.filter(pk=pk).first()
