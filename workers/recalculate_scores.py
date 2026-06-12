"""Recalcula os pontos de todas as partidas finalizadas (sem chamar a API).

Útil após alterar a pontuação na tabela settings — reprocessa o histórico.
    python -m workers.recalculate_scores
"""
from app.core.database import SessionLocal
from app.services import scoring_service


def run() -> int:
    db = SessionLocal()
    try:
        return scoring_service.recalculate_all_finished(db)
    finally:
        db.close()


if __name__ == "__main__":
    print(f"[recalculate_scores] palpites atualizados: {run()}")
