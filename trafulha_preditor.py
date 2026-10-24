import os
import time
import requests
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask
import threading

# --- 1. SERVIDOR FLASK PARA RENDER E UPTIMEROBOT ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Trafulha Preditor Completo a funcionar 24/7!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# --- 2. CONFIGURAÇÕES DO ROBÔ E TELEGRAM ---
TOKEN = "8882501211:AAGQoteMJ86vBY-ShXYU3KjtvgsmNT07_9s"
CHAT_ID = "-5318794924"

ativos_alvo = ["BTC", "ETH", "SOL", "BNB", "SUI"]

# Histórico em memória para calcular indicadores técnicos
historico_precos = {coin: [] for coin in ativos_alvo}

def obter_precos_hyperliquid():
    """Obtém os preços em tempo real da API pública da Hyperliquid."""
    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    payload = {"type": "allMids"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {coin: float(data[coin]) for coin in ativos_alvo if coin in data}
        return None
    except Exception as e:
        print(f"[ERRO API] {e}")
        return None

def calcular_rsi(precos, periodo=14):
    """Calcula o RSI (Relative Strength Index)."""
    if len(precos) < periodo + 1:
        return 50.0  # Valor neutro por defeito se não houver dados suficientes
    
    deltas = np.diff(precos)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-periodo:])
    avg_loss = np.mean(losses[-periodo:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calcular_smas(precos):
    """Calcula as Médias Móveis Simples (SMA 5 vs SMA 15 para ciclos curtos)."""
    if len(precos) < 15:
        return None, None
    sma_curta = np.mean(precos[-5:])
    sma_longa = np.mean(precos[-15:])
    return round(sma_curta, 2), round(sma_longa, 2)

def gerar_grafico(precos_atuais):
    """Gera o gráfico visual azul com os preços atuais."""
    moedas = list(precos_atuais.keys())
    valores = list(precos_atuais.values())

    plt.figure(figsize=(9, 4.5))
    bars = plt.bar(moedas, valores, color='#2196F3', edgecolor='#0D47A1', alpha=0.85)

    plt.title("Trafulha Preditor - Análise Quantitativa", fontsize=13, fontweight='bold', pad=15)
    plt.ylabel("Preço (USD)", fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.4)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, f"${yval:,.2f}", 
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    caminho = "grafico_preditor.png"
    plt.savefig(caminho, dpi=120)
    plt.close()
    return caminho

def enviar_foto_telegram(caminho_imagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(caminho_imagem, 'rb') as photo:
            requests.post(url, data={'chat_id': CHAT_ID}, files={'photo': photo}, timeout=15)
    except Exception as e:
        print(f"[ERRO TELEGRAM FOTO] {e}")

def enviar_texto_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mensagem, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERRO TELEGRAM TEXTO] {e}")

def ciclo_principal():
    precos = obter_precos_hyperliquid()
    if not precos:
        return

    # Guarda histórico de até 100 ciclos para cálculo técnico
    for coin, preco in precos.items():
        historico_precos[coin].append(preco)
        if len(historico_precos[coin]) > 100:
            historico_precos[coin].pop(0)

    # 1. Enviar foto
    caminho_foto = gerar_grafico(precos)
    enviar_foto_telegram(caminho_foto)
    if os.path.exists(caminho_foto):
        os.remove(caminho_foto)

    # 2. Processar Análise Técnica
    msg = "🔮 *TRAFULHA PREDITOR - ANÁLISE QUANTITATIVA*\n"
    msg += "Indicadores: RSI (14) | SMA (5 vs 15)\n"
    msg += "-----------------------------------------\n\n"

    for coin in ativos_alvo:
        preco_atual = precos.get(coin, 0)
        dados = historico_precos[coin]
        
        rsi = calcular_rsi(dados)
        sma_curta, sma_longa = calcular_smas(dados)

        # Determinação do Sinal
        if rsi < 35 or (sma_curta and sma_longa and sma_curta > sma_longa):
            sinal = "🟢 *COMPRA / ACUMULAR* (Oportunidade)"
        elif rsi > 70 or (sma_curta and sma_longa and sma_curta < sma_longa):
            sinal = "🔴 *VENDA / CAIXA* (Proteger Lucro / Stop)"
        else:
            sinal = "🟡 *NEUTRO / MANTER*"

        msg += f"🔹 *{coin}*: ${preco_atual:,.2f}\n"
        msg += f"   └ RSI: `{rsi}` | Sinal: {sinal}\n\n"

    msg += "-----------------------------------------\n"
    msg += "⏳ Próxima análise em 15 minutos."

    enviar_texto_telegram(msg)

# --- 3. PONTO DE ENTRADA ---
if __name__ == "__main__":
    print("--- INICIANDO TRAFULHA PREDITOR COMPLETO ---")
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    while True:
        ciclo_principal()
        time.sleep(900)
