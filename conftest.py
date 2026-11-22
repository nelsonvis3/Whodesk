import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.knowledge import retrieval
from apps.tickets import services


@pytest.fixture(autouse=True)
def _clean_state(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # tests más rápidos
    cache.clear()  # reinicia los contadores de throttling entre tests
    retrieval.clear_cache()
    yield
    retrieval.clear_cache()


def _user(email, role, first="Test"):
    return User.objects.create_user(email, "pass-1234-xyz", first_name=first, last_name=role.label, role=role)


@pytest.fixture
def customer(db):
    return _user("cliente@test.com", Role.CUSTOMER, "Lucía")


@pytest.fixture
def customer2(db):
    return _user("cliente2@test.com", Role.CUSTOMER, "Diego")


@pytest.fixture
def agent(db):
    return _user("agente@test.com", Role.AGENT, "Martín")


@pytest.fixture
def agent2(db):
    return _user("agente2@test.com", Role.AGENT, "Sofía")


@pytest.fixture
def admin(db):
    return _user("admin@test.com", Role.ADMIN, "Ana")


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def as_user():
    def _make(user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    return _make


@pytest.fixture
def make_ticket():
    def _make(owner, title="No puedo entrar", description="Error al iniciar sesión", **kw):
        return services.create_ticket(owner, title=title, description=description, **kw)

    return _make
