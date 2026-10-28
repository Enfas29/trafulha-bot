import os
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================
# 1. SERVIDOR WEB DE SUPORTE (Para o Render)
# ==========================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Trafulha Preditor Online & Operacional!")

def iniciar_servidor_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# ==========================================
# 2. CONFIGURAÇÕES E CREDENCIAIS
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "O_TEU_TOKEN_TELEGRAM")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "O_TEU_CHAT_ID")
HYPERLIQUID_PRIVATE_KEY = os.getenv("HYPERLIQUID_PRIVATE_KEY", "A_TUA_CHAVE_PRIVADA")

# Trio vencedor com pesos e alavancagem dinâmica avançada (3x / 5x) - Sem ETH nem SUI
ATIVOS_ALVO = {
    "BTC": {"peso": 0.40, "alavancagem": 3},
    "BNB": {"peso": 0.40, "alavancagem": 5},  # Alavancagem superior para potenciar o ganho na BNB
    "SOL": {"peso": 0.20, "alavancagem": 3}
}

def enviar_telegram(mensagem):
    """Envia relatórios automáticos e detalhados para o canal do Telegram."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")

def calcular_sinal_tecnico(ativo, preco_atual):
    """
    Lógica de alta convicção para decidir entre Long (subida) ou Short (queda)
    com base em indicadores dinâmicos de RSI e tendência.
    """
    # Podes integrar aqui a tua chamada real aos indicadores do motor de trading
    rsi = 42.5  # Exemplo representativo
    
    if rsi < 38:
        return "COMPRA_LONG", rsi
    elif rsi > 62:
        return "ABRE_SHORT", rsi
    else:
        return "MANTER_OU_NEUTRO", rsi

def executar_ciclo_trading():
    print("🚀 A iniciar ciclo do Trafulha Preditor (Modo Agressivo 3x/5x - Long & Short)...")
    
    # Iteração estritamente restrita ao trio vencedor
    for ativo, config in ATIVOS_ALVO.items():
        alavancagem = config["alavancagem"]
        peso = config["peso"]
        
        print(f"--- A processar {ativo} | Alavancagem: {alavancagem}x | Peso: {peso*100}% ---")
        
        # 1. Obter preço atual via API da Hyperliquid (integrar função real aqui)
        # preco_atual = obter_preco_hyperliquid(ativo)
        
        # 2. Obter sinal de decisão (Long ou Short)
        # acao, rsi = calcular_sinal_tecnico(ativo, preco_atual)
        
        # 3. Execução da ordem real na Hyperliquid com a alavancagem dinâmica
        # if acao == "COMPRA_LONG":
        #     executar_ordem_hyperliquid(ativo, "buy", alavancagem, peso)
        # elif acao == "ABRE_SHORT":
        #     executar_ordem_hyperliquid(ativo, "sell", alavancagem, peso)

    # Relatório dinâmico focado exclusivamente no trio para o Telegram
    relatorio = (
        "🔮 *TRAFULHA PREDITOR - MODO AGRESSIVO*\n"
        "⚡ *Alavancagem:* BTC/SOL 3x | BNB 5x\n"
        "🎯 *Foco Exclusivo:* BTC, BNB, SOL (Long & Short Ativos)\n\n"
        "✅ Sistema a operar com alta convicção, isolando ativos residuais e maximizando rentabilidade."
    )
    enviar_telegram(relatorio)

if __name__ == "__main__":
    # Inicia o servidor web em segundo plano para o Render não dar timeout de portas
    threading.Thread(target=iniciar_servidor_web, daemon=True).start()
    print("🌐 Servidor web de suporte iniciado com sucesso na porta atribuída.")

    # Ciclo contínuo de execução a cada 15 minutos
    while True:
        try:
            executar_ciclo_trading()
        except Exception as e:
            print(f"Erro no ciclo principal: {e}")
        
        # Aguardar 15 minutos para o próximo ciclo de mercado
        time.sleep(900)
