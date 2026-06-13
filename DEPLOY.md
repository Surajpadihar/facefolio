# Deploying FaceFolio — free, 24/7, on Oracle Cloud Always Free

This runs the **entire stack** (UI, Django Admin, API, face-AI workers, Postgres, MinIO)
on one free VM, behind a single HTTPS domain via Caddy (auto Let's Encrypt cert).

> **Why Oracle?** The face model (InsightFace) needs ~1.5–2 GB RAM, which doesn't fit
> typical free PaaS tiers. Oracle's **Always Free Ampere (ARM) VM** gives up to 4 cores /
> 24 GB RAM **free forever** — plenty for the whole stack. (Vercel/Render can host only the
> frontend, not the face-AI backend.)

---

## 1. Create the free VM (≈15 min — only you can do this)

1. Sign up at **https://www.oracle.com/cloud/free/** → "Always Free". (A card is required for
   identity verification; Always Free resources are **not charged**.)
2. **Create a VM instance:**
   - Image: **Ubuntu 22.04**
   - Shape: **Ampere — VM.Standard.A1.Flex**, set **2 OCPU / 12 GB RAM** (free allowance is up
     to 4/24; 12 GB is comfortable). ⚠️ Do **not** pick the tiny `E2.1.Micro` (1 GB) — too small.
   - Add your SSH public key (it's `~/.ssh/id_ed25519.pub` on your laptop).
   - Create. Note the **public IP**.
   > If you see "Out of host capacity" for A1, try a different Availability Domain or region, or
   > retry later — ARM free capacity is popular.
3. **Open ports 80 + 443:**
   - In the VM's **VCN → Subnet → Security List → Add Ingress Rules**: source `0.0.0.0/0`,
     TCP ports **80** and **443**.
   - Ubuntu images also block them at the OS firewall — after SSHing in (step 2 below), run:
     ```bash
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
     sudo netfilter-persistent save
     ```

## 2. Free domain (DuckDNS — 2 min)

1. Go to **https://www.duckdns.org**, sign in, create a subdomain e.g. `facefolio`.
2. Set its IP to your VM's **public IP**. You now own `facefolio.duckdns.org`.

## 3. Install Docker on the VM

SSH in (`ssh ubuntu@YOUR_VM_IP`), then:
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker   # run docker without sudo
```

## 4. Deploy

```bash
git clone https://github.com/Surajpadihar/facefolio.git
cd facefolio
cp .env.prod.example .env
nano .env          # replace every CHANGE-ME: DOMAIN, PUBLIC_BASE_URL, secrets, passwords
                   # (use your real duckdns domain everywhere)

# build + launch the whole stack (first run pulls images, builds, downloads the face model)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# create your super-admin
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api \
  python manage.py createsuperuser
```

Caddy fetches the HTTPS certificate automatically on first start (needs DNS pointing at the IP
and ports 80/443 open). Give it ~1 minute, then open:

| | URL |
|---|---|
| App (guests + photographers) | `https://facefolio.duckdns.org` |
| Django Admin | `https://facefolio.duckdns.org/admin/` |

That's it — live, with HTTPS, for free.

## Updating later

```bash
cd facefolio && git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Moving to a paid server later

Nothing changes architecturally — copy the repo + `.env` to the new box (bigger VM, or a managed
host), point your domain at it, and run the same compose command. Swap DuckDNS for a custom domain
whenever you buy one (just update `DOMAIN`/`*_BASE_URL` in `.env`).

## Troubleshooting

- **Cert not issued / site not loading:** confirm `dig facefolio.duckdns.org` returns the VM IP,
  and ports 80/443 are open (both OCI security list **and** OS iptables). Check `docker compose ... logs caddy`.
- **Photos don't load:** check `S3_PUBLIC_ENDPOINT_URL=https://<domain>` (no port) so presigned URLs
  route through Caddy's `/facefolio-photos/` path.
- **Out of memory during build/index:** use a 2+ OCPU / 12 GB A1 shape.
- **First face search is slow:** the worker downloads buffalo_l (~280 MB) once on first boot.
