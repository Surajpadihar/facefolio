from __future__ import annotations

from rest_framework import serializers

from photos.models import Photo
from photos.storage import public_presigned_get


class PublicPhotoSerializer(serializers.ModelSerializer):
    """A photo as a guest sees it — thumbnail + original presigned URLs, no internal fields."""

    thumbnail_url = serializers.SerializerMethodField()
    original_url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ("id", "thumbnail_url", "original_url", "width", "height")
        read_only_fields = fields

    def get_thumbnail_url(self, obj: Photo) -> str | None:
        return public_presigned_get(obj.thumbnail.name) if obj.thumbnail else None

    def get_original_url(self, obj: Photo) -> str | None:
        return public_presigned_get(obj.original.name) if obj.original else None


class MatchSerializer(PublicPhotoSerializer):
    """A matched photo plus the confidence score and matched-face box for display."""

    score = serializers.FloatField(read_only=True)
    bbox = serializers.SerializerMethodField()

    class Meta(PublicPhotoSerializer.Meta):
        fields = (*PublicPhotoSerializer.Meta.fields, "score", "bbox")
        read_only_fields = fields

    def get_bbox(self, obj):
        # Relative [x1, y1, x2, y2] (0..1) of the matched face, set by the search view.
        return getattr(obj, "match_bbox", None)
