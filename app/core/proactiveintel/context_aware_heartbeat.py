"""ATLAS Bağlama Duyarlı Heartbeat modülü.

Bağlam ve duruma göre frekans ve içerik ayarlaması,
otomatik heartbeat üretimi, yapılandırma yönetimi.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.proactiveintel_models import (
    HeartbeatConfig,
    HeartbeatFrequency,
)

logger = logging.getLogger(__name__)

_FREQUENCY_INTERVALS = {
    HeartbeatFrequency.REALTIME: 10,
    HeartbeatFrequency.FREQUENT: 60,
    HeartbeatFrequency.NORMAL: 300,
    HeartbeatFrequency.LOW: 900,
    HeartbeatFrequency.IDLE: 3600,
}

_MAX_CONFIGS = 500


class ContextAwareHeartbeat:
    """Bağlama duyarlı heartbeat yöneticisi.

    Bağlam ve duruma göre heartbeat frekansını
    ve içeriğini dinamik olarak ayarlar.

    Attributes:
        _configs: Bağlam bazlı heartbeat yapılandırmaları.
        _history: Gönderim geçmişi.
    """

    def __init__(self) -> None:
        """Heartbeat yöneticisini başlatır."""
        self._configs: dict[str, HeartbeatConfig] = {}
        self._history: list[dict[str, Any]] = []
        self._context_states: dict[str, dict[str, Any]] = {}
        self._stats = {
            "configs_created": 0,
            "heartbeats_sent": 0,
            "frequency_adjustments": 0,
            "context_updates": 0,
        }

        logger.info(
            "ContextAwareHeartbeat baslatildi",
        )

    def configure(
        self,
        context: str,
        frequency: str = HeartbeatFrequency.NORMAL,
        content_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> HeartbeatConfig:
        """Bağlam için heartbeat yapılandırır.

        Args:
            context: Bağlam adı.
            frequency: Heartbeat sıklığı.
            content_type: İçerik tipi.
            metadata: Ek metadata.

        Returns:
            Oluşturulan yapılandırma.
        """
        config = HeartbeatConfig(
            id=str(uuid4())[:8],
            context=context,
            frequency=frequency,
            content_type=content_type or "status",
            metadata=metadata or {},
        )

        if len(self._configs) >= _MAX_CONFIGS:
            oldest = min(
                self._configs,
                key=lambda k: (
                    self._configs[k].last_sent
                    or datetime.min.replace(
                        tzinfo=timezone.utc,
                    )
                ),
            )
            del self._configs[oldest]

        self._configs[context] = config
        self._context_states[context] = {
            "state": "active",
            "updated_at": time.time(),
        }
        self._stats["configs_created"] += 1

        logger.info(
            "Heartbeat yapilandirildi: %s freq=%s",
            context,
            frequency,
        )

        return config

    def should_send(self, context: str) -> bool:
        """Heartbeat gönderilmeli mi kontrol eder.

        Args:
            context: Bağlam adı.

        Returns:
            Gönderilmeli ise True.
        """
        config = self._configs.get(context)
        if not config or not config.active:
            return False

        interval = _FREQUENCY_INTERVALS.get(
            config.frequency,
            _FREQUENCY_INTERVALS[
                HeartbeatFrequency.NORMAL
            ],
        )

        if config.last_sent is None:
            return True

        elapsed = (
            datetime.now(timezone.utc)
            - config.last_sent
        ).total_seconds()

        return elapsed >= interval

    def generate(
        self, context: str
    ) -> dict[str, Any]:
        """Heartbeat içeriği üretir ve gönderir.

        Args:
            context: Bağlam adı.

        Returns:
            Üretilen heartbeat içeriği.
        """
        config = self._configs.get(context)
        if not config:
            return {"error": "config_not_found"}

        now = datetime.now(timezone.utc)
        state = self._context_states.get(
            context, {}
        )

        heartbeat = {
            "heartbeat_id": str(uuid4())[:8],
            "context": context,
            "frequency": config.frequency,
            "content_type": config.content_type,
            "state": state.get("state", "unknown"),
            "timestamp": now.isoformat(),
            "metadata": config.metadata,
        }

        config.last_sent = now
        self._history.append(heartbeat)
        self._stats["heartbeats_sent"] += 1

        logger.debug(
            "Heartbeat uretildi: %s",
            context,
        )

        return heartbeat

    def update_context(
        self,
        context: str,
        new_state: dict[str, Any],
    ) -> HeartbeatConfig | None:
        """Bağlam durumunu günceller.

        Args:
            context: Bağlam adı.
            new_state: Yeni durum bilgisi.

        Returns:
            Güncellenen yapılandırma veya None.
        """
        config = self._configs.get(context)
        if not config:
            return None

        self._context_states[context] = {
            **self._context_states.get(context, {}),
            **new_state,
            "updated_at": time.time(),
        }
        self._stats["context_updates"] += 1

        logger.info(
            "Baglam guncellendi: %s", context
        )

        return config

    def get_config(
        self, context: str
    ) -> HeartbeatConfig | None:
        """Bağlam yapılandırmasını döndürür.

        Args:
            context: Bağlam adı.

        Returns:
            Yapılandırma veya None.
        """
        return self._configs.get(context)

    def list_configs(self) -> list[HeartbeatConfig]:
        """Tüm yapılandırmaları listeler.

        Returns:
            Yapılandırma listesi.
        """
        return list(self._configs.values())

    def adjust_frequency(
        self,
        context: str,
        new_frequency: str,
    ) -> bool:
        """Heartbeat frekansını ayarlar.

        Args:
            context: Bağlam adı.
            new_frequency: Yeni frekans.

        Returns:
            Başarılı ise True.
        """
        config = self._configs.get(context)
        if not config:
            return False

        config.frequency = new_frequency
        self._stats["frequency_adjustments"] += 1

        logger.info(
            "Frekans ayarlandi: %s -> %s",
            context,
            new_frequency,
        )

        return True

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        return {
            **self._stats,
            "active_configs": sum(
                1
                for c in self._configs.values()
                if c.active
            ),
            "total_configs": len(self._configs),
            "history_size": len(self._history),
        }
