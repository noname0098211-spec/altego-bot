import random
import requests
import telebot
from telebot import types

TELEGRAM_TOKEN = "8992810594:AAHv1D0V6Ti8a4Esn-tQXj5LFQkzYe0rH0o"
GOOGLE_API_KEY = "AQ.Ab8RN6K2qIg6fv66pL4ehhJh4FPlS5N31gh1cBv4pfzyXDzekQ"

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


def get_mode_keyboard():
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(
          "📱 Тикток-Токсик 🔥", callback_data="mode_tiktok_toxic"
      ),
      types.InlineKeyboardButton(
          "🥊 Жесткий Тренер 💪", callback_data="mode_trainer"
      ),
      types.InlineKeyboardButton("🤓 Главный Душнила", callback_data="mode_dushnila"),
      types.InlineKeyboardButton(
          "🔮 Гадалка / Таро 🃏", callback_data="mode_fortune"
      ),
      types.InlineKeyboardButton("🕶 Братва из 90-х", callback_data="mode_bro90s"),
      types.InlineKeyboardButton(
          "🎙 Спортивный Диктор ⚽️", callback_data="mode_commentator"
      ),
      types.InlineKeyboardButton("🎭 Сарказм", callback_data="mode_sarcastic"),
      types.InlineKeyboardButton("🎮 Геймер Бро", callback_data="mode_gamer"),
  )
  return markup


def can_manage_bot(chat_id, user):
  if not user:
    return False
  if (
      user.username
      and user.username.lower() == SUPER_ADMIN_USERNAME.lower()
  ):
    return True
  if chat_id > 0:
    return False
  try:
    member = bot.get_chat_member(chat_id, user.id)
    return member.status in ["administrator", "creator"]
  except Exception:
    return False


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
      return f"Ошибка Google API: {result['error'].get('message', 'Неизвестная ошибка')}"

    if "candidates" in result and len(result["candidates"]) > 0:
      candidate = result["candidates"][0]
      if "content" in candidate and "parts" in candidate["content"]:
        return candidate["content"]["parts"][0]["text"]

    return f"Странный ответ от Google: {result}"
  except Exception as e:
    return f"Ошибка при обращении к Gemini: {e}"


@bot.message_handler(commands=["start", "mode"])
def send_welcome(message):
  if not can_manage_bot(message.chat.id, message.from_user):
    bot.reply_to(
        message, "⛔️ Настраивать бота могут только администраторы чата!"
    )
    return

  bot.send_message(
      message.chat.id,
      "Панель управления ботом. Выбери режим:",
      reply_markup=get_mode_keyboard(),
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("mode_"))
def callback_mode(call):
  chat_id = call.message.chat.id

  if not can_manage_bot(chat_id, call.from_user):
    bot.answer_callback_query(
        call.id,
        "⛔️ Менять режим могут только администраторы чата!",
        show_alert=True,
    )
    return

  mode_key = call.data.replace("mode_", "")
  user_modes[chat_id] = mode_key
  user_history[chat_id] = [{"role": "system", "content": PROMPTS[mode_key]}]

  mode_names = {
      "tiktok_toxic": "📱 Тикток-Токсик 🔥",
      "trainer": "🥊 Жесткий Тренер 💪",
      "dushnila": "🤓 Главный Душнила",
      "fortune": "🔮 Гадалка / Таро 🃏",
      "bro90s": "🕶 Братва из 90-х",
      "commentator": "🎙 Спортивный Диктор ⚽️",
      "sarcastic": "🎭 Сарказм",
      "gamer": "🎮 Геймер Бро",
  }

  bot.answer_callback_query(call.id, "Режим изменен!")
  bot.send_message(
      chat_id,
      f"Режим изменен на: *{mode_names[mode_key]}*!\nИстория очищена.",
      parse_mode="Markdown",
  )


@bot.message_handler(commands=["predict"])
def handle_predict(message):
  bot.send_chat_action(message.chat.id, "typing")
  user_tag = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )
  predict_prompt = [
      {"role": "system", "content": PROMPTS["fortune"]},
      {
          "role": "user",
          "content": (
              f"Сделай ОЧЕНЬ КОРОТКОЕ (максимум 2-3 предложения), кринжовое,"
              f" трешовое и жесткое предсказание для {user_tag}. Используй мат"
              " и чернуху!"
          ),
      },
  ]
  reply = get_ai_response(predict_prompt)
  bot.reply_to(message, reply)


