import urllib.request
import urllib.error
import json
import time
import base64
import os

API_URL = "https://evolution-bolao-8b7u.onrender.com"
API_KEY = "senha-bolao-123"
INSTANCE_NAME = "BolaoBot"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "instanceName": INSTANCE_NAME,
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(f"{API_URL}/instance/create", data=data, headers=headers, method="POST")

print(f"Criando sessão e buscando QR Code em {API_URL}...")
try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        base64_img = res_data.get("base64", "")
        
        if not base64_img:
            print("Não retornou base64. O WhatsApp pode já estar conectado!")
            print(res_data)

        if base64_img:
            if "," in base64_img:
                base64_img = base64_img.split(",")[1]
                
            img_data = base64.b64decode(base64_img)
            img_path = r"C:\Users\lucor\.gemini\antigravity\brain\014e5dd6-46ed-4839-90d5-6b87b7cb35c3\qrcode_whatsapp.png"
            
            with open(img_path, "wb") as f:
                f.write(img_data)
                
            print(f"\n[SUCESSO] QR Code salvo! Abra a imagem em: {img_path}")
            os.system(f'start "" "{img_path}"')
        else:
            print("\nSessão criada, mas não retornou QR Code. Ele pode já estar conectado.")
            print(res_data)
except urllib.error.HTTPError as e:
    print(f"\nErro ao criar instância ({e.code}): {e.read().decode('utf-8')}")
except Exception as e:
    print(f"\nErro genérico: {e}")
