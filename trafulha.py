import os
import time
import threading
import requests
import datetime
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

web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()

# --- Configuração do Robô de Trading ---
TOKEN = "8882501211:AAGQoteMJ86vBY-ShXYU3KjtvgsmNT07_9s"
CHAT_ID = "-5318794924"

ativos_binance = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "BNB": "BNBUSDT",
    "SUI": "SUIUSDT"
}

ativos_coingecko = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "SUI": "sui"
}

capital_alocado = {
    "BTC": 200.0,
    "ETH": 100.0,
    "SOL": 100.0,
    "BNB": 100.0,
    "SUI": 100.0
}

historico_tempos = []
historico_valores = []

def enviar_telegram_texto(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        response = requests.post(url, data=payload, timeout=15)
        print(f"[TELEGRAM TEXTO] Resposta da API: {response.status_code}", flush=True)
    except Exception as e:
        print(f"[ERRO TELEGRAM TEXTO] {e}", flush=True)

def enviar_telegram_foto(caminho_img):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(caminho_img, 'rb') as foto:
            payload = {"chat_id": CHAT_ID}
            response = requests.post(url, data=payload, files={"photo": foto}, timeout=15)
            print(f"[TELEGRAM FOTO] Resposta da API: {response.status_code}", flush=True)
    except Exception as e:
        print(f"[ERRO TELEGRAM FOTO] {e}", flush=True)

def obter_todos_os_precos():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # 1. Tentar Binance primeiro
    precos = {}
    try:
        for ativo, symbol in ativos_binance.items():
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            res = requests.get(url, headers=headers, timeout=4)
            data = res.json()
            if 'price' in data:
                precos[ativo] = float(data['price'])
        if len(precos) == len(ativos_binance):
            return precos
    except Exception as e:
        print(f"[AVISO API BINANCE] {e}", flush=True)

    # 2. Se a Binance falhar, tentar CoinGecko em lote
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,sui&vs_currencies=usd"
        res = requests.get(url, headers=headers, timeout=6)
        data = res.json()
        precos_cg = {}
        for ativo, coin_id in ativos_coingecko.items():
            if coin_id in data and 'usd' in data[coin_id]:
                precos_cg[ativo] = float(data[coin_id]['usd'])
        if len(precos_cg) == len(ativos_coingecko):
            return precos_cg
    except Exception as e:
        print(f"[AVISO API COINGECKO] {e}", flush=True)
    
    return None

def gerar_grafico(tempos, valores):
    plt.figure(figsize=(10, 5))
    plt.plot(tempos, valores, marker='o', color='#2ecc71', linewidth=2, markersize=6)
    plt.title('Evolução do Portfólio Trafulha (USD)', fontsize=14, fontweight='bold', color='#2c3e50')
    plt.xlabel('Hora do Registo', fontsize=11)
    plt.ylabel('Valor Total (USD)', fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=30)
    plt.tight_layout()
    
    caminho_img = 'grafico_portfolio.png'
    plt.savefig(caminho_img, dpi=150)
    plt.close()
    return caminho_img

def main():
    print("🚀 [ROBÔ] A iniciar a lógica principal do Trafulha...", flush=True)
    time.sleep(3)
    
    caixa_total = sum(capital_alocado.values())
    
    portfolio = {}
    precos_iniciais = None
    while not precos_iniciais:
        precos_iniciais = obter_todos_os_precos()
        if not precos_iniciais:
            print("[ROBÔ] A aguardar ligação às fontes de preços...", flush=True)
            time.sleep(5)
            
    for ativo, investido in capital_alocado.items():
        preco_inicial = precos_iniciais[ativo]
        quantidade = investido / preco_inicial if preco_inicial > 0 else 0
        portfolio[ativo] = {
            "preco_compra": preco_inicial,
            "quantidade": quantidade,
            "investido": investido
        }
    
    print("[ROBÔ] Configuração inicial concluída com sucesso.", flush=True)

    while True:
        try:
            print("[ROBÔ] A executar ciclo de verificação de preços...", flush=True)
            precos_atuais = obter_todos_os_precos()
            
            if not precos_atuais:
                print("[ROBÔ] Falha ao atualizar preços neste ciclo, a tentar novamente...", flush=True)
                time.sleep(30)
                continue
                
            relatorio = "📈 *Relatório de Portfólio Trafulha*\n\n"
            valor_total_portfolio = 0
            
            for ativo, dados in portfolio.items():
                preco_atual = precos_atuais.get(ativo, dados["preco_compra"])
                valor_atual = dados["quantidade"] * preco_atual
                lucro_prejuizo = valor_atual - dados["investido"]
                variacao = (lucro_prejuizo / dados["investido"]) * 100 if dados["investido"] > 0 else 0
                emoji = "🟢" if lucro_prejuizo >= 0 else "🔴"
                
                valor_total_portfolio += valor_atual
                
                relatorio += f"*{ativo}*:\n" \
                             f"• Preço Atual: `{preco_atual:.2f} USD`\n" \
                             f"• Investido: `{dados['investido']:.2f} USD`\n" \
                             f"• Valor Atual: `{valor_atual:.2f} USD`\n" \
                             f"• P/L: {emoji} `{lucro_prejuizo:+.2f} USD` (`{variacao:+.2f}%`)\n\n"
            
            lucro_total_geral = valor_total_portfolio - caixa_total
            variacao_total = (lucro_total_geral / caixa_total) * 100
            emoji_geral = "🟢" if lucro_total_geral >= 0 else "🔴"
            
            relatorio += f"💼 *Caixa Inicial:* `{caixa_total:.2f} USD`\n" \
                         f"💼 *Valor Atual:* `{valor_total_portfolio:.2f} USD`\n" \
                         f"📊 *Resultado Global:* {emoji_geral} `{lucro_total_geral:+.2f} USD` (`{variacao_total:+.2f}%`)"
            
            agora_str = datetime.datetime.now().strftime("%H:%M")
            historico_tempos.append(agora_str)
            historico_valores.append(valor_total_portfolio)
            
            if len(historico_tempos) > 24:
                historico_tempos.pop(0)
                historico_valores.pop(0)
                
            caminho_grafico = gerar_grafico(historico_tempos, historico_valores)
            
            enviar_telegram_texto(relatorio)
            enviar_telegram_foto(caminho_grafico)
            
        except Exception as e:
            print(f"[ERRO CICLO] {e}", flush=True)
        
        print("[ROBÔ] Ciclo terminado. A aguardar 900 segundos (15 minutos)...", flush=True)
        time.sleep(900)

if __name__ == "__main__":
    main()
