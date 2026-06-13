# FaceFolio

Self-hosted event-photography platform. Photographers (admin-approved) create events and batch-upload photos; guests scan an event QR code, take a selfie, and instantly see every photo they appear in — free to view and download, no guest account required. Super-admin via Django Admin.

> Built with GSD. Canonical project context lives in [`.planning/`](.planning/) — see `PROJECT.md`, `ROADMAP.md`, `REQUIREMENTS.md`.

## Stack

Django 5.2 + DRF · Next.js 16 + React 19 · InsightFace (face embeddings) · PostgreSQL + pgvector · MinIO · Celery + Redis — all via Docker Compose.

## Quick start

```bash
cp .env.example .env          # adjust secrets if you like
docker compose up --build     # first run builds images + migrates
```

Then:

| Service | URL |
|---------|-----|
| API (Django)        | http://localhost:8088/api/ |
| Django Admin        | http://localhost:8088/admin/ |
| Frontend (Next.js)  | http://localhost:3000 |
| MinIO console       | http://localhost:9101 |

> Host ports are remapped (8088/6380/9100/9101) to avoid clashing with other local stacks; change them in `docker-compose.yml` if you like. Internal service ports are unchanged.

### Create the super-admin

```bash
docker compose exec api python manage.py createsuperuser --username admin --email admin@example.com
```

Log in at `/admin/` to approve photographer signups, manage events, and inspect data.

## Build status

Phase 1 (Foundation) — accounts + approval, events + QR, admin, Dockerized stack. See `.planning/STATE.md` for current progress.
