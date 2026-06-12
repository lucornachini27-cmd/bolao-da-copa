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

from app.services import sync_service, screenshot_service
from app.services.whatsapp_service import whatsapp_service
from app.models.match import Match
from sqlalchemy import select

log = logging.getLogger("uvicorn.error")
_scheduler: Optional[BackgroundScheduler] = None


def _bot_notification_job() -> None:
    db = SessionLocal()
    try:
        now = now_utc()
        
        # Encontra jogos que começam em 15 minutos ou menos e ainda não enviou preview
        from datetime import timedelta
        horizon = now + timedelta(minutes=15)
        
        upcoming_matches = db.scalars(
            select(Match)
            .where(Match.utc_date <= horizon)
            .where(Match.status != "FINISHED")
            .where(Match.preview_sent == 0)
        ).all()

        for match in upcoming_matches:
            log.info(f"[bot] Gerando preview para jogo {match.id} (começa em breve)")
            
            try:
                from app.services.image_generator_service import generate_preview_image
                image_path = generate_preview_image(db, match.id)
                
                caption = f"🚨 Apostas Fechadas para {match.home_team} vs {match.away_team}!\nConfira os palpites da galera:"
                target_number = getattr(settings, 'whatsapp_target_number', '')
                
                if target_number:
                    success = whatsapp_service.send_image(target_number, image_path, caption)
                    if success:
                        match.preview_sent = 1
                        db.commit()
                        log.info(f"[bot] Notificação de preview enviada para {match.id}")
                else:
                    log.warning("whatsapp_target_number não configurado. Imagem gerada mas não enviada.")
                    
            except Exception as e:
                log.error(f"[bot] Falha ao gerar/enviar preview do jogo {match.id}: {e}")

        # 2. Encontra jogos que acabaram de finalizar e não enviaram resultado
        finished_matches = db.scalars(
            select(Match)
            .where(Match.status == "FINISHED")
            .where(Match.result_sent == 0)
        ).all()

        for match in finished_matches:
            log.info(f"[bot] Gerando resultado para jogo {match.id} (finalizado)")
            try:
                # TODO: We would call generate_result_image here similar to preview
                # For now, let's just mark it as sent so it doesn't loop
                match.result_sent = 1
                db.commit()
                log.info(f"[bot] Notificação de resultado marcada como enviada para {match.id}")
            except Exception as e:
                log.error(f"[bot] Falha ao processar resultado do jogo {match.id}: {e}")

    except Exception as exc:
        log.warning("[bot-notification] falhou: %s", exc)
    finally:
        db.close()

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
    
    # Sincronização ESPN
    _scheduler.add_job(
        _sync_job,
        trigger="interval",
        minutes=minutes,
        id="espn_sync",
        max_instances=1,
        coalesce=True,
        next_run_time=now_utc(),  # já sincroniza na subida
    )
    
    # Job do Bot (roda a cada minuto para ser preciso na checagem dos 15 minutos)
    _scheduler.add_job(
        _bot_notification_job,
        trigger="interval",
        minutes=1,
        id="bot_notification",
        max_instances=1,
        coalesce=True
    )
    
    _scheduler.start()
    log.info("Agendador ESPN ativo: sincroniza a cada %s min.", minutes)


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
