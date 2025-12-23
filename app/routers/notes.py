from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.note import NewNoteIn, NewNoteOut, NotePatchIn
from app.services.board_service import BoardService

router = APIRouter()
svc = BoardService()

@router.post("/new_note", response_model=NewNoteOut)
async def new_note(payload: NewNoteIn, request: Request, db: AsyncSession = Depends(get_session)):
    note = await svc.create_note(
        db=db,
        user_key=payload.user,
        device=payload.device,
        text=payload.text,
        geo=(payload.geo.model_dump() if payload.geo else None),
        pos_x=payload.pos_x,
        pos_y=payload.pos_y,
    )
    url = str(request.url_for("board_page", user=payload.user)) + f"?focus_note_id={note.id}"
    return NewNoteOut(ok=True, note_id=note.id, url=url)

@router.patch("/api/notes/{note_id}")
async def patch_note(note_id: int, payload: NotePatchIn, db: AsyncSession = Depends(get_session)):
    await svc.notes.patch(db, note_id, **payload.model_dump())
    return {"ok": True}

@router.post("/api/users/{user}/process_notes_by_llm")
async def process_notes(user: str, db: AsyncSession = Depends(get_session)):
    processed = await svc.process_notes_by_llm(db, user)
    return {"ok": True, "processed": processed}


@router.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_session)):
    await svc.delete_note(db, note_id)
    return {"ok": True}
