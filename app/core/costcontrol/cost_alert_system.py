"""Maliyet uyarı sistemi.

Eşik bazlı uyarılar, artış tespiti,
çoklu kanal dağıtımı (Telegram, email).
"""

import logging
import time
from typing import Any

from app.models.costcontrol_models import (
    CostAlert,
    AlertSeverity,
)

logger = logging.getLogger(__name__)

_MAX_ALERTS = 5000
_MAX_RULES = 100


class CostAlertSystem:
    """Maliyet uyarı sistemi.

    Maliyet eşikleri izler, uyarı üretir,
    kanallara dağıtır.

    Attributes:
        _alerts: Oluşturulan uyarılar.
        _rules: Uyarı kuralları.
    """

    def __init__(self) -> None:
        """CostAlertSystem başlatır."""
        self._alerts: list[CostAlert] = []
        self._rules: list[dict[str, Any]] = []
        self._total_alerts: int = 0
        self._total_acknowledged: int = 0

        logger.info("CostAlertSystem baslatildi")

    def add_rule(
        self,
        name: str,
        threshold_usd: float,
        severity: str = "warning",
        channels: list[str] | None = None,
        period: str = "daily",
    ) -> dict[str, Any]:
        """Uyarı kuralı ekle.

        Args:
            name: Kural adı.
            threshold_usd: USD eşik değeri.
            severity: Uyarı şiddeti.
            channels: Bildirim kanalları.
            period: Kontrol dönemi.

        Returns:
            Kural bilgisi.
        """
        if len(self._rules) >= _MAX_RULES:
            logger.warning("Max kural limiti: %d", _MAX_RULES)
            return {}

        rule = {
            "name": name,
            "threshold_usd": threshold_usd,
            "severity": severity,
            "channels": channels or ["telegram"],
            "period": period,
            "enabled": True,
            "trigger_count": 0,
        }

        self._rules.append(rule)
        logger.info("Uyari kurali eklendi: %s ($%.2f)", name, threshold_usd)
        return rule

    def check_and_alert(
        self,
        current_spend: float,
        budget_limit: float = 0.0,
        period: str = "daily",
    ) -> list[CostAlert]:
        """Harcamayı kontrol et ve gerekirse uyarı üret.

        Args:
            current_spend: Mevcut harcama.
            budget_limit: Bütçe limiti.
            period: Dönem.

        Returns:
            Üretilen uyarılar.
        """
        new_alerts: list[CostAlert] = []

        for rule in self._rules:
            if not rule.get("enabled", True):
                continue
            if rule.get("period") != period:
                continue

            if current_spend >= rule["threshold_usd"]:
                percentage = 0.0
                if budget_limit > 0:
                    percentage = round((current_spend / budget_limit) * 100, 1)

                alert = CostAlert(
                    severity=rule.get("severity", "warning"),
                    title=f"Maliyet uyarisi: {rule['name']}",
                    message=f"Harcama ${current_spend:.2f} esigi ${rule['threshold_usd']:.2f} asti",
                    current_spend=current_spend,
                    limit_usd=budget_limit,
                    percentage=percentage,
                    channels=rule.get("channels", ["telegram"]),
                )

                if len(self._alerts) < _MAX_ALERTS:
                    self._alerts.append(alert)
                new_alerts.append(alert)
                rule["trigger_count"] = rule.get("trigger_count", 0) + 1
                self._total_alerts += 1

        if new_alerts:
            logger.warning(
                "%d maliyet uyarisi uretildi (harcama: $%.2f)",
                len(new_alerts),
                current_spend,
            )

        return new_alerts

    def create_alert(
        self,
        severity: str,
        title: str,
        message: str,
        current_spend: float = 0.0,
        limit_usd: float = 0.0,
        channels: list[str] | None = None,
    ) -> CostAlert:
        """Manuel uyarı oluştur.

        Args:
            severity: Şiddet.
            title: Başlık.
            message: Mesaj.
            current_spend: Mevcut harcama.
            limit_usd: Bütçe limiti.
            channels: Kanallar.

        Returns:
            Uyarı kaydı.
        """
        percentage = 0.0
        if limit_usd > 0:
            percentage = round((current_spend / limit_usd) * 100, 1)

        alert = CostAlert(
            severity=severity,
            title=title,
            message=message,
            current_spend=current_spend,
            limit_usd=limit_usd,
            percentage=percentage,
            channels=channels or ["telegram"],
        )

        if len(self._alerts) < _MAX_ALERTS:
            self._alerts.append(alert)
        self._total_alerts += 1
        return alert

    def acknowledge(self, alert_id: str) -> bool:
        """Uyarıyı onayla.

        Args:
            alert_id: Uyarı ID.

        Returns:
            Başarılı ise True.
        """
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self._total_acknowledged += 1
                return True
        return False

    def get_unacknowledged(self) -> list[CostAlert]:
        """Onaylanmamış uyarıları getir."""
        return [a for a in self._alerts if not a.acknowledged]

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_alerts": self._total_alerts,
            "total_acknowledged": self._total_acknowledged,
            "total_rules": len(self._rules),
            "pending_alerts": len(self.get_unacknowledged()),
        }
