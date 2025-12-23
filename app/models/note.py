from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

SeverityEnum = Enum("low", "normal", "high", name="severity_enum")
NotifyByEnum = Enum("time", "location", name="notify_by_enum")


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_user_created", "user_id", "created_at"),
        Index("ix_notes_user_list", "user_id", "todo_list_id"),
        Index(
            "ix_notes_geo_gin",
            "geo",
            postgresql_using="gin",
            postgresql_ops={"geo": "jsonb_path_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    device: Mapped[str | None] = mapped_column(Text, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    geo: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    todo_list_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("todo_lists.id", ondelete="SET NULL"), nullable=True)

    pos_x: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")
    pos_y: Mapped[float] = mapped_column(Float, nullable=False, server_default="0")

    is_processed_by_llm: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    notify_by: Mapped[str | None] = mapped_column(NotifyByEnum, nullable=True)
    notify_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    severity: Mapped[str] = mapped_column(SeverityEnum, nullable=False, server_default="normal")
    tag: Mapped[str | None] = mapped_column(Text, nullable=True)

    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
