"""Şablon bazlı maliyet analizi.

Template bazlı maliyet takibi,
karşılaştırma, optimizasyon önerileri.
"""

import logging
from typing import Any

from app.models.costcontrol_models import (
    TemplateCostReport,
    CostPeriod,
)

logger = logging.getLogger(__name__)

_MAX_TEMPLATES = 100


class CostPerTemplate:
    """Şablon bazlı maliyet analizi.

    Her şablon için maliyet takibi yapar,
    karşılaştırır, optimizasyon önerir.

    Attributes:
        _template_costs: Şablon maliyet verileri.
        _reports: Oluşturulan raporlar.
    """

    def __init__(self) -> None:
        """CostPerTemplate başlatır."""
        self._template_costs: dict[str, dict[str, Any]] = {}
        self._reports: list[TemplateCostReport] = []
        self._total_reports: int = 0

        logger.info("CostPerTemplate baslatildi")

    def record_cost(
        self,
        template_id: str,
        template_name: str,
        cost_usd: float,
        tokens: int = 0,
        skill_name: str = "",
        model_name: str = "",
    ) -> None:
        """Şablon maliyeti kaydet.

        Args:
            template_id: Şablon ID.
            template_name: Şablon adı.
            cost_usd: Maliyet (USD).
            tokens: Token sayısı.
            skill_name: Beceri adı.
            model_name: Model adı.
        """
        if template_id not in self._template_costs:
            self._template_costs[template_id] = {
                "name": template_name,
                "total_cost": 0.0,
                "total_tokens": 0,
                "total_requests": 0,
                "by_skill": {},
                "by_model": {},
            }

        data = self._template_costs[template_id]
        data["total_cost"] += cost_usd
        data["total_tokens"] += tokens
        data["total_requests"] += 1

        if skill_name:
            data["by_skill"][skill_name] = data["by_skill"].get(skill_name, 0) + cost_usd
        if model_name:
            data["by_model"][model_name] = data["by_model"].get(model_name, 0) + cost_usd

    def generate_report(
        self,
        template_id: str,
        period: str = "monthly",
    ) -> TemplateCostReport | None:
        """Şablon maliyet raporu oluştur.

        Args:
            template_id: Şablon ID.
            period: Rapor dönemi.

        Returns:
            Maliyet raporu veya None.
        """
        data = self._template_costs.get(template_id)
        if not data:
            logger.warning("Sablon maliyet verisi yok: %s", template_id)
            return None

        avg_cost = (
            data["total_cost"] / data["total_requests"]
            if data["total_requests"] > 0
            else 0.0
        )

        suggestions = []
        if data["total_cost"] > 50:
            suggestions.append("Yuksek maliyet - model tier dusurmeyi deneyin")
        if data["by_model"]:
            most_expensive = max(data["by_model"].items(), key=lambda x: x[1])
            suggestions.append(f"En pahali model: {most_expensive[0]} (${most_expensive[1]:.2f})")
        if data["total_requests"] > 1000:
            suggestions.append("Yuksek istek sayisi - cache kullanmayi deneyin")

        report = TemplateCostReport(
            template_id=template_id,
            template_name=data["name"],
            period=period,
            total_cost=round(data["total_cost"], 4),
            cost_by_skill=dict(data["by_skill"]),
            cost_by_model=dict(data["by_model"]),
            total_tokens=data["total_tokens"],
            total_requests=data["total_requests"],
            avg_cost_per_request=round(avg_cost, 6),
            optimization_suggestions=suggestions,
        )

        self._reports.append(report)
        self._total_reports += 1

        logger.info(
            "Sablon maliyet raporu: %s ($%.2f, %d istek)",
            data["name"],
            data["total_cost"],
            data["total_requests"],
        )
        return report

    def compare_templates(self) -> list[dict[str, Any]]:
        """Şablonları maliyet bazlı karşılaştır.

        Returns:
            Karşılaştırma listesi.
        """
        comparison = []
        for tid, data in self._template_costs.items():
            avg = data["total_cost"] / data["total_requests"] if data["total_requests"] > 0 else 0
            comparison.append({
                "template_id": tid,
                "name": data["name"],
                "total_cost": round(data["total_cost"], 4),
                "total_requests": data["total_requests"],
                "avg_cost": round(avg, 6),
            })

        comparison.sort(key=lambda x: x["total_cost"], reverse=True)
        return comparison

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "tracked_templates": len(self._template_costs),
            "total_reports": self._total_reports,
        }
