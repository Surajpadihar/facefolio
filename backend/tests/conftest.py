from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture(autouse=True)
def _inmemory_storage(settings):
    """Avoid needing MinIO in tests — store files in memory."""
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture(autouse=True)
def _fast_throttles(settings):
    """Don't let rate limits interfere with tests."""
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_RATES": {"selfie": "1000/min", "auth": "1000/min"},
    }


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def approved(db):
    return User.objects.create_user(
        username="alice", email="alice@example.com", password="pw-test-12345", is_approved=True
    )


@pytest.fixture
def pending(db):
    return User.objects.create_user(
        username="bob", email="bob@example.com", password="pw-test-12345", is_approved=False
    )


@pytest.fixture
def superadmin(db):
    return User.objects.create_superuser(username="root", email="root@example.com", password="pw-test-12345")
