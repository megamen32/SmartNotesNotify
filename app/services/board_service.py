from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.repos.note_repo import NoteRepo
from app.repos.action_log_repo import ActionLogRepo
from app.repos.todo_list_repo import TodoListRepo
from app.repos.user_repo import UserRepo
from app.services.llm_service import LlmService


class BoardService:
    def __init__(self) -> None:
        self.users = UserRepo()
        self.lists = TodoListRepo()
        self.notes = NoteRepo()
        self.actions = ActionLogRepo()
        self.llm = LlmService()

    @staticmethod
    def _note_snapshot(note: Note) -> dict:
        return {
            "id": note.id,
            "user_id": note.user_id,
            "device": note.device,
            "text": note.text,
            "geo": note.geo,
            "todo_list_id": note.todo_list_id,
            "pos_x": note.pos_x,
            "pos_y": note.pos_y,
            "is_processed_by_llm": note.is_processed_by_llm,
            "notify_by": note.notify_by,
            "notify_value": note.notify_value,
            "severity": note.severity,
            "tag": note.tag,
            "meta": note.meta,
        }

    @staticmethod
    def _note_patch_fields(snapshot: dict) -> dict:
        return {
            "device": snapshot.get("device"),
            "text": snapshot.get("text"),
            "geo": snapshot.get("geo"),
            "todo_list_id": snapshot.get("todo_list_id"),
            "pos_x": snapshot.get("pos_x"),
            "pos_y": snapshot.get("pos_y"),
            "is_processed_by_llm": snapshot.get("is_processed_by_llm"),
            "notify_by": snapshot.get("notify_by"),
            "notify_value": snapshot.get("notify_value"),
            "severity": snapshot.get("severity"),
            "tag": snapshot.get("tag"),
            "meta": snapshot.get("meta"),
        }

    @staticmethod
    def _list_snapshot(todo_list) -> dict:
        return {
            "id": todo_list.id,
            "user_id": todo_list.user_id,
            "title": todo_list.title,
            "pos_x": todo_list.pos_x,
            "pos_y": todo_list.pos_y,
            "width": todo_list.width,
            "height": todo_list.height,
        }

    @staticmethod
    def _list_patch_fields(snapshot: dict) -> dict:
        return {
            "title": snapshot.get("title"),
            "pos_x": snapshot.get("pos_x"),
            "pos_y": snapshot.get("pos_y"),
            "width": snapshot.get("width"),
            "height": snapshot.get("height"),
        }

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
        note = await self.notes.create(db, note)
        await self.actions.clear_redo_for_user(db, user.id)
        await self.actions.create(
            db,
            user_id=user.id,
            action_type="create",
            entity_type="note",
            entity_id=note.id,
            before=None,
            after=self._note_snapshot(note),
        )
        return note

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

            await self.patch_note(
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

    async def patch_note(self, db: AsyncSession, note_id: int, **fields) -> None:
        note = await self.notes.get(db, note_id)
        if not note:
            return
        before = self._note_snapshot(note)
        await self.notes.patch(db, note_id, **fields)
        updated = await self.notes.get(db, note_id)
        if not updated:
            return
        await self.actions.clear_redo_for_user(db, note.user_id)
        await self.actions.create(
            db,
            user_id=note.user_id,
            action_type="update",
            entity_type="note",
            entity_id=note_id,
            before=before,
            after=self._note_snapshot(updated),
        )

    async def delete_note(self, db: AsyncSession, note_id: int) -> None:
        note = await self.notes.get(db, note_id)
        if not note:
            return
        before = self._note_snapshot(note)
        await self.notes.delete(db, note_id)
        await self.actions.clear_redo_for_user(db, note.user_id)
        await self.actions.create(
            db,
            user_id=note.user_id,
            action_type="delete",
            entity_type="note",
            entity_id=note_id,
            before=before,
            after=None,
        )

    async def patch_todo_list(self, db: AsyncSession, list_id: int, **fields) -> None:
        todo_list = await self.lists.get(db, list_id)
        if not todo_list:
            return
        before = self._list_snapshot(todo_list)
        await self.lists.patch(db, list_id, **fields)
        updated = await self.lists.get(db, list_id)
        if not updated:
            return
        await self.actions.clear_redo_for_user(db, todo_list.user_id)
        await self.actions.create(
            db,
            user_id=todo_list.user_id,
            action_type="update",
            entity_type="todo_list",
            entity_id=list_id,
            before=before,
            after=self._list_snapshot(updated),
        )

    async def undo_last_action(self, db: AsyncSession, user_key: str) -> bool:
        user = await self.users.get_by_key(db, user_key)
        if not user:
            return False
        action = await self.actions.get_last_undoable(db, user.id)
        if not action:
            return False
        await self._apply_action(db, action, reverse=True)
        await self.actions.mark_undone(db, action.id)
        return True

    async def redo_last_action(self, db: AsyncSession, user_key: str) -> bool:
        user = await self.users.get_by_key(db, user_key)
        if not user:
            return False
        action = await self.actions.get_last_redoable(db, user.id)
        if not action:
            return False
        await self._apply_action(db, action, reverse=False)
        await self.actions.mark_redone(db, action.id)
        return True

    async def _apply_action(self, db: AsyncSession, action, reverse: bool) -> None:
        payload = action.before if reverse else action.after
        if action.entity_type == "note":
            await self._apply_note_action(db, action.action_type, action.entity_id, payload, reverse)
        elif action.entity_type == "todo_list":
            await self._apply_list_action(db, action.action_type, action.entity_id, payload, reverse)

    async def _apply_note_action(self, db: AsyncSession, action_type: str, entity_id: int | None, payload: dict | None, reverse: bool) -> None:
        if action_type == "create":
            if reverse:
                if entity_id is not None:
                    await self.notes.delete(db, entity_id)
            else:
                if payload:
                    existing = await self.notes.get(db, payload["id"])
                    if existing:
                        await self.notes.patch(db, payload["id"], **self._note_patch_fields(payload))
                    else:
                        await self.notes.create_from_snapshot(db, payload)
            return
        if action_type == "delete":
            if reverse:
                if payload:
                    existing = await self.notes.get(db, payload["id"])
                    if existing:
                        await self.notes.patch(db, payload["id"], **self._note_patch_fields(payload))
                    else:
                        await self.notes.create_from_snapshot(db, payload)
            else:
                if entity_id is not None:
                    await self.notes.delete(db, entity_id)
            return
        if action_type == "update":
            if payload and entity_id is not None:
                await self.notes.patch(db, entity_id, **self._note_patch_fields(payload))

    async def _apply_list_action(self, db: AsyncSession, action_type: str, entity_id: int | None, payload: dict | None, reverse: bool) -> None:
        if action_type == "update":
            if payload and entity_id is not None:
                await self.lists.patch(db, entity_id, **self._list_patch_fields(payload))
            return
        if action_type == "create":
            if reverse:
                if entity_id is not None:
                    # delete list action not currently exposed
                    await self.lists.patch(db, entity_id, title=payload.get("title") if payload else None)
            else:
                if payload:
                    existing = await self.lists.get(db, payload["id"])
                    if existing:
                        await self.lists.patch(db, payload["id"], **self._list_patch_fields(payload))
                    else:
                        await self.lists.create_from_snapshot(db, payload)
            return
        if action_type == "delete":
            if reverse and payload:
                existing = await self.lists.get(db, payload["id"])
                if existing:
                    await self.lists.patch(db, payload["id"], **self._list_patch_fields(payload))
                else:
                    await self.lists.create_from_snapshot(db, payload)
            elif not reverse and entity_id is not None:
                # delete list action not currently exposed
                await self.lists.patch(db, entity_id, title=payload.get("title") if payload else None)
