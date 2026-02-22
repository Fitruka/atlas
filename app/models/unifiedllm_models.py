"""Unified LLM Client veri modelleri."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """LLM saglayici."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    XAI = "xai"
    VOLCANO = "volcano"
    BYTEPLUS = "byteplus"
    CLOUDFLARE = "cloudflare"
    MOONSHOT = "moonshot"
    VLLM = "vllm"


class MessageRole(str, Enum):
    """Mesaj rolu."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class FinishReason(str, Enum):
    """Tamamlanma nedeni."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_USE = "tool_use"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    TIMEOUT = "timeout"


class ModelCapability(str, Enum):
    """Model yetenegi."""

    CHAT = "chat"
    COMPLETION = "completion"
    VISION = "vision"
    TOOL_USE = "tool_use"
    STREAMING = "streaming"
    EMBEDDING = "embedding"
    CODE = "code"
    MULTIMODAL = "multimodal"
    LONG_CONTEXT = "long_context"
    JSON_MODE = "json_mode"
    THINKING = "thinking"
    CONTEXT_1M = "context_1m"


class KeyState(str, Enum):
    """API anahtar durumu."""

    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    RATE_LIMITED = "rate_limited"
    INVALID = "invalid"
    COOLDOWN = "cooldown"
    REVOKED = "revoked"


class ChatMessage(BaseModel):
    """Sohbet mesaji."""

    role: MessageRole = MessageRole.USER
    content: str = ""
    name: str = ""
    tool_call_id: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    """Arac tanimi."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Arac cagrisi."""

    tool_call_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)


class UsageInfo(BaseModel):
    """Kullanim bilgisi."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    turn_id: str = ""  # per-turn izolasyon


class LLMResponse(BaseModel):
    """LLM yanit modeli."""

    response_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    provider: LLMProvider = LLMProvider.ANTHROPIC
    model: str = ""
    content: str = ""
    finish_reason: FinishReason = FinishReason.STOP
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: UsageInfo = Field(default_factory=UsageInfo)
    latency_ms: float = 0.0
    raw_response: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class StreamChunk(BaseModel):
    """Akim parcasi."""

    chunk_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    content: str = ""
    is_final: bool = False
    tool_call_delta: dict[str, Any] = Field(default_factory=dict)
    usage: UsageInfo | None = None


class LLMRequest(BaseModel):
    """LLM istek modeli."""

    request_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    provider: LLMProvider = LLMProvider.ANTHROPIC
    model: str = ""
    messages: list[ChatMessage] = Field(default_factory=list)
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stop_sequences: list[str] = Field(default_factory=list)
    tools: list[ToolDefinition] = Field(default_factory=list)
    stream: bool = False
    timeout_seconds: int = 60
    metadata: dict[str, Any] = Field(default_factory=dict)
    context_1m: bool = False  # anthropic-beta: context-1m-2025-08-07
    thinking_mode: str = ""  # thinkingDefault override


class ModelInfo(BaseModel):
    """Model bilgisi."""

    model_id: str = ""
    provider: LLMProvider = LLMProvider.ANTHROPIC
    display_name: str = ""
    context_window: int = 0
    max_output_tokens: int = 0
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    capabilities: list[ModelCapability] = Field(default_factory=list)
    is_available: bool = True
    description: str = ""


class APIKeyInfo(BaseModel):
    """API anahtar bilgisi."""

    key_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    provider: LLMProvider = LLMProvider.ANTHROPIC
    key_masked: str = ""
    state: KeyState = KeyState.ACTIVE
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    quota_remaining: float = -1.0
    rate_limit_reset: datetime | None = None
    last_used: datetime | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ProviderStatus(BaseModel):
    """Saglayici durumu."""

    provider: LLMProvider = LLMProvider.ANTHROPIC
    is_available: bool = True
    active_keys: int = 0
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    error_count: int = 0
    models_available: int = 0


class UnifiedLLMSnapshot(BaseModel):
    """Unified LLM sistem durumu."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    providers: list[ProviderStatus] = Field(default_factory=list)
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    active_provider: str = ""
    fallback_chain: list[str] = Field(default_factory=list)
    models_registered: int = 0
    keys_active: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
