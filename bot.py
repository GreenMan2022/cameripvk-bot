from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import asyncio
import time

# === Настройки ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro")
WEB_APP_URL = os.environ.get("WEB_APP_URL", "https://cameri-github-io.onrender.com")
PORT = int(os.environ.get("PORT", 10000))  # Render автоматически назначает порт

# Переменная для хранения chat_id администратора (можно заменить)
ADMIN_CHAT_ID = None

# === Обработчик /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_CHAT_ID
    if not ADMIN_CHAT_ID:
        ADMIN_CHAT_ID = update.effective_chat.id
    await update.message.reply_text(
        "🎥 Добро пожаловать! Нажмите кнопку ниже, чтобы открыть камеры:",
        reply_markup={
            "inline_keyboard": [
                [{
                    "text": "📷 Открыть камеры",
                    "web_app": {"url": WEB_APP_URL}
                }]
            ]
        }
    )

# === Периодически отправляем сообщение администратору ===
async def keep_alive():
    while True:
        try:
            await asyncio.sleep(120)  # Ждем 2 минуты
            await app.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Ping!")
        except Exception as e:
            print(f"Ошибка ping: {e}")

# === Запуск ===
if __name__ == "__main__":
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Бот запущен. Ожидаем команду /start...")
    
    # Создаем цикл обновления каждые 2 минуты
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())
    
    # Запускаем бота в режиме polling
    loop.create_task(app.run_polling())
