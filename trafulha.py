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

# IDs para a API da CoinGecko
ativos_ids = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "SUI": "sui"
}

# Capital alocado por cada ativo (Total = 1000 USD: 200 para BTC + 200 para os outros 4)
capital_alocado = {
    "BTC": 200.0,
    "ETH": 200.0,
    "SOL": 200.0,
    "BNB": 200.0,
    "SUI": 200.0
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
        if coin_id in res and 'usd' in res[coin_id]:
            return float(res[coin_id]['usd'])
    except Exception as e:
        print(f"[ERRO API] Falha ao obter {ativo}: {e}", flush=True)
    
    precos_fallback = {"BTC": 81300.0, "ETH": 2400.0, "SOL": 170.0, "BNB": 620.0, "SUI": 2.30}
    return precos_fallback.get(ativo, 100.0)

def main():
    print("🚀 [ROBÔ] A iniciar a lógica principal do Trafulha...", flush=True)
    time.sleep(3)
    
    enviar_telegram("🤖 *Robô Trafulha* iniciado com sucesso na nuvem 24/7!\n💰 *Caixa Total:* `1000.00 USD` (`200 USD` por ativo).")
    
    portfolio = {}
    
    # Registar o preço de compra inicial e calcular a quantidade comprada de cada ativo
    for ativo in ativos_ids.keys():
        preco_inicial = obter_preco(ativo)
        investido = capital_alocado[ativo]
        quantidade = investido / preco_inicial if preco_inicial > 0 else 0
        
        portfolio[ativo] = {
            "preco_compra": preco_inicial,
            "quantidade": quantidade,
            "investido": investido
        }
        print(f"[ROBÔ] {ativo} - Compra: {preco_inicial} | Qtd: {quantidade:.4f}", flush=True)
        
    enviar_telegram("📊 Configuração inicial de portfólio concluída. A monitorizar os mercados...")

    while True:
        try:
            print("[ROBÔ] A executar ciclo de verificação de preços...", flush=True)
            relatorio = "📈 *Relatório de Portfólio (1000 USD) - Trafulha*\n\n"
            
            valor_total_portfolio = 0
            
            for ativo, dados in portfolio.items():
                preco_atual = obter_preco(ativo)
                valor_atual = dados["quantidade"] * preco_atual
                lucro_prejuizo = valor_atual - dados["investido"]
                variacao = (lucro_prejuizo / dados["investido"]) * 100 if dados["investido"] > 0 else 0
                emoji = "🟢" if lucro_prejuizo >= 0 else "🔴"
                
                valor_total_portfolio += valor_atual
                
                relatorio += f"*{ativo}*:\n" \
                             f"• Investido: `{dados['investido']:.2f} USD`\n" \
                             f"• Valor Atual: `{valor_atual:.2f} USD`\n" \
                             f"• P/L: {emoji} `{lucro_prejuizo:+.2f} USD` (`{variacao:+.2f}%`)\n\n"
            
            lucro_total_geral = valor_total_portfolio - 1000.0
            variacao_total = (lucro_total_geral / 1000.0) * 100
             emoji_geral = "🟢" if lucro_total_geral >= 0 else "🔴"
            
            relatorio += f"💼 *Total da Carteira:* `1000 USD` ➡️ `{valor_total_portfolio:.2f} USD`\n" \
                         f"📊 *Lucro/Prejuízo Global:* {emoji_geral} `{lucro_total_geral:+.2f} USD` (`{variacao_total:+.2f}%`)"
            
            enviar_telegram(relatorio)
        except Exception as e:
            print(f"[ERRO CICLO] {e}", flush=True)
        
        print("[ROBÔ] Ciclo terminado. A aguardar 1 hora...", flush=True)
        time.sleep(3600)

if __name__ == "__main__":
    main()
