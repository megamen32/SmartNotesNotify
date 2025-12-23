from dataclasses import dataclass
from typing import Optional


@dataclass
class LlmResult:
    todo_list_title: Optional[str] = None
    severity: str = "normal"
    tag: Optional[str] = None
    notify_by: Optional[str] = None
    notify_value: Optional[dict] = None


class LlmService:
    async def analyze(self, text: str) -> LlmResult:
        return LlmResult(todo_list_title=None)
