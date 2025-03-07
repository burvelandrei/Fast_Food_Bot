import logging
import logging.config
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User
from services.logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("db_operations")


class UserDO:
    """Класс c операциями для модели User"""

    model = User

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int):
        """Получить элементы по id или вернуть None если нет"""
        logger.info(f"Fetching {cls.model.__name__} with id {id}")
        query = select(cls.model).where(cls.model.id == id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_tg_id(cls, tg_id: str, session: AsyncSession):
        """Получить элементы user по tg_id"""
        logger.info(f"Fetching User by Telegram ID")
        query = select(cls.model).where(cls.model.tg_id == tg_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def add(cls, session: AsyncSession, **values):
        """Добавить объект в БД"""
        new_instance = cls.model(**values)
        session.add(new_instance)
        try:
            await session.commit()
            logger.info(f"Added new {cls.model.__name__}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding {cls.model.__name__}: {e}")
            raise e
        return new_instance
