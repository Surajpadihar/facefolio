"""Public, unauthenticated guest endpoints: QR landing → consent → selfie search.

PRIV-02 is enforced structurally here: the selfie's embedding is computed in-process,
used for one pgvector query, and never written to a model, queued to Celery, or logged.
"""

from __future__ import annotations

import zipfile
from tempfile import SpooledTemporaryFile

from django.conf import settings
from django.db import connection
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from pgvector.django import MaxInnerProduct
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from events.models import Event
from faces.engine import detect_faces, load_rgb
from faces.models import FaceEmbedding
from photos.models import Photo
from photos.storage import public_presigned_download

from .models import CONSENT_NOTICE_VERSION, ConsentRecord
from .serializers import MatchSerializer, PublicPhotoSerializer

# How many candidate faces to pull from the ANN before grouping by photo.
SEARCH_CANDIDATES = 300


def _get_active_event(token: str) -> Event:
    event = get_object_or_404(Event, token=token)
    return event


def _event_status(event: Event) -> dict:
    counts = {"total": 0, "indexed": 0, "pending": 0}
    for p in event.photos.all():
        counts["total"] += 1
        if p.status == Photo.Status.INDEXED:
            counts["indexed"] += 1
        elif p.status != Photo.Status.FAILED:
            counts["pending"] += 1
    return counts


class PublicEventView(APIView):
    """GET /api/public/events/{token}/ — event summary + indexing status (SEARCH-01, SEARCH-05)."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        event = _get_active_event(token)
        if event.is_expired:
            return Response({"detail": "This event has expired."}, status=status.HTTP_410_GONE)
        c = _event_status(event)
        return Response(
            {
                "name": event.name,
                "date": event.date,
                "photo_count": c["total"],
                "indexed_count": c["indexed"],
                "pending_count": c["pending"],
                # SEARCH-05: tell the guest indexing is still in progress.
                "still_processing": c["pending"] > 0,
                "ready_for_search": c["indexed"] > 0,
            }
        )


class PublicGalleryView(APIView):
    """GET /api/public/events/{token}/gallery/ — browse all indexed photos (SEARCH-04 fallback)."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        event = _get_active_event(token)
        if event.is_expired:
            return Response({"detail": "This event has expired."}, status=status.HTTP_410_GONE)
        photos = event.photos.filter(status=Photo.Status.INDEXED)
        return Response(PublicPhotoSerializer(photos, many=True).data)


class ConsentView(APIView):
    """POST /api/public/events/{token}/consent/ — record consent before selfie capture (PRIV-01)."""

    permission_classes = [AllowAny]

    def post(self, request, token):
        event = _get_active_event(token)
        if event.is_expired:
            return Response({"detail": "This event has expired."}, status=status.HTTP_410_GONE)
        record = ConsentRecord.objects.create(event=event)
        return Response(
            {"consent_id": str(record.consent_id), "notice_version": CONSENT_NOTICE_VERSION},
            status=status.HTTP_201_CREATED,
        )


