from __future__ import annotations

from rest_framework import serializers

from .models import Photo
from .storage import public_presigned_get


class PhotoSerializer(serializers.ModelSerializer):
    original_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    face_count = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = (
            "id",
            "event",
            "status",
            "original_filename",
            "width",
            "height",
            "original_url",
            "thumbnail_url",
            "face_count",
            "error",
            "created_at",
        )
        read_only_fields = fields

    def get_face_count(self, obj: Photo) -> int:
        # Uses the prefetched/annotated count when available, else falls back to a query.
        return getattr(obj, "face_count", None) or obj.faces.count()

    def get_original_url(self, obj: Photo) -> str | None:
        return public_presigned_get(obj.original.name) if obj.original else None

    def get_thumbnail_url(self, obj: Photo) -> str | None:
        return public_presigned_get(obj.thumbnail.name) if obj.thumbnail else None
