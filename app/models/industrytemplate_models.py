"""Industry Agent Template Engine modelleri.

Sektörel agent şablonu, beceri paketi,
iş akışı, CRM yapısı, uyumluluk kuralları
veri modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class IndustryType(str, Enum):
    """Sektör tipi."""
    ECOMMERCE = "ecommerce"
    MEDICAL_TOURISM = "medical_tourism"
    REAL_ESTATE = "real_estate"
    DIGITAL_AGENCY = "digital_agency"
    RESTAURANT = "restaurant"
    LAW_FIRM = "law_firm"
    EDUCATION = "education"
    CUSTOMER_SUPPORT = "customer_support"
    CUSTOM = "custom"


class TemplateStatus(str, Enum):
    """Şablon durumu."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class SkillStatus(str, Enum):
    """Beceri durumu."""
    PENDING = "pending"
    CONFIGURED = "configured"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class WorkflowStepType(str, Enum):
    """İş akışı adım tipi."""
    ACTION = "action"
    CONDITION = "condition"
    NOTIFICATION = "notification"
    APPROVAL = "approval"
    DELAY = "delay"
    PARALLEL = "parallel"
    LOOP = "loop"


class CRMFieldType(str, Enum):
    """CRM alan tipi."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
    CURRENCY = "currency"
    URL = "url"
    RATING = "rating"


class ComplianceLevel(str, Enum):
    """Uyumluluk seviyesi."""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class DeploymentStatus(str, Enum):
    """Dağıtım durumu."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    TERMINATED = "terminated"


class TemplateSkillDef(BaseModel):
    """Şablon beceri tanımı."""
    skill_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    description: str = ""
    category: str = ""
    status: SkillStatus = SkillStatus.PENDING
    config: dict = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    required: bool = True
    enabled: bool = True


class WorkflowStepDef(BaseModel):
    """İş akışı adım tanımı."""
    step_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    step_type: WorkflowStepType = WorkflowStepType.ACTION
    skill_ref: str = ""
    config: dict = Field(default_factory=dict)
    next_steps: list[str] = Field(default_factory=list)
    condition: str = ""
    timeout_seconds: int = 0
    retry_count: int = 0


class WorkflowDef(BaseModel):
    """İş akışı tanımı."""
    workflow_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    description: str = ""
    trigger: str = ""
    steps: list[WorkflowStepDef] = Field(default_factory=list)
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)


class CRMFieldDef(BaseModel):
    """CRM alan tanımı."""
    field_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    label: str = ""
    field_type: CRMFieldType = CRMFieldType.TEXT
    required: bool = False
    default_value: str = ""
    options: list[str] = Field(default_factory=list)
    searchable: bool = True
    sortable: bool = True
    category: str = ""


class CRMSegmentDef(BaseModel):
    """CRM segment tanımı."""
    segment_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    description: str = ""
    criteria: dict = Field(default_factory=dict)
    auto_assign: bool = False


class ComplianceRuleDef(BaseModel):
    """Uyumluluk kuralı tanımı."""
    rule_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    description: str = ""
    level: ComplianceLevel = ComplianceLevel.RECOMMENDED
    category: str = ""
    check_function: str = ""
    remediation: str = ""
    jurisdictions: list[str] = Field(default_factory=list)


class IndustryTemplateDef(BaseModel):
    """Sektörel agent şablon tanımı."""
    template_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    industry: IndustryType = IndustryType.CUSTOM
    version: str = "1.0.0"
    description: str = ""
    author: str = "ATLAS"
    status: TemplateStatus = TemplateStatus.DRAFT
    skills: list[TemplateSkillDef] = Field(default_factory=list)
    workflows: list[WorkflowDef] = Field(default_factory=list)
    crm_fields: list[CRMFieldDef] = Field(default_factory=list)
    crm_segments: list[CRMSegmentDef] = Field(default_factory=list)
    compliance_rules: list[ComplianceRuleDef] = Field(default_factory=list)
    supported_languages: list[str] = Field(default_factory=lambda: ["tr", "en"])
    default_config: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    updated_at: float = 0.0
    metadata: dict = Field(default_factory=dict)


class TemplateDeployment(BaseModel):
    """Şablon dağıtım kaydı."""
    deployment_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    template_id: str = ""
    template_name: str = ""
    industry: IndustryType = IndustryType.CUSTOM
    status: DeploymentStatus = DeploymentStatus.PENDING
    config_overrides: dict = Field(default_factory=dict)
    active_skills: list[str] = Field(default_factory=list)
    active_workflows: list[str] = Field(default_factory=list)
    crm_schema: dict = Field(default_factory=dict)
    compliance_status: dict = Field(default_factory=dict)
    started_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
    completed_at: float = 0.0
    error_message: str = ""
    metadata: dict = Field(default_factory=dict)


class TemplateCustomization(BaseModel):
    """Şablon özelleştirme kaydı."""
    customization_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    template_id: str = ""
    skill_overrides: dict = Field(default_factory=dict)
    workflow_overrides: dict = Field(default_factory=dict)
    crm_additions: list[CRMFieldDef] = Field(default_factory=list)
    extra_compliance: list[ComplianceRuleDef] = Field(default_factory=list)
    language_config: dict = Field(default_factory=dict)
    created_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


class SkillBundleEntry(BaseModel):
    """Beceri paketi kayıt."""
    bundle_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    template_id: str = ""
    skills: list[TemplateSkillDef] = Field(default_factory=list)
    total_skills: int = 0
    configured_count: int = 0
    active_count: int = 0
    error_count: int = 0
    created_at: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
