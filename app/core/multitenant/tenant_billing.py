"""ATLAS Tenant Billing modulu.

Kiraciya ozel faturalandirma,
abonelik ve kullanim takibi.
"""

import logging
import time
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Any
from uuid import uuid4

from app.models.multitenant_models import (
    BillingCycle,
    BillingPlan,
    BillingRecord,
)

logger = logging.getLogger(__name__)

_MAX_BILLING_HISTORY = 500

_PLAN_PRICING: dict[
    BillingPlan, dict[str, float]
] = {
    BillingPlan.FREE: {
        "monthly": 0.0,
        "quarterly": 0.0,
        "yearly": 0.0,
    },
    BillingPlan.STARTER: {
        "monthly": 29.0,
        "quarterly": 79.0,
        "yearly": 290.0,
    },
    BillingPlan.PROFESSIONAL: {
        "monthly": 99.0,
        "quarterly": 269.0,
        "yearly": 990.0,
    },
    BillingPlan.ENTERPRISE: {
        "monthly": 299.0,
        "quarterly": 799.0,
        "yearly": 2990.0,
    },
    BillingPlan.CUSTOM: {
        "monthly": 0.0,
        "quarterly": 0.0,
        "yearly": 0.0,
    },
}

_CYCLE_DAYS: dict[BillingCycle, int] = {
    BillingCycle.MONTHLY: 30,
    BillingCycle.QUARTERLY: 90,
    BillingCycle.YEARLY: 365,
}


