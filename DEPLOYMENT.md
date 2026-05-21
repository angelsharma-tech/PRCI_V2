# PRCI v2 — Production Deployment Guide

## Phase 4.4 — Full Production Deployment & Dockerization

---

## Quick Start

```bash
# 1. Clone / navigate to project
cd PRCI_v2

# 2. Copy environment template
cp .env.example .env
#    Edit .env — set real passwords & secrets

# 3. One-command startup 🔥
docker compose up --build

# 4. Open browser
#    Frontend  → http://localhost
#    API Docs  → http://localhost/docs
#    Health    → http://localhost/api/health
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└──────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│                    Nginx (Port 80/443)                       │
│              Reverse Proxy + SSL + Rate Limit               │
│                                                            │
│   /api/*  ────────>  FastAPI Backend  (port 8000)         │
│   /docs   ────────>  FastAPI Swagger UI                   │
│   /       ────────>  Streamlit Frontend (port 8501)       │
└────────────────────────┬───────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────┐
│              Internal Docker Network (bridge)               │
│                                                            │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐             │
│   │  FastAPI │   │ Streamlit│   │PostgreSQL│             │
│   │  backend │   │ frontend │   │    db    │             │
│   │ :8000    │   │ :8501    │   │  :5432   │             │
│   └──────────┘   └──────────┘   └──────────┘             │
└────────────────────────────────────────────────────────────┘
```

---

## Services

| Service | Container | Port | Image | Purpose |
|---------|-----------|------|-------|---------|
| **Nginx** | `prci-nginx` | 80, 443 | `nginx:alpine` | Reverse proxy, SSL, static files |
| **Backend** | `prci-backend` | 8000 | `Dockerfile.backend` | FastAPI + business logic |
| **Frontend** | `prci-frontend` | 8501 | `Dockerfile.frontend` | Streamlit UI |
| **Database** | `prci-db` | 5432 | `postgres:15-alpine` | PostgreSQL persistent store |

---

## Docker Commands

```bash
# Build & start everything
docker compose up --build

# Start in background (detached)
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend

# Stop everything
docker compose down

# Stop & remove volumes (⚠️ destroys DB data)
docker compose down -v

# Restart a service
docker compose restart backend

# Exec into a container
docker compose exec db psql -U prci -d prci_v2

# Check health
curl http://localhost/health
curl http://localhost/api/health/live
curl http://localhost/_stcore/health
```

---

## Railway Deployment

### Step 1: Prepare Repo

```bash
# Ensure these files are committed:
#   Dockerfile.backend
#   Dockerfile.frontend
#   docker-compose.yml
#   nginx/nginx.conf
#   .env.example
#   requirements.txt
#   requirements-backend.txt
```

### Step 2: Deploy PostgreSQL

