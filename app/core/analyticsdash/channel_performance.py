"""
Kanal performans modülü.

Kanal bazlı performans metrikleri,
aktivite kayıt, metrik sorgulama,
en aktif kanal, yanıt süresi karşılaştırma.
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.analyticsdash_models import (
    ChannelMetric,
    ChannelType,
)

logger = logging.getLogger(__name__)

_MAX_RECORDS = 10000


class ChannelPerformance:
    """Kanal performans izleyicisi.

    Attributes:
        _records: Aktivite kayıtları.
        _metrics: Metrik listesi.
        _stats: İstatistikler.
    """

    def __init__(self) -> None:
        """İzleyiciyi başlatır."""
        self._records: list[dict] = []
        self._metrics: list[
            ChannelMetric
        ] = []
        self._stats: dict[str, int] = {
            "activities_recorded": 0,
            "queries_performed": 0,
        }
        logger.info(
            "ChannelPerformance baslatildi"
        )

    @property
    def record_count(self) -> int:
        """Kayıt sayısı."""
        return len(self._records)

    def record_activity(
        self,
        channel_type: str = "telegram",
        messages_in: int = 0,
        messages_out: int = 0,
        active_users: int = 0,
        response_time: float | None = None,
    ) -> None:
        """Kanal aktivitesi kaydeder.

        Args:
            channel_type: Kanal türü.
            messages_in: Gelen mesaj.
            messages_out: Giden mesaj.
            active_users: Aktif kullanıcı.
            response_time: Yanıt süresi (sn).
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
                "channel_type": channel_type,
                "messages_in": messages_in,
                "messages_out": messages_out,
                "active_users": active_users,
                "response_time": response_time,
                "timestamp": datetime.now(
                    timezone.utc
                ),
                "day": datetime.now(
                    timezone.utc
                ).strftime("%Y-%m-%d"),
            }
            self._records.append(record)
            self._stats[
                "activities_recorded"
            ] += 1

        except Exception as e:
            logger.error(
                f"Aktivite kayit hatasi: {e}"
            )

    def get_channel_metrics(
        self,
        channel_type: str | None = None,
        period: str = "day",
    ) -> list[dict[str, Any]]:
        """Kanal metriklerini getirir.

        Args:
            channel_type: Kanal türü filtresi.
            period: Dönem.

        Returns:
            Metrik listesi.
        """
        try:
            self._stats[
                "queries_performed"
            ] += 1

            filtered = self._records
            if channel_type:
                filtered = [
                    r
                    for r in filtered
                    if r["channel_type"]
                    == channel_type
                ]

            channel_groups: dict[
                str, list[dict]
            ] = defaultdict(list)
            for rec in filtered:
                channel_groups[
                    rec["channel_type"]
                ].append(rec)

            results = []
            for ch, recs in channel_groups.items():
                total_in = sum(
                    r["messages_in"]
                    for r in recs
                )
                total_out = sum(
                    r["messages_out"]
                    for r in recs
                )
                max_users = max(
                    (
                        r["active_users"]
                        for r in recs
                    ),
                    default=0,
                )

                resp_times = [
                    r["response_time"]
                    for r in recs
                    if r["response_time"]
                    is not None
                ]
                avg_resp = (
                    sum(resp_times)
                    / len(resp_times)
                    if resp_times
                    else 0.0
                )

                metric = ChannelMetric(
                    channel_type=ch,
                    messages_in=total_in,
                    messages_out=total_out,
                    active_users=max_users,
                    avg_response_time=round(
                        avg_resp, 2
                    ),
                    period=period,
                )
                self._metrics.append(metric)

                results.append(
                    {
                        "channel_type": ch,
                        "messages_in": total_in,
                        "messages_out": total_out,
                        "total_messages": (
                            total_in + total_out
                        ),
                        "active_users": max_users,
                        "avg_response_time": round(
                            avg_resp, 2
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

    def get_most_active_channel(
        self,
    ) -> str | None:
        """En aktif kanalı getirir.

        Returns:
            Kanal türü veya None.
        """
        try:
            if not self._records:
                return None

            channel_totals: dict[
                str, int
            ] = defaultdict(int)
            for r in self._records:
                channel_totals[
                    r["channel_type"]
                ] += (
                    r["messages_in"]
                    + r["messages_out"]
                )

            if not channel_totals:
                return None

            return max(
                channel_totals,
                key=channel_totals.get,  # type: ignore[arg-type]
            )

        except Exception as e:
            logger.error(
                f"Aktif kanal sorgulama hatasi: {e}"
            )
            return None

    def get_response_time_comparison(
        self,
    ) -> dict[str, float]:
        """Yanıt süresi karşılaştırmasını getirir.

        Returns:
            Kanal -> ortalama süre eşleşmesi.
        """
        try:
            channel_times: dict[
                str, list[float]
            ] = defaultdict(list)
            for r in self._records:
                if r["response_time"] is not None:
                    channel_times[
                        r["channel_type"]
                    ].append(r["response_time"])

            return {
                ch: round(
                    sum(times) / len(times), 2
                )
                for ch, times in channel_times.items()
                if times
            }

        except Exception as e:
            logger.error(
                f"Karsilastirma hatasi: {e}"
            )
            return {}

    def get_channel_growth(
        self,
        channel_type: str = "telegram",
        periods: int = 7,
    ) -> list[dict[str, Any]]:
        """Kanal büyümesini getirir.

        Args:
            channel_type: Kanal türü.
            periods: Dönem sayısı.

        Returns:
            Büyüme verileri.
        """
        try:
            filtered = [
                r
                for r in self._records
                if r["channel_type"]
                == channel_type
            ]

            day_groups: dict[
                str, dict[str, int]
            ] = defaultdict(
                lambda: {
                    "messages_in": 0,
                    "messages_out": 0,
                    "active_users": 0,
                }
            )

            for r in filtered:
                day = r["day"]
                day_groups[day][
                    "messages_in"
                ] += r["messages_in"]
                day_groups[day][
                    "messages_out"
                ] += r["messages_out"]
                day_groups[day][
                    "active_users"
                ] = max(
                    day_groups[day][
                        "active_users"
                    ],
                    r["active_users"],
                )

            growth = []
            for day in sorted(
                day_groups.keys()
            )[-periods:]:
                data = day_groups[day]
                growth.append(
                    {
                        "day": day,
                        "messages_in": data[
                            "messages_in"
                        ],
                        "messages_out": data[
                            "messages_out"
                        ],
                        "total": (
                            data["messages_in"]
                            + data[
                                "messages_out"
                            ]
                        ),
                        "active_users": data[
                            "active_users"
                        ],
                    }
                )

            return growth

        except Exception as e:
            logger.error(
                f"Buyume sorgulama hatasi: {e}"
            )
            return []

    def compare_channels(
        self,
    ) -> list[dict[str, Any]]:
        """Kanalları karşılaştırır.

        Returns:
            Sıralı kanal listesi.
        """
        try:
            metrics = self.get_channel_metrics()

            return sorted(
                metrics,
                key=lambda x: x.get(
                    "total_messages", 0
                ),
                reverse=True,
            )

        except Exception as e:
            logger.error(
                f"Kanal karsilastirma hatasi: {e}"
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
            "unique_channels": len(
                {
                    r["channel_type"]
                    for r in self._records
                }
            ),
            **self._stats,
        }
