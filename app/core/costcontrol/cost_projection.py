"""Maliyet projeksiyonu.

Aylık, haftalık maliyet tahmini,
trend analizi, bütçe tahmini.
"""

import logging
import time
from typing import Any

from app.models.costcontrol_models import (
    CostProjectionResult,
    CostPeriod,
)

logger = logging.getLogger(__name__)


class CostProjection:
    """Maliyet projeksiyonu.

    Geçmiş harcama verilerine göre
    gelecek maliyet tahmini yapar.

    Attributes:
        _projections: Projeksiyon sonuçları.
        _daily_costs: Günlük maliyet geçmişi.
    """

    def __init__(self) -> None:
        """CostProjection başlatır."""
        self._projections: list[CostProjectionResult] = []
        self._daily_costs: list[dict[str, Any]] = []
        self._total_projections: int = 0

        logger.info("CostProjection baslatildi")

    def record_daily_cost(
        self,
        cost_usd: float,
        breakdown_by_model: dict[str, float] | None = None,
        breakdown_by_tool: dict[str, float] | None = None,
    ) -> None:
        """Günlük maliyet kaydet.

        Args:
            cost_usd: Günlük maliyet.
            breakdown_by_model: Model bazlı dağılım.
            breakdown_by_tool: Araç bazlı dağılım.
        """
        self._daily_costs.append({
            "date": time.time(),
            "cost": cost_usd,
            "by_model": breakdown_by_model or {},
            "by_tool": breakdown_by_tool or {},
        })

    def project(
        self,
        period: str = "monthly",
        current_spend: float = 0.0,
        days_elapsed: int = 0,
    ) -> CostProjectionResult:
        """Maliyet projeksiyonu yap.

        Args:
            period: Projeksiyon dönemi.
            current_spend: Mevcut harcama.
            days_elapsed: Geçen gün sayısı.

        Returns:
            Projeksiyon sonucu.
        """
        days_in_period = {"hourly": 1/24, "daily": 1, "weekly": 7, "monthly": 30}
        total_days = days_in_period.get(period, 30)

        if days_elapsed > 0 and current_spend > 0:
            daily_avg = current_spend / days_elapsed
            projected = daily_avg * total_days
        elif self._daily_costs:
            costs = [d["cost"] for d in self._daily_costs[-30:]]
            daily_avg = sum(costs) / len(costs) if costs else 0
            projected = daily_avg * total_days
        else:
            projected = current_spend

        trend = "stable"
        trend_percent = 0.0
        if len(self._daily_costs) >= 7:
            recent = [d["cost"] for d in self._daily_costs[-7:]]
            earlier = [d["cost"] for d in self._daily_costs[-14:-7]]
            if earlier:
                recent_avg = sum(recent) / len(recent)
                earlier_avg = sum(earlier) / len(earlier)
                if earlier_avg > 0:
                    trend_percent = round(((recent_avg - earlier_avg) / earlier_avg) * 100, 1)
                    if trend_percent > 5:
                        trend = "increasing"
                    elif trend_percent < -5:
                        trend = "decreasing"

        recommendations = []
        if trend == "increasing" and trend_percent > 20:
            recommendations.append("Maliyet hizla artiyor, model optimizasyonu oneririz")
        if projected > 100:
            recommendations.append("Aylik maliyet $100'i asacak, butce limiti tanimlayiniz")

        # Model dağılımı
        by_model: dict[str, float] = {}
        for dc in self._daily_costs[-30:]:
            for model, cost in dc.get("by_model", {}).items():
                by_model[model] = by_model.get(model, 0) + cost

        result = CostProjectionResult(
            period=period,
            current_spend=current_spend,
            projected_spend=round(projected, 2),
            trend=trend,
            trend_percent=trend_percent,
            confidence=0.8 if len(self._daily_costs) >= 14 else 0.5,
            breakdown_by_model=by_model,
            recommendations=recommendations,
        )

        self._projections.append(result)
        self._total_projections += 1

        logger.info(
            "Projeksiyon: %s $%.2f -> $%.2f (%s)",
            period,
            current_spend,
            projected,
            trend,
        )
        return result

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_projections": self._total_projections,
            "daily_records": len(self._daily_costs),
        }
