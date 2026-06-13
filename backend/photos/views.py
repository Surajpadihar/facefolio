from __future__ import annotations

from django.db.models import Q
from rest_framework import mixins, viewsets

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
    also removes its MinIO objects and (Phase 3) its face embeddings (UPLOAD-04).
    """

    serializer_class = PhotoSerializer
    permission_classes = [IsApprovedPhotographer]

    def get_queryset(self):
        user = self.request.user
        qs = Photo.objects.select_related("event")
        if not user.is_superuser:
            qs = qs.filter(Q(event__owner=user) | Q(event__collaborators=user)).distinct()
        event_id = self.request.query_params.get("event")
        if event_id:
            qs = qs.filter(event_id=event_id)
        return qs
