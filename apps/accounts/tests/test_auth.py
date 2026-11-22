import pytest

from apps.accounts.models import Role, User

pytestmark = pytest.mark.django_db


def test_register_always_creates_customer_even_if_role_is_sent(api):
    r = api.post(
        "/api/auth/register/",
        {"email": "nuevo@test.com", "password": "S3gura-clave-99", "first_name": "Nuevo", "role": "admin"},
        format="json",
    )
    assert r.status_code == 201
    assert User.objects.get(email="nuevo@test.com").role == Role.CUSTOMER
    assert r.json()["role"] == "customer"


def test_register_rejects_duplicate_email_and_weak_password(api, customer):
    r = api.post(
        "/api/auth/register/", {"email": customer.email, "password": "S3gura-clave-99"}, format="json"
    )
    assert r.status_code == 400 and "email" in r.json()
    r = api.post("/api/auth/register/", {"email": "otro@test.com", "password": "123"}, format="json")
    assert r.status_code == 400


def test_login_logout_and_me_with_session(api, customer):
    assert api.get("/api/users/me/").status_code == 401
    bad = api.post("/api/auth/login/", {"email": customer.email, "password": "mala"}, format="json")
    assert bad.status_code == 401
    ok = api.post("/api/auth/login/", {"email": customer.email, "password": "pass-1234-xyz"}, format="json")
    assert ok.status_code == 200
    assert api.get("/api/users/me/").json()["email"] == customer.email
    assert api.post("/api/auth/logout/").status_code == 204
    assert api.get("/api/users/me/").status_code == 401


def test_jwt_token_flow_for_external_clients(api, customer):
    r = api.post("/api/auth/token/", {"email": customer.email, "password": "pass-1234-xyz"}, format="json")
    assert r.status_code == 200 and {"access", "refresh"} <= set(r.json())
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['access']}")
    assert api.get("/api/users/me/").json()["email"] == customer.email
    refreshed = api.post("/api/auth/token/refresh/", {"refresh": r.json()["refresh"]}, format="json")
    assert refreshed.status_code == 200


def test_login_is_case_insensitive_on_email(api, customer):
    r = api.post(
        "/api/auth/login/", {"email": customer.email.upper(), "password": "pass-1234-xyz"}, format="json"
    )
    assert r.status_code == 200


def test_staff_list_only_for_staff(as_user, customer, agent, admin):
    assert as_user(customer).get("/api/users/staff/").status_code == 403
    r = as_user(agent).get("/api/users/staff/")
    assert r.status_code == 200
    assert {u["role"] for u in r.json()} <= {"agent", "admin"}


def test_login_is_throttled(api, customer, settings):
    from rest_framework.throttling import ScopedRateThrottle

    ScopedRateThrottle.THROTTLE_RATES = {**ScopedRateThrottle.THROTTLE_RATES, "auth": "3/min"}
    try:
        codes = [
            api.post(
                "/api/auth/login/", {"email": customer.email, "password": "mala"}, format="json"
            ).status_code
            for _ in range(5)
        ]
    finally:
        ScopedRateThrottle.THROTTLE_RATES = {**ScopedRateThrottle.THROTTLE_RATES, "auth": "30/min"}
    assert codes[:3] == [401, 401, 401] and 429 in codes[3:]
