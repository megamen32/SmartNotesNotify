from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note


class NoteRepo:
    async def create(self, db: AsyncSession, note: Note) -> Note:
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    async def list_by_user(self, db: AsyncSession, user_id: int) -> list[Note]:
        q = await db.execute(
            select(Note)
            .where(Note.user_id == user_id)
            .order_by(Note.created_at.desc())
            .limit(2000)
        )
        return list(q.scalars().all())

    async def patch(self, db: AsyncSession, note_id: int, **fields) -> None:
        q = await db.execute(select(Note).where(Note.id == note_id))
        obj = q.scalar_one()
        for k, v in fields.items():
            if k in {"todo_list_id", "tag", "notify_by", "notify_value"}:
                setattr(obj, k, v)
            elif v is not None:
                setattr(obj, k, v)
        await db.commit()
