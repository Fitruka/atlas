"""
Şablon dashboard modülü.

Şablon bazlı metrikler,
kullanım kaydı, şablon sıralama,
maliyet ve memnuniyet analizi.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.analyticsdash_models import (
    TemplateMetric,
)

logger = logging.getLogger(__name__)

_MAX_RECORDS = 10000


class TemplateDashboard:
    """Şablon dashboard yöneticisi.

    Attributes:
        _records: Kullanım kayıtları.
        _metrics: Metrik listesi.
        _stats: İstatistikler.
    """

    def __init__(self) -> None:
        """Dashboard yöneticisini başlatır."""
        self._records: list[dict] = []
        self._metrics: list[
            TemplateMetric
        ] = []
        self._stats: dict[str, int] = {
            "usages_recorded": 0,
            "queries_performed": 0,
        }
        logger.info(
            "TemplateDashboard baslatildi"
        )

    @property
    def record_count(self) -> int:
        """Kayıt sayısı."""
        return len(self._records)

    def record_template_usage(
        self,
        template_name: str = "",
        industry: str = "",
        cost: float = 0.0,
        satisfaction: float | None = None,
    ) -> None:
        """Şablon kullanımı kaydeder.

        Args:
            template_name: Şablon adı.
            industry: Sektör.
            cost: Maliyet.
            satisfaction: Memnuniyet puanı.
        """
        try:
            if (
                len(self._records)
                >= _MAX_RECORDS
            ):
                self._records = (
                    self._records[
                        -(_MAX_RECORDS // 2) :
                    ]
                )

            record = {
                "id": str(uuid4())[:8],
                "template_name": template_name,
                "industry": industry,
                "cost": cost,
                "satisfaction": satisfaction,
                "timestamp": datetime.now(
                    timezone.utc
                ),
                "day": datetime.now(
                    timezone.utc
                ).strftime("%Y-%m-%d"),
            }
            self._records.append(record)
            self._stats[
                "usages_recorded"
            ] += 1

        except Exception as e:
            logger.error(
                f"Kullanim kayit hatasi: {e}"
            )

    def get_template_metrics(
        self,
        template_name: str | None = None,
        period: str = "day",
    ) -> list[dict[str, Any]]:
        """Şablon metriklerini getirir.

        Args:
            template_name: Şablon adı filtresi.
            period: Dönem.

        Returns:
            Metrik listesi.
        """
        try:
            self._stats[
                "queries_performed"
            ] += 1

            filtered = self._records
            if template_name:
                filtered = [
                    r
                    for r in filtered
                    if r["template_name"]
                    == template_name
                ]

            template_groups: dict[
                str, list[dict]
            ] = defaultdict(list)
            for rec in filtered:
                template_groups[
                    rec["template_name"]
                ].append(rec)

            results = []
            for tmpl, recs in template_groups.items():
                total_requests = len(recs)
                avg_cost = (
                    sum(r["cost"] for r in recs)
                    / total_requests
                    if total_requests > 0
                    else 0.0
                )

                sats = [
                    r["satisfaction"]
                    for r in recs
                    if r["satisfaction"]
                    is not None
                ]
                avg_sat = (
                    sum(sats) / len(sats)
                    if sats
                    else 0.0
                )

                industries = {
                    r["industry"]
                    for r in recs
                    if r["industry"]
                }
                industry = (
                    next(iter(industries))
                    if len(industries) == 1
                    else ", ".join(industries)
                )

                metric = TemplateMetric(
                    template_name=tmpl,
                    industry=industry,
                    total_requests=total_requests,
                    avg_cost=round(avg_cost, 4),
                    satisfaction=round(
                        avg_sat, 2
                    ),
                    period=period,
                )
                self._metrics.append(metric)

                results.append(
                    {
                        "template_name": tmpl,
                        "industry": industry,
                        "total_requests": (
                            total_requests
                        ),
                        "avg_cost": round(
                            avg_cost, 4
                        ),
                        "satisfaction": round(
                            avg_sat, 2
                        ),
                        "period": period,
                    }
                )

            return results

        except Exception as e:
            logger.error(
                f"Metrik sorgulama hatasi: {e}"
            )
            return []

    def get_top_templates(
        self,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """En çok kullanılan şablonları getirir.

        Args:
            limit: Kaç şablon.

        Returns:
            Şablon listesi.
        """
        try:
            template_counts: dict[
                str, int
            ] = defaultdict(int)
            for r in self._records:
                template_counts[
                    r["template_name"]
                ] += 1

            sorted_templates = sorted(
                template_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            return [
                {
                    "template_name": name,
                    "usage_count": count,
                    "rank": idx + 1,
                }
                for idx, (name, count) in enumerate(
                    sorted_templates[:limit]
                )
            ]

        except Exception as e:
            logger.error(
                f"Top sablon hatasi: {e}"
            )
            return []

    def get_cost_per_template(
        self,
    ) -> dict[str, float]:
        """Şablon bazlı ortalama maliyeti getirir.

        Returns:
            Şablon -> ortalama maliyet eşleşmesi.
        """
        try:
            template_costs: dict[
                str, list[float]
            ] = defaultdict(list)
            for r in self._records:
                template_costs[
                    r["template_name"]
                ].append(r["cost"])

            return {
                tmpl: round(
                    sum(costs) / len(costs), 4
                )
                for tmpl, costs in template_costs.items()
                if costs
            }

        except Exception as e:
            logger.error(
                f"Maliyet sorgulama hatasi: {e}"
            )
            return {}

    def get_template_satisfaction(
        self,
    ) -> dict[str, float]:
        """Şablon bazlı memnuniyeti getirir.

        Returns:
            Şablon -> memnuniyet eşleşmesi.
        """
        try:
            template_sats: dict[
                str, list[float]
            ] = defaultdict(list)
            for r in self._records:
                if r["satisfaction"] is not None:
                    template_sats[
                        r["template_name"]
                    ].append(r["satisfaction"])

            return {
                tmpl: round(
                    sum(sats) / len(sats), 2
                )
                for tmpl, sats in template_sats.items()
                if sats
            }

        except Exception as e:
            logger.error(
                f"Memnuniyet sorgulama hatasi: {e}"
            )
            return {}

    def compare_templates(
        self,
    ) -> list[dict[str, Any]]:
        """Şablonları karşılaştırır.

        Returns:
            Sıralı şablon listesi.
        """
        try:
            metrics = self.get_template_metrics()

            return sorted(
                metrics,
                key=lambda x: x.get(
                    "total_requests", 0
                ),
                reverse=True,
            )

        except Exception as e:
            logger.error(
                f"Karsilastirma hatasi: {e}"
            )
            return []

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri getirir.

        Returns:
            İstatistik bilgileri.
        """
        return {
            "total_records": len(
                self._records
            ),
            "total_metrics": len(
                self._metrics
            ),
            "unique_templates": len(
                {
                    r["template_name"]
                    for r in self._records
                }
            ),
            **self._stats,
        }
