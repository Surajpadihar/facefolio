"""Calibrate the face-match thresholds against a labeled set of REAL photos.

This closes the "threshold is a guess" gap: it measures how same-person vs
different-person similarities actually separate on YOUR data, then recommends
values for FACE_MATCH_THRESHOLD (confident) and FACE_MATCH_MAYBE_THRESHOLD.

Usage:
    # organize a folder with one subfolder per person, 2+ clear photos each:
    #   calib/alice/1.jpg  calib/alice/2.jpg  calib/bob/1.jpg ...
    docker compose exec worker python manage.py calibrate_threshold --dir /path/to/calib

Embeddings are L2-normalized, so similarity = inner product (the same metric the
search uses). Bigger separation between the positive/negative distributions = a
more reliable threshold.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Recommend face-match thresholds from a labeled photo set (subfolder per person)."

    def add_arguments(self, parser):
        parser.add_argument("--dir", required=True, help="Directory with one subfolder per person.")
        parser.add_argument("--max-neg", type=int, default=2000, help="Max different-person pairs to sample.")

    def handle(self, *args, **opts):
        from faces.engine import detect_faces, load_rgb

        root = Path(opts["dir"])
        if not root.is_dir():
            raise CommandError(f"Not a directory: {root}")

        # 1. Embed the most prominent face in each image, grouped by person (folder).
        people: dict[str, list[np.ndarray]] = {}
        n_imgs = n_faces = 0
        for person_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            for img_path in sorted(person_dir.iterdir()):
                if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}:
                    continue
                n_imgs += 1
                try:
                    faces = detect_faces(load_rgb(str(img_path)))
                except Exception as exc:  # noqa: BLE001
                    self.stderr.write(f"  skip {img_path}: {exc}")
                    continue
                if not faces:
                    self.stderr.write(f"  no face: {img_path}")
                    continue
                best = max(faces, key=lambda f: f["det_score"])
                people.setdefault(person_dir.name, []).append(np.asarray(best["embedding"], dtype=float))
                n_faces += 1

        people = {k: v for k, v in people.items() if len(v) >= 2}
        if len(people) < 2:
            raise CommandError("Need >=2 people each with >=2 usable photos. Add more labeled images.")

        # 2. Positive pairs (same person) and negative pairs (different people).
        pos = [float(a @ b) for embs in people.values() for a, b in itertools.combinations(embs, 2)]
        names = list(people)
        neg = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                for a in people[names[i]]:
                    for b in people[names[j]]:
                        neg.append(float(a @ b))
        rng = np.random.default_rng(0)
        if len(neg) > opts["max_neg"]:
            neg = list(rng.choice(neg, opts["max_neg"], replace=False))

        pos_a, neg_a = np.array(pos), np.array(neg)
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Calibration data ==="))
        self.stdout.write(f"  people: {len(people)} | images: {n_imgs} | faces embedded: {n_faces}")
        self.stdout.write(f"  same-person pairs: {len(pos_a)} | different-person pairs: {len(neg_a)}")
        self.stdout.write(
            f"  same-person  sim: mean={pos_a.mean():.3f} min={pos_a.min():.3f} p5={np.percentile(pos_a, 5):.3f}"
        )
        self.stdout.write(
            f"  diff-person  sim: mean={neg_a.mean():.3f} max={neg_a.max():.3f} p95={np.percentile(neg_a, 95):.3f}"
        )

        # 3. Sweep thresholds, score F1 (positives should match).
        best_t, best_f1 = 0.0, -1.0
        rows = []
        for t in np.arange(0.10, 0.75, 0.01):
            tp = int((pos_a >= t).sum())
            fn = len(pos_a) - tp
            fp = int((neg_a >= t).sum())
            prec = tp / (tp + fp) if (tp + fp) else 1.0
            rec = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
            rows.append((t, prec, rec, f1))
            if f1 > best_f1:
                best_f1, best_t = f1, float(t)

        # "maybe" lower bound: loosest threshold that still keeps false-positives near-zero
        # (<=1% of different-person pairs), to surface borderline shots without strangers.
        maybe_t = best_t
        for t, _prec, _rec, _f1 in rows:
            if (neg_a >= t).mean() <= 0.01:
                maybe_t = float(t)
                break

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== threshold sweep (sim >= t) ==="))
        self.stdout.write("    t     precision  recall   F1")
        for t, prec, rec, f1 in rows:
            mark = "  <= best F1" if abs(t - best_t) < 1e-9 else ""
            if abs((t * 100) % 5) < 1e-6 or mark:
                self.stdout.write(f"  {t:.2f}     {prec:.3f}     {rec:.3f}   {f1:.3f}{mark}")

        self.stdout.write(self.style.SUCCESS("\n=== RECOMMENDATION ==="))
        self.stdout.write(f"  FACE_MATCH_THRESHOLD={best_t:.2f}        # confident (best F1={best_f1:.3f})")
        self.stdout.write(f"  FACE_MATCH_MAYBE_THRESHOLD={min(maybe_t, best_t):.2f}   # 'you might also be in these'")
        self.stdout.write("\n  Put these in your .env, then recreate the api + worker.")
        if neg_a.max() >= best_t:
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠ Some different-person pairs exceed the threshold — expect occasional false matches. "
                    "Add more/better photos or raise the threshold."
                )
            )
