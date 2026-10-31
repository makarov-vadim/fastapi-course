from datetime import datetime

from sqlalchemy import text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationships, relationship

from .database import BaseORMModel


class UserORMModel(BaseORMModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    phone_number: Mapped[None | str] = mapped_column(unique=True)

    hashed_password: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),      # значение на стороне базы данных
        nullable=False,
    )

class PostORMModel(BaseORMModel):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(
        default=True,                    # значение на стороне Python
        server_default=text("true"),     # значение на стороне базы данных
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),      # значение на стороне базы данных
        nullable=False,
    )

    user: Mapped[UserORMModel] = relationship(lazy="selectin")


class VoteORMModel(BaseORMModel):
    __tablename__ = "votes"

    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),      # значение на стороне базы данных
        nullable=False,
    )

    user: Mapped[UserORMModel] = relationship(lazy="selectin")
    post: Mapped[PostORMModel] = relationship(lazy="selectin")
