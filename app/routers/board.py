from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services.board_service import BoardService

router = APIRouter()
svc = BoardService()
templates = Jinja2Templates(directory="templates")

@router.get("/api/board/{user}")
async def board_json(user: str, db: AsyncSession = Depends(get_session)):
    _, lists, notes = await svc.get_board(db, user)
    return {
        "user": user,
        "lists": [
            {
                "id": x.id,
                "title": x.title,
                "pos_x": x.pos_x,
                "pos_y": x.pos_y,
                "width": x.width,
                "height": x.height,
            }
            for x in lists
        ],
        "notes": [
            {
                "id": n.id,
                "text": n.text,
                "pos_x": n.pos_x,
                "pos_y": n.pos_y,
                "todo_list_id": n.todo_list_id,
                "severity": n.severity,
                "tag": n.tag,
                "is_processed_by_llm": n.is_processed_by_llm,
                "notify_time": (
                    n.notify_value.get("at") if isinstance(n.notify_value, dict) and n.notify_by == "time" and n.notify_value.get("at")
                    else None
                ),
            }
            for n in notes
        ],
    }

@router.get("/board/{user}", response_class=HTMLResponse, name="board_page")
async def board_page(user: str, request: Request):
    return templates.TemplateResponse("board.html", {"request": request, "user": user})

@router.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    return templates.TemplateResponse("root.html", {"request": request})
