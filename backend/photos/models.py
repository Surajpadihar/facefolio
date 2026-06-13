from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from events.models import Event


def photo_upload_path(instance: Photo, filename: str) -> str:
    """Originals live under the event's token namespace in MinIO."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"events/{instance.event.token}/originals/{uuid.uuid4()}.{ext}"


def thumb_upload_path(instance: Photo, filename: str) -> str:
    return f"events/{instance.event.token}/thumbs/{uuid.uuid4()}.jpg"


class Photo(models.Model):
    """A photo uploaded to an event.

    The status field makes the upload→processing pipeline observable (UPLOAD-03):
    a photo is never left in a silent/unknown state. Face indexing (Phase 3)
    advances READY → INDEXED.
    """

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready (thumbnail generated)"
        INDEXED = "indexed", "Indexed (faces embedded)"
        FAILED = "failed", "Failed"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="photos")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_photos",
    )
    original = models.ImageField(upload_to=photo_upload_path)
    thumbnail = models.ImageField(upload_to=thumb_upload_path, null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPLOADED)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["event", "status"])]

    def __str__(self) -> str:
        return f"{self.original_filename or self.pk} ({self.status})"

    def delete(self, *args, **kwargs):
        """Remove the underlying MinIO objects when the row is deleted (UPLOAD-04).

        Face embeddings (Phase 3) are removed via FK cascade on the DB side.
        """
        for field in (self.original, self.thumbnail):
            if field:
                field.delete(save=False)
        super().delete(*args, **kwargs)
