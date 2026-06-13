from __future__ import annotations

from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    guest_url = serializers.CharField(read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id",
            "name",
            "date",
            "token",
            "owner",
            "retention_days",
            "guest_url",
            "qr_code_url",
            "expires_at",
            "is_expired",
            "created_at",
        )
        read_only_fields = (
            "id",
            "token",
            "owner",
            "guest_url",
            "qr_code_url",
            "expires_at",
            "is_expired",
            "created_at",
        )

    def get_qr_code_url(self, obj: Event) -> str:
        request = self.context.get("request")
        path = reverse("event-qr", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(path) if request else path
