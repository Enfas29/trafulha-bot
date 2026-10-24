import os
import time
import threading
import requests
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

print("--- INICIO DO SCRIPT TRAFULHA PREDITOR (HYPERLIQUID) ---", flush=True)

# --- Configuração do Servidor Web (Flask para o Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    print("[WEB] Recebido pedido HTTP no Flask (Preditor)!", flush=True)
    return "Robô Trafulha Preditor a operar 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    print(f"[WEB] A iniciar servidor Flask na porta {port}...", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()

# --- Configuração do Robô ---
TOKEN = "8882501211:AAGQoteMJ86vBY-ShXYU3KjtvgsmNT07_9s"
CHAT_ID = "-5318794924"

ativos_alvo = ["BTC", "ETH", "SOL", "BNB", "SUI"]

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
    url = "https://api.hyperliquid.xyz/info"
    headers = {'Content-Type': 'application/json'}
    payload = {"type": "allMids"}
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=5)
        data = res.json()
        precos = {}
        
        for ativo in ativos_alvo:
            if ativo in data:
                precos[ativo] = float(data[ativo])
                
        if len(precos) == len(ativos_alvo):
            return precos
            
    except Exception as e:
        print(f"[ERRO API HYPERLIQUID] {e}", flush=True)
        
    return None

def gerar_grafico(tempos, valores):
    plt.figure(figsize=(10, 5))
    plt.plot(tempos, valores, marker='o', color='#3498db', linewidth=2, markersize=6)
    plt.title('Evolução do Portfólio - Trafulha Preditor (USD)', fontsize=14, fontweight='bold', color='#2c3e50')
    plt.xlabel('Hora do Registo', fontsize=11)
    plt.ylabel('Valor Total (USD)', fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=30)
    plt.tight_layout()
    
    caminho_img = 'grafico_preditor.png'
    plt.savefig(caminho_img, dpi=150)
    plt.close()
    return caminho_img

def main():
    print("🚀 [ROBÔ] A iniciar o Trafulha Preditor...", flush=True)
    time.sleep(3)
    
    caixa_total = sum(capital_alocado.values())
    
    portfolio = {}
    precos_anteriores = None
    
    while not precos_anteriores:
        precos_anteriores = obter_todos_os_precos()
        if not precos_anteriores:
            print("[ROBÔ] A aguardar ligação à API da Hyperliquid...", flush=True)
            time.sleep(5)
            
    for ativo, investido in capital_alocado.items():
        preco_inicial = precos_anteriores[ativo]
        quantidade = investido / preco_inicial if preco_inicial > 0 else 0
        portfolio[ativo] = {
            "preco_compra": preco_inicial,
            "quantidade": quantidade,
            "investido": investido
        }
    
    print("[ROBÔ] Configuração inicial concluída com sucesso.", flush=True)

    while True:
        try:
            print("[ROBÔ] A executar ciclo de análise e preços...", flush=True)
            precos_atuais = obter_todos_os_precos()
            
            if not precos_atuais:
                print("[ROBÔ] Falha ao atualizar preços neste ciclo, a tentar novamente...", flush=True)
                time.sleep(30)
                continue
                
            relatorio = "🔮 *Relatório & Tendência - Trafulha Preditor*\n\n"
            valor_total_portfolio = 0
            
            for ativo, dados in portfolio.items():
                preco_atual = precos_atuais.get(ativo, dados["preco_compra"])
                preco_antigo = precos_anteriores.get(ativo, preco_atual)
                
                # Análise de tendência de curto prazo (comparação com o ciclo anterior)
                diff_preco = preco_atual - preco_antigo
                if diff_preco > 0:
                    tendencia = "📈 A Subir (Alta)"
                    emoji_tend = "🟢"
                elif diff_preco < 0:
                    tendencia = "📉 A Descer (Baixa)"
                    emoji_tend = "🔴"
                else:
                    tendencia = "➡️ Estável"
                    emoji_tend = "⚪"
                
                valor_atual = dados["quantidade"] * preco_atual
                lucro_prejuizo = valor_atual - dados["investido"]
                variacao = (lucro_prejuizo / dados["investido"]) * 100 if dados["investido"] > 0 else 0
                emoji_pl = "🟢" if lucro_prejuizo >= 0 else "🔴"
                
                valor_total_portfolio += valor_atual
                
                relatorio += f"*{ativo}*:\n" \
                             f"• Preço Atual: `{preco_atual:.2f} USD`\n" \
                             f"• Tendência: {emoji_tend} *{tendencia}*\n" \
                             f"• P/L: {emoji_pl} `{lucro_prejuizo:+.2f} USD` (`{variacao:+.2f}%`)\n\n"
            
            # Atualizar preços anteriores para o próximo ciclo
            precos_anteriores = precos_atuais.copy()
            
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
            
            # Envio ordenado: Gráfico primeiro, texto depois
            enviar_telegram_foto(caminho_grafico)
            enviar_telegram_texto(relatorio)
            
        except Exception as e:
            print(f"[ERRO CICLO] {e}", flush=True)
        
        print("[ROBÔ] Ciclo terminado. A aguardar 900 segundos (15 minutos)...", flush=True)
        time.sleep(900)

if __name__ == "__main__":
    main()
