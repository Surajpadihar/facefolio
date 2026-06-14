from __future__ import annotations

import io
import math

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

pytestmark = pytest.mark.django_db

DIM = 512


def unit_vector(idx: int) -> list[float]:
    """A unit-norm 512-d basis vector (1.0 at `idx`). Two different idx are orthogonal,
    so inner-product similarity is exactly 1.0 (same) or 0.0 (different) — unambiguous."""
    v = [0.0] * DIM
    v[idx % DIM] = 1.0
    return v


def partial_vector(sim: float) -> list[float]:
    """A unit vector whose inner product with unit_vector(0) is exactly `sim`."""
    v = [0.0] * DIM
    v[0] = sim
    v[1] = math.sqrt(max(0.0, 1.0 - sim * sim))
    return v


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (40, 40), (10, 10, 10)).save(buf, format="PNG")
    return SimpleUploadedFile("selfie.png", buf.getvalue(), content_type="image/png")


@pytest.fixture
def indexed_event(approved):
    """An event with one INDEXED photo carrying a known face embedding."""
    from django.core.files.base import ContentFile

    from events.models import Event
    from faces.models import FaceEmbedding
    from photos.models import Photo

    ev = Event.objects.create(owner=approved, name="Gala", date="2026-07-01")
    photo = Photo.objects.create(
        event=ev,
        uploaded_by=approved,
        original=ContentFile(b"x", name="o.jpg"),
        original_filename="o.jpg",
        status=Photo.Status.INDEXED,
    )
    face_vec = unit_vector(0)
    FaceEmbedding.objects.create(photo=photo, event=ev, embedding=face_vec, bbox=[1, 2, 3, 4], det_score=0.9)
    return ev, photo, face_vec


def _consent(api, token):
    return api.post(f"/api/public/events/{token}/consent/").json()["consent_id"]


def _mock_engine(monkeypatch, embedding):
    monkeypatch.setattr("search.views.load_rgb", lambda f: object())
    monkeypatch.setattr(
        "search.views.detect_faces",
        lambda img: [{"embedding": embedding, "bbox": [0, 0, 10, 10], "det_score": 0.95}] if embedding else [],
    )


def test_search_requires_consent(api, indexed_event, monkeypatch):
    ev, _, vec = indexed_event
    _mock_engine(monkeypatch, vec)
    res = api.post(f"/api/public/events/{ev.token}/search/", {"selfie": _png()}, format="multipart")
    assert res.status_code == 403  # no consent


def test_matching_selfie_finds_the_photo(api, indexed_event, monkeypatch):
    ev, photo, vec = indexed_event
    _mock_engine(monkeypatch, vec)
    cid = _consent(api, ev.token)
    res = api.post(f"/api/public/events/{ev.token}/search/", {"selfie": _png(), "consent_id": cid}, format="multipart")
    assert res.status_code == 200
    body = res.json()
    assert body["match_count"] >= 1
    assert photo.id in [m["id"] for m in body["matches"]]


def test_selfie_embedding_is_never_persisted(api, indexed_event, monkeypatch):
    """PRIV-02 — the guest's face embedding must not be written to the DB."""
    from faces.models import FaceEmbedding

    ev, _, vec = indexed_event
    _mock_engine(monkeypatch, vec)
    cid = _consent(api, ev.token)
    before = FaceEmbedding.objects.count()
    api.post(f"/api/public/events/{ev.token}/search/", {"selfie": _png(), "consent_id": cid}, format="multipart")
    assert FaceEmbedding.objects.count() == before  # unchanged → selfie not stored


def test_no_face_in_selfie(api, indexed_event, monkeypatch):
    ev, _, _ = indexed_event
    _mock_engine(monkeypatch, None)  # detect_faces -> []
    cid = _consent(api, ev.token)
    res = api.post(f"/api/public/events/{ev.token}/search/", {"selfie": _png(), "consent_id": cid}, format="multipart")
    assert res.status_code == 200 and res.json().get("no_face_detected") is True


def test_stranger_selfie_no_match(api, indexed_event, monkeypatch):
    ev, _, _ = indexed_event
    _mock_engine(monkeypatch, unit_vector(300))  # very different face
    cid = _consent(api, ev.token)
    res = api.post(f"/api/public/events/{ev.token}/search/", {"selfie": _png(), "consent_id": cid}, format="multipart")
    assert res.status_code == 200 and res.json()["no_match"] is True


def test_low_confidence_lands_in_maybe_tier(api, indexed_event, monkeypatch):
    ev, _, _ = indexed_event
    _mock_engine(monkeypatch, partial_vector(0.28))  # between maybe (0.22) and match (0.35)
    cid = _consent(api, ev.token)
    body = api.post(
        f"/api/public/events/{ev.token}/search/", {"selfie": _png(), "consent_id": cid}, format="multipart"
    ).json()
    assert body["match_count"] == 0
    assert body["maybe_count"] >= 1
    assert body["no_match"] is False
