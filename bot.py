# bot.py
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# === Настройки ===
API_TOKEN = "8191852280:AAFcOI5tVlJlk4xxnzxAgIUBmW4DW5KElro"
GROUP_ID = -1003033000994
WEB_APP_URL = "https://cameri-github-io.onrender.com"

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Создаём бота ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === /start ===
@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    logger.info(f"Получен /start от {user.full_name}")

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="🎥 Открыть камеры",
        web_app=WebAppInfo(url=WEB_APP_URL)
    ))

    # ✅ Правильно: .answer()
    await message.answer("👋 Добро пожаловать!", reply_markup=builder.as_markup())

# === Обработка web_app_data ===
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = message.web_app_data.data
        logger.info(f"📩 Получены данные: {data}")

        import json
        data = json.loads(data)
        event_type = data.get("type", "неизвестно")
        camera = data.get("camera", "неизвестна")
        timestamp = data.get("timestamp", "неизвестно")
        user = message.from_user

        text = (
            f"🚨 <b>Событие:</b> {event_type}\n"
            f"📹 <b>Камера:</b> {camera}\n"
            f"👤 <b>Пользователь:</b> {user.full_name}\n"
            f"🆔 <b>ID:</b> {user.id}\n"
            f"🕒 <b>Время:</b> {timestamp}"
        )

        await bot.send_message(chat_id=GROUP_ID, text=text, parse_mode="HTML")
        await message.answer("✅ Отправлено в группу!")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await message.answer(f"❌ Ошибка: {e}")

# === Запуск ===
async def main():
    logger.info("🚀 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
