from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import DialogManager, StartMode
from sqlalchemy.ext.asyncio import AsyncSession
from states import StartState, MenuState
from db.operations import UserDO

router = Router()


# Хэндлер на /start, если пользователь есть отправляем в меню
@router.message(CommandStart())
async def start(message: Message, dialog_manager: DialogManager, session: AsyncSession):
    db_user = await UserDO.get_by_tg_id(tg_id=str(message.from_user.id), session=session)
    if db_user:
        await dialog_manager.start(state=MenuState.menu, mode=StartMode.RESET_STACK)
    else:
        await dialog_manager.start(state=StartState.start, mode=StartMode.RESET_STACK)
