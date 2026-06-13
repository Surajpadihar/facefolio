from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "owner", "expires_at", "is_expired")
    list_filter = ("date", "owner")
    search_fields = ("name", "owner__username", "token")
    readonly_fields = ("token", "expires_at", "created_at", "updated_at", "guest_link")
    filter_horizontal = ("collaborators",)

    @admin.display(description="Guest gallery URL")
    def guest_link(self, obj: Event) -> str:
        if not obj.pk:
            return "—"
        return format_html('<a href="{}" target="_blank">{}</a>', obj.guest_url, obj.guest_url)
