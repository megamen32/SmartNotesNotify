from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.action_log import ActionLog


class ActionLogRepo:
    async def clear_redo_for_user(self, db: AsyncSession, user_id: int) -> None:
        await db.execute(
            delete(ActionLog)
            .where(ActionLog.user_id == user_id)
            .where(ActionLog.undone_at.isnot(None))
        )
        await db.commit()

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        action_type: str,
        entity_type: str,
        entity_id: int | None,
        before: dict | None,
        after: dict | None,
    ) -> ActionLog:
        action = ActionLog(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action

    async def get_last_undoable(self, db: AsyncSession, user_id: int) -> ActionLog | None:
        q = await db.execute(
            select(ActionLog)
            .where(ActionLog.user_id == user_id)
            .where(ActionLog.undone_at.is_(None))
            .order_by(ActionLog.id.desc())
            .limit(1)
        )
        return q.scalar_one_or_none()

    async def get_last_redoable(self, db: AsyncSession, user_id: int) -> ActionLog | None:
        q = await db.execute(
            select(ActionLog)
            .where(ActionLog.user_id == user_id)
            .where(ActionLog.undone_at.isnot(None))
            .order_by(ActionLog.undone_at.desc())
            .limit(1)
        )
        return q.scalar_one_or_none()

    async def mark_undone(self, db: AsyncSession, action_id: int) -> None:
        await db.execute(
            update(ActionLog)
            .where(ActionLog.id == action_id)
            .values(undone_at=func.now())
        )
        await db.commit()

    async def mark_redone(self, db: AsyncSession, action_id: int) -> None:
        await db.execute(
            update(ActionLog)
            .where(ActionLog.id == action_id)
            .values(undone_at=None)
        )
        await db.commit()
