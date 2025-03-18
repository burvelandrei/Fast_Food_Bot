from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return str(self.id)
