"""Motor de pontuação variável. Os pontos vêm da tabela settings (não hardcoded)."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.bet import Bet
from app.models.match import Match
from app.services import settings_service


def _sign(value: int) -> int:
    """-1, 0 ou 1: representa derrota/empate/vitória do mandante."""
    return (value > 0) - (value < 0)


def points_for(
    predicted_home: int,
    predicted_away: int,
    real_home: Optional[int],
    real_away: Optional[int],
    points_exact: int,
    points_result: int,
) -> int:
    """Pontos de um palpite — ACUMULATIVO.

    - Acertar o vencedor/empate soma `points_result`.
    - Cravar o placar exato soma `points_exact` por cima.
    Logo, cravar o placar = points_result + points_exact.
    """
    if real_home is None or real_away is None:
        return 0
    points = 0
    # Acertou quem ganhou (ou o empate)?
    if _sign(predicted_home - predicted_away) == _sign(real_home - real_away):
        points += points_result
    # Cravou o placar exato? (bônus que soma com o de cima)
    if predicted_home == real_home and predicted_away == real_away:
        points += points_exact
    return points


def recalculate_match(db: Session, match: Match) -> int:
    """Recalcula os pontos de todos os palpites de uma partida finalizada."""
    if match.status != "FINISHED" or match.score_home is None or match.score_away is None:
        return 0

    points_exact = settings_service.get_setting_int(db, "points_exact_score", 2)
    points_result = settings_service.get_setting_int(db, "points_correct_result", 1)

    bets = db.query(Bet).filter(Bet.match_id == match.id).all()
    changed = 0
    for bet in bets:
        new_points = points_for(
            bet.predicted_home,
            bet.predicted_away,
            match.score_home,
            match.score_away,
            points_exact,
            points_result,
        )
        if bet.points_earned != new_points:
            bet.points_earned = new_points
            changed += 1
    db.commit()
    return changed


def recalculate_all_finished(db: Session) -> int:
    """Recalcula todas as partidas finalizadas. Retorna nº de palpites atualizados."""
    total_changed = 0
    for match in db.query(Match).filter(Match.status == "FINISHED").all():
        total_changed += recalculate_match(db, match)
    return total_changed
