"""ATLAS Zero-Trust Security Architecture modelleri.

Sifir guven guvenlik mimarisi veri modelleri.
Sifrelenmis kimlik, enjeksiyon koruma, sandbox,
ag politikasi, gateway, denetim izi modelleri.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ZTSTrustLevel(str, Enum):
    """Guven seviyesi."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL = "full"


class CredentialType(str, Enum):
    """Kimlik bilgisi tipi."""

    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    PASSWORD = "password"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"


class InjectionType(str, Enum):
    """Enjeksiyon saldiri tipi."""

    DIRECT = "direct"
    INDIRECT = "indirect"
    JAILBREAK = "jailbreak"
    DATA_EXFIL = "data_exfil"
    ROLE_HIJACK = "role_hijack"


class ThreatSeverity(str, Enum):
    """Tehdit siddeti."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyAction(str, Enum):
    """Politika aksiyonu."""

    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"


class VerificationStatus(str, Enum):
    """Dogrulama durumu."""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    EXPIRED = "expired"


class UpdateChannel(str, Enum):
    """Guncelleme kanali."""

    STABLE = "stable"
    BETA = "beta"
    NIGHTLY = "nightly"
    SECURITY_PATCH = "security_patch"


class NetworkDirection(str, Enum):
    """Ag trafik yonu."""

    INGRESS = "ingress"
    EGRESS = "egress"
    BOTH = "both"


class EncryptedCredential(BaseModel):
    """Sifrelenmis kimlik bilgisi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    credential_type: CredentialType = (
        CredentialType.API_KEY
    )
    encrypted_value: str = ""
    salt: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    expires_at: datetime | None = None
    last_rotated: datetime | None = None
    owner: str = ""
    tags: list[str] = Field(default_factory=list)


class InjectionAttempt(BaseModel):
    """Enjeksiyon girisimi kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    input_text: str = ""
    injection_type: InjectionType = (
        InjectionType.DIRECT
    )
    confidence: float = 0.0
    blocked: bool = False
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    source: str = ""


class SandboxResult(BaseModel):
    """Sandbox dogrulama sonucu."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    skill_id: str = ""
    skill_name: str = ""
    status: VerificationStatus = (
        VerificationStatus.PENDING
    )
    threats_found: list[str] = Field(
        default_factory=list,
    )
    execution_time: float = 0.0
    resource_usage: dict = Field(
        default_factory=dict,
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )


class NetworkPolicy(BaseModel):
    """Ag politikasi kurali."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    name: str = ""
    direction: NetworkDirection = (
        NetworkDirection.BOTH
    )
    action: PolicyAction = PolicyAction.DENY
    source_pattern: str = "*"
    dest_pattern: str = "*"
    port_range: str = ""
    protocol: str = "tcp"
    enabled: bool = True


class GatewayRequest(BaseModel):
    """Gateway istek kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    source: str = ""
    destination: str = ""
    method: str = ""
    trust_level: ZTSTrustLevel = (
        ZTSTrustLevel.NONE
    )
    authenticated: bool = False
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    allowed: bool = False


class PoisonAttempt(BaseModel):
    """Hafiza zehirleme girisimi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    memory_key: str = ""
    original_hash: str = ""
    tampered_hash: str = ""
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    severity: ThreatSeverity = (
        ThreatSeverity.HIGH
    )
    remediated: bool = False


class AuditEntry(BaseModel):
    """Denetim kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    actor: str = ""
    action: str = ""
    resource: str = ""
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    trust_level: ZTSTrustLevel = (
        ZTSTrustLevel.NONE
    )
    ip_address: str = ""
    result: str = ""
    signature: str = ""


class UpdatePackage(BaseModel):
    """Guncelleme paketi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    version: str = ""
    channel: UpdateChannel = UpdateChannel.STABLE
    checksum_sha256: str = ""
    signature: str = ""
    released_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    size_bytes: int = 0
    changelog: str = ""
    verified: bool = False


class ThreatIntelEntry(BaseModel):
    """Tehdit istihbarat kaydi."""

    id: str = Field(
        default_factory=lambda: str(uuid4())[:8],
    )
    indicator_type: str = ""
    indicator_value: str = ""
    severity: ThreatSeverity = (
        ThreatSeverity.MEDIUM
    )
    source: str = ""
    first_seen: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        ),
    )
    active: bool = True
    description: str = ""
