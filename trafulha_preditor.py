import os
import time
import json
import requests
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

ARQUIVO_ESTADO = "estado_trafulha.json"

# ==========================================
# 1. GESTÃO DE ESTADO E PERSISTÊNCIA LIMPA
# ==========================================
def carregar_estado():
    # Se quiseres forçar a limpeza total ao arrancar, 
    # podes apagar o ficheiro anterior no Render ou usar esta base limpa:
    if os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, "r") as f:
                print("📂 Estado anterior recuperado com sucesso!")
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler ficheiro de estado: {e}")
    
    return {
        "inicializado": False,
        "caixa": 0.0,
        "btc_tamanho": 0.0,
        "btc_preco_referencia": 0.0,
        "eth_tamanho": 0.0,
        "eth_preco_referencia": 0.0,
        "patrimonio_inicio_dia": 10000.00,
        "data_atual": ""
    }

def salvar_estado(estado):
    try:
        with open(ARQUIVO_ESTADO, "w") as f:
            json.dump(estado, f)
    except Exception as e:
        print(f"Erro ao salvar estado: {e}")

ESTADO_ROBO = carregar_estado()

# Histórico do gráfico começa totalmente limpo para a nova fase
HISTORICO_GRAFICO = {
    "timestamps": [],
    "patrimonio": []
}

# ==========================================
# 2. SERVIDOR WEB COM AUTO-REFRESH
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/dados":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            dados = {
                "timestamps": HISTORICO_GRAFICO["timestamps"],
                "patrimonio": HISTORICO_GRAFICO["patrimonio"]
            }
            self.wfile.write(json.dumps(dados).encode("utf-8"))
            
        elif self.path == "/" or self.path == "/grafico":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html lang="pt">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Trafulha Smart Trading - Live Chart</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; text-align: center; margin: 0; padding: 20px; }
                    h1 { color: #38bdf8; }
                    .card { background: #1e293b; padding: 20px; border-radius: 12px; max-width: 800px; margin: 20px auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
                    canvas { max-height: 400px; }
                    .status { font-size: 14px; color: #10b981; margin-top: 10px; }
                </style>
            </head>
            <body>
                <h1>🤖 Trafulha Smart Trading - Live Chart</h1>
                <div class="card">
                    <h3>Evolução do Património Total (100% Cripto)</h3>
                    <canvas id="graficoPatrimonio"></canvas>
                    <div class="status">🟢 Atualização automática em tempo real ativa</div>
                </div>
                <script>
                    const ctx = document.getElementById('graficoPatrimonio').getContext('2d');
                    const grafico = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'Património ($ USD)',
                                data: [],
                                borderColor: '#38bdf8',
                                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                                borderWidth: 2,
                                fill: true,
                                tension: 0.2
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { labels: { color: '#f8fafc' } } },
                            scales: {
                                x: { ticks: { color: '#94a3b8' } },
                                y: { 
                                    ticks: { color: '#94a3b8' },
                                    suggestedMin: 9800,
                                    suggestedMax: 10200
                                }
                            }
                        }
                    });

                    async function atualizarGrafico() {
                        try {
                            const resposta = await fetch('/dados');
                            const dados = await resposta.json();
                            grafico.data.labels = dados.timestamps;
                            grafico.data.datasets[0].data = dados.patrimonio;
                            grafico.update('none');
                        } catch (erro) {
                            console.error('Erro ao atualizar o gráfico:', erro);
                        }
                    }

                    atualizarGrafico();
                    setInterval(atualizarGrafico, 10000);
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
# 3. CREDENCIAIS TELEGRAM
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
# 4. MOTOR DE TRADING
# ==========================================
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

    hoje = datetime.now().strftime("%Y-%m-%d")

    # Força recomeço limpo se o estado anterior não estiver inicializado a 100% cripto
    if not ESTADO_ROBO["inicializado"] or ESTADO_ROBO["caixa"] > 0:
        ESTADO_ROBO["btc_tamanho"] = 5000.0 / btc_preco
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        ESTADO_ROBO["eth_tamanho"] = 5000.0 / eth_preco
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        ESTADO_ROBO["caixa"] = 0.0
        ESTADO_ROBO["patrimonio_inicio_dia"] = 10000.00
        ESTADO_ROBO["data_atual"] = hoje
        ESTADO_ROBO["inicializado"] = True
        salvar_estado(ESTADO_ROBO)
        enviar_telegram("🟢 *[TRAFULHA]* Novo ciclo iniciado com 100% do capital alocado em cripto e gráfico limpo!")

    btc_val = ESTADO_ROBO["btc_tamanho"] * btc_preco
    eth_val = ESTADO_ROBO["eth_tamanho"] * eth_preco
    patrimonio_atual = ESTADO_ROBO["caixa"] + btc_val + eth_val

    # Regista o ponto atual para o gráfico em direto
    hora_atual = datetime.now().strftime("%H:%M:%S")
    if not HISTORICO_GRAFICO["timestamps"] or HISTORICO_GRAFICO["timestamps"][-1] != hora_atual:
        HISTORICO_GRAFICO["timestamps"].append(hora_atual)
        HISTORICO_GRAFICO["patrimonio"].append(round(patrimonio_atual, 2))
        if len(HISTORICO_GRAFICO["timestamps"]) > 50:
            HISTORICO_GRAFICO["timestamps"].pop(0)
            HISTORICO_GRAFICO["patrimonio"].pop(0)

    # Mudança de dia
    if hoje != ESTADO_ROBO["data_atual"]:
        lucro_ontem = patrimonio_atual - ESTADO_ROBO["patrimonio_inicio_dia"]
        emoji_ontem = "🟢" if lucro_ontem >= 0 else "🔴"
        enviar_telegram(f"📅 *Resumo Diário*\n• **Resultado**: `$ {lucro_ontem:,.2f}` {emoji_ontem}")
        ESTADO_ROBO["data_atual"] = hoje
        ESTADO_ROBO["patrimonio_inicio_dia"] = patrimonio_atual
        salvar_estado(ESTADO_ROBO)

    # Lógica de Trading BTC
    variacao_btc = ((btc_preco - ESTADO_ROBO["btc_preco_referencia"]) / ESTADO_ROBO["btc_preco_referencia"]) * 100
    if variacao_btc <= -0.6 and ESTADO_ROBO["caixa"] >= 500:
        qtd = 500.0 / btc_preco
        ESTADO_ROBO["caixa"] -= 500.0
        ESTADO_ROBO["btc_tamanho"] += qtd
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        salvar_estado(ESTADO_ROBO)
        enviar_telegram(f"🟢 *[COMPRA BTC]* Queda de {variacao_btc:.2f}% (`{qtd:.4f} BTC`)")
    elif variacao_btc >= 1.0 and ESTADO_ROBO["btc_tamanho"] > 0:
        qtd_venda = ESTADO_ROBO["btc_tamanho"] * 0.25
        valor_recebido = qtd_venda * btc_preco
        ESTADO_ROBO["caixa"] += valor_recebido
        ESTADO_ROBO["btc_tamanho"] -= qtd_venda
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        salvar_estado(ESTADO_ROBO)
        enviar_telegram(f"💰 *[VENDA BTC]* Subida de {variacao_btc:.2f}% (`$ {valor_recebido:,.2f}`)")

    # Lógica de Trading ETH
    variacao_eth = ((eth_preco - ESTADO_ROBO["eth_preco_referencia"]) / ESTADO_ROBO["eth_preco_referencia"]) * 100
    if variacao_eth <= -0.6 and ESTADO_ROBO["caixa"] >= 500:
        qtd = 500.0 / eth_preco
        ESTADO_ROBO["caixa"] -= 500.0
        ESTADO_ROBO["eth_tamanho"] += qtd
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        salvar_estado(ESTADO_ROBO)
        enviar_telegram(f"🟢 *[COMPRA ETH]* Queda de {variacao_eth:.2f}% (`{qtd:.4f} ETH`)")
    elif variacao_eth >= 1.0 and ESTADO_ROBO["eth_tamanho"] > 0:
        qtd_venda = ESTADO_ROBO["eth_tamanho"] * 0.25
        valor_recebido = qtd_venda * eth_preco
        ESTADO_ROBO["caixa"] += valor_recebido
        ESTADO_ROBO["eth_tamanho"] -= qtd_venda
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        salvar_estado(ESTADO_ROBO)
        enviar_telegram(f"💰 *[VENDA ETH]* Subida de {variacao_eth:.2f}% (`$ {valor_recebido:,.2f}`)")

