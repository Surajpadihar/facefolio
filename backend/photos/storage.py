"""Presigned URL helpers.

The API/worker reach MinIO over the internal Docker network (``S3_ENDPOINT_URL``,
e.g. http://minio:9000), but browsers must use a host-reachable endpoint
(``S3_PUBLIC_ENDPOINT_URL``, e.g. http://localhost:9100). A presigned URL signed
for the internal host is useless to a browser — and a metric/endpoint mismatch is
a classic MinIO footgun. So browser-facing GET URLs are signed with a boto3 client
pointed at the *public* endpoint.
"""

from __future__ import annotations

import os
from functools import lru_cache

import boto3
from botocore.config import Config
from django.conf import settings

# Read S3/MinIO config from the environment so this works regardless of the
# configured Django storage backend (e.g. in-memory storage during tests).
BUCKET = os.environ.get("S3_BUCKET_NAME", "facefolio-photos")


@lru_cache(maxsize=1)
def _public_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_PUBLIC_ENDPOINT_URL,
        aws_access_key_id=os.environ.get("MINIO_ROOT_USER", "minioadmin"),
        aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin"),
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def public_presigned_get(key: str, expires: int = 3600) -> str | None:
    """A browser-usable presigned GET URL for an object key, or None if no key."""
    if not key:
        return None
    return _public_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def public_presigned_download(key: str, filename: str, expires: int = 3600) -> str | None:
    """Presigned GET URL that forces a download with a friendly filename (DL-01)."""
    if not key:
        return None
    return _public_client().generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET,
            "Key": key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
        },
        ExpiresIn=expires,
    )
