from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
import os
import logging

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка настроек из окружения
BOT_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"
WEB_APP_URL = "https://cameri-github-io.onrender.com"
PORT = int(os.getenv("PORT", 8080))

# Функция-обработчик команды /start
async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Открыть камеру", callback_data="open_camera")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# Основная точка входа
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Начало прослушивания на выбранном порту
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/" + BOT_TOKEN,
        webhook_url=WEBHOOK_URL + "/" + BOT_TOKEN,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
