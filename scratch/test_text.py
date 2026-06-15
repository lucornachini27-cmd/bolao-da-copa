import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("EVOLUTION_API_URL")
API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE = os.getenv("EVOLUTION_INSTANCE_NAME")
TARGET_GROUP = "120363426735484014@g.us"

endpoint = f"{API_URL}/message/sendText/{INSTANCE}"
headers = {"apikey": API_KEY}
payload = {
    "number": TARGET_GROUP,
    "options": {"delay": 0, "presence": "composing"},
    "text": "👍"
}

print(f"Enviando mensagem para {TARGET_GROUP}...")
try:
    response = httpx.post(endpoint, headers=headers, json=payload, timeout=10.0)
    response.raise_for_status()
    print("Mensagem enviada com sucesso!")
except Exception as e:
    print(f"Erro ao enviar: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(e.response.text)
