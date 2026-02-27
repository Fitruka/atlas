"""ATLAS Cloud Tam Orkestrator modulu.

Tum Atlas Cloud bilesenlerini koordine eder:
dagitim, olcekleme, guncelleme, yedekleme,
saglik izleme ve onboarding.
"""

import logging
from typing import Any

from app.core.atlascloud.auto_scaler import (
    AutoScaler,
)
from app.core.atlascloud.backup_restore import (
    BackupRestore,
)
from app.core.atlascloud.cloud_orchestrator import (
    AtlasCloudOrchestrator,
)
from app.core.atlascloud.health_monitoring import (
    HealthMonitoring,
)
from app.core.atlascloud.managed_updates import (
    ManagedUpdates,
)
from app.core.atlascloud.onboarding_wizard import (
    OnboardingWizard,
)
from app.models.atlascloud_models import (
    BackupType,
    CloudDeployment,
    CloudUpdate,
    InstanceSize,
    Region,
    UpdateStrategy,
)

logger = logging.getLogger(__name__)


class AtlasCloudFullOrchestrator:
    """Tam Atlas Cloud orkestratoru.

    Tum bulut dagitim bilesenlerini
    tek bir arayuzden koordine eder.

    Attributes:
        cloud: Dagitim orkestratoru.
        scaler: Otomatik olcekleyici.
        updates: Guncelleme yoneticisi.
        backups: Yedekleme yoneticisi.
        health: Saglik izleyici.
        wizard: Onboarding sihirbazi.
    """

    def __init__(self) -> None:
        """Orkestratoru baslatir."""
        self.cloud = AtlasCloudOrchestrator()
        self.scaler = AutoScaler()
        self.updates = ManagedUpdates()
        self.backups = BackupRestore()
        self.health = HealthMonitoring()
        self.wizard = OnboardingWizard()

        self._stats: dict[str, int] = {
            "full_deploys": 0,
            "full_updates": 0,
            "overviews_generated": 0,
        }

        logger.info(
            "AtlasCloudFullOrchestrator baslatildi",
        )

    def full_deploy(
        self,
        name: str,
        tenant_id: str,
        region: str = Region.EU_CENTRAL,
        size: str = InstanceSize.MEDIUM,
        version: str = "1.0.0",
    ) -> dict[str, Any]:
        """Tam dagitim yapar.

        Dagitim + yedekleme + saglik kontrolu.

        Args:
            name: Dagitim adi.
            tenant_id: Kiralayici ID.
            region: Bulut bolgesi.
            size: Ornek boyutu.
            version: Surum.

        Returns:
            Tam dagitim sonucu.
        """
        # 1) Dagitim olustur
        deployment = self.cloud.deploy(
            name=name,
            tenant_id=tenant_id,
            region=region,
            size=size,
            version=version,
        )

        # 2) Otomatik olcekleme yapilandir
        scale_config = self.scaler.configure(
            deployment_id=deployment.id,
            min_replicas=1,
            max_replicas=10,
        )

        # 3) Ilk yedekleme
        backup = self.backups.create_backup(
            deployment_id=deployment.id,
            backup_type=BackupType.FULL,
        )

        # 4) Saglik kontrolu
        health_check = self.health.check_health(
            deployment_id=deployment.id,
        )

        # 5) Uyari yapilandirmasi
        self.health.configure_alerts(
            deployment_id=deployment.id,
        )

        self._stats["full_deploys"] += 1

        logger.info(
            "Tam dagitim tamamlandi: %s (%s)",
            deployment.id,
            name,
        )

        return {
            "success": True,
            "deployment": {
                "id": deployment.id,
                "name": deployment.name,
                "url": deployment.url,
                "status": deployment.status,
                "region": deployment.region,
                "version": deployment.version,
            },
            "scale_config": scale_config,
            "backup": {
                "id": backup.id,
                "type": backup.backup_type,
                "size_mb": backup.size_mb,
            },
            "health": {
                "status": health_check.status,
                "cpu_pct": health_check.cpu_pct,
                "memory_pct": (
                    health_check.memory_pct
                ),
            },
        }

    def full_update(
        self,
        deployment_id: str,
        version: str,
        strategy: str = UpdateStrategy.ROLLING,
    ) -> dict[str, Any]:
        """Tam guncelleme yapar.

        Guncelleme + yedekleme + dogrulama.

        Args:
            deployment_id: Dagitim ID.
            version: Hedef surum.
            strategy: Guncelleme stratejisi.

        Returns:
            Tam guncelleme sonucu.
        """
        deployment = self.cloud.get_deployment(
            deployment_id,
        )
        if not deployment:
            return {
                "success": False,
                "error": "deployment_not_found",
            }

        # 1) Guncelleme oncesi yedekleme
        pre_backup = self.backups.create_backup(
            deployment_id=deployment_id,
            backup_type=BackupType.SNAPSHOT,
        )

        # 2) Guncelleme planla ve uygula
        update_plan = self.updates.plan_update(
            deployment_id=deployment_id,
            target_version=version,
            strategy=strategy,
        )
        update_result = self.updates.execute_update(
            update_id=update_plan.id,
        )

        # 3) Dagitim surumunu guncelle
        self.cloud.update_deployment(
            deployment_id=deployment_id,
            version=version,
            strategy=strategy,
        )

        # 4) Saglik dogrulama
        health_check = self.health.check_health(
            deployment_id=deployment_id,
        )

        self._stats["full_updates"] += 1

        logger.info(
            "Tam guncelleme tamamlandi: %s -> %s",
            deployment_id,
            version,
        )

        return {
            "success": True,
            "deployment_id": deployment_id,
            "pre_backup": {
                "id": pre_backup.id,
                "type": pre_backup.backup_type,
            },
            "update": {
                "id": (
                    update_result.id
                    if update_result
                    else None
                ),
                "from_version": (
                    update_result.from_version
                    if update_result
                    else None
                ),
                "to_version": (
                    update_result.to_version
                    if update_result
                    else version
                ),
                "status": (
                    update_result.status
                    if update_result
                    else "unknown"
                ),
            },
            "health": {
                "status": health_check.status,
                "cpu_pct": health_check.cpu_pct,
                "memory_pct": (
                    health_check.memory_pct
                ),
            },
        }

    def get_cloud_overview(
        self,
    ) -> dict[str, Any]:
        """Bulut genel gorunumunu dondurur.

        Returns:
            Tum dagitimlar ve saglik durumu.
        """
        deployments = self.cloud.list_deployments()
        overview: list[dict[str, Any]] = []

        for dep in deployments:
            latest_health = self.health.get_latest(
                dep.id,
            )
            health_status = (
                latest_health.status
                if latest_health
                else "unknown"
            )

            overview.append({
                "id": dep.id,
                "name": dep.name,
                "tenant_id": dep.tenant_id,
                "region": dep.region,
                "status": dep.status,
                "version": dep.version,
                "replicas": dep.replicas,
                "url": dep.url,
                "health": health_status,
            })

        overall_health = (
            self.health.get_overall_status()
        )

        self._stats["overviews_generated"] += 1

        return {
            "total_deployments": len(deployments),
            "deployments": overview,
            "overall_health": overall_health,
            "cloud_stats": self.cloud.get_stats(),
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Birlesmis istatistik sozlugu.
        """
        return {
            "full_deploys": self._stats[
                "full_deploys"
            ],
            "full_updates": self._stats[
                "full_updates"
            ],
            "overviews_generated": self._stats[
                "overviews_generated"
            ],
            "cloud": self.cloud.get_stats(),
            "scaler": self.scaler.get_stats(),
            "updates": self.updates.get_stats(),
            "backups": self.backups.get_stats(),
            "health": self.health.get_stats(),
            "wizard": self.wizard.get_stats(),
        }
