from __future__ import annotations

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import SignupSerializer, UserSerializer


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Login endpoint, rate-limited to slow brute-force / credential stuffing."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class SignupView(generics.CreateAPIView):
    """POST /api/auth/signup/ — register a photographer (pending approval)."""

    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "id": serializer.instance.id,
                "username": serializer.instance.username,
                "message": "Account created. An admin must approve it before you can upload.",
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ — the current user's profile and approval status."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the supplied refresh token (AUTH-04)."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response({"detail": "invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)
