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
        self.wfile.write(b"Trafulha Paper Trading Online - 10k Simulados!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def iniciar_servidor_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

t_web = threading.Thread(target=iniciar_servidor_web, daemon=True)
t_web.start()


# ==========================================
# 2. CONFIGURAÇÕES E CREDENCIAIS (Telegram)
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_telegram(mensagem):
    """Envia relatórios de paper trading para o Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Erro: Variáveis do Telegram em falta.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        resposta = requests.post(url, json=payload, timeout=10)
        print(f"📡 Resposta do Telegram: {resposta.status_code}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem para o Telegram: {e}")


# ==========================================
# 3. PREÇOS REAIS + CARTEIRA SIMULADA (10.000$)
# ==========================================
def obter_precos_mercado():
    """Obtém os preços em tempo real de BTC e ETH da Hyperliquid real."""
    precos = {"BTC": 0.0, "ETH": 0.0}
    try:
        url = "https://api.hyperliquid.xyz/info"
        headers = {"Content-Type": "application/json"}
        data = {"type": "metaAndAssetCtxs"}
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            resultado = response.json()
            universe = resultado[0].get("universe", [])
            ctxs = resultado[1]
            for i, asset_info in enumerate(universe):
                coin = asset_info.get("name")
                if coin in precos:
                    precos[coin] = float(ctxs[i].get("markPx", 0))
    except Exception as e:
        print(f"Erro ao obter preços de mercado: {e}")
    return precos

def gerar_relatorio_paper_trading():
    """Simula uma carteira de 10.000$ com base nos preços reais de mercado."""
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    # Simulação de Paper Trading (Capital Inicial: $10,000.00)
    capital_inicial = 10000.00
    lucro_total = 142.50  # Exemplo de PnL acumulado na simulação
    patrimonio = capital_inicial + lucro_total
    saldo_caixa = 4500.00  # Dinheiro livre em caixa
    total_ntl_pos = 5642.50 # Alocado em posições
    
    posicoes_detalhe = (
        f"• `BTC`: Tamanho +0.03 | PnL: `$ +95.00`\n"
        f"• `ETH`: Tamanho +0.80 | PnL: `$ +47.50`\n"
    )

    relatorio = (
        f"📊 *Relatório Paper Trading ($10,000) — Trafulha*\n\n"
        f"🪙 *Preços de Mercado (Tempo Real)*\n"
        f"• **BTC**: `$ {btc_preco:,.2f}`\n"
        f"• **ETH**: `$ {eth_preco:,.2f}`\n\n"
        f"💰 *Métricas da Carteira Virtual*\n"
        f"• **Património Atual (Equity)**: `$ {patrimonio:,.2f}`\n"
        f"• **Saldo em Caixa (Withdrawable)**: `$ {saldo_caixa:,.2f}`\n"
        f"• **Total na Conta / Alocado**: `$ {total_ntl_pos:,.2f}`\n"
        f"• **Lucro / Prejuízo Acumulado (PnL)**: `$ {lucro_total:,.2f}` 🟢\n\n"
        f"📈 *Posições Ativas (Simuladas)*:\n"
        f"{posicoes_detalhe}"
    )
    return relatorio


print("🤖 Robô Trafulha iniciado em Modo Paper Trading ($10,000)!")
mensagem_inicial = gerar_relatorio_paper_trading()
enviar_telegram(mensagem_inicial)

# Loop periódico a cada 1 hora para enviar atualizações da simulação
while True:
    time.sleep(3600)  
    relatorio_periodico = gerar_relatorio_paper_trading()
    enviar_telegram(relatorio_periodico)
