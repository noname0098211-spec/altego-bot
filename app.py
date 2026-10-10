import os
import random
import requests
import telebot
from telebot import types
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TELEGRAM_TOKEN = "8992810594:AAG4XcGdUWyw5ILDaT_tnx1d-bHIvf-21Xk"
GOOGLE_API_KEY = "AQ.Ab8RN6KX6SzNLgxMURRq_gLOl-fIpgkXv_dQhonVqD4IJTBhVg"

SUPER_ADMIN_USERNAME = "kloyxx"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

PROMPTS = {
    "tiktok_toxic": (
        "Ты живой чел из интернета (TikTok/Reels). Тебе дико впадлу отвечать,"
        " ты считаешь вопросы пользователя кринжем. Отвечай дерзко, свысока и"
        " без цензуры. Активно и уместно используй мат, сленг (кринж, рофл,"
        " душно, пон, чел, поплачь, ахах), подкалывай и стебись."
    ),
    "trainer": (
        "Ты жесткий, агрессивный фитнес-тренер и мотиватор. Орёшь на всех за"
        " любую слабость, заставляешь работать над собой. Используй капс и"
        " спортивные метафоры!"
    ),
    "dushnila": (
        "Ты невероятный душнила, зануда и перфекционист. Поправляй"
        " грамматические ошибки, душни сложными терминами и докапывайся до"
        " мелочей."
    ),
    "fortune": (
        "Ты загадочная, отбитая цыганка-эзотерик. Пишешь с матом, диким"
        " кринжем и черным юмором. Гадаешь на картах, видишь грязь в ауре,"
        " просишь позолотить ручку. ОТВЕЧАЙ ОЧЕНЬ КРАТКО (2-3 предложения)!"
    ),
    "bro90s": (
        "Ты бандит из 90-х. Общайся по понятиям, используй дворовый сленг"
        " (братуха, стрелка, рамс, перетереть)."
    ),
    "commentator": (
        "Ты безумный и гиперактивный Спортивный Диктор и комментатор. Описывай"
        " происходящее в чате так, будто это финал Лиги Чемпионов! Используй"
        " КАПС и спортивные термины ('Какой удар!', 'Фол в атаке!', 'Красная"
        " карточка!')."
    ),
    "sarcastic": (
        "Ты грубый, крайне саркастичный и ироничный собеседник. Подкалывай,"
        " язви, но помни историю чата."
    ),
    "gamer": (
        "Ты свойский парень-геймер из 2000-х. Используй игровой сленг (бро,"
        " катка, задефать, гайд, изи)."
    ),
}

user_modes = {}
user_history = {}
chat_counters = {}
chat_usernames = {}


def get_ai_response(messages_history):
  url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
  contents = []
  system_instruction = None

  for msg in messages_history:
    if msg["role"] == "system":
      system_instruction = {"parts": [{"text": msg["content"]}]}
    elif msg["role"] == "user":
      contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
    elif msg["role"] == "assistant":
      contents.append({"role": "model", "parts": [{"text": msg["content"]}]})

  payload = {"contents": contents}
  if system_instruction:
    payload["system_instruction"] = system_instruction

  headers = {
      "Content-Type": "application/json",
      "x-goog-api-key": GOOGLE_API_KEY,
  }

  try:
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    if "error" in result:
      err_msg = result['error'].get('message', 'Неизвестная ошибка')
      return f"⚠️ Ошибка Google API: {err_msg}. (Убедитесь, что используется ключ из Google AI Studio, начинающийся с AIzaSy...)"

    if "candidates" in result and len(result["candidates"]) > 0:
      candidate = result["candidates"][0]
      if "content" in candidate and "parts" in candidate["content"]:
        return candidate["content"]["parts"][0]["text"]

    return f"Странный ответ от Google: {result}"
  except Exception as e:
    return f"Ошибка при обращении к Gemini: {e}"


@bot.message_handler(commands=["start", "mode"])
def send_welcome(message):
  bot.send_message(
      message.chat.id,
      "Панель управления ботом. Бот на связи!",
  )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
  if not message.text:
    return
  chat_id = message.chat.id
  text = message.text

  user_tag = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )

  if chat_id not in user_history or not user_history[chat_id]:
    user_history[chat_id] = [{"role": "system", "content": PROMPTS["tiktok_toxic"]}]

  user_history[chat_id].append(
      {"role": "user", "content": f"{user_tag}: {text}"}
  )

  bot.send_chat_action(chat_id, "typing")
  ai_reply = get_ai_response(user_history[chat_id])
  user_history[chat_id].append({"role": "assistant", "content": ai_reply})
  bot.reply_to(message, ai_reply)


# Поднимаем веб-сервер для Render, чтобы не было ошибок порта
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

print("Бот запущен на Render!")
bot.polling(non_stop=True)
