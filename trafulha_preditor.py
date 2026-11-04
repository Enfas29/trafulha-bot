import os
import time
import json
import requests
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo import MongoClient

# ==========================================
# 1. LIGAÇÃO AO MONGODB ATLAS (NUVEM)
# ==========================================
MONGO_URI = os.getenv("MONGO_URI")
db = None
collection_estado = None
collection_historico = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["trafulha_db"]
        collection_estado = db["estado"]
        collection_historico = db["historico_grafico"]
        print("☁️ Ligado ao MongoDB Atlas com sucesso!")
    except Exception as e:
        print(f"❌ Erro crítico ao ligar ao MongoDB: {e}")
else:
    print("⚠️ Aviso: A variável de ambiente MONGO_URI não foi detetada!")

def carregar_estado():
    if collection_estado is not None:
        try:
            dados_db = collection_estado.find_one({"_id": "trafulha_principal"})
            if dados_db:
                print("📂 Estado recuperado da nuvem com sucesso!")
                dados_db.pop("_id", None)
                return dados_db
        except Exception as e:
            print(f"Erro ao ler do MongoDB: {e}")
            
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
    if collection_estado is not None:
        try:
            doc = estado.copy()
            doc["_id"] = "trafulha_principal"
            collection_estado.replace_one({"_id": "trafulha_principal"}, doc, upsert=True)
        except Exception as e:
            print(f"Erro ao salvar no MongoDB: {e}")

def carregar_historico_nuvem():
    timestamps = []
    patrimonio = []
    if collection_historico is not None:
        try:
            registos = collection_historico.find().sort("timestamp_ordenado", 1)
            for reg in registos:
                timestamps.append(reg["hora"])
                patrimonio.append(reg["valor"])
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
    return timestamps, patrimonio

def salvar_ponto_historico(hora, valor):
    if collection_historico is not None:
        try:
            doc = {
                "timestamp_ordenado": datetime.now(),
                "hora": hora,
                "valor": valor
            }
            collection_historico.insert_one(doc)
        except Exception as e:
            print(f"Erro ao salvar ponto no histórico: {e}")

ESTADO_ROBO = carregar_estado()

ts_inicial, pat_inicial = carregar_historico_nuvem()
HISTORICO_GRAFICO = {
    "timestamps": ts_inicial,
    "patrimonio": pat_inicial
}

# ==========================================
# 2. SERVIDOR WEB COM GRÁFICO GLOBAL
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
                    .card { background: #1e293b; padding: 20px; border-radius: 12px; max-width: 900px; margin: 20px auto; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
                    canvas { max-height: 450px; }
                    .status { font-size: 14px; color: #10b981; margin-top: 10px; }
                </style>
            </head>
            <body>
                <h1>🤖 Trafulha Smart Trading - Live Chart</h1>
                <div class="card">
                    <h3>Evolução Completa do Património (Anti-Drawdown Ativo)</h3>
                    <canvas id="graficoPatrimonio"></canvas>
                    <div class="status">🟢 Gestão de risco otimizada na nuvem</div>
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
                                x: { ticks: { color: '#94a3b8', maxTicksLimit: 10 } },
                                y: { ticks: { color: '#94a3b8' } }
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
                    setInterval(atualizarGrafico, 2000);
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
# 4. MOTOR DE TRADING INTELIGENTE (60s)
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
        enviar_telegram("🟢 *[TRAFULHA]* Ciclo Anti-Drawdown Ativo (100% Cripto)!")

    btc_val = ESTADO_ROBO["btc_tamanho"] * btc_preco
    eth_val = ESTADO_ROBO["eth_tamanho"] * eth_preco
    patrimonio_atual = ESTADO_ROBO["caixa"] + btc_val + eth_val

    # Registo para o gráfico histórico na nuvem
    hora_curta = datetime.now().strftime("%H:%M:%S")
    if not HISTORICO_GRAFICO["timestamps"] or HISTORICO_GRAFICO["timestamps"][-1] != hora_curta:
        HISTORICO_GRAFICO["timestamps"].append(hora_curta)
        HISTORICO_GRAFICO["patrimonio"].append(round(patrimonio_atual, 2))
        salvar_ponto_historico(hora_curta, round(patrimonio_atual, 2))

    # Mudança de dia e fecho de ganhos
    if hoje != ESTADO_ROBO["data_atual"]:
        lucro_ontem = patrimonio_atual - ESTADO_ROBO["patrimonio_inicio_dia"]
        emoji_ontem = "🟢" if lucro_ontem >= 0 else "🔴"
        enviar_telegram(f"📅 *Resumo Diário*\n• **Resultado**: `$ {lucro_ontem:,.2f}` {emoji_ontem}")
        ESTADO_ROBO["data_atual"] = hoje
        ESTADO_ROBO["patrimonio_inicio_dia"] = patrimonio_atual
        salvar_estado(ESTADO_ROBO)

    # ----------------------------------------------------
    # LÓGICA DE TRADING BTC (Com Stop Loss de Proteção)
    # ----------------------------------------------------
    variacao_btc = ((btc_preco - ESTADO_ROBO["btc_preco_referencia"]) / ESTADO_ROBO["btc_preco_referencia"]) * 100
    
    # PROTEÇÃO ANTI-DRAWDOWN: Se o preço despencar mais de -3.0%, corta para evitar buracos profundos
    if variacao_btc <= -3.0 and ESTADO_ROBO["btc_tamanho"] > 0:
        qtd_corte = ESTADO_ROBO["btc_tamanho"] * 0.50 # Corta metade da exposição
        valor_recuperado = qtd_corte * btc_preco
        ESTADO_ROBO["caixa"] += valor_recuperado
        ESTADO_ROBO["btc_tamanho"] -= qtd_corte
        ESTADO_ROBO["btc_preco_referencia"] = btc_preco
        salvar_estado(ESTADO_ROBO)
        enviar_telegram(f"🛡️ *[STOP LOSS BTC]* Queda drástica de {variacao_btc:.2f}%. Posição reduzida para defesa!")

    elif variacao_btc <= -0.6 and ESTADO_ROBO["caixa"] >= 500:
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

    # ----------------------------------------------------
    # LÓGICA DE TRADING ETH (Com Stop Loss de Proteção)
    # ----------------------------------------------------
    variacao_eth = ((eth_preco - ESTADO_ROBO["eth_preco_referencia"]) / ESTADO_ROBO["eth_preco_referencia"]) * 100
    
    # PROTEÇÃO ANTI-DRAWDOWN ETH
    if variacao_eth <= -3.0 and ESTADO_ROBO["eth_tamanho"] > 0:
        qtd_corte = ESTADO_ROBO["eth_tamanho"] * 0.50
        valor_recuperado = qtd_corte * eth_preco
        ESTADO_ROBO["caixa"] += valor_recuperado
        ESTADO_ROBO["eth_tamanho"] -= qtd_corte
        ESTADO_ROBO["eth_preco_referencia"] = eth_preco
        salvar_estado(ESTADO_ROBO)
        enviar_telegram(f"🛡️ *[STOP LOSS ETH]* Queda drástica de {variacao_eth:.2f}%. Posição reduzida para defesa!")

    elif variacao_eth <= -0.6 and ESTADO_ROBO["caixa"] >= 500:
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
        f"📊 *Relatório Trafulha (Anti-Drawdown)*\n\n"
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

print("🤖 Trafulha Anti-Drawdown com MongoDB Ativo!")
threading.Thread(target=loop_trading, daemon=True).start()
threading.Thread(target=loop_relatorios, daemon=True).start()

while True:
    time.sleep(3600)
