# bot.py
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# === Настройки ===
BOT_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"
WEB_APP_URL = "https://cameri-github-io.onrender.com"  # Ваш сайт

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
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Бот запущен. Ожидаем команду /start...")
    app.run_polling()
