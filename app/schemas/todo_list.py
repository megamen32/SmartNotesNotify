from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TodoListOut(BaseModel):
    id: int
    title: str
    pos_x: float
    pos_y: float
    width: float
    height: float


class TodoListPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    title: Optional[str] = Field(None, max_length=200)
