"""Heartbeat maliyet optimizasyonu.

Heartbeat frekansı optimizasyonu,
toplu gönderim, koşullu çalıştırma,
%90 maliyet düşürme hedefi.
"""

import logging
import time
from typing import Any

from app.models.costcontrol_models import (
    HeartbeatConfig,
    HeartbeatMode,
)

logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL = 300  # 5 dakika
_MIN_INTERVAL = 60
_MAX_INTERVAL = 3600
_COST_PER_HEARTBEAT_FULL = 0.003  # Varsayılan tam heartbeat maliyeti


class HeartbeatCostOptimizer:
    """Heartbeat maliyet optimizasyonu.

    Heartbeat maliyetini %90 düşürür:
    minimal mod, toplu gönderim, koşullu çalıştırma.

    Attributes:
        _config: Aktif yapılandırma.
        _history: Heartbeat geçmişi.
    """

    def __init__(self) -> None:
        """HeartbeatCostOptimizer başlatır."""
        self._config = HeartbeatConfig(
            mode=HeartbeatMode.CONDITIONAL,
            interval_seconds=_DEFAULT_INTERVAL,
            skip_if_idle=True,
            cost_per_heartbeat=_COST_PER_HEARTBEAT_FULL,
        )
        self._history: list[dict[str, Any]] = []
        self._total_heartbeats: int = 0
        self._total_skipped: int = 0
        self._total_saved: float = 0.0
        self._last_heartbeat: float = 0.0

        logger.info("HeartbeatCostOptimizer baslatildi")

    def configure(
        self,
        mode: str = "conditional",
        interval_seconds: int = 300,
        batch_size: int = 10,
        skip_if_idle: bool = True,
    ) -> HeartbeatConfig:
        """Heartbeat yapılandır.

        Args:
            mode: Heartbeat modu.
            interval_seconds: Aralık (saniye).
            batch_size: Toplu gönderim sayısı.
            skip_if_idle: Boştayken atla.

        Returns:
            Yapılandırma.
        """
        interval = max(_MIN_INTERVAL, min(_MAX_INTERVAL, interval_seconds))

        mode_cost_map = {
            "full": _COST_PER_HEARTBEAT_FULL,
            "minimal": _COST_PER_HEARTBEAT_FULL * 0.1,
            "batched": _COST_PER_HEARTBEAT_FULL * 0.2,
            "conditional": _COST_PER_HEARTBEAT_FULL * 0.15,
            "disabled": 0.0,
        }

        cost = mode_cost_map.get(mode, _COST_PER_HEARTBEAT_FULL * 0.15)

        # Aylık tasarruf tahmini
        full_monthly = _COST_PER_HEARTBEAT_FULL * (86400 * 30 / _DEFAULT_INTERVAL)
        opt_monthly = cost * (86400 * 30 / interval)
        savings = full_monthly - opt_monthly

        self._config = HeartbeatConfig(
            mode=mode,
            interval_seconds=interval,
            batch_size=batch_size,
            skip_if_idle=skip_if_idle,
            cost_per_heartbeat=cost,
            estimated_monthly_savings=round(savings, 2),
        )

        logger.info(
            "Heartbeat yapilandirildi: %s, %ds aralik, ~$%.2f/ay tasarruf",
            mode,
            interval,
            savings,
        )
        return self._config

    def should_send(self, is_idle: bool = False) -> bool:
        """Heartbeat gönderilmeli mi kontrol et.

        Args:
            is_idle: Sistem boşta mı.

        Returns:
            Gönderilmeli ise True.
        """
        mode_val = self._config.mode.value if isinstance(self._config.mode, HeartbeatMode) else str(self._config.mode)

        if mode_val == "disabled":
            self._total_skipped += 1
            return False

        now = time.time()
        elapsed = now - self._last_heartbeat

        if elapsed < self._config.interval_seconds:
            return False

        if mode_val == "conditional" and is_idle and self._config.skip_if_idle:
            self._total_skipped += 1
            self._total_saved += _COST_PER_HEARTBEAT_FULL
            return False

        return True

    def record_heartbeat(self, cost: float = 0.0) -> None:
        """Heartbeat kaydı oluştur.

        Args:
            cost: Gerçek maliyet.
        """
        actual_cost = cost or self._config.cost_per_heartbeat
        saved = _COST_PER_HEARTBEAT_FULL - actual_cost

        self._last_heartbeat = time.time()
        self._total_heartbeats += 1
        self._total_saved += max(0, saved)

        self._history.append({
            "timestamp": self._last_heartbeat,
            "cost": actual_cost,
            "saved": max(0, saved),
        })

    def get_config(self) -> HeartbeatConfig:
        """Aktif yapılandırmayı getir."""
        return self._config

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "mode": self._config.mode.value if isinstance(self._config.mode, HeartbeatMode) else str(self._config.mode),
            "total_heartbeats": self._total_heartbeats,
            "total_skipped": self._total_skipped,
            "total_saved_usd": round(self._total_saved, 4),
            "monthly_savings_estimate": self._config.estimated_monthly_savings,
        }
