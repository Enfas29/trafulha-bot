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
    """Envia sinais de trading e relatórios para o Telegram."""
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
# 3. MOTOR DE TRADING AUTOMÁTICO ($10,000 INICIAL)
# ==========================================
ESTADO_ROBO = {
    "inicializado": False,
    "caixa": 5000.0,          # $5,000 em dinheiro livre
    "btc_tamanho": 0.0,
    "btc_preco_anterior": 0.0,
    "eth_tamanho": 0.0,
    "eth_preco_anterior": 0.0
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

def executar_logica_trading(ativo, preco_atual):
    """Lógica inteligente de compra e venda automática baseada na variação de preço."""
    global ESTADO_ROBO
    sinal_mensagem = ""
    
    # Se for a primeira execução, guarda apenas o preço de referência
    if ativo == "BTC":
        if ESTADO_ROBO["btc_preco_anterior"] == 0.0:
            ESTADO_ROBO["btc_preco_anterior"] = preco_atual
            # Abre posição inicial de teste
            ESTADO_ROBO["btc_tamanho"] = 2500.0 / preco_atual
            return "🟢 *[TRAFULHA INÍCIO]* Posição inicial aberta em BTC."
        
        variacao = ((preco_atual - ESTADO_ROBO["btc_preco_anterior"]) / ESTADO_ROBO["btc_preco_anterior"]) * 100
        
        # Estratégia: Se cair mais de 0.5%, compra em baixa (se tiver caixa)
        if variacao <= -0.5 and ESTADO_ROBO["caixa"] >= 500:
            valor_investir = 500.0
            qtd = valor_investir / preco_atual
            ESTADO_ROBO["caixa"] -= valor_investir
            ESTADO_ROBO["btc_tamanho"] += qtd
            sinal_mensagem = f"🟢 *[TRAFULHA COMPRA]* BTC caiu {variacao:.2f}%. Compra automática de `{qtd:.4f} BTC` a `$ {preco_atual:,.2f}`!"
        
        # Estratégia: Se subir mais de 0.8%, vende parte para encaixar lucro
        elif variacao >= 0.8 and ESTADO_ROBO["btc_tamanho"] > 0:
            qtd_venda = ESTADO_ROBO["btc_tamanho"] * 0.2 # Vende 20 da posição
            valor_recebido = qtd_venda * preco_atual
            ESTADO_ROBO["caixa"] += valor_recebido
            ESTADO_ROBO["btc_tamanho"] -= qtd_venda
            sinal_mensagem = f"💰 *[TRAFULHA VENDA/LUCRO]* BTC subiu {variacao:.2f}%. Lucro realizado de `$ {valor_recebido:,.2f}`!"
            
        ESTADO_ROBO["btc_preco_anterior"] = preco_atual

    elif ativo == "ETH":
        if ESTADO_ROBO["eth_preco_anterior"] == 0.0:
            ESTADO_ROBO["eth_preco_anterior"] = preco_atual
            ESTADO_ROBO["eth_tamanho"] = 2500.0 / preco_atual
            return "🟢 *[TRAFULHA INÍCIO]* Posição inicial aberta em ETH."
        
        variacao = ((preco_atual - ESTADO_ROBO["eth_preco_anterior"]) / ESTADO_ROBO["eth_preco_anterior"]) * 100
        
        if variacao <= -0.5 and ESTADO_ROBO["caixa"] >= 500:
            valor_investir = 500.0
            qtd = valor_investir / preco_atual
            ESTADO_ROBO["caixa"] -= valor_investir
            ESTADO_ROBO["eth_tamanho"] += qtd
            sinal_mensagem = f"🟢 *[TRAFULHA COMPRA]* ETH caiu {variacao:.2f}%. Compra automática de `{qtd:.4f} ETH` a `$ {preco_atual:,.2f}`!"
            
        elif variacao >= 0.8 and ESTADO_ROBO["eth_tamanho"] > 0:
            qtd_venda = ESTADO_ROBO["eth_tamanho"] * 0.2
            valor_recebido = qtd_venda * preco_atual
            ESTADO_ROBO["caixa"] += valor_recebido
            ESTADO_ROBO["eth_tamanho"] -= qtd_venda
            sinal_mensagem = f"💰 *[TRAFULHA VENDA/LUCRO]* ETH subiu {variacao:.2f}%. Lucro realizado de `$ {valor_recebido:,.2f}`!"
            
        ESTADO_ROBO["eth_preco_anterior"] = preco_atual

    return sinal_mensagem

def gerar_relatorio_ciclo():
    global ESTADO_ROBO
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return "⚠️ Erro ao obter preços de mercado."

    # Executa a lógica de decisão para cada ativo
    alerta_btc = executar_logica_trading("BTC", btc_preco)
    alerta_eth = executar_logica_trading("ETH", eth_preco)

    # Cálculos financeiros globais da carteira
    btc_valor_atual = ESTADO_ROBO["btc_tamanho"] * btc_preco
    eth_valor_atual = ESTADO_ROBO["eth_tamanho"] * eth_preco
    total_ntl_pos = btc_valor_atual + eth_valor_atual
    
    # Património total = Caixa + Valor atual das posições
    patrimonio = ESTADO_ROBO["caixa"] + total_ntl_pos
    
    # Capital inicial de referência era $10,000.00
    lucro_total = patrimonio - 10000.00
    emoji_pnl = "🟢" if lucro_total >= 0 else "🔴"

    # Constrói o relatório completo
    relatorio = f"🤖 *Relatório Smart Trading — Trafulha*\n\n"
    
    if alerta_btc:
        relatorio += f"{alerta_btc}\n"
    if alerta_eth:
        relatorio += f"{alerta_eth}\n"

    relatorio += (
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


print("🤖 Robô Trafulha Smart Trading Iniciado!")
mensagem_inicial = gerar_relatorio_ciclo()
enviar_telegram(mensagem_initial)

# Loop principal: monitoriza o mercado e envia relatórios a cada 30 minutos
while True:
    time.sleep(1800) # Intervalo de 30 minutos para avaliar o mercado
    relatorio_periodico = gerar_relatorio_ciclo()
    enviar_telegram(relatorio_periodico)
