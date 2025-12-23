import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/notes_db",
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

SET_UPDATED_AT_FUNCTION = """
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;
"""

CREATE_LIST_TRIGGER = """
DO $$ BEGIN
  CREATE TRIGGER trg_lists_updated_at
  BEFORE UPDATE ON todo_lists
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
EXCEPTION WHEN DUPLICATE_OBJECT THEN NULL; END $$;
"""

CREATE_NOTE_TRIGGER = """
DO $$ BEGIN
  CREATE TRIGGER trg_notes_updated_at
  BEFORE UPDATE ON notes
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
EXCEPTION WHEN DUPLICATE_OBJECT THEN NULL; END $$;
"""

async def ensure_triggers(connection) -> None:
    await connection.execute(text(SET_UPDATED_AT_FUNCTION))
    await connection.execute(text(CREATE_LIST_TRIGGER))
    await connection.execute(text(CREATE_NOTE_TRIGGER))
