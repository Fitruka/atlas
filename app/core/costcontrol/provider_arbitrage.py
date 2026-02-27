"""Sağlayıcı arbitrajı.

En ucuz sağlayıcıyı anlık seçme,
sağlayıcı sağlık takibi, maliyet karşılaştırma.
"""

import logging
import time
from typing import Any

from app.models.costcontrol_models import (
    ProviderInfo,
    ArbitrageDecision,
    ProviderStatus,
)

logger = logging.getLogger(__name__)

_MAX_PROVIDERS = 30


class ProviderArbitrage:
    """Sağlayıcı arbitrajı.

    Aynı modeli sunan sağlayıcılar
    arasında en ucuzunu seçer.

    Attributes:
        _providers: Kayıtlı sağlayıcılar.
        _decisions: Arbitraj kararları.
    """

    def __init__(self) -> None:
        """ProviderArbitrage başlatır."""
        self._providers: dict[str, ProviderInfo] = {}
        self._decisions: list[ArbitrageDecision] = []
        self._total_decisions: int = 0
        self._total_savings: float = 0.0

        logger.info("ProviderArbitrage baslatildi")

    def register_provider(
        self,
        name: str,
        models: list[str],
        cost_multiplier: float = 1.0,
        latency_ms: float = 100.0,
        reliability_score: float = 1.0,
    ) -> ProviderInfo:
        """Sağlayıcı kaydet.

        Args:
            name: Sağlayıcı adı.
            models: Desteklenen modeller.
            cost_multiplier: Maliyet çarpanı.
            latency_ms: Gecikme (ms).
            reliability_score: Güvenilirlik puanı.

        Returns:
            Sağlayıcı bilgisi.
        """
        if len(self._providers) >= _MAX_PROVIDERS:
            logger.warning("Max saglayici limiti: %d", _MAX_PROVIDERS)
            return ProviderInfo()

        provider = ProviderInfo(
            name=name,
            models=models,
            cost_multiplier=cost_multiplier,
            latency_ms=latency_ms,
            reliability_score=reliability_score,
            last_checked=time.time(),
        )

        self._providers[provider.provider_id] = provider
        logger.info("Saglayici kaydedildi: %s (%d model)", name, len(models))
        return provider

    def find_cheapest(
        self,
        model_name: str,
        base_cost: float = 0.0,
        min_reliability: float = 0.5,
    ) -> ArbitrageDecision:
        """En ucuz sağlayıcıyı bul.

        Args:
            model_name: Model adı.
            base_cost: Temel maliyet.
            min_reliability: Min güvenilirlik.

        Returns:
            Arbitraj kararı.
        """
        candidates: list[tuple[ProviderInfo, float]] = []

        for provider in self._providers.values():
            status = provider.status
            status_val = status.value if isinstance(status, ProviderStatus) else str(status)
            if status_val not in ("available", "degraded"):
                continue
            if provider.reliability_score < min_reliability:
                continue
            if model_name not in provider.models:
                continue

            cost = base_cost * provider.cost_multiplier
            candidates.append((provider, cost))

        candidates.sort(key=lambda x: x[1])

        if not candidates:
            return ArbitrageDecision(
                model_name=model_name,
                reason="Uygun saglayici bulunamadi",
            )

        selected, cheapest_cost = candidates[0]
        most_expensive = candidates[-1][1] if candidates else cheapest_cost
        savings = most_expensive - cheapest_cost

        decision = ArbitrageDecision(
            model_name=model_name,
            selected_provider=selected.name,
            cost_usd=cheapest_cost,
            cheapest_cost=cheapest_cost,
            savings_usd=round(savings, 6),
            latency_ms=selected.latency_ms,
            providers_compared=len(candidates),
            reason=f"En ucuz: {selected.name} (x{selected.cost_multiplier})",
        )

        self._decisions.append(decision)
        self._total_decisions += 1
        self._total_savings += savings

        return decision

    def update_status(
        self,
        provider_id: str,
        status: str,
        latency_ms: float = 0.0,
    ) -> bool:
        """Sağlayıcı durumu güncelle.

        Args:
            provider_id: Sağlayıcı ID.
            status: Yeni durum.
            latency_ms: Güncel gecikme.

        Returns:
            Başarılı ise True.
        """
        provider = self._providers.get(provider_id)
        if not provider:
            return False

        provider.status = status
        if latency_ms > 0:
            provider.latency_ms = latency_ms
        provider.last_checked = time.time()
        return True

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_providers": len(self._providers),
            "total_decisions": self._total_decisions,
            "total_savings_usd": round(self._total_savings, 4),
        }
