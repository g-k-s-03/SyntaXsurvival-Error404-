# BloodBond — Documentation

## Repository structure
- **Frontend**: `FRONTEND/` (static HTML/CSS/JS)
- **Backend**: `BACKEND/` (FastAPI)

## Local development

### Backend (FastAPI)
From repo root:

```powershell
cd "BACKEND"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Check:
- `http://127.0.0.1:8001/health`
- `http://127.0.0.1:8001/docs`

### Frontend (static)
Important: serve **`FRONTEND/` as the site root** (not `FRONTEND/HTML`) so `../CSS` and `../JS` resolve correctly.

```powershell
cd "FRONTEND"
npx --yes serve
```

Open:
- `http://localhost:3000/HTML/landing.html`
- `http://localhost:3000/HTML/login.html`

## Environment variables

### Backend (`BACKEND/.env`)
Minimal keys:
- **DATABASE_URL**
  - Local SQLite (quick): `sqlite:///./bloodconnect.db`
  - Production: use Postgres on Render (recommended)
- **SECRET_KEY**: used for JWT signing + OTP hashing
- **CORS_ORIGINS**: comma-separated list of frontend origins
- **DEMO_MODE**: `true` for demo OTP
- **DEMO_OTP_CODE**: default `123456`

## OTP behavior
This project uses demo/offline OTP behavior:
- `POST /v1/auth/otp/send` returns `demo_otp` in the response (demo mode)
- Rate limiting / lockouts apply on the backend.

## Frontend ↔ Backend integration

### API base selection (important)
Frontend uses `Auth.apiFetch()` and reads the API base from:
1) `?api_base=https://.../v1` query param (stored to `localStorage` as `bc_api_base`)
2) default API base in `FRONTEND/JS/auth.js`

Recommended production entry URL:
- `/?api_base=https://<your-backend>.onrender.com/v1`

### CORS
On backend host, set `CORS_ORIGINS` to include your frontend origin, e.g.:
- `https://<your-vercel-site>.vercel.app`

## Deployment (recommended)

### Backend on Render
1) Create a **Postgres** database on Render.
2) Create a **Web Service** connected to your GitHub repo.
3) Configure:
   - **Root Directory**: `BACKEND`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4) Set Render env vars (minimum):
   - `DATABASE_URL` (Render internal Postgres URL)
   - `SECRET_KEY` (generate a strong one)
   - `DEMO_MODE=true`
   - `DEMO_OTP_CODE=123456`
   - `CORS_ORIGINS=https://<your-vercel-site>.vercel.app`
5) Verify:
   - `https://<your-render-service>.onrender.com/health`
   - `https://<your-render-service>.onrender.com/docs`

### Frontend on Vercel
1) Import the GitHub repo into Vercel.
2) Set **Root Directory** to `FRONTEND`.
3) Deploy.

This repo includes `FRONTEND/vercel.json` for redirects like:
- `/` → `/HTML/landing.html`

### Final production URL to share
Share the frontend URL with an explicit backend selection:
- `https://<your-vercel-site>.vercel.app/?api_base=https://<your-render-service>.onrender.com/v1`

## Troubleshooting

### “Access other apps/services on this device” browser prompt
This happens if a deployed site tries to call `http://localhost/...`.
Fix: open the site with `?api_base=https://<your-render-service>.onrender.com/v1` and ensure `bc_api_base` is not set to localhost.

### `/docs` shows Not Found
You’re likely hitting the wrong domain. Confirm `/health` works on the same base URL, then open `/docs` on that exact base.

