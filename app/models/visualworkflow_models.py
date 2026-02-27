"""
Visual Workflow Builder (No-Code) modelleri.

Gorsel is akisi olusturucu, dugum, baglanti,
tetikleyici, aksiyon, kosul, sablon modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Dugum turleri."""

    trigger = "trigger"
    action = "action"
    condition = "condition"
    delay = "delay"
    loop = "loop"
    merge = "merge"
    end = "end"


class TriggerType(str, Enum):
    """Tetikleyici turleri."""

    webhook = "webhook"
    schedule = "schedule"
    event = "event"
    manual = "manual"
    api_call = "api_call"
    message_received = "message_received"


class ActionType(str, Enum):
    """Aksiyon turleri."""

    send_message = "send_message"
    api_request = "api_request"
    database_query = "database_query"
    transform_data = "transform_data"
    notify = "notify"
    assign_task = "assign_task"
    run_skill = "run_skill"


class ConditionOperator(str, Enum):
    """Kosul operatorleri."""

    equals = "equals"
    not_equals = "not_equals"
    greater_than = "greater_than"
    less_than = "less_than"
    contains = "contains"
    matches_regex = "matches_regex"
    is_empty = "is_empty"
    is_not_empty = "is_not_empty"


class WorkflowStatus(str, Enum):
    """Is akisi durumlari."""

    draft = "draft"
    active = "active"
    paused = "paused"
    archived = "archived"
    error = "error"


class ConnectionType(str, Enum):
    """Baglanti turleri."""

    success = "success"
    failure = "failure"
    default = "default"
    conditional = "conditional"


class PreviewStatus(str, Enum):
    """Onizleme durumlari."""

    idle = "idle"
    running = "running"
    completed = "completed"
    error = "error"


class TriggerConfig(BaseModel):
    """Tetikleyici yapilandirmasi."""

    trigger_type: str = "manual"
    schedule_cron: str = ""
    webhook_path: str = ""
    event_name: str = ""
    filters: dict = Field(default_factory=dict)


class ActionConfig(BaseModel):
    """Aksiyon yapilandirmasi."""

    action_type: str = "send_message"
    target: str = ""
    method: str = "POST"
    payload_template: dict = Field(
        default_factory=dict
    )
    timeout: int = 30
    retry_count: int = 0


class ConditionConfig(BaseModel):
    """Kosul yapilandirmasi."""

    left_operand: str = ""
    operator: str = "equals"
    right_operand: str = ""
    combine_with: str = "and"


class WorkflowNode(BaseModel):
    """Is akisi dugumu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8]
    )
    node_type: str = "action"
    name: str = ""
    description: str = ""
    config: dict = Field(default_factory=dict)
    position_x: float = 0.0
    position_y: float = 0.0
    inputs: list[str] = Field(
        default_factory=list
    )
    outputs: list[str] = Field(
        default_factory=list
    )


class WorkflowConnection(BaseModel):
    """Is akisi baglantisi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8]
    )
    source_node_id: str = ""
    source_port: str = "out"
    target_node_id: str = ""
    target_port: str = "in"
    connection_type: str = "default"
    condition_expr: str = ""


class VisualWorkflow(BaseModel):
    """Gorsel is akisi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8]
    )
    name: str = ""
    description: str = ""
    status: str = "draft"
    nodes: list[WorkflowNode] = Field(
        default_factory=list
    )
    connections: list[WorkflowConnection] = Field(
        default_factory=list
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    version: int = 1
    tags: list[str] = Field(
        default_factory=list
    )


class WorkflowTemplate(BaseModel):
    """Is akisi sablonu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8]
    )
    name: str = ""
    description: str = ""
    category: str = ""
    industry: str = ""
    workflow_def: dict = Field(
        default_factory=dict
    )
    usage_count: int = 0
    rating: float = 0.0


class PreviewResult(BaseModel):
    """Onizleme sonucu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8]
    )
    workflow_id: str = ""
    status: str = "idle"
    executed_nodes: list[str] = Field(
        default_factory=list
    )
    results: list[dict] = Field(
        default_factory=list
    )
    errors: list[str] = Field(
        default_factory=list
    )
    duration_ms: float = 0.0
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


class DeploymentResult(BaseModel):
    """Dagitim sonucu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8]
    )
    workflow_id: str = ""
    version: int = 1
    deployed_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )
    active: bool = False
    endpoint_url: str = ""
