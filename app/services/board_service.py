from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.repos.note_repo import NoteRepo
from app.repos.todo_list_repo import TodoListRepo
from app.repos.user_repo import UserRepo
from app.services.llm_service import LlmService


class BoardService:
    def __init__(self) -> None:
        self.users = UserRepo()
        self.lists = TodoListRepo()
        self.notes = NoteRepo()
        self.llm = LlmService()

    async def ensure_user_and_defaults(self, db: AsyncSession, user_key: str):
        user = await self.users.get_or_create(db, user_key)
        await self.lists.create_defaults_if_empty(db, user.id)
        return user

    async def create_note(
        self,
        db: AsyncSession,
        user_key: str,
        device: str | None,
        text: str,
        geo: dict | None,
        pos_x: float | None = None,
        pos_y: float | None = None,
    ) -> Note:
        user = await self.ensure_user_and_defaults(db, user_key)
        final_pos_x = pos_x if pos_x is not None else 0
        final_pos_y = pos_y if pos_y is not None else 0
        note = Note(
            user_id=user.id,
            device=device,
            text=text.strip(),
            geo=geo,
            pos_x=final_pos_x,
            pos_y=final_pos_y,
        )
        return await self.notes.create(db, note)

    async def get_board(self, db: AsyncSession, user_key: str):
        user = await self.ensure_user_and_defaults(db, user_key)
        lists = await self.lists.list_by_user(db, user.id)
        notes = await self.notes.list_by_user(db, user.id)
        return user, lists, notes

    async def process_notes_by_llm(self, db: AsyncSession, user_key: str) -> int:
        user = await self.ensure_user_and_defaults(db, user_key)
        notes = await self.notes.list_by_user(db, user.id)

        count = 0
        lists = await self.lists.list_by_user(db, user.id)
        title_to_id = {x.title.lower(): x.id for x in lists}

        for n in notes:
            if n.is_processed_by_llm:
                continue
            res = await self.llm.analyze(n.text)

            todo_list_id = None
            if res.todo_list_title:
                todo_list_id = title_to_id.get(res.todo_list_title.lower())

            await self.notes.patch(
                db,
                n.id,
                todo_list_id=todo_list_id,
                severity=res.severity,
                tag=res.tag,
                notify_by=res.notify_by,
                notify_value=res.notify_value,
                is_processed_by_llm=True,
            )
            count += 1
        return count

    async def delete_note(self, db: AsyncSession, note_id: int) -> None:
        await self.notes.delete(db, note_id)
