# bot.py
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

# === Настройки ===
API_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"
WEB_APP_URL = "https://cameri-github-io.onrender.com"  # Замените на свой URL

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Создаём бота ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === /start — кнопка ===
@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    logger.info(f"Получен /start от {user.full_name}")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="🎥 Открыть камеры",
        web_app={"url": WEB_APP_URL}
    ))

    await message.answer("👋 Добро пожаловать!", reply_markup=builder.as_markup())

# === Запуск ===
async def main():
    logger.info("🚀 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
