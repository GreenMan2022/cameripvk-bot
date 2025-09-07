# bot.py
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from aiohttp import web
import os

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://cameripvk-bot.onrender.com
PORT = int(os.getenv("PORT", 10000))
HOST = "0.0.0.0"

# === Обработчики команд ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я работаю на Render!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Пример: пересылка в группу
    await context.bot.send_message(
        chat_id=-1003033000994,
        text=f"📩 {update.message.text}"
    )

# === Настройка веб-приложения ===
async def setup_application():
    app = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(None, echo))

    return app

# === Веб-сервер ===
async def handle_update(request):
    application = request.app["bot_app"]
    await application.update_queue.put(
        Update.de_json(data=await request.json(), bot=application.bot)
    )
    return web.Response()

async def on_startup(app):
    await app["bot_app"].initialize()
    await app["bot_app"].start()
    await app["bot_app"].bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    print(f"Бот запущен. Вебхук установлен на {WEBHOOK_URL}/webhook")

async def on_shutdown(app):
    await app["bot_app"].bot.delete_webhook()
    await app["bot_app"].stop()
    await app["bot_app"].shutdown()
    print("Бот остановлен")

# === Запуск ===
if __name__ == "__main__":
    # Создаём веб-приложение
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Инициализируем бота
    from asyncio import get_event_loop
    bot_app = get_event_loop().run_until_complete(setup_application())
    app["bot_app"] = bot_app

    # Добавляем маршрут
    app.router.add_post("/webhook", handle_update)

    # Запускаем
    web.run_app(app, host=HOST, port=PORT)
