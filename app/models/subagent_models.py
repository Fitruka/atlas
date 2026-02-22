"""Subagent sistemi modelleri.

Ic ice sub-agent yonetimi, derinlik kontrolu
ve baglamlar arasi guvenligi saglar.
"""

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SubagentStatus(str, Enum):
    """Sub-agent durumu."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEPTH_EXCEEDED = "depth_exceeded"


class ToolPolicy(str, Enum):
    """Derinlik bazli arac politikasi."""
    FULL = "full"
    RESTRICTED = "restricted"
    READ_ONLY = "read_only"
    NONE = "none"


class SubagentConfig(BaseModel):
    """Sub-agent yapilandirmasi."""
    max_spawn_depth: int = 3
    max_children_per_agent: int = 5
    tool_policy_by_depth: dict[int, ToolPolicy] = Field(default_factory=lambda: {
        0: ToolPolicy.FULL,
        1: ToolPolicy.FULL,
        2: ToolPolicy.RESTRICTED,
        3: ToolPolicy.READ_ONLY,
    })
    max_tool_output_chars: int = 50000
    context_guard_enabled: bool = True
    announce_chain: bool = True
    max_announce_retries: int = 3
    announce_expiry_seconds: int = 300


class SubagentInstance(BaseModel):
    """Sub-agent ornegi."""
    agent_id: str = Field(default_factory=lambda: str(uuid4())[:12])
    parent_id: str = ""
    name: str = ""
    depth: int = 0
    status: SubagentStatus = SubagentStatus.PENDING
    model: str = ""
    provider: str = ""
    tool_policy: ToolPolicy = ToolPolicy.FULL
    children: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    created_at: float = 0.0
    completed_at: float = 0.0


class AnnounceMessage(BaseModel):
    """Announce zinciri mesaji."""
    message_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    from_agent: str = ""
    to_agent: str = ""
    content: str = ""
    chain: list[str] = Field(default_factory=list)
    retry_count: int = 0
    created_at: float = 0.0
    expires_at: float = 0.0


class CompactionResult(BaseModel):
    """Mesaj sikistirma sonucu."""
    original_chars: int = 0
    compacted_chars: int = 0
    messages_compacted: int = 0
    truncated_outputs: int = 0
