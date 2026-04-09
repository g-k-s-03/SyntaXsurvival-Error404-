# SyntaXsurvival-Error404- (BloodConnect)

## Frontend (static)
The HTML pages live in `FRONTEND/HTML/` and they reference assets via `../CSS/...` and `../JS/...`.

That means you should serve **`FRONTEND/` as the site root** (not `FRONTEND/HTML`), otherwise CSS/JS may not load on pages like `admin.html`.

Run:

```powershell
Set-Location "C:\Users\gs626\hakathon\SyntaXsurvival-Error404-\FRONTEND"
npx --yes serve
```

Open (examples):
- `http://localhost:3000/HTML/landing.html`
- `http://localhost:3000/HTML/login.html`
- `http://localhost:3000/HTML/admin.html`

## Backend (FastAPI)
Backend lives in `BACKEND/`.

Run:

```powershell
Set-Location "C:\Users\gs626\hakathon\SyntaXsurvival-Error404-\BACKEND"
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Check:
- `http://127.0.0.1:8001/health` should return `{"status":"ok"}`
- `http://127.0.0.1:8001/docs` for Swagger UI
