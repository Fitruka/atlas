"""Session yonetimi modelleri."""

from enum import Enum
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class SessionState(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class SessionLockState(str, Enum):
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    WATCHDOG_EXPIRED = "watchdog_expired"


class SessionEntry(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4())[:12])
    state: SessionState = SessionState.ACTIVE
    lock_state: SessionLockState = SessionLockState.UNLOCKED
    lock_holder: str = ""
    lock_expires_at: float = 0.0
    transcript_path: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    archived_at: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AtomicWriteResult(BaseModel):
    success: bool = False
    path: str = ""
    bytes_written: int = 0
    is_atomic: bool = False
    error: str = ""
