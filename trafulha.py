import os
import time
import threading
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

# --- Configuração do Servidor Web (Flask para manter o Render acordado) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Robô Trafulha a operar 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Iniciar o servidor web numa thread separada para não bloquear o robô
threading.Thread(target=run_web, daemon=True).start()

# --- Configuração do Robô de Trading ---
TOKEN = "8882501211:AAFDhktaz51HqJ_SYuiExFlhbyWXvJDgEo"
CHAT_ID = "-5318794924"
ativos = ["BTC", "ETH", "SOL", "BNB", "SUI"]

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")

def obter_preco(ativo):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={ativo}USDT"
        res = requests.get(url, timeout=10).json()
        return float(res['price'])
    except Exception:
        # Fallback de segurança caso a API falhe temporariamente
        precos_base = {"BTC": 65000, "ETH": 3500, "SOL": 150, "BNB": 600, "SUI": 2}
        return precos_base.get(ativo, 100)

def main():
    enviar_telegram("🤖 *Robô Trafulha* iniciado com sucesso na nuvem 24/7!")
    
    portfolio = {ativo: {"preco_compra": 0} for ativo in ativos}
    
    # Preço inicial de referência
    for ativo in ativos:
        portfolio[ativo]["preco_compra"] = obtain_price = obter_preco(ativo)
        
    enviar_telegram("📊 Configuração inicial concluída. A monitorizar os mercados...")

    while True:
        try:
            relatorio = "📈 *Relatório de Estado - Trafulha*\n\n"
            for ativo in ativos:
                preco_atual = obter_preco(ativo)
                preco_compra = portfolio[ativo]["preco_compra"]
                variacao = ((preco_atual - preco_compra) / preco_compra) * 100
                emoji = "🟢" if variacao >= 0 else "🔴"
                relatorio += f"*{ativo}*: `{preco_atual:.2f} USD` ({emoji} `{variacao:+.2f}%`)\n"
            
            enviar_telegram(relatorio)
        except Exception as e:
            print(f"Erro no ciclo do robô: {e}")
        
        # Aguardar 1 hora antes do próximo ciclo de verificação
        time.sleep(3600)

if __name__ == "__main__":
    main()
