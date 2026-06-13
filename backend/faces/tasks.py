"""Face indexing task (INDEX-01). Runs after thumbnailing; advances READY → INDEXED."""

from __future__ import annotations

from celery import shared_task

from .engine import detect_faces, load_rgb


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def index_photo(self, photo_id: int) -> str:
    """Detect every face in a photo and store one embedding row per face, scoped to the event."""
    from photos.models import Photo

    from .models import FaceEmbedding

    try:
        photo = Photo.objects.select_related("event").get(pk=photo_id)
    except Photo.DoesNotExist:
        return "missing"

    photo.status = Photo.Status.PROCESSING
    photo.save(update_fields=["status", "updated_at"])

    try:
        photo.original.open("rb")
        rgb = load_rgb(photo.original)
        faces = detect_faces(rgb)

        # Idempotent: clear any prior embeddings so re-indexing doesn't duplicate.
        FaceEmbedding.objects.filter(photo=photo).delete()
        FaceEmbedding.objects.bulk_create(
            [
                FaceEmbedding(
                    photo=photo,
                    event_id=photo.event_id,
                    embedding=f["embedding"],
                    bbox=f["bbox"],
                    det_score=f["det_score"],
                )
                for f in faces
            ]
        )

        photo.status = Photo.Status.INDEXED
        photo.error = ""
        photo.save(update_fields=["status", "error", "updated_at"])
        return f"indexed:{len(faces)}"
    except Exception as exc:  # noqa: BLE001 — record failure, never leave a silent unknown state
        photo.status = Photo.Status.FAILED
        photo.error = str(exc)[:2000]
        photo.save(update_fields=["status", "error", "updated_at"])
        raise
    finally:
        photo.original.close()
