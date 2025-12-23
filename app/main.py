from fastapi import FastAPI

from app.db import ensure_triggers, engine
from app.models.base import Base
from app.routers.board import router as board_router
from app.routers.notes import router as notes_router

app = FastAPI(title="Notes Board")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await ensure_triggers(conn)

app.include_router(notes_router)
app.include_router(board_router)

if __name__=='__main__':
    import uvicorn
    uvicorn.run('app.main:app',port=9432,host='0.0.0.0',reload=True)