# bot.py
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, AiohttpWebhookRunner
from aiohttp import web
import os

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_PORT = int(os.getenv("PORT", 10000))
APP_HOST = "0.0.0.0"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://cameripvk-bot.onrender.com

# === Инициализация бота ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Обработчики ===
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я работаю на Render!")

@dp.message(F.text)
async def echo(message: Message):
    # Пример: пересылка сообщений в группу
    await bot.send_message(-1003033000994, f"Сообщение от {message.from_user.first_name}: {message.text}")

# === Запуск вебхука ===
async def main():
    # Устанавливаем вебхук
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")

    # Создаём веб-приложение
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    runner = AiohttpWebhookRunner(app)
    await runner.setup()
    await web._run_app(app, host=APP_HOST, port=APP_PORT)

if __name__ == "__main__":
    asyncio.run(main())
