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
        now = datetime.now(timezone.utc)
        
        # Encontra jogos que estão começando exatamento agora (ou já começaram) e ainda não enviou preview
        from datetime import timedelta
        horizon = now
        
        upcoming_matches = db.scalars(
            select(Match)
            .where(Match.utc_date <= horizon)
            .where(Match.status != "FINISHED")
            .where(Match.preview_sent == 0)
        ).all()

        for match in upcoming_matches:
            log.info(f"[bot] Gerando preview para jogo {match.id} (começando agora)")
            
            try:
                from app.services.image_generator_service import generate_preview_image
                image_path = generate_preview_image(db, match.id)
                
                caption = f"Palpites encerrados para o jogo {match.home_team} vs {match.away_team} 🔒\nConfira os palpites da galera:"
                target_group = getattr(settings, 'whatsapp_group_id', '')
                
                if target_group:
                    # Marca como enviado ANTES para evitar mensagens duplicadas em caso de timeout
                    match.preview_sent = 1
                    db.commit()
                    
                    success = whatsapp_service.send_image(target_group, image_path, caption)
                    if success:
                        log.info(f"[bot] Notificação de preview enviada para {match.id}")
                    else:
                        log.warning(f"[bot] Falha ao enviar preview, mas evitamos re-tentar para não causar spam.")
                else:
                    log.warning("whatsapp_group_id não configurado. Imagem gerada mas não enviada.")
                    
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
                from app.services.image_generator_service import generate_result_image
                result_path = generate_result_image(db, match.id)
                
                caption = "FIM DE JOGO! 🏁\nConfira o placar final e como ficou o ranking da galera:"
                target_group = getattr(settings, 'whatsapp_group_id', '')
                
                if target_group:
                    # Marca como enviado ANTES para evitar mensagens duplicadas em caso de timeout
                    match.result_sent = 1
                    db.commit()
                    
                    success = whatsapp_service.send_image(target_group, result_path, caption)
                    if success:
                        log.info(f"[bot] Notificação de resultado enviada para {match.id}")
                    else:
                        log.warning(f"[bot] Falha ao enviar resultado, mas evitamos re-tentar para não causar spam.")
                else:
                    log.warning("whatsapp_group_id não configurado. Imagem gerada mas não enviada.")
                    
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


def _ping_evolution_job() -> None:
    """Mantém a Evolution API acordada perto de eventos importantes."""
    db = SessionLocal()
    try:
        now = now_utc()
        from datetime import timedelta
        
        # Precisa estar acordada entre 20 min antes do jogo até 2 horas depois (se o preview falhou)
        upcoming_preview = db.scalars(
            select(Match)
            .where(Match.utc_date >= now - timedelta(minutes=120))
            .where(Match.utc_date <= now + timedelta(minutes=20))
            .where(Match.preview_sent == 0)
        ).first()

        # Precisa estar acordada a partir de 1h55m após o início até 6 horas depois (se o resultado falhou)
        # Removemos o .where(Match.status != "FINISHED") porque se a pessoa forçar o envio manual
        # de um jogo que JÁ está FINISHED, o Ping precisa acontecer do mesmo jeito!
        pending_result = db.scalars(
            select(Match)
            .where(Match.utc_date >= now - timedelta(hours=6))
            .where(Match.utc_date <= now - timedelta(minutes=115))
            .where(Match.result_sent == 0)
        ).first()

        if upcoming_preview or pending_result:
            evolution_url = getattr(settings, 'evolution_api_url', '')
            if evolution_url:
                import httpx
                # Apenas um ping leve para resetar o contador de inatividade do Render
                httpx.get(evolution_url, timeout=10.0)
                log.info(f"[smart-ping] Ping enviado para {evolution_url} para manter acordada.")
    except Exception as exc:
        log.warning("[smart-ping] falhou: %s", exc)
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler

    # --- FORÇAR REENVIO TEMPORÁRIO (Jogo Irã x Nova Zelândia) ---
    try:
        db = SessionLocal()
        m = db.get(Match, 760427)
        if m and m.preview_sent == 1:
            m.preview_sent = 0
            db.commit()
            log.info("Flag de envio do jogo 760427 resetada para disparar novamente!")
        db.close()
    except Exception as e:
        log.warning(f"Erro no reset temporário: {e}")
    # -------------------------------------------------------------

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
        next_run_time=datetime.now(timezone.utc),  # já sincroniza na subida
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
    
    # Ping Inteligente (roda a cada 5 minutos para manter a Evolution API acordada)
    _scheduler.add_job(
        _ping_evolution_job,
        trigger="interval",
        minutes=5,
        id="evolution_smart_ping",
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
