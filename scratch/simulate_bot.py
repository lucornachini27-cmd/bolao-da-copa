import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import SessionLocal
from app.models.match import Match
from app.services.whatsapp_service import whatsapp_service

def simulate_notification():
    db = SessionLocal()
    try:
        # Pega o jogo do Canadá vs Bósnia
        match = db.query(Match).filter(Match.home_team.ilike('%Canada%'), Match.away_team.ilike('%Bosnia%')).first()
        if not match:
            # Tenta inverter caso a ordem seja Bósnia vs Canadá
            match = db.query(Match).filter(Match.home_team.ilike('%Bosnia%'), Match.away_team.ilike('%Canada%')).first()
        if not match:
            print("Nenhum jogo do Canadá encontrado!")
            return
            
        print(f"\nGerando RESULTADO REAL para o jogo: {match.home_team} vs {match.away_team}")
        from app.services.image_generator_service import generate_result_image
        
        # Envia a imagem de resultado com o placar do banco de dados
        result_path = generate_result_image(db, match.id)
        caption_result = "fimmmm de jogo!!!"
        target_group = "120363426735484014@g.us"
        
        print(f"Enviando RESULTADO para o grupo {target_group}...")
        success = whatsapp_service.send_image(target_group, result_path, caption_result)
        
        if success:
            print("\nNotificação enviada com sucesso para o grupo!")
        else:
            print("\nFalha ao enviar notificação!")
            
    finally:
        db.close()

if __name__ == "__main__":
    simulate_notification()
