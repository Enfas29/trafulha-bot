import os
import time
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask
import threading

# --- 1. SERVIDOR FLASK PARA RENDER E UPTIMEROBOT ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Trafulha Bot Principal a funcionar 24/7!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# --- 2. CONFIGURAÇÕES DO ROBÔ E TELEGRAM ---
TOKEN = "8882501211:AAGQoteMJ86vBY-ShXYU3KjtvgsmNT07_9s"
CHAT_ID = "-5318794924"

# Carteira Spot Inicial (Investimento Teórico)
carteira_inicial = {
    "BTC": {"investido": 200.0, "alocacao_inicial": 200.0},
    "ETH": {"investido": 100.0, "alocacao_inicial": 100.0},
    "SOL": {"investido": 100.0, "alocacao_inicial": 100.0},
    "BNB": {"investido": 100.0, "alocacao_inicial": 100.0},
    "SUI": {"investido": 100.0, "alocacao_inicial": 100.0}
}

caixa_inicial = 600.0  # Capital Total Inicial em USD
historico_saldo = []
pico_historico_saldo = caixa_inicial  # Registo do All-Time High em sessão

def obter_precos_hyperliquid():
    """Obtém preços da API pública da Hyperliquid."""
    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    payload = {"type": "allMids"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {coin: float(data[coin]) for coin in carteira_inicial.keys() if coin in data}
        return None
    except Exception as e:
        print(f"[ERRO HYPERLIQUID] {e}")
        return None

def gerar_grafico_evolucao(historico):
    """Gera o gráfico de evolução do portfólio."""
    horas = [h['hora'] for h in historico[-20:]]  # Mostra as últimas 20 medições
    valores = [h['valor'] for h in historico[-20:]]

    plt.figure(figsize=(9, 4.5))
    plt.plot(horas, valores, marker='o', color='#4CAF50', linewidth=2, markersize=5)
    plt.title("Evolução do Portfólio Trafulha (Hyperliquid USD)", fontsize=13, fontweight='bold', pad=15)
    plt.xlabel("Hora do Registo", fontsize=9)
    plt.ylabel("Valor Total (USD)", fontsize=9)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.xticks(rotation=30, fontsize=8)
    plt.tight_layout()

    caminho = "grafico_portfolio.png"
    plt.savefig(caminho, dpi=120)
    plt.close()
    return caminho

def enviar_foto_telegram(caminho_imagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(caminho_imagem, 'rb') as photo:
            requests.post(url, data={'chat_id': CHAT_ID}, files={'photo': photo}, timeout=15)
    except Exception as e:
        print(f"[ERRO TELEGRAM FOTO] {e}")

def enviar_texto_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mensagem, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[ERRO TELEGRAM TEXTO] {e}")

def ciclo_principal():
    global pico_historico_saldo
    precos = obter_precos_hyperliquid()
    if not precos:
        return

    hora_atual = time.strftime("%H:%M")
    valor_carteira_atual = 0.0
    detalhes_moedas = []

    # Cálculo da posição de cada moeda
    for coin, info in carteira_inicial.items():
        preco_atual = precos.get(coin, 0)
        investido = info["investido"]
        
        # Na primeira execução guarda-se o preço base de referência
        if "preco_entrada" not in info and preco_atual > 0:
            info["preco_entrada"] = preco_atual

        preco_entrada = info.get("preco_entrada", preco_atual)
        qtd = investido / preco_entrada if preco_entrada > 0 else 0
        valor_atual_moeda = qtd * preco_atual
        valor_carteira_atual += valor_atual_moeda

        pl_moeda = valor_atual_moeda - investido
        pl_pct = (pl_moeda / investido * 100) if investido > 0 else 0
        
        emoji_pl = "🟢" if pl_moeda >= 0 else "🔴"
        detalhes_moedas.append(
            f"🔹 *{coin}*:\n"
            f"   • Preço Atual: `${preco_atual:,.2f}`\n"
            f"   • Investido: `${investido:,.2f}`\n"
            f"   • Valor Atual: `${valor_atual_moeda:,.2f}`\n"
            f"   • P/L: {emoji_pl} `${pl_moeda:+.2f}` (`{pl_pct:+.2f}%`)\n"
        )

    pl_global = valor_carteira_atual - caixa_inicial
    pl_global_pct = (pl_global / caixa_inicial * 100)
    
    # Atualiza Pico Histórico (ATH)
    if valor_carteira_atual > pico_historico_saldo:
        pico_historico_saldo = valor_carteira_atual

    # Registo para o gráfico
    historico_saldo.append({"hora": hora_atual, "valor": valor_carteira_atual})

    # 1. Enviar Gráficos de Evolução
    caminho_foto = gerar_grafico_evolucao(historico_saldo)
    enviar_foto_telegram(caminho_foto)
    if os.path.exists(caminho_foto):
        os.remove(caminho_foto)

    # 2. Avaliação de Estado e Alerta de Risco
    if pl_global_pct >= 1.0:
        estado_mercado = "🟢 *ESTADO: MERCADO SAUDÁVEL / GANHO*"
    elif pl_global_pct >= -1.5:
        estado_mercado = "🟡 *ESTADO: MERCADO LATERAL / ATENÇÃO*"
    else:
        estado_mercado = "🔴 *ESTADO: ALERTA DE QUEDA / PROTEÇÃO DE CAPITAL*"

    # 3. Construção do Relatório
    msg = f"📈 *RELATÓRIO DE PORTFÓLIO TRAFULHA*\n"
    msg += f"{estado_mercado}\n"
    msg += "-----------------------------------------\n\n"
    
    msg += "\n".join(detalhes_moedas) + "\n"
    msg += "-----------------------------------------\n"
    msg += f"💼 *Caixa Inicial:* `${caixa_inicial:,.2f}` USD\n"
    msg += f"💼 *Valor Atual:* `${valor_carteira_atual:,.2f}` USD\n"
    
    emoji_global = "🟢" if pl_global >= 0 else "🔴"
    msg += f"📊 *Resultado Global:* {emoji_global} `${pl_global:+.2f}` USD (`{pl_global_pct:+.2f}%`)\n"
    msg += f"🏆 *Pico Máximo Atingido:* `${pico_historico_saldo:,.2f}` USD\n\n"

    # Alerta especial se o prejuízo for significativo
    if pl_global_pct <= -2.0:
        msg += "🚨 *AVISO DE RISCO:* A carteira está exposta a uma queda superior a -2.0%. Considerar acionar a Caixa de Proteção.\n\n"

    msg += "⏳ Próxima atualização em 15 minutos."

    enviar_texto_telegram(msg)

# --- 3. PONTO DE ENTRADA ---
if __name__ == "__main__":
    print("--- INICIANDO ROBÔ PRINCIPAL PORTFÓLIO TRAFULHA ---")
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    while True:
        ciclo_principal()
        time.sleep(900)
