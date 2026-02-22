"""Google Gemini API adaptoru.

Gemini API, multi-modal, streaming, safety settings
ve grounding destegi saglar.
"""

import logging
import time
from typing import Any, AsyncIterator

from app.models.unifiedllm_models import (
    ChatMessage,
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


class GeminiAdapter:
    """Google Gemini API adaptoru.

    Gemini API ile iletisim kurar, multi-modal,
    streaming, safety settings ve grounding destekler.

    Attributes:
        _api_key: API anahtari.
        _default_model: Varsayilan model.
        _safety_settings: Guvenlik ayarlari.
        _request_count: Toplam istek sayisi.
        _total_tokens: Toplam token.
        _total_cost: Toplam maliyet.
        _errors: Hata sayisi.
    """

    PROVIDER = LLMProvider.GEMINI

    def __init__(
        self,
        api_key: str = "",
        default_model: str = "gemini-2.0-flash",
        safety_settings: dict[str, str] | None = None,
    ) -> None:
        """GeminiAdapter baslatir.

        Args:
            api_key: Google AI API anahtari.
            default_model: Varsayilan model.
            safety_settings: Guvenlik ayarlari.
        """
        self._api_key = api_key
        self._default_model = default_model
        self._safety_settings = safety_settings or {}
        self._request_count: int = 0
        self._total_tokens: int = 0
        self._total_cost: float = 0.0
        self._errors: int = 0

        logger.info("GeminiAdapter baslatildi: model=%s", default_model)

    def _build_contents(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Mesajlari Gemini formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            Gemini formati icerik listesi.
        """
        contents = []

        for msg in request.messages:
            if msg.role == MessageRole.SYSTEM:
                continue

            parts: list[dict[str, Any]] = []

            if msg.content:
                parts.append({"text": msg.content})

            if msg.images:
                for img in msg.images:
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": img,
                        }
                    })

            role = "user" if msg.role in (MessageRole.USER, MessageRole.TOOL) else "model"
            contents.append({"role": role, "parts": parts})

        return contents

    def _build_tools(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Araclari Gemini formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            Gemini formati arac listesi.
        """
        if not request.tools:
            return []

        declarations = []
        for tool in request.tools:
            declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            })

        return [{"function_declarations": declarations}]

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Sohbet istegi gonderir.

        Args:
            request: LLM istegi.

        Returns:
            LLM yaniti.
        """
        start = time.time()
        model = request.model or self._default_model
        contents = self._build_contents(request)

        try:
            response_content = self._simulate_response(contents, model)

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
                len(str(c.get("parts", ""))) // 4 for c in contents
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
            logger.error("Gemini hatasi: %s", e)
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
        contents = self._build_contents(request)
        response_text = self._simulate_response(contents, model)

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

    def set_safety_settings(self, settings: dict[str, str]) -> None:
        """Guvenlik ayarlarini gunceller.

        Args:
            settings: Guvenlik ayarlari.
        """
        self._safety_settings.update(settings)
        logger.info("Guvenlik ayarlari guncellendi: %d ayar", len(settings))

    def _simulate_response(
        self, contents: list[dict[str, Any]], model: str
    ) -> str:
        """Simule edilmis yanit uretir.

        Args:
            contents: Icerik listesi.
            model: Model adi.

        Returns:
            Simule yanit metni.
        """
        last = ""
        for c in reversed(contents):
            parts = c.get("parts", [])
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    last = part["text"]
                    break
            if last:
                break

        return f"[Gemini/{model}] Simulated response to: {last[:50]}"

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Maliyet hesaplar.

        Args:
            model: Model adi.
            prompt_tokens: Girdi token.
            completion_tokens: Cikti token.

        Returns:
            Maliyet (USD).
        """
        costs = {
            "gemini-2.0-flash": (0.0001, 0.0004),
            "gemini-2.0-pro": (0.00125, 0.005),
            "gemini-1.5-pro": (0.00125, 0.005),
            "gemini-1.5-flash": (0.000075, 0.0003),
        }
        input_cost, output_cost = costs.get(model, (0.0001, 0.0004))
        return (prompt_tokens * input_cost + completion_tokens * output_cost) / 1000

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "provider": self.PROVIDER.value,
            "default_model": self._default_model,
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
            "errors": self._errors,
            "safety_settings": dict(self._safety_settings),
        }
