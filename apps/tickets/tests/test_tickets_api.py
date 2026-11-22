import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.tickets.models import Comment, Ticket, TicketEvent

pytestmark = pytest.mark.django_db


# ---- creación -----------------------------------------------------------------------
def test_create_ticket_ignores_forbidden_fields_and_logs_event(as_user, customer, agent):
    r = as_user(customer).post(
        "/api/tickets/",
        {
            "title": "Problema",
            "description": "Detalle",
            "priority": "high",
            "status": "resolved",
            "created_by": agent.pk,
            "assigned_to": agent.pk,
        },
        format="json",
    )
    assert r.status_code == 201
    t = Ticket.objects.get()
    assert t.created_by == customer and t.status == "open" and t.assigned_to is None
    assert list(t.events.values_list("event_type", flat=True)) == ["created"]


def test_create_ticket_validation(as_user, customer):
    r = as_user(customer).post("/api/tickets/", {"title": "  ", "description": ""}, format="json")
    assert r.status_code == 400 and {"title", "description"} <= set(r.json())


# ---- visibilidad --------------------------------------------------------------------
def test_customer_sees_only_own_tickets_and_gets_404_on_others(as_user, customer, customer2, make_ticket):
    mine = make_ticket(customer)
    other = make_ticket(customer2)
    c = as_user(customer)
    ids = [t["id"] for t in c.get("/api/tickets/").json()["results"]]
    assert ids == [mine.pk]
    assert c.get(f"/api/tickets/{other.pk}/").status_code == 404
    assert c.get(f"/api/tickets/{other.pk}/comments/").status_code == 404
    assert (
        c.post(f"/api/tickets/{other.pk}/transition/", {"status": "closed"}, format="json").status_code == 404
    )
    assert c.patch(f"/api/tickets/{other.pk}/", {"title": "x"}, format="json").status_code == 404


def test_agent_sees_all_tickets(as_user, agent, customer, customer2, make_ticket):
    make_ticket(customer)
    make_ticket(customer2)
    assert as_user(agent).get("/api/tickets/").json()["count"] == 2


def test_unauthenticated_is_401(api):
    assert api.get("/api/tickets/").status_code == 401


@pytest.mark.parametrize(
    "method,suffix,payload",
    [
        ("delete", "", None),
        ("put", "", {"title": "x", "description": "y"}),
    ],
)
def test_no_delete_or_put(as_user, admin, customer, make_ticket, method, suffix, payload):
    t = make_ticket(customer)
    r = getattr(as_user(admin), method)(f"/api/tickets/{t.pk}/{suffix}", payload, format="json")
    assert r.status_code == 405


# ---- matriz de permisos de transición ----------------------------------------------------
@pytest.mark.parametrize(
    "role,start,to,expected",
    [
        ("customer", "open", "in_progress", 403),
        ("customer", "open", "closed", 200),
        ("agent", "open", "in_progress", 200),
        ("agent", "open", "closed", 200),
        ("admin", "open", "in_progress", 200),
        ("agent", "open", "resolved", 409),
        ("agent", "closed", "in_progress", 409),
        ("customer", "resolved", "closed", 200),
        ("customer", "resolved", "in_progress", 200),
        ("customer", "in_progress", "resolved", 403),  # la transición existe, pero no para clientes
        ("customer", "in_progress", "waiting_customer", 403),
        ("customer", "waiting_customer", "in_progress", 200),
    ],
)
def test_transition_matrix(as_user, customer, agent, admin, make_ticket, role, start, to, expected):
    from apps.tickets import services

    t = make_ticket(customer)
    # llevar el ticket al estado de partida usando el servicio, siempre como agente
    path = {
        "open": [],
        "in_progress": ["in_progress"],
        "waiting_customer": ["in_progress", "waiting_customer"],
        "resolved": ["in_progress", "resolved"],
        "closed": ["in_progress", "resolved", "closed"],
    }[start]
    for step in path:
        services.transition_ticket(agent, t.pk, step, "nota de resolución" if step == "resolved" else "")
    user = {"customer": customer, "agent": agent, "admin": admin}[role]
    body = {"status": to, "resolution_note": "Resuelto" if to == "resolved" else ""}
    before = TicketEvent.objects.filter(ticket=t).count()
    r = as_user(user).post(f"/api/tickets/{t.pk}/transition/", body, format="json")
    assert r.status_code == expected, r.content
    after = TicketEvent.objects.filter(ticket=t).count()
    if expected == 200:
        assert r.json()["status"] == to and after > before
    else:
        assert after == before  # un intento fallido no deja rastros
        t.refresh_from_db()
        assert t.status == start


