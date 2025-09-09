from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Настройки ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro")
WEB_APP_URL = os.environ.get("WEB_APP_URL", "https://cameri-github-io.onrender.com")  # Обязательно полный URL с HTTPS
PORT = int(os.environ.get("PORT", 10000))  # Портируемый порт

# === Обработчик /start ===
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 Добро пожаловать! Нажмите кнопку ниже, чтобы открыть камеры:",
        reply_markup={
            "inline_keyboard": [
                [{
                    "text": "📷 Открыть камеры",
                    "web_app": {"url": f"{WEB_APP_URL}"}
                }]
            ]
        }
    )

# === Основная функция ===
def main():
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчик команды /start
    app.add_handler(CommandHandler("start", start_command))

    # Начинаем прослушивание на порту
    app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN,
                   webhook_url=f"{WEB_APP_URL}/{BOT_TOKEN}",
                   allowed_updates=["message"],
                   drop_pending_updates=True)

if __name__ == "__main__":
    main()
