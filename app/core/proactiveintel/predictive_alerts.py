"""ATLAS Tahminsel Uyarılar modülü.

Sorunlar oluşmadan önce uyarı üretimi,
metrik analizi, eşik aşımı tespiti, doğruluk takibi.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.proactiveintel_models import (
    AlertPriority,
    PredictiveAlert,
)

logger = logging.getLogger(__name__)

_MAX_ALERTS = 1000
_DEFAULT_CONFIDENCE = 0.5


class PredictiveAlerts:
    """Tahminsel uyarı yöneticisi.

    Metrik verilerini analiz ederek sorunları
    önceden tahmin eder ve uyarı üretir.

    Attributes:
        _alerts: Uyarı kayıtları.
        _predictions: Tahmin geçmişi.
    """

    def __init__(self) -> None:
        """Uyarı yöneticisini başlatır."""
        self._alerts: dict[str, PredictiveAlert] = {}
        self._predictions: list[dict[str, Any]] = []
        self._accuracy_log: list[dict[str, Any]] = []
        self._thresholds: dict[str, dict[str, Any]] = {}
        self._stats = {
            "alerts_created": 0,
            "alerts_acknowledged": 0,
            "predictions_made": 0,
            "threshold_breaches": 0,
        }

        logger.info(
            "PredictiveAlerts baslatildi",
        )

    def analyze(
        self,
        metric_name: str,
        current_value: float,
        history: list[float],
    ) -> PredictiveAlert | None:
        """Metrik verisini analiz ederek uyarı üretir.

        Args:
            metric_name: Metrik adı.
            current_value: Mevcut değer.
            history: Geçmiş değerler.

        Returns:
            Uyarı veya None.
        """
        self._stats["predictions_made"] += 1

        if len(history) < 3:
            return None

        avg = sum(history) / len(history)
        std_dev = (
            sum((x - avg) ** 2 for x in history)
            / len(history)
        ) ** 0.5

        if std_dev == 0:
            return None

        z_score = (
            abs(current_value - avg) / std_dev
        )

        if z_score < 2.0:
            return None

        if z_score >= 3.0:
            priority = AlertPriority.CRITICAL
            confidence = min(0.95, 0.7 + z_score * 0.05)
        elif z_score >= 2.5:
            priority = AlertPriority.HIGH
            confidence = min(0.85, 0.6 + z_score * 0.05)
        else:
            priority = AlertPriority.MEDIUM
            confidence = 0.55 + z_score * 0.05

        trend = "yukseliyor" if current_value > avg else "dusuyor"

        alert = self.create_alert(
            title=f"{metric_name} anomali tespit edildi",
            description=(
                f"{metric_name} degeri {current_value:.2f}, "
                f"ortalama {avg:.2f}, z-skor {z_score:.2f}. "
                f"Deger {trend}."
            ),
            priority=priority,
            expected_at=None,
            confidence=confidence,
            category="metric_anomaly",
            recommended_action=(
                f"{metric_name} degerini kontrol edin. "
                f"Mevcut trend: {trend}."
            ),
        )

        self._predictions.append({
            "metric": metric_name,
            "value": current_value,
            "avg": avg,
            "z_score": z_score,
            "alert_id": alert.id,
            "timestamp": time.time(),
        })

        return alert

    def create_alert(
        self,
        title: str,
        description: str,
        priority: str = AlertPriority.MEDIUM,
        expected_at: datetime | None = None,
        confidence: float = _DEFAULT_CONFIDENCE,
        category: str = "",
        recommended_action: str = "",
    ) -> PredictiveAlert:
        """Yeni tahminsel uyarı oluşturur.

        Args:
            title: Uyarı başlığı.
            description: Açıklama.
            priority: Öncelik seviyesi.
            expected_at: Beklenen gerçekleşme zamanı.
            confidence: Güven skoru.
            category: Kategori.
            recommended_action: Önerilen aksiyon.

        Returns:
            Oluşturulan uyarı.
        """
        alert = PredictiveAlert(
            id=str(uuid4())[:8],
            title=title,
            description=description,
            priority=priority,
            predicted_at=datetime.now(timezone.utc),
            expected_at=expected_at,
            confidence=confidence,
            category=category,
            recommended_action=recommended_action,
        )

        if len(self._alerts) >= _MAX_ALERTS:
            ack_keys = [
                k
                for k, v in self._alerts.items()
                if v.acknowledged
            ]
            if ack_keys:
                del self._alerts[ack_keys[0]]
            else:
                oldest = min(
                    self._alerts,
                    key=lambda k: (
                        self._alerts[k].predicted_at
                    ),
                )
                del self._alerts[oldest]

        self._alerts[alert.id] = alert
        self._stats["alerts_created"] += 1

        logger.info(
            "Tahminsel uyari olusturuldu: %s [%s]",
            title,
            priority,
        )

        return alert

    def acknowledge(self, alert_id: str) -> bool:
        """Uyarıyı onaylar.

        Args:
            alert_id: Uyarı ID.

        Returns:
            Başarılı ise True.
        """
        alert = self._alerts.get(alert_id)
        if not alert:
            return False

        alert.acknowledged = True
        self._stats["alerts_acknowledged"] += 1

        self._accuracy_log.append({
            "alert_id": alert_id,
            "acknowledged_at": time.time(),
            "was_accurate": True,
        })

        logger.info(
            "Uyari onaylandi: %s", alert_id
        )

        return True

    def get_active_alerts(
        self, priority: str | None = None
    ) -> list[PredictiveAlert]:
        """Aktif uyarıları döndürür.

        Args:
            priority: Filtre için öncelik seviyesi.

        Returns:
            Aktif uyarı listesi.
        """
        alerts = [
            a
            for a in self._alerts.values()
            if not a.acknowledged
        ]

        if priority:
            alerts = [
                a
                for a in alerts
                if a.priority == priority
            ]

        return sorted(
            alerts,
            key=lambda a: a.predicted_at,
            reverse=True,
        )

    def get_alert(
        self, alert_id: str
    ) -> PredictiveAlert | None:
        """Belirli uyarıyı döndürür.

        Args:
            alert_id: Uyarı ID.

        Returns:
            Uyarı veya None.
        """
        return self._alerts.get(alert_id)

    def check_threshold_breach(
        self,
        metric_name: str,
        value: float,
        threshold: float,
        trend: str = "stable",
    ) -> PredictiveAlert | None:
        """Eşik aşımını kontrol eder.

        Args:
            metric_name: Metrik adı.
            value: Mevcut değer.
            threshold: Eşik değer.
            trend: Mevcut trend yönü.

        Returns:
            Uyarı veya None.
        """
        if value < threshold:
            return None

        self._stats["threshold_breaches"] += 1

        ratio = value / threshold if threshold else 1.0

        if ratio >= 2.0:
            priority = AlertPriority.CRITICAL
        elif ratio >= 1.5:
            priority = AlertPriority.HIGH
        elif ratio >= 1.2:
            priority = AlertPriority.MEDIUM
        else:
            priority = AlertPriority.LOW

        confidence = min(0.95, 0.6 + ratio * 0.1)

        return self.create_alert(
            title=(
                f"{metric_name} esik asimi"
            ),
            description=(
                f"{metric_name} degeri {value:.2f}, "
                f"esik {threshold:.2f} "
                f"(oran: {ratio:.2f}x). "
                f"Trend: {trend}."
            ),
            priority=priority,
            confidence=confidence,
            category="threshold_breach",
            recommended_action=(
                f"{metric_name} icin acil "
                f"mudahale gerekebilir."
            ),
        )

    def get_accuracy(self) -> float:
        """Geçmiş tahminlerin doğruluğunu döndürür.

        Returns:
            Doğruluk yüzdesi (0.0-1.0).
        """
        if not self._accuracy_log:
            return 0.0

        accurate = sum(
            1
            for log in self._accuracy_log
            if log.get("was_accurate", False)
        )

        return accurate / len(self._accuracy_log)

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        return {
            **self._stats,
            "total_alerts": len(self._alerts),
            "active_alerts": sum(
                1
                for a in self._alerts.values()
                if not a.acknowledged
            ),
            "accuracy": self.get_accuracy(),
            "predictions_count": len(
                self._predictions
            ),
        }
