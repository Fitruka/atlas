"""ATLAS Ag Politika Motoru modulu.

Egress/ingress kurallari, SSRF korumasi,
IP araligi filtreleme, politika yonetimi.
"""

import logging
import re
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    NetworkDirection,
    NetworkPolicy,
    PolicyAction,
)

logger = logging.getLogger(__name__)

_MAX_POLICIES = 1000
_DEFAULT_ACTION = PolicyAction.DENY

# Varsayilan engellenen ozel IP araliklari
_DEFAULT_DENIED: list[str] = [
    "127.0.0.0/8",
    "10.0.0.0/8",
    "192.168.0.0/16",
    "172.16.0.0/12",
    "169.254.0.0/16",
    "0.0.0.0/8",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
]

# SSRF icin engellenen URL kaliplari
_SSRF_PATTERNS: list[str] = [
    r"^https?://localhost",
    r"^https?://127\.",
    r"^https?://10\.",
    r"^https?://192\.168\.",
    r"^https?://172\.(1[6-9]|2\d|3[01])\.",
    r"^https?://169\.254\.",
    r"^https?://0\.",
    r"^https?://\[::1\]",
    r"^https?://metadata\.",
    r"^https?://169\.254\.169\.254",
]


class NetworkPolicyEngine:
    """Ag politika motoru.

    Egress/ingress kurallari, SSRF korumasi,
    IP araligi filtreleme ve politika yonetimi.

    Attributes:
        _policies: Kayitli ag politikalari.
        _denied_ranges: Engellenen IP araliklari.
        _ssrf_patterns: SSRF tespit kaliplari.
    """

    def __init__(
        self,
        default_action: PolicyAction = _DEFAULT_ACTION,
    ) -> None:
        """Politika motorunu baslatir.

        Args:
            default_action: Varsayilan politika aksiyonu.
        """
        self._policies: dict[
            str, NetworkPolicy
        ] = {}
        self._denied_ranges = list(
            _DEFAULT_DENIED
        )
        self._default_action = default_action
        self._ssrf_patterns: list[re.Pattern] = [
            re.compile(p, re.IGNORECASE)
            for p in _SSRF_PATTERNS
        ]
        self._stats = {
            "policies_added": 0,
            "policies_removed": 0,
            "evaluations": 0,
            "allowed": 0,
            "denied": 0,
            "ssrf_blocked": 0,
        }

        logger.info(
            "NetworkPolicyEngine baslatildi, "
            "%d engelli aralik, %d SSRF kalibi",
            len(self._denied_ranges),
            len(self._ssrf_patterns),
        )

    def add_policy(
        self,
        name: str,
        direction: NetworkDirection = NetworkDirection.BOTH,
        action: PolicyAction = PolicyAction.ALLOW,
        source_pattern: str = "*",
        dest_pattern: str = "*",
        port_range: str = "",
        protocol: str = "tcp",
    ) -> NetworkPolicy:
        """Yeni ag politikasi ekler.

        Args:
            name: Politika adi.
            direction: Trafik yonu.
            action: Politika aksiyonu.
            source_pattern: Kaynak deseni.
            dest_pattern: Hedef deseni.
            port_range: Port araligi.
            protocol: Protokol.

        Returns:
            Olusturulan politika.
        """
        if len(self._policies) >= _MAX_POLICIES:
            logger.warning("Politika kapasitesi dolu")
            raise ValueError(
                "Politika kapasitesi dolu"
            )

        policy = NetworkPolicy(
            name=name,
            direction=direction,
            action=action,
            source_pattern=source_pattern,
            dest_pattern=dest_pattern,
            port_range=port_range,
            protocol=protocol,
        )

        self._policies[policy.id] = policy
        self._stats["policies_added"] += 1

        logger.info(
            "Ag politikasi eklendi: %s (%s)",
            name,
            policy.id,
        )
        return policy

    def _match_pattern(
        self,
        value: str,
        pattern: str,
    ) -> bool:
        """Degeri desene gore eslestirir.

        Args:
            value: Kontrol edilecek deger.
            pattern: Eslesme deseni.

        Returns:
            Eslesiyor ise True.
        """
        if pattern == "*":
            return True
        if "*" in pattern:
            regex = pattern.replace(
                ".", r"\."
            ).replace("*", ".*")
            return bool(
                re.match(regex, value, re.IGNORECASE)
            )
        return value.lower() == pattern.lower()

    def _check_port(
        self,
        port: int,
        port_range: str,
    ) -> bool:
        """Port araligini kontrol eder.

        Args:
            port: Kontrol edilecek port.
            port_range: Port araligi (orn: '80-443').

        Returns:
            Port aralikta ise True.
        """
        if not port_range:
            return True
        if "-" in port_range:
            parts = port_range.split("-")
            try:
                low = int(parts[0])
                high = int(parts[1])
                return low <= port <= high
            except (ValueError, IndexError):
                return False
        try:
            return port == int(port_range)
        except ValueError:
            return False

    def evaluate(
        self,
        source: str,
        destination: str,
        port: int = 0,
        direction: NetworkDirection = NetworkDirection.EGRESS,
    ) -> PolicyAction:
        """Ag istegini politikalara gore degerlendirir.

        Args:
            source: Kaynak adresi.
            destination: Hedef adresi.
            port: Port numarasi.
            direction: Trafik yonu.

        Returns:
            Uygulanacak politika aksiyonu.
        """
        self._stats["evaluations"] += 1

        for policy in self._policies.values():
            if not policy.enabled:
                continue

            dir_match = (
                policy.direction == direction
                or policy.direction
                == NetworkDirection.BOTH
            )
            if not dir_match:
                continue

            src_match = self._match_pattern(
                source, policy.source_pattern
            )
            dst_match = self._match_pattern(
                destination, policy.dest_pattern
            )
            port_match = self._check_port(
                port, policy.port_range
            )

            if src_match and dst_match and port_match:
                if policy.action == PolicyAction.ALLOW:
                    self._stats["allowed"] += 1
                else:
                    self._stats["denied"] += 1
                return policy.action

        self._stats["denied"] += 1
        return self._default_action

    def check_ssrf(
        self,
        url: str,
    ) -> bool:
        """URL'nin SSRF saldirisi olup olmadigini kontrol eder.

        Args:
            url: Kontrol edilecek URL.

        Returns:
            SSRF girisimi ise True.
        """
        for pattern in self._ssrf_patterns:
            if pattern.search(url):
                self._stats["ssrf_blocked"] += 1
                logger.warning(
                    "SSRF girisimi engellendi: %s",
                    url[:200],
                )
                return True
        return False

    def remove_policy(
        self,
        policy_id: str,
    ) -> bool:
        """Politikayi kaldirir.

        Args:
            policy_id: Politika ID.

        Returns:
            Basarili ise True.
        """
        if policy_id in self._policies:
            del self._policies[policy_id]
            self._stats["policies_removed"] += 1
            logger.info(
                "Politika kaldirildi: %s",
                policy_id,
            )
            return True
        return False

    def list_policies(
        self,
        direction: NetworkDirection | None = None,
    ) -> list[NetworkPolicy]:
        """Politikalari listeler.

        Args:
            direction: Yon filtresi (None = hepsi).

        Returns:
            Politika listesi.
        """
        results = []
        for policy in self._policies.values():
            if direction and (
                policy.direction != direction
            ):
                continue
            results.append(policy)
        return results

    def get_stats(self) -> dict[str, Any]:
        """Motor istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_policies": len(self._policies),
            "active_policies": sum(
                1
                for p in self._policies.values()
                if p.enabled
            ),
            "denied_ranges": len(
                self._denied_ranges
            ),
            "ssrf_patterns": len(
                self._ssrf_patterns
            ),
            "default_action": (
                self._default_action.value
            ),
            **self._stats,
        }
