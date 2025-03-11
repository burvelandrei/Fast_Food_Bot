import aio_pika
import json
from aiogram import Bot
from aiogram.types import Chat, User
from aiogram.types import Message
from aiogram_dialog import BgManagerFactory
from sqlalchemy.ext.asyncio import AsyncSession
from environs import Env
from db.operations import UserDO
from dialogs.states import MenuSG

env = Env()
env.read_env()


# Функция для прочтения очереди rabbitmq на предмет подтверждённых почт
async def listen_for_confirmations(bot: Bot, session:AsyncSession, dialog_bg_factory: BgManagerFactory):
    connection = await aio_pika.connect_robust(
        f"amqp://{env('RMQ_USER')}:{env('RMQ_PASSWORD')}@localhost/"
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
                    await UserDO.add(session=session, **{"tg_id": tg_id, "email": email})
                    await bot.send_message(tg_id, f"✅ Ваша почта {email} успешно подтверждена!")
                    bg_manager = dialog_bg_factory.bg(bot=bot, user_id=tg_id, chat_id=tg_id)
                    await bg_manager.start(state=MenuSG.menu)
