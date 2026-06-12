"""Configuração central da aplicação (lida de variáveis de ambiente / .env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bolão da Copa"

    # Banco: SQLite no MVP, PostgreSQL em produção.
    database_url: str = "sqlite:///./bolao.db"

    # football-data.org (legado — substituído pela ESPN)
    football_data_token: str = ""
    football_data_base_url: str = "https://api.football-data.org/v4"
    competition_code: str = "WC"

    # ESPN scoreboard (fonte atual: pública, em tempo real, sem chave)
    espn_scoreboard_url: str = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
    )
    espn_dates: str = "20260611-20260719"  # janela da Copa 2026 (YYYYMMDD-YYYYMMDD)

    # Sincronização automática com a ESPN (minutos; 0 desliga).
    auto_sync_minutes: int = 10

    # Auth (JWT)
    secret_key: str = "CHANGE_ME_dev_only_nao_use_em_producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 dias

    # Localização
    local_timezone: str = "America/Sao_Paulo"

    # Fallback do bloqueio de palpite (a fonte real é a tabela settings).
    bet_lock_minutes_default: int = 60

    # Bootstrap do admin no primeiro deploy (via variáveis de ambiente).
    bootstrap_admin_user: str = ""
    bootstrap_admin_password: str = ""

    # Evolution API (WhatsApp)
    evolution_api_url: str = ""
    evolution_api_key: str = ""
    evolution_instance_name: str = ""
    whatsapp_target_number: str = "" # Número ou ID do grupo para onde enviar

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
