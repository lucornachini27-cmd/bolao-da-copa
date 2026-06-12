import os
import tempfile
from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.bet import Bet
from app.models.user import User
from app.services import ranking_service
from app.services.screenshot_service import take_screenshot

TEAM_CODES = {
    "Algeria": "dz", "Argentina": "ar", "Australia": "au", "Austria": "at", "Belgium": "be",
    "Bosnia-Herz": "ba", "Brazil": "br", "Canada": "ca", "Cape Verde": "cv", "Colombia": "co",
    "Congo DR": "cd", "Croatia": "hr", "Curaçao": "cw", "Cura\u00e7ao": "cw", "Czechia": "cz",
    "Ecuador": "ec", "Egypt": "eg", "England": "gb-eng", "France": "fr", "Germany": "de",
    "Ghana": "gh", "Haiti": "ht", "Iran": "ir", "Iraq": "iq", "Ivory Coast": "ci",
    "Japan": "jp", "Jordan": "jo", "Mexico": "mx", "Morocco": "ma", "Netherlands": "nl",
    "New Zealand": "nz", "Norway": "no", "Panama": "pa", "Paraguay": "py", "Portugal": "pt",
    "Qatar": "qa", "Saudi Arabia": "sa", "Scotland": "gb-sct", "Senegal": "sn", "South Africa": "za",
    "South Korea": "kr", "Spain": "es", "Sweden": "se", "Switzerland": "ch", "Tunisia": "tn",
    "Türkiye": "tr", "T\u00fcrkiye": "tr", "USA": "us", "Uruguay": "uy", "Uzbekistan": "uz"
}

def get_team_crest(team_name, default_crest):
    clean_name = (team_name or "").strip()
    code = TEAM_CODES.get(clean_name)
    if code:
        return f"https://hatscripts.github.io/circle-flags/flags/{code}.svg"
    return default_crest or "https://placehold.co/40/f1f5f9/94a3b8?text=%20"


