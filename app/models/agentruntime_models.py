"""Agent runtime modelleri."""

from enum import Enum
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class LoopDetectionLevel(str, Enum):
    NONE = "none"
    WARN = "warn"
    BLOCK = "block"


class LoopType(str, Enum):
    IDENTICAL_CALL = "identical_call"
    PING_PONG = "ping_pong"
    CIRCUIT_BREAKER = "circuit_breaker"


class LoopDetectionResult(BaseModel):
    detected: bool = False
    loop_type: LoopType = LoopType.IDENTICAL_CALL
    level: LoopDetectionLevel = LoopDetectionLevel.NONE
    repeat_count: int = 0
    message: str = ""


class AutoPageConfig(BaseModel):
    enabled: bool = True
    chunk_size: int = 2000
    max_chunks: int = 50
    budget_from_context: bool = True


class RuntimeConfig(BaseModel):
    bootstrap_prompt_cap: int = 150000
    identical_call_warn: int = 3
    ping_pong_warn: int = 10
    ping_pong_block: int = 20
    circuit_breaker_limit: int = 30
    auto_page: AutoPageConfig = Field(default_factory=AutoPageConfig)
