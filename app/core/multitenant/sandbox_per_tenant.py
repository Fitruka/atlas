"""ATLAS Sandbox Per Tenant modulu.

Kiraciya ozel izole sandbox ortami
olusturma ve yonetim.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.multitenant_models import (
    SandboxStatus,
    TenantSandbox,
)

logger = logging.getLogger(__name__)

_MAX_SANDBOXES = 5000

_DEFAULT_RESOURCE_LIMITS: dict[str, str] = {
    "cpu": "1",
    "memory": "512Mi",
    "storage": "1Gi",
    "max_processes": "100",
    "network_bandwidth": "10Mbps",
}

_ISOLATION_LEVELS = [
    "namespace",
    "container",
    "vm",
]


class SandboxPerTenant:
    """Kiraciya ozel sandbox yoneticisi.

    Her kiraci icin izole calisma
    ortami saglar.

    Attributes:
        _sandboxes: Sandbox kayitlari.
        _resource_usage: Kaynak kullanimi.
    """

    def __init__(self) -> None:
        """Sandbox yoneticisini baslatir."""
        self._sandboxes: dict[
            str, TenantSandbox
        ] = {}
        self._resource_usage: dict[
            str, dict[str, float]
        ] = {}
        self._stats = {
            "provisioned": 0,
            "started": 0,
            "stopped": 0,
            "reset": 0,
            "errors": 0,
        }

        logger.info(
            "SandboxPerTenant baslatildi",
        )

    def provision(
        self,
        tenant_id: str,
        resource_limits: (
            dict[str, str] | None
        ) = None,
    ) -> TenantSandbox:
        """Yeni sandbox olusturur.

        Args:
            tenant_id: Kiraci ID.
            resource_limits: Kaynak limitleri.

        Returns:
            Olusturulan sandbox.
        """
        # Mevcut sandbox kontrolu
        existing = self._sandboxes.get(
            tenant_id,
        )
        if existing and existing.status not in (
            SandboxStatus.ERROR,
            SandboxStatus.STOPPED,
        ):
            logger.info(
                "Mevcut sandbox kullaniliyor: %s",
                tenant_id,
            )
            return existing

        limits = dict(_DEFAULT_RESOURCE_LIMITS)
        if resource_limits:
            limits.update(resource_limits)

        sandbox = TenantSandbox(
            id=str(uuid4())[:8],
            tenant_id=tenant_id,
            status=SandboxStatus.PROVISIONING,
            resource_limits=limits,
        )

        self._sandboxes[tenant_id] = sandbox

        # Kaynak kullanımını baslat
        self._resource_usage[tenant_id] = {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "storage_mb": 0.0,
            "network_bytes": 0,
        }

        # Hazir durumuna getir
        sandbox.status = SandboxStatus.READY

        self._stats["provisioned"] += 1
        logger.info(
            "Sandbox olusturuldu: %s (%s)",
            tenant_id, sandbox.id,
        )

        return sandbox

    def get_sandbox(
        self,
        tenant_id: str,
    ) -> TenantSandbox | None:
        """Sandbox bilgisini getirir.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Sandbox veya None.
        """
        return self._sandboxes.get(tenant_id)

    def start(
        self,
        tenant_id: str,
    ) -> bool:
        """Sandbox'i baslatir.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Basarili mi.
        """
        sandbox = self._sandboxes.get(
            tenant_id,
        )
        if not sandbox:
            logger.warning(
                "Sandbox bulunamadi: %s",
                tenant_id,
            )
            return False

        if sandbox.status not in (
            SandboxStatus.READY,
            SandboxStatus.STOPPED,
        ):
            logger.warning(
                "Sandbox baslatilabilir "
                "durumda degil: %s (%s)",
                tenant_id,
                sandbox.status.value,
            )
            return False

        sandbox.status = SandboxStatus.RUNNING
        sandbox.last_used = datetime.now(
            timezone.utc,
        )

        self._stats["started"] += 1
        logger.info(
            "Sandbox baslatildi: %s",
            tenant_id,
        )
        return True

    def stop(
        self,
        tenant_id: str,
    ) -> bool:
        """Sandbox'i durdurur.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Basarili mi.
        """
        sandbox = self._sandboxes.get(
            tenant_id,
        )
        if not sandbox:
            return False

        if sandbox.status != (
            SandboxStatus.RUNNING
        ):
            return False

        sandbox.status = SandboxStatus.STOPPED

        # Kaynak kullanimini sifirla
        if tenant_id in self._resource_usage:
            self._resource_usage[tenant_id] = {
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "storage_mb": 0.0,
                "network_bytes": 0,
            }

        self._stats["stopped"] += 1
        logger.info(
            "Sandbox durduruldu: %s",
            tenant_id,
        )
        return True

    def reset(
        self,
        tenant_id: str,
    ) -> bool:
        """Sandbox'i sifirlar.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Basarili mi.
        """
        sandbox = self._sandboxes.get(
            tenant_id,
        )
        if not sandbox:
            return False

        # Durdur
        if sandbox.status == (
            SandboxStatus.RUNNING
        ):
            self.stop(tenant_id)

        # Kaynaklari sifirla
        sandbox.status = SandboxStatus.READY
        self._resource_usage[tenant_id] = {
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "storage_mb": 0.0,
            "network_bytes": 0,
        }

        self._stats["reset"] += 1
        logger.info(
            "Sandbox sifirlandi: %s",
            tenant_id,
        )
        return True

    def get_resource_usage(
        self,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Kaynak kullanimini getirir.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Kaynak kullanim metrikleri.
        """
        sandbox = self._sandboxes.get(
            tenant_id,
        )
        if not sandbox:
            return {}

        usage = self._resource_usage.get(
            tenant_id,
            {
                "cpu_percent": 0.0,
                "memory_mb": 0.0,
                "storage_mb": 0.0,
                "network_bytes": 0,
            },
        )

        return {
            "tenant_id": tenant_id,
            "sandbox_id": sandbox.id,
            "status": sandbox.status.value,
            "limits": dict(
                sandbox.resource_limits,
            ),
            "usage": usage,
            "isolation_level": (
                sandbox.isolation_level
            ),
        }

    def list_sandboxes(
        self,
        status: SandboxStatus | None = None,
    ) -> list[TenantSandbox]:
        """Sandbox'lari listeler.

        Args:
            status: Durum filtresi.

        Returns:
            Sandbox listesi.
        """
        sandboxes = list(
            self._sandboxes.values(),
        )
        if status:
            sandboxes = [
                s for s in sandboxes
                if s.status == status
            ]
        return sandboxes

    def delete_sandbox(
        self,
        tenant_id: str,
    ) -> bool:
        """Sandbox'i siler.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Basarili mi.
        """
        if tenant_id not in self._sandboxes:
            return False

        # Calisiyorsa durdur
        sandbox = self._sandboxes[tenant_id]
        if sandbox.status == (
            SandboxStatus.RUNNING
        ):
            self.stop(tenant_id)

        del self._sandboxes[tenant_id]
        self._resource_usage.pop(
            tenant_id, None,
        )

        logger.info(
            "Sandbox silindi: %s", tenant_id,
        )
        return True

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        status_dist: dict[str, int] = {}
        for sb in self._sandboxes.values():
            s = sb.status.value
            status_dist[s] = (
                status_dist.get(s, 0) + 1
            )

        return {
            "total_sandboxes": len(
                self._sandboxes,
            ),
            "status_distribution": status_dist,
            **self._stats,
            "timestamp": time.time(),
        }
