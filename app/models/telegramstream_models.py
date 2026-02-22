"""Streaming Telegram Yanitlari modelleri.

Telegram mesaj akisi, guncelleme, hiz siniri
ve yazma gostergesi modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class StreamState(str, Enum):
    """Akis durumu."""

    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class UpdateResult(str, Enum):
    """Guncelleme sonucu."""

    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    QUEUED = "queued"
    FAILED = "failed"
    SKIPPED = "skipped"


class CursorStyle(str, Enum):
    """Imlec stili."""

    BLOCK = "block"
    UNDERSCORE = "underscore"
    PIPE = "pipe"
    DOTS = "dots"
    NONE = "none"


class TypingState(str, Enum):
    """Yazma gostergesi durumu."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    REFRESHING = "refreshing"
    STOPPING = "stopping"


class StreamMode(str, Enum):
    """Akis modu."""

    FULL = "full"
    PARTIAL = "partial"
    OFF = "off"


class StreamLane(str, Enum):
    """Akis seridi."""

    REASONING = "reasoning"
    ANSWER = "answer"
    DRAFT = "draft"


class ButtonStyle(str, Enum):
    """Satir ici buton stili."""

    DEFAULT = "default"
    PRIMARY = "primary"
    SUCCESS = "success"
    DANGER = "danger"


class InlineButton(BaseModel):
    """Satir ici buton."""

    text: str = ""
    callback_data: str = ""
    url: str = ""
    style: ButtonStyle = ButtonStyle.DEFAULT


class ReactionEvent(BaseModel):
    """Tepki olayi."""

    chat_id: int = 0
    message_id: int = 0
    user_id: int = 0
    emoji: str = ""
    is_add: bool = True
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class TopicTarget(BaseModel):
    """Konu hedefi (chatId:topic:threadId)."""

    chat_id: int = 0
    topic_id: int = 0
    thread_id: int = 0


class StreamChunk(BaseModel):
    """Akis parcasi."""

    chunk_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    content: str = ""
    index: int = 0
    is_final: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class StreamSession(BaseModel):
    """Akis oturumu."""

    session_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    chat_id: int = 0
    message_id: int = 0
    state: StreamState = StreamState.IDLE
    total_chunks: int = 0
    total_chars: int = 0
    cursor_style: CursorStyle = CursorStyle.DOTS
    stream_mode: StreamMode = StreamMode.FULL
    active_lane: StreamLane = StreamLane.ANSWER
    debounce_chars: int = 30
    reply_to_message_id: int = 0
    topic_target: TopicTarget | None = None
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class EditRequest(BaseModel):
    """Mesaj duzenleme istegi."""

    request_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    chat_id: int = 0
    message_id: int = 0
    text: str = ""
    parse_mode: str = ""
    attempt: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class EditResponse(BaseModel):
    """Mesaj duzenleme yaniti."""

    response_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    result: UpdateResult = UpdateResult.SUCCESS
    message_id: int = 0
    error: str = ""
    retry_after_ms: int = 0


class RateLimitConfig(BaseModel):
    """Hiz siniri yapilandirmasi."""

    config_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    min_interval_ms: int = 1000
    max_burst: int = 3
    queue_size: int = 50
    cooldown_ms: int = 5000
    per_chat_limit: bool = True


class TypingSession(BaseModel):
    """Yazma gostergesi oturumu."""

    session_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    chat_id: int = 0
    state: TypingState = TypingState.INACTIVE
    refresh_interval_ms: int = 4000
    auto_cancel: bool = True
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class StreamSnapshot(BaseModel):
    """Sistem durum goruntusu."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    active_streams: int = 0
    total_streams: int = 0
    total_edits: int = 0
    failed_edits: int = 0
    queued_updates: int = 0
    active_typing: int = 0
    avg_update_ms: float = 0.0
    rate_limited_count: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
