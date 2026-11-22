import httpx
import pytest

from apps.knowledge.models import KnowledgeArticle, RagQuery
from apps.tickets import services as tsvc

pytestmark = pytest.mark.django_db


@pytest.fixture
def articles(db, settings):
    settings.ASSISTANT_MIN_SCORE = 0.5  # corpus de 3-4 fragmentos: el umbral de producción (2.5) no aplica
    KnowledgeArticle.objects.create(
        title="Cómo restablecer tu contraseña",
        body="Elegí «Olvidé mi contraseña» e ingresá tu email. El enlace vence a los 30 minutos.",
    )
    KnowledgeArticle.objects.create(
        title="Exportar tus datos a CSV",
        body="Andá a Reportes > Exportar. Cada exportación admite hasta 50.000 filas.",
    )
    KnowledgeArticle.objects.create(
        title="Procedimiento interno de reembolsos",
        is_public=False,
        body="Los reembolsos los aprueba un administrador. Secreto interno zafiro.",
    )
    KnowledgeArticle.objects.create(
        title="Artículo dado de baja", is_active=False, body="Contenido inactivo sobre contraseña olvidada."
    )


class FakeResponse:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self):
        return self._data


# ---- recuperación y abstención ---------------------------------------------------------
def test_answers_from_public_articles_with_sources(as_user, customer, articles):
    r = as_user(customer).post("/api/assistant/ask/", {"question": "olvidé mi clave"}, format="json")
    assert r.status_code == 200
    data = r.json()
    assert not data["abstained"] and data["mode"] == "extractive"
    assert data["sources"][0]["title"] == "Cómo restablecer tu contraseña"
    assert "30 minutos" in data["answer"]


def test_production_threshold_abstains_on_weak_matches(as_user, customer, articles, settings):
    settings.ASSISTANT_MIN_SCORE = 50  # umbral inalcanzable: toda consulta se abstiene
    data = (
        as_user(customer)
        .post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json")
        .json()
    )
    assert data["abstained"]


def test_abstains_when_nothing_relevant(as_user, customer, articles):
    data = (
        as_user(customer)
        .post("/api/assistant/ask/", {"question": "receta de milanesas"}, format="json")
        .json()
    )
    assert data["abstained"] and data["sources"] == []
    assert "No encontré información suficiente" in data["answer"]


def test_customers_never_get_private_or_inactive_articles(as_user, customer, agent, articles):
    q = {"question": "reembolsos secreto interno zafiro"}
    cust = as_user(customer).post("/api/assistant/ask/", q, format="json").json()
    assert all("reembolsos" not in s["title"].lower() for s in cust["sources"])
    assert "zafiro" not in cust["answer"]
    staff = as_user(agent).post("/api/assistant/ask/", q, format="json").json()
    assert any("reembolsos" in s["title"].lower() for s in staff["sources"])
    inactive = (
        as_user(agent).post("/api/assistant/ask/", {"question": "contraseña olvidada"}, format="json").json()
    )
    assert all(s["title"] != "Artículo dado de baja" for s in inactive["sources"])


def test_customer_audience_never_includes_tickets(as_user, customer, customer2, agent, articles, make_ticket):
    t = make_ticket(customer2, title="Problema de exportación de reportes")
    tsvc.transition_ticket(agent, t.pk, "in_progress")
    tsvc.transition_ticket(agent, t.pk, "resolved", "Se resolvió dividiendo la exportación por fechas")
    q = {"question": "problema exportación dividiendo por fechas"}
    cust = as_user(customer).post("/api/assistant/ask/", q, format="json").json()
    assert all(s["type"] == "article" for s in cust["sources"])
    staff = as_user(agent).post("/api/assistant/ask/", q, format="json").json()
    assert any(s["type"] == "ticket" for s in staff["sources"])


def test_ticket_corpus_uses_resolution_note_not_customer_description(
    as_user, agent, customer, make_ticket, articles
):
    t = make_ticket(customer, title="Consulta", description="Mi DNI es 12345678 y vivo en Calle Falsa 123")
    tsvc.transition_ticket(agent, t.pk, "in_progress")
    tsvc.transition_ticket(agent, t.pk, "resolved", "Se verificó la identidad por email")
    from apps.knowledge import retrieval

    chunks = retrieval.build_index("agent").chunks
    assert not any("12345678" in c.text for c in chunks)


def test_empty_question_is_400(as_user, customer, articles):
    assert as_user(customer).post("/api/assistant/ask/", {"question": "   "}, format="json").status_code in (
        400,
    )


# ---- sugerencia para agentes ---------------------------------------------------------------
def test_suggest_reply_only_for_staff_and_excludes_own_ticket(
    as_user, customer, agent, articles, make_ticket
):
    t = make_ticket(customer, title="No puedo restablecer la contraseña", description="El enlace no llega")
    assert as_user(customer).post(f"/api/tickets/{t.pk}/suggest-reply/").status_code == 403
    r = as_user(agent).post(f"/api/tickets/{t.pk}/suggest-reply/")
    assert r.status_code == 200 and not r.json()["abstained"]
    assert r.json()["answer"].startswith("Hola Lucía")
    tsvc.transition_ticket(agent, t.pk, "in_progress")
    tsvc.transition_ticket(agent, t.pk, "resolved", "Restablecer contraseña: enlace de 30 minutos")
    again = as_user(agent).post(f"/api/tickets/{t.pk}/suggest-reply/").json()
    assert all(not (s["type"] == "ticket" and s["id"] == t.pk) for s in again["sources"])


