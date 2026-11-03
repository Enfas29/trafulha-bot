import os
import time
import requests
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================
# 1. HISTÓRICO E SERVIDOR WEB COM GRÁFICO
# ==========================================
HISTORICO_GRAFICO = {
    "timestamps": [],
    "patrimonio": []
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/grafico":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html lang="pt">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Trafulha Smart Trading - Dashboard</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; text-align: center; margin: 0; padding: 20px; }}
                    h1 {{ color: #38bdf8; }}
                    .card {{ background: #1e293b; padding: 20px; border-radius: 12px; max-width: 800px; margin: 20px auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                    canvas {{ max-height: 400px; }}
                </style>
            </head>
            <body>
                <h1>🤖 Trafulha Smart Trading - Live Chart</h1>
                <div class="card">
                    <h3>Evolução do Património Total (Equity)</h3>
                    <canvas id="graficoPatrimonio"></canvas>
                </div>
                <script>
                    const ctx = document.getElementById('graficoPatrimonio').getContext('2d');
                    const grafico = new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: {HISTORICO_GRAFICO["timestamps"]},
                            datasets: [{{
                                label: 'Património ($ USD)',
                                data: {HISTORICO_GRAFICO["patrimonio"]},
                                borderColor: '#38bdf8',
                                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                                borderWidth: 2,
                                fill: true,
                                tension: 0.2
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }} }},
                            scales: {{
                                x: {{ ticks: {{ color: '#94a3b8' }} }},
                                y: {{ ticks: {{ color: '#94a3b8' }} }}
                            }}
                        }}
                    }});
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Trafulha Bot Online!")

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
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")


# ==========================================
# 3. MOTOR DE TRADING E CONTROLO DIÁRIO
# ==========================================
ESTADO_ROBO = {
    "inicializado": False,
    "caixa": 5000.0,
    "btc_tamanho": 0.0,
    "btc_preco_referencia": 0.0,
    "eth_tamanho": 0.0,
    "eth_preco_referencia": 0.0,
    "patrimonio_inicio_dia": 0.0,
    "data_atual": ""
}

def obter_precos_mercado():
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
        print(f"Erro preços: {e}")
    return precos

def avaliar_e_negociar():
    global ESTADO_ROBO, HISTORICO_GRAFICO
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return

    btc_val = ESTADO_ROBO["btc_tamanho"] * btc_preco
    eth_val = ESTADO_ROBO["eth_tamanho"] * eth_preco
    patrimonio_atual = ESTADO_ROBO["caixa"] + btc_val + eth_val
    
    hoje = datetime.now().strftime("%Y-%m-%d")

    if not ESTADO_ROBO["inicializado"]:
        ESTADO_ROBO["btc_tamanho"] = 2500.0 / btc_preco
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        ESTADO_ROBO["eth_tamanho"] = 2500.0 / eth_preco
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        ESTADO_ROBO["patrimonio_inicio_dia"] = 10000.00
        ESTADO_ROBO["data_atual"] = hoje
        ESTADO_ROBO["inicializado"] = True
        enviar_telegram("🟢 *[TRAFULHA]* Robô inicializado com sucesso e a monitorizar!")
        return

    # Verificar se mudou o dia para enviar o resumo do dia anterior
    if hoje != ESTADO_ROBO["data_atual"]:
        lucro_ontem = patrimonio_atual - ESTADO_ROBO["patrimonio_inicio_dia"]
        emoji_ontem = "🟢" if lucro_ontem >= 0 else "🔴"
        
        relatorio_diario = (
            f"📅 *Resumo Diário do Trafulha*\n"
            f"• **Dia anterior**: `{ESTADO_ROBO['data_atual']}`\n"
            f"• **Resultado do Dia**: `$ {lucro_ontem:,.2f}` {emoji_ontem}\n"
            f"• **Novo Património de Abertura**: `$ {patrimonio_atual:,.2f}`"
        )
        enviar_telegram(relatorio_diario)
        
        # Atualiza para o novo dia
        ESTADO_ROBO["data_atual"] = hoje
        ESTADO_ROBO["patrimonio_inicio_dia"] = patrimonio_atual

    # Lógica BTC
    variacao_btc = ((btc_preco - ESTADO_ROBO["btc_preco_referencia"]) / ESTADO_ROBO["btc_preco_referencia"]) * 100
    if variacao_btc <= -0.6 and ESTADO_ROBO["caixa"] >= 500:
        qtd = 500.0 / btc_preco
        ESTADO_ROBO["caixa"] -= 500.0
        ESTADO_ROBO["btc_tamanho"] += qtd
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        enviar_telegram(f"🟢 *[TRAFULHA COMPRA]* BTC caiu {variacao_btc:.2f}%. Compra de `{qtd:.4f} BTC` a `$ {btc_preco:,.2f}`!")
    elif variacao_btc >= 1.0 and ESTADO_ROBO["btc_tamanho"] > 0:
        qtd_venda = ESTADO_ROBO["btc_tamanho"] * 0.25
        valor_recebido = qtd_venda * btc_preco
        ESTADO_ROBO["caixa"] += valor_recebido
        ESTADO_ROBO["btc_tamanho"] -= qtd_venda
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        enviar_telegram(f"💰 *[TRAFULHA VENDA]* BTC subiu {variacao_btc:.2f}%. Lucro encaixado: `$ {valor_recebido:,.2f}`!")

    # Lógica ETH
    variacao_eth = ((eth_preco - ESTADO_ROBO["eth_preco_referencia"]) / ESTADO_ROBO["eth_preco_referencia"]) * 100
    if variacao_eth <= -0.6 and ESTADO_ROBO["caixa"] >= 500:
        qtd = 500.0 / eth_preco
        ESTADO_ROBO["caixa"] -= 500.0
        ESTADO_ROBO["eth_tamanho"] += qtd
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        enviar_telegram(f"🟢 *[TRAFULHA COMPRA]* ETH caiu {variacao_eth:.2f}%. Compra de `{qtd:.4f} ETH` a `$ {eth_preco:,.2f}`!")
    elif variacao_eth >= 1.0 and ESTADO_ROBO["eth_tamanho"] > 0:
        qtd_venda = ESTADO_ROBO["eth_tamanho"] * 0.25
        valor_recebido = qtd_venda * eth_preco
        ESTADO_ROBO["caixa"] += valor_recebido
        ESTADO_ROBO["eth_tamanho"] -= qtd_venda
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        enviar_telegram(f"💰 *[TRAFULHA VENDA]* ETH subiu {variacao_eth:.2f}%. Lucro encaixado: `$ {valor_recebido:,.2f}`!")

    # Atualiza histórico do gráfico
    hora_atual = datetime.now().strftime("%H:%M")
    if not HISTORICO_GRAFICO["timestamps"] or HISTORICO_GRAFICO["timestamps"][-1] != hora_atual:
        HISTORICO_GRAFICO["timestamps"].append(hora_atual)
        HISTORICO_GRAFICO["patrimonio"].append(round(patrimonio_atual, 2))
        if len(HISTORICO_GRAFICO["timestamps"]) > 50:
            HISTORICO_GRAFICO["timestamps"].pop(0)
            HISTORICO_GRAFICO["patrimonio"].pop(0)

