"""Streaming Token Output modelleri.

LLM'den token gelirken canli akitma,
buffer yonetimi ve olay modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class StreamState(str, Enum):
    """Akim durumu."""

    IDLE = "idle"
    CONNECTING = "connecting"
    STREAMING = "streaming"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class StreamEventType(str, Enum):
    """Akim olay tipi."""

    TOKEN = "token"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    FLUSH = "flush"
    START = "start"
    END = "end"
    ERROR = "error"
    METADATA = "metadata"
    TOOL_CALL = "tool_call"
    HEARTBEAT = "heartbeat"
    PAUSE = "pause"
    RESUME = "resume"


class FlushReason(str, Enum):
    """Temizleme nedeni."""

    BUFFER_FULL = "buffer_full"
    WORD_BOUNDARY = "word_boundary"
    SENTENCE_BOUNDARY = "sentence_boundary"
    INTERVAL = "interval"
    FORCED = "forced"
    COMPLETION = "completion"


class StreamErrorType(str, Enum):
    """Akim hata tipi."""

    CONNECTION = "connection"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    SERVER = "server"
    PARSE = "parse"
    INCOMPLETE = "incomplete"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ProviderFormat(str, Enum):
    """Saglayici akim formati."""

    SSE = "sse"
    WEBSOCKET = "websocket"
    NDJSON = "ndjson"
    RAW = "raw"


class StreamToken(BaseModel):
    """Tek token/parca."""

    token_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    content: str = ""
    index: int = 0
    is_first: bool = False
    is_last: bool = False
    latency_ms: float = 0.0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class StreamEvent(BaseModel):
    """Akim olayi."""

    event_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    event_type: StreamEventType = StreamEventType.TOKEN
    data: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    stream_id: str = ""
    sequence: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class BufferState(BaseModel):
    """Buffer durumu."""

    content: str = ""
    token_count: int = 0
    byte_size: int = 0
    flush_count: int = 0
    last_flush_reason: str = ""
    pending_tokens: int = 0


class StreamError(BaseModel):
    """Akim hatasi."""

    error_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    error_type: StreamErrorType = StreamErrorType.UNKNOWN
    message: str = ""
    retryable: bool = False
    retry_after_ms: int = 0
    partial_content: str = ""
    provider: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class StreamMetrics(BaseModel):
    """Akim metrikleri."""

    stream_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    total_tokens: int = 0
    total_bytes: int = 0
    duration_ms: float = 0.0
    first_token_ms: float = 0.0
    tokens_per_second: float = 0.0
    flush_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    provider: str = ""
    model: str = ""


class StreamConfig(BaseModel):
    """Akim yapilandirmasi."""

    buffer_size: int = 64
    flush_interval_ms: int = 50
    show_typing: bool = True
    max_retries: int = 3
    retry_delay_ms: int = 1000
    timeout_ms: int = 30000
    heartbeat_interval_ms: int = 15000
    backpressure_threshold: int = 100


class StreamingSnapshot(BaseModel):
    """Streaming sistem durumu."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    active_streams: int = 0
    total_streams: int = 0
    total_tokens: int = 0
    total_bytes: int = 0
    total_errors: int = 0
    avg_first_token_ms: float = 0.0
    avg_tokens_per_second: float = 0.0
    subscribers: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
