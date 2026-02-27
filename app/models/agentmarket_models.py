"""ATLAS Secure Agent Marketplace modelleri.

Guvenli agent pazaryeri veri modelleri:
listeleme, denetim, degerlendirme, gelir, bagimlilik, analitik.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ListingStatus(str, Enum):
    """Listeleme durumu."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class AuditResult(str, Enum):
    """Denetim sonucu."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    CRITICAL = "critical"


class ReviewStatus(str, Enum):
    """Degerlendirme durumu."""

    PENDING = "pending"
    APPROVED = "approved"
    FLAGGED = "flagged"
    REMOVED = "removed"


class RevenueModel(str, Enum):
    """Gelir modeli."""

    FREE = "free"
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"


class DependencyStatus(str, Enum):
    """Bagimlilik durumu."""

    RESOLVED = "resolved"
    MISSING = "missing"
    CONFLICT = "conflict"
    OUTDATED = "outdated"


class AnalyticsPeriod(str, Enum):
    """Analitik donemi."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class MarketplaceListing(BaseModel):
    """Pazaryeri listeleme kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    description: str = ""
    author_id: str = ""
    version: str = "1.0.0"
    category: str = ""
    tags: list[str] = Field(
        default_factory=list,
    )
    status: ListingStatus = ListingStatus.DRAFT
    price: float = 0.0
    revenue_model: RevenueModel = (
        RevenueModel.FREE
    )
    download_count: int = 0
    avg_rating: float = 0.0
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


class SecurityAuditReport(BaseModel):
    """Guvenlik denetim raporu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    listing_id: str = ""
    result: AuditResult = AuditResult.PASS
    issues: list[dict] = Field(
        default_factory=list,
    )
    critical_count: int = 0
    warning_count: int = 0
    scanned_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    auditor_version: str = "1.0.0"
    passed: bool = True


class UserReview(BaseModel):
    """Kullanici degerlendirmesi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    listing_id: str = ""
    user_id: str = ""
    rating: float = 5.0
    title: str = ""
    comment: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    helpful_count: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class RevenueRecord(BaseModel):
    """Gelir kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    listing_id: str = ""
    author_id: str = ""
    period: str = ""
    gross_amount: float = 0.0
    platform_fee_pct: float = 30.0
    net_amount: float = 0.0
    currency: str = "USD"
    transactions_count: int = 0


class DependencyNode(BaseModel):
    """Bagimlilik dugumu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    listing_id: str = ""
    name: str = ""
    version: str = ""
    required_version: str = ""
    status: DependencyStatus = (
        DependencyStatus.RESOLVED
    )
    alternatives: list[str] = Field(
        default_factory=list,
    )


class UsageMetric(BaseModel):
    """Kullanim metrigi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    listing_id: str = ""
    period: AnalyticsPeriod = (
        AnalyticsPeriod.DAILY
    )
    installs: int = 0
    uninstalls: int = 0
    active_users: int = 0
    api_calls: int = 0
    error_rate: float = 0.0
    avg_response_ms: float = 0.0
