"""Exec engine modelleri."""

from enum import Enum
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field


class ExecMode(str, Enum):
    SAFE = "safe"
    ASK = "ask"
    FULL = "full"


class ExecResult(BaseModel):
    exec_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    command: str = ""
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    was_approved: bool = False
    mode: ExecMode = ExecMode.SAFE


class SafeBinConfig(BaseModel):
    trusted_dirs: list[str] = Field(default_factory=lambda: ["/usr/bin", "/usr/local/bin", "/bin"])
    blocked_flags: dict[str, list[str]] = Field(default_factory=lambda: {
        "sort": ["-o"], "grep": ["-f"], "jq": ["-f"],
    })


class EnvInjectionResult(BaseModel):
    detected: bool = False
    variable_name: str = ""
    pattern: str = ""
