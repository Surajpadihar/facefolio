from __future__ import annotations

from django.contrib import admin

from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "original_filename", "status", "width", "height", "created_at")
    list_filter = ("status", "event")
    search_fields = ("original_filename", "event__name")
    readonly_fields = ("original", "thumbnail", "width", "height", "status", "error", "created_at", "updated_at")
