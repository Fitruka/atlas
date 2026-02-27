"""
Maliyet dashboard modülü.

Maliyet analitikleri, model/araç/şablon
bazlı maliyet takibi, bütçe yönetimi,
trend analizi, bütçe durumu.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.analyticsdash_models import (
    CostMetric,
)

logger = logging.getLogger(__name__)

_MAX_COST_RECORDS = 10000
_DEFAULT_BUDGET = 1000.0


class CostDashboard:
    """Maliyet dashboard yöneticisi.

    Attributes:
        _records: Maliyet kayıtları.
        _budget: Bütçe bilgisi.
        _stats: İstatistikler.
    """

    def __init__(self) -> None:
        """Dashboard yöneticisini başlatır."""
        self._records: list[dict] = []
        self._budget: dict[str, Any] = {
            "amount": _DEFAULT_BUDGET,
            "period": "monthly",
            "used": 0.0,
        }
        self._stats: dict[str, int] = {
            "costs_recorded": 0,
            "summaries_generated": 0,
            "budget_alerts": 0,
        }
        logger.info(
            "CostDashboard baslatildi"
        )

    @property
    def record_count(self) -> int:
        """Kayıt sayısı."""
        return len(self._records)

    def record_cost(
        self,
        model: str = "",
        tool: str = "",
        template: str = "",
        amount: float = 0.0,
        tokens: int = 0,
    ) -> None:
        """Maliyet kaydeder.

        Args:
            model: Model adı.
            tool: Araç adı.
            template: Şablon adı.
            amount: Tutar.
            tokens: Token sayısı.
        """
        try:
            if (
                len(self._records)
                >= _MAX_COST_RECORDS
            ):
                self._records = self._records[
                    -(_MAX_COST_RECORDS // 2) :
                ]

            record = {
                "id": str(uuid4())[:8],
                "model": model,
                "tool": tool,
                "template": template,
                "amount": amount,
                "tokens": tokens,
                "timestamp": datetime.now(
                    timezone.utc
                ),
                "day": datetime.now(
                    timezone.utc
                ).strftime("%Y-%m-%d"),
            }
            self._records.append(record)
            self._budget["used"] += amount
            self._stats["costs_recorded"] += 1

            used_pct = (
                self._budget["used"]
                / self._budget["amount"]
                * 100
                if self._budget["amount"] > 0
                else 0.0
            )
            if used_pct >= 90:
                self._stats[
                    "budget_alerts"
                ] += 1
                logger.warning(
                    f"Butce uyarisi: %{used_pct:.1f}"
                )

        except Exception as e:
            logger.error(
                f"Maliyet kayit hatasi: {e}"
            )

    def get_cost_summary(
        self,
        period: str = "day",
    ) -> dict[str, Any]:
        """Maliyet özetini getirir.

        Args:
            period: Dönem.

        Returns:
            Maliyet özeti.
        """
        try:
            self._stats[
                "summaries_generated"
            ] += 1

            total = sum(
                r["amount"]
                for r in self._records
            )
            by_model: dict[
                str, float
            ] = defaultdict(float)
            by_tool: dict[
                str, float
            ] = defaultdict(float)
            by_template: dict[
                str, float
            ] = defaultdict(float)

            for r in self._records:
                if r["model"]:
                    by_model[r["model"]] += r[
                        "amount"
                    ]
                if r["tool"]:
                    by_tool[r["tool"]] += r[
                        "amount"
                    ]
                if r["template"]:
                    by_template[
                        r["template"]
                    ] += r["amount"]

            budget_pct = (
                total
                / self._budget["amount"]
                * 100
                if self._budget["amount"] > 0
                else 0.0
            )

            metric = CostMetric(
                period=period,
                total_cost=round(total, 4),
                by_model=dict(by_model),
                by_tool=dict(by_tool),
                by_template=dict(by_template),
                budget_used_pct=round(
                    budget_pct, 2
                ),
            )

            return {
                "period": period,
                "total_cost": round(total, 4),
                "by_model": dict(by_model),
                "by_tool": dict(by_tool),
                "by_template": dict(
                    by_template
                ),
                "budget_used_pct": round(
                    budget_pct, 2
                ),
                "record_count": len(
                    self._records
                ),
            }

        except Exception as e:
            logger.error(
                f"Ozet olusturma hatasi: {e}"
            )
            return {}

    def get_cost_trend(
        self,
        granularity: str = "day",
        periods: int = 30,
    ) -> list[dict[str, Any]]:
        """Maliyet trendini getirir.

        Args:
            granularity: Ayrıntı düzeyi.
            periods: Dönem sayısı.

        Returns:
            Trend verileri.
        """
        try:
            day_costs: dict[
                str, float
            ] = defaultdict(float)
            day_counts: dict[
                str, int
            ] = defaultdict(int)

            for r in self._records:
                day_costs[r["day"]] += r[
                    "amount"
                ]
                day_counts[r["day"]] += 1

            trend = []
            for day in sorted(
                day_costs.keys()
            )[-periods:]:
                trend.append(
                    {
                        "period": day,
                        "total_cost": round(
                            day_costs[day], 4
                        ),
                        "transaction_count": (
                            day_counts[day]
                        ),
                        "avg_cost": round(
                            day_costs[day]
                            / day_counts[day],
                            4,
                        )
                        if day_counts[day] > 0
                        else 0.0,
                    }
                )

            return trend

        except Exception as e:
            logger.error(
                f"Trend sorgulama hatasi: {e}"
            )
            return []

    def get_cost_by_model(
        self,
    ) -> dict[str, float]:
        """Model bazlı maliyetleri getirir.

        Returns:
            Model -> maliyet eşleşmesi.
        """
        try:
            by_model: dict[
                str, float
            ] = defaultdict(float)
            for r in self._records:
                if r["model"]:
                    by_model[r["model"]] += r[
                        "amount"
                    ]
            return {
                k: round(v, 4)
                for k, v in by_model.items()
            }

        except Exception as e:
            logger.error(
                f"Model maliyet hatasi: {e}"
            )
            return {}

    def get_cost_by_tool(
        self,
    ) -> dict[str, float]:
        """Araç bazlı maliyetleri getirir.

        Returns:
            Araç -> maliyet eşleşmesi.
        """
        try:
            by_tool: dict[
                str, float
            ] = defaultdict(float)
            for r in self._records:
                if r["tool"]:
                    by_tool[r["tool"]] += r[
                        "amount"
                    ]
            return {
                k: round(v, 4)
                for k, v in by_tool.items()
            }

        except Exception as e:
            logger.error(
                f"Arac maliyet hatasi: {e}"
            )
            return {}

    def get_cost_by_template(
        self,
    ) -> dict[str, float]:
        """Şablon bazlı maliyetleri getirir.

        Returns:
            Şablon -> maliyet eşleşmesi.
        """
        try:
            by_template: dict[
                str, float
            ] = defaultdict(float)
            for r in self._records:
                if r["template"]:
                    by_template[
                        r["template"]
                    ] += r["amount"]
            return {
                k: round(v, 4)
                for k, v in by_template.items()
            }

        except Exception as e:
            logger.error(
                f"Sablon maliyet hatasi: {e}"
            )
            return {}

    def get_budget_status(
        self,
    ) -> dict[str, Any]:
        """Bütçe durumunu getirir.

        Returns:
            Bütçe durumu.
        """
        try:
            total = self._budget["amount"]
            used = self._budget["used"]
            remaining = max(0, total - used)
            used_pct = (
                used / total * 100
                if total > 0
                else 0.0
            )

            return {
                "total_budget": total,
                "used": round(used, 4),
                "remaining": round(
                    remaining, 4
                ),
                "used_pct": round(used_pct, 2),
                "period": self._budget[
                    "period"
                ],
            }

        except Exception as e:
            logger.error(
                f"Butce sorgulama hatasi: {e}"
            )
            return {}

    def set_budget(
        self,
        amount: float = _DEFAULT_BUDGET,
        period: str = "monthly",
    ) -> None:
        """Bütçe belirler.

        Args:
            amount: Bütçe miktarı.
            period: Dönem.
        """
        self._budget["amount"] = amount
        self._budget["period"] = period
        logger.info(
            f"Butce ayarlandi: {amount} "
            f"({period})"
        )

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri getirir.

        Returns:
            İstatistik bilgileri.
        """
        return {
            "total_records": len(
                self._records
            ),
            "total_spent": round(
                self._budget["used"], 4
            ),
            "budget": self._budget["amount"],
            **self._stats,
        }
