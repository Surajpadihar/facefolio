"""Periodic retention enforcement (PRIV-03)."""

from __future__ import annotations

from celery import shared_task
from django.utils import timezone


@shared_task
def purge_expired_events() -> str:
    """Delete events past their retention window, including MinIO objects + face embeddings.

    Photos are deleted one-by-one so Photo.delete() removes the underlying MinIO objects;
    FaceEmbedding rows cascade at the DB level.
    """
    from events.models import Event

    expired = Event.objects.filter(expires_at__lte=timezone.now())
    n_events = 0
    n_photos = 0
    for event in expired:
        for photo in event.photos.all():
            photo.delete()  # removes original + thumbnail from MinIO
            n_photos += 1
        event.delete()
        n_events += 1
    return f"purged {n_events} event(s), {n_photos} photo(s)"
