"""
Tek tikla dagitim modulu.

Is akisini tek tikla aktive etme,
dagitim, geri alma, durum yonetimi.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.visualworkflow_models import (
    DeploymentResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

_MAX_DEPLOYMENTS = 200


class OneClickDeploy:
    """Tek tikla dagitim yoneticisi.

    Attributes:
        _deployments: Dagitim kayitlari.
        _history: Dagitim gecmisi.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Dagitim yoneticisini baslatir."""
        self._deployments: dict[
            str, DeploymentResult
        ] = {}
        self._history: list[dict] = []
        self._stats: dict[str, int] = {
            "deployments": 0,
            "undeployments": 0,
            "activations": 0,
            "deactivations": 0,
            "rollbacks": 0,
        }
        logger.info("OneClickDeploy baslatildi")

    @property
    def active_count(self) -> int:
        """Aktif dagitim sayisi."""
        return sum(
            1
            for d in self._deployments.values()
            if d.active
        )

    def deploy(
        self,
        workflow_id: str,
        auto_activate: bool = True,
    ) -> DeploymentResult:
        """Is akisini dagitir.

        Args:
            workflow_id: Is akisi ID.
            auto_activate: Otomatik aktif et.

        Returns:
            Dagitim sonucu.
        """
        try:
            if len(self._deployments) >= _MAX_DEPLOYMENTS:
                logger.warning(
                    "Maksimum dagitim siniri"
                )
                return DeploymentResult(
                    workflow_id=workflow_id,
                    active=False,
                )

            # Ayni is akisinin onceki dagitimini deaktif et
            for dep in self._deployments.values():
                if (
                    dep.workflow_id == workflow_id
                    and dep.active
                ):
                    dep.active = False

            # Surum hesapla
            existing_versions = [
                d.version
                for d in self._deployments.values()
                if d.workflow_id == workflow_id
            ]
            version = (
                max(existing_versions) + 1
                if existing_versions
                else 1
            )

            deployment = DeploymentResult(
                workflow_id=workflow_id,
                version=version,
                active=auto_activate,
                endpoint_url=(
                    f"/api/workflows/{workflow_id}/v{version}"
                ),
            )
            self._deployments[deployment.id] = deployment
            self._stats["deployments"] += 1

            self._history.append(
                {
                    "action": "deploy",
                    "deployment_id": deployment.id,
                    "workflow_id": workflow_id,
                    "version": version,
                    "timestamp": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )

            logger.info(
                f"Dagitim tamamlandi: {deployment.id} (v{version})"
            )
            return deployment
        except Exception as e:
            logger.error(f"Dagitim hatasi: {e}")
            return DeploymentResult(
                workflow_id=workflow_id,
                active=False,
            )

    def undeploy(
        self,
        deployment_id: str,
    ) -> bool:
        """Dagitimi kaldirir.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Basarili ise True.
        """
        try:
            dep = self._deployments.get(deployment_id)
            if not dep:
                return False

            dep.active = False
            self._stats["undeployments"] += 1
            self._history.append(
                {
                    "action": "undeploy",
                    "deployment_id": deployment_id,
                    "timestamp": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )
            logger.info(
                f"Dagitim kaldirildi: {deployment_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Dagitim kaldirma hatasi: {e}"
            )
            return False

    def activate(
        self,
        deployment_id: str,
    ) -> bool:
        """Dagitimi aktif eder.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Basarili ise True.
        """
        try:
            dep = self._deployments.get(deployment_id)
            if not dep:
                return False

            # Ayni is akisinin diger dagitimlarini deaktif et
            for other in self._deployments.values():
                if (
                    other.workflow_id == dep.workflow_id
                    and other.id != deployment_id
                    and other.active
                ):
                    other.active = False

            dep.active = True
            self._stats["activations"] += 1
            logger.info(
                f"Dagitim aktif edildi: {deployment_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Aktivasyon hatasi: {e}"
            )
            return False

    def deactivate(
        self,
        deployment_id: str,
    ) -> bool:
        """Dagitimi deaktif eder.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Basarili ise True.
        """
        try:
            dep = self._deployments.get(deployment_id)
            if not dep:
                return False

            dep.active = False
            self._stats["deactivations"] += 1
            logger.info(
                f"Dagitim deaktif edildi: {deployment_id}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Deaktivasyon hatasi: {e}"
            )
            return False

    def get_deployment(
        self,
        deployment_id: str,
    ) -> DeploymentResult | None:
        """Dagitim bilgisini getirir.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Dagitim sonucu veya None.
        """
        return self._deployments.get(deployment_id)

    def list_deployments(
        self,
        active_only: bool = False,
    ) -> list[DeploymentResult]:
        """Dagitimlari listeler.

        Args:
            active_only: Yalnizca aktifler.

        Returns:
            Dagitim listesi.
        """
        result = list(self._deployments.values())
        if active_only:
            result = [d for d in result if d.active]
        return result

    def rollback(
        self,
        deployment_id: str,
    ) -> bool:
        """Onceki surume geri doner.

        Args:
            deployment_id: Mevcut dagitim ID.

        Returns:
            Basarili ise True.
        """
        try:
            dep = self._deployments.get(deployment_id)
            if not dep:
                return False

            # Ayni is akisinin onceki surumunu bul
            previous = [
                d
                for d in self._deployments.values()
                if d.workflow_id == dep.workflow_id
                and d.version < dep.version
            ]
            if not previous:
                logger.warning(
                    "Geri donulecek surum bulunamadi"
                )
                return False

            # En son onceki surumu aktif et
            previous.sort(
                key=lambda d: d.version, reverse=True
            )
            target = previous[0]

            dep.active = False
            target.active = True
            self._stats["rollbacks"] += 1

            self._history.append(
                {
                    "action": "rollback",
                    "from_deployment": deployment_id,
                    "to_deployment": target.id,
                    "from_version": dep.version,
                    "to_version": target.version,
                    "timestamp": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )
            logger.info(
                f"Geri alma: v{dep.version} -> v{target.version}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Geri alma hatasi: {e}"
            )
            return False

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            **self._stats,
            "total_deployments": len(self._deployments),
            "active_deployments": self.active_count,
            "history_entries": len(self._history),
        }
