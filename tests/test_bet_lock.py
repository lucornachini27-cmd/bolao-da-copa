"""Testes da regra de bloqueio de palpite (função pura is_open_at)."""
from datetime import datetime, timedelta, timezone

from app.services.bet_service import is_open_at, teams_defined

UTC = timezone.utc


def test_aberto_bem_antes_do_jogo():
    now = datetime.now(UTC)
    kickoff = now + timedelta(hours=3)
    assert is_open_at("SCHEDULED", kickoff, now, 60) is True


def test_travado_dentro_da_ultima_hora():
    now = datetime.now(UTC)
    kickoff = now + timedelta(minutes=59)
    assert is_open_at("TIMED", kickoff, now, 60) is False


def test_travado_na_borda_exata_de_60min():
    now = datetime.now(UTC)
    kickoff = now + timedelta(minutes=60)
    assert is_open_at("SCHEDULED", kickoff, now, 60) is False


def test_travado_por_status_em_andamento():
    now = datetime.now(UTC)
    kickoff = now + timedelta(hours=2)
    assert is_open_at("IN_PLAY", kickoff, now, 60) is False


def test_lock_configuravel_30min():
    now = datetime.now(UTC)
    kickoff = now + timedelta(minutes=45)
    # Com bloqueio de 30 min, 45 min antes ainda está aberto.
    assert is_open_at("SCHEDULED", kickoff, now, 30) is True


def test_selecoes_definidas():
    assert teams_defined("Brazil", "Argentina") is True


def test_selecao_indefinida_fecha_palpite():
    assert teams_defined("A definir", "Brazil") is False
    assert teams_defined("Brazil", "A definir") is False
    assert teams_defined("A definir", "A definir") is False
