# MH-CyberScore Infrastructure Skill

## Description
Guide for setting up the MH-CyberScore infrastructure — Docker Compose for local dev, Kubernetes for production, CI/CD pipelines, and monitoring. Use when creating Docker configurations, K8s manifests, CI/CD pipelines, or infrastructure-as-code.

## Local Development: Docker Compose

### Services Required
| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| backend | Custom (Dockerfile) | 8000 | FastAPI API |
| frontend | Custom (Dockerfile) | 3000 | Next.js App |
| postgres | postgres:16-alpine | 5432 | Main DB + TimescaleDB |
| redis | redis:7-alpine | 6379 | Cache + Celery broker |
| qdrant | qdrant/qdrant:latest | 6333 | Vector DB for RAG |
| minio | minio/minio:latest | 9000/9001 | Object storage |
| keycloak | quay.io/keycloak/keycloak:24 | 8080 | Auth SSO |
| celery-worker | Custom (backend image) | - | Celery workers |
| celery-beat | Custom (backend image) | - | Scheduled tasks |
| prometheus | prom/prometheus:latest | 9090 | Metrics |
| grafana | grafana/grafana:latest | 3001 | Dashboards |

### Docker Compose Pattern
```yaml
version: "3.9"

services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: mh_cyberscore
      POSTGRES_USER: ${DB_USER:-mhcs}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mhcs"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      MH_DATABASE_URL: postgresql+asyncpg://${DB_USER:-mhcs}:${DB_PASSWORD}@postgres:5432/mh_cyberscore
      MH_REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      MH_CELERY_BROKER_URL: redis://:${REDIS_PASSWORD}@redis:6379/1
      MH_KEYCLOAK_URL: http://keycloak:8080
      MH_DEBUG: "true"
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    command: npm run dev
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

### Backend Dockerfile Pattern
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile Pattern
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
```

## Production: Kubernetes on OVHcloud SecNumCloud

### Directory Structure
```
infra/
├── kubernetes/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── celery-deployment.yaml
│   │   └── ingress.yaml
│   └── overlays/
│       ├── dev/
│       ├── staging/
│       └── production/
├── terraform/           # OVHcloud provisioning
└── ansible/             # Server configuration
```

### Deployment Strategy
- Blue/Green deployment via Kubernetes
- Automatic rollback if health check fails
- DB migrations: Alembic with backward compatibility pre-check
- Feature flags for progressive AI agent deployment
- Backup: PostgreSQL WAL archiving + daily MinIO snapshot
- RTO: 4 hours | RPO: 1 hour

## CI/CD: GitLab CI (self-hosted)

### Pipeline Stages
```yaml
stages:
  - lint
  - test
  - security
  - build
  - deploy

lint:
  stage: lint
  script:
    - cd backend && ruff check . && mypy .
    - cd frontend && npm run lint && npm run type-check

test:
  stage: test
  script:
    - cd backend && pytest --cov=app --cov-report=xml
    - cd frontend && npm run test -- --coverage

security:
  stage: security
  script:
    - semgrep --config=auto backend/
    - trivy image $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - gitleaks detect --source=.
```

## Monitoring Stack
- **Prometheus** — metrics collection
- **Grafana** — dashboards & visualization
- **Loki** — log aggregation
- **PagerDuty** — on-call alerting (RSSI astreinte)

## Environment Variables Template (.env.example)
```bash
# Database
DB_USER=mhcs
DB_PASSWORD=
DATABASE_URL=postgresql+asyncpg://mhcs:password@localhost:5432/mh_cyberscore

# Redis
REDIS_PASSWORD=
REDIS_URL=redis://:password@localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://:password@localhost:6379/1

# Auth
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=mh-cyberscore
KEYCLOAK_CLIENT_ID=mh-cyberscore-api
KEYCLOAK_CLIENT_SECRET=
JWT_SECRET_KEY=

# LLM (sovereign, self-hosted)
VLLM_URL=http://localhost:8001
LLM_MODEL=mistralai/Mistral-Large-Instruct-2407

# OSINT API Keys
SHODAN_API_KEY=
CENSYS_API_ID=
CENSYS_API_SECRET=
VIRUSTOTAL_API_KEY=
HIBP_API_KEY=
ABUSEIPDB_API_KEY=

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=mh-cyberscore

# App
MH_DEBUG=true
MH_CORS_ORIGINS=["http://localhost:3000"]
```

## Sovereignty Constraints (NON-NEGOTIABLE)
- Compute: OVHcloud SecNumCloud ONLY
- NO AWS, GCP, Azure for data
- All images from European registries when possible
- TLS 1.3 exclusive (no TLS 1.2 fallback)
- Keys managed via HSM (Thales Luna or sovereign equivalent)
- Secrets via HashiCorp Vault (self-hosted)
