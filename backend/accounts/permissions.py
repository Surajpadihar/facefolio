from __future__ import annotations

from rest_framework.permissions import BasePermission


class IsApprovedPhotographer(BasePermission):
    """Allows access only to approved (or superuser) authenticated users."""

    message = "Your account is pending admin approval."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(user and user.is_authenticated and user.can_upload)
