"""ATLAS Akıllı Özet modülü.

Akıllı günlük/haftalık özetler, öne çıkanlar,
aksiyon gerektiren maddeler, öncelikli raporlama.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.models.proactiveintel_models import (
    AlertPriority,
    DigestEntry,
    DigestFrequency,
    SmartDigestReport,
)

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 2000
_MAX_DIGESTS = 200

_PRIORITY_WEIGHTS = {
    AlertPriority.CRITICAL: 5,
    AlertPriority.HIGH: 4,
    AlertPriority.MEDIUM: 3,
    AlertPriority.LOW: 2,
    AlertPriority.INFO: 1,
}

_FREQUENCY_HOURS = {
    DigestFrequency.HOURLY: 1,
    DigestFrequency.DAILY: 24,
    DigestFrequency.WEEKLY: 168,
    DigestFrequency.MONTHLY: 720,
}


class SmartDigest:
    """Akıllı özet yöneticisi.

    Girdi toplar ve periyodik olarak akıllı
    özetler oluşturur.

    Attributes:
        _entries: Özet girdileri.
        _digests: Üretilen özetler.
    """

    def __init__(self) -> None:
        """Özet yöneticisini başlatır."""
        self._entries: list[DigestEntry] = []
        self._digests: dict[
            str, SmartDigestReport
        ] = {}
        self._stats = {
            "entries_added": 0,
            "digests_generated": 0,
            "action_items_total": 0,
            "entries_cleared": 0,
        }

        logger.info(
            "SmartDigest baslatildi",
        )

    def add_entry(
        self,
        title: str,
        summary: str,
        category: str,
        priority: str = AlertPriority.MEDIUM,
        action_required: bool = False,
        data: dict[str, Any] | None = None,
    ) -> DigestEntry:
        """Özete yeni girdi ekler.

        Args:
            title: Başlık.
            summary: Özet.
            category: Kategori.
            priority: Öncelik.
            action_required: Aksiyon gerekli mi.
            data: Ek veriler.

        Returns:
            Oluşturulan girdi.
        """
        entry = DigestEntry(
            id=str(uuid4())[:8],
            title=title,
            summary=summary,
            category=category,
            priority=priority,
            timestamp=datetime.now(timezone.utc),
            action_required=action_required,
            data=data or {},
        )

        if len(self._entries) >= _MAX_ENTRIES:
            self._entries = self._entries[
                -(_MAX_ENTRIES // 2) :
            ]

        self._entries.append(entry)
        self._stats["entries_added"] += 1

        if action_required:
            self._stats["action_items_total"] += 1

        logger.debug(
            "Ozet girdisi eklendi: %s [%s]",
            title,
            priority,
        )

        return entry

    def generate(
        self,
        frequency: str = DigestFrequency.DAILY,
        recipient: str | None = None,
    ) -> SmartDigestReport:
        """Özet raporu üretir.

        Args:
            frequency: Özet sıklığı.
            recipient: Alıcı.

        Returns:
            Üretilen özet rapor.
        """
        hours = _FREQUENCY_HOURS.get(
            frequency, 24
        )
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(hours=hours)

        period_entries = [
            e
            for e in self._entries
            if e.timestamp >= period_start
        ]

        sorted_entries = sorted(
            period_entries,
            key=lambda e: _PRIORITY_WEIGHTS.get(
                e.priority, 1
            ),
            reverse=True,
        )

        highlights = self._extract_highlights(
            sorted_entries
        )

        entry_dicts = [
            {
                "id": e.id,
                "title": e.title,
                "summary": e.summary,
                "category": e.category,
                "priority": e.priority,
                "action_required": e.action_required,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in sorted_entries
        ]

        report = SmartDigestReport(
            id=str(uuid4())[:8],
            frequency=frequency,
            period_start=period_start,
            period_end=now,
            entries=entry_dicts,
            highlights=highlights,
            generated_at=now,
            recipient=recipient or "",
        )

        if len(self._digests) >= _MAX_DIGESTS:
            oldest = min(
                self._digests,
                key=lambda k: (
                    self._digests[k].generated_at
                ),
            )
            del self._digests[oldest]

        self._digests[report.id] = report
        self._stats["digests_generated"] += 1

        logger.info(
            "Ozet rapor uretildi: %s (%d girdi)",
            frequency,
            len(sorted_entries),
        )

        return report

    def _extract_highlights(
        self, entries: list[DigestEntry]
    ) -> list[str]:
        """Öne çıkan maddeleri çıkarır.

        Args:
            entries: Sıralı girdiler.

        Returns:
            Öne çıkan maddeler listesi.
        """
        highlights: list[str] = []

        critical = [
            e
            for e in entries
            if e.priority == AlertPriority.CRITICAL
        ]
        if critical:
            highlights.append(
                f"{len(critical)} kritik madde var"
            )

        actions = [
            e
            for e in entries
            if e.action_required
        ]
        if actions:
            highlights.append(
                f"{len(actions)} aksiyon gerektiren madde"
            )

        categories: dict[str, int] = {}
        for e in entries:
            categories[e.category] = (
                categories.get(e.category, 0) + 1
            )

        if categories:
            top_cat = max(
                categories,
                key=lambda k: categories[k],
            )
            highlights.append(
                f"En yogun kategori: {top_cat} "
                f"({categories[top_cat]} madde)"
            )

        for e in entries[:3]:
            highlights.append(
                f"[{e.priority.upper()}] {e.title}"
            )

        return highlights[:10]

    def get_highlights(
        self,
        frequency: str = "daily",
        limit: int = 5,
    ) -> list[str]:
        """Öne çıkan maddeleri döndürür.

        Args:
            frequency: Sıklık.
            limit: Maksimum madde sayısı.

        Returns:
            Öne çıkan maddeler.
        """
        hours = _FREQUENCY_HOURS.get(frequency, 24)
        cutoff = datetime.now(
            timezone.utc
        ) - timedelta(hours=hours)

        entries = [
            e
            for e in self._entries
            if e.timestamp >= cutoff
        ]

        sorted_entries = sorted(
            entries,
            key=lambda e: _PRIORITY_WEIGHTS.get(
                e.priority, 1
            ),
            reverse=True,
        )

        return [
            f"[{e.priority.upper()}] {e.title}: "
            f"{e.summary[:80]}"
            for e in sorted_entries[:limit]
        ]

    def get_action_items(self) -> list[DigestEntry]:
        """Aksiyon gerektiren girdileri döndürür.

        Returns:
            Aksiyon gerektiren girdi listesi.
        """
        return [
            e
            for e in self._entries
            if e.action_required
        ]

    def get_digest(
        self, digest_id: str
    ) -> SmartDigestReport | None:
        """Belirli özet raporunu döndürür.

        Args:
            digest_id: Özet ID.

        Returns:
            Özet rapor veya None.
        """
        return self._digests.get(digest_id)

    def list_digests(
        self, frequency: str | None = None
    ) -> list[SmartDigestReport]:
        """Özet raporlarını listeler.

        Args:
            frequency: Sıklık filtresi.

        Returns:
            Özet rapor listesi.
        """
        digests = list(self._digests.values())

        if frequency:
            digests = [
                d
                for d in digests
                if d.frequency == frequency
            ]

        return sorted(
            digests,
            key=lambda d: d.generated_at,
            reverse=True,
        )

    def clear_entries(self) -> int:
        """Tüm girdileri temizler.

        Returns:
            Temizlenen girdi sayısı.
        """
        count = len(self._entries)
        self._entries.clear()
        self._stats["entries_cleared"] += count

        logger.info(
            "%d girdi temizlendi", count
        )

        return count

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        return {
            **self._stats,
            "current_entries": len(self._entries),
            "total_digests": len(self._digests),
            "pending_actions": sum(
                1
                for e in self._entries
                if e.action_required
            ),
        }
