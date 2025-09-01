# bot.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# === Настройки ===
API_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"
GROUP_ID = -1003033000994
WEB_APP_URL = "https://cameri-github-io.onrender.com/"  # ← Твоя GitHub Pages

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Получен /start от {user.full_name}")

    keyboard = [[{"text": "🎥 Открыть камеры", "web_app": {"url": WEB_APP_URL}}]]
    reply_markup = {"inline_keyboard": keyboard}

    await update.message.reply_text(
        "👋 Добро пожаловать!\nНажмите кнопку ниже.",
        reply_markup=reply_markup
    )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.effective_message.web_app_data.data
        logger.info(f"📩 Получены данные: {data}")

        import json
        data = json.loads(data)
        event_type = data.get("type", "неизвестно")
        camera = data.get("camera", "неизвестна")
        timestamp = data.get("timestamp", "неизвестно")
        user = update.effective_user

        text = (
            f"🚨 <b>Событие:</b> {event_type}\n"
            f"📹 <b>Камера:</b> {camera}\n"
            f"👤 <b>Пользователь:</b> {user.full_name}\n"
            f"🆔 <b>ID:</b> {user.id}\n"
            f"🕒 <b>Время:</b> {timestamp}"
        )

        await context.bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
        await update.message.reply_text("✅ Отправлено в группу!")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


def main():
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    logger.info("🚀 Бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()