def test_resolve_requires_note_and_sets_resolved_at(as_user, agent, customer, make_ticket):
    from apps.tickets import services

    t = make_ticket(customer)
    services.transition_ticket(agent, t.pk, "in_progress")
    c = as_user(agent)
    assert (
        c.post(f"/api/tickets/{t.pk}/transition/", {"status": "resolved"}, format="json").status_code == 400
    )
    r = c.post(
        f"/api/tickets/{t.pk}/transition/", {"status": "resolved", "resolution_note": "Listo"}, format="json"
    )
    assert r.status_code == 200 and r.json()["resolved_at"] and r.json()["resolution_note"] == "Listo"


def test_reopen_clears_resolved_at(as_user, agent, customer, make_ticket):
    from apps.tickets import services

    t = make_ticket(customer)
    services.transition_ticket(agent, t.pk, "in_progress")
    services.transition_ticket(agent, t.pk, "resolved", "ok")
    r = as_user(customer).post(f"/api/tickets/{t.pk}/transition/", {"status": "in_progress"}, format="json")
    assert r.status_code == 200 and r.json()["resolved_at"] is None


def test_taking_open_ticket_auto_assigns_to_agent(as_user, agent, customer, make_ticket):
    t = make_ticket(customer)
    r = as_user(agent).post(f"/api/tickets/{t.pk}/transition/", {"status": "in_progress"}, format="json")
    assert r.json()["assigned_to"]["id"] == agent.pk
    types = list(t.events.values_list("event_type", flat=True))
    assert types == ["created", "assigned", "status_changed"]


def test_allowed_transitions_field_depends_on_role(as_user, agent, customer, make_ticket):
    t = make_ticket(customer)
    assert as_user(customer).get(f"/api/tickets/{t.pk}/").json()["allowed_transitions"] == ["closed"]
    assert set(as_user(agent).get(f"/api/tickets/{t.pk}/").json()["allowed_transitions"]) == {
        "in_progress",
        "closed",
    }


def test_transition_is_atomic(agent, customer, make_ticket, monkeypatch):
    from apps.tickets import services

    t = make_ticket(customer)

    def boom(*a, **k):
        raise RuntimeError("falla al guardar el evento")

    monkeypatch.setattr(services, "_event", boom)
    with pytest.raises(RuntimeError):
        services.transition_ticket(agent, t.pk, "in_progress")
    t.refresh_from_db()
    assert t.status == "open" and t.assigned_to is None  # el cambio se revirtió


# ---- asignación ---------------------------------------------------------------------
def test_assign_rules(as_user, agent, agent2, customer, make_ticket):
    t = make_ticket(customer)
    assert (
        as_user(customer)
        .post(f"/api/tickets/{t.pk}/assign/", {"assigned_to": agent.pk}, format="json")
        .status_code
        == 403
    )
    r = as_user(agent).post(f"/api/tickets/{t.pk}/assign/", {"assigned_to": agent2.pk}, format="json")
    assert r.status_code == 200 and r.json()["assigned_to"]["id"] == agent2.pk
    bad = as_user(agent).post(f"/api/tickets/{t.pk}/assign/", {"assigned_to": customer.pk}, format="json")
    assert bad.status_code == 400
    un = as_user(agent).post(f"/api/tickets/{t.pk}/assign/", {"assigned_to": None}, format="json")
    assert un.status_code == 200 and un.json()["assigned_to"] is None


# ---- comentarios y notas internas ---------------------------------------------------------
def test_internal_notes_are_hidden_from_customers(as_user, agent, customer, make_ticket):
    t = make_ticket(customer)
    as_user(agent).post(
        f"/api/tickets/{t.pk}/comments/", {"body": "Nota privada", "is_internal": True}, format="json"
    )
    as_user(agent).post(f"/api/tickets/{t.pk}/comments/", {"body": "Hola, lo revisamos"}, format="json")
    assert len(as_user(agent).get(f"/api/tickets/{t.pk}/comments/").json()) == 2
    seen = as_user(customer).get(f"/api/tickets/{t.pk}/comments/").json()
    assert [c["body"] for c in seen] == ["Hola, lo revisamos"]
    events = as_user(customer).get(f"/api/tickets/{t.pk}/events/").json()
    assert all(e["to_value"] != "internal" for e in events)


