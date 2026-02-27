"""ATLAS Proaktif İstihbarat Fırsat Tespitçisi modülü.

İş fırsatlarını otomatik tespit etme, maliyet tasarrufu,
gelir, verimlilik ve büyüme fırsatları analizi.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.proactiveintel_models import (
    OpportunityRecord,
    OpportunityType,
)

logger = logging.getLogger(__name__)

_MAX_OPPORTUNITIES = 500
_DEFAULT_MIN_CONFIDENCE = 0.3


class PIOpportunityDetector:
    """Proaktif fırsat tespitçisi.

    Çeşitli veri kaynaklarını tarayarak iş
    fırsatlarını otomatik olarak tespit eder.

    Attributes:
        _opportunities: Tespit edilen fırsatlar.
        _dismissed: Reddedilen fırsat IDleri.
    """

    def __init__(self) -> None:
        """Fırsat tespitçisini başlatır."""
        self._opportunities: dict[
            str, OpportunityRecord
        ] = {}
        self._dismissed: set[str] = set()
        self._acted: dict[str, dict[str, Any]] = {}
        self._stats = {
            "opportunities_detected": 0,
            "cost_savings_found": 0,
            "revenue_found": 0,
            "efficiency_found": 0,
            "dismissed": 0,
            "acted_on": 0,
        }

        logger.info(
            "PIOpportunityDetector baslatildi",
        )

    def scan(
        self,
        data_sources: dict[str, Any],
    ) -> list[OpportunityRecord]:
        """Veri kaynaklarını tarayarak fırsat arar.

        Args:
            data_sources: Taranacak veri kaynakları.

        Returns:
            Tespit edilen fırsatlar listesi.
        """
        found: list[OpportunityRecord] = []

        costs = data_sources.get("costs")
        benchmarks = data_sources.get("benchmarks")
        if costs and benchmarks:
            opp = self.detect_cost_saving(
                costs, benchmarks
            )
            if opp:
                found.append(opp)

        market = data_sources.get("market_data")
        if market:
            opp = self.detect_revenue(market)
            if opp:
                found.append(opp)

        processes = data_sources.get(
            "process_metrics"
        )
        if processes:
            opp = self.detect_efficiency(processes)
            if opp:
                found.append(opp)

        growth = data_sources.get("growth_data")
        if growth:
            opp = self._detect_growth(growth)
            if opp:
                found.append(opp)

        logger.info(
            "Tarama tamamlandi: %d firsat bulundu",
            len(found),
        )

        return found

    def detect_cost_saving(
        self,
        current_costs: dict[str, float],
        benchmarks: dict[str, float],
    ) -> OpportunityRecord | None:
        """Maliyet tasarrufu fırsatı tespit eder.

        Args:
            current_costs: Mevcut maliyetler.
            benchmarks: Kıyaslama değerleri.

        Returns:
            Fırsat kaydı veya None.
        """
        savings: list[tuple[str, float]] = []

        for item, cost in current_costs.items():
            bench = benchmarks.get(item)
            if bench and cost > bench:
                savings.append(
                    (item, cost - bench)
                )

        if not savings:
            return None

        total_saving = sum(s[1] for s in savings)
        top_items = sorted(
            savings, key=lambda x: x[1], reverse=True
        )[:3]

        items_desc = ", ".join(
            f"{name} ({val:.2f})"
            for name, val in top_items
        )

        opp = OpportunityRecord(
            id=str(uuid4())[:8],
            opportunity_type=OpportunityType.COST_SAVING,
            title="Maliyet tasarrufu firsati",
            description=(
                f"{len(savings)} kalemde tasarruf "
                f"mumkun: {items_desc}"
            ),
            estimated_value=total_saving,
            confidence=min(
                0.9, 0.5 + len(savings) * 0.05
            ),
            source="cost_analysis",
        )

        self._store_opportunity(opp)
        self._stats["cost_savings_found"] += 1

        return opp

    def detect_revenue(
        self,
        market_data: dict[str, Any],
    ) -> OpportunityRecord | None:
        """Gelir fırsatı tespit eder.

        Args:
            market_data: Pazar verileri.

        Returns:
            Fırsat kaydı veya None.
        """
        demand = market_data.get("demand_growth", 0)
        gap = market_data.get("market_gap", 0)
        segment = market_data.get("segment", "genel")

        if demand <= 0 and gap <= 0:
            return None

        estimated = (
            demand * 1000 + gap * 500
        )
        confidence = min(
            0.85, 0.4 + demand * 0.1 + gap * 0.05
        )

        opp = OpportunityRecord(
            id=str(uuid4())[:8],
            opportunity_type=OpportunityType.REVENUE,
            title=f"{segment} gelir firsati",
            description=(
                f"{segment} segmentinde talep "
                f"artisi: {demand:.1f}%, "
                f"pazar bosluğu: {gap:.1f}%"
            ),
            estimated_value=estimated,
            confidence=confidence,
            source="market_analysis",
        )

        self._store_opportunity(opp)
        self._stats["revenue_found"] += 1

        return opp

    def detect_efficiency(
        self,
        process_metrics: dict[str, Any],
    ) -> OpportunityRecord | None:
        """Verimlilik fırsatı tespit eder.

        Args:
            process_metrics: Süreç metrikleri.

        Returns:
            Fırsat kaydı veya None.
        """
        bottlenecks = process_metrics.get(
            "bottlenecks", []
        )
        utilization = process_metrics.get(
            "utilization", 1.0
        )
        waste = process_metrics.get("waste", 0.0)

        if not bottlenecks and waste <= 0.05:
            return None

        improvement = waste * 100 + len(bottlenecks) * 5
        estimated_value = improvement * 200

        opp = OpportunityRecord(
            id=str(uuid4())[:8],
            opportunity_type=OpportunityType.EFFICIENCY,
            title="Verimlilik iyilestirme firsati",
            description=(
                f"{len(bottlenecks)} darboğaz, "
                f"kaynak kullanimi: {utilization:.0%}, "
                f"israf orani: {waste:.0%}"
            ),
            estimated_value=estimated_value,
            confidence=min(
                0.85,
                0.5 + len(bottlenecks) * 0.1,
            ),
            source="process_analysis",
        )

        self._store_opportunity(opp)
        self._stats["efficiency_found"] += 1

        return opp

    def _detect_growth(
        self,
        growth_data: dict[str, Any],
    ) -> OpportunityRecord | None:
        """Büyüme fırsatı tespit eder.

        Args:
            growth_data: Büyüme verileri.

        Returns:
            Fırsat kaydı veya None.
        """
        rate = growth_data.get("growth_rate", 0)
        potential = growth_data.get("potential", 0)

        if rate <= 0 and potential <= 0:
            return None

        opp = OpportunityRecord(
            id=str(uuid4())[:8],
            opportunity_type=OpportunityType.GROWTH,
            title="Buyume firsati",
            description=(
                f"Buyume orani: {rate:.1f}%, "
                f"potansiyel: {potential:.1f}%"
            ),
            estimated_value=potential * 1000,
            confidence=min(0.8, 0.4 + rate * 0.05),
            source="growth_analysis",
        )

        self._store_opportunity(opp)
        return opp

    def _store_opportunity(
        self, opp: OpportunityRecord
    ) -> None:
        """Fırsatı depolar.

        Args:
            opp: Fırsat kaydı.
        """
        if len(self._opportunities) >= _MAX_OPPORTUNITIES:
            oldest = min(
                self._opportunities,
                key=lambda k: (
                    self._opportunities[k].detected_at
                ),
            )
            del self._opportunities[oldest]

        self._opportunities[opp.id] = opp
        self._stats["opportunities_detected"] += 1

    def get_opportunities(
        self,
        opportunity_type: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[OpportunityRecord]:
        """Fırsatları filtreli listeler.

        Args:
            opportunity_type: Fırsat tipi filtresi.
            min_confidence: Minimum güven skoru.

        Returns:
            Fırsat listesi.
        """
        results = [
            o
            for o in self._opportunities.values()
            if o.id not in self._dismissed
            and o.confidence >= min_confidence
            and o.status == "active"
        ]

        if opportunity_type:
            results = [
                o
                for o in results
                if o.opportunity_type == opportunity_type
            ]

        return sorted(
            results,
            key=lambda o: o.estimated_value,
            reverse=True,
        )

    def dismiss(
        self, opportunity_id: str
    ) -> bool:
        """Fırsatı reddeder.

        Args:
            opportunity_id: Fırsat ID.

        Returns:
            Başarılı ise True.
        """
        opp = self._opportunities.get(opportunity_id)
        if not opp:
            return False

        opp.status = "dismissed"
        self._dismissed.add(opportunity_id)
        self._stats["dismissed"] += 1

        logger.info(
            "Firsat reddedildi: %s",
            opportunity_id,
        )

        return True

    def act_on(
        self, opportunity_id: str
    ) -> dict[str, Any]:
        """Fırsat üzerinde aksiyon alır.

        Args:
            opportunity_id: Fırsat ID.

        Returns:
            Aksiyon sonucu.
        """
        opp = self._opportunities.get(opportunity_id)
        if not opp:
            return {"error": "opportunity_not_found"}

        opp.status = "acted"
        self._acted[opportunity_id] = {
            "acted_at": time.time(),
            "type": opp.opportunity_type,
            "value": opp.estimated_value,
        }
        self._stats["acted_on"] += 1

        logger.info(
            "Firsat uzerinde aksiyon alindi: %s",
            opportunity_id,
        )

        return {
            "opportunity_id": opportunity_id,
            "type": opp.opportunity_type,
            "title": opp.title,
            "status": "acted",
            "estimated_value": opp.estimated_value,
        }

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        return {
            **self._stats,
            "total_opportunities": len(
                self._opportunities
            ),
            "active_opportunities": sum(
                1
                for o in self._opportunities.values()
                if o.status == "active"
            ),
            "total_acted": len(self._acted),
        }