class TenantBilling:
    """Kiraci faturalandirma yoneticisi.

    Abonelik, odeme ve kullanim
    takibi yapar.

    Attributes:
        _subscriptions: Aktif abonelikler.
        _billing_history: Fatura gecmisi.
    """

    def __init__(self) -> None:
        """Faturalandirmayi baslatir."""
        self._subscriptions: dict[
            str, BillingRecord
        ] = {}
        self._billing_history: dict[
            str, list[BillingRecord]
        ] = {}
        self._usage: dict[
            str, dict[str, int]
        ] = {}
        self._stats = {
            "subscriptions_created": 0,
            "payments_recorded": 0,
            "upgrades": 0,
            "downgrades": 0,
            "total_revenue": 0.0,
        }

        logger.info(
            "TenantBilling baslatildi",
        )

    def create_subscription(
        self,
        tenant_id: str,
        plan: BillingPlan = BillingPlan.FREE,
        cycle: BillingCycle = (
            BillingCycle.MONTHLY
        ),
    ) -> BillingRecord:
        """Yeni abonelik olusturur.

        Args:
            tenant_id: Kiraci ID.
            plan: Faturalandirma plani.
            cycle: Faturalandirma dongusu.

        Returns:
            Abonelik kaydi.
        """
        pricing = _PLAN_PRICING.get(
            plan,
            _PLAN_PRICING[BillingPlan.FREE],
        )
        amount = pricing.get(
            cycle.value, 0.0,
        )
        days = _CYCLE_DAYS.get(
            cycle, 30,
        )

        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=days)

        record = BillingRecord(
            id=str(uuid4())[:8],
            tenant_id=tenant_id,
            plan=plan,
            cycle=cycle,
            amount=amount,
            period_start=now,
            period_end=period_end,
            paid=(plan == BillingPlan.FREE),
        )

        self._subscriptions[tenant_id] = record
        self._billing_history.setdefault(
            tenant_id, [],
        ).append(record)

        # Kullanim sayaclarini baslat
        self._usage.setdefault(
            tenant_id,
            {
                "users": 0,
                "agents": 0,
                "storage_mb": 0,
                "api_calls": 0,
            },
        )

        self._stats[
            "subscriptions_created"
        ] += 1

        logger.info(
            "Abonelik olusturuldu: %s (%s/%s)",
            tenant_id, plan.value, cycle.value,
        )

        return record

    def record_payment(
        self,
        tenant_id: str,
        amount: float,
        invoice_url: str | None = None,
    ) -> BillingRecord | None:
        """Odeme kaydeder.

        Args:
            tenant_id: Kiraci ID.
            amount: Odeme tutari.
            invoice_url: Fatura URL.

        Returns:
            Guncellenmis kayit veya None.
        """
        record = self._subscriptions.get(
            tenant_id,
        )
        if not record:
            logger.warning(
                "Abonelik bulunamadi: %s",
                tenant_id,
            )
            return None

        record.paid = True
        record.amount = amount
        if invoice_url:
            record.invoice_url = invoice_url

        self._stats[
            "payments_recorded"
        ] += 1
        self._stats[
            "total_revenue"
        ] += amount

        logger.info(
            "Odeme kaydedildi: %s (%.2f)",
            tenant_id, amount,
        )

        return record

    def get_current_plan(
        self,
        tenant_id: str,
    ) -> BillingRecord | None:
        """Mevcut plani getirir.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Mevcut abonelik veya None.
        """
        return self._subscriptions.get(
            tenant_id,
        )

    def upgrade_plan(
        self,
        tenant_id: str,
        new_plan: BillingPlan,
    ) -> BillingRecord | None:
        """Plani yukseltir.

        Args:
            tenant_id: Kiraci ID.
            new_plan: Yeni plan.

        Returns:
            Yeni abonelik kaydi veya None.
        """
        current = self._subscriptions.get(
            tenant_id,
        )
        if not current:
            return None

        plan_order = [
            BillingPlan.FREE,
            BillingPlan.STARTER,
            BillingPlan.PROFESSIONAL,
            BillingPlan.ENTERPRISE,
            BillingPlan.CUSTOM,
        ]

        current_idx = (
            plan_order.index(current.plan)
            if current.plan in plan_order
            else 0
        )
        new_idx = (
            plan_order.index(new_plan)
            if new_plan in plan_order
            else 0
        )

        if new_idx <= current_idx:
            logger.warning(
                "Yukseltme degil: %s -> %s",
                current.plan.value,
                new_plan.value,
            )
            return None

        record = self.create_subscription(
            tenant_id, new_plan, current.cycle,
        )

        self._stats["upgrades"] += 1
        logger.info(
            "Plan yukseltildi: %s -> %s (%s)",
            current.plan.value,
            new_plan.value,
            tenant_id,
        )

        return record

    def downgrade_plan(
        self,
        tenant_id: str,
        new_plan: BillingPlan,
    ) -> BillingRecord | None:
        """Plani dusurur.

        Args:
            tenant_id: Kiraci ID.
            new_plan: Yeni plan.

        Returns:
            Yeni abonelik kaydi veya None.
        """
        current = self._subscriptions.get(
            tenant_id,
        )
        if not current:
            return None

        plan_order = [
            BillingPlan.FREE,
            BillingPlan.STARTER,
            BillingPlan.PROFESSIONAL,
            BillingPlan.ENTERPRISE,
            BillingPlan.CUSTOM,
        ]

        current_idx = (
            plan_order.index(current.plan)
            if current.plan in plan_order
            else 0
        )
        new_idx = (
            plan_order.index(new_plan)
            if new_plan in plan_order
            else 0
        )

        if new_idx >= current_idx:
            logger.warning(
                "Dusurme degil: %s -> %s",
                current.plan.value,
                new_plan.value,
            )
            return None

        record = self.create_subscription(
            tenant_id, new_plan, current.cycle,
        )

        self._stats["downgrades"] += 1
        logger.info(
            "Plan dusuruldu: %s -> %s (%s)",
            current.plan.value,
            new_plan.value,
            tenant_id,
        )

        return record

    def get_billing_history(
        self,
        tenant_id: str,
    ) -> list[BillingRecord]:
        """Fatura gecmisini getirir.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Fatura gecmisi.
        """
        return self._billing_history.get(
            tenant_id, [],
        )

    def calculate_usage(
        self,
        tenant_id: str,
    ) -> dict[str, int]:
        """Kullanim istatistiklerini hesaplar.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Kullanim metrikleri.
        """
        return dict(
            self._usage.get(
                tenant_id,
                {
                    "users": 0,
                    "agents": 0,
                    "storage_mb": 0,
                    "api_calls": 0,
                },
            ),
        )

    def record_usage(
        self,
        tenant_id: str,
        metric: str,
        amount: int = 1,
    ) -> None:
        """Kullanim kaydeder.

        Args:
            tenant_id: Kiraci ID.
            metric: Metrik adi.
            amount: Miktar.
        """
        usage = self._usage.setdefault(
            tenant_id,
            {
                "users": 0,
                "agents": 0,
                "storage_mb": 0,
                "api_calls": 0,
            },
        )
        if metric in usage:
            usage[metric] += amount

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        plan_dist: dict[str, int] = {}
        for sub in self._subscriptions.values():
            p = sub.plan.value
            plan_dist[p] = (
                plan_dist.get(p, 0) + 1
            )

        return {
            "total_subscriptions": len(
                self._subscriptions,
            ),
            "plan_distribution": plan_dist,
            **self._stats,
            "timestamp": time.time(),
        }
