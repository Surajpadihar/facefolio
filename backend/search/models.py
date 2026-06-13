from __future__ import annotations

import uuid

from django.db import models

from events.models import Event

# Bump when the consent notice text changes materially (record what the guest agreed to).
CONSENT_NOTICE_VERSION = "2026-06-13"


class ConsentRecord(models.Model):
    """Proof that a guest accepted the biometric consent notice before selfie capture (PRIV-01).

    Stores NO biometric data — only that consent was given, for which event, and when.
    The ``consent_id`` is handed to the client and must be presented to run a search.
    """

    consent_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="consents")
    notice_version = models.CharField(max_length=32, default=CONSENT_NOTICE_VERSION)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-accepted_at",)

    def __str__(self) -> str:
        return f"consent {self.consent_id} for event {self.event_id}"
