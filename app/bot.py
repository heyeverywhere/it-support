import asyncio
import logging
import sys

from app.database import init_db
from app.database.session import engine
from app.handlers.user import router as user_router
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.config import settings
from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router
from app.keyboards.user import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        "Здравствуйте!\n\n"
        "Это бот технической поддержки учреждения.\n"
        "Выберите нужное действие в меню ниже.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("cancel"))
async def command_cancel_handler(message: Message) -> None:
    await message.answer(
        "Текущая операция отменена."
    )


@router.message()
async def unknown_message_handler(message: Message) -> None:
    await message.answer(
        "Используйте команду /start для начала работы."
    )


async def main() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if not settings.bot_token:
        logging.error(
            "BOT_TOKEN не указан. Заполните значение в файле .env."
        )
        return

    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(user_router)
    dispatcher.include_router(admin_router)
    dispatcher.include_router(router)


    try:
        logging.info("Бот запускается...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await engine.dispose()
        logging.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Работа остановлена пользователем.")
        sys.exit(0)