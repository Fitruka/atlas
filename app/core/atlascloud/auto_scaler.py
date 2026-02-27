"""ATLAS Cloud Otomatik Olcekleyici modulu.

CPU ve bellek kullanimina dayali
otomatik olcekleme yapilandirmasi,
degerlendirme ve olcekleme gecmisi.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.atlascloud_models import (
    ScaleDirection,
    ScaleEvent,
)

logger = logging.getLogger(__name__)

_DEFAULT_MIN_REPLICAS = 1
_DEFAULT_MAX_REPLICAS = 10
_DEFAULT_TARGET_CPU = 70.0
_DEFAULT_TARGET_MEMORY = 75.0
_DEFAULT_COOLDOWN = 300


class AutoScaler:
    """Otomatik olcekleyici.

    Dagitimlar icin CPU/bellek tabanli
    otomatik olcekleme yapilandirmasi ve
    degerlendirme yapar.

    Attributes:
        _configs: Olcekleme yapilandirmalari.
        _history: Olcekleme olay gecmisi.
        _stats: Istatistik sayaclari.
    """

    def __init__(self) -> None:
        """Olcekleyiciyi baslatir."""
        self._configs: dict[
            str, dict[str, Any]
        ] = {}
        self._history: list[ScaleEvent] = []
        self._last_scale: dict[str, float] = {}
        self._current_replicas: dict[str, int] = {}
        self._stats: dict[str, int] = {
            "scale_ups": 0,
            "scale_downs": 0,
            "evaluations": 0,
            "configs_set": 0,
        }

        logger.info("AutoScaler baslatildi")

    def configure(
        self,
        deployment_id: str,
        min_replicas: int = _DEFAULT_MIN_REPLICAS,
        max_replicas: int = _DEFAULT_MAX_REPLICAS,
        target_cpu: float = _DEFAULT_TARGET_CPU,
        target_memory: float = _DEFAULT_TARGET_MEMORY,
        cooldown_seconds: int = _DEFAULT_COOLDOWN,
    ) -> dict[str, Any]:
        """Olcekleme yapilandirmasi ayarlar.

        Args:
            deployment_id: Dagitim ID.
            min_replicas: Minimum replika.
            max_replicas: Maksimum replika.
            target_cpu: Hedef CPU yuzde.
            target_memory: Hedef bellek yuzde.
            cooldown_seconds: Soguma suresi.

        Returns:
            Yapilandirma bilgisi.
        """
        config = {
            "deployment_id": deployment_id,
            "min_replicas": min_replicas,
            "max_replicas": max_replicas,
            "target_cpu": target_cpu,
            "target_memory": target_memory,
            "cooldown_seconds": cooldown_seconds,
            "configured_at": datetime.now(
                timezone.utc,
            ).isoformat(),
        }

        self._configs[deployment_id] = config

        if deployment_id not in self._current_replicas:
            self._current_replicas[
                deployment_id
            ] = min_replicas

        self._stats["configs_set"] += 1

        logger.info(
            "Olcekleme yapilandirmasi: %s "
            "[%d-%d] CPU:%s%% MEM:%s%%",
            deployment_id,
            min_replicas,
            max_replicas,
            target_cpu,
            target_memory,
        )

        return config

    def evaluate(
        self,
        deployment_id: str,
        current_cpu: float,
        current_memory: float,
    ) -> ScaleEvent | None:
        """Olcekleme ihtiyacini degerlendirir.

        Args:
            deployment_id: Dagitim ID.
            current_cpu: Guncel CPU yuzde.
            current_memory: Guncel bellek yuzde.

        Returns:
            Olcekleme olayi veya None.
        """
        self._stats["evaluations"] += 1

        config = self._configs.get(deployment_id)
        if not config:
            logger.warning(
                "Yapilandirma bulunamadi: %s",
                deployment_id,
            )
            return None

        # Soguma kontrolu
        now = datetime.now(timezone.utc).timestamp()
        last = self._last_scale.get(
            deployment_id, 0.0,
        )
        if now - last < config["cooldown_seconds"]:
            return None

        current = self._current_replicas.get(
            deployment_id, config["min_replicas"],
        )
        target_cpu = config["target_cpu"]
        target_mem = config["target_memory"]

        # Olcekleme yonu belirle
        direction = ScaleDirection.NONE
        new_replicas = current

        if (
            current_cpu > target_cpu
            or current_memory > target_mem
        ):
            # Yukari olcekle
            new_replicas = min(
                current + 1, config["max_replicas"],
            )
            if new_replicas > current:
                direction = ScaleDirection.UP
        elif (
            current_cpu < target_cpu * 0.5
            and current_memory < target_mem * 0.5
        ):
            # Asagi olcekle
            new_replicas = max(
                current - 1, config["min_replicas"],
            )
            if new_replicas < current:
                direction = ScaleDirection.DOWN

        if direction == ScaleDirection.NONE:
            return None

        return self.scale(
            deployment_id,
            direction,
            abs(new_replicas - current),
        )

    def scale(
        self,
        deployment_id: str,
        direction: str,
        count: int = 1,
    ) -> ScaleEvent:
        """Olcekleme yapar.

        Args:
            deployment_id: Dagitim ID.
            direction: Olcekleme yonu.
            count: Replika sayisi degisimi.

        Returns:
            Olcekleme olayi.
        """
        config = self._configs.get(deployment_id)
        min_r = (
            config["min_replicas"]
            if config
            else _DEFAULT_MIN_REPLICAS
        )
        max_r = (
            config["max_replicas"]
            if config
            else _DEFAULT_MAX_REPLICAS
        )

        current = self._current_replicas.get(
            deployment_id, min_r,
        )

        if direction == ScaleDirection.UP:
            new_replicas = min(current + count, max_r)
            self._stats["scale_ups"] += 1
            reason = "cpu_or_memory_threshold_exceeded"
        elif direction == ScaleDirection.DOWN:
            new_replicas = max(current - count, min_r)
            self._stats["scale_downs"] += 1
            reason = "resources_underutilized"
        else:
            new_replicas = current
            reason = "no_change"

        event = ScaleEvent(
            deployment_id=deployment_id,
            direction=direction,
            from_replicas=current,
            to_replicas=new_replicas,
            reason=reason,
        )

        self._current_replicas[
            deployment_id
        ] = new_replicas
        self._last_scale[deployment_id] = (
            datetime.now(timezone.utc).timestamp()
        )
        self._history.append(event)

        logger.info(
            "Olcekleme: %s %s %d -> %d (%s)",
            deployment_id,
            direction,
            current,
            new_replicas,
            reason,
        )

        return event

    def get_config(
        self,
        deployment_id: str,
    ) -> dict[str, Any] | None:
        """Yapilandirmayi getirir.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Yapilandirma veya None.
        """
        return self._configs.get(deployment_id)

    def get_history(
        self,
        deployment_id: str,
    ) -> list[ScaleEvent]:
        """Olcekleme gecmisini getirir.

        Args:
            deployment_id: Dagitim ID.

        Returns:
            Olay listesi.
        """
        return [
            e for e in self._history
            if e.deployment_id == deployment_id
        ]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_configs": len(self._configs),
            "total_events": len(self._history),
            "scale_ups": self._stats["scale_ups"],
            "scale_downs": self._stats[
                "scale_downs"
            ],
            "evaluations": self._stats[
                "evaluations"
            ],
            "configs_set": self._stats[
                "configs_set"
            ],
        }
