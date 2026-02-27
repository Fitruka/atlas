"""ATLAS Cloud Saglik Izleme modulu.

Dagitim saglik kontrolleri, uyari yapilandi-
rmasi, gecmis kayitlari ve genel durum
gorunumu.
"""

import logging
import random
from datetime import datetime, timezone
from typing import Any

from app.models.atlascloud_models import (
    HealthCheck,
    HealthStatus,
)

logger = logging.getLogger(__name__)

_DEFAULT_CPU_THRESHOLD = 85.0
_DEFAULT_MEMORY_THRESHOLD = 90.0
_DEFAULT_RESPONSE_THRESHOLD = 2000.0
_MAX_HISTORY_PER_DEPLOYMENT = 100


class HealthMonitoring:
    """Saglik izleme yoneticisi.

    Dagitim saglik kontrollerini yapar,
    uyari esiklerini yonetir ve gecmis
    izleme verileri saglar.

    Attributes:
        _checks: Saglik kontrolu kayitlari.
        _alerts: Uyari listesi.
        _alert_configs: Uyari yapilandirmalari.
        _stats: Istatistik sayaclari.
    """

    def __init__(self) -> None:
        """Izleme yoneticisini baslatir."""
        self._checks: dict[
            str, list[HealthCheck]
        ] = {}
        self._alerts: dict[
            str, list[dict[str, Any]]
        ] = {}
        self._alert_configs: dict[
            str, dict[str, float]
        ] = {}
        self._stats: dict[str, int] = {
            "checks_performed": 0,
            "alerts_triggered": 0,
            "healthy_checks": 0,
            "unhealthy_checks": 0,
        }

        logger.info("HealthMonitoring baslatildi")

    def check_health(
        self,
        deployment_id: str,
    ) -> HealthCheck:
        """Saglik kontrolu yapar.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Saglik kontrolu sonucu.
        """
        # Metrik simulasyonu
        cpu = round(random.uniform(10, 80), 1)
        memory = round(random.uniform(20, 85), 1)
        disk = round(random.uniform(15, 70), 1)
        response = round(
            random.uniform(50, 500), 1,
        )

        # Durum belirleme
        config = self._alert_configs.get(
            deployment_id,
            {
                "cpu_threshold": _DEFAULT_CPU_THRESHOLD,
                "memory_threshold": (
                    _DEFAULT_MEMORY_THRESHOLD
                ),
                "response_threshold": (
                    _DEFAULT_RESPONSE_THRESHOLD
                ),
            },
        )

        status = self._determine_status(
            cpu,
            memory,
            response,
            config,
        )

        check = HealthCheck(
            deployment_id=deployment_id,
            status=status,
            cpu_pct=cpu,
            memory_pct=memory,
            disk_pct=disk,
            response_time_ms=response,
        )

        # Gecmise ekle
        if deployment_id not in self._checks:
            self._checks[deployment_id] = []

        history = self._checks[deployment_id]
        history.append(check)

        # Gecmis sinirla
        if len(history) > _MAX_HISTORY_PER_DEPLOYMENT:
            self._checks[deployment_id] = history[
                -_MAX_HISTORY_PER_DEPLOYMENT:
            ]

        # Istatistik guncelle
        self._stats["checks_performed"] += 1
        if status == HealthStatus.HEALTHY:
            self._stats["healthy_checks"] += 1
        else:
            self._stats["unhealthy_checks"] += 1

        # Uyari kontrolu
        self._check_alerts(deployment_id, check)

        logger.info(
            "Saglik kontrolu: %s -> %s "
            "(CPU:%.1f%% MEM:%.1f%% RT:%.1fms)",
            deployment_id,
            status,
            cpu,
            memory,
            response,
        )

        return check

    def get_latest(
        self,
        deployment_id: str,
    ) -> HealthCheck | None:
        """Son saglik kontrolunu getirir.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Son kontrol veya None.
        """
        history = self._checks.get(
            deployment_id, [],
        )
        if not history:
            return None
        return history[-1]

    def get_history(
        self,
        deployment_id: str,
        limit: int = 50,
    ) -> list[HealthCheck]:
        """Saglik gecmisini getirir.

        Args:
            deployment_id: Dagitim ID.
            limit: Maks kayit.

        Returns:
            Kontrol listesi.
        """
        history = self._checks.get(
            deployment_id, [],
        )
        return list(history[-limit:])

    def get_alerts(
        self,
        deployment_id: str,
    ) -> list[dict[str, Any]]:
        """Uyarilari getirir.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Uyari listesi.
        """
        return self._alerts.get(
            deployment_id, [],
        )

    def configure_alerts(
        self,
        deployment_id: str,
        cpu_threshold: float = _DEFAULT_CPU_THRESHOLD,
        memory_threshold: float = (
            _DEFAULT_MEMORY_THRESHOLD
        ),
        response_threshold: float = (
            _DEFAULT_RESPONSE_THRESHOLD
        ),
    ) -> dict[str, Any]:
        """Uyari esiklerini yapilandirir.

        Args:
            deployment_id: Dagitim ID.
            cpu_threshold: CPU esigi.
            memory_threshold: Bellek esigi.
            response_threshold: Yanit suresi esigi.

        Returns:
            Yapilandirma bilgisi.
        """
        config = {
            "cpu_threshold": cpu_threshold,
            "memory_threshold": memory_threshold,
            "response_threshold": response_threshold,
            "configured_at": datetime.now(
                timezone.utc,
            ).isoformat(),
        }

        self._alert_configs[deployment_id] = config

        logger.info(
            "Uyari yapilandirmasi: %s "
            "CPU:%.1f%% MEM:%.1f%% RT:%.1fms",
            deployment_id,
            cpu_threshold,
            memory_threshold,
            response_threshold,
        )

        return config

    def get_overall_status(
        self,
    ) -> dict[str, Any]:
        """Genel saglik durumunu dondurur.

        Returns:
            Dagitim saglik ozeti.
        """
        summary: dict[str, int] = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0,
        }

        for dep_id, history in self._checks.items():
            if history:
                latest = history[-1]
                status = latest.status
                if status in summary:
                    summary[status] += 1
                else:
                    summary[HealthStatus.UNKNOWN] += 1

        total = sum(summary.values())

        return {
            "total_deployments_monitored": total,
            "healthy": summary[HealthStatus.HEALTHY],
            "degraded": summary[
                HealthStatus.DEGRADED
            ],
            "unhealthy": summary[
                HealthStatus.UNHEALTHY
            ],
            "unknown": summary[HealthStatus.UNKNOWN],
            "health_rate": (
                round(
                    summary[HealthStatus.HEALTHY]
                    / total * 100,
                    1,
                )
                if total > 0
                else 0.0
            ),
        }

    def _determine_status(
        self,
        cpu: float,
        memory: float,
        response: float,
        config: dict[str, float],
    ) -> str:
        """Saglik durumunu belirler.

        Args:
            cpu: CPU yuzde.
            memory: Bellek yuzde.
            response: Yanit suresi.
            config: Esik degerleri.

        Returns:
            Saglik durumu.
        """
        cpu_t = config.get(
            "cpu_threshold",
            _DEFAULT_CPU_THRESHOLD,
        )
        mem_t = config.get(
            "memory_threshold",
            _DEFAULT_MEMORY_THRESHOLD,
        )
        resp_t = config.get(
            "response_threshold",
            _DEFAULT_RESPONSE_THRESHOLD,
        )

        if (
            cpu > cpu_t
            or memory > mem_t
            or response > resp_t
        ):
            return HealthStatus.UNHEALTHY

        if (
            cpu > cpu_t * 0.8
            or memory > mem_t * 0.8
            or response > resp_t * 0.7
        ):
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def _check_alerts(
        self,
        deployment_id: str,
        check: HealthCheck,
    ) -> None:
        """Uyari kontrolu yapar.

        Args:
            deployment_id: Dagitim ID.
            check: Saglik kontrolu.
        """
        if check.status in (
            HealthStatus.UNHEALTHY,
            HealthStatus.DEGRADED,
        ):
            alert = {
                "deployment_id": deployment_id,
                "status": check.status,
                "cpu_pct": check.cpu_pct,
                "memory_pct": check.memory_pct,
                "response_time_ms": (
                    check.response_time_ms
                ),
                "triggered_at": datetime.now(
                    timezone.utc,
                ).isoformat(),
            }

            if deployment_id not in self._alerts:
                self._alerts[deployment_id] = []

            self._alerts[deployment_id].append(alert)
            self._stats["alerts_triggered"] += 1

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "deployments_monitored": len(
                self._checks,
            ),
            "checks_performed": self._stats[
                "checks_performed"
            ],
            "alerts_triggered": self._stats[
                "alerts_triggered"
            ],
            "healthy_checks": self._stats[
                "healthy_checks"
            ],
            "unhealthy_checks": self._stats[
                "unhealthy_checks"
            ],
            "alert_configs": len(
                self._alert_configs,
            ),
        }
