from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note


class NoteRepo:
    async def get(self, db: AsyncSession, note_id: int) -> Note | None:
        q = await db.execute(select(Note).where(Note.id == note_id))
        return q.scalar_one_or_none()

    async def create(self, db: AsyncSession, note: Note) -> Note:
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    async def create_from_snapshot(self, db: AsyncSession, data: dict) -> Note:
        note = Note(
            id=data.get("id"),
            user_id=data["user_id"],
            device=data.get("device"),
            text=data.get("text") or "",
            geo=data.get("geo"),
            todo_list_id=data.get("todo_list_id"),
            pos_x=data.get("pos_x", 0),
            pos_y=data.get("pos_y", 0),
            is_processed_by_llm=bool(data.get("is_processed_by_llm", False)),
            notify_by=data.get("notify_by"),
            notify_value=data.get("notify_value"),
            severity=data.get("severity") or "normal",
            tag=data.get("tag"),
            meta=data.get("meta") or {},
        )
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
            if k in {"todo_list_id", "tag", "notify_by", "notify_value", "device", "geo", "meta"}:
                setattr(obj, k, v)
            elif v is not None:
                setattr(obj, k, v)
        await db.commit()

    async def delete(self, db: AsyncSession, note_id: int) -> None:
        q = await db.execute(select(Note).where(Note.id == note_id))
        obj = q.scalar_one_or_none()
        if not obj:
            return
        await db.delete(obj)
        await db.commit()
