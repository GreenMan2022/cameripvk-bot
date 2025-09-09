from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import asyncio

# === Настройки ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro")
WEB_APP_URL = os.environ.get("WEB_APP_URL", "https://cameri-github-io.onrender.com")
PORT = int(os.environ.get("PORT", 10000))  # Render автоматически назначает порт

# === Обработчик /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# === Запуск ===
if __name__ == "__main__":
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Бот запущен. Ожидаем команду /start...")
    
    # Запускаем бота в режиме polling
    # Это создаст фоновую задачу, которая не блокирует основной поток
    loop = asyncio.get_event_loop()
    loop.create_task(app.run_polling())
