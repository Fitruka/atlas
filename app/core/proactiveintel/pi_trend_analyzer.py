"""ATLAS Sektorel Trend Analizcisi modulu.

Sektorel trend analizi, yukselen/dusen
trend tespiti, karsilastirma, momentum
hesaplama.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.proactiveintel_models import (
    TrendDirection,
    TrendRecord,
)

logger = logging.getLogger(__name__)

_MAX_TRENDS = 500
_MIN_DATA_POINTS_FOR_DIRECTION = 3
_VOLATILITY_THRESHOLD = 0.3


class PITrendAnalyzer:
    """Sektorel trend analizcisi.

    Trend takibi, yon analizi, momentum
    hesaplama ve karsilastirma islemleri.

    Attributes:
        _trends: Trend deposu.
    """

    def __init__(self) -> None:
        """Trend analizcisini baslatir."""
        self._trends: dict[str, TrendRecord] = {}
        self._stats: dict[str, Any] = {
            "trends_tracked": 0,
            "data_points_added": 0,
            "analyses_run": 0,
        }
        logger.info("PITrendAnalyzer baslatildi")

    def track(
        self,
        name: str,
        category: str,
        value: float,
        description: str = "",
    ) -> TrendRecord:
        """Trend verisi ekler.

        Args:
            name: Trend adi.
            category: Kategori.
            value: Yeni veri noktasi.
            description: Aciklama.

        Returns:
            Guncellenmis trend kaydi.
        """
        now = datetime.now(timezone.utc)

        if name in self._trends:
            trend = self._trends[name]
            points = list(trend.data_points)
            points.append(value)
            if len(points) > 100:
                points = points[-100:]

            direction = self._calculate_direction(
                points,
            )
            momentum = self._calculate_momentum(
                points,
            )

            updated = TrendRecord(
                id=trend.id,
                name=name,
                category=category,
                direction=direction,
                momentum=momentum,
                data_points=points,
                first_seen=trend.first_seen,
                last_updated=now,
                description=description or trend.description,
            )
            self._trends[name] = updated
            self._stats["data_points_added"] += 1
            return updated

        trend = TrendRecord(
            name=name,
            category=category,
            direction=TrendDirection.STABLE,
            momentum=0.0,
            data_points=[value],
            first_seen=now,
            last_updated=now,
            description=description,
        )
        self._trends[name] = trend
        self._stats["trends_tracked"] += 1
        self._stats["data_points_added"] += 1
        logger.info(
            "Yeni trend takibe alindi: %s", name,
        )
        return trend

    def get_trend(
        self,
        name: str,
    ) -> TrendRecord | None:
        """Trend kaydini getirir.

        Args:
            name: Trend adi.

        Returns:
            Trend kaydi veya None.
        """
        return self._trends.get(name)

    def analyze_direction(
        self,
        name: str,
    ) -> str:
        """Trend yonunu analiz eder.

        Args:
            name: Trend adi.

        Returns:
            Trend yonu.
        """
        self._stats["analyses_run"] += 1
        trend = self._trends.get(name)
        if not trend:
            return TrendDirection.STABLE

        return self._calculate_direction(
            trend.data_points,
        )

    def get_rising_trends(
        self,
        category: str | None = None,
    ) -> list[TrendRecord]:
        """Yukselen trendleri dondurur.

        Args:
            category: Kategori filtresi.

        Returns:
            Yukselen trendler.
        """
        return self._filter_trends(
            TrendDirection.RISING, category,
        )

    def get_declining_trends(
        self,
        category: str | None = None,
    ) -> list[TrendRecord]:
        """Dusen trendleri dondurur.

        Args:
            category: Kategori filtresi.

        Returns:
            Dusen trendler.
        """
        return self._filter_trends(
            TrendDirection.DECLINING, category,
        )

    def get_volatile_trends(self) -> list[TrendRecord]:
        """Oynak trendleri dondurur.

        Returns:
            Oynak trendler.
        """
        return self._filter_trends(
            TrendDirection.VOLATILE,
        )

    def compare_trends(
        self,
        names: list[str],
    ) -> dict[str, Any]:
        """Trendleri karsilastirir.

        Args:
            names: Karsilastirilacak trend adlari.

        Returns:
            Karsilastirma sonucu.
        """
        comparison: dict[str, Any] = {
            "trends": {},
            "strongest_rising": None,
            "strongest_declining": None,
        }

        best_momentum = -999.0
        worst_momentum = 999.0

        for name in names:
            trend = self._trends.get(name)
            if not trend:
                comparison["trends"][name] = None
                continue

            info = {
                "direction": trend.direction,
                "momentum": trend.momentum,
                "data_points": len(trend.data_points),
                "latest_value": (
                    trend.data_points[-1]
                    if trend.data_points
                    else None
                ),
            }
            comparison["trends"][name] = info

            if trend.momentum > best_momentum:
                best_momentum = trend.momentum
                comparison["strongest_rising"] = name

            if trend.momentum < worst_momentum:
                worst_momentum = trend.momentum
                comparison["strongest_declining"] = name

        return comparison

    def get_all_trends(
        self,
        category: str | None = None,
    ) -> list[TrendRecord]:
        """Tum trendleri dondurur.

        Args:
            category: Kategori filtresi.

        Returns:
            Trend listesi.
        """
        trends = list(self._trends.values())
        if category:
            trends = [
                t for t in trends
                if t.category == category
            ]
        return trends

    def _filter_trends(
        self,
        direction: str,
        category: str | None = None,
    ) -> list[TrendRecord]:
        """Trendleri filtreler.

        Args:
            direction: Yon filtresi.
            category: Kategori filtresi.

        Returns:
            Filtrelenmis trendler.
        """
        trends = [
            t for t in self._trends.values()
            if t.direction == direction
        ]
        if category:
            trends = [
                t for t in trends
                if t.category == category
            ]
        return sorted(
            trends,
            key=lambda t: abs(t.momentum),
            reverse=True,
        )

    def _calculate_direction(
        self,
        points: list[float],
    ) -> str:
        """Veri noktalarindan yon hesaplar.

        Args:
            points: Veri noktalari.

        Returns:
            Trend yonu.
        """
        if len(points) < _MIN_DATA_POINTS_FOR_DIRECTION:
            return TrendDirection.STABLE

        # Son noktalara bak
        recent = points[-_MIN_DATA_POINTS_FOR_DIRECTION:]
        diffs = [
            recent[i + 1] - recent[i]
            for i in range(len(recent) - 1)
        ]

        avg_val = sum(abs(d) for d in diffs) / len(diffs)
        mean_val = (
            sum(abs(p) for p in recent) / len(recent)
            if recent else 1.0
        )
        if mean_val == 0:
            mean_val = 1.0

        volatility = avg_val / mean_val

        if volatility > _VOLATILITY_THRESHOLD:
            pos = sum(1 for d in diffs if d > 0)
            neg = sum(1 for d in diffs if d < 0)
            if pos == neg or (pos > 0 and neg > 0):
                return TrendDirection.VOLATILE

        if all(d > 0 for d in diffs):
            return TrendDirection.RISING
        if all(d < 0 for d in diffs):
            return TrendDirection.DECLINING

        avg_diff = sum(diffs) / len(diffs)
        if avg_diff > 0:
            return TrendDirection.RISING
        elif avg_diff < 0:
            return TrendDirection.DECLINING

        return TrendDirection.STABLE

    def _calculate_momentum(
        self,
        points: list[float],
    ) -> float:
        """Momentum hesaplar.

        Args:
            points: Veri noktalari.

        Returns:
            Momentum degeri (-1.0 ile 1.0 arasi).
        """
        if len(points) < 2:
            return 0.0

        recent = points[-5:] if len(points) >= 5 else points
        diffs = [
            recent[i + 1] - recent[i]
            for i in range(len(recent) - 1)
        ]
        avg_diff = sum(diffs) / len(diffs)

        mean_val = (
            sum(abs(p) for p in recent) / len(recent)
            if recent else 1.0
        )
        if mean_val == 0:
            mean_val = 1.0

        momentum = avg_diff / mean_val
        return max(-1.0, min(1.0, round(momentum, 4)))

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Trend analizcisi istatistikleri.
        """
        direction_counts: dict[str, int] = {}
        for trend in self._trends.values():
            d = trend.direction
            direction_counts[d] = (
                direction_counts.get(d, 0) + 1
            )

        return {
            **self._stats,
            "total_trends": len(self._trends),
            "direction_distribution": direction_counts,
        }
