"""ATLAS Managed Cloud Deployment (Atlas Cloud) modelleri.

Bulut dagitimi, otomatik olcekleme, yonetilen
guncellemeler, yedekleme, saglik izleme ve
onboarding sihirbazi icin veri modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DeploymentStatus(str, Enum):
    """Dagitim durumu."""

    PENDING = "pending"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    UPDATING = "updating"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class ScaleDirection(str, Enum):
    """Olcekleme yonu."""

    UP = "up"
    DOWN = "down"
    NONE = "none"


class UpdateStrategy(str, Enum):
    """Guncelleme stratejisi."""

    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"


class BackupType(str, Enum):
    """Yedekleme tipi."""

    FULL = "full"
    INCREMENTAL = "incremental"
    SNAPSHOT = "snapshot"


class HealthStatus(str, Enum):
    """Saglik durumu."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class InstanceSize(str, Enum):
    """Ornek boyutu."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"


class Region(str, Enum):
    """Bulut bolgesi."""

    US_EAST = "us_east"
    US_WEST = "us_west"
    EU_WEST = "eu_west"
    EU_CENTRAL = "eu_central"
    ASIA_PACIFIC = "asia_pacific"


class CloudDeployment(BaseModel):
    """Bulut dagitim kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    tenant_id: str = ""
    region: str = Region.EU_CENTRAL
    instance_size: str = InstanceSize.MEDIUM
    status: str = DeploymentStatus.PENDING
    version: str = "1.0.0"
    replicas: int = 1
    url: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class ScaleEvent(BaseModel):
    """Olcekleme olayi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    deployment_id: str = ""
    direction: str = ScaleDirection.NONE
    from_replicas: int = 1
    to_replicas: int = 1
    reason: str = ""
    triggered_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class CloudUpdate(BaseModel):
    """Bulut guncelleme kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    deployment_id: str = ""
    from_version: str = ""
    to_version: str = ""
    strategy: str = UpdateStrategy.ROLLING
    status: str = DeploymentStatus.PENDING
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    completed_at: datetime | None = None
    rollback_available: bool = True


class CloudBackup(BaseModel):
    """Bulut yedekleme kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    deployment_id: str = ""
    backup_type: str = BackupType.FULL
    size_mb: float = 0.0
    storage_path: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    expires_at: datetime | None = None
    verified: bool = False


class HealthCheck(BaseModel):
    """Saglik kontrolu kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    deployment_id: str = ""
    status: str = HealthStatus.UNKNOWN
    cpu_pct: float = 0.0
    memory_pct: float = 0.0
    disk_pct: float = 0.0
    response_time_ms: float = 0.0
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class WizardStep(BaseModel):
    """Sihirbaz adimi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    step_number: int = 0
    title: str = ""
    description: str = ""
    completed: bool = False
    data: dict[str, Any] = Field(
        default_factory=dict,
    )
