"""Gunicorn config — warm-load the face model once per worker for selfie search.

Selfie search (Phase 4) embeds the selfie synchronously in the API process (the
embedding must never be serialized into Celery/Redis — PRIV-02). Loading the model
in post_fork means the first search isn't penalised by a multi-second cold load.
"""

import os


def post_fork(server, worker):
    # Skip during management commands; only the gunicorn workers need the model.
    try:
        from faces.engine import get_face_app

        get_face_app()
        server.log.info("buffalo_l warm-loaded in gunicorn worker %s", worker.pid)
    except Exception as exc:  # noqa: BLE001 — never let model load crash the worker boot
        server.log.warning("face model warm-load skipped: %s", exc)


# Keep worker count low: each worker holds its own model copy (~1-1.5 GB).
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
bind = "0.0.0.0:8000"
