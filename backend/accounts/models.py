from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A FaceFolio user.

    Most users are photographers, who must be approved by a super-admin before
    they can create events or upload photos (AUTH-02). Super-admins are Django
    superusers and are implicitly approved.
    """

    email = models.EmailField("email address", unique=True)
    is_approved = models.BooleanField(
        default=False,
        help_text="Approved photographers can create events and upload. Set by a super-admin.",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    @property
    def can_upload(self) -> bool:
        """Superusers can always act; everyone else needs explicit approval."""
        return self.is_superuser or self.is_approved

    def __str__(self) -> str:
        return self.username
