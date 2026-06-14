from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def _make_event(api, user, name="Wedding"):
    api.force_authenticate(user=user)
    return api.post("/api/events/", {"name": name, "date": "2026-07-01"}, format="json").json()


def test_event_has_unique_token_and_qr(api, approved):
    ev = _make_event(api, approved)
    assert ev["token"] and ev["qr_code_url"].endswith(f"/api/events/{ev['id']}/qr/")
    res = api.get(f"/api/events/{ev['id']}/qr/")
    assert res.status_code == 200 and res["Content-Type"] == "image/png"


def test_events_are_scoped_to_owner(api, approved, pending):
    ev = _make_event(api, approved)
    # a different (approved) user shouldn't see alice's event
    pending.is_approved = True
    pending.save()
    api.force_authenticate(user=pending)
    listing = api.get("/api/events/").json()
    rows = listing if isinstance(listing, list) else listing["results"]
    assert ev["id"] not in [e["id"] for e in rows]


def test_collaborator_flow(api, approved, pending):
    pending.is_approved = True
    pending.save()
    ev = _make_event(api, approved)

    # owner adds collaborator
    api.force_authenticate(user=approved)
    res = api.post(f"/api/events/{ev['id']}/collaborators/", {"username": "bob"}, format="json")
    assert res.status_code == 200 and "bob" in res.json()["collaborators"]

    # collaborator can now see the event
    api.force_authenticate(user=pending)
    rows = api.get("/api/events/").json()
    rows = rows if isinstance(rows, list) else rows["results"]
    assert ev["id"] in [e["id"] for e in rows]

    # collaborator (non-owner) cannot manage collaborators
    res = api.post(f"/api/events/{ev['id']}/collaborators/", {"username": "root"}, format="json")
    assert res.status_code == 403
