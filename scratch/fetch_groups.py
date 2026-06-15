import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")

if not API_URL:
    print("EVOLUTION_API_URL não encontrada no .env!")
    exit(1)

endpoint = f"{API_URL}/group/fetchAllGroups/{INSTANCE}?getParticipants=false"
headers = {"apikey": API_KEY}

print("Buscando grupos do WhatsApp na Evolution API...")
try:
    response = httpx.get(endpoint, headers=headers, timeout=60.0)
    response.raise_for_status()
    
    groups = response.json()
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    found = False
    for group in groups:
        group_id = group.get('id') or group.get('jid')
        group_name = group.get('subject') or group.get('name') or ""
        
        if "bolao world cup" in group_name.lower():
            print("\n🎉 ACHAMOS O SEU GRUPO!")
            print(f"Nome Exato: {group_name}")
            print(f"ID do Grupo: {group_id}\n")
            found = True
            
    if not found:
        print(f"\nNão encontrei nenhum grupo com 'Bolao world cup' no nome.")
        print("Tem certeza que o número do bot foi adicionado a este grupo?")
            
except Exception as e:
    print(f"Erro ao buscar grupos: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Detalhes: {e.response.text}")
