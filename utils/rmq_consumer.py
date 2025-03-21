import aio_pika
import json
import logging
import logging.config
from aiogram import Bot
from aiogram_dialog import BgManagerFactory
from sqlalchemy.ext.asyncio import AsyncSession
from db.operations import UserDO
from dialogs.states import MenuSG
from config import settings
from utils.logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("rabbit_producer")


async def listen_for_confirmations(
    bot: Bot, session: AsyncSession, dialog_bg_factory: BgManagerFactory
):
    """
    Функция для прочтения очереди rabbitmq на предмет подтверждённых почт
    """
    try:
        logger.info("Connecting to RabbitMQ...")
        connection = await aio_pika.connect_robust(
            f"amqp://{settings.RMQ_USER}:{settings.RMQ_PASSWORD}@"
            f"{settings.RMQ_HOST}:{settings.RMQ_PORT}/"
        )
        channel = await connection.channel()
        queue = await channel.declare_queue("user_confirmations")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    event_data = json.loads(message.body)
                    tg_id = event_data.get("tg_id")
                    email = event_data.get("email")

                    if tg_id:
                        await UserDO.add(
                            session=session,
                            **{"tg_id": tg_id, "email": email}
                        )
                        await bot.send_message(
                            tg_id,
                            f"✅ Ваша почта {email} успешно подтверждена!",
                        )
                        bg_manager = dialog_bg_factory.bg(
                            bot=bot, user_id=tg_id, chat_id=tg_id
                        )
                        await bg_manager.start(state=MenuSG.menu)
    except Exception as e:
        logger.error(
            f"Failed to connect or listen to RabbitMQ: {e}",
            exc_info=True,
        )
