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
        self.wfile.write(b"Trafulha Smart Trading Bot Online!")

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
    """Envia relatórios ou sinais importantes para o Telegram."""
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
# 3. MOTOR DE TRADING AUTÓNOMO E INTELIGENTE
# ==========================================
ESTADO_ROBO = {
    "inicializado": False,
    "caixa": 5000.0,
    "btc_tamanho": 0.0,
    "btc_preco_referencia": 0.0,
    "eth_tamanho": 0.0,
    "eth_preco_referencia": 0.0
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

def avaliar_e_negociar():
    """Corre frequentemente em segundo plano para decidir se deve comprar ou vender."""
    global ESTADO_ROBO
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return

    # Inicialização automática se for a primeira vez
    if not ESTADO_ROBO["inicializado"]:
        ESTADO_ROBO["btc_tamanho"] = 2500.0 / btc_preco
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        ESTADO_ROBO["eth_tamanho"] = 2500.0 / eth_preco
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        ESTADO_ROBO["inicializado"] = True
        enviar_telegram("🟢 *[TRAFULHA]* Robô inicializado. Posições abertas e a monitorizar o mercado ativamente.")
        return

    # --- LÓGICA BTC ---
    variacao_btc = ((btc_preco - ESTADO_ROBO["btc_preco_referencia"]) / ESTADO_ROBO["btc_preco_referencia"]) * 100
    if variacao_btc <= -0.6 and ESTADO_ROBO["caixa"] >= 500: # Compra se cair 0.6%
        valor_investir = 500.0
        qtd = valor_investir / btc_preco
        ESTADO_ROBO["caixa"] -= valor_investir
        ESTADO_ROBO["btc_tamanho"] += qtd
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        enviar_telegram(f"🟢 *[TRAFULHA COMPRA]* BTC caiu {variacao_btc:.2f}%. Compra automática de `{qtd:.4f} BTC` a `$ {btc_preco:,.2f}`!")
    elif variacao_btc >= 1.0 and ESTADO_ROBO["btc_tamanho"] > 0: # Vende se subir 1.0%
        qtd_venda = ESTADO_ROBO["btc_tamanho"] * 0.25
        valor_recebido = qtd_venda * btc_preco
        ESTADO_ROBO["caixa"] += valor_recebido
        ESTADO_ROBO["btc_tamanho"] -= qtd_venda
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        enviar_telegram(f"💰 *[TRAFULHA VENDA/LUCRO]* BTC subiu {variacao_btc:.2f}%. Lucro encaixado: `$ {valor_recebido:,.2f}`!")

    # --- LÓGICA ETH ---
    variacao_eth = ((eth_preco - ESTADO_ROBO["eth_preco_referencia"]) / ESTADO_ROBO["eth_preco_referencia"]) * 100
    if variacao_eth <= -0.6 and ESTADO_ROBO["caixa"] >= 500:
        valor_investir = 500.0
        qtd = valor_investir / eth_preco
        ESTADO_ROBO["caixa"] -= valor_investir
        ESTADO_ROBO["eth_tamanho"] += qtd
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        enviar_telegram(f"🟢 *[TRAFULHA COMPRA]* ETH caiu {variacao_eth:.2f}%. Compra automática de `{qtd:.4f} ETH` a `$ {eth_preco:,.2f}`!")
    elif variacao_eth >= 1.0 and ESTADO_ROBO["eth_tamanho"] > 0:
        qtd_venda = ESTADO_ROBO["eth_tamanho"] * 0.25
        valor_recebido = qtd_venda * eth_preco
        ESTADO_ROBO["caixa"] += valor_recebido
        ESTADO_ROBO["eth_tamanho"] -= qtd_venda
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        enviar_telegram(f"💰 *[TRAFULHA VENDA/LUCRO]* ETH subiu {variacao_eth:.2f}%. Lucro encaixado: `$ {valor_recebido:,.2f}`!")

def gerar_relatorio_carteira():
    """Gera o balanço financeiro atual para enviar no relatório periódico."""
    global ESTADO_ROBO
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return "⚠️ Erro ao obter preços de mercado para o relatório."

    btc_valor_atual = ESTADO_ROBO["btc_tamanho"] * btc_preco
    eth_valor_atual = ESTADO_ROBO["eth_tamanho"] * eth_preco
    total_ntl_pos = btc_valor_atual + eth_valor_atual
    
    patrimonio = ESTADO_ROBO["caixa"] + total_ntl_pos
    lucro_total = patrimonio - 10000.00
    emoji_pnl = "🟢" if lucro_total >= 0 else "🔴"

    relatorio = (
        f"📊 *Relatório Periódico — Trafulha*\n\n"
        f"🪙 *Preços Atuais*\n"
        f"• **BTC**: `$ {btc_preco:,.2f}`\n"
        f"• **ETH**: `$ {eth_preco:,.2f}`\n\n"
        f"💰 *Métricas da Carteira*\n"
        f"• **Património Total (Equity)**: `$ {patrimonio:,.2f}`\n"
        f"• **Saldo em Caixa (Livre)**: `$ {ESTADO_ROBO['caixa']:,.2f}`\n"
        f"• **Alocado em Posições**: `$ {total_ntl_pos:,.2f}`\n"
        f"• **Lucro / Prejuízo (PnL)**: `$ {lucro_total:,.2f}` {emoji_pnl}\n\n"
        f"📈 *Posições Ativas*:\n"
        f"• `BTC`: {ESTADO_ROBO['btc_tamanho']:.4f}\n"
        f"• `ETH`: {ESTADO_ROBO['eth_tamanho']:.4f}"
    )
    return relatorio


# ==========================================
# 4. THREADS DE EXECUÇÃO EM BACKGROUND
# ==========================================
def loop_trading():
    """Loop que avalia o mercado a cada 2 minutos à procura do momento ideal."""
    while True:
        try:
            avaliar_e_negociar()
        except Exception as e:
            print(f"Erro no loop de trading: {e}")
        time.sleep(120) # Verifica o mercado de 2 em 2 minutos

def loop_relatorios():
    """Loop que envia o relatório financeiro para o Telegram a cada 30 minutos."""
    # Aguarda 10 segundos antes do primeiro relatório para garantir arranque
    time.sleep(10)
    while True:
        try:
            relatorio = gerar_relatorio_carteira()
            enviar_telegram(relatorio)
        except Exception as e:
            print(f"Erro ao enviar relatório periódico: {e}")
        time.sleep(1800) # Envia relatório de 30 em 30 minutos

# Arranca as tarefas em segundo plano
print("🤖 Robô Trafulha Smart Trading Autónomo Iniciado!")
t_trade = threading.Thread(target=loop_trading, daemon=True)
t_trade.start()

t_rel = threading.Thread(target=loop_relatorios, daemon=True)
t_rel.start()

# Mantém o script principal ativo para o servidor web e as threads correrem
while True:
    time.sleep(3600)