1. Go to [railway.app](https://railway.app)
2. Create Project → "New" → "Add a Service" → "Database" → "Add PostgreSQL"
3. Note the `DATABASE_URL` from "Variables" tab

### Step 3: Deploy FastAPI Backend

1. "New" → "Deploy from GitHub repo"
2. Select your PRCI_v2 repo
3. Settings:
   - **Root Directory**: `./`
   - **Dockerfile Path**: `Dockerfile.backend`
   - **Port**: `8000`
4. Add Environment Variables:
   ```
   DATABASE_URL=<paste from PostgreSQL service>
   SECRET_KEY=<random_64_char_string>
   LOG_LEVEL=INFO
   ```
5. Generate Domain → e.g. `prci-backend.up.railway.app`

### Step 4: Deploy Streamlit Frontend

1. "New" → "Deploy from GitHub repo" (same repo)
2. Settings:
   - **Root Directory**: `./`
   - **Dockerfile Path**: `Dockerfile.frontend`
   - **Port**: `8501`
3. Add Environment Variables:
   ```
   API_BASE_URL=https://prci-backend.up.railway.app
   DATABASE_URL=<same as backend>
   SECRET_KEY=<same as backend>
   ```
4. Generate Domain → e.g. `prci.up.railway.app`

### Step 5: Railway Variables Reference

| Variable | Source | Example |
|----------|--------|---------|
| `DATABASE_URL` | Railway Postgres | `postgresql://...` |
| `SECRET_KEY` | Generate | `openssl rand -hex 32` |
| `API_BASE_URL` | Backend domain | `https://prci-backend.up.railway.app` |
| `LOG_LEVEL` | Hardcode | `INFO` |

---

## AWS Deployment

### Option A: ECS + Fargate (Serverless Containers)

```bash
# Prerequisites
aws configure  # set access key, secret key, region

# 1. Create ECR repositories
aws ecr create-repository --repository-name prci-backend
aws ecr create-repository --repository-name prci-frontend
aws ecr create-repository --repository-name prci-nginx

# 2. Build & push images
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com

docker build -f Dockerfile.backend -t prci-backend .
docker tag prci-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/prci-backend:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/prci-backend:latest

# 3. Create ECS Cluster
aws ecs create-cluster --cluster-name prci-v2-cluster

# 4. Create Task Definitions (JSON files for each service)
#    See cloud-deployment docs for full JSON specs

# 5. Create ALB (Application Load Balancer)
#    Target groups for backend / frontend

# 6. Run Services
aws ecs create-service \
    --cluster prci-v2-cluster \
    --service-name prci-backend-service \
    --task-definition prci-backend \
    --desired-count 2 \
    --launch-type FARGATE
```

### Option B: EC2 + Docker Compose (Simple)

```bash
# 1. Launch Ubuntu 22.04 EC2 instance (t3.medium+)
# 2. SSH in
ssh -i key.pem ubuntu@<ec2-ip>

# 3. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# 4. Install Docker Compose
sudo apt install docker-compose-plugin -y

# 5. Clone repo
git clone https://github.com/<your-repo>/PRCI_v2.git
cd PRCI_v2

# 6. Copy & edit .env
cp .env.example .env
nano .env  # set real values

# 7. Start
docker compose up -d

# 8. Open EC2 Security Group → Allow inbound TCP 80, 443, 8501, 8000
```

### Option C: Elastic Beanstalk (Easiest)

1. AWS Console → Elastic Beanstalk → "Create Application"
2. Platform: `Docker`
3. Upload: ZIP of your project (including `docker-compose.yml`)
4. Configure:
   - Instance type: `t3.medium`
   - Environment variables from `.env`
5. Deploy

---

## Production Checklist

### Before Deploying

- [ ] `.env` created from `.env.example` with real secrets
- [ ] `SECRET_KEY` is at least 32 random characters
- [ ] `POSTGRES_PASSWORD` is strong and unique
- [ ] `DEBUG=false` (or removed)
- [ ] `DB_ECHO=false`
- [ ] All passwords/secrets rotated from defaults
- [ ] `.env` is in `.gitignore` and NOT committed
- [ ] Docker images build successfully locally
- [ ] `docker compose up` starts all 4 services cleanly
- [ ] Health checks pass (`/health`, `/api/health/live`, `/_stcore/health`)
- [ ] API docs load at `/docs`
- [ ] Frontend loads at `/`

### SSL / HTTPS

- [ ] Nginx SSL certificates configured (or Cloudflare proxy)
- [ ] `X-Forwarded-Proto` headers trusted by FastAPI
- [ ] `API_ENABLE_CORS` configured for production domain
- [ ] HSTS headers enabled

### Database

- [ ] PostgreSQL used (not SQLite)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Backups configured (daily automated)
- [ ] Connection pooling tuned (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`)

### Monitoring

- [ ] Health endpoints accessible to load balancer
- [ ] Log aggregation configured (CloudWatch / Datadog / Loki)
- [ ] Error tracking enabled (Sentry)
- [ ] Alert thresholds set (CPU > 80%, 5xx errors)

### Security

- [ ] No secrets in code or Docker images
- [ ] Non-root containers (`USER prci`)
- [ ] Security headers in Nginx
- [ ] Rate limiting enabled
- [ ] Database not exposed to public internet
- [ ] Firewall / Security Groups restrict ports

### Performance

- [ ] Gunicorn workers = 2-4 x CPU cores
- [ ] Nginx gzip enabled
- [ ] Static files served by Nginx (not backend)
- [ ] Keepalive connections enabled
- [ ] Client max body size appropriate (50M default)

---

## Scaling Recommendations

### Vertical Scaling (Bigger Machine)

| Users | CPU | RAM | Notes |
|-------|-----|-----|-------|
| 1-50  | 2 vCPU | 4 GB | Default `t3.medium` |
| 50-200 | 4 vCPU | 8 GB | `t3.large` |
| 200-1k | 8 vCPU | 16 GB | `t3.xlarge`, separate DB |
| 1k+   | 16+ vCPU | 32+ GB | Horizontal scaling |

### Horizontal Scaling (More Machines)

1. **Backend**: Increase `docker compose` replicas or ECS `desired-count`
2. **Database**: Read replicas for SELECT queries
3. **Cache**: Add Redis layer for sessions / tokens
4. **Static Files**: S3 + CloudFront CDN

### Database Scaling Path

```
Single PostgreSQL
    ↓
PostgreSQL + Read Replica
    ↓
PostgreSQL Primary + 2 Replicas
    ↓
Connection Pooler (PgBouncer)
    ↓
Shard by tenant (future)
```

---

## Security Hardening Checklist

### Container Level

- [ ] **Non-root user**: All containers run as `prci` user (not `root`)
- [ ] **Read-only rootfs**: Mount only necessary volumes as writable
- [ ] **Minimal images**: Use `python:3.11-slim` not `full`
- [ ] **No shell access**: Remove `bash`/`sh` from production images
- [ ] **Health checks**: Every container exposes a health endpoint
- [ ] **Resource limits**: CPU/memory limits set in `docker-compose.yml`

### Network Level

- [ ] **Internal networking**: Backend/DB communicate on Docker network only
- [ ] **No exposed DB**: PostgreSQL port 5432 NOT mapped to host in prod
- [ ] **Nginx shield**: Only Nginx faces the internet
- [ ] **TLS 1.2+**: SSL configured, weak ciphers disabled
- [ ] **HSTS**: `Strict-Transport-Security` header

### Application Level

- [ ] **Strong JWT secret**: `SECRET_KEY` ≥ 64 random chars
- [ ] **Token expiration**: Access tokens expire (1h), refresh tokens (7d)
- [ ] **Password policy**: Minimum 8 chars, mixed case + digits
- [ ] **Rate limiting**: Login endpoints limited to 10/min
- [ ] **Input validation**: All endpoints use Pydantic schemas
- [ ] **SQL injection**: SQLAlchemy ORM used (no raw SQL)
- [ ] **Audit logging**: All admin actions logged with user + timestamp

### Secrets Management

| Secret | Where | Never |
|--------|-------|-------|
| `SECRET_KEY` | `.env` file | Git, logs, images |
| `POSTGRES_PASSWORD` | `.env` file | Git, logs, images |
| SMTP credentials | Vault / `.env` | Hardcoded |
| API keys | Vault / `.env` | Client-side |

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs <service>

# Common issues:
# - Port already in use → change port mapping in docker-compose.yml
# - .env missing → cp .env.example .env
# - Permission denied → check USER in Dockerfile
```

### Database connection refused

```bash
# Verify DB is healthy
docker compose ps

# Check DB logs
docker compose logs db

# Test connection manually
docker compose exec db psql -U prci -d prci_v2 -c "SELECT 1;"
```

### Nginx 502 Bad Gateway

```bash
# Backend not ready
docker compose ps backend

# Check backend health
curl http://localhost:8000/health/live

# Restart backend
docker compose restart backend
```

### Frontend shows "Please wait..." forever

```bash
# Streamlit Websocket issue → check nginx proxy headers
# Verify:
curl http://localhost:8501/_stcore/health
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `Dockerfile.backend` | FastAPI container build |
| `Dockerfile.frontend` | Streamlit container build |
| `docker-compose.yml` | Full stack orchestration |
| `nginx/nginx.conf` | Reverse proxy routing |
| `.env.example` | Environment template |
| `.dockerignore` | Exclude files from Docker context |
| `requirements-backend.txt` | Additional backend deps |

---

## Next Steps

1. ✅ Local Docker: `docker compose up --build`
2. ✅ Railway: Connect GitHub repo, add Postgres + env vars
3. ✅ AWS: ECR → ECS Fargate → ALB → Route 53
4. 🔄 Add CI/CD (GitHub Actions → build → push → deploy)
5. 🔄 Add monitoring (Prometheus + Grafana)
6. 🔄 Add automated backups
7. 🔄 Add Redis caching layer

---

**PRCI v2 is now deployable anywhere with one command.** 🔥
