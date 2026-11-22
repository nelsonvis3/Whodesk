from io import StringIO

import pytest
from django.conf import settings
from django.core.management import call_command

from apps.tickets.models import Ticket

pytestmark = pytest.mark.django_db


def test_seed_demo_is_idempotent_and_builds_realistic_history():
    call_command("seed_demo", stdout=StringIO())
    n = Ticket.objects.count()
    assert n >= 10
    out = StringIO()
    call_command("seed_demo", stdout=out)  # segunda corrida: no duplica
    assert Ticket.objects.count() == n and "Ya hay datos" in out.getvalue()
    states = set(Ticket.objects.values_list("status", flat=True))
    assert {"open", "in_progress", "resolved", "closed"} <= states


def test_eval_rag_quality_regression_guard(settings):
    """Si cambia el texto, el stemming o el índice y la recuperación empeora, este test lo avisa."""
    call_command("seed_demo", stdout=StringIO())
    out = StringIO()
    call_command("eval_rag", file=str(settings.BASE_DIR / "eval" / "questions.jsonl"), stdout=out)
    text = out.getvalue()
    hit1 = float(text.split("Hit@1: ")[1].split("%")[0]) / 100
    hit3 = float(text.split("Hit@3: ")[1].split("%")[0]) / 100
    assert hit1 >= 0.85 and hit3 >= 0.95, text
    assert settings.ASSISTANT_MIN_SCORE == 2.5 and settings.BASE_DIR.name


def test_category_change_is_audited(as_user, agent, customer, make_ticket):
    from apps.tickets.models import Category

    cat = Category.objects.create(name="Facturación")
    t = make_ticket(customer)
    r = as_user(agent).patch(f"/api/tickets/{t.pk}/", {"category": cat.pk}, format="json")
    assert r.status_code == 200 and r.json()["category"]["name"] == "Facturación"
    assert "category_changed" in list(t.events.values_list("event_type", flat=True))
    r = as_user(agent).patch(f"/api/tickets/{t.pk}/", {"category": None}, format="json")
    assert r.json()["category"] is None


def test_settings_dir_exists():
    assert (settings.BASE_DIR / "eval" / "questions.jsonl").exists()