# ---- proveedor LLM ---------------------------------------------------------------------
def test_llm_provider_success_and_prompt_marks_content_as_untrusted(
    as_user, customer, articles, settings, monkeypatch
):
    settings.LLM_PROVIDER, settings.LLM_API_KEY, settings.LLM_MODEL = "anthropic", "k", "modelo-x"
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.update(url=url, json=json, headers=headers)
        return FakeResponse(
            {"content": [{"type": "text", "text": "Podés restablecerla desde el enlace [1]."}]}
        )

    monkeypatch.setattr("apps.knowledge.llm.httpx.post", fake_post)
    data = (
        as_user(customer)
        .post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json")
        .json()
    )
    assert data["mode"] == "llm" and data["answer"].startswith("Podés restablecerla")
    assert "no confiable" in seen["json"]["system"] and "SOLO el contexto" in seen["json"]["system"]
    assert "30 minutos" in seen["json"]["messages"][0]["content"]
    assert seen["headers"]["x-api-key"] == "k"
    rq = RagQuery.objects.get()
    assert rq.used_llm and rq.provider == "anthropic" and rq.generation_ms >= 0


def test_openai_compatible_provider(as_user, customer, articles, settings, monkeypatch):
    settings.LLM_PROVIDER, settings.LLM_API_KEY, settings.LLM_MODEL = "openai", "k", "m"
    settings.LLM_BASE_URL = "https://api.example.com/v1/"
    seen = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen["url"] = url
        return FakeResponse({"choices": [{"message": {"content": "Respuesta generada"}}]})

    monkeypatch.setattr("apps.knowledge.llm.httpx.post", fake_post)
    data = (
        as_user(customer)
        .post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json")
        .json()
    )
    assert (
        data["answer"] == "Respuesta generada"
        and seen["url"] == "https://api.example.com/v1/chat/completions"
    )


def test_provider_failure_falls_back_to_extractive(as_user, customer, articles, settings, monkeypatch):
    settings.LLM_PROVIDER, settings.LLM_API_KEY, settings.LLM_MODEL = "anthropic", "k", "m"

    def fail(*a, **k):
        raise httpx.ConnectTimeout("timeout")

    monkeypatch.setattr("apps.knowledge.llm.httpx.post", fail)
    r = as_user(customer).post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json")
    data = r.json()
    assert r.status_code == 200 and data["mode"] == "extractive" and data["notice"]
    assert "30 minutos" in data["answer"]


def test_missing_api_key_uses_extractive_mode(as_user, customer, articles, settings):
    settings.LLM_PROVIDER, settings.LLM_API_KEY, settings.LLM_MODEL = "anthropic", "", ""
    data = (
        as_user(customer)
        .post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json")
        .json()
    )
    assert data["mode"] == "extractive"


def test_daily_limit_applies_to_llm_queries(as_user, customer, articles, settings, monkeypatch):
    settings.LLM_PROVIDER, settings.LLM_API_KEY, settings.LLM_MODEL = "anthropic", "k", "m"
    settings.ASSISTANT_DAILY_LIMIT = 1
    monkeypatch.setattr(
        "apps.knowledge.llm.httpx.post",
        lambda *a, **k: FakeResponse({"content": [{"type": "text", "text": "ok"}]}),
    )
    c = as_user(customer)
    assert (
        c.post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json").status_code == 200
    )
    assert (
        c.post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json").status_code == 429
    )


# ---- búsqueda, feedback y artículos --------------------------------------------------------
def test_search_endpoint_returns_articles_without_llm(as_user, customer, articles):
    r = as_user(customer).get("/api/assistant/search/?q=no puedo exportar datos")
    assert r.status_code == 200 and r.json()["results"][0]["title"] == "Exportar tus datos a CSV"
    assert as_user(customer).get("/api/assistant/search/?q=ab").json()["results"] == []
    assert RagQuery.objects.count() == 0


def test_feedback_only_for_owner_and_valid_values(as_user, customer, customer2, articles):
    qid = (
        as_user(customer)
        .post("/api/assistant/ask/", {"question": "olvidé mi contraseña"}, format="json")
        .json()["query_id"]
    )
    url = f"/api/assistant/queries/{qid}/feedback/"
    assert as_user(customer2).post(url, {"value": 1}, format="json").status_code == 403
    assert as_user(customer).post(url, {"value": 5}, format="json").status_code == 400
    assert as_user(customer).post(url, {"value": -1}, format="json").status_code == 204
    assert RagQuery.objects.get(pk=qid).feedback == -1


def test_article_permissions(as_user, customer, agent, admin, articles):
    c = as_user(customer)
    assert {a["title"] for a in c.get("/api/knowledge/articles/").json()["results"]} == {
        "Cómo restablecer tu contraseña",
        "Exportar tus datos a CSV",
    }
    payload = {"title": "Nuevo", "body": "Cuerpo", "is_public": True}
    assert as_user(agent).post("/api/knowledge/articles/", payload, format="json").status_code == 403
    assert c.post("/api/knowledge/articles/", payload, format="json").status_code == 403
    r = as_user(admin).post("/api/knowledge/articles/", payload, format="json")
    assert r.status_code == 201
    # el índice se actualiza solo cuando cambia el contenido
    data = c.post("/api/assistant/ask/", {"question": "nuevo cuerpo"}, format="json").json()
    assert data["sources"] and data["sources"][0]["title"] == "Nuevo"
