from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """Photographer self-signup. New accounts are unapproved until an admin acts (AUTH-01/02)."""

    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data: dict) -> User:
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            is_approved=False,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    can_upload = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "is_approved", "is_superuser", "can_upload")
        read_only_fields = fields
