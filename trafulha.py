import os
import time
import threading
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

print("--- INICIO DO SCRIPT TRAFULHA ---")

# --- Configuração do Servidor Web (Flask para o Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    print("[WEB] Recebido pedido HTTP no Flask!")
    return "Robô Trafulha a operar 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    print(f"[WEB] A iniciar servidor Flask na porta {port}...")
    app.run(host="0.0.0.0", port=port)

# Iniciar o servidor Flask numa thread separada
threading.Thread(target=run_web, daemon=True).start()

# --- Configuração do Robô de Trading ---
TOKEN = "8882501211:AAFDhktaz51HqJ_SYuiExFlhbyWXvJDgEo"
CHAT_ID = "-5318794924"
ativos = ["BTC", "ETH", "SOL", "BNB", "SUI"]

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        print(f"[TELEGRAM] A enviar mensagem para o chat {CHAT_ID}...")
        response = requests.post(url, json=payload, timeout=10)
        print(f"[TELEGRAM] Resposta da API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERRO TELEGRAM] Falha ao enviar mensagem: {e}")

def obter_preco(ativo):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={ativo}USDT"
        res = requests.get(url, timeout=10).json()
        return float(res['price'])
    except Exception as e:
        print(f"[ERRO BINANCE] Falha ao obter preço para {ativo}: {e}")
        precos_base = {"BTC": 65000, "ETH": 3500, "SOL": 150, "BNB": 600, "SUI": 2}
        return precos_base.get(ativo, 100)

def main():
    print("🚀 [ROBÔ] A entrar na função main()...")
    time.sleep(2)  # Pequena pausa para garantir que o Flask estabilizou
    
    enviar_telegram("🤖 *Robô Trafulha* iniciado com sucesso na nuvem 24/7!")
    
    portfolio = {ativo: {"preco_compra": 0} for ativo in ativos}
    
    for ativo in ativos:
        preco = obter_preco(ativo)
        portfolio[ativo]["preco_compra"] = preco
        print(f"[ROBÔ] Preço inicial {ativo}: {preco}")
        
    enviar_telegram("📊 Configuração inicial concluída. A monitorizar os mercados...")

    while True:
        try:
            print("[ROBÔ] A executar ciclo de verificação de preços...")
            relatorio = "📈 *Relatório de Estado - Trafulha*\n\n"
            for ativo in ativos:
                preco_atual = obter_preco(ativo)
                preco_compra = portfolio[ativo]["preco_compra"]
                variacao = ((preco_atual - preco_compra) / preco_compra) * 100
                emoji = "🟢" if variacao >= 0 else "🔴"
                relatorio += f"*{ativo}*: `{preco_atual:.2f} USD` ({emoji} `{variacao:+.2f}%`)\n"
            
            enviar_telegram(relatorio)
        except Exception as e:
            print(f"[ERRO CICLO] Erro no ciclo do robô: {e}")
        
        print("[ROBÔ] Ciclo terminado. A aguardar 1 hora...")
        time.sleep(3600)

if __name__ == "__main__":
    main()
