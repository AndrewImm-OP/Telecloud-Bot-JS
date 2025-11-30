import asyncio
import logging
import sys
import os
from datetime import datetime

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer 
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards import *
from translations import translations_messages as tm
from tortoise import Tortoise, run_async

from handlers import user_router
from db import User

load_dotenv()
TOKEN = os.getenv("TOKEN") or ""
LOCAL_TAPI = bool(os.getenv("LOCAL_TAPI", False).lower() == 'true')
LOCAL_TAPI_URL = os.getenv("LOCAL_TAPI_URL", "http://localhost:8000")

if TOKEN == "":
    logging.error("No TOKEN found in environment variables.")
    sys.exit(1)

dp = Dispatcher()

TORTOISE_ORM = {
    "connections": {"default": "sqlite://database.sqlite3"},
    "apps": {
        "models": {
            "models": ["db"], # Список модулей, где лежат модели (например, ["models", "handlers.other_models"])
            "default_connection": "default",
        }
    },
}

async def init_db():
    await Tortoise.init(
        config=TORTOISE_ORM
    )
    await Tortoise.generate_schemas()
    logging.info("Database initialized and schemas generated.")

@dp.message(CommandStart())
async def send_welcome(message: Message):
    language = message.from_user.language_code
    if await User.filter(telegram_id=message.from_user.id).exists() is False:
        await User.create(telegram_id=message.from_user.id, created_at=datetime.utcnow(), user_token=None)
    logging.info(f"User {message.from_user.id} started the bot with language {language}")
    markup = get_welcome_keyboard(language)
    await message.answer(tm["start_message"].get(language, "en"), reply_markup=markup)

async def on_startup():
    logging.info(f"Bot has started.")

async def on_shutdown():
    logging.info("Bot is shutting down.")
    await Tortoise.close_connections()

async def main() -> None:
    await init_db()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    if LOCAL_TAPI:
        logging.info(f"Using local TAPI at {LOCAL_TAPI_URL}")
        session = AiohttpSession(api=TelegramAPIServer.from_base(LOCAL_TAPI_URL, is_local=True))
        bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)

    dp.include_router(user_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    asyncio.run(main())