def test_customer_cannot_create_internal_note(as_user, customer, make_ticket):
    t = make_ticket(customer)
    r = as_user(customer).post(
        f"/api/tickets/{t.pk}/comments/", {"body": "x", "is_internal": True}, format="json"
    )
    assert r.status_code == 403 and Comment.objects.count() == 0


def test_customer_reply_returns_waiting_ticket_to_in_progress(as_user, agent, customer, make_ticket):
    from apps.tickets import services

    t = make_ticket(customer)
    services.transition_ticket(agent, t.pk, "in_progress")
    services.transition_ticket(agent, t.pk, "waiting_customer")
    as_user(customer).post(f"/api/tickets/{t.pk}/comments/", {"body": "Ya respondí"}, format="json")
    t.refresh_from_db()
    assert t.status == "in_progress"


def test_cannot_comment_on_closed_ticket_or_empty_body(as_user, customer, make_ticket):
    t = make_ticket(customer)
    c = as_user(customer)
    assert c.post(f"/api/tickets/{t.pk}/comments/", {"body": "   "}, format="json").status_code == 400
    c.post(f"/api/tickets/{t.pk}/transition/", {"status": "closed"}, format="json")
    assert c.post(f"/api/tickets/{t.pk}/comments/", {"body": "hola"}, format="json").status_code == 409


# ---- edición ----------------------------------------------------------------------
def test_edit_rules(as_user, agent, admin, customer, make_ticket):
    from apps.tickets import services

    t = make_ticket(customer)
    c = as_user(customer)
    assert c.patch(f"/api/tickets/{t.pk}/", {"title": "Nuevo título"}, format="json").status_code == 200
    assert c.patch(f"/api/tickets/{t.pk}/", {"priority": "urgent"}, format="json").status_code == 403
    a = as_user(agent)
    assert a.patch(f"/api/tickets/{t.pk}/", {"priority": "urgent"}, format="json").status_code == 200
    assert a.patch(f"/api/tickets/{t.pk}/", {"title": "Hack"}, format="json").status_code == 403
    assert (
        as_user(admin).patch(f"/api/tickets/{t.pk}/", {"title": "Corregido"}, format="json").status_code
        == 200
    )
    services.transition_ticket(agent, t.pk, "in_progress")
    assert c.patch(f"/api/tickets/{t.pk}/", {"title": "Tarde"}, format="json").status_code == 403
    assert "priority_changed" in list(t.events.values_list("event_type", flat=True))


# ---- filtros, búsqueda y stats ---------------------------------------------------------
def test_filters_search_and_stats(as_user, agent, agent2, customer, make_ticket):
    from apps.tickets import services

    a = make_ticket(customer, title="Factura duplicada", priority="high")
    b = make_ticket(customer, title="Error de login")
    services.transition_ticket(agent, a.pk, "in_progress")
    c = as_user(agent)
    assert [t["id"] for t in c.get("/api/tickets/?assigned_to=me").json()["results"]] == [a.pk]
    assert [t["id"] for t in c.get("/api/tickets/?assigned_to=unassigned").json()["results"]] == [b.pk]
    assert [t["id"] for t in c.get("/api/tickets/?search=factura").json()["results"]] == [a.pk]
    assert c.get("/api/tickets/?status=open&status=in_progress").json()["count"] == 2
    assert c.get("/api/tickets/?priority=high").json()["count"] == 1
    s = c.get("/api/tickets/stats/").json()
    assert s["by_status"]["open"] == 1 and s["by_status"]["in_progress"] == 1
    assert s["unassigned"] == 1 and s["mine"] == 1
    assert "unassigned" not in as_user(customer).get("/api/tickets/stats/").json()


def test_pagination_page_size_is_capped(as_user, agent, customer, make_ticket):
    for i in range(3):
        make_ticket(customer, title=f"T{i}")
    r = as_user(agent).get("/api/tickets/?page_size=1000")
    assert r.status_code == 200 and r.json()["count"] == 3


def test_list_query_count_does_not_grow_with_rows(as_user, agent, customer, make_ticket):
    c = as_user(agent)

    def count():
        with CaptureQueriesContext(connection) as ctx:
            assert c.get("/api/tickets/?page_size=50").status_code == 200
        return len(ctx)

    for i in range(3):
        make_ticket(customer, title=f"A{i}")
    small = count()
    for i in range(25):
        make_ticket(customer, title=f"B{i}")
    assert count() == small  # sin N+1


def test_health(api):
    assert api.get("/api/health/").json() == {"status": "ok", "database": "ok"}
