"""Agendador em segundo plano: sincroniza com a ESPN a cada N minutos.

Roda dentro do processo do servidor (BackgroundScheduler). No Render free, o
serviço dorme quando ocioso — ao acordar, o agendador reinicia e já sincroniza.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.services import sync_service

log = logging.getLogger("uvicorn.error")
_scheduler: Optional[BackgroundScheduler] = None


def _sync_job() -> None:
    db = SessionLocal()
    try:
        stats = sync_service.run_full_sync(db)
        log.info("[auto-sync] %s", stats)
    except Exception as exc:  # nunca derruba o agendador
        log.warning("[auto-sync] falhou: %s", exc)
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    minutes = settings.auto_sync_minutes
    if minutes <= 0 or _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True, timezone="UTC")
    _scheduler.add_job(
        _sync_job,
        trigger="interval",
        minutes=minutes,
        id="espn_sync",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(timezone.utc),  # já sincroniza na subida
    )
    _scheduler.start()
    log.info("Agendador ESPN ativo: sincroniza a cada %s min.", minutes)


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
