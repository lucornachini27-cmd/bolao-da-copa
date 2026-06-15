import urllib.request, json, urllib.error

url = 'https://evolution-bolao-8b7u.onrender.com/message/sendText/BolaoBot'
headers = {'apikey': 'senha-bolao-123', 'Content-Type': 'application/json'}
payload = {
    "number": "5511919301236",
    "text": "Oi! 🤖 Este é um teste do robô do Bolão da Copa mandando mensagem direto da nuvem!"
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
try:
    response_body = urllib.request.urlopen(req).read()
    print("MENSAGEM ENVIADA COM SUCESSO!")
except urllib.error.HTTPError as e:
    print("ERRO:", e.read().decode('utf-8'))
