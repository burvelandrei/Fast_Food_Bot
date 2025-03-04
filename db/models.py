from typing import List
from datetime import datetime
from decimal import Decimal
from sqlalchemy import ForeignKey, DECIMAL
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[str] = mapped_column(unique=True, nullable=True)

    def __repr__(self):
        return str(self.id)
