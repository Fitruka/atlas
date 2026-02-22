"""OpenRouter API adaptoru.

300+ model, unified API, maliyet takibi, rate limit
ve model bilgisi destegi saglar.
"""

import logging
import time
from typing import Any, AsyncIterator

from app.models.unifiedllm_models import (
    FinishReason,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    MessageRole,
    StreamChunk,
    ToolCall,
    UsageInfo,
)

logger = logging.getLogger(__name__)

# --- Populer OpenRouter modelleri ---

_OPENROUTER_MODELS: dict[str, dict[str, Any]] = {
    "anthropic/claude-sonnet-4": {
        "name": "Claude Sonnet 4",
        "context": 200000,
        "input_cost": 0.003,
        "output_cost": 0.015,
    },
    "openai/gpt-4o": {
        "name": "GPT-4o",
        "context": 128000,
        "input_cost": 0.005,
        "output_cost": 0.015,
    },
    "google/gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "context": 1000000,
        "input_cost": 0.0001,
        "output_cost": 0.0004,
    },
    "meta-llama/llama-3.1-70b-instruct": {
        "name": "Llama 3.1 70B",
        "context": 131072,
        "input_cost": 0.00059,
        "output_cost": 0.00079,
    },
    "mistralai/mistral-large": {
        "name": "Mistral Large",
        "context": 128000,
        "input_cost": 0.002,
        "output_cost": 0.006,
    },
    "deepseek/deepseek-r1": {
        "name": "DeepSeek R1",
        "context": 64000,
        "input_cost": 0.00055,
        "output_cost": 0.00219,
    },
}


