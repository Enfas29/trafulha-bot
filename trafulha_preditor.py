import os
import time
import json
import requests
import threading
import ccxt
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo import MongoClient

# ==========================================
# CONFIGURAÇÕES DE ESTRATÉGIA
# ==========================================
MODO_REAL = False # Coloca a True quando quiseres negociar dinheiro real
CORRETORA = 'binance' # Podes mudar para 'bybit', 'kraken', etc.

# Parâmetros de Gestão de Risco
STOP_LOSS_PCT = -5.0      # Vende para cortar perdas se cair 5%
TAKE_PROFIT_PCT = 3.0     # Vende para garantir lucro se subir 3%
BUY_DIP_PCT = -1.5        # Compra a queda se descer 1.5%
VALOR_COMPRA_DIP = 500.0  # Quantidade de USD a usar em cada compra

# ==========================================
# 1. LIGAÇÃO AO MONGODB E CCXT
# ==========================================
MONGO_URI = os.getenv("MONGO_URI")
db, collection_estado, collection_historico = None, None, None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client["trafulha_db"]
        collection_estado = db["estado"]
        collection_historico = db["historico_grafico"]
        print("☁️ Ligado ao MongoDB Atlas com sucesso!")
    except Exception as e:
        print(f"❌ Erro crítico ao ligar ao MongoDB: {e}")

# Inicializar a corretora via CCXT (para leitura de preços e OHLCV)
exchange = getattr(ccxt, CORRETORA)({
    'apiKey': os.getenv('API_KEY_CORRETORA', ''),
    'secret': os.getenv('API_SECRET_CORRETORA', ''),
    'enableRateLimit': True,
})

def carregar_estado():
    if collection_estado is not None:
        try:
            dados_db = collection_estado.find_one({"_id": "trafulha_principal"})
            if dados_db:
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
    timestamps, patrimonio = [], []
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
HISTORICO_GRAFICO = {"timestamps": ts_inicial, "patrimonio": pat_inicial}

# ==========================================
# 2. SERVIDOR WEB COM GRÁFICO GLOBAL
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/dados":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(HISTORICO_GRAFICO).encode("utf-8"))
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
                <title>Trafulha Smart Trading v2</title>
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
                    <h3>Evolução do Património (Tendência SMA 50)</h3>
                    <canvas id="graficoPatrimonio"></canvas>
                    <div class="status">🟢 Motor CCXT & Gestão de Risco Ativos</div>
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
                        options: { responsive: true, plugins: { legend: { labels: { color: '#f8fafc' } } }, scales: { x: { ticks: { color: '#94a3b8', maxTicksLimit: 10 } }, y: { ticks: { color: '#94a3b8' } } } }
                    });
                    async function atualizarGrafico() {
                        try {
                            const resposta = await fetch('/dados');
                            const dados = await resposta.json();
                            grafico.data.labels = dados.timestamps;
                            grafico.data.datasets[0].data = dados.patrimonio;
                            grafico.update('none');
                        } catch (erro) { console.error('Erro gráfico:', erro); }
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
            self.wfile.write(b"Trafulha Bot V2 Online!")

def iniciar_servidor_web():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthCheckHandler).serve_forever()

threading.Thread(target=iniciar_servidor_web, daemon=True).start()

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
# 4. MOTOR DE TENDÊNCIA E PREÇOS (CCXT)
# ==========================================
def obter_tendencia_e_preco(simbolo="BTC/USDT"):
    try:
        # Busca as últimas 50 horas de preços para calcular a Média Móvel (SMA)
        velas = exchange.fetch_ohlcv(simbolo, timeframe='1h', limit=50)
        fechos = [vela[4] for vela in velas]
        preco_atual = fechos[-1]
        sma_50 = sum(fechos) / len(fechos)
        tendencia_alta = preco_atual > sma_50
        return preco_atual, tendencia_alta, sma_50
    except Exception as e:
        print(f"Erro ao obter dados de {simbolo}: {e}")
        return 0.0, False, 0.0

