r"""Job de sincronização (tarefa em segundo plano / cron).

Busca a tabela na football-data.org, faz UPSERT das partidas (PK = id da API)
e recalcula os pontos das partidas finalizadas.

Execute pelo agendador do sistema operacional:
    # Linux/macOS (crontab, a cada 5 min):
    #   */5 * * * * cd /caminho/projeto && /caminho/.venv/bin/python -m workers.sync_matches
    # Windows (Agendador de Tarefas):
    #   Programa: python   Argumentos: -m workers.sync_matches   Iniciar em: C:\...\bolão
"""
from app.core.database import SessionLocal
from app.services import football_api, sync_service


def run() -> dict:
    db = SessionLocal()
    try:
        return sync_service.run_full_sync(db)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        print("[sync_matches] OK:", run())
    except football_api.FootballApiError as exc:
        print("[sync_matches] ERRO de API:", exc)
        raise SystemExit(1)
