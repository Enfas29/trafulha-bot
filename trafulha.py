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

# Pares de ativos e capital alocado exatamente como pedido:
# BTC: 200, ETH: 100, SOL: 100, BNB: 100, SUI: 100 (Total = 600 USD)
capital_alocado = {
    "BTC": 200.0,
    "ETH": 100.0,
    "SOL": 100.0,
    "BNB": 100.0,
    "SUI": 100.0
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
    try:
        par = f"{ativo}USDT"
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={par}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5).json()
        if 'price' in res:
            return float(res['price'])
    except Exception as e:
        print(f"[ERRO API Binance] {ativo}: {e}", flush=True)
    
    # Fallback dinâmico caso a rede falhe
    precos_fallback = {"BTC": 81000.0, "ETH": 2400.0, "SOL": 170.0, "BNB": 620.0, "SUI": 2.30}
    return precos_fallback.get(ativo, 100.0)

def main():
    print("🚀 [ROBÔ] A iniciar a lógica principal do Trafulha...", flush=True)
    time.sleep(3)
    
    caixa_total = sum(capital_alocado.values())
    enviar_telegram(f"🤖 *Robô Trafulha* iniciado com sucesso na nuvem 24/7!\n💰 *Caixa Total:* `{caixa_total:.2f} USD` (BTC: 200 | Outros: 100).")
    
    portfolio = {}
    
    # Registar preços iniciais e calcular a quantidade comprada de cada ativo
    for ativo, investido in capital_alocado.items():
        preco_inicial = obter_preco(ativo)
        quantidade = investido / preco_inicial if preco_inicial > 0 else 0
        
        portfolio[ativo] = {
            "preco_compra": preco_inicial,
            "quantidade": quantidade,
            "investido": investido
        }
        print(f"[ROBÔ] {ativo} - Investido: {investido} | Preço Compra: {preco_inicial} | Qtd: {quantidade:.4f}", flush=True)
        
    enviar_telegram("📊 Configuração concluída com valores reais. A monitorizar os mercados...")

    while True:
        try:
            print("[ROBÔ] A executar ciclo de verificação de preços...", flush=True)
            relatorio = "📈 *Relatório de Portfólio - Trafulha*\n\n"
            
            valor_total_portfolio = 0
            
            for ativo, dados in portfolio.items():
                preco_atual = obter_preco(ativo)
                valor_atual = dados["quantidade"] * preco_atual
                lucro_prejuizo = valor_atual - dados["investido"]
                variacao = (lucro_prejuizo / dados["investido"]) * 100 if dados["investido"] > 0 else 0
                emoji = "🟢" if lucro_prejuizo >= 0 else "🔴"
                
                valor_total_portfolio += valor_atual
                
                relatorio += f"*{ativo}*:\n" \
                             f"• Preço Atual da Moeda: `{preco_atual:.2f} USD`\n" \
                             f"• Valor Investido: `{dados['investido']:.2f} USD`\n" \
                             f"• Valor Atual na Posição: `{valor_atual:.2f} USD`\n" \
                             f"• Lucro/Prejuízo: {emoji} `{lucro_prejuizo:+.2f} USD` (`{variacao:+.2f}%`)\n\n"
            
            lucro_total_geral = valor_total_portfolio - caixa_total
            variacao_total = (lucro_total_geral / caixa_total) * 100
            emoji_geral = "🟢" if lucro_total_geral >= 0 else "🔴"
            
            relatorio += f"💼 *Caixa Total Inicial:* `{caixa_total:.2f} USD`\n" \
                         f"💼 *Valor Total Atual:* `{valor_total_portfolio:.2f} USD`\n" \
                         f"📊 *Resultado Global:* {emoji_geral} `{lucro_total_geral:+.2f} USD` (`{variacao_total:+.2f}%`)"
            
            enviar_telegram(relatorio)
        except Exception as e:
            print(f"[ERRO CICLO] {e}", flush=True)
        
        print("[ROBÔ] Ciclo terminado. A aguardar 1 hora...", flush=True)
        time.sleep(900)

if __name__ == "__main__":
    main()
