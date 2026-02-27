"""Akıllı model yönlendirici.

Görev karmaşıklığına göre model seçimi,
ucuzdan pahalıya kademeli yönlendirme,
maliyet-kalite dengesi.
"""

import logging
from typing import Any

from app.models.costcontrol_models import (
    ModelRouteConfig,
    RouteDecision,
    ModelTier,
    TaskComplexity,
)

logger = logging.getLogger(__name__)

_MAX_MODELS = 50

_DEFAULT_ROUTES: list[dict[str, Any]] = [
    {"model_name": "claude-haiku-3.5", "provider": "anthropic", "tier": "economy",
     "cost_per_1k_input": 0.0008, "cost_per_1k_output": 0.004,
     "quality_score": 0.7, "supported_tasks": ["simple", "classification", "extraction"]},
    {"model_name": "gpt-4o-mini", "provider": "openai", "tier": "economy",
     "cost_per_1k_input": 0.00015, "cost_per_1k_output": 0.0006,
     "quality_score": 0.65, "supported_tasks": ["simple", "classification"]},
    {"model_name": "claude-sonnet-4", "provider": "anthropic", "tier": "standard",
     "cost_per_1k_input": 0.003, "cost_per_1k_output": 0.015,
     "quality_score": 0.85, "supported_tasks": ["moderate", "analysis", "coding", "writing"]},
    {"model_name": "gpt-4o", "provider": "openai", "tier": "standard",
     "cost_per_1k_input": 0.005, "cost_per_1k_output": 0.015,
     "quality_score": 0.85, "supported_tasks": ["moderate", "analysis", "coding"]},
    {"model_name": "claude-opus-4", "provider": "anthropic", "tier": "premium",
     "cost_per_1k_input": 0.015, "cost_per_1k_output": 0.075,
     "quality_score": 0.95, "supported_tasks": ["complex", "expert", "reasoning", "creative"]},
]

_COMPLEXITY_TO_TIER: dict[str, str] = {
    "trivial": "economy",
    "simple": "economy",
    "moderate": "standard",
    "complex": "premium",
    "expert": "ultra",
}


class SmartModelRouter:
    """Akıllı model yönlendirici.

    Görev karmaşıklığına göre en uygun
    ve en uygun maliyetli modeli seçer.

    Attributes:
        _models: Kayıtlı model yapılandırmaları.
        _decisions: Yönlendirme kararları.
    """

    def __init__(self) -> None:
        """SmartModelRouter başlatır."""
        self._models: dict[str, ModelRouteConfig] = {}
        self._decisions: list[RouteDecision] = []
        self._total_routes: int = 0

        self._load_defaults()
        logger.info("SmartModelRouter baslatildi (%d model)", len(self._models))

    def _load_defaults(self) -> None:
        """Varsayılan model yapılandırmalarını yükle."""
        for md in _DEFAULT_ROUTES:
            config = ModelRouteConfig(
                model_name=md["model_name"],
                provider=md["provider"],
                tier=md["tier"],
                cost_per_1k_input=md["cost_per_1k_input"],
                cost_per_1k_output=md["cost_per_1k_output"],
                quality_score=md["quality_score"],
                supported_tasks=md["supported_tasks"],
            )
            self._models[config.model_name] = config

    def register_model(self, config: ModelRouteConfig) -> bool:
        """Model kaydet.

        Args:
            config: Model yapılandırması.

        Returns:
            Başarılı ise True.
        """
        if len(self._models) >= _MAX_MODELS:
            return False
        self._models[config.model_name] = config
        logger.info("Model kaydedildi: %s", config.model_name)
        return True

    def route(
        self,
        task_type: str = "",
        complexity: str = "moderate",
        max_cost_usd: float = 0.0,
        preferred_provider: str = "",
    ) -> RouteDecision:
        """Görev için en uygun modeli seç.

        Args:
            task_type: Görev tipi.
            complexity: Karmaşıklık seviyesi.
            max_cost_usd: Maksimum maliyet.
            preferred_provider: Tercih edilen sağlayıcı.

        Returns:
            Yönlendirme kararı.
        """
        target_tier = _COMPLEXITY_TO_TIER.get(complexity, "standard")

        candidates: list[tuple[ModelRouteConfig, float]] = []

        for config in self._models.values():
            if not config.enabled:
                continue

            tier_val = config.tier.value if isinstance(config.tier, ModelTier) else str(config.tier)

            tier_match = self._tier_compatible(tier_val, target_tier)
            if not tier_match:
                continue

            if preferred_provider and config.provider != preferred_provider:
                continue

            avg_cost = (config.cost_per_1k_input + config.cost_per_1k_output) / 2
            score = config.quality_score / (avg_cost + 0.0001)
            candidates.append((config, score))

        candidates.sort(key=lambda x: x[1], reverse=True)

        if not candidates:
            # Fallback: en ucuz model
            all_models = sorted(
                self._models.values(),
                key=lambda m: m.cost_per_1k_input + m.cost_per_1k_output,
            )
            if all_models:
                candidates = [(all_models[0], 0.0)]

        if not candidates:
            return RouteDecision(
                task_type=task_type,
                complexity=complexity,
                reason="Model bulunamadi",
            )

        selected = candidates[0][0]
        est_cost = (selected.cost_per_1k_input + selected.cost_per_1k_output) * 2

        alternatives = []
        for cfg, sc in candidates[1:3]:
            alternatives.append({
                "model": cfg.model_name,
                "provider": cfg.provider,
                "score": round(sc, 4),
            })

        decision = RouteDecision(
            task_type=task_type,
            complexity=complexity,
            selected_model=selected.model_name,
            selected_provider=selected.provider,
            selected_tier=selected.tier,
            estimated_cost=round(est_cost, 6),
            reason=f"En iyi kalite/maliyet orani ({target_tier} tier)",
            alternatives=alternatives,
        )

        self._decisions.append(decision)
        self._total_routes += 1

        logger.info(
            "Model yonlendirildi: %s -> %s (karmasiklik: %s)",
            task_type or "genel",
            selected.model_name,
            complexity,
        )
        return decision

    def _tier_compatible(self, model_tier: str, target_tier: str) -> bool:
        """Tier uyumluluğunu kontrol et."""
        tier_order = ["economy", "standard", "premium", "ultra"]
        try:
            model_idx = tier_order.index(model_tier)
            target_idx = tier_order.index(target_tier)
            return model_idx >= target_idx - 1 and model_idx <= target_idx + 1
        except ValueError:
            return True

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_models": len(self._models),
            "total_routes": self._total_routes,
        }
