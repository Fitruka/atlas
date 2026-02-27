"""ATLAS Tehdit Istihbarat Beslemesi modulu.

Bilinen zararli skill, IP, domain takibi.
Tehdit gostergesi ekleme, sorgulama,
deaktivasyon ve besleme yenileme.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    ThreatIntelEntry,
    ThreatSeverity,
)

logger = logging.getLogger(__name__)

_MAX_INDICATORS = 50000
_DEFAULT_SEVERITY = ThreatSeverity.MEDIUM

# Baslangic tehdit gostergeleri
_SEED_INDICATORS: list[
    tuple[str, str, ThreatSeverity, str]
] = [
    (
        "ip",
        "192.0.2.1",
        ThreatSeverity.HIGH,
        "Bilinen C2 sunucusu",
    ),
    (
        "domain",
        "malware-distribution.example.com",
        ThreatSeverity.CRITICAL,
        "Malware dagitim alani",
    ),
    (
        "domain",
        "phishing-site.example.org",
        ThreatSeverity.HIGH,
        "Phishing sitesi",
    ),
    (
        "hash",
        "e3b0c44298fc1c149afbf4c8996fb924",
        ThreatSeverity.MEDIUM,
        "Bilinen zararli dosya hash'i",
    ),
    (
        "ip",
        "198.51.100.0",
        ThreatSeverity.MEDIUM,
        "Brute-force kaynak IP",
    ),
    (
        "skill",
        "backdoor-installer",
        ThreatSeverity.CRITICAL,
        "Arka kapi yukleyici skill",
    ),
    (
        "skill",
        "data-exfiltrator",
        ThreatSeverity.CRITICAL,
        "Veri sizdirma skill'i",
    ),
    (
        "domain",
        "crypto-miner.example.net",
        ThreatSeverity.HIGH,
        "Kripto madenciligi alani",
    ),
]


class ThreatIntelFeed:
    """Tehdit istihbarat beslemesi.

    Bilinen zararli skill, IP, domain takibi.
    Gosterge ekleme, sorgulama ve yenileme.

    Attributes:
        _indicators: Tehdit gostergeleri.
        _index: Deger bazli hizli arama indeksi.
    """

    def __init__(
        self,
        load_seed: bool = True,
    ) -> None:
        """Beslemeyi baslatir.

        Args:
            load_seed: Baslangic verileri yuklensin mi.
        """
        self._indicators: dict[
            str, ThreatIntelEntry
        ] = {}
        self._index: dict[
            str, str
        ] = {}
        self._stats = {
            "added": 0,
            "checked": 0,
            "hits": 0,
            "misses": 0,
            "deactivated": 0,
            "refreshed": 0,
        }

        if load_seed:
            self._load_seed_data()

        logger.info(
            "ThreatIntelFeed baslatildi, "
            "%d gosterge yuklendi",
            len(self._indicators),
        )

    def _load_seed_data(self) -> None:
        """Baslangic tehdit verilerini yukler."""
        for (
            ind_type,
            ind_value,
            severity,
            desc,
        ) in _SEED_INDICATORS:
            self.add_indicator(
                indicator_type=ind_type,
                indicator_value=ind_value,
                severity=severity,
                source="seed",
                description=desc,
            )

    def add_indicator(
        self,
        indicator_type: str,
        indicator_value: str,
        severity: ThreatSeverity = _DEFAULT_SEVERITY,
        source: str = "",
        description: str = "",
    ) -> ThreatIntelEntry:
        """Yeni tehdit gostergesi ekler.

        Args:
            indicator_type: Gosterge tipi (ip, domain, hash, skill).
            indicator_value: Gosterge degeri.
            severity: Tehdit siddeti.
            source: Kaynak bilgisi.
            description: Aciklama.

        Returns:
            Olusturulan tehdit gostergesi.
        """
        if len(self._indicators) >= _MAX_INDICATORS:
            logger.warning(
                "Gosterge kapasitesi dolu"
            )
            raise ValueError(
                "Gosterge kapasitesi dolu"
            )

        existing_id = self._index.get(
            indicator_value.lower()
        )
        if existing_id:
            existing = self._indicators.get(
                existing_id
            )
            if existing:
                existing.last_seen = datetime.now(
                    timezone.utc
                )
                existing.active = True
                if (
                    self._severity_value(severity)
                    > self._severity_value(
                        existing.severity
                    )
                ):
                    existing.severity = severity
                return existing

        entry = ThreatIntelEntry(
            indicator_type=indicator_type,
            indicator_value=indicator_value,
            severity=severity,
            source=source,
            description=description,
        )

        self._indicators[entry.id] = entry
        self._index[
            indicator_value.lower()
        ] = entry.id
        self._stats["added"] += 1

        logger.debug(
            "Tehdit gostergesi eklendi: %s=%s "
            "(siddet: %s)",
            indicator_type,
            indicator_value,
            severity.value,
        )
        return entry

    def _severity_value(
        self,
        severity: ThreatSeverity,
    ) -> int:
        """Siddet seviyesini sayisal degere cevirir.

        Args:
            severity: Tehdit siddeti.

        Returns:
            Sayisal deger (0-4).
        """
        mapping = {
            ThreatSeverity.INFO: 0,
            ThreatSeverity.LOW: 1,
            ThreatSeverity.MEDIUM: 2,
            ThreatSeverity.HIGH: 3,
            ThreatSeverity.CRITICAL: 4,
        }
        return mapping.get(severity, 0)

    def check(
        self,
        value: str,
    ) -> ThreatIntelEntry | None:
        """Degerin tehdit olup olmadigini kontrol eder.

        Args:
            value: Kontrol edilecek deger.

        Returns:
            Tehdit gostergesi veya None.
        """
        self._stats["checked"] += 1

        indicator_id = self._index.get(
            value.lower()
        )
        if indicator_id:
            entry = self._indicators.get(
                indicator_id
            )
            if entry and entry.active:
                self._stats["hits"] += 1
                logger.info(
                    "Tehdit tespit edildi: %s "
                    "(siddet: %s)",
                    value,
                    entry.severity.value,
                )
                return entry

        self._stats["misses"] += 1
        return None

    def is_known_threat(
        self,
        value: str,
    ) -> bool:
        """Degerin bilinen tehdit olup olmadigini kontrol eder.

        Args:
            value: Kontrol edilecek deger.

        Returns:
            Bilinen tehdit ise True.
        """
        result = self.check(value)
        return result is not None

    def deactivate(
        self,
        indicator_id: str,
    ) -> bool:
        """Tehdit gostergesini deaktive eder.

        Args:
            indicator_id: Gosterge ID.

        Returns:
            Basarili ise True.
        """
        entry = self._indicators.get(indicator_id)
        if not entry:
            return False

        entry.active = False
        self._stats["deactivated"] += 1

        logger.info(
            "Gosterge deaktive edildi: %s (%s)",
            entry.indicator_value,
            indicator_id,
        )
        return True

    def get_active_threats(
        self,
        severity: ThreatSeverity | None = None,
    ) -> list[ThreatIntelEntry]:
        """Aktif tehdit gostergelerini listeler.

        Args:
            severity: Siddet filtresi (None = hepsi).

        Returns:
            Aktif tehdit gostergeleri.
        """
        results = []
        for entry in self._indicators.values():
            if not entry.active:
                continue
            if (
                severity
                and entry.severity != severity
            ):
                continue
            results.append(entry)

        results.sort(
            key=lambda e: self._severity_value(
                e.severity
            ),
            reverse=True,
        )
        return results

    def refresh_feed(self) -> int:
        """Beslemeyi yeniler (simule edilmis).

        Returns:
            Guncellenen gosterge sayisi.
        """
        self._stats["refreshed"] += 1
        updated = 0

        for entry in self._indicators.values():
            if entry.active:
                entry.last_seen = datetime.now(
                    timezone.utc
                )
                updated += 1

        logger.info(
            "Besleme yenilendi: %d gosterge "
            "guncellendi",
            updated,
        )
        return updated

    def get_stats(self) -> dict[str, Any]:
        """Besleme istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        active_count = sum(
            1
            for e in self._indicators.values()
            if e.active
        )
        severity_dist: dict[str, int] = {}
        for entry in self._indicators.values():
            if entry.active:
                key = entry.severity.value
                severity_dist[key] = (
                    severity_dist.get(key, 0) + 1
                )

        return {
            "total_indicators": len(
                self._indicators
            ),
            "active_indicators": active_count,
            "severity_distribution": severity_dist,
            **self._stats,
        }
