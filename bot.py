import asyncio
import logging
import logging.config
from environs import Env
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram_dialog import setup_dialogs
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from utils.logger import logging_config
from handlers import start_handler
from dialogs import (
    start_dialog,
    menu_dialog,
    products_dialog,
    orders_dialog,
    carts_dialog,
)
from db.connect import AsyncSessionLocal
from utils.middlewares import DBSessionMiddleware


env = Env()
env.read_env()


logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main() -> None:
    logging.config.dictConfig(logging_config)
    logger.info("Starting BOTV")

    # Инициализируем бот, редис и диспетчер
    bot: Bot = Bot(
        token=env("BOT_TOKEN"), default=DefaultBotProperties(parse_mode="HTML")
    )
    storage = RedisStorage.from_url(
        f'redis://{env("REDIS_HOST")}:{env("REDIS_PORT")}/0',
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp: Dispatcher = Dispatcher(storage=storage)
    dp.update.middleware(DBSessionMiddleware(AsyncSessionLocal))

    # Регистриуем роутеры в диспетчере
    dp.include_router(start_handler.router)
    dp.include_router(start_dialog.dialog)
    dp.include_router(menu_dialog.dialog)
    dp.include_router(products_dialog.dialog)
    dp.include_router(carts_dialog.dialog)
    dp.include_router(orders_dialog.dialog)
    setup_dialogs(dp)

    # Пропускаем накопившиеся апдейты и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"[Exception] - {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
