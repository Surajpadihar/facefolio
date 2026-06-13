from __future__ import annotations

import io

import qrcode
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from accounts.permissions import IsApprovedPhotographer

from .models import Event
from .serializers import EventSerializer

# Accepted image content types for upload.
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class EventViewSet(viewsets.ModelViewSet):
    """CRUD for events. Only approved photographers, scoped to events they own or collaborate on.

    Covers EVENT-01 (create), EVENT-02 (unique token/QR), EVENT-03 (QR PNG export).
    """

    serializer_class = EventSerializer
    permission_classes = [IsApprovedPhotographer]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Event.objects.all()
        return Event.objects.filter(Q(owner=user) | Q(collaborators=user)).distinct()

    def perform_create(self, serializer) -> None:
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"], url_path="qr")
    def qr(self, request, pk=None) -> HttpResponse:
        """GET /api/events/{id}/qr/ — the event's QR code as a PNG (EVENT-03)."""
        event = self.get_object()
        img = qrcode.make(event.guest_url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        response = HttpResponse(buffer.getvalue(), content_type="image/png")
        response["Content-Disposition"] = f'inline; filename="event-{event.token}-qr.png"'
        return response

    @action(
        detail=True,
        methods=["post"],
        url_path="upload",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload(self, request, pk=None) -> Response:
        """POST /api/events/{id}/upload/ — batch-upload photos (UPLOAD-01).

        Accepts one or more files under the ``files`` form field. Each becomes a
        Photo row (status=uploaded) and is queued for thumbnail processing.
        """
        from photos.models import Photo
        from photos.serializers import PhotoSerializer
        from photos.tasks import process_photo

        event = self.get_object()  # queryset-scoped: enforces ownership/collaboration
        files = request.FILES.getlist("files")
        if not files:
            return Response(
                {"detail": "No files provided. Send one or more files under the 'files' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created, rejected = [], []
        for f in files:
            if f.content_type not in ALLOWED_IMAGE_TYPES:
                rejected.append({"filename": f.name, "reason": f"unsupported type {f.content_type}"})
                continue
            photo = Photo.objects.create(
                event=event,
                uploaded_by=request.user,
                original=f,
                original_filename=f.name[:255],
                status=Photo.Status.UPLOADED,
            )
            process_photo.delay(photo.pk)
            created.append(photo)

        body = {
            "created": PhotoSerializer(created, many=True, context={"request": request}).data,
            "rejected": rejected,
        }
        code = status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST
        return Response(body, status=code)
