"""ATLAS Proaktif İstihbarat Rakip Takipçisi modülü.

Rakip değişikliklerini izleme, olay kaydetme,
rekabet analizi ve rakip profili yönetimi.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.proactiveintel_models import (
    CompetitorAction,
    CompetitorEvent,
)

logger = logging.getLogger(__name__)

_MAX_EVENTS = 1000
_MAX_COMPETITORS = 200


class PICompetitorTracker:
    """Proaktif rakip takipçisi.

    Rakiplerin hareketlerini izler ve önemli
    değişiklikleri kaydeder.

    Attributes:
        _competitors: Kayıtlı rakipler.
        _events: Rakip olayları.
    """

    def __init__(self) -> None:
        """Rakip takipçisini başlatır."""
        self._competitors: dict[
            str, dict[str, Any]
        ] = {}
        self._events: list[CompetitorEvent] = []
        self._stats = {
            "competitors_tracked": 0,
            "events_recorded": 0,
            "high_impact_events": 0,
            "competitors_removed": 0,
        }

        logger.info(
            "PICompetitorTracker baslatildi",
        )

    def add_competitor(
        self,
        name: str,
        domain: str | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Yeni rakip ekler.

        Args:
            name: Rakip adı.
            domain: Web domain.
            tags: Etiketler.

        Returns:
            Rakip ID.
        """
        if name in self._competitors:
            return self._competitors[name]["id"]

        if len(self._competitors) >= _MAX_COMPETITORS:
            logger.warning(
                "Maksimum rakip sayisina ulasildi"
            )
            return ""

        comp_id = str(uuid4())[:8]

        self._competitors[name] = {
            "id": comp_id,
            "name": name,
            "domain": domain or "",
            "tags": tags or [],
            "added_at": time.time(),
            "event_count": 0,
            "last_event": None,
        }

        self._stats["competitors_tracked"] += 1

        logger.info(
            "Rakip eklendi: %s", name
        )

        return comp_id

    def record_event(
        self,
        competitor_name: str,
        action: str,
        description: str,
        source_url: str | None = None,
        impact_level: str = "medium",
    ) -> CompetitorEvent:
        """Rakip olayı kaydeder.

        Args:
            competitor_name: Rakip adı.
            action: Aksiyon tipi.
            description: Olay açıklaması.
            source_url: Kaynak URL.
            impact_level: Etki seviyesi.

        Returns:
            Oluşturulan olay kaydı.
        """
        if competitor_name not in self._competitors:
            self.add_competitor(competitor_name)

        event = CompetitorEvent(
            id=str(uuid4())[:8],
            competitor_name=competitor_name,
            action=action,
            description=description,
            detected_at=datetime.now(timezone.utc),
            impact_level=impact_level,
            source_url=source_url or "",
        )

        if len(self._events) >= _MAX_EVENTS:
            self._events = self._events[
                -(_MAX_EVENTS // 2) :
            ]

        self._events.append(event)
        self._stats["events_recorded"] += 1

        if impact_level in ("high", "critical"):
            self._stats["high_impact_events"] += 1

        comp = self._competitors.get(
            competitor_name
        )
        if comp:
            comp["event_count"] += 1
            comp["last_event"] = time.time()

        logger.info(
            "Rakip olayi kaydedildi: %s - %s",
            competitor_name,
            action,
        )

        return event

    def get_events(
        self,
        competitor_name: str | None = None,
        action: str | None = None,
        days: int = 30,
    ) -> list[CompetitorEvent]:
        """Olayları filtreli döndürür.

        Args:
            competitor_name: Rakip adı filtresi.
            action: Aksiyon tipi filtresi.
            days: Son kaç gün.

        Returns:
            Olay listesi.
        """
        cutoff = datetime.now(
            timezone.utc
        ).timestamp() - (days * 86400)

        results = [
            e
            for e in self._events
            if e.detected_at.timestamp() >= cutoff
        ]

        if competitor_name:
            results = [
                e
                for e in results
                if e.competitor_name == competitor_name
            ]

        if action:
            results = [
                e
                for e in results
                if e.action == action
            ]

        return sorted(
            results,
            key=lambda e: e.detected_at,
            reverse=True,
        )

    def get_competitor_summary(
        self, competitor_name: str
    ) -> dict[str, Any]:
        """Rakip özet bilgisini döndürür.

        Args:
            competitor_name: Rakip adı.

        Returns:
            Özet bilgi sözlüğü.
        """
        comp = self._competitors.get(
            competitor_name
        )
        if not comp:
            return {"error": "competitor_not_found"}

        events = [
            e
            for e in self._events
            if e.competitor_name == competitor_name
        ]

        action_counts: dict[str, int] = {}
        for event in events:
            action_counts[event.action] = (
                action_counts.get(event.action, 0) + 1
            )

        recent = sorted(
            events,
            key=lambda e: e.detected_at,
            reverse=True,
        )[:5]

        return {
            "name": competitor_name,
            "domain": comp.get("domain", ""),
            "tags": comp.get("tags", []),
            "total_events": len(events),
            "action_breakdown": action_counts,
            "recent_events": [
                {
                    "action": e.action,
                    "description": e.description,
                    "impact": e.impact_level,
                    "date": e.detected_at.isoformat(),
                }
                for e in recent
            ],
            "tracked_since": comp.get("added_at"),
        }

    def list_competitors(self) -> list[dict[str, Any]]:
        """Tüm rakipleri listeler.

        Returns:
            Rakip listesi.
        """
        return [
            {
                "id": c["id"],
                "name": c["name"],
                "domain": c.get("domain", ""),
                "tags": c.get("tags", []),
                "event_count": c.get("event_count", 0),
            }
            for c in self._competitors.values()
        ]

    def get_recent_activity(
        self, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Son aktiviteleri döndürür.

        Args:
            limit: Maksimum sonuç sayısı.

        Returns:
            Aktivite listesi.
        """
        sorted_events = sorted(
            self._events,
            key=lambda e: e.detected_at,
            reverse=True,
        )[:limit]

        return [
            {
                "id": e.id,
                "competitor": e.competitor_name,
                "action": e.action,
                "description": e.description,
                "impact": e.impact_level,
                "detected_at": e.detected_at.isoformat(),
                "verified": e.verified,
            }
            for e in sorted_events
        ]

    def remove_competitor(
        self, name: str
    ) -> bool:
        """Rakibi kaldırır.

        Args:
            name: Rakip adı.

        Returns:
            Başarılı ise True.
        """
        if name not in self._competitors:
            return False

        del self._competitors[name]
        self._events = [
            e
            for e in self._events
            if e.competitor_name != name
        ]
        self._stats["competitors_removed"] += 1

        logger.info(
            "Rakip kaldirildi: %s", name
        )

        return True

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        return {
            **self._stats,
            "active_competitors": len(
                self._competitors
            ),
            "total_events": len(self._events),
        }
