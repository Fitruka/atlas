"""Bütçe sınırlayıcı.

Günlük, haftalık, aylık bütçe limitleri,
uyarı eşikleri, hard stop mekanizması.
"""

import logging
import time
from typing import Any

from app.models.costcontrol_models import (
    BudgetLimit,
    BudgetStatus,
    CostPeriod,
)

logger = logging.getLogger(__name__)

_MAX_BUDGETS = 50
_PERIOD_SECONDS = {
    "hourly": 3600,
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
}


class BudgetLimiter:
    """Bütçe sınırlayıcı.

    Periyodik bütçe limitleri tanımlar,
    harcamayı izler, hard stop uygular.

    Attributes:
        _budgets: Tanımlı bütçeler.
    """

    def __init__(self) -> None:
        """BudgetLimiter başlatır."""
        self._budgets: dict[str, BudgetLimit] = {}
        self._total_checks: int = 0
        self._total_blocks: int = 0

        logger.info("BudgetLimiter baslatildi")

    def set_limit(
        self,
        name: str,
        period: str,
        limit_usd: float,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95,
        hard_stop: bool = True,
    ) -> BudgetLimit:
        """Bütçe limiti tanımla.

        Args:
            name: Bütçe adı.
            period: Dönem (daily, weekly, monthly).
            limit_usd: USD limit.
            warning_threshold: Uyarı eşiği (0-1).
            critical_threshold: Kritik eşik (0-1).
            hard_stop: Limitte durdur.

        Returns:
            Bütçe kaydı.
        """
        if len(self._budgets) >= _MAX_BUDGETS:
            logger.warning("Max butce limiti: %d", _MAX_BUDGETS)
            return BudgetLimit()

        period_seconds = _PERIOD_SECONDS.get(period, _PERIOD_SECONDS["daily"])

        budget = BudgetLimit(
            name=name,
            period=period,
            limit_usd=limit_usd,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            hard_stop=hard_stop,
            reset_at=time.time() + period_seconds,
        )

        self._budgets[budget.limit_id] = budget
        logger.info(
            "Butce limiti tanimlandi: %s ($%.2f/%s)",
            name,
            limit_usd,
            period,
        )
        return budget

    def check_budget(
        self,
        cost_usd: float,
        budget_id: str = "",
    ) -> dict[str, Any]:
        """Bütçe kontrolü yap.

        Args:
            cost_usd: Eklenecek maliyet.
            budget_id: Spesifik bütçe ID (boş = tümü).

        Returns:
            Kontrol sonucu.
        """
        self._total_checks += 1
        budgets = (
            [self._budgets[budget_id]]
            if budget_id and budget_id in self._budgets
            else list(self._budgets.values())
        )

        blocked = False
        alerts: list[dict] = []

        for budget in budgets:
            self._check_reset(budget)

            new_spend = budget.current_spend + cost_usd
            ratio = new_spend / budget.limit_usd if budget.limit_usd > 0 else 0

            if ratio >= 1.0 and budget.hard_stop:
                budget.status = BudgetStatus.HARD_STOP
                blocked = True
                self._total_blocks += 1
                alerts.append({
                    "budget_id": budget.limit_id,
                    "name": budget.name,
                    "status": "hard_stop",
                    "current": budget.current_spend,
                    "limit": budget.limit_usd,
                })
            elif ratio >= budget.critical_threshold:
                budget.status = BudgetStatus.CRITICAL
                alerts.append({
                    "budget_id": budget.limit_id,
                    "name": budget.name,
                    "status": "critical",
                    "percentage": round(ratio * 100, 1),
                })
            elif ratio >= budget.warning_threshold:
                budget.status = BudgetStatus.WARNING
                alerts.append({
                    "budget_id": budget.limit_id,
                    "name": budget.name,
                    "status": "warning",
                    "percentage": round(ratio * 100, 1),
                })

        return {
            "allowed": not blocked,
            "blocked": blocked,
            "alerts": alerts,
        }

    def add_spend(
        self,
        cost_usd: float,
        budget_id: str = "",
    ) -> bool:
        """Harcama ekle.

        Args:
            cost_usd: Maliyet (USD).
            budget_id: Spesifik bütçe ID.

        Returns:
            İzin verildiyse True.
        """
        check = self.check_budget(cost_usd, budget_id)
        if check["blocked"]:
            logger.warning("Butce asimi! Harcama engellendi: $%.6f", cost_usd)
            return False

        budgets = (
            [self._budgets[budget_id]]
            if budget_id and budget_id in self._budgets
            else list(self._budgets.values())
        )

        for budget in budgets:
            budget.current_spend += cost_usd

        return True

    def _check_reset(self, budget: BudgetLimit) -> None:
        """Dönem sıfırlama kontrolü.

        Args:
            budget: Bütçe kaydı.
        """
        now = time.time()
        if budget.reset_at > 0 and now >= budget.reset_at:
            period_str = budget.period.value if isinstance(budget.period, CostPeriod) else str(budget.period)
            period_seconds = _PERIOD_SECONDS.get(period_str, _PERIOD_SECONDS["daily"])
            budget.current_spend = 0.0
            budget.status = BudgetStatus.NORMAL
            budget.reset_at = now + period_seconds
            logger.info("Butce sifirlandi: %s", budget.name)

    def get_budget(self, budget_id: str) -> BudgetLimit | None:
        """Bütçe getir."""
        return self._budgets.get(budget_id)

    def list_budgets(self) -> list[BudgetLimit]:
        """Tüm bütçeleri listele."""
        return list(self._budgets.values())

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_budgets": len(self._budgets),
            "total_checks": self._total_checks,
            "total_blocks": self._total_blocks,
        }
