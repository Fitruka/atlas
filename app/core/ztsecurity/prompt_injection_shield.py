"""ATLAS Prompt Enjeksiyon Kalkani modulu.

Cok katmanli prompt enjeksiyon savunmasi.
Bilinen kaliplari regex ile tarama, guven
puanlamasi, toplu tarama, engelleme.
"""

import logging
import re
import time
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    InjectionAttempt,
    InjectionType,
)

logger = logging.getLogger(__name__)

_MAX_PATTERNS = 500
_DEFAULT_THRESHOLD = 0.6

# Bilinen enjeksiyon kaliplari
_INJECTION_PATTERNS: list[
    tuple[str, InjectionType, float]
] = [
    (
        r"ignore\s+(all\s+)?previous\s+instructions",
        InjectionType.JAILBREAK,
        0.95,
    ),
    (
        r"forget\s+(all\s+)?(your\s+)?instructions",
        InjectionType.JAILBREAK,
        0.90,
    ),
    (
        r"you\s+are\s+now\s+(?:a|an)\s+",
        InjectionType.ROLE_HIJACK,
        0.80,
    ),
    (
        r"act\s+as\s+(?:a|an|if)\s+",
        InjectionType.ROLE_HIJACK,
        0.70,
    ),
    (
        r"pretend\s+(?:you\s+are|to\s+be)\s+",
        InjectionType.ROLE_HIJACK,
        0.75,
    ),
    (
        r"system\s*:\s*",
        InjectionType.DIRECT,
        0.85,
    ),
    (
        r"<\s*system\s*>",
        InjectionType.DIRECT,
        0.90,
    ),
    (
        r"\[INST\]",
        InjectionType.DIRECT,
        0.85,
    ),
    (
        r"###\s*(system|instruction|prompt)",
        InjectionType.DIRECT,
        0.80,
    ),
    (
        r"reveal\s+(your\s+)?(system\s+)?prompt",
        InjectionType.DATA_EXFIL,
        0.90,
    ),
    (
        r"show\s+(me\s+)?(your\s+)?instructions",
        InjectionType.DATA_EXFIL,
        0.85,
    ),
    (
        r"output\s+(your\s+)?initial\s+prompt",
        InjectionType.DATA_EXFIL,
        0.92,
    ),
    (
        r"print\s+(your\s+)?(system|hidden)\s+",
        InjectionType.DATA_EXFIL,
        0.88,
    ),
    (
        r"disregard\s+(all\s+)?(prior|above)\s+",
        InjectionType.JAILBREAK,
        0.90,
    ),
    (
        r"override\s+(safety|content)\s+",
        InjectionType.JAILBREAK,
        0.85,
    ),
    (
        r"bypass\s+(filter|restriction|safety)",
        InjectionType.JAILBREAK,
        0.88,
    ),
    (
        r"(?:do\s+not|don'?t)\s+follow\s+(?:your\s+)?rules",
        InjectionType.JAILBREAK,
        0.92,
    ),
    (
        r"execute\s+(?:this\s+)?(?:code|command|script)",
        InjectionType.INDIRECT,
        0.70,
    ),
    (
        r"(?:import|eval|exec)\s*\(",
        InjectionType.INDIRECT,
        0.75,
    ),
    (
        r"base64\s*(?:decode|encode)",
        InjectionType.INDIRECT,
        0.60,
    ),
]


