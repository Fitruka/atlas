"""Cost Control & Budget Engine modelleri.

Gerçek zamanlı maliyet takibi, bütçe limitleri,
maliyet uyarıları, akıllı model yönlendirme,
token sıkıştırma, maliyet projeksiyonu
veri modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class CostPeriod(str, Enum):
    """Maliyet dönemi."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class BudgetStatus(str, Enum):
    """Bütçe durumu."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"
    HARD_STOP = "hard_stop"


class AlertSeverity(str, Enum):
    """Uyarı şiddeti."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ModelTier(str, Enum):
    """Model katmanı."""
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"
    ULTRA = "ultra"


class TaskComplexity(str, Enum):
    """Görev karmaşıklığı."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class ProviderStatus(str, Enum):
    """Sağlayıcı durumu."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"


class HeartbeatMode(str, Enum):
    """Heartbeat modu."""
    FULL = "full"
    MINIMAL = "minimal"
    BATCHED = "batched"
    CONDITIONAL = "conditional"
    DISABLED = "disabled"


class CompressionStrategy(str, Enum):
    """Sıkıştırma stratejisi."""
    NONE = "none"
    SUMMARY = "summary"
    TRUNCATE = "truncate"
    SELECTIVE = "selective"
    AGGRESSIVE = "aggressive"


class CostEntry(BaseModel):
    """Maliyet kaydı."""
    entry_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    session_id: str = ""
    model_name: str = ""
    provider: str = ""
    tool_name: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    task_type: str = ""
    template_id: str = ""
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    metadata: dict = Field(default_factory=dict)


class BudgetLimit(BaseModel):
    """Bütçe limiti."""
    limit_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    period: CostPeriod = CostPeriod.DAILY
    limit_usd: float = 0.0
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95
    hard_stop: bool = True
    current_spend: float = 0.0
    status: BudgetStatus = BudgetStatus.NORMAL
    reset_at: float = 0.0
    created_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    metadata: dict = Field(default_factory=dict)


class CostAlert(BaseModel):
    """Maliyet uyarısı."""
    alert_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    message: str = ""
    budget_id: str = ""
    current_spend: float = 0.0
    limit_usd: float = 0.0
    percentage: float = 0.0
    acknowledged: bool = False
    channels: list[str] = Field(default_factory=lambda: ["telegram"])
    created_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


class ModelRouteConfig(BaseModel):
    """Model yönlendirme yapılandırması."""
    config_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    model_name: str = ""
    provider: str = ""
    tier: ModelTier = ModelTier.STANDARD
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_tokens: int = 0
    latency_ms: float = 0.0
    quality_score: float = 0.0
    supported_tasks: list[str] = Field(default_factory=list)
    enabled: bool = True
    metadata: dict = Field(default_factory=dict)


class RouteDecision(BaseModel):
    """Yönlendirme kararı."""
    decision_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    task_type: str = ""
    complexity: TaskComplexity = TaskComplexity.MODERATE
    selected_model: str = ""
    selected_provider: str = ""
    selected_tier: ModelTier = ModelTier.STANDARD
    estimated_cost: float = 0.0
    reason: str = ""
    alternatives: list[dict] = Field(default_factory=list)
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


class HeartbeatConfig(BaseModel):
    """Heartbeat yapılandırması."""
    config_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    mode: HeartbeatMode = HeartbeatMode.FULL
    interval_seconds: int = 300
    batch_size: int = 10
    include_metrics: bool = True
    include_status: bool = True
    skip_if_idle: bool = True
    cost_per_heartbeat: float = 0.0
    estimated_monthly_savings: float = 0.0
    metadata: dict = Field(default_factory=dict)


class CompressionResult(BaseModel):
    """Sıkıştırma sonucu."""
    result_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    strategy: CompressionStrategy = CompressionStrategy.NONE
    original_tokens: int = 0
    compressed_tokens: int = 0
    savings_tokens: int = 0
    savings_percent: float = 0.0
    quality_loss: float = 0.0
    cost_saved_usd: float = 0.0
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


class CostProjectionResult(BaseModel):
    """Maliyet projeksiyon sonucu."""
    projection_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    period: CostPeriod = CostPeriod.MONTHLY
    current_spend: float = 0.0
    projected_spend: float = 0.0
    trend: str = ""
    trend_percent: float = 0.0
    confidence: float = 0.0
    breakdown_by_model: dict = Field(default_factory=dict)
    breakdown_by_tool: dict = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    projected_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


class ProviderInfo(BaseModel):
    """Sağlayıcı bilgisi."""
    provider_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    status: ProviderStatus = ProviderStatus.AVAILABLE
    models: list[str] = Field(default_factory=list)
    base_url: str = ""
    latency_ms: float = 0.0
    reliability_score: float = 1.0
    cost_multiplier: float = 1.0
    rate_limit_remaining: int = 0
    last_checked: float = 0.0
    metadata: dict = Field(default_factory=dict)


class ArbitrageDecision(BaseModel):
    """Arbitraj kararı."""
    decision_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    model_name: str = ""
    selected_provider: str = ""
    cost_usd: float = 0.0
    cheapest_cost: float = 0.0
    savings_usd: float = 0.0
    latency_ms: float = 0.0
    providers_compared: int = 0
    reason: str = ""
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


class TemplateCostReport(BaseModel):
    """Şablon maliyet raporu."""
    report_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    template_id: str = ""
    template_name: str = ""
    period: CostPeriod = CostPeriod.MONTHLY
    total_cost: float = 0.0
    cost_by_skill: dict = Field(default_factory=dict)
    cost_by_model: dict = Field(default_factory=dict)
    total_tokens: int = 0
    total_requests: int = 0
    avg_cost_per_request: float = 0.0
    optimization_suggestions: list[str] = Field(default_factory=list)
    generated_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
