"""ATLAS Proaktif İstihbarat Duygu İzleyici modülü.

Marka duygu analizi, ortalama duygu hesaplama,
trend takibi, negatif uyarılar, dağılım analizi.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.proactiveintel_models import (
    SentimentLevel,
    SentimentRecord,
)

logger = logging.getLogger(__name__)

_MAX_RECORDS = 5000

_SENTIMENT_SCORES = {
    SentimentLevel.VERY_NEGATIVE: -1.0,
    SentimentLevel.NEGATIVE: -0.5,
    SentimentLevel.NEUTRAL: 0.0,
    SentimentLevel.POSITIVE: 0.5,
    SentimentLevel.VERY_POSITIVE: 1.0,
}


class PISentimentMonitor:
    """Proaktif duygu izleyici.

    Marka ve varlıklar hakkındaki duyguları analiz
    ederek trend ve uyarı üretir.

    Attributes:
        _records: Duygu analizi kayıtları.
        _entity_index: Varlık bazlı indeks.
    """

    def __init__(self) -> None:
        """Duygu izleyiciyi başlatır."""
        self._records: list[SentimentRecord] = []
        self._entity_index: dict[
            str, list[int]
        ] = {}
        self._stats = {
            "total_analyzed": 0,
            "negative_alerts": 0,
            "positive_count": 0,
            "negative_count": 0,
        }

        logger.info(
            "PISentimentMonitor baslatildi",
        )

    def analyze(
        self,
        text: str,
        source: str | None = None,
        entity: str | None = None,
        channel: str | None = None,
    ) -> SentimentRecord:
        """Metin duygu analizi yapar.

        Args:
            text: Analiz edilecek metin.
            source: Kaynak.
            entity: İlişkili varlık.
            channel: Kanal.

        Returns:
            Duygu analizi kaydı.
        """
        score = self._compute_score(text)
        level = self._score_to_level(score)

        record = SentimentRecord(
            id=str(uuid4())[:8],
            source=source or "unknown",
            text=text[:500],
            sentiment_level=level,
            score=score,
            analyzed_at=datetime.now(timezone.utc),
            entity=entity or "",
            channel=channel or "",
        )

        if len(self._records) >= _MAX_RECORDS:
            self._records = self._records[
                -(_MAX_RECORDS // 2) :
            ]
            self._rebuild_index()

        idx = len(self._records)
        self._records.append(record)

        if entity:
            if entity not in self._entity_index:
                self._entity_index[entity] = []
            self._entity_index[entity].append(idx)

        self._stats["total_analyzed"] += 1
        if score > 0:
            self._stats["positive_count"] += 1
        elif score < 0:
            self._stats["negative_count"] += 1

        logger.debug(
            "Duygu analizi: score=%.2f level=%s",
            score,
            level,
        )

        return record

    def _compute_score(self, text: str) -> float:
        """Metin için duygu skoru hesaplar.

        Args:
            text: Metin.

        Returns:
            Duygu skoru (-1.0 ile 1.0 arası).
        """
        positive_words = {
            "harika", "mukemmel", "guzel",
            "basarili", "iyi", "super",
            "great", "excellent", "good",
            "amazing", "love", "perfect",
            "fantastic", "wonderful", "best",
        }
        negative_words = {
            "kotu", "berbat", "sorun",
            "hata", "problem", "fail",
            "bad", "terrible", "awful",
            "horrible", "worst", "poor",
            "hate", "broken", "disappointed",
        }

        words = text.lower().split()
        if not words:
            return 0.0

        pos = sum(
            1 for w in words if w in positive_words
        )
        neg = sum(
            1 for w in words if w in negative_words
        )

        total = pos + neg
        if total == 0:
            return 0.0

        return (pos - neg) / max(total, 1)

    def _score_to_level(
        self, score: float
    ) -> str:
        """Skordan duygu seviyesine dönüştürür.

        Args:
            score: Duygu skoru.

        Returns:
            Duygu seviyesi.
        """
        if score >= 0.5:
            return SentimentLevel.VERY_POSITIVE
        elif score >= 0.1:
            return SentimentLevel.POSITIVE
        elif score > -0.1:
            return SentimentLevel.NEUTRAL
        elif score > -0.5:
            return SentimentLevel.NEGATIVE
        else:
            return SentimentLevel.VERY_NEGATIVE

    def _rebuild_index(self) -> None:
        """Varlık indeksini yeniden oluşturur."""
        self._entity_index.clear()
        for idx, rec in enumerate(self._records):
            if rec.entity:
                if rec.entity not in self._entity_index:
                    self._entity_index[rec.entity] = []
                self._entity_index[rec.entity].append(
                    idx
                )

    def get_average_sentiment(
        self,
        entity: str | None = None,
        days: int = 30,
    ) -> float:
        """Ortalama duygu skorunu döndürür.

        Args:
            entity: Varlık filtresi.
            days: Son kaç gün.

        Returns:
            Ortalama duygu skoru.
        """
        cutoff = datetime.now(
            timezone.utc
        ).timestamp() - (days * 86400)

        records = self._get_filtered(
            entity, cutoff
        )

        if not records:
            return 0.0

        return sum(r.score for r in records) / len(
            records
        )

    def get_sentiment_trend(
        self,
        entity: str | None = None,
        granularity: str = "day",
    ) -> list[dict[str, Any]]:
        """Duygu trendini döndürür.

        Args:
            entity: Varlık filtresi.
            granularity: Zaman çözünürlüğü.

        Returns:
            Trend veri noktaları.
        """
        records = self._get_filtered(entity)

        if not records:
            return []

        buckets: dict[str, list[float]] = {}
        for rec in records:
            if granularity == "hour":
                key = rec.analyzed_at.strftime(
                    "%Y-%m-%d %H:00"
                )
            elif granularity == "week":
                key = rec.analyzed_at.strftime(
                    "%Y-W%W"
                )
            else:
                key = rec.analyzed_at.strftime(
                    "%Y-%m-%d"
                )

            if key not in buckets:
                buckets[key] = []
            buckets[key].append(rec.score)

        return [
            {
                "period": period,
                "avg_score": sum(scores) / len(scores),
                "count": len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
            }
            for period, scores in sorted(
                buckets.items()
            )
        ]

    def get_negative_alerts(
        self, threshold: float = -0.5
    ) -> list[SentimentRecord]:
        """Negatif duygu uyarılarını döndürür.

        Args:
            threshold: Eşik skoru.

        Returns:
            Negatif kayıt listesi.
        """
        alerts = [
            r
            for r in self._records
            if r.score <= threshold
        ]

        self._stats["negative_alerts"] = len(alerts)

        return sorted(
            alerts,
            key=lambda r: r.score,
        )

    def get_sentiment_distribution(
        self, entity: str | None = None
    ) -> dict[str, int]:
        """Duygu dağılımını döndürür.

        Args:
            entity: Varlık filtresi.

        Returns:
            Seviye bazlı dağılım.
        """
        records = self._get_filtered(entity)

        distribution: dict[str, int] = {
            level.value: 0
            for level in SentimentLevel
        }

        for rec in records:
            level = rec.sentiment_level
            if level in distribution:
                distribution[level] += 1

        return distribution

    def get_records(
        self,
        entity: str | None = None,
        channel: str | None = None,
        limit: int = 100,
    ) -> list[SentimentRecord]:
        """Kayıtları filtreli döndürür.

        Args:
            entity: Varlık filtresi.
            channel: Kanal filtresi.
            limit: Maksimum sonuç.

        Returns:
            Kayıt listesi.
        """
        records = self._get_filtered(entity)

        if channel:
            records = [
                r
                for r in records
                if r.channel == channel
            ]

        return sorted(
            records,
            key=lambda r: r.analyzed_at,
            reverse=True,
        )[:limit]

    def _get_filtered(
        self,
        entity: str | None = None,
        cutoff: float | None = None,
    ) -> list[SentimentRecord]:
        """Filtrelenmiş kayıtları döndürür.

        Args:
            entity: Varlık filtresi.
            cutoff: Zaman eşiği (timestamp).

        Returns:
            Filtrelenmiş kayıtlar.
        """
        if entity and entity in self._entity_index:
            records = [
                self._records[i]
                for i in self._entity_index[entity]
                if i < len(self._records)
            ]
        elif entity:
            records = [
                r
                for r in self._records
                if r.entity == entity
            ]
        else:
            records = list(self._records)

        if cutoff:
            records = [
                r
                for r in records
                if r.analyzed_at.timestamp() >= cutoff
            ]

        return records

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        avg = 0.0
        if self._records:
            avg = sum(
                r.score for r in self._records
            ) / len(self._records)

        return {
            **self._stats,
            "total_records": len(self._records),
            "entities_tracked": len(
                self._entity_index
            ),
            "overall_sentiment": round(avg, 3),
        }
