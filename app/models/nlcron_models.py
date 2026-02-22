"""Natural Language Cron modelleri.

Dogal dille zamanlama veri modelleri.
"""

from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Is durumu."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class RunStatus(str, Enum):
    """Calistirma durumu."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


class RecurrenceType(str, Enum):
    """Yinelenme tipi."""

    ONCE = "once"
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class ParsedSchedule(BaseModel):
    """Ayristirilmis zamanlama."""

    original_text: str = ""
    cron_expression: str = ""
    recurrence_type: RecurrenceType = (
        RecurrenceType.ONCE
    )
    timezone: str = "Europe/Istanbul"
    next_run: float = 0.0
    confidence: float = 0.0
    parsed_at: float = 0.0


class DeliveryMode(str, Enum):
    """Teslimat modu."""

    INLINE = "inline"
    WEBHOOK = "webhook"


class WebhookDelivery(BaseModel):
    """Webhook teslimat yapilandirmasi."""

    url: str = ""
    auth_token: str = ""
    timeout_seconds: int = 30
    ssrf_guard: bool = True


class ScheduledJob(BaseModel):
    """Zamanlanmis is."""

    job_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    name: str = ""
    description: str = ""
    schedule_text: str = ""
    cron_expression: str = ""
    recurrence_type: RecurrenceType = (
        RecurrenceType.ONCE
    )
    timezone: str = "Europe/Istanbul"
    status: JobStatus = JobStatus.ACTIVE
    task_type: str = ""
    task_config: dict[str, str] = Field(
        default_factory=dict,
    )
    created_at: float = 0.0
    updated_at: float = 0.0
    next_run: float = 0.0
    last_run: float = 0.0
    run_count: int = 0
    fail_count: int = 0
    max_runs: int = 0
    max_concurrent_runs: int = 1
    active_runs: int = 0
    stagger_ms: int = 0
    min_refire_gap_seconds: int = 10
    timeout_seconds: int = 300
    delivery_mode: DeliveryMode = DeliveryMode.INLINE
    webhook: WebhookDelivery | None = None
    tags: list[str] = Field(
        default_factory=list,
    )


class RunRecord(BaseModel):
    """Calistirma kaydi."""

    run_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    job_id: str = ""
    status: RunStatus = RunStatus.PENDING
    started_at: float = 0.0
    completed_at: float = 0.0
    duration: float = 0.0
    output: dict[str, str] = Field(
        default_factory=dict,
    )
    error_message: str = ""
    model_used: str = ""
    provider_used: str = ""
    tokens_used: int = 0


class RecurrenceRule(BaseModel):
    """Yinelenme kurali."""

    rule_id: str = Field(
        default_factory=lambda: str(
            uuid4(),
        )[:8],
    )
    recurrence_type: RecurrenceType = (
        RecurrenceType.DAILY
    )
    interval: int = 1
    days_of_week: list[int] = Field(
        default_factory=list,
    )
    days_of_month: list[int] = Field(
        default_factory=list,
    )
    months: list[int] = Field(
        default_factory=list,
    )
    hour: int = 0
    minute: int = 0
    end_after_runs: int = 0
    end_date: float = 0.0
    exception_dates: list[float] = Field(
        default_factory=list,
    )
    skip_weekends: bool = False
