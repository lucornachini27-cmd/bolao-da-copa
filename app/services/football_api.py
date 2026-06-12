"""Cliente da football-data.org. Autenticação via header X-Auth-Token."""
import httpx

from app.core.config import settings
from app.schemas.football_data import MatchesResponseDTO


class FootballApiError(Exception):
    """Erro ao consumir a API externa (rede, auth, rate limit, payload)."""


def _headers() -> dict:
    return {"X-Auth-Token": settings.football_data_token}


def fetch_matches(competition: str | None = None) -> MatchesResponseDTO:
    """GET /competitions/{code}/matches -> DTO validado.

    Free Tier: ~10 req/min. Trate 429 com backoff no agendador.
    """
    code = competition or settings.competition_code
    url = f"{settings.football_data_base_url}/competitions/{code}/matches"

    try:
        resp = httpx.get(url, headers=_headers(), timeout=30.0)
    except httpx.HTTPError as exc:
        raise FootballApiError(f"Falha de rede ao chamar a API: {exc}") from exc

    if resp.status_code == 429:
        raise FootballApiError("Rate limit atingido (Free Tier ~10 req/min).")
    if resp.status_code in (401, 403):
        raise FootballApiError(
            "Acesso negado: verifique o X-Auth-Token e se a competição está no seu plano."
        )
    if resp.status_code >= 400:
        raise FootballApiError(f"Erro {resp.status_code} da API: {resp.text[:200]}")

    return MatchesResponseDTO.model_validate(resp.json())
