"""ATLAS Zero-Trust Security Orkestrator modulu.

Tam guvenlik pipeline'i: Authenticate -> Authorize ->
Scan -> Verify -> Log. Tum guvenlik bilesenlerini
koordine eder.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any

from app.core.ztsecurity.audit_trail import (
    AuditTrail,
)
from app.core.ztsecurity.encrypted_credential_vault import (
    EncryptedCredentialVault,
)
from app.core.ztsecurity.memory_poison_detector import (
    MemoryPoisonDetector,
)
from app.core.ztsecurity.network_policy_engine import (
    NetworkPolicyEngine,
)
from app.core.ztsecurity.prompt_injection_shield import (
    PromptInjectionShield,
)
from app.core.ztsecurity.secure_update_chain import (
    SecureUpdateChain,
)
from app.core.ztsecurity.skill_sandbox_verifier import (
    SkillSandboxVerifier,
)
from app.core.ztsecurity.threat_intel_feed import (
    ThreatIntelFeed,
)
from app.core.ztsecurity.zero_trust_gateway import (
    ZeroTrustGateway,
)
from app.models.ztsecurity_models import (
    NetworkDirection,
    PolicyAction,
    ZTSTrustLevel,
)

logger = logging.getLogger(__name__)

_VERSION = "1.0.0"


class ZeroTrustSecurityOrchestrator:
    """Zero-Trust Security Orkestrator.

    Tum guvenlik bilesenlerini koordine eden
    merkezi orkestrator. Authenticate -> Authorize ->
    Scan -> Verify -> Log pipeline'i.

    Attributes:
        vault: Sifrelenmis kimlik kasasi.
        shield: Prompt enjeksiyon kalkani.
        sandbox: Skill sandbox dogrulayici.
        network: Ag politika motoru.
        gateway: Zero Trust gateway.
        poison_detector: Hafiza zehirleme tespitcisi.
        audit: Denetim izi.
        updates: Guvenli guncelleme zinciri.
        threat_intel: Tehdit istihbarat beslemesi.
    """

    def __init__(
        self,
        master_key: str = "atlas-vault-master-key",
        injection_threshold: float = 0.6,
        default_min_trust: ZTSTrustLevel = ZTSTrustLevel.MEDIUM,
    ) -> None:
        """Orkestratoru baslatir.

        Args:
            master_key: Kasa ana anahtari.
            injection_threshold: Enjeksiyon esigi.
            default_min_trust: Varsayilan min guven.
        """
        self.vault = EncryptedCredentialVault(
            master_key=master_key,
        )
        self.shield = PromptInjectionShield(
            threshold=injection_threshold,
        )
        self.sandbox = SkillSandboxVerifier()
        self.network = NetworkPolicyEngine()
        self.gateway = ZeroTrustGateway(
            default_min_trust=default_min_trust,
        )
        self.poison_detector = (
            MemoryPoisonDetector()
        )
        self.audit = AuditTrail()
        self.updates = SecureUpdateChain()
        self.threat_intel = ThreatIntelFeed()

        self._stats = {
            "requests_processed": 0,
            "skills_verified": 0,
            "security_scans": 0,
            "threats_blocked": 0,
            "summaries_generated": 0,
        }

        logger.info(
            "ZeroTrustSecurityOrchestrator "
            "baslatildi (v%s)",
            _VERSION,
        )

    def process_request(
        self,
        source: str,
        destination: str,
        method: str = "GET",
        credentials: str | None = None,
        input_text: str | None = None,
    ) -> dict[str, Any]:
        """Istegi tam guvenlik pipeline'indan gecirir.

        Pipeline: ThreatCheck -> NetworkCheck ->
        Authenticate -> Authorize -> InjectionScan -> Log

        Args:
            source: Kaynak.
            destination: Hedef.
            method: HTTP metodu.
            credentials: Kimlik bilgisi.
            input_text: Girdi metni (taranacak).

        Returns:
            Islem sonucu sozlugu.
        """
        start = time.time()
        self._stats["requests_processed"] += 1

        result: dict[str, Any] = {
            "source": source,
            "destination": destination,
            "method": method,
            "allowed": False,
            "checks": {},
        }

        # 1. Tehdit istihbarat kontrolu
        source_threat = self.threat_intel.check(
            source
        )
        dest_threat = self.threat_intel.check(
            destination
        )

        if source_threat or dest_threat:
            self._stats["threats_blocked"] += 1
            result["checks"]["threat_intel"] = {
                "passed": False,
                "source_threat": bool(
                    source_threat
                ),
                "dest_threat": bool(dest_threat),
            }
            self.audit.record(
                actor=source,
                action="request_blocked",
                resource=destination,
                trust_level=ZTSTrustLevel.NONE,
                result="threat_detected",
            )
            result["elapsed_ms"] = round(
                (time.time() - start) * 1000, 2
            )
            return result

        result["checks"]["threat_intel"] = {
            "passed": True,
        }

        # 2. Ag politikasi kontrolu
        ssrf = self.network.check_ssrf(
            destination
        )
        if ssrf:
            self._stats["threats_blocked"] += 1
            result["checks"]["network"] = {
                "passed": False,
                "reason": "SSRF detected",
            }
            self.audit.record(
                actor=source,
                action="ssrf_blocked",
                resource=destination,
                trust_level=ZTSTrustLevel.NONE,
                result="blocked",
            )
            result["elapsed_ms"] = round(
                (time.time() - start) * 1000, 2
            )
            return result

        net_action = self.network.evaluate(
            source=source,
            destination=destination,
            direction=NetworkDirection.EGRESS,
        )
        result["checks"]["network"] = {
            "passed": net_action
            == PolicyAction.ALLOW,
            "action": net_action.value,
        }

        # 3. Gateway: kimlik dogrulama + yetkilendirme
        gw_request = self.gateway.process_request(
            source=source,
            destination=destination,
            method=method,
            credentials=credentials,
        )
        result["checks"]["gateway"] = {
            "passed": gw_request.allowed,
            "trust_level": (
                gw_request.trust_level.value
            ),
            "authenticated": (
                gw_request.authenticated
            ),
        }

        if not gw_request.allowed:
            self.audit.record(
                actor=source,
                action="request_denied",
                resource=destination,
                trust_level=gw_request.trust_level,
                result="unauthorized",
            )
            result["elapsed_ms"] = round(
                (time.time() - start) * 1000, 2
            )
            return result

        # 4. Prompt enjeksiyon tarami
        injection_result = None
        if input_text:
            attempt = self.shield.scan(
                input_text, source=source
            )
            injection_result = {
                "passed": not attempt.blocked,
                "injection_type": (
                    attempt.injection_type.value
                ),
                "confidence": attempt.confidence,
            }
            result["checks"]["injection"] = (
                injection_result
            )

            if attempt.blocked:
                self._stats[
                    "threats_blocked"
                ] += 1
                self.audit.record(
                    actor=source,
                    action="injection_blocked",
                    resource=destination,
                    trust_level=(
                        gw_request.trust_level
                    ),
                    result="blocked",
                )
                result["elapsed_ms"] = round(
                    (time.time() - start) * 1000,
                    2,
                )
                return result

        # 5. Tum kontroller basarili
        result["allowed"] = True
        self.audit.record(
            actor=source,
            action="request_allowed",
            resource=destination,
            trust_level=gw_request.trust_level,
            result="success",
        )

        result["elapsed_ms"] = round(
            (time.time() - start) * 1000, 2
        )
        return result

    def verify_skill(
        self,
        skill_id: str,
        skill_name: str,
        code_content: str,
    ) -> dict[str, Any]:
        """Skill'i guvenlik dogrulamasinden gecirir.

        Args:
            skill_id: Skill kimlik numarasi.
            skill_name: Skill adi.
            code_content: Skill kodu.

        Returns:
            Dogrulama sonucu sozlugu.
        """
        start = time.time()
        self._stats["skills_verified"] += 1

        # Tehdit istihbarat kontrolu
        threat = self.threat_intel.check(
            skill_name
        )
        if threat:
            self._stats["threats_blocked"] += 1
            self.audit.record(
                actor="system",
                action="skill_blocked_threat",
                resource=skill_name,
                trust_level=ZTSTrustLevel.NONE,
                result="known_threat",
            )
            return {
                "skill_id": skill_id,
                "skill_name": skill_name,
                "approved": False,
                "reason": "known_threat",
                "threat_severity": (
                    threat.severity.value
                ),
                "elapsed_ms": round(
                    (time.time() - start) * 1000,
                    2,
                ),
            }

        # Sandbox dogrulama
        sandbox_result = self.sandbox.verify(
            skill_id, skill_name, code_content
        )

        approved = sandbox_result.status.value == (
            "passed"
        )

        self.audit.record(
            actor="system",
            action=(
                "skill_approved"
                if approved
                else "skill_rejected"
            ),
            resource=skill_name,
            trust_level=(
                ZTSTrustLevel.HIGH
                if approved
                else ZTSTrustLevel.NONE
            ),
            result=sandbox_result.status.value,
        )

        return {
            "skill_id": skill_id,
            "skill_name": skill_name,
            "approved": approved,
            "status": sandbox_result.status.value,
            "threats_found": (
                sandbox_result.threats_found
            ),
            "execution_time": (
                sandbox_result.execution_time
            ),
            "elapsed_ms": round(
                (time.time() - start) * 1000, 2
            ),
        }

    def security_scan(
        self,
        text: str,
        source: str = "",
    ) -> dict[str, Any]:
        """Metni guvenlik taramisindan gecirir.

        Args:
            text: Taranacak metin.
            source: Kaynak bilgisi.

        Returns:
            Tarama sonucu sozlugu.
        """
        self._stats["security_scans"] += 1

        # Enjeksiyon tarami
        attempt = self.shield.scan(
            text, source=source
        )

        # Tehdit kontrolu
        words = text.split()
        threats_found = []
        for word in words:
            clean = word.strip(".,!?;:\"'()[]{}").lower()
            if len(clean) > 3:
                threat = self.threat_intel.check(
                    clean
                )
                if threat:
                    threats_found.append({
                        "value": clean,
                        "type": (
                            threat.indicator_type
                        ),
                        "severity": (
                            threat.severity.value
                        ),
                    })

        is_safe = (
            not attempt.blocked
            and not threats_found
        )

        if not is_safe:
            self._stats["threats_blocked"] += 1

        return {
            "is_safe": is_safe,
            "injection": {
                "blocked": attempt.blocked,
                "type": (
                    attempt.injection_type.value
                ),
                "confidence": attempt.confidence,
            },
            "threats": threats_found,
            "source": source,
        }

    def get_security_summary(
        self,
    ) -> dict[str, Any]:
        """Genel guvenlik ozetini dondurur.

        Returns:
            Guvenlik ozet sozlugu.
        """
        self._stats["summaries_generated"] += 1

        return {
            "version": _VERSION,
            "vault": self.vault.get_stats(),
            "shield": self.shield.get_stats(),
            "sandbox": self.sandbox.get_stats(),
            "network": self.network.get_stats(),
            "gateway": self.gateway.get_stats(),
            "poison_detector": (
                self.poison_detector.get_stats()
            ),
            "audit": self.audit.get_stats(),
            "updates": self.updates.get_stats(),
            "threat_intel": (
                self.threat_intel.get_stats()
            ),
            "orchestrator": dict(self._stats),
        }

    def get_stats(self) -> dict[str, Any]:
        """Orkestrator istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "version": _VERSION,
            "components": 9,
            "vault_credentials": (
                self.vault.get_stats()[
                    "total_credentials"
                ]
            ),
            "shield_scans": (
                self.shield.get_stats()[
                    "total_scans"
                ]
            ),
            "sandbox_verified": (
                self.sandbox.get_stats()["verified"]
            ),
            "gateway_requests": (
                self.gateway.get_stats()[
                    "total_requests"
                ]
            ),
            "audit_entries": (
                self.audit.get_stats()[
                    "total_entries"
                ]
            ),
            "active_threats": (
                self.threat_intel.get_stats()[
                    "active_indicators"
                ]
            ),
            **self._stats,
        }
