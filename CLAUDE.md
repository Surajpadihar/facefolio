# FaceFolio — Project Guide

Self-hosted event-photography platform. Photographers (admin-approved) create events and batch-upload photos; guests scan an event QR code, take a selfie, and instantly see every photo they appear in. Free view + download, no guest accounts. Super-admin via Django Admin.

## Source of Truth

This is a **GSD** project. `.planning/` holds the canonical context — read it before working:

- `.planning/PROJECT.md` — what/why, requirements, key decisions
- `.planning/REQUIREMENTS.md` — 34 v1 requirements with REQ-IDs + traceability
- `.planning/ROADMAP.md` — 5 phases, success criteria, dependencies
- `.planning/STATE.md` — current progress / next action
- `.planning/research/` — STACK / FEATURES / ARCHITECTURE / PITFALLS / SUMMARY

**Workflow:** discuss → plan → execute → verify, per phase. Run `/gsd-progress` to see where things stand, `/gsd-plan-phase N` to plan, `/clear` between phases.

## Stack (version-pinned in research/STACK.md)

- **Backend:** Python 3.12 · Django 5.2 LTS · Django REST Framework 3.17 (Django Admin = super-admin panel)
- **Frontend:** Next.js 16 · React 19 · Tailwind
- **Face AI:** InsightFace 1.0.1 (`buffalo_l`, 512-dim L2-normalized embeddings), onnxruntime CPU (`numpy<2`)
- **Data:** PostgreSQL 16 + pgvector 0.8.x (relational + vector search)
- **Storage:** MinIO (S3-compatible), `django-storages`
- **Jobs:** Celery 5.6 + Redis 7
- **Run:** `docker compose up` — six services: api, web, worker, db, redis, minio

## Non-negotiable engineering rules (from research — do not relearn the hard way)

1. **pgvector operator must match index opclass.** Embeddings are L2-normalized → use **inner product** (`vector_ip_ops` HNSW index + `<#>` query operator) for both. A mismatch silently falls back to sequential scan (100×+ slower). Set `hnsw.ef_search = 100` per session. Assert `Index Scan` via `EXPLAIN ANALYZE`.
2. **Load the InsightFace model once per process**, never inside a task body (`worker_process_init` in Celery, `post_fork` in gunicorn). Per-task load = ~500 MB/call OOM.
3. **Selfie embeddings are ephemeral.** Never persist, never serialize into a Celery task/Redis, never log. The selfie ANN query runs synchronously in the API request and the vector stays a local array.
4. **Handle EXIF orientation + HEIC** (`ImageOps.exif_transpose()`, `pillow-heif`) or ~40% of iPhone photos index zero faces.
5. **Face matching is scoped per event** (partial HNSW index `WHERE event_id = N`), not global.
6. **`buffalo_l` is non-commercial-license** — blocks any future paid feature until a commercial license is secured. v1 (free) is fine.

## Human gates (don't auto-resolve)

- **Phase 3:** calibrate `FACE_MATCH_THRESHOLD` against a real-photo fixture — no universal value exists.
- **Phase 4:** consent-notice text needs a legal review (BIPA/GDPR specificity) before shipping.

## Code conventions

- Python: Ruff format + lint on every change; type hints on signatures; `python-dotenv` for env (never `source .env`).
- Secrets in `.env` only — never commit/echo/log. Scan diffs before staging.
- Commits: `feat:`/`fix:`/`docs:`/`refactor:`/`test:`/`chore:` prefix, human-authored (no AI trailers).
