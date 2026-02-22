"""Reply threading modelleri."""

from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class ThreadContext(BaseModel):
    thread_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    channel: str = ""
    reply_to_id: str = ""
    original_message_id: str = ""
    is_sticky: bool = True
    chunk_ids: list[str] = Field(default_factory=list)
    created_at: float = 0.0
    last_used_at: float = 0.0
    stale_threshold_seconds: int = 300
