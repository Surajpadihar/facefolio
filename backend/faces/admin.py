from __future__ import annotations

from django.contrib import admin

from .models import FaceEmbedding


@admin.register(FaceEmbedding)
class FaceEmbeddingAdmin(admin.ModelAdmin):
    list_display = ("id", "photo", "event", "det_score", "created_at")
    list_filter = ("event",)
    readonly_fields = ("photo", "event", "bbox", "det_score", "created_at")

    def has_add_permission(self, request) -> bool:
        return False  # embeddings are produced by the indexing task only
