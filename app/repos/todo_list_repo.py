from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo_list import TodoList


class TodoListRepo:
    async def list_by_user(self, db: AsyncSession, user_id: int) -> list[TodoList]:
        q = await db.execute(select(TodoList).where(TodoList.user_id == user_id))
        return list(q.scalars().all())

    async def create_defaults_if_empty(self, db: AsyncSession, user_id: int) -> None:
        existing = await self.list_by_user(db, user_id)
        if existing:
            return
        titles = ["Рутуб", "Автопродажник", "Покупки"]
        frames = [
            TodoList(user_id=user_id, title=titles[0], pos_x=200, pos_y=120),
            TodoList(user_id=user_id, title=titles[1], pos_x=800, pos_y=120),
            TodoList(user_id=user_id, title=titles[2], pos_x=200, pos_y=560),
        ]
        db.add_all(frames)
        await db.commit()

    async def patch(self, db: AsyncSession, list_id: int, **fields) -> None:
        q = await db.execute(select(TodoList).where(TodoList.id == list_id))
        obj = q.scalar_one()
        for k, v in fields.items():
            if v is not None:
                setattr(obj, k, v)
        await db.commit()
