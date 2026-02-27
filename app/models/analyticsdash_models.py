"""
Native Analytics & Reporting Dashboard modelleri.

Metrik, dashboard, widget, konuşma, maliyet,
cron, kanal, şablon, dışa aktarma modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Metrik türleri."""

    counter = "counter"
    gauge = "gauge"
    histogram = "histogram"
    rate = "rate"
    percentage = "percentage"


class TimeGranularity(str, Enum):
    """Zaman ayrıntı düzeyleri."""

    minute = "minute"
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"


class DashboardLayout(str, Enum):
    """Dashboard düzen türleri."""

    grid = "grid"
    list = "list"
    freeform = "freeform"
    tabbed = "tabbed"


class WidgetType(str, Enum):
    """Widget türleri."""

    line_chart = "line_chart"
    bar_chart = "bar_chart"
    pie_chart = "pie_chart"
    gauge = "gauge"
    table = "table"
    metric_card = "metric_card"
    heatmap = "heatmap"
    timeline = "timeline"


class ExportFormat(str, Enum):
    """Dışa aktarma formatları."""

    pdf = "pdf"
    excel = "excel"
    csv = "csv"
    png = "png"
    html = "html"


class ChannelType(str, Enum):
    """Kanal türleri."""

    telegram = "telegram"
    whatsapp = "whatsapp"
    discord = "discord"
    slack = "slack"
    email = "email"
    web = "web"
    voice = "voice"
    api = "api"


class CronStatus(str, Enum):
    """Cron iş durumları."""

    running = "running"
    completed = "completed"
    failed = "failed"
    pending = "pending"
    skipped = "skipped"


class MetricPoint(BaseModel):
    """Tek metrik noktası."""

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    value: float = 0.0
    labels: dict = Field(default_factory=dict)
    metric_type: str = "gauge"


class MetricSeries(BaseModel):
    """Metrik serisi."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    name: str = ""
    metric_type: str = "gauge"
    points: list = Field(default_factory=list)
    aggregation: str = "avg"
    granularity: str = "hour"


class DashboardConfig(BaseModel):
    """Dashboard yapılandırması."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    name: str = ""
    description: str = ""
    layout: str = "grid"
    widgets: list = Field(default_factory=list)
    refresh_interval: int = 30
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    owner: str = ""


class WidgetConfig(BaseModel):
    """Widget yapılandırması."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    widget_type: str = "metric_card"
    title: str = ""
    data_source: str = ""
    query: str = ""
    size_x: int = 1
    size_y: int = 1
    position_x: int = 0
    position_y: int = 0
    settings: dict = Field(default_factory=dict)


class ConversationMetric(BaseModel):
    """Konuşma metriği."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    channel: str = "telegram"
    total_messages: int = 0
    avg_response_time: float = 0.0
    satisfaction_score: float = 0.0
    period: str = "day"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class CostMetric(BaseModel):
    """Maliyet metriği."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    period: str = "day"
    total_cost: float = 0.0
    by_model: dict = Field(default_factory=dict)
    by_tool: dict = Field(default_factory=dict)
    by_template: dict = Field(
        default_factory=dict
    )
    budget_used_pct: float = 0.0
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class CronJobMetric(BaseModel):
    """Cron iş metriği."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    job_name: str = ""
    status: str = "pending"
    last_run: datetime | None = None
    next_run: datetime | None = None
    avg_duration: float = 0.0
    success_rate: float = 100.0
    consecutive_failures: int = 0


class ChannelMetric(BaseModel):
    """Kanal metriği."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    channel_type: str = "telegram"
    messages_in: int = 0
    messages_out: int = 0
    active_users: int = 0
    avg_response_time: float = 0.0
    period: str = "day"


class TemplateMetric(BaseModel):
    """Şablon metriği."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    template_name: str = ""
    industry: str = ""
    active_deployments: int = 0
    total_requests: int = 0
    avg_cost: float = 0.0
    satisfaction: float = 0.0
    period: str = "day"


class ExportResult(BaseModel):
    """Dışa aktarma sonucu."""

    id: str = Field(
        default_factory=lambda: str(
            uuid4()
        )[:8]
    )
    format: str = "pdf"
    file_path: str = ""
    file_size: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    dashboard_id: str = ""
    status: str = "completed"
