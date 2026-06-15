import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import SessionLocal
from app.models.match import Match
from app.models.bet import Bet
from app.services import scoring_service, ranking_service

def test_live_scoring():
    db = SessionLocal()
    try:
        # Pega a primeira partida que tem apostas
        bet = db.query(Bet).first()
        if not bet:
            print("Nenhum palpite para testar.")
            return

        match = db.query(Match).filter(Match.id == bet.match_id).first()
        print(f"Modificando partida: {match.home_team} vs {match.away_team}")

        # Guarda os valores antigos
        old_status = match.status
        old_home = match.score_home
        old_away = match.score_away

        # Simula jogo ao vivo
        match.status = "IN_PLAY"
        match.score_home = 1
        match.score_away = 0
        db.commit()

        print("Recalculando pontos...")
        changed = scoring_service.recalculate_all_scorable(db)
        print(f"Palpites alterados: {changed}")

        ranking = ranking_service.compute(db)
        print("\nRanking Top 5 (com placar parcial):")
        for r in ranking[:5]:
            print(f"{r['position']}. {r['name']} - {r['total_points']} pts (Cravadas: {r['exact_hits']})")

        # Restaura os valores antigos
        match.status = old_status
        match.score_home = old_home
        match.score_away = old_away
        db.commit()

        print("\nRestaurando partida e recalculando...")
        scoring_service.recalculate_all_scorable(db)
        ranking_restored = ranking_service.compute(db)
        print("\nRanking Top 5 (original restaurado):")
        for r in ranking_restored[:5]:
            print(f"{r['position']}. {r['name']} - {r['total_points']} pts (Cravadas: {r['exact_hits']})")

    finally:
        db.close()

if __name__ == "__main__":
    test_live_scoring()
