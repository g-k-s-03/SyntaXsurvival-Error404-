from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.database import init_db
from app.routers import auth, directory, health, me, profiles

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
    except OperationalError as exc:
        raise RuntimeError(
            "Database unreachable (is PostgreSQL running on DATABASE_URL?). "
            "From the BACKEND folder run: docker compose up -d "
            "then retry. See .env.example for connection defaults."
        ) from exc
    yield


app = FastAPI(title="BloodConnect API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/v1")
app.include_router(me.router, prefix="/v1")
app.include_router(profiles.router, prefix="/v1")
app.include_router(directory.router, prefix="/v1")
