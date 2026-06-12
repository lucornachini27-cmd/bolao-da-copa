"""Testes do motor de pontuação (função pura) — pontuação ACUMULATIVA."""
from app.services.scoring_service import points_for

EXACT, RESULT = 2, 1  # bônus do placar exato e ponto do vencedor/empate


def test_cravou_o_placar_acumula():
    # Palpite 2x0, jogo 2x0: acertou o vencedor (1) + cravou o placar (2) = 3.
    assert points_for(2, 0, 2, 0, EXACT, RESULT) == EXACT + RESULT


def test_acertou_apenas_vencedor():
    # Palpite 1x0, jogo 2x0: só acertou quem ganhou = 1.
    assert points_for(1, 0, 2, 0, EXACT, RESULT) == RESULT


def test_cravou_empate_acumula():
    # Palpite 1x1, jogo 1x1: acertou o empate (1) + placar (2) = 3.
    assert points_for(1, 1, 1, 1, EXACT, RESULT) == EXACT + RESULT


def test_acertou_empate_sem_placar_exato():
    # Previu empate (1x1); real 2x2 → só o empate.
    assert points_for(1, 1, 2, 2, EXACT, RESULT) == RESULT


def test_errou_o_resultado():
    assert points_for(2, 1, 0, 2, EXACT, RESULT) == 0


def test_partida_sem_placar_ainda():
    assert points_for(1, 0, None, None, EXACT, RESULT) == 0


def test_pontuacao_e_configuravel():
    # Bônus de placar = 5, vencedor = 2 → cravar dá 5 + 2 = 7.
    assert points_for(0, 0, 0, 0, 5, 2) == 7
