from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Event(models.Model):
    """A photo event. Guests reach its gallery via a per-event token/QR code.

    Photos + face index auto-expire after `retention_days` (PRIV-03, enforced by a
    Celery beat job in Phase 4).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
    )
    # Collaborators (EVENT-04/05) — invite flow ships in Phase 5; field defined now
    # to avoid a later schema migration.
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="collaborating_events",
        blank=True,
    )
    name = models.CharField(max_length=200)
    date = models.DateField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    retention_days = models.PositiveIntegerField(default=settings.DEFAULT_EVENT_RETENTION_DAYS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ("-date", "-created_at")

    def __str__(self) -> str:
        return f"{self.name} ({self.date})"

    def save(self, *args, **kwargs) -> None:
        # (Re)compute expiry from creation time + retention window.
        base = self.created_at or timezone.now()
        self.expires_at = base + timedelta(days=self.retention_days)
        super().save(*args, **kwargs)

    @property
    def guest_url(self) -> str:
        """The URL a guest lands on after scanning the QR code (SEARCH-01)."""
        return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/event/{self.token}"

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and timezone.now() >= self.expires_at

    def can_be_managed_by(self, user) -> bool:
        if user.is_superuser:
            return True
        return self.owner_id == user.id or self.collaborators.filter(pk=user.pk).exists()
