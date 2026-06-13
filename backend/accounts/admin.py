from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Super-admin control over photographers, including approval (ADMIN-01/02)."""

    list_display = ("username", "email", "is_approved", "is_staff", "is_superuser", "date_joined")
    list_filter = ("is_approved", "is_staff", "is_superuser", "is_active")
    actions = ("approve_photographers", "revoke_approval")

    fieldsets = BaseUserAdmin.fieldsets + (("Photographer approval", {"fields": ("is_approved", "approved_at")}),)
    readonly_fields = ("approved_at",)

    @admin.action(description="Approve selected photographers")
    def approve_photographers(self, request, queryset) -> None:
        updated = queryset.update(is_approved=True, approved_at=timezone.now())
        self.message_user(request, f"Approved {updated} photographer(s).")

    @admin.action(description="Revoke approval for selected photographers")
    def revoke_approval(self, request, queryset) -> None:
        updated = queryset.update(is_approved=False, approved_at=None)
        self.message_user(request, f"Revoked approval for {updated} photographer(s).")
