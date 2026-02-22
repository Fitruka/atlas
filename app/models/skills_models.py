"""Beceri sistemi modelleri.

250 beceri icin tanimlar, yurutme sonuclari
ve kategori yonetimi.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class SkillCategory(str, Enum):
    """Beceri kategorisi."""

    BASIC_TOOLS = "basic_tools"
    DATETIME = "datetime"
    DOCUMENT = "document"
    MEDIA = "media"
    WEB = "web"
    DEVELOPER = "developer"
    SEO = "seo"
    FINANCE = "finance"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    DATA_SCIENCE = "data_science"


class RiskLevel(str, Enum):
    """Risk seviyesi."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SkillStatus(str, Enum):
    """Beceri durumu."""

    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class SkillDefinition(BaseModel):
    """Beceri tanimi."""

    skill_id: str
    name: str
    description: str
    category: str
    risk_level: str = "low"
    parameters: dict[str, str] = {}
    requires_approval: list[str] = []
    status: str = "active"
    version: str = "1.0.0"


class SkillExecution(BaseModel):
    """Beceri yurutme sonucu."""

    execution_id: str
    skill_id: str
    skill_name: str
    parameters: dict[str, Any] = {}
    result: dict[str, Any] = {}
    success: bool = True
    error: str = ""
    execution_time: float = 0.0
    timestamp: float = 0.0


class SkillRegistryEntry(BaseModel):
    """Beceri kayit girdisi."""

    skill_id: str
    name: str
    category: str
    risk_level: str = "low"
    status: str = "active"
    total_executions: int = 0
    success_rate: float = 1.0
    avg_execution_time: float = 0.0
