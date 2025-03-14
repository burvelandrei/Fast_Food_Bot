from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram_dialog import DialogManager, StartMode
from sqlalchemy.ext.asyncio import AsyncSession
from dialogs.states import StartSG, MenuSG
from db.operations import UserDO

router = Router()


# Хэндлер на /start, если пользователь есть отправляем в меню
@router.message(CommandStart())
async def start_handler(
    message: Message, dialog_manager: DialogManager, session: AsyncSession
):
    db_user = await UserDO.get_by_tg_id(
        tg_id=str(message.from_user.id), session=session
    )
    if db_user:
        await dialog_manager.start(state=MenuSG.menu, mode=StartMode.RESET_STACK)
    else:
        await dialog_manager.start(state=StartSG.input_email, mode=StartMode.RESET_STACK)


# Хэндлер на /menu для вызова меню навигации
@router.message(Command(commands="menu"))
async def menu_handler(
    message: Message, dialog_manager: DialogManager, session: AsyncSession
):
    db_user = await UserDO.get_by_tg_id(
        tg_id=str(message.from_user.id), session=session
    )
    if db_user:
        await dialog_manager.start(state=MenuSG.menu, mode=StartMode.RESET_STACK)
    else:
        await message.answer(
            "Вы не прошли этап регистрации! Введите команду /start для регистрации."
        )


# Хэндлер на /menu для вызова меню навигации
@router.message(Command(commands="help"))
async def help_handler(
    message: Message, dialog_manager: DialogManager, session: AsyncSession
):
    await message.answer("Техническая поддержка - @burvelandrei .")
