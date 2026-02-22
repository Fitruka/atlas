"""Cron zamanlayici.

Is zamanlama, cron yurutme,
sonraki calistirma hesaplama ve gecmis.
"""

import logging
import time
from typing import Any, Callable
from uuid import uuid4

from app.models.nlcron_models import (
    JobStatus,
    RunRecord,
    RunStatus,
    ScheduledJob,
)

logger = logging.getLogger(__name__)

_MAX_JOBS = 10000
_MAX_HISTORY = 10000


class CronScheduler:
    """Cron zamanlayici.

    Is zamanlama, cron yurutme,
    sonraki calistirma hesaplama ve gecmis.

    Attributes:
        _jobs: Zamanlanmis isler.
        _handlers: Is isleyicileri.
        _run_history: Calistirma gecmisi.
    """

    def __init__(
        self,
        max_jobs: int = _MAX_JOBS,
    ) -> None:
        """CronScheduler baslatir.

        Args:
            max_jobs: Maks is sayisi.
        """
        self._jobs: dict[
            str, ScheduledJob
        ] = {}
        self._handlers: dict[
            str, Callable[..., Any]
        ] = {}
        self._run_history: list[
            RunRecord
        ] = []
        self._max_jobs: int = max_jobs
        self._total_runs: int = 0
        self._total_failures: int = 0

        logger.info(
            "CronScheduler baslatildi",
        )

    # ---- Is Zamanlama ----

    def schedule(
        self,
        job: ScheduledJob,
        handler: Callable[..., Any] | None = None,
    ) -> str:
        """Is zamanlar.

        Args:
            job: Zamanlanmis is.
            handler: Is isleyicisi.

        Returns:
            Is ID.
        """
        if len(self._jobs) >= self._max_jobs:
            logger.warning(
                "Maks is sayisi asildi: %d",
                self._max_jobs,
            )
            return ""

        self._jobs[job.job_id] = job
        if handler:
            self._handlers[job.job_id] = handler

        job.created_at = time.time()
        job.updated_at = job.created_at

        logger.info(
            "Is zamanlandi: %s (%s)",
            job.job_id, job.name,
        )
        return job.job_id

    def unschedule(
        self, job_id: str,
    ) -> bool:
        """Is zamanlamasini kaldirir.

        Args:
            job_id: Is ID.

        Returns:
            Basarili ise True.
        """
        if job_id not in self._jobs:
            return False

        self._jobs[job_id].status = (
            JobStatus.DELETED
        )
        self._handlers.pop(job_id, None)

        logger.info(
            "Is zamanlama kaldirildi: %s",
            job_id,
        )
        return True

    def get_job(
        self, job_id: str,
    ) -> ScheduledJob | None:
        """Isi dondurur.

        Args:
            job_id: Is ID.

        Returns:
            Is veya None.
        """
        return self._jobs.get(job_id)

    def get_active_jobs(
        self,
    ) -> list[ScheduledJob]:
        """Aktif isleri dondurur.

        Returns:
            Aktif is listesi.
        """
        return [
            j for j in self._jobs.values()
            if j.status == JobStatus.ACTIVE
        ]

    # ---- Cron Yurutme ----

    def execute_job(
        self, job_id: str,
    ) -> RunRecord:
        """Isi yurutur.

        Args:
            job_id: Is ID.

        Returns:
            Calistirma kaydi.
        """
        job = self._jobs.get(job_id)
        if not job:
            return RunRecord(
                job_id=job_id,
                status=RunStatus.FAILED,
                error_message="Is bulunamadi",
            )

        if job.status != JobStatus.ACTIVE:
            return RunRecord(
                job_id=job_id,
                status=RunStatus.SKIPPED,
                error_message=(
                    f"Is aktif degil: "
                    f"{job.status.value}"
                ),
            )

        # Esanli calistirma limiti
        if (
            job.max_concurrent_runs > 0
            and job.active_runs >= job.max_concurrent_runs
        ):
            return RunRecord(
                job_id=job_id,
                status=RunStatus.SKIPPED,
                error_message=(
                    f"Esanli limit asildi: "
                    f"{job.active_runs}/{job.max_concurrent_runs}"
                ),
            )

        # Spin loop onleme (min refire gap)
        now = time.time()
        if (
            job.last_run > 0
            and job.min_refire_gap_seconds > 0
            and (now - job.last_run) < job.min_refire_gap_seconds
        ):
            return RunRecord(
                job_id=job_id,
                status=RunStatus.SKIPPED,
                error_message="Min refire gap icinde",
            )

        job.active_runs += 1
        handler = self._handlers.get(job_id)
        record = RunRecord(
            run_id=str(uuid4())[:8],
            job_id=job_id,
            status=RunStatus.RUNNING,
            started_at=time.time(),
        )

        try:
            if handler:
                result = handler(job)
                record.output = (
                    {"result": str(result)}
                    if result
                    else {}
                )
            record.status = RunStatus.SUCCESS

        except Exception as e:
            record.status = RunStatus.FAILED
            record.error_message = str(e)
            self._total_failures += 1
            job.fail_count += 1

        record.completed_at = time.time()
        record.duration = (
            record.completed_at
            - record.started_at
        )

        job.active_runs = max(0, job.active_runs - 1)
        job.run_count += 1
        job.last_run = record.completed_at
        job.updated_at = record.completed_at
        self._total_runs += 1

        # Max runs kontrolu
        if (
            job.max_runs > 0
            and job.run_count >= job.max_runs
        ):
            job.status = JobStatus.COMPLETED

        self._record_run(record)
        return record

    def execute_due_jobs(
        self,
        current_time: float = 0.0,
    ) -> list[RunRecord]:
        """Zamani gelen isleri yurutur.

        Args:
            current_time: Simdi. 0 ise time.time().

        Returns:
            Calistirma kayitlari.
        """
        now = current_time or time.time()
        records: list[RunRecord] = []

        for job in self.get_active_jobs():
            if (
                job.next_run > 0
                and job.next_run <= now
            ):
                record = self.execute_job(
                    job.job_id,
                )
                records.append(record)

        return records

    # ---- Sonraki Calistirma ----

    def calculate_next_run(
        self,
        cron_expr: str,
        from_time: float = 0.0,
    ) -> float:
        """Sonraki calistirma zamanini hesaplar.

        Basit cron hesaplama.

        Args:
            cron_expr: Cron ifadesi.
            from_time: Baslangic zamani.

        Returns:
            Sonraki calistirma epoch.
        """
        now = from_time or time.time()
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return 0.0

        minute_part = parts[0]
        hour_part = parts[1]

        # Her dakika
        if all(p == "*" for p in parts):
            return now + 60

        # Her saat
        if (
            minute_part != "*"
            and hour_part == "*"
        ):
            return now + 3600

        # Gunluk
        if (
            minute_part != "*"
            and hour_part != "*"
        ):
            return now + 86400

        return now + 86400

    def update_next_run(
        self,
        job_id: str,
        next_run: float = 0.0,
    ) -> bool:
        """Sonraki calistirmayi gunceller.

        Args:
            job_id: Is ID.
            next_run: Sonraki zaman.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if next_run > 0:
            job.next_run = next_run
        else:
            job.next_run = (
                self.calculate_next_run(
                    job.cron_expression,
                )
            )

        job.updated_at = time.time()
        return True

    # ---- Gecmis ----

    def _record_run(
        self, record: RunRecord,
    ) -> None:
        """Calistirma kaydeder.

        Args:
            record: Calistirma kaydi.
        """
        self._run_history.append(record)

        if len(self._run_history) > (
            _MAX_HISTORY
        ):
            self._run_history = (
                self._run_history[-5000:]
            )

    def get_run_history(
        self,
        job_id: str = "",
        limit: int = 50,
    ) -> list[RunRecord]:
        """Calistirma gecmisini dondurur.

        Args:
            job_id: Is filtresi.
            limit: Maks sayi.

        Returns:
            Kayit listesi.
        """
        records = list(self._run_history)

        if job_id:
            records = [
                r for r in records
                if r.job_id == job_id
            ]

        return list(
            reversed(records[-limit:]),
        )

    def get_last_run(
        self, job_id: str,
    ) -> RunRecord | None:
        """Son calistirmayi dondurur.

        Args:
            job_id: Is ID.

        Returns:
            Son kayit veya None.
        """
        for r in reversed(self._run_history):
            if r.job_id == job_id:
                return r
        return None

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        active = len(self.get_active_jobs())
        return {
            "total_jobs": len(self._jobs),
            "active_jobs": active,
            "total_runs": self._total_runs,
            "total_failures": (
                self._total_failures
            ),
            "failure_rate": (
                self._total_failures
                / self._total_runs
                * 100
                if self._total_runs > 0
                else 0.0
            ),
            "max_jobs": self._max_jobs,
            "history_size": len(
                self._run_history,
            ),
        }
