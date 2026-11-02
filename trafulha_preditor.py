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
        self.wfile.write(b"Trafulha Paper Trading Dinamico Online!")

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
# 3. MOTOR DE PAPER TRADING DINÂMICO ($10,000)
# ==========================================
# Variáveis de estado global para a simulação
ESTADO_SIMULACAO = {
    "inicializada": False,
    "caixa": 5000.0,          # $5,000 em dinheiro livre
    "btc_tamanho": 0.0,
    "btc_preco_entrada": 0.0,
    "eth_tamanho": 0.0,
    "eth_preco_entrada": 0.0
}

def obter_precos_mercado():
    """Obtém os preços em tempo real de BTC e ETH da Hyperliquid."""
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
    global ESTADO_SIMULACAO
    
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return "⚠️ Erro ao obter preços de mercado da Hyperliquid para a simulação."

    # Inicializa as posições virtuais na primeira execução com os preços reais do momento
    if not ESTADO_SIMULACAO["inicializada"]:
        # Aloca $2,500 em BTC e $2,500 em ETH aos preços atuais
        ESTADO_SIMULACAO["btc_tamanho"] = 2500.0 / btc_preco
        ESTADO_SIMULACAO["btc_preco_entrada"] = btc_preco
        
        ESTADO_SIMULACAO["eth_tamanho"] = 2500.0 / eth_preco
        ESTADO_SIMULACAO["eth_preco_entrada"] = eth_preco
        
        ESTADO_SIMULACAO["inicializada"] = True

    # Cálculos dinâmicos em tempo real com base nos preços atuais do mercado
    btc_valor_atual = ESTADO_SIMULACAO["btc_tamanho"] * btc_preco
    btc_pnl = ESTADO_SIMULACAO["btc_tamanho"] * (btc_preco - ESTADO_SIMULACAO["btc_preco_entrada"])

    eth_valor_atual = ESTADO_SIMULACAO["eth_tamanho"] * eth_preco
    eth_pnl = ESTADO_SIMULACAO["eth_tamanho"] * (eth_preco - ESTADO_SIMULACAO["eth_preco_entrada"])

    lucro_total = btc_pnl + eth_pnl
    total_ntl_pos = btc_valor_atual + eth_valor_atual
    patrimonio = ESTADO_SIMULACAO["caixa"] + total_ntl_pos
    
    # Indicador visual de lucro ou prejuízo
    emoji_pnl = "🟢" if lucro_total >= 0 else "🔴"

    posicoes_detalhe = (
        f"• `BTC`: Tam: {ESTADO_SIMULACAO['btc_tamanho']:.4f} | Entr: `$ {ESTADO_SIMULACAO['btc_preco_entrada']:,.2f}` | PnL: `$ {btc_pnl:,.2f}`\n"
        f"• `ETH`: Tam: {ESTADO_SIMULACAO['eth_tamanho']:.4f} | Entr: `$ {ESTADO_SIMULACAO['eth_preco_entrada']:,.2f}` | PnL: `$ {eth_pnl:,.2f}`\n"
    )

    relatorio = (
        f"📊 *Paper Trading Dinâmico ($10k Inicial) — Trafulha*\n\n"
        f"🪙 *Preços de Mercado (Tempo Real)*\n"
        f"• **BTC**: `$ {btc_preco:,.2f}`\n"
        f"• **ETH**: `$ {eth_preco:,.2f}`\n\n"
        f"💰 *Métricas da Carteira Virtual*\n"
        f"• **Património Atual (Equity)**: `$ {patrimonio:,.2f}`\n"
        f"• **Saldo em Caixa (Withdrawable)**: `$ {ESTADO_SIMULACAO['caixa']:,.2f}`\n"
        f"• **Total Alocado em Posições**: `$ {total_ntl_pos:,.2f}`\n"
        f"• **Lucro / Prejuízo Acumulado (PnL)**: `$ {lucro_total:,.2f}` {emoji_pnl}\n\n"
        f"📈 *Posições Ativas (Simuladas)*:\n"
        f"{posicoes_detalhe}"
    )
    return relatorio


print("🤖 Robô Trafulha iniciado em Modo Paper Trading Dinâmico ($10,000)!")
mensagem_inicial = gerar_relatorio_paper_trading()
enviar_telegram(mensagem_inicial)

# Loop periódico: atualiza o PnL e envia relatórios a cada 1 hora
while True:
    time.sleep(1800)  
    relatorio_periodico = gerar_relatorio_paper_trading()
    enviar_telegram(relatorio_periodico)