def generate_preview_image(db: Session, match_id: int) -> str:
    """Gera o screenshot de preview e retorna o caminho da imagem salva."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise ValueError(f"Match {match_id} not found")

    home_crest = get_team_crest(match.home_team, match.home_team_crest)
    away_crest = get_team_crest(match.away_team, match.away_team_crest)

    bets_query = db.query(Bet, User).join(User, Bet.user_id == User.id).filter(
        Bet.match_id == match.id,
        User.is_admin == False
    ).order_by(User.name).all()

    bets_list = []
    for bet, user in bets_query:
        bets_list.append({
            "name": user.name,
            "predicted_home": bet.predicted_home,
            "predicted_away": bet.predicted_away,
            "initial": user.name[0].upper() if user.name else "?",
            "photo_url": user.photo_url
        })

    ranking = ranking_service.compute(db)

    # Simplified HTML Generation
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bolão da Copa - Preview</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        :root {{
            --bg-primary: #f0fdf4; --card-bg: #ffffff; --text-main: #0f172a; --text-muted: #64748b;
            --emerald-primary: #10b981; --emerald-light: #ecfdf5; --emerald-dark: #047857;
            --border-color: #f1f5f9; --font-sans: 'Plus Jakarta Sans', sans-serif;
        }}
        body {{
            font-family: var(--font-sans); background-color: var(--bg-primary);
            background-image: radial-gradient(at 0% 0%, hsla(160, 84%, 85%, 0.4) 0px, transparent 50%),
                              radial-gradient(at 100% 0%, hsla(140, 93%, 90%, 0.3) 0px, transparent 50%);
            display: flex; justify-content: center; align-items: center;
            padding: 20px; margin: 0; gap: 20px; height: 100vh; box-sizing: border-box; overflow: hidden;
        }}
        .card {{
            background-color: var(--card-bg); border-radius: 20px; border: 1px solid rgba(226, 232, 240, 0.8);
            box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.06); padding: 20px; box-sizing: border-box;
        }}
        .card-bot {{ width: 390px; }} .card-ranking {{ width: 330px; }}
        .header {{ text-align: center; margin-bottom: 16px; }}
        .aviso-container {{
            display: inline-flex; align-items: center; gap: 6px; background-color: var(--emerald-light);
            color: var(--emerald-dark); padding: 6px 12px; border-radius: 9999px; font-weight: 700;
            font-size: 12px; text-transform: uppercase; margin-bottom: 16px;
        }}
        .matchup {{
            display: flex; align-items: center; justify-content: space-between;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); padding: 14px 20px;
            border-radius: 16px; border: 1px solid var(--border-color); margin-bottom: 16px; position: relative;
        }}
        .matchup::before {{ content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, #3b82f6, #10b981); opacity: 0.8; }}
        .team {{ display: flex; flex-direction: column; align-items: center; font-weight: 700; color: var(--text-main); font-size: 14px; width: 40%; gap: 6px; }}
        .flag-wrapper {{ width: 48px; height: 48px; background: white; border-radius: 50%; box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06); border: 2px solid #fff; overflow: hidden; }}
        .flag-img {{ width: 100%; height: 100%; object-fit: cover; }}
        .versus-badge {{ background-color: var(--text-main); color: white; font-size: 10px; font-weight: 800; padding: 4px 10px; border-radius: 9999px; z-index: 2; }}
        .palpites-title {{ font-size: 11px; color: var(--text-muted); text-align: center; margin-bottom: 12px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; font-weight: 800; text-transform: uppercase; }}
        .player-list {{ display: flex; flex-direction: column; gap: 2px; }}
        .player-row {{ display: flex; align-items: center; justify-content: space-between; padding: 8px 6px; border-radius: 12px; }}
        .player-info {{ display: flex; align-items: center; gap: 10px; }}
        .avatar {{ width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: white; overflow: hidden; }}
        .avatar-1 {{ background: linear-gradient(135deg, #6366f1, #4f46e5); }} .avatar-2 {{ background: linear-gradient(135deg, #ec4899, #d946ef); }}
        .avatar-3 {{ background: linear-gradient(135deg, #14b8a6, #0d9488); }} .avatar-4 {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .avatar-5 {{ background: linear-gradient(135deg, #ef4444, #dc2626); }} .avatar-6 {{ background: linear-gradient(135deg, #8b5cf6, #7c3aed); }}
        .player-name {{ font-size: 13px; color: #334155; font-weight: 600; }}
        .score-pill {{ font-size: 14px; font-weight: 800; color: var(--text-main); background-color: #f1f5f9; width: 72px; padding: 5px 0; text-align: center; border-radius: 8px; border: 1px solid rgba(226, 232, 240, 0.5); }}
        
        .ranking-title-container {{ display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 800; color: var(--text-main); margin-bottom: 16px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }}
        .rank-list {{ display: flex; flex-direction: column; gap: 4px; }}
        .rank-item {{ display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 12px; }}
        .rank-left {{ display: flex; align-items: center; gap: 10px; }}
        .rank-position {{ width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800; color: var(--text-muted); border-radius: 50%; }}
        .rank-item.top-1 .rank-position, .rank-item.top-2 .rank-position, .rank-item.top-3 .rank-position {{ font-size: 16px; }}
        .avatar-gold {{ border: 2px solid #fbbf24; background: linear-gradient(135deg, #fef3c7, #fde68a); color: #b45309; }}
        .avatar-silver {{ border: 2px solid #cbd5e1; background: linear-gradient(135deg, #f1f5f9, #e2e8f0); color: #475569; }}
        .avatar-bronze {{ border: 2px solid #fed7aa; background: linear-gradient(135deg, #ffedd5, #fed7aa); color: #c2410c; }}
        .rank-points {{ font-size: 14px; font-weight: 800; color: var(--emerald-primary); background-color: var(--emerald-light); width: 66px; padding: 3px 0; text-align: center; border-radius: 8px; }}
        .rank-points-neutral {{ font-size: 13px; font-weight: 700; color: var(--text-muted); width: 66px; padding: 3px 0; text-align: center; }}
    </style>
</head>
<body>
    <div class="card card-bot">
        <div class="header">
            <div class="aviso-container"><div class="dot" style="background: var(--emerald-dark);"></div> O jogo vai começar!</div>
            <div class="matchup">
                <div class="team"><div class="flag-wrapper"><img src="{home_crest}" class="flag-img"></div><span>{match.home_team}</span></div>
                <div class="versus-badge">VS</div>
                <div class="team"><div class="flag-wrapper"><img src="{away_crest}" class="flag-img"></div><span>{match.away_team}</span></div>
            </div>
        </div>
        <div class="palpites-title">Palpites da Galera ({len(bets_list)})</div>
        <div class="player-list">"""

    avatar_index = 1
    for b in bets_list:
        photo = b.get('photo_url')
        if photo:
            avatar_html = f"""<div class="avatar"><img src="{photo}" style="width: 100%; height: 100%; object-fit: cover;"></div>"""
        else:
            avatar_html = f"""<div class="avatar avatar-{avatar_index}">{b['initial']}</div>"""
        html += f"""<div class="player-row"><div class="player-info">{avatar_html}<div class="player-name">{b['name']}</div></div><div class="score-pill">{b['predicted_home']} - {b['predicted_away']}</div></div>"""
        avatar_index = (avatar_index % 6) + 1

    html += """</div></div>
    <div class="card card-ranking"><div class="ranking-title-container"><div class="diamond" style="background: #f59e0b;"></div><span>Ranking Geral</span></div><div class="rank-list">"""

    for r in ranking:
        pos = r['position']
        name = r['name']
        points = r['total_points']
        photo = r.get('photo_url')
        initial = name[0].upper() if name else "?"
        
        if photo:
            avatar_html = f"""<div class="avatar"><img src="{photo}" style="width: 100%; height: 100%; object-fit: cover;"></div>"""
        else:
            if pos == 1:
                avatar_html = f"""<div class="avatar avatar-gold">{initial}</div>"""
            elif pos == 2:
                avatar_html = f"""<div class="avatar avatar-silver">{initial}</div>"""
            elif pos == 3:
                avatar_html = f"""<div class="avatar avatar-bronze">{initial}</div>"""
            else:
                avatar_html = f"""<div class="avatar avatar-{(pos % 6) + 1}">{initial}</div>"""

        if pos == 1:
            item_class, pos_label, points_label = "rank-item top-1", "1", f'<div class="rank-points">{points} {"pts" if points != 1 else "pt"}</div>'
        elif pos == 2:
            item_class, pos_label, points_label = "rank-item top-2", "2", f'<div class="rank-points">{points} {"pts" if points != 1 else "pt"}</div>'
        elif pos == 3:
            item_class, pos_label, points_label = "rank-item top-3", "3", f'<div class="rank-points">{points} {"pts" if points != 1 else "pt"}</div>'
        else:
            item_class, pos_label, points_label = "rank-item", str(pos), f'<div class="rank-points-neutral">{points} {"pts" if points != 1 else "pt"}</div>'
        
        html += f"""<div class="{item_class}"><div class="rank-left"><div class="rank-position">{pos_label}</div>{avatar_html}<div class="player-name">{name}</div></div>{points_label}</div>"""

    html += "</div></div></body></html>"

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        temp_html_path = f.name

    output_image_path = os.path.join(tempfile.gettempdir(), f"preview_match_{match_id}.png")
    take_screenshot(temp_html_path, output_image_path)
    
    try:
        os.remove(temp_html_path)
    except:
        pass
        
    return output_image_path

