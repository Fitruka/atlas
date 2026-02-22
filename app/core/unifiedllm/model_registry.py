"""LLM model kayit defteri.

Model katalogu, yetenekler, fiyatlandirma,
limitler ve oneriler saglar.
"""

import logging
from typing import Any

from app.models.unifiedllm_models import (
    LLMProvider,
    ModelCapability,
    ModelInfo,
)

logger = logging.getLogger(__name__)

# --- Varsayilan model katalogu ---

_DEFAULT_MODELS: list[dict[str, Any]] = [
    # Anthropic
    {
        "model_id": "claude-opus-4-20250514",
        "provider": LLMProvider.ANTHROPIC,
        "display_name": "Claude Opus 4",
        "context_window": 200000,
        "max_output_tokens": 32000,
        "input_cost_per_1k": 0.015,
        "output_cost_per_1k": 0.075,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
    },
    {
        "model_id": "claude-sonnet-4-20250514",
        "provider": LLMProvider.ANTHROPIC,
        "display_name": "Claude Sonnet 4",
        "context_window": 200000,
        "max_output_tokens": 16000,
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
    },
    {
        "model_id": "claude-haiku-4-20250506",
        "provider": LLMProvider.ANTHROPIC,
        "display_name": "Claude Haiku 4",
        "context_window": 200000,
        "max_output_tokens": 8192,
        "input_cost_per_1k": 0.0008,
        "output_cost_per_1k": 0.004,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
    },
    # OpenAI
    {
        "model_id": "gpt-4o",
        "provider": LLMProvider.OPENAI,
        "display_name": "GPT-4o",
        "context_window": 128000,
        "max_output_tokens": 16384,
        "input_cost_per_1k": 0.005,
        "output_cost_per_1k": 0.015,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT, ModelCapability.JSON_MODE,
        ],
    },
    {
        "model_id": "gpt-4o-mini",
        "provider": LLMProvider.OPENAI,
        "display_name": "GPT-4o Mini",
        "context_window": 128000,
        "max_output_tokens": 16384,
        "input_cost_per_1k": 0.00015,
        "output_cost_per_1k": 0.0006,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT, ModelCapability.JSON_MODE,
        ],
    },
    # Gemini
    {
        "model_id": "gemini-2.0-flash",
        "provider": LLMProvider.GEMINI,
        "display_name": "Gemini 2.0 Flash",
        "context_window": 1000000,
        "max_output_tokens": 8192,
        "input_cost_per_1k": 0.0001,
        "output_cost_per_1k": 0.0004,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
    },
    {
        "model_id": "gemini-2.0-pro",
        "provider": LLMProvider.GEMINI,
        "display_name": "Gemini 2.0 Pro",
        "context_window": 1000000,
        "max_output_tokens": 8192,
        "input_cost_per_1k": 0.00125,
        "output_cost_per_1k": 0.005,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
    },
    # Ollama (yerel)
    {
        "model_id": "llama3.1",
        "provider": LLMProvider.OLLAMA,
        "display_name": "Llama 3.1 8B",
        "context_window": 131072,
        "max_output_tokens": 4096,
        "input_cost_per_1k": 0.0,
        "output_cost_per_1k": 0.0,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.EMBEDDING,
        ],
    },
    # Anthropic - Sonnet 4.6
    {
        "model_id": "claude-sonnet-4-6-20260214",
        "provider": LLMProvider.ANTHROPIC,
        "display_name": "Claude Sonnet 4.6",
        "context_window": 200000,
        "max_output_tokens": 16000,
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT, ModelCapability.THINKING,
        ],
    },
    # OpenAI - GPT-5.3 Codex
    {
        "model_id": "gpt-5.3-codex",
        "provider": LLMProvider.OPENAI,
        "display_name": "GPT-5.3 Codex",
        "context_window": 256000,
        "max_output_tokens": 32768,
        "input_cost_per_1k": 0.01,
        "output_cost_per_1k": 0.03,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.CODE,
            ModelCapability.LONG_CONTEXT, ModelCapability.JSON_MODE,
            ModelCapability.THINKING,
        ],
    },
    # Gemini 3.1 Pro
    {
        "model_id": "gemini-3.1-pro-preview",
        "provider": LLMProvider.GEMINI,
        "display_name": "Gemini 3.1 Pro Preview",
        "context_window": 2000000,
        "max_output_tokens": 16384,
        "input_cost_per_1k": 0.00125,
        "output_cost_per_1k": 0.005,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT, ModelCapability.CONTEXT_1M,
            ModelCapability.THINKING,
        ],
    },
    # xAI Grok
    {
        "model_id": "grok-3",
        "provider": LLMProvider.XAI,
        "display_name": "Grok 3",
        "context_window": 131072,
        "max_output_tokens": 16384,
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
        ],
    },
    # Volcano / Doubao
    {
        "model_id": "doubao-pro-256k",
        "provider": LLMProvider.VOLCANO,
        "display_name": "Doubao Pro 256K",
        "context_window": 256000,
        "max_output_tokens": 8192,
        "input_cost_per_1k": 0.0008,
        "output_cost_per_1k": 0.002,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.LONG_CONTEXT,
        ],
    },
    # Cloudflare Workers AI
    {
        "model_id": "cloudflare/llama-3.3-70b",
        "provider": LLMProvider.CLOUDFLARE,
        "display_name": "Llama 3.3 70B (Cloudflare)",
        "context_window": 131072,
        "max_output_tokens": 4096,
        "input_cost_per_1k": 0.0,
        "output_cost_per_1k": 0.0,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
        ],
    },
    # Moonshot
    {
        "model_id": "moonshot-v1-128k",
        "provider": LLMProvider.MOONSHOT,
        "display_name": "Moonshot v1 128K",
        "context_window": 128000,
        "max_output_tokens": 8192,
        "input_cost_per_1k": 0.002,
        "output_cost_per_1k": 0.006,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.LONG_CONTEXT,
        ],
    },
    # vLLM (local)
    {
        "model_id": "vllm/default",
        "provider": LLMProvider.VLLM,
        "display_name": "vLLM Local Model",
        "context_window": 32768,
        "max_output_tokens": 4096,
        "input_cost_per_1k": 0.0,
        "output_cost_per_1k": 0.0,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
        ],
    },
    # OpenRouter
    {
        "model_id": "anthropic/claude-sonnet-4",
        "provider": LLMProvider.OPENROUTER,
        "display_name": "Claude Sonnet 4 (OpenRouter)",
        "context_window": 200000,
        "max_output_tokens": 16000,
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
        "capabilities": [
            ModelCapability.CHAT, ModelCapability.STREAMING,
            ModelCapability.TOOL_USE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT,
        ],
    },
]


