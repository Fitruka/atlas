"""Headless Browser Engine veri modelleri."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class BrowserType(str, Enum):
    """Tarayici tipi."""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserState(str, Enum):
    """Tarayici durumu."""

    IDLE = "idle"
    BUSY = "busy"
    LAUNCHING = "launching"
    CLOSED = "closed"
    ERROR = "error"


class WaitStrategy(str, Enum):
    """Bekleme stratejisi."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"
    NONE = "none"


class ElementAction(str, Enum):
    """Element aksiyon tipi."""

    CLICK = "click"
    DBLCLICK = "dblclick"
    TYPE = "type"
    SELECT = "select"
    HOVER = "hover"
    DRAG = "drag"
    SCROLL = "scroll"
    CHECK = "check"
    UNCHECK = "uncheck"
    FOCUS = "focus"
    CLEAR = "clear"


class FieldType(str, Enum):
    """Form alan tipi."""

    TEXT = "text"
    PASSWORD = "password"
    EMAIL = "email"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FILE = "file"
    DATE = "date"
    HIDDEN = "hidden"
    SUBMIT = "submit"


class DownloadState(str, Enum):
    """Indirme durumu."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PoolStrategy(str, Enum):
    """Havuz stratejisi."""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"


class CookieSameSite(str, Enum):
    """Cookie SameSite politikasi."""

    STRICT = "Strict"
    LAX = "Lax"
    NONE = "None"


class SSRFPolicy(str, Enum):
    """SSRF koruma politikasi."""

    STRICT = "strict"
    WARN = "warn"
    OFF = "off"


class BrowserConfig(BaseModel):
    """Tarayici yapilandirmasi."""

    config_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    timeout_ms: int = 30000
    viewport_width: int = 1280
    viewport_height: int = 720
    user_agent: str = ""
    locale: str = "en-US"
    proxy: str = ""
    ignore_https_errors: bool = False
    extra_args: list[str] = Field(default_factory=list)
    screenshot_on_error: bool = True
    ssrf_policy: SSRFPolicy = SSRFPolicy.STRICT
    gateway_token: str = ""
    no_sandbox: bool = False


class BrowserInstance(BaseModel):
    """Tarayici ornegi."""

    instance_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    browser_type: BrowserType = BrowserType.CHROMIUM
    state: BrowserState = BrowserState.IDLE
    page_count: int = 0
    context_count: int = 0
    memory_mb: float = 0.0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_activity: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class PageInfo(BaseModel):
    """Sayfa bilgisi."""

    page_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    url: str = ""
    title: str = ""
    status_code: int = 0
    content_type: str = ""
    load_time_ms: float = 0.0
    is_loaded: bool = False
    frame_count: int = 0
    error: str = ""


class NavigationEntry(BaseModel):
    """Navigasyon kaydı."""

    entry_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    url: str = ""
    title: str = ""
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status_code: int = 0
    load_time_ms: float = 0.0
    wait_strategy: WaitStrategy = WaitStrategy.LOAD


class ElementInfo(BaseModel):
    """Element bilgisi."""

    element_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    selector: str = ""
    tag_name: str = ""
    text_content: str = ""
    inner_html: str = ""
    visible: bool = False
    enabled: bool = True
    attributes: dict[str, str] = Field(default_factory=dict)
    bounding_box: dict[str, float] = Field(default_factory=dict)


class InteractionResult(BaseModel):
    """Etkilesim sonucu."""

    result_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    action: ElementAction = ElementAction.CLICK
    selector: str = ""
    success: bool = False
    error: str = ""
    duration_ms: float = 0.0
    screenshot_path: str = ""


class FormField(BaseModel):
    """Form alani."""

    field_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    field_type: FieldType = FieldType.TEXT
    selector: str = ""
    label: str = ""
    value: str = ""
    required: bool = False
    options: list[str] = Field(default_factory=list)
    placeholder: str = ""


class FormInfo(BaseModel):
    """Form bilgisi."""

    form_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    action: str = ""
    method: str = "GET"
    selector: str = ""
    fields: list[FormField] = Field(default_factory=list)
    submit_selector: str = ""
    field_count: int = 0


class FormFillResult(BaseModel):
    """Form doldurma sonucu."""

    result_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    form_selector: str = ""
    fields_filled: int = 0
    fields_total: int = 0
    submitted: bool = False
    success: bool = False
    errors: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0


class ScriptResult(BaseModel):
    """JavaScript calistirma sonucu."""

    result_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    script: str = ""
    return_value: Any = None
    success: bool = False
    error: str = ""
    duration_ms: float = 0.0
    is_async: bool = False


class CookieData(BaseModel):
    """Cookie verisi."""

    cookie_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    value: str = ""
    domain: str = ""
    path: str = "/"
    expires: float = -1
    http_only: bool = False
    secure: bool = False
    same_site: CookieSameSite = CookieSameSite.LAX


class CookieSnapshot(BaseModel):
    """Cookie snapshot."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    cookies: list[CookieData] = Field(default_factory=list)
    domain: str = ""
    count: int = 0
    exported_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class DownloadInfo(BaseModel):
    """Indirme bilgisi."""

    download_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    url: str = ""
    filename: str = ""
    save_path: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    downloaded_bytes: int = 0
    state: DownloadState = DownloadState.PENDING
    progress_percent: float = 0.0
    error: str = ""
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None


class PoolStatus(BaseModel):
    """Havuz durumu."""

    pool_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    total_instances: int = 0
    idle_instances: int = 0
    busy_instances: int = 0
    max_size: int = 5
    strategy: PoolStrategy = PoolStrategy.ROUND_ROBIN
    total_requests: int = 0
    avg_wait_ms: float = 0.0


class HeadlessSnapshot(BaseModel):
    """Headless Engine sistem durumu."""

    snapshot_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    browser_config: BrowserConfig = Field(default_factory=BrowserConfig)
    pool_status: PoolStatus = Field(default_factory=PoolStatus)
    total_navigations: int = 0
    total_interactions: int = 0
    total_scripts: int = 0
    total_downloads: int = 0
    total_forms_filled: int = 0
    active_pages: int = 0
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
