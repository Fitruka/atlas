"""Gorev kaliciligi.

Is depolama, kurtarma,
migrasyon ve temizlik.
"""

import json
import logging
import time
from typing import Any

from app.models.nlcron_models import (
    JobStatus,
    RecurrenceType,
    ScheduledJob,
)

logger = logging.getLogger(__name__)

_MAX_SNAPSHOTS = 100
_DEFAULT_RETENTION_DAYS = 30


class TaskPersistence:
    """Gorev kaliciligi.

    Is depolama, kurtarma,
    migrasyon ve temizlik.

    Attributes:
        _store: Is deposu.
        _snapshots: Anlk goruntuler.
        _metadata: Depo metadata.
    """

    def __init__(
        self,
        retention_days: int = (
            _DEFAULT_RETENTION_DAYS
        ),
    ) -> None:
        """TaskPersistence baslatir.

        Args:
            retention_days: Saklama suresi (gun).
        """
        self._store: dict[
            str, dict[str, Any]
        ] = {}
        self._snapshots: list[
            dict[str, Any]
        ] = []
        self._metadata: dict[str, Any] = {
            "created_at": time.time(),
            "version": "1.0",
            "total_saves": 0,
            "total_loads": 0,
        }
        self._retention_days: int = (
            retention_days
        )

        logger.info(
            "TaskPersistence baslatildi",
        )

    # ---- Is Depolama ----

    def save_job(
        self, job: ScheduledJob,
    ) -> bool:
        """Isi kaydeder.

        Args:
            job: Zamanlanmis is.

        Returns:
            Basarili ise True.
        """
        data = job.model_dump()
        # Enum'lari string'e cevir
        data["status"] = job.status.value
        data["recurrence_type"] = (
            job.recurrence_type.value
        )

        self._store[job.job_id] = data
        self._metadata["total_saves"] = (
            self._metadata.get(
                "total_saves", 0,
            ) + 1
        )

        logger.debug(
            "Is kaydedildi: %s", job.job_id,
        )
        return True

    def load_job(
        self, job_id: str,
    ) -> ScheduledJob | None:
        """Isi yukler.

        Args:
            job_id: Is ID.

        Returns:
            Is veya None.
        """
        data = self._store.get(job_id)
        if not data:
            return None

        self._metadata["total_loads"] = (
            self._metadata.get(
                "total_loads", 0,
            ) + 1
        )

        try:
            job = ScheduledJob(**data)
            return job
        except Exception as e:
            logger.error(
                "Is yukleme hatasi %s: %s",
                job_id, e,
            )
            return None

    def save_all(
        self,
        jobs: list[ScheduledJob],
    ) -> int:
        """Tum isleri kaydeder.

        Args:
            jobs: Is listesi.

        Returns:
            Kaydedilen sayi.
        """
        count = 0
        for job in jobs:
            if self.save_job(job):
                count += 1
        return count

    def load_all(self) -> list[ScheduledJob]:
        """Tum isleri yukler.

        Returns:
            Is listesi.
        """
        jobs: list[ScheduledJob] = []
        for job_id in list(self._store.keys()):
            job = self.load_job(job_id)
            if job:
                jobs.append(job)
        return jobs

    def delete_job(
        self, job_id: str,
    ) -> bool:
        """Isi siler.

        Args:
            job_id: Is ID.

        Returns:
            Basarili ise True.
        """
        if job_id in self._store:
            del self._store[job_id]
            return True
        return False

    def exists(self, job_id: str) -> bool:
        """Is var mi kontrol eder.

        Args:
            job_id: Is ID.

        Returns:
            Varsa True.
        """
        return job_id in self._store

    # ---- Kurtarma ----

    def create_snapshot(self) -> str:
        """Anlik goruntu olusturur.

        Returns:
            Goruntu ID.
        """
        snapshot_id = f"snap_{int(time.time())}"
        snapshot: dict[str, Any] = {
            "id": snapshot_id,
            "timestamp": time.time(),
            "job_count": len(self._store),
            "data": dict(self._store),
        }

        self._snapshots.append(snapshot)

        if len(self._snapshots) > _MAX_SNAPSHOTS:
            self._snapshots = (
                self._snapshots[-50:]
            )

        logger.info(
            "Goruntu olusturuldu: %s",
            snapshot_id,
        )
        return snapshot_id

    def restore_snapshot(
        self, snapshot_id: str,
    ) -> int:
        """Goruntuyu geri yukler.

        Args:
            snapshot_id: Goruntu ID.

        Returns:
            Yuklenen is sayisi.
        """
        for snap in reversed(self._snapshots):
            if snap["id"] == snapshot_id:
                self._store = dict(
                    snap["data"],
                )
                logger.info(
                    "Goruntu geri yuklendi: %s",
                    snapshot_id,
                )
                return len(self._store)

        logger.warning(
            "Goruntu bulunamadi: %s",
            snapshot_id,
        )
        return 0

    def get_snapshots(
        self,
    ) -> list[dict[str, Any]]:
        """Goruntuler listesini dondurur.

        Returns:
            Goruntu bilgileri.
        """
        return [
            {
                "id": s["id"],
                "timestamp": s["timestamp"],
                "job_count": s["job_count"],
            }
            for s in self._snapshots
        ]

    # ---- Migrasyon ----

    def export_data(self) -> str:
        """Verileri disa aktarir.

        Returns:
            JSON string.
        """
        export: dict[str, Any] = {
            "version": self._metadata.get(
                "version", "1.0",
            ),
            "exported_at": time.time(),
            "jobs": dict(self._store),
            "metadata": dict(self._metadata),
        }
        return json.dumps(
            export, default=str,
        )

    def import_data(
        self,
        data: str,
        merge: bool = False,
    ) -> int:
        """Verileri iceri aktarir.

        Args:
            data: JSON string.
            merge: Birlestir mi.

        Returns:
            Yuklenen is sayisi.
        """
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(
                "JSON parse hatasi: %s", e,
            )
            return 0

        jobs = parsed.get("jobs", {})

        if not merge:
            self._store.clear()

        for job_id, job_data in jobs.items():
            self._store[job_id] = job_data

        logger.info(
            "Veri aktarildi: %d is",
            len(jobs),
        )
        return len(jobs)

    def migrate(
        self,
        from_version: str,
        to_version: str,
    ) -> int:
        """Veri migrasyonu yapar.

        Args:
            from_version: Kaynak versiyon.
            to_version: Hedef versiyon.

        Returns:
            Migrate edilen is sayisi.
        """
        migrated = 0

        for job_id, data in self._store.items():
            # Eksik alanlari ekle
            if "tags" not in data:
                data["tags"] = []
            if "max_runs" not in data:
                data["max_runs"] = 0
            if "fail_count" not in data:
                data["fail_count"] = 0
            migrated += 1

        self._metadata["version"] = to_version

        logger.info(
            "Migrasyon tamamlandi: "
            "%s -> %s (%d is)",
            from_version, to_version, migrated,
        )
        return migrated

    # ---- Temizlik ----

    def cleanup_old_jobs(
        self,
        max_age_days: int = 0,
    ) -> int:
        """Eski isleri temizler.

        Args:
            max_age_days: Maks yas (gun).
                0 ise varsayilan kullanilir.

        Returns:
            Temizlenen sayi.
        """
        days = max_age_days or (
            self._retention_days
        )
        cutoff = time.time() - (
            days * 86400
        )

        to_delete: list[str] = []
        for job_id, data in (
            self._store.items()
        ):
            status = data.get("status", "")
            updated = data.get(
                "updated_at", 0,
            )

            # Tamamlanmis veya silinmis
            # ve eski
            if status in (
                "completed", "deleted",
                "failed",
            ) and updated < cutoff:
                to_delete.append(job_id)

        for job_id in to_delete:
            del self._store[job_id]

        if to_delete:
            logger.info(
                "%d eski is temizlendi",
                len(to_delete),
            )

        return len(to_delete)

    def cleanup_snapshots(
        self, keep: int = 10,
    ) -> int:
        """Eski goruntuler temizler.

        Args:
            keep: Saklanacak sayi.

        Returns:
            Temizlenen sayi.
        """
        if len(self._snapshots) <= keep:
            return 0

        removed = (
            len(self._snapshots) - keep
        )
        self._snapshots = (
            self._snapshots[-keep:]
        )
        return removed

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        status_counts: dict[str, int] = {}
        for data in self._store.values():
            status = data.get(
                "status", "unknown",
            )
            status_counts[status] = (
                status_counts.get(status, 0) + 1
            )

        return {
            "total_jobs": len(self._store),
            "status_counts": status_counts,
            "snapshot_count": len(
                self._snapshots,
            ),
            "total_saves": (
                self._metadata.get(
                    "total_saves", 0,
                )
            ),
            "total_loads": (
                self._metadata.get(
                    "total_loads", 0,
                )
            ),
            "version": self._metadata.get(
                "version", "1.0",
            ),
            "retention_days": (
                self._retention_days
            ),
        }