class LLMModelRegistry:
    """LLM model kayit defteri.

    Model katalogu, yetenek sorgulama, fiyatlandirma
    ve model onerileri saglar.

    Attributes:
        _models: Model katalogu.
        _lookup_count: Sorgulama sayisi.
    """

    def __init__(self, load_defaults: bool = True) -> None:
        """LLMModelRegistry baslatir.

        Args:
            load_defaults: Varsayilan modelleri yukle.
        """
        self._models: dict[str, ModelInfo] = {}
        self._lookup_count: int = 0

        if load_defaults:
            self._load_defaults()

        logger.info(
            "LLMModelRegistry baslatildi: %d model",
            len(self._models),
        )

    def _load_defaults(self) -> None:
        """Varsayilan modelleri yukler."""
        for data in _DEFAULT_MODELS:
            info = ModelInfo(
                model_id=data["model_id"],
                provider=data["provider"],
                display_name=data["display_name"],
                context_window=data["context_window"],
                max_output_tokens=data["max_output_tokens"],
                input_cost_per_1k=data["input_cost_per_1k"],
                output_cost_per_1k=data["output_cost_per_1k"],
                capabilities=data["capabilities"],
            )
            self._models[info.model_id] = info

    def register(self, model: ModelInfo) -> None:
        """Model kaydeder.

        Args:
            model: Model bilgisi.
        """
        self._models[model.model_id] = model
        logger.info("Model kaydedildi: %s", model.model_id)

    def unregister(self, model_id: str) -> bool:
        """Model kaydini siler.

        Args:
            model_id: Model ID'si.

        Returns:
            Basarili ise True.
        """
        if model_id in self._models:
            del self._models[model_id]
            logger.info("Model silindi: %s", model_id)
            return True
        return False

    def get(self, model_id: str) -> ModelInfo | None:
        """Model bilgisi getirir.

        Args:
            model_id: Model ID'si.

        Returns:
            Model bilgisi veya None.
        """
        self._lookup_count += 1
        return self._models.get(model_id)

    def list_all(self) -> list[ModelInfo]:
        """Tum modelleri listeler.

        Returns:
            Model listesi.
        """
        return list(self._models.values())

    def list_by_provider(self, provider: LLMProvider) -> list[ModelInfo]:
        """Saglayiciya gore filtreler.

        Args:
            provider: LLM saglayicisi.

        Returns:
            Filtrelenmis model listesi.
        """
        return [
            m for m in self._models.values()
            if m.provider == provider
        ]

    def list_by_capability(
        self, capability: ModelCapability
    ) -> list[ModelInfo]:
        """Yetenege gore filtreler.

        Args:
            capability: Model yetenegi.

        Returns:
            Filtrelenmis model listesi.
        """
        return [
            m for m in self._models.values()
            if capability in m.capabilities
        ]

    def find_cheapest(
        self,
        capability: ModelCapability | None = None,
        provider: LLMProvider | None = None,
    ) -> ModelInfo | None:
        """En ucuz modeli bulur.

        Args:
            capability: Gerekli yetenek.
            provider: Saglayici filtresi.

        Returns:
            En ucuz model veya None.
        """
        candidates = list(self._models.values())

        if capability:
            candidates = [
                m for m in candidates if capability in m.capabilities
            ]
        if provider:
            candidates = [m for m in candidates if m.provider == provider]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda m: m.input_cost_per_1k + m.output_cost_per_1k,
        )

    def find_best_context(
        self,
        min_context: int = 0,
        provider: LLMProvider | None = None,
    ) -> ModelInfo | None:
        """En genis baglamli modeli bulur.

        Args:
            min_context: Minimum baglam penceresi.
            provider: Saglayici filtresi.

        Returns:
            En genis baglamli model veya None.
        """
        candidates = [
            m for m in self._models.values()
            if m.context_window >= min_context
        ]

        if provider:
            candidates = [m for m in candidates if m.provider == provider]

        if not candidates:
            return None

        return max(candidates, key=lambda m: m.context_window)

    def recommend(
        self,
        task_type: str = "general",
        budget: str = "medium",
    ) -> list[ModelInfo]:
        """Gorev tipine gore model onerir.

        Args:
            task_type: Gorev tipi (general, coding, vision, embedding).
            budget: Butce (low, medium, high).

        Returns:
            Onerilen model listesi.
        """
        candidates = list(self._models.values())

        # Gorev tipine gore filtrele
        cap_map = {
            "coding": ModelCapability.TOOL_USE,
            "vision": ModelCapability.VISION,
            "embedding": ModelCapability.EMBEDDING,
        }
        if task_type in cap_map:
            cap = cap_map[task_type]
            candidates = [m for m in candidates if cap in m.capabilities]

        # Butceye gore sirala
        if budget == "low":
            candidates.sort(
                key=lambda m: m.input_cost_per_1k + m.output_cost_per_1k
            )
        elif budget == "high":
            candidates.sort(
                key=lambda m: m.context_window, reverse=True
            )
        else:
            # medium: maliyet/yetenek dengesi
            candidates.sort(
                key=lambda m: (
                    len(m.capabilities) * -1,
                    m.input_cost_per_1k + m.output_cost_per_1k,
                )
            )

        return candidates[:3]

    def estimate_cost(
        self,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Maliyet tahmini yapar.

        Args:
            model_id: Model ID'si.
            prompt_tokens: Girdi token sayisi.
            completion_tokens: Cikti token sayisi.

        Returns:
            Tahmini maliyet (USD).
        """
        model = self._models.get(model_id)
        if not model:
            return 0.0

        input_cost = (prompt_tokens / 1000) * model.input_cost_per_1k
        output_cost = (completion_tokens / 1000) * model.output_cost_per_1k
        return input_cost + output_cost

    def clamp_max_tokens(
        self,
        model_id: str,
        requested_tokens: int,
    ) -> int:
        """maxTokens'i contextWindow'a gore kisitlar.

        Args:
            model_id: Model ID'si.
            requested_tokens: Istenen token sayisi.

        Returns:
            Kisitlanmis token sayisi.
        """
        model = self._models.get(model_id)
        if not model:
            return requested_tokens
        max_allowed = model.max_output_tokens
        if max_allowed <= 0:
            max_allowed = model.context_window
        return min(requested_tokens, max_allowed)

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        providers: dict[str, int] = {}
        for m in self._models.values():
            prov = m.provider.value
            providers[prov] = providers.get(prov, 0) + 1

        return {
            "total_models": len(self._models),
            "providers": providers,
            "lookup_count": self._lookup_count,
        }
