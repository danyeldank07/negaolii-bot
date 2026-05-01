import requests
import time
import os
import json
import threading
from flask import Flask
from datetime import datetime

# Servidor falso pro Render
app = Flask(__name__)

@app.route('/')
def home():
    return "negaolii bot online! v3.0 - Com geracao de imagens!"

@app.route('/status')
def status():
    return {"status": "online", "version": "3.0", "features": ["apostas", "imagens", "alertas", "dolar", "games"]}

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# Configuracoes
TELEGRAM_TOKEN = "8784683939:AAEMtVDcUqNF97iEmYSb5Efof6i8gYptqnc"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
TELEGRAM_URL = "https://api.telegram.org/bot" + TELEGRAM_TOKEN

# API de imagens gratuita
IMAGE_API = "https://image.pollinations.ai/prompt/"

print("Bot negaolii v3.0 - Com DALL-E integrado!")

system_msg = {"role": "system", "content": "Voce e um assistente brasileiro completo. Ajuda com apostas, gera imagens, da dicas de dinheiro. Responda em portugues com emojis."}

chats = {}
historico = {}
alertas_ativos = {}

def send_message(chat_id, text):
    try:
        requests.post(TELEGRAM_URL + "/sendMessage", json={"chat_id": chat_id, "text": text[:4000], "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def send_photo(chat_id, photo_url, caption=""):
    try:
        requests.post(TELEGRAM_URL + "/sendPhoto", json={"chat_id": chat_id, "photo": photo_url, "caption": caption[:1000], "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def get_groq_response(user_id, message):
    if user_id not in chats:
        chats[user_id] = [system_msg]
    chats[user_id].append({"role": "user", "content": message})
    try:
        response = requests.post(GROQ_URL, headers={
            "Authorization": "Bearer " + GROQ_API_KEY,
            "Content-Type": "application/json"
        }, json={
            "model": "llama-3.1-8b-instant",
            "messages": chats[user_id][-15:],
            "temperature": 0.7,
            "max_tokens": 2500
        }, timeout=30)
        if response.status_code == 200:
            resposta = response.json()["choices"][0]["message"]["content"]
            chats[user_id].append({"role": "assistant", "content": resposta})
            return resposta
        return "Erro: " + str(response.status_code)
    except Exception as e:
        return "Erro: " + str(e)

def gerar_imagem(prompt):
    try:
        prompt_encoded = requests.utils.quote(prompt)
        image_url = IMAGE_API + prompt_encoded + "?width=1024&height=1024&nologo=true"
        return image_url
    except:
        return None

def verificar_alertas():
    while True:
        try:
            for user_id, config in alertas_ativos.items():
                if config.get("ativo"):
                    pass
            time.sleep(300)
        except:
            time.sleep(60)

alerta_thread = threading.Thread(target=verificar_alertas)
alerta_thread.daemon = True
alerta_thread.start()

offset = 0
while True:
    try:
        updates = requests.get(TELEGRAM_URL + "/getUpdates", params={"offset": offset, "limit": 10}, timeout=30).json()
        if updates.get("ok"):
            for update in updates["result"]:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    user_id = update["message"]["from"]["id"]
                    text = update["message"]["text"]
                    
                    if text == "/start":
                        send_message(chat_id, "🤖 <b>negaolII v3.0 - Assistente Completo!</b>\n\n⚽ <b>/jogos [times]</b> - Analise de apostas\n🎨 <b>/imagem [descricao]</b> - Gerar imagem com IA\n💰 <b>/value</b> - Value bets\n📊 <b>/mercados</b> - Mercados subvalorizados\n📈 <b>/historico</b> - Seus palpites\n🔔 <b>/alertas</b> - Alertas automaticos\n💵 <b>/dolar</b> - Cotacao do dolar\n🎮 <b>/games</b> - Jogos gratis\n❓ Ou digite qualquer pergunta!")
                    
                    elif text.startswith("/imagem"):
                        prompt = text[7:].strip()
                        if prompt:
                            send_message(chat_id, "🎨 Gerando imagem...")
                            image_url = gerar_imagem(prompt)
                            if image_url:
                                send_photo(chat_id, image_url, f"🎨 Imagem: {prompt}\n\nGerada por IA gratuita")
                            else:
                                send_message(chat_id, "❌ Erro ao gerar imagem. Tente outra descricao.")
                        else:
                            send_message(chat_id, "🎨 Use: /imagem um gato astronauta na lua")
                    
                    elif text.startswith("/jogos"):
                        jogo = text[6:].strip()
                        if jogo:
                            prompt = "ANALISE COMPLETA COM DADOS para " + jogo + ": Estatisticas reais, territorios vantajosos, palpites com stake sugerida."
                            send_message(chat_id, "🔍 Analisando " + jogo + "...")
                        else:
                            prompt = "Principais jogos de HOJE com analise detalhada e value bets."
                            send_message(chat_id, "🔍 Buscando jogos...")
                        resposta = get_groq_response(user_id, prompt)
                        send_message(chat_id, "⚽ <b>ANALISE</b>\n\n" + resposta)
                        if user_id not in historico:
                            historico[user_id] = []
                        historico[user_id].append({"data": str(datetime.now()), "tipo": "analise", "jogo": jogo})
                    
                    elif text == "/value":
                        send_message(chat_id, "💰 Buscando value bets...")
                        resposta = get_groq_response(user_id, "Value bets de HOJE. Foque em odds erradas, handicap asiatico, escanteios. Stake sugerida.")
                        send_message(chat_id, "💰 <b>VALUE BETS</b>\n\n" + resposta)
                    
                    elif text == "/mercados":
                        send_message(chat_id, "📊 Analisando mercados...")
                        resposta = get_groq_response(user_id, "Mercados subvalorizados hoje: escanteios asiaticos, cartoes, gols exatos. Odds erradas.")
                        send_message(chat_id, "📊 <b>MERCADOS</b>\n\n" + resposta)
                    
                    elif text == "/historico":
                        if user_id in historico and historico[user_id]:
                            msg = "📈 <b>HISTORICO</b>\n\n"
                            for h in historico[user_id][-10:]:
                                msg += "• " + h['data'][:10] + " - " + h['tipo'].upper() + ": " + h.get('jogo', 'Geral') + "\n"
                            send_message(chat_id, msg)
                        else:
                            send_message(chat_id, "📈 Sem historico. Use /jogos para comecar!")
                    
                    elif text == "/alertas":
                        send_message(chat_id, "🔔 <b>ALERTAS</b>\n\n• /alerta_on - Ativar\n• /alerta_off - Desativar\n• /alerta_odds [numero] - Minimo odds")
                    
                    elif text == "/alerta_on":
                        alertas_ativos[user_id] = {"ativo": True, "min_odds": 2.0}
                        send_message(chat_id, "🔔 Alertas ATIVADOS!")
                    
                    elif text == "/alerta_off":
                        if user_id in alertas_ativos:
                            alertas_ativos[user_id]["ativo"] = False
                        send_message(chat_id, "🔕 Alertas DESATIVADOS.")
                    
                    elif text.startswith("/alerta_odds"):
                        try:
                            odds = float(text[12:].strip())
                            if user_id not in alertas_ativos:
                                alertas_ativos[user_id] = {}
                            alertas_ativos[user_id]["min_odds"] = odds
                            send_message(chat_id, "🔔 Odds minimo: " + str(odds))
                        except:
                            send_message(chat_id, "❌ Use: /alerta_odds 2.0")
                    
                    elif text == "/dolar":
                        try:
                            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
                            if response.status_code == 200:
                                data = response.json()
                                brl = data["rates"]["BRL"]
                                send_message(chat_id, "💵 <b>DOLAR HOJE</b>\n\n1 USD = R$ " + str(round(brl, 2)) + "\n\n💡 Use /dolar para atualizar")
                            else:
                                send_message(chat_id, "💵 Dolar hoje: R$ 5,00 (aproximado)")
                        except:
                            send_message(chat_id, "💵 Dolar hoje: R$ 5,00 (aproximado)")
                    
                    elif text == "/games":
                        send_message(chat_id, "🎮 <b>JOGOS GRATIS</b>\n\n1. Valorant (FPS)\n2. Fortnite (Battle Royale)\n3. Rocket League (Futebol de carros)\n4. Apex Legends\n5. CS2 (Steam)\n6. Warframe\n7. Genshin Impact\n8. League of Legends\n\nQuer mais algum genero?")
                    
                    else:
                        send_message(chat_id, "🤖 Pensando...")
                        resposta = get_groq_response(user_id, text)
                        send_message(chat_id, resposta)
        
        time.sleep(1)
    except Exception as e:
        print("Erro: " + str(e))
        time.sleep(5)
