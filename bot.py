import telebot
from telebot import types

BOT_TOKEN = "8767133042:AAGzicAUQxYnEF0FEEdEsF2PiG2mU-EXN_E"
MINI_APP_URL = "https://mybot-gkck.onrender.com"
CHANNEL = "@Dev_HamsterClicker"

bot = telebot.TeleBot(BOT_TOKEN)

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/Dev_HamsterClicker"))
        markup.add(types.InlineKeyboardButton("✅ Я подписался!", callback_data="check_sub"))
        bot.send_message(
            message.chat.id,
            "❌ *Для игры нужно подписаться на наш канал!*\n\n👇 Подпишись и нажми кнопку ниже",
            parse_mode="Markdown",
            reply_markup=markup
        )
        return
    send_game(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Отлично! Добро пожаловать!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_game(call.message.chat.id)
    else:
        bot.answer_callback_query(call.id, "❌ Ты ещё не подписался!", show_alert=True)

def send_game(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🐹 Играть в Hamster Clicker!",
        web_app=types.WebAppInfo(url=MINI_APP_URL)
    ))
    bot.send_message(
        chat_id,
        "🐹 *Добро пожаловать в Hamster Clicker!*\n\nНажми кнопку ниже чтобы начать играть 👇",
        parse_mode="Markdown",
        reply_markup=markup
    )

if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.infinity_polling()