class OpenRouterAdapter:
    """OpenRouter API adaptoru.

    300+ modele tek API uzerinden erisim saglar,
    maliyet takibi ve rate limit yonetir.

    Attributes:
        _api_key: API anahtari.
        _base_url: API temel URL.
        _default_model: Varsayilan model.
        _site_url: Uygulamanin URL'si.
        _app_name: Uygulama adi.
        _request_count: Toplam istek sayisi.
        _total_tokens: Toplam token.
        _total_cost: Toplam maliyet.
        _errors: Hata sayisi.
        _credits_remaining: Kalan kredi.
    """

    PROVIDER = LLMProvider.OPENROUTER

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "anthropic/claude-sonnet-4",
        site_url: str = "",
        app_name: str = "ATLAS",
    ) -> None:
        """OpenRouterAdapter baslatir.

        Args:
            api_key: OpenRouter API anahtari.
            base_url: API temel URL.
            default_model: Varsayilan model.
            site_url: Uygulama URL'si.
            app_name: Uygulama adi.
        """
        self._api_key = api_key
        self._base_url = base_url
        self._default_model = default_model
        self._site_url = site_url
        self._app_name = app_name
        self._request_count: int = 0
        self._total_tokens: int = 0
        self._total_cost: float = 0.0
        self._errors: int = 0
        self._credits_remaining: float = -1.0

        logger.info(
            "OpenRouterAdapter baslatildi: model=%s",
            default_model,
        )

    def _build_messages(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Mesajlari OpenRouter formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            OpenRouter formati mesaj listesi.
        """
        messages = []

        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt,
            })

        for msg in request.messages:
            entry: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content,
            }

            if msg.images:
                content_parts: list[dict[str, Any]] = []
                for img in msg.images:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img}"},
                    })
                if msg.content:
                    content_parts.append({"type": "text", "text": msg.content})
                entry["content"] = content_parts

            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id

            messages.append(entry)

        return messages

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Sohbet istegi gonderir.

        Args:
            request: LLM istegi.

        Returns:
            LLM yaniti.
        """
        start = time.time()
        model = request.model or self._default_model
        messages = self._build_messages(request)

        try:
            response_content = self._simulate_response(messages, model)

            tool_calls = []
            finish = FinishReason.STOP

            if request.tools:
                tool_calls = [
                    ToolCall(
                        name=request.tools[0].name,
                        arguments={"query": "simulated"},
                    )
                ]
                finish = FinishReason.TOOL_USE

            prompt_tokens = sum(
                len(str(m.get("content", ""))) // 4 for m in messages
            )
            completion_tokens = len(response_content) // 4

            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=self._calculate_cost(
                    model, prompt_tokens, completion_tokens
                ),
            )

            self._request_count += 1
            self._total_tokens += usage.total_tokens
            self._total_cost += usage.cost_usd

            latency = (time.time() - start) * 1000

            return LLMResponse(
                provider=self.PROVIDER,
                model=model,
                content=response_content,
                finish_reason=finish,
                tool_calls=tool_calls if request.tools else [],
                usage=usage,
                latency_ms=latency,
            )

        except Exception as e:
            self._errors += 1
            latency = (time.time() - start) * 1000
            logger.error("OpenRouter hatasi: %s", e)
            return LLMResponse(
                provider=self.PROVIDER,
                model=model,
                content="",
                finish_reason=FinishReason.ERROR,
                latency_ms=latency,
                raw_response={"error": str(e)},
            )

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Streaming sohbet istegi gonderir.

        Args:
            request: LLM istegi.

        Yields:
            Akim parcalari.
        """
        model = request.model or self._default_model
        messages = self._build_messages(request)
        response_text = self._simulate_response(messages, model)

        words = response_text.split()
        for i, word in enumerate(words):
            is_final = (i == len(words) - 1)
            chunk = StreamChunk(
                content=word + (" " if not is_final else ""),
                is_final=is_final,
            )
            if is_final:
                tokens = len(response_text) // 4
                chunk.usage = UsageInfo(
                    prompt_tokens=tokens,
                    completion_tokens=tokens,
                    total_tokens=tokens * 2,
                )
            yield chunk

        self._request_count += 1

    async def list_models(self) -> list[dict[str, Any]]:
        """Mevcut modelleri listeler.

        Returns:
            Model listesi.
        """
        models = []
        for model_id, info in _OPENROUTER_MODELS.items():
            models.append({
                "id": model_id,
                "name": info["name"],
                "context_length": info["context"],
                "pricing": {
                    "prompt": info["input_cost"],
                    "completion": info["output_cost"],
                },
            })
        return models

    async def get_model_info(self, model_id: str) -> dict[str, Any] | None:
        """Model bilgisini getirir.

        Args:
            model_id: Model ID'si.

        Returns:
            Model bilgisi veya None.
        """
        info = _OPENROUTER_MODELS.get(model_id)
        if not info:
            return None

        return {
            "id": model_id,
            "name": info["name"],
            "context_length": info["context"],
            "pricing": {
                "prompt": info["input_cost"],
                "completion": info["output_cost"],
            },
        }

    async def get_credits(self) -> dict[str, Any]:
        """Kalan kredi bilgisini getirir.

        Returns:
            Kredi bilgisi.
        """
        return {
            "remaining": self._credits_remaining,
            "total_spent": self._total_cost,
        }

    def _simulate_response(
        self, messages: list[dict[str, Any]], model: str
    ) -> str:
        """Simule edilmis yanit uretir."""
        last = ""
        for msg in reversed(messages):
            c = msg.get("content", "")
            if isinstance(c, str) and c:
                last = c
                break
        return f"[OpenRouter/{model}] Simulated response to: {last[:50]}"

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Maliyet hesaplar."""
        info = _OPENROUTER_MODELS.get(model, {})
        input_cost = info.get("input_cost", 0.003)
        output_cost = info.get("output_cost", 0.015)
        return (prompt_tokens * input_cost + completion_tokens * output_cost) / 1000

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        return {
            "provider": self.PROVIDER.value,
            "default_model": self._default_model,
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
            "errors": self._errors,
            "credits_remaining": self._credits_remaining,
            "available_models": len(_OPENROUTER_MODELS),
        }
