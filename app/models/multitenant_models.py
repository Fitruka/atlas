"""ATLAS Enterprise Multi-Tenant Architecture modelleri.

Coklu kiracili mimari veri modelleri.
Tenant izolasyonu, RBAC, SSO, uyumluluk
ve faturalandirma modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    """Kiraci durumu."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"
    DELETED = "deleted"


class RoleType(str, Enum):
    """Rol tipi."""

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"
    GUEST = "guest"


class PermissionAction(str, Enum):
    """Izin aksiyonu."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


class SSOProvider(str, Enum):
    """SSO saglayici tipi."""

    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    LDAP = "ldap"


class ComplianceStandard(str, Enum):
    """Uyumluluk standardi."""

    KVKK = "kvkk"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"


class BillingPlan(str, Enum):
    """Faturalandirma plani."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycle(str, Enum):
    """Faturalandirma dongusu."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SandboxStatus(str, Enum):
    """Sandbox durumu."""

    PROVISIONING = "provisioning"
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class Tenant(BaseModel):
    """Kiraci modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    slug: str = ""
    status: TenantStatus = TenantStatus.ACTIVE
    plan: BillingPlan = BillingPlan.FREE
    owner_id: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    settings: dict = Field(default_factory=dict)
    domain: str = ""
    max_users: int = 10
    max_agents: int = 5


class TenantUser(BaseModel):
    """Kiraci kullanicisi modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    tenant_id: str = ""
    user_id: str = ""
    email: str = ""
    role: RoleType = RoleType.MEMBER
    permissions: list[str] = Field(
        default_factory=list,
    )
    joined_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    last_active: datetime | None = None
    is_active: bool = True


class Role(BaseModel):
    """Rol modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    tenant_id: str = ""
    name: str = ""
    role_type: RoleType = RoleType.MEMBER
    permissions: list[str] = Field(
        default_factory=list,
    )
    description: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    is_system: bool = False


class Permission(BaseModel):
    """Izin modeli."""

    resource: str = ""
    action: PermissionAction = (
        PermissionAction.READ
    )
    conditions: dict = Field(
        default_factory=dict,
    )
    granted: bool = True


class Organization(BaseModel):
    """Organizasyon modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    tenant_id: str = ""
    parent_org_id: str | None = None
    members: list[str] = Field(
        default_factory=list,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    settings: dict = Field(default_factory=dict)


class SSOConfig(BaseModel):
    """SSO yapilandirma modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    tenant_id: str = ""
    provider: SSOProvider = SSOProvider.SAML
    entity_id: str = ""
    sso_url: str = ""
    certificate: str = ""
    metadata: dict = Field(default_factory=dict)
    enabled: bool = True


class ComplianceRule(BaseModel):
    """Uyumluluk kurali modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    standard: ComplianceStandard = (
        ComplianceStandard.KVKK
    )
    rule_name: str = ""
    description: str = ""
    check_fn: str = ""
    severity: str = "medium"
    auto_remediate: bool = False


class BillingRecord(BaseModel):
    """Faturalandirma kaydi modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    tenant_id: str = ""
    plan: BillingPlan = BillingPlan.FREE
    cycle: BillingCycle = BillingCycle.MONTHLY
    amount: float = 0.0
    currency: str = "USD"
    period_start: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    period_end: datetime | None = None
    paid: bool = False
    invoice_url: str = ""


class TenantSandbox(BaseModel):
    """Kiraci sandbox modeli."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    tenant_id: str = ""
    status: SandboxStatus = (
        SandboxStatus.PROVISIONING
    )
    resource_limits: dict = Field(
        default_factory=lambda: {
            "cpu": "1",
            "memory": "512Mi",
            "storage": "1Gi",
        },
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    last_used: datetime | None = None
    isolation_level: str = "namespace"
