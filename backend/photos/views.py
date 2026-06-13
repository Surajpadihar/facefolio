from __future__ import annotations

from django.db.models import Count, Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsApprovedPhotographer

from .models import Photo
from .serializers import PhotoSerializer


class PhotoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """List / retrieve / delete photos, scoped to events the user owns or collaborates on.

    Batch upload lives on the event (POST /api/events/{id}/upload/). Deleting a photo
    also removes its MinIO objects and its face embeddings (UPLOAD-04).
    """

    serializer_class = PhotoSerializer
    permission_classes = [IsApprovedPhotographer]

    def get_queryset(self):
        user = self.request.user
        qs = Photo.objects.select_related("event").annotate(face_count=Count("faces"))
        if not user.is_superuser:
            qs = qs.filter(Q(event__owner=user) | Q(event__collaborators=user)).distinct()
        event_id = self.request.query_params.get("event")
        if event_id:
            qs = qs.filter(event_id=event_id)
        return qs

    @action(detail=True, methods=["post"], url_path="reindex")
    def reindex(self, request, pk=None) -> Response:
        """POST /api/photos/{id}/reindex/ — re-run face detection on this photo (ADMIN-03)."""
        from faces.tasks import index_photo

        photo = self.get_object()
        index_photo.delay(photo.pk)
        return Response({"detail": "reindex queued", "photo": photo.pk})
