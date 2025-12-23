from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# import models so SQLAlchemy registers them on Base.metadata
from app.models.base import Base  # noqa: E402
import app.models.action_log  # noqa: F401,E402
import app.models.note  # noqa: F401,E402
import app.models.todo_list  # noqa: F401,E402
import app.models.user  # noqa: F401,E402

target_metadata = Base.metadata

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/notes_db"
)

def _get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

section = config.get_section(config.config_ini_section, {})
if not section.get("sqlalchemy.url"):
    section["sqlalchemy.url"] = _get_database_url()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