@bot.message_handler(commands=["duel"])
def handle_duel(message):
  chat_id = message.chat.id
  bot.send_chat_action(chat_id, "typing")
  fighter1 = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )
  target = message.text.replace("/duel", "").strip()
  if not target and message.reply_to_message:
    target = (
        f"@{message.reply_to_message.from_user.username}"
        if message.reply_to_message.from_user.username
        else message.reply_to_message.from_user.first_name
    )
  if not target:
    target = "случайного соперника из чата"

  duel_prompt = [
      {"role": "system", "content": PROMPTS["commentator"]},
      {
          "role": "user",
          "content": (
              f"Прокомментируй жесткую дуэль и эпичную схватку между {fighter1}"
              f" и {target}! Опиши их битву, используй капс, спортивные крики и"
              " объяви победителя!"
          ),
      },
  ]
  reply = get_ai_response(duel_prompt)
  bot.reply_to(message, reply)


@bot.message_handler(commands=["roast"])
def handle_roast(message):
  chat_id = message.chat.id
  bot.send_chat_action(chat_id, "typing")
  mode = user_modes.get(chat_id, "tiktok_toxic")
  history_slice = user_history.get(chat_id, [])[-30:]
  chat_text = "\n".join([
      m["content"]
      for m in history_slice
      if isinstance(m["content"], str) and m["role"] == "user"
  ])

  target = message.text.replace("/roast", "").strip()
  if not target and message.reply_to_message:
    target = (
        f"@{message.reply_to_message.from_user.username}"
        if message.reply_to_message.from_user.username
        else message.reply_to_message.from_user.first_name
    )

  roast_prompt = [
      {"role": "system", "content": PROMPTS[mode]},
      {
          "role": "user",
          "content": (
              "Вот последние сообщения из чата:\n"
              f"{chat_text}\n\n"
              f"Прожарь жестко {target if target else 'весь этот чат'}, опираясь"
              " на их базар выше!"
          ),
      },
  ]
  reply = get_ai_response(roast_prompt)
  bot.reply_to(message, reply)


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

  if chat_id not in chat_usernames:
    chat_usernames[chat_id] = set()
  chat_usernames[chat_id].add(user_tag)

  if chat_id not in user_history or not user_history[chat_id]:
    mode = user_modes.get(chat_id, "tiktok_toxic")
    user_history[chat_id] = [{"role": "system", "content": PROMPTS[mode]}]

  user_history[chat_id].append(
      {"role": "user", "content": f"{user_tag}: {text}"}
  )
  if len(user_history[chat_id]) > 41:
    user_history[chat_id] = [user_history[chat_id][0]] + user_history[
        chat_id
    ][-40:]

  chat_counters[chat_id] = chat_counters.get(chat_id, 0) + 1

  if text.lower().startswith("altego какой шанс"):
    chance = random.randint(0, 100)
    users = list(chat_usernames[chat_id])
    random_user = random.choice(users) if users else user_tag
    phrases = [
        f"🎲 Шанс того, что {random_user} это сделает — ровно {chance}%!",
        f"📊 Мои расчеты показывают {chance}% для {random_user}. Живите с этим.",
        f"🔮 Карты говорят: {chance}% на успех {random_user}.",
        f"💥 Всего {chance}%. {random_user}, кринж полный, конечно.",
    ]
    bot.reply_to(message, random.choice(phrases))
    return

  if text.lower().startswith("altego кто сегодня"):
    users = list(chat_usernames[chat_id])
    chosen_user = random.choice(users) if users else user_tag
    action = text[18:].strip()
    phrases = [
        f"👉 Однозначно это {chosen_user}!",
        f"🏆 Победитель в категории '{action}' — {chosen_user}!",
        f"💀 Без вариантов, сегодня это {chosen_user}.",
        f"🎯 Стрелы угара указывают прямо на {chosen_user}!",
    ]
    bot.reply_to(message, random.choice(phrases))
    return

  is_private = message.chat.type == "private"
  bot_user = bot.get_me()
  is_reply_to_bot = (
      message.reply_to_message
      and message.reply_to_message.from_user.id == bot_user.id
  )
  is_mentioned = (
      bot_user.username and f"@{bot_user.username.lower()}" in text.lower()
  )

  should_auto_respond = False
  if chat_counters[chat_id] >= 100:
    chat_counters[chat_id] = 0
    should_auto_respond = True

  if is_private or is_reply_to_bot or is_mentioned or should_auto_respond:
    bot.send_chat_action(chat_id, "typing")
    ai_reply = get_ai_response(user_history[chat_id])
    user_history[chat_id].append({"role": "assistant", "content": ai_reply})
    bot.reply_to(message, ai_reply)


print("Бот запущен на Render!")
bot.polling(non_stop=True)
    