class SelfieSearchView(APIView):
    """POST /api/public/events/{token}/search/ — find a guest's photos from a selfie (SEARCH-02/03/04)."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "selfie"

    def post(self, request, token):
        event = _get_active_event(token)
        if event.is_expired:
            return Response({"detail": "This event has expired."}, status=status.HTTP_410_GONE)

        # PRIV-01: a valid consent record for THIS event is required before searching.
        consent_id = request.data.get("consent_id")
        if not consent_id or not ConsentRecord.objects.filter(consent_id=consent_id, event=event).exists():
            return Response(
                {"detail": "Consent is required before searching. Accept the privacy notice first."},
                status=status.HTTP_403_FORBIDDEN,
            )

        selfie = request.FILES.get("selfie")
        if not selfie:
            return Response({"detail": "No selfie provided (field 'selfie')."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Ephemeral zone: the embedding lives only in local variables (PRIV-02) ---
        try:
            rgb = load_rgb(selfie)
        except Exception:  # noqa: BLE001
            return Response({"detail": "Could not read that image."}, status=status.HTTP_400_BAD_REQUEST)

        faces = detect_faces(rgb)
        if not faces:
            return Response(
                {
                    "no_face_detected": True,
                    "detail": "We couldn't find a face in that photo. Try again with a clear, front-facing selfie.",
                },
                status=status.HTTP_200_OK,
            )
        # Use the most prominent face if the selfie has more than one.
        query_vec = max(faces, key=lambda f: f["det_score"])["embedding"]

        c = _event_status(event)
        threshold = settings.FACE_MATCH_THRESHOLD

        # Boost recall for this connection, then ANN search scoped to the event with the
        # inner-product operator that matches the index opclass.
        with connection.cursor() as cur:
            cur.execute("SET LOCAL hnsw.ef_search = 100")
        candidates = (
            FaceEmbedding.objects.filter(event=event)
            .annotate(distance=MaxInnerProduct("embedding", query_vec))
            .order_by("distance")[:SEARCH_CANDIDATES]
        )

        # Group by photo, keeping the best score per photo. distance = -inner_product.
        best: dict[int, float] = {}
        for fe in candidates:
            sim = -float(fe.distance)
            if sim >= threshold and sim > best.get(fe.photo_id, -1.0):
                best[fe.photo_id] = sim
        # query_vec falls out of scope here — never persisted.

        ranked_ids = sorted(best, key=lambda pid: best[pid], reverse=True)
        photos = {p.id: p for p in Photo.objects.filter(id__in=ranked_ids)}
        matches = []
        for pid in ranked_ids:
            photo = photos[pid]
            photo.score = round(best[pid], 4)
            matches.append(photo)

        return Response(
            {
                "match_count": len(matches),
                "no_match": len(matches) == 0,  # SEARCH-04: frontend shows retry + browse gallery
                "still_processing": c["pending"] > 0,  # SEARCH-05
                "matches": MatchSerializer(matches, many=True).data,
            }
        )


def _photo_filename(photo: Photo) -> str:
    base = photo.original_filename or f"photo-{photo.id}.jpg"
    return f"{photo.id}-{base}"


class PhotoDownloadView(APIView):
    """GET /api/public/events/{token}/photos/{photo_id}/download/ — free single download (DL-01)."""

    permission_classes = [AllowAny]

    def get(self, request, token, photo_id):
        event = _get_active_event(token)
        if event.is_expired:
            return Response({"detail": "This event has expired."}, status=status.HTTP_410_GONE)
        photo = get_object_or_404(Photo, id=photo_id, event=event)
        url = public_presigned_download(photo.original.name, _photo_filename(photo))
        return HttpResponseRedirect(url)


class BulkDownloadView(APIView):
    """POST /api/public/events/{token}/download-zip/ — download selected/all photos as one ZIP (DL-02/03).

    Body: {"photo_ids": [...]} (omit/empty = all indexed photos). Capped at MAX_BULK_DOWNLOAD.
    """

    permission_classes = [AllowAny]

    def post(self, request, token):
        event = _get_active_event(token)
        if event.is_expired:
            return Response({"detail": "This event has expired."}, status=status.HTTP_410_GONE)

        photo_ids = request.data.get("photo_ids") or []
        qs = Photo.objects.filter(event=event, status=Photo.Status.INDEXED)
        if photo_ids:
            qs = qs.filter(id__in=photo_ids)

        cap = settings.MAX_BULK_DOWNLOAD
        count = qs.count()
        if count == 0:
            return Response({"detail": "No photos to download."}, status=status.HTTP_400_BAD_REQUEST)
        if count > cap:
            return Response(
                {"detail": f"Too many photos ({count}). Select at most {cap} per download."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        spool = SpooledTemporaryFile(max_size=64 * 1024 * 1024)  # spill to disk past 64 MB
        with zipfile.ZipFile(spool, "w", zipfile.ZIP_STORED) as zf:
            for photo in qs:
                photo.original.open("rb")
                try:
                    zf.writestr(_photo_filename(photo), photo.original.read())
                finally:
                    photo.original.close()
        spool.seek(0)
        response = FileResponse(spool, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{event.name}-photos.zip"'
        return response
