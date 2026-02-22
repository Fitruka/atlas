"""Zamanlama yoneticisi.

CRUD islemleri, is listeleme,
duraklat/devam et, sil ve degistir.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.nlcron_models import (
    JobStatus,
    RecurrenceType,
    ScheduledJob,
)

logger = logging.getLogger(__name__)

_MAX_JOBS = 10000


class ScheduleManager:
    """Zamanlama yoneticisi.

    CRUD islemleri, is listeleme,
    duraklat/devam et, sil ve degistir.

    Attributes:
        _jobs: Is deposu.
        _max_jobs: Maks is sayisi.
    """

    def __init__(
        self,
        max_jobs: int = _MAX_JOBS,
    ) -> None:
        """ScheduleManager baslatir.

        Args:
            max_jobs: Maks is sayisi.
        """
        self._jobs: dict[
            str, ScheduledJob
        ] = {}
        self._max_jobs: int = max_jobs
        self._total_created: int = 0
        self._total_deleted: int = 0
        self._total_modified: int = 0

        logger.info(
            "ScheduleManager baslatildi",
        )

    # ---- CRUD ----

    def create_job(
        self,
        name: str,
        schedule_text: str,
        cron_expression: str = "",
        recurrence_type: RecurrenceType = (
            RecurrenceType.ONCE
        ),
        task_type: str = "",
        task_config: dict[str, str]
        | None = None,
        tags: list[str] | None = None,
        timezone: str = "Europe/Istanbul",
        max_runs: int = 0,
    ) -> ScheduledJob:
        """Yeni is olusturur.

        Args:
            name: Is adi.
            schedule_text: Zamanlama metni.
            cron_expression: Cron ifadesi.
            recurrence_type: Yinelenme tipi.
            task_type: Gorev tipi.
            task_config: Gorev ayarlari.
            tags: Etiketler.
            timezone: Saat dilimi.
            max_runs: Maks calistirma.

        Returns:
            Olusturulan is.
        """
        now = time.time()
        job = ScheduledJob(
            job_id=str(uuid4())[:8],
            name=name,
            schedule_text=schedule_text,
            cron_expression=cron_expression,
            recurrence_type=recurrence_type,
            timezone=timezone,
            status=JobStatus.ACTIVE,
            task_type=task_type,
            task_config=task_config or {},
            created_at=now,
            updated_at=now,
            max_runs=max_runs,
            tags=tags or [],
        )

        self._jobs[job.job_id] = job
        self._total_created += 1

        logger.info(
            "Is olusturuldu: %s (%s)",
            job.job_id, name,
        )
        return job

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

    def update_job(
        self,
        job_id: str,
        **kwargs: Any,
    ) -> bool:
        """Isi gunceller.

        Args:
            job_id: Is ID.
            **kwargs: Guncellenecek alanlar.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        for key, val in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, val)

        job.updated_at = time.time()
        self._total_modified += 1
        return True

    def delete_job(
        self, job_id: str,
    ) -> bool:
        """Isi siler.

        Args:
            job_id: Is ID.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        job.status = JobStatus.DELETED
        job.updated_at = time.time()
        self._total_deleted += 1

        logger.info(
            "Is silindi: %s", job_id,
        )
        return True

    def remove_job(
        self, job_id: str,
    ) -> bool:
        """Isi tamamen kaldirir.

        Args:
            job_id: Is ID.

        Returns:
            Basarili ise True.
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._total_deleted += 1
            return True
        return False

    # ---- Listeleme ----

    def list_jobs(
        self,
        status: JobStatus | None = None,
        tag: str = "",
        task_type: str = "",
        limit: int = 100,
    ) -> list[ScheduledJob]:
        """Isleri listeler.

        Args:
            status: Durum filtresi.
            tag: Etiket filtresi.
            task_type: Gorev tipi filtresi.
            limit: Maks sayi.

        Returns:
            Is listesi.
        """
        jobs = list(self._jobs.values())

        if status is not None:
            jobs = [
                j for j in jobs
                if j.status == status
            ]

        if tag:
            jobs = [
                j for j in jobs
                if tag in j.tags
            ]

        if task_type:
            jobs = [
                j for j in jobs
                if j.task_type == task_type
            ]

        # Guncelleme tarihine gore sirala
        jobs.sort(
            key=lambda j: j.updated_at,
            reverse=True,
        )

        return jobs[:limit]

    def search_jobs(
        self,
        query: str,
        limit: int = 50,
    ) -> list[ScheduledJob]:
        """Isleri arar.

        Args:
            query: Arama sorgusu.
            limit: Maks sayi.

        Returns:
            Eslesen isler.
        """
        q = query.lower()
        results: list[ScheduledJob] = []

        for job in self._jobs.values():
            if (
                q in job.name.lower()
                or q in job.description.lower()
                or q in job.schedule_text.lower()
                or any(
                    q in t.lower()
                    for t in job.tags
                )
            ):
                results.append(job)

        return results[:limit]

    # ---- Duraklat / Devam Et ----

    def pause_job(
        self, job_id: str,
    ) -> bool:
        """Isi duraklatir.

        Args:
            job_id: Is ID.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status != JobStatus.ACTIVE:
            return False

        job.status = JobStatus.PAUSED
        job.updated_at = time.time()
        return True

    def resume_job(
        self, job_id: str,
    ) -> bool:
        """Isi devam ettirir.

        Args:
            job_id: Is ID.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status != JobStatus.PAUSED:
            return False

        job.status = JobStatus.ACTIVE
        job.updated_at = time.time()
        return True

    def pause_all(self) -> int:
        """Tum aktif isleri duraklatir.

        Returns:
            Duraklanan sayi.
        """
        count = 0
        for job in self._jobs.values():
            if job.status == JobStatus.ACTIVE:
                job.status = JobStatus.PAUSED
                job.updated_at = time.time()
                count += 1
        return count

    def resume_all(self) -> int:
        """Tum duraklamis isleri devam ettirir.

        Returns:
            Devam ettirilen sayi.
        """
        count = 0
        for job in self._jobs.values():
            if job.status == JobStatus.PAUSED:
                job.status = JobStatus.ACTIVE
                job.updated_at = time.time()
                count += 1
        return count

    # ---- Degistirme ----

    def modify_schedule(
        self,
        job_id: str,
        schedule_text: str = "",
        cron_expression: str = "",
        recurrence_type: (
            RecurrenceType | None
        ) = None,
    ) -> bool:
        """Zamanlama degistirir.

        Args:
            job_id: Is ID.
            schedule_text: Yeni zamanlama.
            cron_expression: Yeni cron.
            recurrence_type: Yeni tekrar.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if schedule_text:
            job.schedule_text = schedule_text
        if cron_expression:
            job.cron_expression = cron_expression
        if recurrence_type is not None:
            job.recurrence_type = recurrence_type

        job.updated_at = time.time()
        self._total_modified += 1
        return True

    def modify_task(
        self,
        job_id: str,
        task_type: str = "",
        task_config: dict[str, str]
        | None = None,
    ) -> bool:
        """Gorev ayarlarini degistirir.

        Args:
            job_id: Is ID.
            task_type: Yeni gorev tipi.
            task_config: Yeni ayarlar.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if task_type:
            job.task_type = task_type
        if task_config is not None:
            job.task_config = task_config

        job.updated_at = time.time()
        self._total_modified += 1
        return True

    def add_tags(
        self,
        job_id: str,
        tags: list[str],
    ) -> bool:
        """Etiket ekler.

        Args:
            job_id: Is ID.
            tags: Etiketler.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        for tag in tags:
            if tag not in job.tags:
                job.tags.append(tag)

        job.updated_at = time.time()
        return True

    def remove_tags(
        self,
        job_id: str,
        tags: list[str],
    ) -> bool:
        """Etiket kaldirir.

        Args:
            job_id: Is ID.
            tags: Etiketler.

        Returns:
            Basarili ise True.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        for tag in tags:
            if tag in job.tags:
                job.tags.remove(tag)

        job.updated_at = time.time()
        return True

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        status_counts: dict[str, int] = {}
        for job in self._jobs.values():
            s = job.status.value
            status_counts[s] = (
                status_counts.get(s, 0) + 1
            )

        return {
            "total_jobs": len(self._jobs),
            "status_counts": status_counts,
            "total_created": (
                self._total_created
            ),
            "total_deleted": (
                self._total_deleted
            ),
            "total_modified": (
                self._total_modified
            ),
            "max_jobs": self._max_jobs,
        }
