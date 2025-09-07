# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web
import os

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://cameripvk-bot.onrender.com
PORT = int(os.getenv("PORT", 10000))
HOST = "0.0.0.0"

# === Инициализация бота и диспетчера ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Обработчики ===
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я работаю на Render!")

@dp.message()
async def echo(message: Message):
    # Пример: пересылка в группу
    await bot.send_message(-1003033000994, f"📩 {message.text}")

# === Веб-сервер ===
async def handle_update(request):
    update = await request.json()
    await dp.feed_update(bot, update=update)
    return web.Response()

async def on_startup(app):
    await bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    print(f"Бот запущен. Вебхук установлен на {WEBHOOK_URL}/webhook")

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    print("Бот остановлен")

# Создаём веб-приложение
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.router.add_post("/webhook", handle_update)

# === Запуск ===
if __name__ == "__main__":
    web.run_app(app, host=HOST, port=PORT)
