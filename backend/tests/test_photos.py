from __future__ import annotations

import io

import pytest
from PIL import Image

pytestmark = pytest.mark.django_db


def _png_bytes(size=(50, 50)):
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 80, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _upload(api, content_type="image/png", name="p.png", data=None):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, data or _png_bytes(), content_type=content_type)


@pytest.fixture
def event(api, approved):
    api.force_authenticate(user=approved)
    return api.post("/api/events/", {"name": "Ev", "date": "2026-07-01"}, format="json").json()


def test_batch_upload_creates_photos(api, approved, event, monkeypatch):
    monkeypatch.setattr("photos.tasks.process_photo.delay", lambda *a, **k: None)
    api.force_authenticate(user=approved)
    res = api.post(
        f"/api/events/{event['id']}/upload/",
        {"files": [_upload(api), _upload(api, name="q.png")]},
        format="multipart",
    )
    assert res.status_code == 201
    assert len(res.json()["created"]) == 2


def test_non_image_rejected(api, approved, event, monkeypatch):
    monkeypatch.setattr("photos.tasks.process_photo.delay", lambda *a, **k: None)
    api.force_authenticate(user=approved)
    bad = _upload(api, content_type="text/plain", name="x.txt", data=b"nope")
    res = api.post(f"/api/events/{event['id']}/upload/", {"files": [bad]}, format="multipart")
    assert res.status_code == 400
    assert res.json()["rejected"]


def test_batch_cap_enforced(api, approved, event, settings, monkeypatch):
    monkeypatch.setattr("photos.tasks.process_photo.delay", lambda *a, **k: None)
    settings.MAX_UPLOAD_BATCH = 2
    api.force_authenticate(user=approved)
    files = [_upload(api, name=f"{i}.png") for i in range(3)]
    res = api.post(f"/api/events/{event['id']}/upload/", {"files": files}, format="multipart")
    assert res.status_code == 400
    assert "at a time" in res.json()["detail"]
