from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepo:
    async def get_by_key(self, db: AsyncSession, user_key: str) -> User | None:
        q = await db.execute(select(User).where(User.user_key == user_key))
        return q.scalar_one_or_none()

    async def get_or_create(self, db: AsyncSession, user_key: str) -> User:
        q = await db.execute(select(User).where(User.user_key == user_key))
        user = q.scalar_one_or_none()
        if user:
            return user
        user = User(user_key=user_key)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
