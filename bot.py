import requests
import time

TELEGRAM_TOKEN = "8784683939:AAEMtVDcUqNF97iEmYSb5Efof6i8gYptqnc"
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
TELEGRAM_URL = "https://api.telegram.org/bot" + TELEGRAM_TOKEN

print("Bot negaolii online!")

system_msg = {"role": "system", "content": "Voce e um especialista brasileiro em analise de apostas esportivas. Responda em portugues com emojis."}

chats = {}

def send_message(chat_id, text):
    requests.post(TELEGRAM_URL + "/sendMessage", json={"chat_id": chat_id, "text": text[:4000], "parse_mode": "HTML"})

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
            "messages": chats[user_id][-10:],
            "temperature": 0.7,
            "max_tokens": 2000
        }, timeout=30)
        if response.status_code == 200:
            resposta = response.json()["choices"][0]["message"]["content"]
            chats[user_id].append({"role": "assistant", "content": resposta})
            return resposta
        return "Erro: " + str(response.status_code)
    except Exception as e:
        return "Erro: " + str(e)

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
                        send_message(chat_id, "🤖 negaolII Bot\n\n⚽ /jogos [time1 vs time2]\n💰 /value - Value bets\n📊 /mercados - Mercados subvalorizados")
                    elif text.startswith("/jogos"):
                        jogo = text[6:].strip()
                        prompt = "ANALISE DE VALOR para " + jogo + ": odds erradas, handicap asiatico, escanteios." if jogo else "Jogos de hoje com valor."
                        send_message(chat_id, "🔍 Analisando...")
                        resposta = get_groq_response(user_id, prompt)
                        send_message(chat_id, "🔍 ANALISE:\n\n" + resposta)
                    elif text == "/value":
                        send_message(chat_id, "💰 Buscando...")
                        resposta = get_groq_response(user_id, "Value bets de hoje.")
                        send_message(chat_id, "💰 VALUE BETS:\n\n" + resposta)
                    elif text == "/mercados":
                        send_message(chat_id, "📊 Analisando...")
                        resposta = get_groq_response(user_id, "Mercados subvalorizados hoje.")
                        send_message(chat_id, "📊 MERCADOS:\n\n" + resposta)
                    else:
                        send_message(chat_id, "🤖 Pensando...")
                        resposta = get_groq_response(user_id, text)
                        send_message(chat_id, resposta)
        time.sleep(1)
    except Exception as e:
        print("Erro: " + str(e))
        time.sleep(5)