class PromptInjectionShield:
    """Prompt enjeksiyon kalkani.

    Cok katmanli enjeksiyon savunmasi, kalip
    tarama, guven puanlamasi ve engelleme.

    Attributes:
        _patterns: Enjeksiyon kaliplari.
        _blocked: Engellenen girisimlerin listesi.
        _threshold: Engelleme esik degeri.
    """

    def __init__(
        self,
        threshold: float = _DEFAULT_THRESHOLD,
    ) -> None:
        """Kalkani baslatir.

        Args:
            threshold: Engelleme esik degeri.
        """
        self._patterns: list[
            tuple[re.Pattern, InjectionType, float]
        ] = []
        self._blocked: list[InjectionAttempt] = []
        self._scanned: list[InjectionAttempt] = []
        self._threshold = threshold
        self._stats = {
            "total_scans": 0,
            "blocked": 0,
            "safe": 0,
            "patterns_added": 0,
        }

        for pattern_str, inj_type, conf in (
            _INJECTION_PATTERNS
        ):
            self._patterns.append((
                re.compile(pattern_str, re.IGNORECASE),
                inj_type,
                conf,
            ))

        logger.info(
            "PromptInjectionShield baslatildi, "
            "%d kalip yuklendi",
            len(self._patterns),
        )

    def scan(
        self,
        text: str,
        source: str = "",
    ) -> InjectionAttempt:
        """Metni enjeksiyon icin tarar.

        Args:
            text: Taranan metin.
            source: Kaynak bilgisi.

        Returns:
            Enjeksiyon girisimi kaydi.
        """
        self._stats["total_scans"] += 1

        max_confidence = 0.0
        detected_type = InjectionType.DIRECT
        found = False

        normalized = text.strip().lower()

        for pattern, inj_type, base_conf in (
            self._patterns
        ):
            match = pattern.search(normalized)
            if match:
                found = True
                length_factor = min(
                    1.0,
                    len(match.group()) / 20.0,
                )
                confidence = base_conf * (
                    0.7 + 0.3 * length_factor
                )
                if confidence > max_confidence:
                    max_confidence = confidence
                    detected_type = inj_type

        blocked = (
            found
            and max_confidence >= self._threshold
        )

        attempt = InjectionAttempt(
            input_text=text[:500],
            injection_type=detected_type,
            confidence=round(max_confidence, 4),
            blocked=blocked,
            source=source,
        )

        self._scanned.append(attempt)

        if blocked:
            self._blocked.append(attempt)
            self._stats["blocked"] += 1
            logger.warning(
                "Enjeksiyon engellendi: tip=%s "
                "guven=%.2f kaynak=%s",
                detected_type.value,
                max_confidence,
                source,
            )
        else:
            self._stats["safe"] += 1

        return attempt

    def scan_batch(
        self,
        texts: list[str],
        source: str = "",
    ) -> list[InjectionAttempt]:
        """Birden fazla metni toplu tarar.

        Args:
            texts: Taranacak metinler.
            source: Kaynak bilgisi.

        Returns:
            Enjeksiyon girisimi kayitlari.
        """
        results = []
        for text in texts:
            result = self.scan(text, source)
            results.append(result)
        return results

    def add_pattern(
        self,
        pattern: str,
        injection_type: InjectionType = InjectionType.DIRECT,
        confidence: float = 0.80,
    ) -> bool:
        """Yeni enjeksiyon kalibi ekler.

        Args:
            pattern: Regex kalibi.
            injection_type: Enjeksiyon tipi.
            confidence: Temel guven puani.

        Returns:
            Basarili ise True.
        """
        if len(self._patterns) >= _MAX_PATTERNS:
            logger.warning("Kalip kapasitesi dolu")
            return False

        try:
            compiled = re.compile(
                pattern, re.IGNORECASE
            )
            self._patterns.append(
                (compiled, injection_type, confidence)
            )
            self._stats["patterns_added"] += 1
            logger.info(
                "Yeni kalip eklendi: %s", pattern
            )
            return True
        except re.error as e:
            logger.error(
                "Gecersiz regex: %s - %s",
                pattern,
                e,
            )
            return False

    def is_safe(
        self,
        text: str,
    ) -> bool:
        """Metnin guvenli olup olmadigini kontrol eder.

        Args:
            text: Kontrol edilecek metin.

        Returns:
            Guvenli ise True.
        """
        attempt = self.scan(text)
        return not attempt.blocked

    def get_blocked_count(self) -> int:
        """Engellenen girisim sayisini dondurur.

        Returns:
            Engellenen girisim sayisi.
        """
        return len(self._blocked)

    def get_stats(self) -> dict[str, Any]:
        """Kalkan istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "pattern_count": len(self._patterns),
            "threshold": self._threshold,
            "total_scanned": len(self._scanned),
            **self._stats,
        }
