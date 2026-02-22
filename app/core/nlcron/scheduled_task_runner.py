"""Zamanlanmis gorev yurutucu.

Gorev yurutme, sonuc isleme,
hata kurtarma ve bildirim.
"""

import logging
import time
from typing import Any, Callable

from app.models.nlcron_models import (
    JobStatus,
    RunRecord,
    RunStatus,
    ScheduledJob,
)

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY = 5.0
_MAX_NOTIFICATIONS = 10000


class ScheduledTaskRunner:
    """Zamanlanmis gorev yurutucu.

    Gorev yurutme, sonuc isleme,
    hata kurtarma ve bildirim.

    Attributes:
        _task_handlers: Gorev isleyicileri.
        _notifications: Bildirim gecmisi.
        _retry_counts: Yeniden deneme sayaclari.
    """

    def __init__(
        self,
        max_retries: int = _MAX_RETRIES,
        retry_delay: float = _RETRY_DELAY,
    ) -> None:
        """ScheduledTaskRunner baslatir.

        Args:
            max_retries: Maks yeniden deneme.
            retry_delay: Yeniden deneme gecikmesi.
        """
        self._task_handlers: dict[
            str, Callable[..., Any]
        ] = {}
        self._notifications: list[
            dict[str, Any]
        ] = []
        self._retry_counts: dict[
            str, int
        ] = {}
        self._max_retries: int = max_retries
        self._retry_delay: float = retry_delay
        self._total_executions: int = 0
        self._total_successes: int = 0
        self._total_failures: int = 0
        self._notification_callback: (
            Callable[[dict[str, Any]], None]
            | None
        ) = None

        logger.info(
            "ScheduledTaskRunner baslatildi",
        )

    # ---- Gorev Yurutme ----

    def register_handler(
        self,
        task_type: str,
        handler: Callable[..., Any],
    ) -> None:
        """Gorev isleyicisi kaydeder.

        Args:
            task_type: Gorev tipi.
            handler: Isleyici fonksiyon.
        """
        self._task_handlers[task_type] = handler

    def run_task(
        self,
        job: ScheduledJob,
    ) -> RunRecord:
        """Gorevi yurutur.

        Args:
            job: Zamanlanmis is.

        Returns:
            Calistirma kaydi.
        """
        self._total_executions += 1

        record = RunRecord(
            job_id=job.job_id,
            status=RunStatus.RUNNING,
            started_at=time.time(),
        )

        handler = self._task_handlers.get(
            job.task_type,
        )
        if not handler:
            record.status = RunStatus.FAILED
            record.error_message = (
                f"Isleyici bulunamadi: "
                f"{job.task_type}"
            )
            record.completed_at = time.time()
            record.duration = (
                record.completed_at
                - record.started_at
            )
            self._total_failures += 1
            self._notify(
                job, record, "failure",
            )
            return record

        try:
            result = handler(
                job.task_config,
            )
            record.status = RunStatus.SUCCESS
            record.output = (
                {"result": str(result)}
                if result
                else {}
            )
            self._total_successes += 1
            self._notify(
                job, record, "success",
            )

        except Exception as e:
            record.status = RunStatus.FAILED
            record.error_message = str(e)
            self._total_failures += 1
            self._notify(
                job, record, "failure",
            )

        record.completed_at = time.time()
        record.duration = (
            record.completed_at
            - record.started_at
        )

        return record

    def run_with_retry(
        self,
        job: ScheduledJob,
    ) -> RunRecord:
        """Yeniden denemeli yurutme.

        Args:
            job: Zamanlanmis is.

        Returns:
            Son calistirma kaydi.
        """
        attempt = 0
        last_record = RunRecord(
            job_id=job.job_id,
            status=RunStatus.FAILED,
        )

        while attempt <= self._max_retries:
            record = self.run_task(job)
            last_record = record

            if record.status == RunStatus.SUCCESS:
                self._retry_counts.pop(
                    job.job_id, None,
                )
                return record

            attempt += 1
            self._retry_counts[job.job_id] = (
                attempt
            )

            if attempt > self._max_retries:
                break

            logger.warning(
                "Yeniden deneme %d/%d: %s",
                attempt, self._max_retries,
                job.job_id,
            )

        # Maks deneme asildi
        if (
            last_record.status
            == RunStatus.FAILED
        ):
            job.status = JobStatus.FAILED
            self._notify(
                job, last_record,
                "max_retries_exceeded",
            )

        return last_record

    # ---- Sonuc Isleme ----

    def handle_result(
        self,
        job: ScheduledJob,
        record: RunRecord,
    ) -> dict[str, Any]:
        """Sonucu isler.

        Args:
            job: Zamanlanmis is.
            record: Calistirma kaydi.

        Returns:
            Isleme sonucu.
        """
        result: dict[str, Any] = {
            "job_id": job.job_id,
            "run_id": record.run_id,
            "status": record.status.value,
            "duration": record.duration,
        }

        if record.status == RunStatus.SUCCESS:
            job.run_count += 1
            job.last_run = record.completed_at
            result["output"] = record.output

        elif record.status == RunStatus.FAILED:
            job.fail_count += 1
            result["error"] = (
                record.error_message
            )

        # Max runs kontrolu
        if (
            job.max_runs > 0
            and job.run_count >= job.max_runs
        ):
            job.status = JobStatus.COMPLETED
            result["completed"] = True

        job.updated_at = time.time()
        return result

    # ---- Hata Kurtarma ----

    def recover_failed_job(
        self,
        job: ScheduledJob,
    ) -> bool:
        """Basarisiz isi kurtarir.

        Args:
            job: Zamanlanmis is.

        Returns:
            Kurtarildi ise True.
        """
        if job.status != JobStatus.FAILED:
            return False

        job.status = JobStatus.ACTIVE
        job.fail_count = 0
        job.updated_at = time.time()
        self._retry_counts.pop(
            job.job_id, None,
        )

        self._notify(
            job, None, "recovered",
        )

        logger.info(
            "Is kurtarildi: %s", job.job_id,
        )
        return True

    def get_retry_count(
        self, job_id: str,
    ) -> int:
        """Yeniden deneme sayisini dondurur.

        Args:
            job_id: Is ID.

        Returns:
            Deneme sayisi.
        """
        return self._retry_counts.get(
            job_id, 0,
        )

    # ---- Bildirim ----

    def set_notification_callback(
        self,
        callback: Callable[
            [dict[str, Any]], None
        ],
    ) -> None:
        """Bildirim geri aramasini ayarlar.

        Args:
            callback: Geri arama fonksiyonu.
        """
        self._notification_callback = callback

    def _notify(
        self,
        job: ScheduledJob,
        record: RunRecord | None,
        event_type: str,
    ) -> None:
        """Bildirim gonderir.

        Args:
            job: Zamanlanmis is.
            record: Calistirma kaydi.
            event_type: Olay tipi.
        """
        notification: dict[str, Any] = {
            "event": event_type,
            "job_id": job.job_id,
            "job_name": job.name,
            "timestamp": time.time(),
        }

        if record:
            notification["run_id"] = (
                record.run_id
            )
            notification["status"] = (
                record.status.value
            )
            if record.error_message:
                notification["error"] = (
                    record.error_message
                )

        self._notifications.append(
            notification,
        )

        if len(self._notifications) > (
            _MAX_NOTIFICATIONS
        ):
            self._notifications = (
                self._notifications[-5000:]
            )

        if self._notification_callback:
            try:
                self._notification_callback(
                    notification,
                )
            except Exception as e:
                logger.error(
                    "Bildirim hatasi: %s", e,
                )

    def get_notifications(
        self,
        job_id: str = "",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Bildirimleri dondurur.

        Args:
            job_id: Is filtresi.
            limit: Maks sayi.

        Returns:
            Bildirim listesi.
        """
        records = list(self._notifications)

        if job_id:
            records = [
                r for r in records
                if r.get("job_id") == job_id
            ]

        return list(
            reversed(records[-limit:]),
        )

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_executions": (
                self._total_executions
            ),
            "total_successes": (
                self._total_successes
            ),
            "total_failures": (
                self._total_failures
            ),
            "success_rate": (
                self._total_successes
                / self._total_executions
                * 100
                if self._total_executions > 0
                else 0.0
            ),
            "registered_handlers": len(
                self._task_handlers,
            ),
            "pending_retries": len(
                self._retry_counts,
            ),
            "notification_count": len(
                self._notifications,
            ),
            "max_retries": self._max_retries,
        }