def gerar_relatorio_carteira():
    global ESTADO_ROBO
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return "⚠️ Erro ao obter preços para o relatório."

    btc_val = ESTADO_ROBO["btc_tamanho"] * btc_preco
    eth_val = ESTADO_ROBO["eth_tamanho"] * eth_preco
    total_pos = btc_val + eth_val
    patrimonio = ESTADO_ROBO["caixa"] + total_pos
    
    # Lucro do dia atual
    lucro_hoje = patrimonio - ESTADO_ROBO["patrimonio_inicio_dia"]
    emoji_hoje = "🟢" if lucro_hoje >= 0 else "🔴"
    
    # Lucro total desde o início
    lucro_total = patrimonio - 10000.00
    emoji_total = "🟢" if lucro_total >= 0 else "🔴"

    return (
        f"📊 *Relatório Periódico — Trafulha*\n\n"
        f"🪙 *Preços Atuais*\n"
        f"• **BTC**: `$ {btc_preco:,.2f}`\n"
        f"• **ETH**: `$ {eth_preco:,.2f}`\n\n"
        f"💰 *Métricas da Carteira*\n"
        f"• **Património Total**: `$ {patrimonio:,.2f}`\n"
        f"• **Saldo em Caixa**: `$ {ESTADO_ROBO['caixa']:,.2f}`\n"
        f"• **Resultado de Hoje**: `$ {lucro_hoje:,.2f}` {emoji_hoje}\n"
        f"• **Lucro Total Acumulado**: `$ {lucro_total:,.2f}` {emoji_total}"
    )


# ==========================================
# 4. BACKGROUND LOOPS
# ==========================================
def loop_trading():
    while True:
        try:
            avaliar_e_negociar()
        except Exception as e:
            print(f"Erro trading: {e}")
        time.sleep(120)

def loop_relatorios():
    time.sleep(10)
    while True:
        try:
            rel = gerar_relatorio_carteira()
            enviar_telegram(rel)
        except Exception as e:
            print(f"Erro relatórios: {e}")
        time.sleep(1800)

print("🤖 Robô Trafulha com Resumo Diário e Gráfico Iniciado!")
threading.Thread(target=loop_trading, daemon=True).start()
threading.Thread(target=loop_relatorios, daemon=True).start()

while True:
    time.sleep(3600)
