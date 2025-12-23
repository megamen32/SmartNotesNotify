from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GeoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class NewNoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: str = Field(..., min_length=1, max_length=200)
    device: Optional[str] = Field(None, max_length=200)
    text: str = Field(..., min_length=1, max_length=20000)
    geo: Optional[GeoIn] = None
    pos_x: float = 0
    pos_y: float = 0


class NewNoteOut(BaseModel):
    ok: bool
    note_id: int
    url: str


class NotePatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    todo_list_id: Optional[int] = None
    tag: Optional[str] = None
    severity: Optional[Literal["low", "normal", "high"]] = None
    notify_by: Optional[Literal["time", "location"]] = None
    notify_value: Optional[dict[str, Any]] = None
    is_processed_by_llm: Optional[bool] = None
