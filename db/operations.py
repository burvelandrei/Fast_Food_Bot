import logging
import logging.config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User
from utils.logger import logging_config


logging.config.dictConfig(logging_config)
logger = logging.getLogger("db_operations")


class UserDO:
    """Класс c операциями для модели User"""

    model = User

    @classmethod
    async def get_by_email(cls, email: str, session: AsyncSession):
        """Получить элементы user по email"""
        try:
            logger.info("Fetching User by email")
            query = select(cls.model).where(cls.model.email == email)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching User by email: {e}",
            )
            raise e

    @classmethod
    async def get_by_tg_id(cls, tg_id: str, session: AsyncSession):
        """Получить элементы user по tg_id"""
        try:
            logger.info("Fetching User by Telegram ID")
            query = select(cls.model).where(cls.model.tg_id == tg_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"An error occurred while fetching User by Telegram ID: {e}",
            )
            raise e

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
