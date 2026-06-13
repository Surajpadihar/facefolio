from __future__ import annotations

from django.contrib import admin

from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "original_filename", "status", "face_count", "width", "height", "created_at")
    list_filter = ("status", "event")
    search_fields = ("original_filename", "event__name")
    readonly_fields = ("original", "thumbnail", "width", "height", "status", "error", "created_at", "updated_at")
    actions = ("reindex_faces",)

    @admin.display(description="Faces")
    def face_count(self, obj: Photo) -> int:
        return obj.faces.count()

    @admin.action(description="Re-run face indexing on selected photos")
    def reindex_faces(self, request, queryset) -> None:
        from faces.tasks import index_photo

        for photo in queryset:
            index_photo.delay(photo.pk)
        self.message_user(request, f"Queued re-indexing for {queryset.count()} photo(s).")
