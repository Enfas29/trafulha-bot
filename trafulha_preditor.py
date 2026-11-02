import os
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from eth_account import Account

# ==========================================
# 1. SERVIDOR WEB DE SUPORTE (Para o Render e UptimeRobot)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Trafulha Preditor Online - Modo Testnet Ativo!")

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
# 2. CONFIGURAÇÕES E CREDENCIAIS (Testnet)
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HYPERLIQUID_PRIVATE_KEY = os.getenv("HYPERLIQUID_PRIVATE_KEY")

# URL Oficial da Testnet da Hyperliquid
HYPERLIQUID_API_URL = "https://api.hyperliquid-testnet.xyz/info"

ACCOUNT_ADDRESS = ""
if HYPERLIQUID_PRIVATE_KEY:
    try:
        account = Account.from_key(HYPERLIQUID_PRIVATE_KEY)
        ACCOUNT_ADDRESS = account.address
    except Exception as e:
        print(f"Erro ao derivar endereço da carteira: {e}")

def enviar_telegram(mensagem):
    """Envia relatórios financeiros para o Telegram."""
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
# 3. CONSULTAS À API DA TESTNET
# ==========================================
def obter_precos_mercado():
    """Obtém os preços em tempo real de BTC e ETH na Testnet."""
    precos = {"BTC": 0.0, "ETH": 0.0}
    try:
        headers = {"Content-Type": "application/json"}
        data = {"type": "metaAndAssetCtxs"}
        response = requests.post(HYPERLIQUID_API_URL, json=data, headers=headers, timeout=10)
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

def obter_estado_conta():
    """Obtém o património, saldo e posições na Testnet."""
    if not ACCOUNT_ADDRESS:
        return None
    try:
        headers = {"Content-Type": "application/json"}
        data = {"type": "clearinghouseState", "user": ACCOUNT_ADDRESS}
        response = requests.post(HYPERLIQUID_API_URL, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Erro ao consultar o estado da conta na Testnet: {e}")
    return None

def gerar_relatorio_financeiro():
    """Constrói o relatório financeiro detalhado com base na Testnet."""
    precos = obter_precos_mercado()
    estado = obter_estado_conta()
    
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    patrimonio = 0.0
    saldo_caixa = 0.0
    total_ntl_pos = 0.0
    lucro_total = 0.0
    posicoes_detalhe = ""
    
    if estado:
        margin_summary = estado.get("marginSummary", {})
        patrimonio = float(margin_summary.get("accountValue", 0.0))
        total_ntl_pos = float(margin_summary.get("totalNtlPos", 0.0))
        saldo_caixa = float(estado.get("withdrawable", 0.0))
        
        asset_positions = estado.get("assetPositions", [])
        for p in asset_positions:
            pos = p.get("position", {})
            coin = pos.get("coin")
            szi = float(pos.get("szi", 0.0))
            unrealized_pnl = float(pos.get("unrealizedPnl", 0.0))
            lucro_total += unrealized_pnl
            if szi != 0:
                posicoes_detalhe += f"• `{coin}`: Tamanho {szi} | PnL: `$ {unrealized_pnl:.2f}`\n"
    
    if not posicoes_detalhe:
        posicoes_detalhe = "• Sem posições abertas na Testnet.\n"

    relatorio = (
        f"🧪 *Relatório Testnet (Dinheiro Falso) — Trafulha*\n\n"
        f"🪙 *Preços de Mercado (Testnet)*\n"
        f"• **BTC**: `$ {btc_preco:,.2f}`\n"
        f"• **ETH**: `$ {eth_preco:,.2f}`\n\n"
        f"💰 *Métricas da Carteira (Testnet)*\n"
        f"• **Património Atual (Equity)**: `$ {patrimonio:,.2f}`\n"
        f"• **Saldo em Caixa (Withdrawable)**: `$ {saldo_caixa:,.2f}`\n"
        f"• **Total na Conta / Alocado**: `$ {total_ntl_pos:,.2f}`\n"
        f"• **Lucro / Prejuízo Acumulado (PnL)**: `$ {lucro_total:,.2f}`\n\n"
        f"📈 *Posições Ativas*:\n"
        f"{posicoes_detalhe}"
    )
    return relatorio


print("🤖 Robô Trafulha iniciado na Testnet!")
mensagem_inicial = gerar_relatorio_financeiro()
enviar_telegram(mensagem_inicial)

# Loop periódico a cada 1 hora
while True:
    time.sleep(1800)  
    relatorio_periodico = gerar_relatorio_financeiro()
    enviar_telegram(relatorio_periodico)
