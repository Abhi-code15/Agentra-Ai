# AGENTRA — Deployment & Operations Guide

**Document Version:** 1.0.0  
**Status:** Approved for Review  
**Date:** 2026-11-12  

---

## 1. Local Development Setup (Windows PowerShell)

### 1.1 Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 15+ (Local or via Docker)
- Git for Windows

### 1.2 Backend Initialization
```powershell
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment configuration
Copy-Item .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 1.3 Frontend Initialization
```powershell
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

---

## 2. Docker Compose Deployment

Agentra provides a production-grade multi-container `docker-compose.yml` comprising:
1. `agentra-db`: PostgreSQL 15 with healthcheck and persistent volume.
2. `agentra-backend`: FastAPI running under Uvicorn with non-root security.
3. `agentra-frontend`: React application built and served via NGINX.

```powershell
# Start all containers in background
docker compose up -d --build

# View container status
docker compose ps

# Inspect logs
docker compose logs -f agentra-backend

# Execute migrations inside running container
docker compose exec agentra-backend alembic upgrade head
```

---

## 3. Environment Variable Specification

| Variable Name | Required | Default / Example | Purpose |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Yes | `development` / `production` | Application runtime mode |
| `APP_NAME` | No | `Agentra` | Platform display name |
| `DATABASE_URL` | Yes | `postgresql+psycopg2://user:pass@localhost:5432/agentra_db` | PostgreSQL connection URI |
| `GEMINI_API_KEY` | Yes | `AIzaSy...` | Google Gen AI API authentication key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model identifier |
| `JWT_SECRET_KEY` | Yes | `min-32-chars-random-secret` | Key for signing JWT access tokens |
| `JWT_ALGORITHM` | No | `HS256` | Cryptographic algorithm for JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | JWT access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh session duration |
| `STORAGE_DIRECTORY` | No | `./storage/documents` | Path for private document storage |
| `MAX_UPLOAD_SIZE_BYTES` | No | `26214400` | Maximum upload size (25 MB) |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Allowed web origins |
| `LOG_LEVEL` | No | `INFO` | Logging threshold (`DEBUG`, `INFO`, `WARNING`) |

---

## 4. Health & Readiness Verification

- **Liveness:** `GET http://localhost:8000/health` $\to$ Returns HTTP 200 `{ "status": "healthy" }`.
- **Readiness:** `GET http://localhost:8000/ready` $\to$ Verifies PostgreSQL connection pool checkout and storage directory writeability.