def avaliar_ativo(moeda, simbolo, preco_atual, tendencia_alta, tamanho_posicao, preco_ref):
    global ESTADO_ROBO
    
    variacao = ((preco_atual - preco_ref) / preco_ref) * 100 if preco_ref > 0 else 0
    
    # PROTEÇÃO STOP-LOSS (Corte imediato, independentemente da tendência)
    if variacao <= STOP_LOSS_PCT and tamanho_posicao > 0:
        qtd_venda = tamanho_posicao * 0.75 # Vende 75% da posição para travar a sangria
        valor_recuperado = qtd_venda * preco_atual
        
        if MODO_REAL:
            # Aqui entraria a ordem real de venda no CCXT: exchange.create_market_sell_order(...)
            pass
            
        ESTADO_ROBO["caixa"] += valor_recuperado
        ESTADO_ROBO[f"{moeda}_tamanho"] -= qtd_venda
        ESTADO_ROBO[f"{moeda}_preco_referencia"] = preco_atual
        enviar_telegram(f"🚨 *[STOP LOSS]* {moeda.upper()} caiu {variacao:.2f}%. Posição descarregada para defesa! Recuperado: `$ {valor_recuperado:.2f}`")
        return True

    # ESTRATÉGIA: TAKE PROFIT (Venda na alta)
    elif variacao >= TAKE_PROFIT_PCT and tamanho_posicao > 0:
        qtd_venda = tamanho_posicao * 0.25 # Tranca lucro de 25% da posição
        valor_recebido = qtd_venda * preco_atual
        
        if MODO_REAL:
            pass # Ordem CCXT de venda real
            
        ESTADO_ROBO["caixa"] += valor_recebido
        ESTADO_ROBO[f"{moeda}_tamanho"] -= qtd_venda
        ESTADO_ROBO[f"{moeda}_preco_referencia"] = preco_atual
        enviar_telegram(f"💰 *[TAKE PROFIT]* {moeda.upper()} subiu {variacao:.2f}%. Lucro trancado: `$ {valor_recebido:.2f}`")
        return True

    # ESTRATÉGIA: COMPRA NA QUEDA (Apenas se a tendência macro for de alta!)
    elif variacao <= BUY_DIP_PCT and ESTADO_ROBO["caixa"] >= VALOR_COMPRA_DIP:
        if tendencia_alta:
            qtd_compra = VALOR_COMPRA_DIP / preco_atual
            
            if MODO_REAL:
                pass # Ordem CCXT de compra real
                
            ESTADO_ROBO["caixa"] -= VALOR_COMPRA_DIP
            ESTADO_ROBO[f"{moeda}_tamanho"] += qtd_compra
            ESTADO_ROBO[f"{moeda}_preco_referencia"] = preco_atual
            enviar_telegram(f"🟢 *[BUY THE DIP]* {moeda.upper()} corrigiu {variacao:.2f}% mas mantém-se acima da Média Móvel (50). Comprados `$ {VALOR_COMPRA_DIP}`.")
            return True
        else:
            print(f"Queda de {moeda.upper()} detetada ({variacao:.2f}%), mas a Tendência é de BAIXA. Compra abortada para evitar faca a cair.")

    return False

# ==========================================
# 5. MOTOR PRINCIPAL
# ==========================================
def avaliar_e_negociar():
    global ESTADO_ROBO, HISTORICO_GRAFICO
    
    btc_preco, btc_tendencia, btc_sma = obter_tendencia_e_preco("BTC/USDT")
    eth_preco, eth_tendencia, eth_sma = obter_tendencia_e_preco("ETH/USDT")
    
    if btc_preco == 0.0 or eth_preco == 0.0:
        return

    hoje = datetime.now().strftime("%Y-%m-%d")

    # Injeção de Capital Inicial (Simulação)
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
        enviar_telegram("🤖 *[TRAFULHA V2 INICIADO]*\n• Integração CCXT Ativa\n• Filtro de Média Móvel (SMA 50) Ativado!")

    # Gestão Diária
    patrimonio_atual = ESTADO_ROBO["caixa"] + (ESTADO_ROBO["btc_tamanho"] * btc_preco) + (ESTADO_ROBO["eth_tamanho"] * eth_preco)
    if hoje != ESTADO_ROBO["data_atual"]:
        lucro_ontem = patrimonio_atual - ESTADO_ROBO["patrimonio_inicio_dia"]
        emoji = "🟢" if lucro_ontem >= 0 else "🔴"
        enviar_telegram(f"📅 *Resumo Diário Trafulha V2*\n• **Resultado**: `$ {lucro_ontem:,.2f}` {emoji}")
        ESTADO_ROBO["data_atual"] = hoje
        ESTADO_ROBO["patrimonio_inicio_dia"] = patrimonio_atual
        salvar_estado(ESTADO_ROBO)

    # Registo Histórico
    hora_curta = datetime.now().strftime("%H:%M")
    if not HISTORICO_GRAFICO["timestamps"] or HISTORICO_GRAFICO["timestamps"][-1] != hora_curta:
        HISTORICO_GRAFICO["timestamps"].append(hora_curta)
        HISTORICO_GRAFICO["patrimonio"].append(round(patrimonio_atual, 2))
        salvar_ponto_historico(hora_curta, round(patrimonio_atual, 2))

    # Executar Avaliações
    alteracao_btc = avaliar_ativo("btc", "BTC/USDT", btc_preco, btc_tendencia, ESTADO_ROBO["btc_tamanho"], ESTADO_ROBO["btc_preco_referencia"])
    alteracao_eth = avaliar_ativo("eth", "ETH/USDT", eth_preco, eth_tendencia, ESTADO_ROBO["eth_tamanho"], ESTADO_ROBO["eth_preco_referencia"])
    
    if alteracao_btc or alteracao_eth:
        salvar_estado(ESTADO_ROBO)

def loop_trading():
    while True:
        try:
            avaliar_e_negociar()
        except Exception as e:
            print(f"Erro no ciclo principal: {e}")
        time.sleep(60)

print("🤖 Trafulha V2 (CCXT + SMA 50) Online!")
threading.Thread(target=loop_trading, daemon=True).start()

while True:
    time.sleep(3600)
