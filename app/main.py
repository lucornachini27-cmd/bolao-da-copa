"""Ponto de entrada da API FastAPI (serve também o frontend)."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.bootstrap import bootstrap
from app.core.config import settings
from app.core.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria tabelas, semeia configurações e o admin no primeiro boot.
    bootstrap()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# Token Bearer (sem cookies) → allow_credentials=False permite origin "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "app": settings.app_name}


# Serve o frontend (index.html, admin.html). Montado por ÚLTIMO para não
# atropelar as rotas /api/v1 e /health.
_frontend = Path(__file__).resolve().parent.parent / "frontend"
if _frontend.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
