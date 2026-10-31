import os
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================
# 1. SERVIDOR WEB DE SUPORTE (Para o Render e UptimeRobot)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Trafulha Preditor Online, Blindado & Com Leitura de Orderbook!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def iniciar_servidor_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Inicia o servidor web numa thread separada para manter o Render acordado
t_web = threading.Thread(target=iniciar_servidor_web, daemon=True)
t_web.start()


# ==========================================
# 2. CONFIGURAÇÕES E CREDENCIAIS (Seguras via Render)
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HYPERLIQUID_PRIVATE_KEY = os.getenv("HYPERLIQUID_PRIVATE_KEY")

def enviar_telegram(mensagem):
    """Envia relatórios automáticos para o canal do Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")


# ==========================================
# 3. ESTRATÉGIA DO TRIO VENCEDOR & ORDERBOOK
# ==========================================
ATIVOS_ALVO = {
    "BTC": {"peso": 0.40, "alavancagem": 3},
    "BNB": {"peso": 0.40, "alavancagem": 5},
    "SOL": {"peso": 0.20, "alavancagem": 3}
}

def consultar_densidade_orderbook(coin):
    """Exemplo de consulta ao l2Book da Hyperliquid para análise de densidade."""
    try:
        url = "https://api.hyperliquid.xyz/info"
        headers = {"Content-Type": "application/json"}
        data = {"type": "l2Book", "coin": coin}
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            book = response.json()
            # Processamento básico de bids/asks (densidade)
            levels = book.get("levels", [[], []])
            bids = levels[0] if len(levels) > 0 else []
            asks = levels[1] if len(levels) > 1 else []
            
            volume_bids = sum([float(b.get("sz", 0)) for b in bids[:5]])
            volume_asks = sum([float(a.get("sz", 0)) for a in asks[:5]])
            
            return {"bids": volume_bids, "asks": volume_asks}
    except Exception as e:
        print(f"Erro ao consultar orderbook de {coin}: {e}")
    return None

print("🤖 Robô Trafulha iniciado com sucesso focado no Trio Vencedor e Orderbook!")
enviar_telegram("🚀 *Trafulha Online!*\nRobô arrancado com sucesso, focado estritamente no trio vencedor (`BTC`, `BNB`, `SOL`).")

# Loop principal do robô de trading
while True:
    for ativo in ATIVOS_ALVO.keys():
        densidade = consultar_densidade_orderbook(ativo)
        if densidade:
            print(f"[{ativo}] Bids Top 5: {densidade['bids']:.2f} | Asks Top 5: {densidade['asks']:.2f}")
        
    time.sleep(60)
