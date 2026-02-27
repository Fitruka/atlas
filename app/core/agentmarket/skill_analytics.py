"""ATLAS Skill Analytics modulu.

Beceri analitigi: kurulum, kaldirim, kullanim,
trend, en populer, tutundurma orani.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.agentmarket_models import (
    AnalyticsPeriod,
    UsageMetric,
)

logger = logging.getLogger(__name__)

_DEFAULT_TRENDING_LIMIT = 10
_DEFAULT_TOP_LIMIT = 10


class SkillAnalytics:
    """Beceri analitik sistemi.

    Kurulum, kullanim ve performans
    metriklerini toplar ve analiz eder.

    Attributes:
        _metrics: Kullanim metrikleri.
        _install_counts: Kurulum sayilari.
        _uninstall_counts: Kaldirim sayilari.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Analitik sistemini baslatir."""
        self._metrics: dict[
            str, UsageMetric
        ] = {}
        self._listing_metrics: dict[
            str, dict[str, str]
        ] = {}
        self._install_counts: dict[
            str, int
        ] = {}
        self._uninstall_counts: dict[
            str, int
        ] = {}
        self._usage_data: dict[
            str, dict[str, Any]
        ] = {}
        self._ratings: dict[
            str, float
        ] = {}
        self._stats = {
            "installs_recorded": 0,
            "uninstalls_recorded": 0,
            "usage_events": 0,
            "metrics_queried": 0,
        }

        logger.info(
            "SkillAnalytics baslatildi",
        )

    def record_install(
        self,
        listing_id: str,
    ) -> None:
        """Kurulum kaydeder.

        Args:
            listing_id: Listeleme ID.
        """
        current = self._install_counts.get(
            listing_id, 0,
        )
        self._install_counts[listing_id] = (
            current + 1
        )

        # Metrik guncelle
        self._ensure_metric(listing_id)
        metric = self._get_current_metric(
            listing_id,
        )
        if metric:
            metric.installs += 1
            metric.active_users += 1

        self._stats["installs_recorded"] += 1

        logger.info(
            "Kurulum kaydedildi: %s",
            listing_id,
        )

    def record_uninstall(
        self,
        listing_id: str,
    ) -> None:
        """Kaldirim kaydeder.

        Args:
            listing_id: Listeleme ID.
        """
        current = self._uninstall_counts.get(
            listing_id, 0,
        )
        self._uninstall_counts[listing_id] = (
            current + 1
        )

        # Metrik guncelle
        metric = self._get_current_metric(
            listing_id,
        )
        if metric:
            metric.uninstalls += 1
            metric.active_users = max(
                0, metric.active_users - 1,
            )

        self._stats["uninstalls_recorded"] += 1

        logger.info(
            "Kaldirim kaydedildi: %s",
            listing_id,
        )

    def record_usage(
        self,
        listing_id: str,
        api_calls: int = 0,
        errors: int = 0,
        response_ms: float = 0.0,
    ) -> None:
        """Kullanim kaydeder.

        Args:
            listing_id: Listeleme ID.
            api_calls: API cagri sayisi.
            errors: Hata sayisi.
            response_ms: Ortalama yanit suresi.
        """
        self._ensure_metric(listing_id)
        metric = self._get_current_metric(
            listing_id,
        )
        if metric:
            metric.api_calls += api_calls
            if api_calls > 0:
                metric.error_rate = round(
                    errors / api_calls * 100, 2,
                )
            # Ortalama yanit suresi
            if metric.avg_response_ms > 0:
                metric.avg_response_ms = round(
                    (
                        metric.avg_response_ms
                        + response_ms
                    ) / 2,
                    2,
                )
            else:
                metric.avg_response_ms = (
                    response_ms
                )

        # Ham veri kaydi
        if listing_id not in self._usage_data:
            self._usage_data[listing_id] = {
                "total_api_calls": 0,
                "total_errors": 0,
                "total_response_ms": 0.0,
                "usage_count": 0,
            }

        data = self._usage_data[listing_id]
        data["total_api_calls"] += api_calls
        data["total_errors"] += errors
        data["total_response_ms"] += response_ms
        data["usage_count"] += 1

        self._stats["usage_events"] += 1

    def _ensure_metric(
        self,
        listing_id: str,
    ) -> None:
        """Metrik varligini saglar.

        Args:
            listing_id: Listeleme ID.
        """
        period_key = time.strftime("%Y-%m-%d")

        if listing_id not in (
            self._listing_metrics
        ):
            self._listing_metrics[
                listing_id
            ] = {}

        if period_key not in (
            self._listing_metrics[listing_id]
        ):
            metric = UsageMetric(
                listing_id=listing_id,
                period=AnalyticsPeriod.DAILY,
            )
            self._metrics[metric.id] = metric
            self._listing_metrics[listing_id][
                period_key
            ] = metric.id

    def _get_current_metric(
        self,
        listing_id: str,
    ) -> UsageMetric | None:
        """Guncel metrigi getirir.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Metrik veya None.
        """
        period_key = time.strftime("%Y-%m-%d")
        periods = self._listing_metrics.get(
            listing_id, {},
        )
        metric_id = periods.get(period_key)
        if metric_id:
            return self._metrics.get(metric_id)
        return None

    def get_metrics(
        self,
        listing_id: str,
        period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
    ) -> UsageMetric | None:
        """Metrikleri getirir.

        Args:
            listing_id: Listeleme ID.
            period: Donem.

        Returns:
            Metrik veya None.
        """
        self._stats["metrics_queried"] += 1

        # En son metrigi dondur
        periods = self._listing_metrics.get(
            listing_id, {},
        )
        if not periods:
            return None

        # Son donem
        latest_key = max(periods.keys())
        metric_id = periods[latest_key]
        return self._metrics.get(metric_id)

    def get_trending(
        self,
        period: AnalyticsPeriod = AnalyticsPeriod.DAILY,
        limit: int = _DEFAULT_TRENDING_LIMIT,
    ) -> list[dict[str, Any]]:
        """Trend listelemeler getirir.

        Args:
            period: Donem.
            limit: Maksimum sonuc.

        Returns:
            Trend listesi.
        """
        trending = []

        for (
            listing_id,
            install_count,
        ) in self._install_counts.items():
            usage = self._usage_data.get(
                listing_id, {},
            )
            score = (
                install_count * 10
                + usage.get(
                    "total_api_calls", 0,
                )
            )

            trending.append({
                "listing_id": listing_id,
                "installs": install_count,
                "api_calls": usage.get(
                    "total_api_calls", 0,
                ),
                "trend_score": score,
            })

        trending.sort(
            key=lambda t: t["trend_score"],
            reverse=True,
        )
        return trending[:limit]

    def get_top_rated(
        self,
        limit: int = _DEFAULT_TOP_LIMIT,
    ) -> list[dict[str, Any]]:
        """En yuksek puanli listeler.

        Args:
            limit: Maksimum sonuc.

        Returns:
            En puanli listesi.
        """
        rated = [
            {
                "listing_id": lid,
                "rating": rating,
                "installs": (
                    self._install_counts.get(
                        lid, 0,
                    )
                ),
            }
            for lid, rating
            in self._ratings.items()
        ]

        rated.sort(
            key=lambda r: r["rating"],
            reverse=True,
        )
        return rated[:limit]

    def set_rating(
        self,
        listing_id: str,
        rating: float,
    ) -> None:
        """Puan ayarlar (harici kaynak).

        Args:
            listing_id: Listeleme ID.
            rating: Puan.
        """
        self._ratings[listing_id] = rating

    def get_most_installed(
        self,
        limit: int = _DEFAULT_TOP_LIMIT,
    ) -> list[dict[str, Any]]:
        """En cok kurulan listeler.

        Args:
            limit: Maksimum sonuc.

        Returns:
            En cok kurulan listesi.
        """
        installed = [
            {
                "listing_id": lid,
                "installs": count,
                "uninstalls": (
                    self._uninstall_counts.get(
                        lid, 0,
                    )
                ),
            }
            for lid, count
            in self._install_counts.items()
        ]

        installed.sort(
            key=lambda i: i["installs"],
            reverse=True,
        )
        return installed[:limit]

    def get_retention_rate(
        self,
        listing_id: str,
    ) -> float:
        """Tutundurma oranini hesaplar.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Tutundurma orani (0.0-1.0).
        """
        installs = self._install_counts.get(
            listing_id, 0,
        )
        uninstalls = (
            self._uninstall_counts.get(
                listing_id, 0,
            )
        )

        if installs == 0:
            return 0.0

        retained = max(
            0, installs - uninstalls,
        )
        return round(
            retained / installs, 4,
        )

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        total_installs = sum(
            self._install_counts.values(),
        )
        total_uninstalls = sum(
            self._uninstall_counts.values(),
        )

        return {
            "total_metrics": len(
                self._metrics,
            ),
            "tracked_listings": len(
                self._listing_metrics,
            ),
            "total_installs": total_installs,
            "total_uninstalls": total_uninstalls,
            "net_installs": (
                total_installs
                - total_uninstalls
            ),
            **self._stats,
        }
