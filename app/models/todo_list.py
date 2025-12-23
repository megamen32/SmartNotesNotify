from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TodoList(Base):
    __tablename__ = "todo_lists"
    __table_args__ = (
        Index("ix_todo_lists_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)

    pos_x: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    pos_y: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    width: Mapped[float] = mapped_column(Float, nullable=False, server_default="520")
    height: Mapped[float] = mapped_column(Float, nullable=False, server_default="360")

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