def generate_result_image(db: Session, match_id: int, mock_score=None) -> str:
    """Gera o screenshot de fim de jogo (resultado)."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise ValueError(f"Match {match_id} not found")

    home_crest = get_team_crest(match.home_team, match.home_team_crest)
    away_crest = get_team_crest(match.away_team, match.away_team_crest)

    final_home = mock_score[0] if mock_score else match.score_home
    final_away = mock_score[1] if mock_score else match.score_away

    if final_home is None or final_away is None:
        final_home, final_away = 0, 0

    bets_query = db.query(Bet, User).join(User, Bet.user_id == User.id).filter(
        Bet.match_id == match.id,
        User.is_admin == False
    ).order_by(User.name).all()

    bets_list = []
    for bet, user in bets_query:
        # Calculate points
        pts = 0
        if bet.predicted_home == final_home and bet.predicted_away == final_away:
            pts = 3
        elif (bet.predicted_home > bet.predicted_away and final_home > final_away) or \
             (bet.predicted_home < bet.predicted_away and final_home < final_away) or \
             (bet.predicted_home == bet.predicted_away and final_home == final_away):
            pts = 1

        bets_list.append({
            "name": user.name,
            "predicted_home": bet.predicted_home,
            "predicted_away": bet.predicted_away,
            "points": pts,
            "initial": user.name[0].upper() if user.name else "?",
            "photo_url": user.photo_url
        })

    # Sort bets by points descending
    bets_list.sort(key=lambda x: x["points"], reverse=True)
    ranking = ranking_service.compute(db)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bolão da Copa - Resultado</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
        :root {{
            --bg-primary: #f0fdf4; --card-bg: #ffffff; --text-main: #0f172a; --text-muted: #64748b;
            --emerald-primary: #10b981; --emerald-light: #ecfdf5; --emerald-dark: #047857;
            --border-color: #f1f5f9; --font-sans: 'Plus Jakarta Sans', sans-serif;
        }}
        body {{
            font-family: var(--font-sans); background-color: var(--bg-primary);
            background-image: radial-gradient(at 0% 0%, hsla(160, 84%, 85%, 0.4) 0px, transparent 50%),
                              radial-gradient(at 100% 0%, hsla(140, 93%, 90%, 0.3) 0px, transparent 50%);
            display: flex; justify-content: center; align-items: center;
            padding: 20px; margin: 0; gap: 20px; height: 100vh; box-sizing: border-box; overflow: hidden;
        }}
        .card {{
            background-color: var(--card-bg); border-radius: 20px; border: 1px solid rgba(226, 232, 240, 0.8);
            box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.06); padding: 20px; box-sizing: border-box;
        }}
        .card-bot {{ width: 390px; }} .card-ranking {{ width: 330px; }}
        .header {{ text-align: center; margin-bottom: 16px; }}
        .aviso-container {{
            display: inline-flex; align-items: center; gap: 6px; background-color: #fef2f2;
            color: #b91c1c; padding: 6px 12px; border-radius: 9999px; font-weight: 800;
            font-size: 12px; text-transform: uppercase; margin-bottom: 16px; border: 1px solid #fca5a5;
        }}
        .matchup {{
            display: flex; align-items: center; justify-content: space-between;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); padding: 16px 20px;
            border-radius: 16px; border: 1px solid var(--border-color); margin-bottom: 16px; position: relative;
        }}
        .matchup::before {{ content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, #ef4444, #f59e0b); opacity: 0.8; }}
        .team {{ display: flex; flex-direction: column; align-items: center; font-weight: 700; color: var(--text-main); font-size: 14px; width: 30%; gap: 6px; }}
        .flag-wrapper {{ width: 56px; height: 56px; background: white; border-radius: 50%; box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06); border: 2px solid #fff; overflow: hidden; }}
        .flag-img {{ width: 100%; height: 100%; object-fit: cover; }}
        .score-board {{ display: flex; align-items: center; gap: 8px; font-size: 28px; font-weight: 900; color: var(--text-main); }}
        .score-box {{ background: white; padding: 4px 12px; border-radius: 8px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
        .palpites-title {{ font-size: 11px; color: var(--text-muted); text-align: center; margin-bottom: 12px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; font-weight: 800; text-transform: uppercase; }}
        .player-list {{ display: flex; flex-direction: column; gap: 4px; }}
        .player-row {{ display: flex; align-items: center; justify-content: space-between; padding: 6px 8px; border-radius: 12px; background-color: #f8fafc; border: 1px solid #f1f5f9; }}
        .player-row.winner-3 {{ background-color: #ecfdf5; border-color: #d1fae5; }}
        .player-row.winner-1 {{ background-color: #f0fdfa; border-color: #ccfbf1; }}
        .player-row.loser {{ opacity: 0.7; }}
        .player-info {{ display: flex; align-items: center; gap: 10px; }}
        .avatar {{ width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: white; overflow: hidden; }}
        .avatar-1 {{ background: linear-gradient(135deg, #6366f1, #4f46e5); }} .avatar-2 {{ background: linear-gradient(135deg, #ec4899, #d946ef); }}
        .avatar-3 {{ background: linear-gradient(135deg, #14b8a6, #0d9488); }} .avatar-4 {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .avatar-5 {{ background: linear-gradient(135deg, #ef4444, #dc2626); }} .avatar-6 {{ background: linear-gradient(135deg, #8b5cf6, #7c3aed); }}
        .player-name {{ font-size: 13px; color: #334155; font-weight: 600; }}
        .bet-info {{ display: flex; align-items: center; gap: 8px; }}
        .bet-score {{ font-size: 13px; font-weight: 700; color: var(--text-muted); background: white; padding: 2px 8px; border-radius: 6px; border: 1px solid #e2e8f0; }}
        .points-badge {{ font-size: 12px; font-weight: 800; padding: 2px 8px; border-radius: 6px; width: 44px; text-align: center; }}
        .points-3 {{ background-color: #10b981; color: white; }}
        .points-1 {{ background-color: #3b82f6; color: white; }}
        .points-0 {{ background-color: #cbd5e1; color: #64748b; }}
        
        .ranking-title-container {{ display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 800; color: var(--text-main); margin-bottom: 16px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }}
        .rank-list {{ display: flex; flex-direction: column; gap: 4px; }}
        .rank-item {{ display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 12px; }}
        .rank-left {{ display: flex; align-items: center; gap: 10px; }}
        .rank-position {{ width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800; color: var(--text-muted); border-radius: 50%; }}
        .rank-item.top-1 .rank-position, .rank-item.top-2 .rank-position, .rank-item.top-3 .rank-position {{ font-size: 16px; }}
        .avatar-gold {{ border: 2px solid #fbbf24; background: linear-gradient(135deg, #fef3c7, #fde68a); color: #b45309; }}
        .avatar-silver {{ border: 2px solid #cbd5e1; background: linear-gradient(135deg, #f1f5f9, #e2e8f0); color: #475569; }}
        .avatar-bronze {{ border: 2px solid #fed7aa; background: linear-gradient(135deg, #ffedd5, #fed7aa); color: #c2410c; }}
        .rank-points {{ font-size: 14px; font-weight: 800; color: var(--emerald-primary); background-color: var(--emerald-light); width: 66px; padding: 3px 0; text-align: center; border-radius: 8px; }}
        .rank-points-neutral {{ font-size: 13px; font-weight: 700; color: var(--text-muted); width: 66px; padding: 3px 0; text-align: center; }}
    </style>
</head>
<body>
    <div class="card card-bot">
        <div class="header">
            <div class="aviso-container"><div class="dot" style="background: #b91c1c;"></div> FIM DE JOGO</div>
            <div class="matchup">
                <div class="team"><div class="flag-wrapper"><img src="{home_crest}" class="flag-img"></div><span>{match.home_team}</span></div>
                <div class="score-board"><div class="score-box">{final_home}</div><span>-</span><div class="score-box">{final_away}</div></div>
                <div class="team"><div class="flag-wrapper"><img src="{away_crest}" class="flag-img"></div><span>{match.away_team}</span></div>
            </div>
        </div>
        <div class="palpites-title">Pontuação da Rodada</div>
        <div class="player-list">"""

    avatar_index = 1
    for b in bets_list:
        pts = b['points']
        row_class = f"winner-{pts}" if pts > 0 else "loser"
        points_class = f"points-{pts}"
        
        photo = b.get('photo_url')
        if photo:
            avatar_html = f"""<div class="avatar"><img src="{photo}" style="width: 100%; height: 100%; object-fit: cover;"></div>"""
        else:
            avatar_html = f"""<div class="avatar avatar-{avatar_index}">{b['initial']}</div>"""
            
        html += f"""<div class="player-row {row_class}">
            <div class="player-info">{avatar_html}<div class="player-name">{b['name']}</div></div>
            <div class="bet-info"><div class="bet-score">{b['predicted_home']} - {b['predicted_away']}</div><div class="points-badge {points_class}">+{pts}</div></div>
        </div>"""
        avatar_index = (avatar_index % 6) + 1

    html += """</div></div>
    <div class="card card-ranking"><div class="ranking-title-container"><div class="diamond" style="background: #f59e0b;"></div><span>Ranking Atualizado</span></div><div class="rank-list">"""

    for r in ranking:
        pos = r['position']
        name = r['name']
        points = r['total_points']
        photo = r.get('photo_url')
        initial = name[0].upper() if name else "?"
        
        if photo:
            avatar_html = f"""<div class="avatar"><img src="{photo}" style="width: 100%; height: 100%; object-fit: cover;"></div>"""
        else:
            if pos == 1:
                avatar_html = f"""<div class="avatar avatar-gold">{initial}</div>"""
            elif pos == 2:
                avatar_html = f"""<div class="avatar avatar-silver">{initial}</div>"""
            elif pos == 3:
                avatar_html = f"""<div class="avatar avatar-bronze">{initial}</div>"""
            else:
                avatar_html = f"""<div class="avatar avatar-{(pos % 6) + 1}">{initial}</div>"""

        if pos == 1:
            item_class, pos_label, points_label = "rank-item top-1", "1", f'<div class="rank-points">{points} {"pts" if points != 1 else "pt"}</div>'
        elif pos == 2:
            item_class, pos_label, points_label = "rank-item top-2", "2", f'<div class="rank-points">{points} {"pts" if points != 1 else "pt"}</div>'
        elif pos == 3:
            item_class, pos_label, points_label = "rank-item top-3", "3", f'<div class="rank-points">{points} {"pts" if points != 1 else "pt"}</div>'
        else:
            item_class, pos_label, points_label = "rank-item", str(pos), f'<div class="rank-points-neutral">{points} {"pts" if points != 1 else "pt"}</div>'
        
        html += f"""<div class="{item_class}"><div class="rank-left"><div class="rank-position">{pos_label}</div>{avatar_html}<div class="player-name">{name}</div></div>{points_label}</div>"""

    html += "</div></div></body></html>"

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        temp_html_path = f.name

    output_image_path = os.path.join(tempfile.gettempdir(), f"result_match_{match_id}.png")
    take_screenshot(temp_html_path, output_image_path)
    
    try:
        os.remove(temp_html_path)
    except:
        pass
        
    return output_image_path
