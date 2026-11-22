"""Querysets: qué ve cada rol. La visibilidad se decide acá, no en las vistas."""

from apps.accounts.models import Role

from .models import Comment, Ticket, TicketEvent


def tickets_visible_to(user):
    qs = Ticket.objects.select_related("created_by", "assigned_to", "category")
    if user.role == Role.CUSTOMER:
        return qs.filter(created_by=user)
    return qs


def comments_visible_to(user, ticket):
    qs = Comment.objects.filter(ticket=ticket).select_related("author")
    if user.role == Role.CUSTOMER:
        qs = qs.filter(is_internal=False)
    return qs


def events_visible_to(user, ticket):
    qs = TicketEvent.objects.filter(ticket=ticket).select_related("actor")
    if user.role == Role.CUSTOMER:
        # El cliente no debe enterarse de que existen notas internas.
        qs = qs.exclude(event_type="commented", to_value="internal")
    return qs
