import matplotlib
matplotlib.use('Agg') # Essencial para servidores na nuvem sem ecrã
import requests
import datetime
import time
import matplotlib.pyplot as plt

# --- CONFIGURAÇÕES GERAIS ---
TOKEN_TELEGRAM = "8882501211:AAFDhktaz51HqJ_SYuiExFlhbyWXvJDgEo"
CHAT_ID = "-5318794924"

capital_investido = 1000.0
saldo_caixa = 200.0
valor_para_cripto = capital_investido - saldo_caixa  # $800.00

# Parâmetros do Agendador e Gestão de Risco
INTERVALO_SEGUNDOS = 1800      # 30 minutos por ciclo
TRAILING_STOP_DISTANCIA = 6.0  # Margem de segurança de 6% a partir do pico
TEMPO_EM_CAIXA_CICLOS = 2      # Espera 2 ciclos em caixa antes de reentrar automaticamente

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "SUI": "sui"
}

def obter_preco_seguro(simbolo):
    try:
        coin_id = COINGECKO_IDS.get(simbolo)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        res = requests.get(url, timeout=10).json()
        preco = res[coin_id]["usd"]
        if preco > 0:
            return float(preco)
    except Exception as e:
        print(f"⚠️ Erro ao obter preço de {simbolo}: {e}")
    return 0.0

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Erro ao enviar mensagem para o Telegram: {e}")

# --- COMPRA INICIAL ---
alocacao_inicial = valor_para_cripto / 5.0
carteira = {}

print("🚀 A realizar a compra inicial dos 5 ativos...")
for cripto in COINGECKO_IDS:
    preco = obter_preco_seguro(cripto)
    carteira[cripto] = alocacao_inicial / preco if preco > 0 else 0.0

print("✅ Compra inicial concluída! A iniciar o agendador em ciclo contínuo...")

historico_tempos = []
historico_totais = []
max_lucro_atingido = 0.0
ciclos_em_caixa = 0

try:
    while True:
        data_execucao = datetime.datetime.now().strftime("%H:%M:%S")
        data_completa = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        patrimonio_cripto = 0.0
        valores_por_ativo = {}

        # Reentrada automática se estiver 100% em caixa
        if sum(carteira.values()) == 0.0:
            ciclos_em_caixa += 1
            print(f"⏳ Robô em caixa seguro. Ciclo de espera: {ciclos_em_caixa}/{TEMPO_EM_CAIXA_CICLOS}")
            
            if ciclos_em_caixa >= TEMPO_EM_CAIXA_CICLOS:
                print("🚀 Reentrada automática: a reinvestir o saldo em caixa...")
                valor_por_ativo_reinvestir = saldo_caixa / 5.0
                for cripto in carteira:
                    preco = obter_preco_seguro(cripto)
                    carteira[cripto] = valor_por_ativo_reinvestir / preco if preco > 0 else 0.0
                
                saldo_caixa = 0.0
                ciclos_em_caixa = 0
                max_lucro_atingido = 0.0
                enviar_telegram("🚀 *TRAFULHA: REENTRADA AUTOMÁTICA NO MERCADO!*\nO robô reinvestiu o saldo em caixa para apanhar nova tendência.")

        # Calcular património atual
        for cripto, quantidade in carteira.items():
            if quantidade > 0:
                preco = obter_preco_seguro(cripto)
                valor_ativo = quantidade * preco
                valores_por_ativo[cripto] = valor_ativo
                patrimonio_cripto += valor_ativo
            else:
                valores_por_ativo[cripto] = 0.0

        total_conta = saldo_caixa + patrimonio_cripto
        lucro_prejuizo = total_conta - capital_investido
        percentagem_lucro = (lucro_prejuizo / capital_investido) * 100 if capital_investido > 0 else 0.0

        historico_tempos.append(data_execucao)
        historico_totais.append(total_conta)

        if percentagem_lucro > max_lucro_atingido:
            max_lucro_atingido = percentagem_lucro

        # Gestão de Risco: Trailing Stop
        trailing_disparado = False
        if max_lucro_atingido >= 2.5 and percentagem_lucro <= (max_lucro_atingido - TRAILING_STOP_DISTANCIA):
            trailing_disparado = True

        icone_balanco = "🟢" if lucro_prejuizo >= 0 else "🔴"

        if trailing_disparado:
            saldo_caixa = total_conta
            for c in carteira:
                carteira[c] = 0.0
                valores_por_ativo[c] = 0.0
            patrimonio_cripto = 0.0
            ciclos_em_caixa = 0
            
            relatorio_emergencia = (
                f"🛑 *TRAFULHA: TRAILING STOP ACIONADO!* 🛑\n"
                f"📅 *Data:* `{data_completa}`\n\n"
                f"⚠️ *Lucros protegidos com sucesso!*\n"
                f"• *Pico Máximo:* `+{max_lucro_atingido:.2f}%`\n"
                f"• *Total Salvo em Caixa:* `${saldo_caixa:,.2f}`\n\n"
                f"🔄 *O robô irá reentrar automaticamente em breve.*"
            )
            enviar_telegram(relatorio_emergencia)
            max_lucro_atingido = 0.0
        else:
            relatorio = (
                f"🤖 *TRAFULHA QUANT TRADING: RELATÓRIO* 🤖\n"
                f"📅 *Data:* `{data_completa}`\n\n"
                f"🪙 *POSIÇÃO ATUAL:*\n"
                f"• *BTC:* `${valores_por_ativo['BTC']:,.2f}`\n"
                f"• *ETH:* `${valores_por_ativo['ETH']:,.2f}`\n"
                f"• *SOL:* `${valores_por_ativo['SOL']:,.2f}`\n"
                f"• *BNB:* `${valores_por_ativo['BNB']:,.2f}`\n"
                f"• *SUI:* `${valores_por_ativo['SUI']:,.2f}`\n\n"
                f"🏦 *BALANÇO GERAL:*\n"
                f"• *Caixa Livre:* `${saldo_caixa:,.2f}`\n"
                f"• *Património em Cripto:* `${patrimonio_cripto:,.2f}`\n"
                f"• *Total na Conta:* `${total_conta:,.2f}`\n"
                f"• *Balanço:* {icone_balanco} `${lucro_prejuizo:,.2f} ({percentagem_lucro:.2f}%)`\n"
                f"• *Pico Máximo:* `+{max_lucro_atingido:.2f}%`"
            )
            enviar_telegram(relatorio)

        print(f"✅ Ciclo executado às {data_execucao}. A aguardar próximo ciclo...")
        time.sleep(INTERVALO_SEGUNDOS)

except KeyboardInterrupt:
    print("\n🛑 Robô parado pelo utilizador.")