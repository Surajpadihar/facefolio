from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_signup_creates_unapproved_user(api):
    res = api.post(
        "/api/auth/signup/",
        {"username": "carol", "email": "carol@example.com", "password": "pw-test-12345"},
        format="json",
    )
    assert res.status_code == 201
    from accounts.models import User

    u = User.objects.get(username="carol")
    assert u.is_approved is False
    assert u.can_upload is False


def test_login_returns_jwt(api, approved):
    res = api.post("/api/auth/login/", {"username": "alice", "password": "pw-test-12345"}, format="json")
    assert res.status_code == 200
    assert "access" in res.json() and "refresh" in res.json()


def test_unapproved_photographer_cannot_create_event(api, pending):
    api.force_authenticate(user=pending)
    res = api.post("/api/events/", {"name": "Party", "date": "2026-07-01"}, format="json")
    assert res.status_code == 403  # approval gate


def test_approved_photographer_can_create_event(api, approved):
    api.force_authenticate(user=approved)
    res = api.post("/api/events/", {"name": "Party", "date": "2026-07-01"}, format="json")
    assert res.status_code == 201
    assert res.json()["token"]
