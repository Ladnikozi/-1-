import telebot
import datetime
import threading
import schedule
import time
import re
import os

TOKEN = '8159628798:AAFBIqmylFJBzHRiTC6j9yCoVvm466cYcvo'
bot = telebot.TeleBot(TOKEN)

REPORT_FILE = "report.txt"
CHAT_ID = 8159628798
CREATOR_ID = 6463792262
bot_enabled = True

@bot.message_handler(commands=['start', 'статус'])
def send_welcome(message):
    text = (
        "🤖 Привет! Я бот для отчётности и активности.\n"
        "📌 Команды:\n"
        "/пост — зафиксировать пост\n"
        "/идея — предложить идею\n"
        "/приглашение N — отметить приглашённых\n"
        "/итоги — общий отчёт\n"
        "/отчёт @username — посмотреть отчёт участника\n"
        "/топ — топ активных\n"
        "/архив — файл отчётов\n"
        "/сбросить — очистить (только админ)\n"
        "/debug /лог /заморозить — только создатель"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    for user in message.new_chat_members:
        name = user.first_name or "друг"
        bot.send_message(message.chat.id, f"👋 Добро пожаловать, {name}!\nНе забудь сдать отчёт через /пост или /идея.")

def save_entry(message, entry_type):
    username = message.from_user.username or message.from_user.first_name or "Неизвестный"
    time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    log_line = f"{time_str} — @{username}: {entry_type}\n"
    with open(REPORT_FILE, "a") as f:
        f.write(log_line)
    with open(f"report_{datetime.date.today()}.txt", "a") as f:
        f.write(log_line)

@bot.message_handler(commands=['пост'])
def post_entry(message):
    if bot_enabled:
        save_entry(message, "✅ Пост")
        bot.send_message(message.chat.id, "✅ Пост зафиксирован!")

@bot.message_handler(commands=['идея'])
def idea_entry(message):
    if bot_enabled:
        save_entry(message, "💡 Идея")
        bot.send_message(message.chat.id, "💡 Идея записана!")

@bot.message_handler(commands=['приглашение'])
def invite_entry(message):
    if not bot_enabled: return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.send_message(message.chat.id, "❗ Пример: /приглашение 2")
        return
    count = int(parts[1])
    save_entry(message, f"👥 Приглашено: {count}")
    bot.send_message(message.chat.id, f"👥 Принято! Вы пригласили {count} человек.")

@bot.message_handler(commands=['итоги'])
def send_report(message):
    if not os.path.exists(REPORT_FILE):
        bot.send_message(message.chat.id, "⚠️ Отчётов пока нет.")
        return
    with open(REPORT_FILE, "r") as f:
        text = f.read()
    if not text.strip():
        bot.send_message(message.chat.id, "📭 Пока что никто ничего не отправил.")
    else:
        bot.send_message(message.chat.id, f"📊 Итоги:\n\n{text}")

@bot.message_handler(commands=['сбросить'])
def reset_report(message):
    chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
    if chat_member.status not in ['administrator', 'creator']:
        bot.reply_to(message, "⛔ Только админ может это сделать.")
        return
    with open(REPORT_FILE, "w") as f:
        f.write("")
    bot.send_message(message.chat.id, "🗑 Отчёт очищен.")

@bot.message_handler(commands=['отчёт'])
def report_user(message):
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "❗ Пример: /отчёт @username")
        return
    username = parts[1].strip()
    with open(REPORT_FILE, "r") as f:
        lines = [line for line in f if username in line]
    if lines:
        bot.send_message(message.chat.id, f"📄 Отчёт {username}:\n\n{''.join(lines)}")
    else:
        bot.send_message(message.chat.id, f"🔍 Данных по {username} не найдено.")

@bot.message_handler(commands=['топ'])
def top_users(message):
    stats = {}
    with open(REPORT_FILE, "r") as f:
        for line in f:
            match = re.search(r"@[\w_]+", line)
            if match:
                user = match.group()
                stats[user] = stats.get(user, 0) + 1
    if stats:
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        text = "🏆 Топ активных:\n"
        for user, count in sorted_stats:
            text += f"{user}: {count}\n"
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "📉 Нет данных для топа.")

@bot.message_handler(commands=['архив'])
def send_archive(message):
    if not os.path.exists(REPORT_FILE):
        bot.send_message(message.chat.id, "📂 Архив не найден.")
        return
    with open(REPORT_FILE, "rb") as f:
        bot.send_document(message.chat.id, f)

@bot.message_handler(commands=['debug'])
def debug_command(message):
    if message.from_user.id != CREATOR_ID:
        bot.send_message(message.chat.id, "⛔ Только для создателя.")
        return
    bot.send_message(message.chat.id, f"🧪 Chat ID: {message.chat.id}")

@bot.message_handler(commands=['лог'])
def show_log(message):
    if message.from_user.id != CREATOR_ID:
        return
    if not os.path.exists(REPORT_FILE):
        bot.send_message(message.chat.id, "Лог пуст.")
        return
    with open(REPORT_FILE, "r") as f:
        lines = f.readlines()[-10:]
    text = ''.join(lines)
    bot.send_message(message.chat.id, f"📝 Последние записи:\n{text}")

@bot.message_handler(commands=['заморозить'])
def toggle_bot(message):
    global bot_enabled
    if message.from_user.id != CREATOR_ID:
        return
    bot_enabled = not bot_enabled
    status = "🧊 Бот заморожен." if not bot_enabled else "✅ Бот снова активен."
    bot.send_message(message.chat.id, status)

def evening_reminder():
    if not os.path.exists(REPORT_FILE): return
    with open(REPORT_FILE, "r") as f:
        if not f.read().strip():
            bot.send_message(CHAT_ID, "⏰ Напоминание: сегодня ещё никто не сдал отчёт!")

def weekly_report():
    if not os.path.exists(REPORT_FILE): return
    with open(REPORT_FILE, "r") as f:
        report = f.read()
    if report.strip():
        bot.send_message(CHAT_ID, f"📊 Еженедельный отчёт:\n\n{report}")
    else:
        bot.send_message(CHAT_ID, "📭 На этой неделе не было активности.")

def auto_cleanup():
    for file in os.listdir():
        if file.startswith("report_") and file.endswith(".txt"):
            date_str = file[7:-4]
            try:
                file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if (datetime.date.today() - file_date).days > 30:
                    os.remove(file)
            except:
                continue

def run_schedule():
    schedule.every().day.at("20:00").do(evening_reminder)
    schedule.every().sunday.at("21:00").do(weekly_report)
    schedule.every().day.at("03:00").do(auto_cleanup)
    while True:
        schedule.run_pending()
        time.sleep(10)

threading.Thread(target=run_schedule).start()
bot.polling()
