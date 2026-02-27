"""Multi-Language Skill Runtime modelleri.

Cok dilli beceri calisma zamani, paket yonetimi,
yurume, test, SDK ve pazar yeri icin veri modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class SkillLanguage(str, Enum):
    """Beceri programlama dili."""

    PYTHON = "python"
    NODEJS = "nodejs"
    GO = "go"
    WASM = "wasm"
    RUST = "rust"
    RUBY = "ruby"


class SkillStatus(str, Enum):
    """Beceri durumu."""

    PENDING = "pending"
    BUILDING = "building"
    READY = "ready"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"


class TestResult(str, Enum):
    """Test sonucu."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class SDKFeature(str, Enum):
    """SDK ozellik tipi."""

    HTTP_CLIENT = "http_client"
    DB_ACCESS = "db_access"
    FILE_IO = "file_io"
    MESSAGING = "messaging"
    CACHING = "caching"
    LOGGING = "logging"


class MarketplaceCategory(str, Enum):
    """Pazar yeri kategorisi."""

    AUTOMATION = "automation"
    ANALYTICS = "analytics"
    COMMUNICATION = "communication"
    SECURITY = "security"
    INTEGRATION = "integration"
    UTILITY = "utility"


class SecurityLevel(str, Enum):
    """Guvenlik seviyesi."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SkillPackage(BaseModel):
    """Beceri paketi."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    name: str = ""
    language: SkillLanguage = (
        SkillLanguage.PYTHON
    )
    version: str = "1.0.0"
    entry_point: str = "main"
    dependencies: list[str] = Field(
        default_factory=list,
    )
    size_bytes: int = 0
    checksum: str = ""
    status: SkillStatus = SkillStatus.PENDING
    code: str = ""
    created_at: float = Field(
        default_factory=lambda: (
            datetime.now(
                timezone.utc,
            ).timestamp()
        ),
    )


class SkillExecution(BaseModel):
    """Beceri calistirma sonucu."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    skill_id: str = ""
    language: SkillLanguage = (
        SkillLanguage.PYTHON
    )
    start_time: float = Field(
        default_factory=lambda: (
            datetime.now(
                timezone.utc,
            ).timestamp()
        ),
    )
    end_time: float = 0.0
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    memory_used_mb: float = 0.0
    cpu_time_ms: float = 0.0


class SkillTestReport(BaseModel):
    """Beceri test raporu."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    skill_id: str = ""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    coverage_pct: float = 0.0
    duration_ms: float = 0.0
    results: list[dict] = Field(
        default_factory=list,
    )


class SDKConfig(BaseModel):
    """SDK yapilandirmasi."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    language: SkillLanguage = (
        SkillLanguage.PYTHON
    )
    features: list[str] = Field(
        default_factory=list,
    )
    sandbox_enabled: bool = True
    max_memory_mb: int = 256
    max_cpu_ms: int = 30000
    network_allowed: bool = False


class MarketplaceEntry(BaseModel):
    """Pazar yeri kaydi."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    skill_id: str = ""
    name: str = ""
    description: str = ""
    author: str = ""
    category: MarketplaceCategory = (
        MarketplaceCategory.UTILITY
    )
    language: SkillLanguage = (
        SkillLanguage.PYTHON
    )
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    verified: bool = False
    price: float = 0.0
    reviews: list[dict] = Field(
        default_factory=list,
    )
    created_at: float = Field(
        default_factory=lambda: (
            datetime.now(
                timezone.utc,
            ).timestamp()
        ),
    )


class SecurityScanResult(BaseModel):
    """Guvenlik tarama sonucu."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    skill_id: str = ""
    language: SkillLanguage = (
        SkillLanguage.PYTHON
    )
    issues: list[dict] = Field(
        default_factory=list,
    )
    risk_level: SecurityLevel = (
        SecurityLevel.LOW
    )
    passed: bool = True
    scan_duration_ms: float = 0.0
