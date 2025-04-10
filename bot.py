import asyncio
import logging
import logging.config
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram_dialog import setup_dialogs
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from utils.logger import logging_config
from utils.set_main_menu_bot import set_main_menu
from handlers import user_handler
from dialogs import (
    history_orders_dialog,
    current_orders_dialog,
    start_dialog,
    menu_dialog,
    products_dialog,
    carts_dialog,
    profile_dialog,
    сheckout_order_dialog,
)
from db.connect import AsyncSessionLocal
from utils.middlewares import DBSessionMiddleware
from utils.rmq_consumer import listen_for_confirmations
from config import settings


logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main() -> None:
    logging.config.dictConfig(logging_config)
    logger.info("Starting BOTV")

    # Инициализируем бот, редис и диспетчер
    bot: Bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    storage = RedisStorage.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp: Dispatcher = Dispatcher(storage=storage)

    # Настраиваем кнопку Menu бота
    await set_main_menu(bot)

    # Добавляем миддлварь для сессий к БД
    dp.update.middleware(DBSessionMiddleware(AsyncSessionLocal))

    # Регистриуем роутеры в диспетчере
    dp.include_router(user_handler.router)
    dp.include_router(start_dialog.dialog)
    dp.include_router(menu_dialog.dialog)
    dp.include_router(profile_dialog.dialog)
    dp.include_router(products_dialog.dialog)
    dp.include_router(carts_dialog.dialog)
    dp.include_router(current_orders_dialog.dialog)
    dp.include_router(history_orders_dialog.dialog)
    dp.include_router(сheckout_order_dialog.dialog)
    dialog_bg_factory = setup_dialogs(dp)

    asyncio.create_task(
        listen_for_confirmations(
            bot=bot,
            session=AsyncSessionLocal(),
            dialog_bg_factory=dialog_bg_factory,
        )
    )
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
