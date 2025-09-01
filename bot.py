# bot.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# === Настройки ===
API_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"  # ← Твой токен
GROUP_ID = -1003033000994  # ← ID твоей группы
WEB_APP_URL = "https://test-webapp.onrender.com"  # ← Ссылка на твой Static Site

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === /start — отправляем кнопку ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Получен /start от {user.full_name}")

    # Кнопка с WebApp
    keyboard = [[{"text": "🔧 Открыть тестовую страницу", "web_app": {"url": WEB_APP_URL}}]]
    reply_markup = {"inline_keyboard": keyboard}

    await update.message.reply_text(
        "👋 Привет! Нажми кнопку ниже, чтобы протестировать WebApp.",
        reply_markup=reply_markup
    )


# === Обработка web_app_data ===
async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.effective_message.web_app_data.data
        logger.info(f"📩 Получены данные: {data}")

        # Отправляем ОТВЕТ В ТОТ ЖЕ ЧАТ (в бот)
        await update.message.reply_text(f"✅ Получено: {data}")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


# === Запуск бота ===
def main():
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))

    logger.info("🚀 Бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()
