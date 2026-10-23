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
TOKEN = "8882501211:AAGQoteMJ86vBY-ShXYU3KjtvgsmNT07_9s"
CHAT_ID = "-5318794924"

# Mapeamento para a API da CoinGecko (sem bloqueios na nuvem)
ativos_ids = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "SUI": "sui"
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"[TELEGRAM] Resposta da API: {response.status_code}", flush=True)
    except Exception as e:
        print(f"[ERRO TELEGRAM] {e}", flush=True)

def obter_preco(ativo):
    coin_id = ativos_ids.get(ativo, "bitcoin")
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        res = requests.get(url, timeout=10).json()
        return float(res[coin_id]['usd'])
    except Exception as e:
        print(f"[ERRO API] Falha ao obter {ativo}: {e}", flush=True)
        # Fallbacks atualizados caso haja falha pontual de rede
        precos_fallback = {"BTC": 68000.0, "ETH": 3700.0, "SOL": 170.0, "BNB": 620.0, "SUI": 2.30}
        return precos_fallback.get(ativo, 100.0)

def main():
    print("🚀 [ROBÔ] A iniciar a lógica principal do Trafulha...", flush=True)
    time.sleep(3)  # Aguardar estabilização do Flask
    
    enviar_telegram("🤖 *Robô Trafulha* iniciado com sucesso na nuvem 24/7!")
    
    portfolio = {}
    
    # Registar o preço de compra inicial de referência
    for ativo in ativos_ids.keys():
        preco = obter_preco(ativo)
        portfolio[ativo] = preco
        print(f"[ROBÔ] Preço de compra inicial de {ativo}: {preco}", flush=True)
        
    enviar_telegram("📊 Configuração inicial concluída. A monitorizar os mercados em tempo real...")

    while True:
        try:
            print("[ROBÔ] A executar ciclo de verificação de preços...", flush=True)
            relatorio = "📈 *Relatório Detalhado - Trafulha*\n\n"
            
            for ativo, preco_compra in portfolio.items():
                preco_atual = obter_preco(ativo)
                dif = preco_atual - preco_compra
                variacao = (dif / preco_compra) * 100
                emoji = "🟢" if variacao >= 0 else "🔴"
                
                relatorio += f"*{ativo}*:\n" \
                             f"• Compra: `{preco_compra:.2f} USD`\n" \
                             f"• Atual: `{preco_atual:.2f} USD`\n" \
                             f"• Lucro/Prejuízo: {emoji} `{dif:+.2f} USD` (`{variacao:+.2f}%`)\n\n"
            
            enviar_telegram(relatorio)
        except Exception as e:
            print(f"[ERRO CICLO] {e}", flush=True)
        
        print("[ROBÔ] Ciclo terminado. A aguardar 1 hora...", flush=True)
        time.sleep(3600)

if __name__ == "__main__":
    main()
