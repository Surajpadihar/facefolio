from __future__ import annotations

from django.db import models
from pgvector.django import HnswIndex, VectorField

from events.models import Event
from photos.models import Photo

# buffalo_l (ArcFace) produces 512-dimensional L2-normalized embeddings.
EMBEDDING_DIM = 512


class FaceEmbedding(models.Model):
    """One detected face in one photo (INDEX-02: a photo with N faces → N rows).

    ``event`` is denormalized from ``photo.event`` so similarity search can filter
    by event cheaply and so the HNSW index traversal stays within one event's faces.

    Embeddings are L2-normalized, so cosine similarity == inner product. We use the
    inner-product opclass (``vector_ip_ops``) and MUST query with the matching ``<#>``
    operator — a mismatch silently falls back to a sequential scan.
    """

    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="faces")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="faces")
    embedding = VectorField(dimensions=EMBEDDING_DIM)
    bbox = models.JSONField(help_text="[x1, y1, x2, y2] in original-image pixels")
    det_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["event"], name="faceemb_event_idx"),
            HnswIndex(
                name="faceemb_hnsw_ip",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_ip_ops"],
            ),
        ]

    def __str__(self) -> str:
        return f"face#{self.pk} of photo#{self.photo_id}"
