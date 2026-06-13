"""Background photo processing.

Phase 2 generates a thumbnail and records dimensions. Phase 3 will add a
``index_photo`` task that detects faces and writes embeddings, advancing the
photo READY → INDEXED.
"""

from __future__ import annotations

import io

from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

THUMBNAIL_MAX = (600, 600)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def process_photo(self, photo_id: int) -> str:
    """Generate a thumbnail + record dimensions for a freshly uploaded photo (UPLOAD-03)."""
    from .models import Photo

    try:
        photo = Photo.objects.get(pk=photo_id)
    except Photo.DoesNotExist:
        return "missing"

    photo.status = Photo.Status.PROCESSING
    photo.save(update_fields=["status", "updated_at"])

    try:
        photo.original.open("rb")
        with Image.open(photo.original) as img:
            # Respect EXIF orientation so portrait/rotated photos render correctly.
            img = ImageOps.exif_transpose(img)
            photo.width, photo.height = img.size

            thumb = img.convert("RGB")
            thumb.thumbnail(THUMBNAIL_MAX)
            buffer = io.BytesIO()
            thumb.save(buffer, format="JPEG", quality=85)

        photo.thumbnail.save(f"{photo.pk}.jpg", ContentFile(buffer.getvalue()), save=False)
        photo.status = Photo.Status.READY
        photo.error = ""
        photo.save(update_fields=["thumbnail", "width", "height", "status", "error", "updated_at"])
        return "ready"
    except Exception as exc:  # noqa: BLE001 — record failure, never leave a silent unknown state
        photo.status = Photo.Status.FAILED
        photo.error = str(exc)[:2000]
        photo.save(update_fields=["status", "error", "updated_at"])
        raise
    finally:
        photo.original.close()
