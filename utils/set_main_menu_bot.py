from aiogram import Bot
from aiogram.types import BotCommand
from config import settings


# Функция для настройки кнопки Menu бота
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command=command, description=description)
        for command, description in settings.MAIN_MENU_BOT.items()
    ]
    await bot.set_my_commands(main_menu_commands)
