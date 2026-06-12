"""Inspeciona rapidamente o estado das partidas no banco.
    python -m scripts.db_stats
"""
from collections import Counter

import app.models  # noqa: F401
from app.core.database import SessionLocal
from app.models.match import Match
from app.utils.timezone import to_local


def main():
    db = SessionLocal()
    try:
        matches = db.query(Match).order_by(Match.utc_date).all()
        print(f"Total de partidas: {len(matches)}")
        if not matches:
            print("(banco vazio - rode a sincronizacao)")
            return
        print("Por status:", dict(Counter(m.status for m in matches)))
        first, last = matches[0], matches[-1]
        print("Primeira:", to_local(first.utc_date).strftime("%d/%m/%Y %H:%M"),
              f"{first.home_team} x {first.away_team}")
        print("Ultima:  ", to_local(last.utc_date).strftime("%d/%m/%Y %H:%M"),
              f"{last.home_team} x {last.away_team}")
        print("\nProximas 5 nao finalizadas:")
        upcoming = [m for m in matches if m.status != "FINISHED"][:5]
        for m in upcoming:
            print(f"  [{m.id}] {to_local(m.utc_date).strftime('%d/%m %H:%M')} "
                  f"{m.home_team} x {m.away_team} ({m.status})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
