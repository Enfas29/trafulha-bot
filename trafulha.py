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

# Iniciar o servidor Flask numa thread separada
web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()

# --- Configuração do Robô de Trading ---
TOKEN = "8882501211:AAGQoteMJ86vBY-ShXYU3KjtvgsmNT07_9s"
CHAT_ID = "-5318794924"

# Pares na Binance para obter preços reais ao cêntimo
ativos_binance = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
    "BNB": "BNBUSDT",
    "SUI": "SUIUSDT"
}

# Capital alocado por ativo: BTC = 200 USD | Outros = 100 USD cada (Total = 600 USD)
capital_alocado = {
    "BTC": 200.0,
    "ETH": 100.0,
    "SOL": 100.0,
    "BNB": 100.0,
    "SUI": 100.0
}

# Histórico para o gráfico
historico_tempos = []
historico_valores = []

def enviar_telegram_com_foto(mensagem, caminho_img):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(caminho_img, 'rb') as foto:
            payload = {"chat_id": CHAT_ID, "caption": mensagem, "parse_mode": "Markdown"}
            response = requests.post(url, data=payload, files={"photo": foto}, timeout=15)
            print(f"[TELEGRAM FOTO] Resposta da API: {response.status_code}", flush=True)
    except Exception as e:
        print(f"[ERRO TELEGRAM FOTO] {e}", flush=True)

def obter_todos_os_precos():
    precos = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        for ativo, symbol in ativos_binance.items():
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            res = requests.get(url, headers=headers, timeout=5).json()
            if 'price' in res:
                precos[ativo] = float(res['price'])
        
        if len(precos) == len(ativos_binance):
            return precos
    except Exception as e:
        print(f"[ERRO API BINANCE] {e}", flush=True)
    
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
            print("[ROBÔ] A aguardar ligação à API de preços da Binance...", flush=True)
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
                time.sleep(60)
                continue
                
            relatorio = "📈 *Relatório de Portfólio com Gráfico*\n\n"
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
            
            # Registar dados para o histórico do gráfico
            agora_str = datetime.datetime.now().strftime("%H:%M")
            historico_tempos.append(agora_str)
            historico_valores.append(valor_total_portfolio)
            
            # Manter apenas os últimos 24 registos para o gráfico
            if len(historico_tempos) > 24:
                historico_tempos.pop(0)
                historico_valores.pop(0)
                
            # Gerar imagem do gráfico
            caminho_grafico = gerar_grafico(historico_tempos, historico_valores)
            
            # Enviar relatório com a foto para o Telegram
            enviar_telegram_com_foto(relatorio, caminho_grafico)
            
        except Exception as e:
            print(f"[ERRO CICLO] {e}", flush=True)
        
        print("[ROBÔ] Ciclo terminado. A aguardar 900 segundos (15 minutos)...", flush=True)
        time.sleep(900)

if __name__ == "__main__":
    main()
