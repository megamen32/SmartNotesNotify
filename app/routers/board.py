from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.todo_list import TodoListPatchIn
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
                "device": n.device,
                "notify_time": (
                    n.notify_value.get("at") if isinstance(n.notify_value, dict) and n.notify_by == "time" and n.notify_value.get("at")
                    else None
                ),
                "is_done": n.is_done,
            }
            for n in notes
        ],
    }

@router.get("/board/{user}", response_class=HTMLResponse, name="board_page")
async def board_page(user: str, request: Request):
    response = templates.TemplateResponse("board.html", {"request": request, "user": user})
    response.set_cookie(
        key="smartnotes_user",
        value=user,
        max_age=60 * 60 * 24 * 30,
        path="/",
        httponly=True,
        samesite="lax",
    )
    return response

@router.get("/list/{user}", response_class=HTMLResponse, name="list_page")
async def list_page(user: str, request: Request):
    response = templates.TemplateResponse("list.html", {"request": request, "user": user})
    response.set_cookie(
        key="smartnotes_user",
        value=user,
        max_age=60 * 60 * 24 * 30,
        path="/",
        httponly=True,
        samesite="lax",
    )
    return response

@router.patch("/api/todo_lists/{list_id}")
async def patch_todo_list(list_id: int, payload: TodoListPatchIn, db: AsyncSession = Depends(get_session)):
    await svc.patch_todo_list(db, list_id, **payload.model_dump())
    return {"ok": True}

@router.post("/api/users/{user}/undo")
async def undo_last_action(user: str, db: AsyncSession = Depends(get_session)):
    ok = await svc.undo_last_action(db, user)
    return {"ok": ok}

@router.post("/api/users/{user}/redo")
async def redo_last_action(user: str, db: AsyncSession = Depends(get_session)):
    ok = await svc.redo_last_action(db, user)
    return {"ok": ok}

@router.get("/", response_class=HTMLResponse)
async def root_page(request: Request):
    cached_user = request.cookies.get("smartnotes_user")
    if cached_user:
        return RedirectResponse(url=f"/board/{cached_user}")
    return templates.TemplateResponse("root.html", {"request": request})
