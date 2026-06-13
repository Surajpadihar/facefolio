"""InsightFace engine — loaded ONCE per process, never per task.

Instantiating FaceAnalysis costs seconds + ~hundreds of MB; doing it inside a task
body OOM-kills the worker under load. We load a module-level singleton at worker
process init (Celery prefork) and at gunicorn post-fork (Phase 4 selfie search).
"""

from __future__ import annotations

import threading

import numpy as np
from celery.signals import worker_init, worker_process_init
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

# Let PIL open HEIC/HEIF (iPhone photos) — INDEX-03.
register_heif_opener()

MODEL_NAME = "buffalo_l"
DET_SIZE = (640, 640)

_app = None
_lock = threading.Lock()


def get_face_app():
    """Return the process-wide FaceAnalysis singleton, loading it on first use."""
    global _app
    if _app is None:
        with _lock:
            if _app is None:
                from insightface.app import FaceAnalysis

                app = FaceAnalysis(name=MODEL_NAME, providers=["CPUExecutionProvider"])
                app.prepare(ctx_id=-1, det_size=DET_SIZE)  # ctx_id=-1 => CPU
                _app = app
    return _app


def load_rgb(fileobj) -> Image.Image:
    """Open an image file (incl. HEIC), apply EXIF orientation, return RGB."""
    with Image.open(fileobj) as img:
        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")


def detect_faces(rgb_image: Image.Image) -> list[dict]:
    """Detect faces and return normalized embeddings + bbox + score.

    Returns a list of {"embedding": list[float] (512, L2-normalized), "bbox": [x1,y1,x2,y2],
    "det_score": float}.
    """
    # insightface expects BGR (OpenCV convention).
    bgr = np.asarray(rgb_image)[:, :, ::-1]
    results = []
    for face in get_face_app().get(bgr):
        results.append(
            {
                "embedding": face.normed_embedding.astype(float).tolist(),
                "bbox": [int(v) for v in face.bbox],
                "det_score": float(face.det_score),
            }
        )
    return results


@worker_init.connect
def _predownload_model(**_kwargs) -> None:
    """Ensure the model files exist BEFORE the worker forks children.

    Downloading happens once here in the single main process; if every forked child
    raced to download to the same path on a cold start, the archive could corrupt.
    We then reset the singleton so each child builds its own (fork-safe) session from
    the now-present files.
    """
    global _app
    get_face_app()
    _app = None


@worker_process_init.connect
def _warm_load_model(**_kwargs) -> None:
    """Load the model once in each Celery worker child process (from disk, no download)."""
    get_face_app()
