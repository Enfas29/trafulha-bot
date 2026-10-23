import os
import time
import threading
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

print("--- INICIO DO SCRIPT TRAFULHA ---", flush=True)

# --- Configuração do Servidor Web (Flask para o Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    print("[WEB] Recebido pedido HTTP no Flask!", flush=True)
    return "Robô Trafulha a operar 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    print(f"[WEB] A iniciar servidor Flask na porta {port}...", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Iniciar o servidor Flask numa thread separada
web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()

# --- Configuração do Robô de Trading ---
# ATENÇÃO: Confirma se este Token está correto no BotFather caso dê erro 401
TOKEN = "8882501211:AAFDhktaz51HqJ_SYuiExFlhbyWXvJDgEo"
CHAT_ID = "-5318794924"

# Mapeamento dos ativos para os IDs da CoinCap
ativos_ids = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binance-coin",
    "SUI": "sui"
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        print(f"[TELEGRAM] A enviar mensagem para o chat {CHAT_ID}...", flush=True)
        response = requests.post(url, json=payload, timeout=10)
        print(f"[TELEGRAM] Resposta da API: {response.status_code} - {response.text}", flush=True)
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha ao enviar mensagem: {e}", flush=True)

def obter_preco(ativo):
    coin_id = ativos_ids.get(ativo, "bitcoin")
    try:
        url = f"https://api.coincap.io/v2/assets/{coin_id}"
        res = requests.get(url, timeout=10).json()
        return float(res['data']['priceUsd'])
    except Exception as e:
        print(f"[ERRO API] Falha ao obter preço para {ativo}: {e}", flush=True)
        precos_base = {"BTC": 65000, "ETH": 3500, "SOL": 150, "BNB": 600, "SUI": 2}
        return precos_base.get(ativo, 100)

def main():
    print("🚀 [ROBÔ] A iniciar a lógica principal do Trafulha...", flush=True)
    time.sleep(3)  # Aguardar estabilização do Flask
    
    enviar_telegram("🤖 *Robô Trafulha* iniciado com sucesso na nuvem 24/7!")
    
    portfolio = {ativo: {"preco_compra": 0} for ativo in ativos_ids.keys()}
    
    for ativo in ativos_ids.keys():
        preco = obter_preco(ativo)
        portfolio[ativo]["preco_compra"] = preco
        print(f"[ROBÔ] Preço inicial {ativo}: {preco}", flush=True)
        
    enviar_telegram("📊 Configuração inicial concluída. A monitorizar os mercados...")

    while True:
        try:
            print("[ROBÔ] A executar ciclo de verificação de preços...", flush=True)
            relatorio = "📈 *Relatório de Estado - Trafulha*\n\n"
            for ativo in ativos_ids.keys():
                preco_atual = obter_preco(ativo)
                preco_compra = portfolio[ativo]["preco_compra"]
                variacao = ((preco_atual - preco_compra) / preco_compra) * 100
                emoji = "🟢" if variacao >= 0 else "🔴"
                relatorio += f"*{ativo}*: `{preco_atual:.2f} USD` ({emoji} `{variacao:+.2f}%`)\n"
            
            enviar_telegram(relatorio)
        except Exception as e:
            print(f"[ERRO CICLO] Erro no ciclo do robô: {e}", flush=True)
        
        print("[ROBÔ] Ciclo terminado. A aguardar 1 hora...", flush=True)
        time.sleep(3600)

if __name__ == "__main__":
    main()
