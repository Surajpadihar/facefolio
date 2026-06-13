#!/usr/bin/env bash
# Bring the whole stack live on a free public Cloudflare quick-tunnel URL.
# The trycloudflare URL changes each run, so this re-points the app config automatically.
#   ./deploy/tunnel-up.sh
set -euo pipefail
cd "$(dirname "$0")/.."

C="docker compose -f docker-compose.yml -f docker-compose.tunnel.yml"

echo "▶ starting stack + tunnel…"
$C up -d --build

echo "▶ waiting for the public URL…"
URL=""
for _ in $(seq 1 40); do
  URL=$($C logs cloudflared 2>&1 | grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" | tail -1)
  [ -n "$URL" ] && break
  sleep 2
done
[ -z "$URL" ] && { echo "✗ tunnel URL not found — check: $C logs cloudflared"; exit 1; }
HOST=${URL#https://}

echo "▶ pointing app config at $URL"
python3 - "$HOST" "$URL" <<'PY'
import sys, re, pathlib
host, url = sys.argv[1], sys.argv[2]
p = pathlib.Path(".env"); lines = p.read_text().splitlines()
def setkv(lines, key, val):
    out, found = [], False
    for l in lines:
        if re.match(rf'^{re.escape(key)}=', l):
            out.append(f"{key}={val}"); found = True
        else:
            out.append(l)
    if not found:
        out.append(f"{key}={val}")
    return out
for k, v in {
    "DJANGO_ALLOWED_HOSTS": f"localhost,127.0.0.1,api,{host}",
    "DJANGO_CORS_ALLOWED_ORIGINS": f"http://localhost:3000,{url}",
    "DJANGO_CSRF_TRUSTED_ORIGINS": url,
    "DJANGO_BEHIND_PROXY": "true",
    "FRONTEND_BASE_URL": url,
    "WEB_API_BASE_URL": url,
    "S3_PUBLIC_ENDPOINT_URL": url,
}.items():
    lines = setkv(lines, k, v)
p.write_text("\n".join(lines) + "\n")
PY

echo "▶ reloading web + api…"
$C up -d --force-recreate web api >/dev/null

echo ""
echo "✅ LIVE AT:  $URL"
echo "   Admin:    $URL/admin/"
echo "   (live while this machine + these containers stay running)"
