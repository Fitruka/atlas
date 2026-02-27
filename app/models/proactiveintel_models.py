"""ATLAS Proactive Intelligence Engine modelleri."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class HeartbeatFrequency(str, Enum):
    """Heartbeat sıklığı."""

    REALTIME = "realtime"
    FREQUENT = "frequent"
    NORMAL = "normal"
    LOW = "low"
    IDLE = "idle"


class AlertPriority(str, Enum):
    """Uyarı önceliği."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OpportunityType(str, Enum):
    """Fırsat tipi."""

    COST_SAVING = "cost_saving"
    REVENUE = "revenue"
    EFFICIENCY = "efficiency"
    RISK_MITIGATION = "risk_mitigation"
    GROWTH = "growth"


class CompetitorAction(str, Enum):
    """Rakip aksiyonu."""

    PRICE_CHANGE = "price_change"
    NEW_PRODUCT = "new_product"
    CAMPAIGN = "campaign"
    PARTNERSHIP = "partnership"
    HIRING = "hiring"
    EXPANSION = "expansion"


class SentimentLevel(str, Enum):
    """Duygu seviyesi."""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class DigestFrequency(str, Enum):
    """Özet sıklığı."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TrendDirection(str, Enum):
    """Trend yönü."""

    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class HeartbeatConfig(BaseModel):
    """Heartbeat yapılandırması."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    context: str = ""
    frequency: str = HeartbeatFrequency.NORMAL
    last_sent: datetime | None = None
    content_type: str = "status"
    active: bool = True
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class PredictiveAlert(BaseModel):
    """Tahminsel uyarı."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    title: str = ""
    description: str = ""
    priority: str = AlertPriority.MEDIUM
    predicted_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    expected_at: datetime | None = None
    confidence: float = 0.5
    category: str = ""
    recommended_action: str = ""
    acknowledged: bool = False


class OpportunityRecord(BaseModel):
    """Fırsat kaydı."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    opportunity_type: str = (
        OpportunityType.EFFICIENCY
    )
    title: str = ""
    description: str = ""
    estimated_value: float = 0.0
    confidence: float = 0.5
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    expires_at: datetime | None = None
    status: str = "active"
    source: str = ""


class CompetitorEvent(BaseModel):
    """Rakip olayı."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    competitor_name: str = ""
    action: str = CompetitorAction.PRICE_CHANGE
    description: str = ""
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    impact_level: str = "medium"
    source_url: str = ""
    verified: bool = False


class SentimentRecord(BaseModel):
    """Duygu analizi kaydı."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    source: str = ""
    text: str = ""
    sentiment_level: str = SentimentLevel.NEUTRAL
    score: float = 0.0
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    entity: str = ""
    channel: str = ""


class DigestEntry(BaseModel):
    """Özet girdisi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    title: str = ""
    summary: str = ""
    category: str = ""
    priority: str = AlertPriority.MEDIUM
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    action_required: bool = False
    data: dict[str, Any] = Field(
        default_factory=dict,
    )


class SmartDigestReport(BaseModel):
    """Akıllı özet raporu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    frequency: str = DigestFrequency.DAILY
    period_start: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    period_end: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    entries: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    highlights: list[str] = Field(
        default_factory=list,
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    recipient: str = ""


class TrendRecord(BaseModel):
    """Trend kaydı."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    category: str = ""
    direction: str = TrendDirection.STABLE
    momentum: float = 0.0
    data_points: list[float] = Field(
        default_factory=list,
    )
    first_seen: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    description: str = ""
