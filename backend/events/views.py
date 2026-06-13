from __future__ import annotations

import io

import qrcode
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action

from accounts.permissions import IsApprovedPhotographer

from .models import Event
from .serializers import EventSerializer


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
