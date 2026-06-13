from __future__ import annotations

from django.contrib import admin

from .models import ConsentRecord


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("consent_id", "event", "notice_version", "accepted_at")
    list_filter = ("event", "notice_version")
    readonly_fields = ("consent_id", "event", "notice_version", "accepted_at")

    def has_add_permission(self, request) -> bool:
        return False
