# Bolão da Copa — Backend (FastAPI)

App web responsivo para gerenciar um bolão da Copa do Mundo. Consome a
[football-data.org](https://www.football-data.org/) e calcula a pontuação dos palpites.

## Stack
- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic
- **Banco:** SQLite (MVP) → PostgreSQL (produção)
- **Auth:** JWT (PyJWT) + bcrypt
- **Frontend:** HTML + Tailwind (CDN) em cards responsivos

## Estrutura
```
app/          # aplicação (API que o front consome)
  core/       # config, database, security
  models/     # tabelas SQLAlchemy (users, matches, bets, settings)
  schemas/    # Pydantic (I/O + football_data.py = espelho do JSON da API)
  services/   # regras de negócio (consumo, sync, pontuação, bloqueio, ranking)
  api/v1/     # rotas REST
workers/      # ⭐ tarefas em segundo plano / cron (sync_matches, recalculate_scores)
scripts/      # init_db, seed_settings, create_admin
migrations/   # Alembic
frontend/     # index.html (Tailwind)
tests/        # pytest (pontuação e bloqueio)
```

## Setup (Windows / PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env   # edite o FOOTBALL_DATA_TOKEN e o SECRET_KEY

# Banco (MVP em SQLite):
python -m scripts.init_db          # cria as tabelas
python -m scripts.seed_settings    # popula a pontuação padrão (3 / 1 / 60)

# (opcional) cria um admin para editar a pontuação:
python -m scripts.create_admin admin@bolao.com senha123 "Admin"
```

## Rodar
```powershell
uvicorn app.main:app --reload          # API em http://localhost:8000
# Docs interativas: http://localhost:8000/docs
```
Abra `frontend/index.html` no navegador (a API permite CORS de qualquer origem em dev).

## Sincronizar dados da API
Manual:
```powershell
python -m workers.sync_matches         # busca, faz upsert e recalcula pontos
```
Agendado (escolha um):
- **Windows:** Agendador de Tarefas → Programa `python`, argumentos `-m workers.sync_matches`, "Iniciar em" = pasta do projeto.
- **Linux (cron, a cada 5 min):** `*/5 * * * * cd /proj && /proj/.venv/bin/python -m workers.sync_matches`
- **Produção escalável:** APScheduler embutido ou Celery + Redis (beat).

> **Free Tier:** ~10 req/min. Sincronize a cada 5–10 min; aumente a frequência só na janela dos jogos.

## Produção (PostgreSQL + Alembic)
```powershell
# DATABASE_URL=postgresql+psycopg://user:senha@host:5432/bolao  (no .env)
alembic revision --autogenerate -m "init schema"
alembic upgrade head
```

## Endpoints principais
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Cadastro |
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| GET  | `/api/v1/users/me` | Perfil (foto, pontos, posição) |
| GET  | `/api/v1/matches` | Lista de partidas (hora local + `is_open`) |
| POST | `/api/v1/bets` | Cria/edita palpite (valida bloqueio) |
| GET  | `/api/v1/bets/me` | Histórico vs. resultado real |
| GET  | `/api/v1/ranking` | Leaderboard |
| GET/PUT | `/api/v1/admin/settings` | Edita a pontuação (admin) |

## Testes
```powershell
pytest -q
```
