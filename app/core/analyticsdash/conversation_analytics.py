"""
Konuşma analitik modülü.

Konuşma metriklerini izleme,
kanal bazlı özet, yanıt süresi trendi,
memnuniyet takibi, en aktif saatler.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.analyticsdash_models import (
    ConversationMetric,
)

logger = logging.getLogger(__name__)

_MAX_RECORDS = 10000


class ConversationAnalytics:
    """Konuşma analitik yöneticisi.

    Attributes:
        _messages: Mesaj kayıtları.
        _metrics: Periyodik metrikler.
        _stats: İstatistikler.
    """

    def __init__(self) -> None:
        """Analitik yöneticisini başlatır."""
        self._messages: list[dict] = []
        self._metrics: list[
            ConversationMetric
        ] = []
        self._stats: dict[str, int] = {
            "messages_recorded": 0,
            "summaries_generated": 0,
        }
        logger.info(
            "ConversationAnalytics baslatildi"
        )

    @property
    def message_count(self) -> int:
        """Mesaj sayısı."""
        return len(self._messages)

    def record_message(
        self,
        channel: str = "telegram",
        direction: str = "in",
        response_time: float | None = None,
        satisfaction: float | None = None,
    ) -> None:
        """Mesaj kaydeder.

        Args:
            channel: Kanal adı.
            direction: Yön (in/out).
            response_time: Yanıt süresi (sn).
            satisfaction: Memnuniyet puanı.
        """
        try:
            if (
                len(self._messages) >= _MAX_RECORDS
            ):
                self._messages = (
                    self._messages[
                        -(_MAX_RECORDS // 2) :
                    ]
                )

            record = {
                "id": str(uuid4())[:8],
                "channel": channel,
                "direction": direction,
                "response_time": response_time,
                "satisfaction": satisfaction,
                "timestamp": datetime.now(
                    timezone.utc
                ),
                "hour": datetime.now(
                    timezone.utc
                ).hour,
            }
            self._messages.append(record)
            self._stats[
                "messages_recorded"
            ] += 1

        except Exception as e:
            logger.error(
                f"Mesaj kayit hatasi: {e}"
            )

    def get_channel_summary(
        self,
        channel: str | None = None,
        period: str = "day",
    ) -> list[dict[str, Any]]:
        """Kanal bazlı özet getirir.

        Args:
            channel: Kanal filtresi.
            period: Dönem.

        Returns:
            Kanal özet listesi.
        """
        try:
            self._stats[
                "summaries_generated"
            ] += 1

            filtered = self._messages
            if channel:
                filtered = [
                    m
                    for m in filtered
                    if m["channel"] == channel
                ]

            channel_groups: dict[
                str, list[dict]
            ] = defaultdict(list)
            for msg in filtered:
                channel_groups[
                    msg["channel"]
                ].append(msg)

            summaries = []
            for ch, msgs in channel_groups.items():
                total = len(msgs)
                resp_times = [
                    m["response_time"]
                    for m in msgs
                    if m["response_time"]
                    is not None
                ]
                avg_resp = (
                    sum(resp_times)
                    / len(resp_times)
                    if resp_times
                    else 0.0
                )

                sats = [
                    m["satisfaction"]
                    for m in msgs
                    if m["satisfaction"]
                    is not None
                ]
                avg_sat = (
                    sum(sats) / len(sats)
                    if sats
                    else 0.0
                )

                metric = ConversationMetric(
                    channel=ch,
                    total_messages=total,
                    avg_response_time=round(
                        avg_resp, 2
                    ),
                    satisfaction_score=round(
                        avg_sat, 2
                    ),
                    period=period,
                )
                self._metrics.append(metric)

                summaries.append(
                    {
                        "channel": ch,
                        "total_messages": total,
                        "avg_response_time": round(
                            avg_resp, 2
                        ),
                        "satisfaction_score": round(
                            avg_sat, 2
                        ),
                        "period": period,
                    }
                )

            return summaries

        except Exception as e:
            logger.error(
                f"Ozet olusturma hatasi: {e}"
            )
            return []

    def get_response_time_trend(
        self,
        channel: str | None = None,
        granularity: str = "hour",
    ) -> list[dict[str, Any]]:
        """Yanıt süresi trendini getirir.

        Args:
            channel: Kanal filtresi.
            granularity: Ayrıntı düzeyi.

        Returns:
            Trend verileri.
        """
        try:
            filtered = self._messages
            if channel:
                filtered = [
                    m
                    for m in filtered
                    if m["channel"] == channel
                ]

            time_groups: dict[
                int, list[float]
            ] = defaultdict(list)
            for msg in filtered:
                if msg["response_time"] is not None:
                    key = msg["hour"]
                    time_groups[key].append(
                        msg["response_time"]
                    )

            trend = []
            for hour in sorted(
                time_groups.keys()
            ):
                values = time_groups[hour]
                trend.append(
                    {
                        "hour": hour,
                        "avg_response_time": round(
                            sum(values)
                            / len(values),
                            2,
                        ),
                        "count": len(values),
                        "min": round(
                            min(values), 2
                        ),
                        "max": round(
                            max(values), 2
                        ),
                    }
                )

            return trend

        except Exception as e:
            logger.error(
                f"Trend sorgulama hatasi: {e}"
            )
            return []

    def get_satisfaction_trend(
        self,
        period: str = "day",
    ) -> list[dict[str, Any]]:
        """Memnuniyet trendini getirir.

        Args:
            period: Dönem.

        Returns:
            Memnuniyet verileri.
        """
        try:
            channel_sats: dict[
                str, list[float]
            ] = defaultdict(list)
            for msg in self._messages:
                if msg["satisfaction"] is not None:
                    channel_sats[
                        msg["channel"]
                    ].append(msg["satisfaction"])

            result = []
            for ch, sats in channel_sats.items():
                result.append(
                    {
                        "channel": ch,
                        "avg_satisfaction": round(
                            sum(sats) / len(sats),
                            2,
                        ),
                        "count": len(sats),
                        "period": period,
                    }
                )

            return sorted(
                result,
                key=lambda x: x[
                    "avg_satisfaction"
                ],
                reverse=True,
            )

        except Exception as e:
            logger.error(
                f"Memnuniyet trend hatasi: {e}"
            )
            return []

    def get_top_channels(
        self,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """En aktif kanalları getirir.

        Args:
            limit: Kaç kanal.

        Returns:
            Kanal listesi.
        """
        try:
            channel_counts: dict[
                str, int
            ] = defaultdict(int)
            for msg in self._messages:
                channel_counts[
                    msg["channel"]
                ] += 1

            sorted_channels = sorted(
                channel_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            return [
                {
                    "channel": ch,
                    "message_count": count,
                    "rank": idx + 1,
                }
                for idx, (ch, count) in enumerate(
                    sorted_channels[:limit]
                )
            ]

        except Exception as e:
            logger.error(
                f"Kanal sorgulama hatasi: {e}"
            )
            return []

    def get_busiest_hours(
        self,
    ) -> dict[int, int]:
        """En yoğun saatleri getirir.

        Returns:
            Saat -> mesaj sayısı eşleşmesi.
        """
        try:
            hour_counts: dict[
                int, int
            ] = defaultdict(int)
            for msg in self._messages:
                hour_counts[msg["hour"]] += 1

            return dict(
                sorted(hour_counts.items())
            )

        except Exception as e:
            logger.error(
                f"Saat sorgulama hatasi: {e}"
            )
            return {}

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri getirir.

        Returns:
            İstatistik bilgileri.
        """
        return {
            "total_messages": len(
                self._messages
            ),
            "total_metrics": len(
                self._metrics
            ),
            **self._stats,
        }