def gerar_relatorio_carteira():
    global ESTADO_ROBO
    precos = obter_precos_mercado()
    btc_preco = precos.get("BTC", 0.0)
    eth_preco = precos.get("ETH", 0.0)
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return "⚠️ Erro ao obter preços."

    patrimonio = ESTADO_ROBO["caixa"] + (ESTADO_ROBO["btc_tamanho"] * btc_preco) + (ESTADO_ROBO["eth_tamanho"] * eth_preco)
    lucro_hoje = patrimonio - ESTADO_ROBO["patrimonio_inicio_dia"]
    lucro_total = patrimonio - 10000.00
    
    return (
        f"📊 *Relatório Trafulha (100% Cripto)*\n\n"
        f"• **Património Total**: `$ {patrimonio:,.2f}`\n"
        f"• **Saldo em Caixa**: `$ {ESTADO_ROBO['caixa']:,.2f}`\n"
        f"• **Resultado de Hoje**: `$ {lucro_hoje:,.2f}`\n"
        f"• **Lucro Total**: `$ {lucro_total:,.2f}`"
    )

def loop_trading():
    while True:
        try:
            avaliar_e_negociar()
        except Exception as e:
            print(f"Erro trading: {e}")
        time.sleep(60)

def loop_relatorios():
    time.sleep(10)
    while True:
        try:
            enviar_telegram(gerar_relatorio_carteira())
        except Exception as e:
            print(f"Erro relatórios: {e}")
        time.sleep(1800)

print("🤖 Trafulha 100% Cripto Ativo!")
threading.Thread(target=loop_trading, daemon=True).start()
threading.Thread(target=loop_relatorios, daemon=True).start()

while True:
    time.sleep(3600)
