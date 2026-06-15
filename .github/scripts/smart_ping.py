import urllib.request
import json
import datetime
import os

# URLs para ping. Como é apenas para acordar, a raiz "/" é suficiente.
BOLAO_URL = os.environ.get("URL_BOLAO", "")
EVOLUTION_URL = os.environ.get("URL_EVOLUTION", "")
ESPN_API = "http://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

def ping_urls():
    urls_to_ping = [url for url in [BOLAO_URL, EVOLUTION_URL] if url]
    if not urls_to_ping:
        print("Nenhuma URL configurada nos secrets do GitHub.")
        return
        
    for url in urls_to_ping:
        try:
            print(f"Acordando {url} ...")
            # Timeout curto, se a máquina acordar demorar, não tem problema, o Ping já foi registrado pelo Render!
            req = urllib.request.Request(url, headers={'User-Agent': 'SmartKeeper/1.0'})
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            # Erros de timeout (502, socket) são normais e esperados durante um cold start do Render.
            print(f"Ping result for {url}: {e} (O Render já deve estar ligando a máquina!)")

def main():
    try:
        req = urllib.request.Request(ESPN_API, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
    except Exception as e:
        print(f"Erro ao buscar ESPN API: {e}")
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    should_ping = False
    reasons = []

    if 'events' not in data:
        print("Nenhum evento retornado pela ESPN hoje.")
        return

    for event in data['events']:
        # Data do jogo ex: "2026-06-12T16:00:00Z"
        date_str = event.get('date')
        if not date_str:
            continue
            
        start_time = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        status_name = event.get('status', {}).get('type', {}).get('name', 'UNKNOWN')
        
        # 1. Preview (Ligamos 20 minutos antes e mantemos até 5 mins depois)
        preview_start = start_time - datetime.timedelta(minutes=20)
        preview_end = start_time + datetime.timedelta(minutes=5)
        
        # 2. Resultado (Ligamos 1 hora e 55 minutos depois do começo)
        result_check_start = start_time + datetime.timedelta(minutes=115)
        # E mantemos ligada enquanto o jogo não for dado como encerrado (limitado a 4h de segurança)
        result_check_end = start_time + datetime.timedelta(minutes=240)
        
        if preview_start <= now <= preview_end:
            should_ping = True
            reasons.append(f"Pré-jogo: {event['shortName']} começa em {int((start_time - now).total_seconds()/60)} mins")
            
        elif result_check_start <= now <= result_check_end and status_name not in ["STATUS_FINAL", "STATUS_POSTPONED", "STATUS_CANCELED"]:
            should_ping = True
            reasons.append(f"Fim de jogo iminente: {event['shortName']} (Status ESPN: {status_name})")

    if should_ping:
        print("Motivos para manter as máquinas acordadas:")
        for r in reasons:
            print(f" - {r}")
        ping_urls()
    else:
        print("Nenhum jogo precisando de atenção agora. Máquinas podem dormir zzz...")

if __name__ == "__main__":
    main()
