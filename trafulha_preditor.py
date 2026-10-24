import os
import time
import requests
import matplotlib
matplotlib.use('Agg')  # Configura o matplotlib para ambientes headless (servidores)
import matplotlib.pyplot as plt
from flask import Flask
import threading

# --- 1. CONFIGURAÇÃO DO SERVIDOR WEB (FLASK) PARA O RENDER E UPTIMEROBOT ---
app = Flask(__name__)

@app.route('/')
def home():
    # Rota raiz necessária para responder ao UptimeRobot com código 200 (evita erro 502)
    return "Trafulha Preditor a funcionar 24/7!", 200

def run_flask():
    # Arranca o servidor Flask na porta 10000 exigida pelo Render
    app.run(host='0.0.0.0', port=10000)

# --- 2. CONFIGURAÇÕES DO ROBÔ E TELEGRAM ---
TOKEN = "8882501211:AAGQoteMJ86vBY-ShXYU3KjtvgsmNT07_9s"
CHAT_ID = "-5318794924"

# Moedas a monitorizar
ativos_alvo = ["BTC", "ETH", "SOL", "BNB", "SUI"]

# Histórico em memória para guardar preços de ciclos anteriores
historico_precos = {coin: [] for coin in ativos_alvo}

def obter_precos_hyperliquid():
    """Obtém os preços médios mais recentes da API pública da Hyperliquid."""
    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    payload = {"type": "allMids"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            precos = {}
            for coin in ativos_alvo:
                if coin in data:
                    precos[coin] = float(data[coin])
            return precos
        else:
            print(f"[ERRO HYPERLIQUID] Código HTTP: {response.status_code}")
            return None
    except Exception as e:
        print(f"[EXCEÇÃO HYPERLIQUID] {e}")
        return None

def gerar_grafico(precos_atuais):
    """Gera o gráfico de barras azul com o resumo dos preços atuais."""
    moedas = list(precos_atuais.keys())
    valores = list(precos_atuais.values())

    plt.figure(figsize=(9, 4.5))
    bars = plt.bar(moedas, valores, color='#2196F3', edgecolor='#0D47A1', alpha=0.85)

    plt.title("Trafulha Preditor - Preços Hyperliquid (Spot)", fontsize=13, fontweight='bold', pad=15)
    plt.ylabel("Preço (USD)", fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.4)

    # Adiciona os valores por cima de cada barra no gráfico
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval, f"${yval:,.2f}", 
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    caminho_imagem = "grafico_preditor.png"
    plt.savefig(caminho_imagem, dpi=120)
    plt.close()
    return caminho_imagem

def enviar_foto_telegram(caminho_imagem):
    """Envia o gráfico azul para o Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(caminho_imagem, 'rb') as photo:
            payload = {'chat_id': CHAT_ID}
            files = {'photo': photo}
            res = requests.post(url, data=payload, files=files, timeout=15)
            print(f"[TELEGRAM FOTO] Resposta da API: {res.status_code}")
    except Exception as e:
        print(f"[ERRO TELEGRAM FOTO] {e}")

def enviar_texto_telegram(mensagem):
    """Envia o relatório com indicadores de tendência para o Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }
    try:
        res = requests.
