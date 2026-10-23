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

# Mapeamento para a API
ativos_ids = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "SUI": "sui"
}

# Capital alocado por cada ativo (Total = 1000 USD: 200 para cada um dos 5 ativos)
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

def obter_todos_os_precos():
    # Pedido único em lote para evitar bloqueios e obter preços em direto
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,sui&vs_currencies=usd"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10).json()
        
        precos = {}
        for ativo, coin_id in ativos_ids.items():
            if coin_id in res and 'usd' in res[coin_id]:
                precos[ativo] = float(res[coin_id]['usd'])
        
        if len(precos) == len(ativos_ids):
            return precos
    except Exception as e:
        print(f"[ERRO API BATCH] {e}", flush=True)
    
    return None

def main():
    print("🚀 [ROBÔ] A iniciar a lógica principal do Trafulha...", flush=True)
    time.sleep(3)
    
    enviar_telegram("🤖 *Robô Trafulha* iniciado com sucesso na nuvem 24/7!\n💰 *Caixa Total:* `1000.00 USD` (`200 USD` por ativo).")
    
    portfolio = {}
    
    # Obter preços iniciais reais em direto
    precos_iniciais = None
    while not precos_iniciais:
        precos_iniciais = obter_todos_os_precos()
        if not precos_iniciais:
            print("[ROBÔ] A aguardar ligação à API de preços...", flush=True)
            time.sleep(5)
            
    for ativo, preco_inicial in precos_iniciais.items():
        investido = capital_alocado[ativo]
        quantidade = investido / preco_inicial if preco_inicial > 0 else 0
        
        portfolio[ativo] = {
            "preco_compra": preco_inicial,
            "quantidade": quantidade,
            "investido": investido
        }
        print(f"[ROBÔ] {ativo} - Compra: {preco_inicial} | Qtd: {quantidade:.4f}", flush=True)
        
    enviar_telegram("📊 Configuração de portfólio concluída com preços reais. A monitorizar os mercados...")

    while True:
        try:
            print("[ROBÔ] A executar ciclo de verificação de preços...", flush=True)
            precos_atuais = obter_todos_os_precos()
            
            if not precos_atuais:
                print("[ROBÔ] Falha ao atualizar preços neste ciclo, a tentar novamente no próximo...", flush=True)
                time.sleep(60)
                continue
                
            relatorio = "📈 *Relatório de Portfólio em Direto (1000 USD)*\n\n"
            valor_total_portfolio = 0
            
            for ativo, dados in portfolio.items():
                preco_atual = precos_atuais.get(ativo, dados["preco_compra"])
                valor_atual = dados["quantidade"] * preco_atual
                lucro_prejuizo = valor_atual - dados["investido"]
                variacao = (lucro_prejuizo / dados["investido"]) * 100 if dados["investido"] > 0 else 0
                emoji = "🟢" if lucro_prejuizo >= 0 else "🔴"
                
                valor_total_portfolio += valor_atual
                
                relatorio += f"*{ativo}*:\n" \
                             f"• Compra: `{dados['preco_compra']:.2f} USD`\n" \
                             f"• Atual: `{preco_atual:.2f} USD`\n" \
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
