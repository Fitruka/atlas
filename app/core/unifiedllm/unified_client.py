"""Unified LLM Client - Tek arayuz.

Tum LLM saglayicilarini tek arayuzden kullanma,
provider soyutlama, yanit normalizasyonu,
hata yonetimi ve yeniden deneme saglar.
"""

import logging
import time
from typing import Any, AsyncIterator

from app.models.unifiedllm_models import (
    FinishReason,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ModelInfo,
    ProviderStatus,
    StreamChunk,
    UnifiedLLMSnapshot,
)
from app.core.unifiedllm.anthropic_adapter import AnthropicAdapter
from app.core.unifiedllm.openai_adapter import OpenAIAdapter
from app.core.unifiedllm.gemini_adapter import GeminiAdapter
from app.core.unifiedllm.ollama_adapter import OllamaAdapter
from app.core.unifiedllm.openrouter_adapter import OpenRouterAdapter
from app.core.unifiedllm.model_registry import LLMModelRegistry
from app.core.unifiedllm.api_key_rotator import APIKeyRotator

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    """Unified LLM Client.

    Tum LLM saglayicilarini tek arayuzden yonetir,
    otomatik failover, maliyet takibi ve yeniden deneme saglar.

    Attributes:
        _default_provider: Varsayilan saglayici.
        _fallback_chain: Yedek saglayici zinciri.
        _retry_count: Yeniden deneme sayisi.
        _timeout: Zaman asimi (saniye).
        _registry: Model kayit defteri.
        _rotator: API anahtar rotatoru.
        _adapters: Saglayici adaptorler.
        _request_count: Toplam istek.
        _total_tokens: Toplam token.
        _total_cost: Toplam maliyet.
        _errors: Hata sayisi.
        _provider_errors: Saglayici bazli hata.
    """

    def __init__(
        self,
        default_provider: str = "anthropic",
        fallback_chain: str = "anthropic,openai,gemini",
        retry_count: int = 3,
        timeout_seconds: int = 30,
        anthropic_api_key: str = "",
        openai_api_key: str = "",
        gemini_api_key: str = "",
        openrouter_api_key: str = "",
        ollama_base_url: str = "http://localhost:11434",
    ) -> None:
        """UnifiedLLMClient baslatir.

        Args:
            default_provider: Varsayilan saglayici.
            fallback_chain: Yedek zinciri (virgul ayirmali).
            retry_count: Yeniden deneme sayisi.
            timeout_seconds: Zaman asimi.
            anthropic_api_key: Anthropic API anahtari.
            openai_api_key: OpenAI API anahtari.
            gemini_api_key: Gemini API anahtari.
            openrouter_api_key: OpenRouter API anahtari.
            ollama_base_url: Ollama sunucu URL.
        """
        self._default_provider = default_provider
        self._fallback_chain = [
            p.strip() for p in fallback_chain.split(",") if p.strip()
        ]
        self._retry_count = retry_count
        self._timeout = timeout_seconds

        # Alt bilesenleri olustur
        self._registry = LLMModelRegistry()
        self._rotator = APIKeyRotator()

        # Adaptorleri olustur
        self._adapters: dict[str, Any] = {}

        self._adapters["anthropic"] = AnthropicAdapter(
            api_key=anthropic_api_key,
        )
        self._adapters["openai"] = OpenAIAdapter(
            api_key=openai_api_key,
        )
        self._adapters["gemini"] = GeminiAdapter(
            api_key=gemini_api_key,
        )
        self._adapters["ollama"] = OllamaAdapter(
            base_url=ollama_base_url,
        )
        self._adapters["openrouter"] = OpenRouterAdapter(
            api_key=openrouter_api_key,
        )

        # API anahtarlarini rotatora ekle
        if anthropic_api_key:
            self._rotator.add_key(
                LLMProvider.ANTHROPIC, anthropic_api_key, "anthropic_0"
            )
        if openai_api_key:
            self._rotator.add_key(
                LLMProvider.OPENAI, openai_api_key, "openai_0"
            )
        if gemini_api_key:
            self._rotator.add_key(
                LLMProvider.GEMINI, gemini_api_key, "gemini_0"
            )
        if openrouter_api_key:
            self._rotator.add_key(
                LLMProvider.OPENROUTER, openrouter_api_key, "openrouter_0"
            )

        # Istatistikler
        self._request_count: int = 0
        self._total_tokens: int = 0
        self._total_cost: float = 0.0
        self._errors: int = 0
        self._provider_errors: dict[str, int] = {}

        logger.info(
            "UnifiedLLMClient baslatildi: default=%s, fallback=%s",
            default_provider, self._fallback_chain,
        )

    def _build_headers(self, request: LLMRequest) -> dict[str, str]:
        """Istege ozel ek basliklar olusturur.

        Args:
            request: LLM istegi.

        Returns:
            Baslik sozlugu.
        """
        headers: dict[str, str] = {}
        if request.context_1m and request.provider == LLMProvider.ANTHROPIC:
            headers["anthropic-beta"] = "context-1m-2025-08-07"
        return headers

    def _classify_stop_reason(self, reason: str) -> FinishReason:
        """Durdurma nedenini siniflandirir.

        abort/timeout → failover icin TIMEOUT olarak siniflandirilir.

        Args:
            reason: Ham durdurma nedeni.

        Returns:
            FinishReason enum degeri.
        """
        reason_lower = reason.lower() if reason else ""
        if reason_lower in ("abort", "timeout", "cancelled"):
            return FinishReason.TIMEOUT
        if reason_lower in ("stop", "end_turn"):
            return FinishReason.STOP
        if reason_lower in ("length", "max_tokens"):
            return FinishReason.LENGTH
        if reason_lower in ("tool_use", "tool_calls"):
            return FinishReason.TOOL_USE
        if reason_lower in ("content_filter", "safety"):
            return FinishReason.CONTENT_FILTER
        return FinishReason.ERROR

    def _probe_primary(self, provider_name: str) -> bool:
        """Cooldown'u bitmek uzere olan birincil saglayiciyi test eder.

        Args:
            provider_name: Saglayici adi.

        Returns:
            Saglayici kullanilabilir ise True.
        """
        adapter = self._get_adapter(provider_name)
        if not adapter:
            return False
        try:
            stats = adapter.get_stats()
            return stats.get("is_available", True)
        except Exception:
            return False

    def _clamp_request_tokens(self, request: LLMRequest) -> None:
        """maxTokens'i model limitlerine gore kisitlar.

        Args:
            request: LLM istegi (yerinde degistirilir).
        """
        if request.model and request.max_tokens > 0:
            clamped = self._registry.clamp_max_tokens(
                request.model, request.max_tokens,
            )
            if clamped != request.max_tokens:
                logger.debug(
                    "maxTokens kisitlandi: %d -> %d (model: %s)",
                    request.max_tokens, clamped, request.model,
                )
                request.max_tokens = clamped

    def _resolve_provider(self, request: LLMRequest) -> str:
        """Istek icin saglayiciyi belirler.

        Args:
            request: LLM istegi.

        Returns:
            Saglayici adi.
        """
        if request.provider:
            return request.provider.value
        return self._default_provider

    def _get_adapter(self, provider: str) -> Any:
        """Saglayici adaptorunU getirir.

        Args:
            provider: Saglayici adi.

        Returns:
            Adaptor veya None.
        """
        return self._adapters.get(provider)

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Sohbet istegi gonderir (failover ile).

        Args:
            request: LLM istegi.

        Returns:
            LLM yaniti.
        """
        # maxTokens kisitla
        self._clamp_request_tokens(request)

        primary = self._resolve_provider(request)
        providers_to_try = [primary]

        # Fallback zincirini ekle
        for fb in self._fallback_chain:
            if fb != primary and fb not in providers_to_try:
                providers_to_try.append(fb)

        last_error: str = ""

        for provider_name in providers_to_try:
            adapter = self._get_adapter(provider_name)
            if not adapter:
                continue

            for attempt in range(self._retry_count):
                try:
                    response = await adapter.chat(request)

                    if response.finish_reason != FinishReason.ERROR:
                        self._request_count += 1
                        if response.usage:
                            self._total_tokens += response.usage.total_tokens
                            self._total_cost += response.usage.cost_usd
                        return response

                    last_error = str(
                        response.raw_response.get("error", "unknown")
                        if response.raw_response else "unknown"
                    )

                except Exception as e:
                    last_error = str(e)
                    self._provider_errors[provider_name] = (
                        self._provider_errors.get(provider_name, 0) + 1
                    )
                    logger.warning(
                        "Saglayici hatasi: %s, deneme %d/%d: %s",
                        provider_name, attempt + 1,
                        self._retry_count, e,
                    )

            logger.warning(
                "Saglayici basarisiz, sonrakine geciliyor: %s",
                provider_name,
            )

        # Tum saglayicilar basarisiz
        self._errors += 1
        return LLMResponse(
            provider=LLMProvider(primary) if primary in [
                p.value for p in LLMProvider
            ] else LLMProvider.ANTHROPIC,
            model=request.model or "",
            content="",
            finish_reason=FinishReason.ERROR,
            latency_ms=0.0,
            raw_response={"error": f"Tum saglayicilar basarisiz: {last_error}"},
        )

    async def stream(
        self, request: LLMRequest
    ) -> AsyncIterator[StreamChunk]:
        """Streaming sohbet istegi gonderir.

        Args:
            request: LLM istegi.

        Yields:
            Akim parcalari.
        """
        provider_name = self._resolve_provider(request)
        adapter = self._get_adapter(provider_name)

        if not adapter:
            yield StreamChunk(
                content="[Hata: Saglayici bulunamadi]",
                is_final=True,
            )
            return

        try:
            async for chunk in adapter.stream(request):
                yield chunk

            self._request_count += 1

        except Exception as e:
            self._errors += 1
            logger.error("Stream hatasi: %s", e)
            yield StreamChunk(
                content=f"[Hata: {e}]",
                is_final=True,
            )

    def get_model_info(self, model_id: str) -> ModelInfo | None:
        """Model bilgisi getirir.

        Args:
            model_id: Model ID'si.

        Returns:
            Model bilgisi veya None.
        """
        return self._registry.get(model_id)

    def list_models(
        self, provider: LLMProvider | None = None
    ) -> list[ModelInfo]:
        """Modelleri listeler.

        Args:
            provider: Saglayici filtresi.

        Returns:
            Model listesi.
        """
        if provider:
            return self._registry.list_by_provider(provider)
        return self._registry.list_all()

    def estimate_cost(
        self,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Maliyet tahmini yapar.

        Args:
            model_id: Model ID'si.
            prompt_tokens: Girdi token.
            completion_tokens: Cikti token.

        Returns:
            Tahmini maliyet (USD).
        """
        return self._registry.estimate_cost(
            model_id, prompt_tokens, completion_tokens
        )

    def get_provider_status(
        self, provider: LLMProvider
    ) -> ProviderStatus:
        """Saglayici durumunu dondurur.

        Args:
            provider: LLM saglayicisi.

        Returns:
            Saglayici durumu.
        """
        adapter = self._get_adapter(provider.value)
        stats = adapter.get_stats() if adapter else {}

        return ProviderStatus(
            provider=provider,
            is_available=adapter is not None,
            active_keys=self._rotator.get_active_count(provider),
            total_requests=stats.get("request_count", 0),
            total_tokens=stats.get("total_tokens", 0),
            total_cost=stats.get("total_cost", 0.0),
            error_count=stats.get("errors", 0),
        )

    @property
    def registry(self) -> LLMModelRegistry:
        """Model kayit defterini dondurur."""
        return self._registry

    @property
    def rotator(self) -> APIKeyRotator:
        """API anahtar rotatorunu dondurur."""
        return self._rotator

    def get_snapshot(self) -> UnifiedLLMSnapshot:
        """Sistem snapshot'i dondurur.

        Returns:
            Sistem durumu.
        """
        provider_statuses: list[ProviderStatus] = []
        for name, adapter in self._adapters.items():
            try:
                prov = LLMProvider(name)
            except ValueError:
                continue
            stats = adapter.get_stats()
            provider_statuses.append(ProviderStatus(
                provider=prov,
                is_available=True,
                total_requests=stats.get("request_count", 0),
                total_tokens=stats.get("total_tokens", 0),
                total_cost=stats.get("total_cost", 0.0),
                error_count=stats.get("errors", 0),
            ))

        rotator_stats = self._rotator.get_stats()
        registry_stats = self._registry.get_stats()

        return UnifiedLLMSnapshot(
            providers=provider_statuses,
            total_requests=self._request_count,
            total_tokens=self._total_tokens,
            total_cost=self._total_cost,
            active_provider=self._default_provider,
            fallback_chain=list(self._fallback_chain),
            models_registered=registry_stats.get("total_models", 0),
            keys_active=rotator_stats.get("active_keys", 0),
        )

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "default_provider": self._default_provider,
            "fallback_chain": self._fallback_chain,
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
            "errors": self._errors,
            "provider_errors": dict(self._provider_errors),
            "registry": self._registry.get_stats(),
            "rotator": self._rotator.get_stats(),
        }
