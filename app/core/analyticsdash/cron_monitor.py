"""
Cron izleme modülü.

Zamanlanmış görev izleme,
iş kaydı, yürütme takibi,
başarısız iş tespiti, sonraki çalışmalar.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

from app.models.analyticsdash_models import (
    CronJobMetric,
)

logger = logging.getLogger(__name__)

_MAX_JOBS = 500
_MAX_HISTORY_PER_JOB = 100


class CronMonitor:
    """Cron iş izleyicisi.

    Attributes:
        _jobs: Kayıtlı işler.
        _history: Yürütme geçmişi.
        _stats: İstatistikler.
    """

    def __init__(self) -> None:
        """İzleyiciyi başlatır."""
        self._jobs: dict[
            str, CronJobMetric
        ] = {}
        self._history: dict[
            str, list[dict]
        ] = {}
        self._stats: dict[str, int] = {
            "jobs_registered": 0,
            "executions_recorded": 0,
            "failures_detected": 0,
        }
        logger.info(
            "CronMonitor baslatildi"
        )

    @property
    def job_count(self) -> int:
        """İş sayısı."""
        return len(self._jobs)

    def register_job(
        self,
        job_name: str = "",
        schedule: str = "*/5 * * * *",
    ) -> str:
        """Cron işi kaydeder.

        Args:
            job_name: İş adı.
            schedule: Cron ifadesi.

        Returns:
            İş ID'si.
        """
        try:
            if len(self._jobs) >= _MAX_JOBS:
                logger.warning(
                    "Maksimum is sayisina ulasildi"
                )
                return ""

            job_id = str(uuid4())[:8]
            now = datetime.now(timezone.utc)

            metric = CronJobMetric(
                id=job_id,
                job_name=job_name,
                status="pending",
                next_run=now + timedelta(
                    minutes=5
                ),
            )

            self._jobs[job_name] = metric
            self._history[job_name] = []
            self._stats[
                "jobs_registered"
            ] += 1

            logger.info(
                f"Cron is kaydedildi: {job_name}"
            )
            return job_id

        except Exception as e:
            logger.error(
                f"Is kayit hatasi: {e}"
            )
            return ""

    def record_execution(
        self,
        job_name: str = "",
        status: str = "completed",
        duration: float = 0.0,
    ) -> None:
        """Yürütme kaydeder.

        Args:
            job_name: İş adı.
            status: Durum.
            duration: Süre (saniye).
        """
        try:
            job = self._jobs.get(job_name)
            if not job:
                logger.warning(
                    f"Is bulunamadi: {job_name}"
                )
                return

            now = datetime.now(timezone.utc)

            record = {
                "timestamp": now,
                "status": status,
                "duration": duration,
            }

            if job_name not in self._history:
                self._history[job_name] = []

            self._history[job_name].append(
                record
            )
            if (
                len(self._history[job_name])
                > _MAX_HISTORY_PER_JOB
            ):
                self._history[job_name] = (
                    self._history[job_name][
                        -_MAX_HISTORY_PER_JOB:
                    ]
                )

            job.last_run = now
            job.status = status
            job.next_run = now + timedelta(
                minutes=5
            )

            history = self._history[job_name]
            total_dur = sum(
                h["duration"] for h in history
            )
            job.avg_duration = round(
                total_dur / len(history), 3
            )

            if status == "failed":
                job.consecutive_failures += 1
                self._stats[
                    "failures_detected"
                ] += 1
            else:
                job.consecutive_failures = 0

            completed = sum(
                1
                for h in history
                if h["status"] == "completed"
            )
            job.success_rate = round(
                completed / len(history) * 100,
                2,
            )

            self._stats[
                "executions_recorded"
            ] += 1

        except Exception as e:
            logger.error(
                f"Yurutme kayit hatasi: {e}"
            )

    def get_job_status(
        self,
        job_name: str = "",
    ) -> CronJobMetric | None:
        """İş durumunu getirir.

        Args:
            job_name: İş adı.

        Returns:
            İş metriği veya None.
        """
        return self._jobs.get(job_name)

    def get_all_jobs(
        self,
    ) -> list[dict[str, Any]]:
        """Tüm işleri listeler.

        Returns:
            İş listesi.
        """
        try:
            result = []
            for name, job in self._jobs.items():
                result.append(
                    {
                        "id": job.id,
                        "job_name": name,
                        "status": job.status,
                        "last_run": (
                            job.last_run.isoformat()
                            if job.last_run
                            else None
                        ),
                        "next_run": (
                            job.next_run.isoformat()
                            if job.next_run
                            else None
                        ),
                        "avg_duration": (
                            job.avg_duration
                        ),
                        "success_rate": (
                            job.success_rate
                        ),
                        "consecutive_failures": (
                            job.consecutive_failures
                        ),
                    }
                )
            return result

        except Exception as e:
            logger.error(
                f"Is listeleme hatasi: {e}"
            )
            return []

    def get_failing_jobs(
        self,
    ) -> list[dict[str, Any]]:
        """Başarısız işleri getirir.

        Returns:
            Başarısız iş listesi.
        """
        try:
            failing = []
            for name, job in self._jobs.items():
                if (
                    job.consecutive_failures > 0
                    or job.success_rate < 90.0
                ):
                    failing.append(
                        {
                            "job_name": name,
                            "status": job.status,
                            "success_rate": (
                                job.success_rate
                            ),
                            "consecutive_failures": (
                                job.consecutive_failures
                            ),
                            "last_run": (
                                job.last_run.isoformat()
                                if job.last_run
                                else None
                            ),
                        }
                    )

            return sorted(
                failing,
                key=lambda x: x[
                    "consecutive_failures"
                ],
                reverse=True,
            )

        except Exception as e:
            logger.error(
                f"Basarisiz is sorgu hatasi: {e}"
            )
            return []

    def get_next_runs(
        self,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Sonraki çalışmaları getirir.

        Args:
            limit: Kaç iş.

        Returns:
            Sonraki çalışma listesi.
        """
        try:
            jobs_with_next = [
                {
                    "job_name": name,
                    "next_run": (
                        job.next_run.isoformat()
                        if job.next_run
                        else None
                    ),
                    "status": job.status,
                }
                for name, job in self._jobs.items()
                if job.next_run is not None
            ]

            return sorted(
                jobs_with_next,
                key=lambda x: x["next_run"]
                or "",
            )[:limit]

        except Exception as e:
            logger.error(
                f"Sonraki calisma hatasi: {e}"
            )
            return []

    def calculate_success_rate(
        self,
        job_name: str = "",
    ) -> float:
        """Başarı oranını hesaplar.

        Args:
            job_name: İş adı.

        Returns:
            Başarı oranı (0-100).
        """
        try:
            history = self._history.get(
                job_name, []
            )
            if not history:
                return 0.0

            completed = sum(
                1
                for h in history
                if h["status"] == "completed"
            )
            return round(
                completed
                / len(history)
                * 100,
                2,
            )

        except Exception as e:
            logger.error(
                f"Basari orani hatasi: {e}"
            )
            return 0.0

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri getirir.

        Returns:
            İstatistik bilgileri.
        """
        return {
            "total_jobs": len(self._jobs),
            "total_history": sum(
                len(h)
                for h in self._history.values()
            ),
            **self._stats,
        }
