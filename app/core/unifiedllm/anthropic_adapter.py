"""Anthropic Claude API adaptoru.

Claude API, Messages API, streaming, tool use
ve vision destegi saglar.
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


class AnthropicAdapter:
    """Anthropic Claude API adaptoru.

    Claude Messages API ile iletisim kurar,
    streaming, tool use ve vision destekler.

    Attributes:
        _api_key: API anahtari.
        _base_url: API temel URL.
        _default_model: Varsayilan model.
        _request_count: Toplam istek sayisi.
        _total_tokens: Toplam token.
        _total_cost: Toplam maliyet.
        _errors: Hata sayisi.
    """

    PROVIDER = LLMProvider.ANTHROPIC

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.anthropic.com/v1",
        default_model: str = "claude-sonnet-4-20250514",
    ) -> None:
        """AnthropicAdapter baslatir.

        Args:
            api_key: Anthropic API anahtari.
            base_url: API temel URL.
            default_model: Varsayilan model.
        """
        self._api_key = api_key
        self._base_url = base_url
        self._default_model = default_model
        self._request_count: int = 0
        self._total_tokens: int = 0
        self._total_cost: float = 0.0
        self._errors: int = 0

        logger.info(
            "AnthropicAdapter baslatildi: model=%s",
            default_model,
        )

    def _build_messages(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Mesajlari Anthropic formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            Anthropic formati mesaj listesi.
        """
        messages = []
        for msg in request.messages:
            if msg.role == MessageRole.SYSTEM:
                continue

            content: Any
            if msg.images:
                content = []
                for img in msg.images:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img,
                        },
                    })
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
            else:
                content = msg.content

            role = "user" if msg.role == MessageRole.USER else "assistant"
            if msg.role == MessageRole.TOOL:
                role = "user"
                content = [{
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content,
                }]

            messages.append({"role": role, "content": content})

        return messages

    def _build_tools(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Araclari Anthropic formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            Anthropic formati arac listesi.
        """
        tools = []
        for tool in request.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            })
        return tools

    def _get_system_prompt(self, request: LLMRequest) -> str:
        """Sistem promptunu cikarir.

        Args:
            request: LLM istegi.

        Returns:
            Sistem promptu.
        """
        if request.system_prompt:
            return request.system_prompt

        for msg in request.messages:
            if msg.role == MessageRole.SYSTEM:
                return msg.content

        return ""

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
        system_prompt = self._get_system_prompt(request)

        try:
            # Simule edilmis yanit (gercek API cagrisi yerine)
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

            prompt_tokens = sum(len(m.get("content", "")) // 4 for m in messages)
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

            resp = LLMResponse(
                provider=self.PROVIDER,
                model=model,
                content=response_content,
                finish_reason=finish if not request.tools else finish,
                tool_calls=tool_calls if request.tools else [],
                usage=usage,
                latency_ms=latency,
            )

            logger.info(
                "Anthropic yaniti: model=%s, tokens=%d, latency=%.0fms",
                model, usage.total_tokens, latency,
            )
            return resp

        except Exception as e:
            self._errors += 1
            latency = (time.time() - start) * 1000
            logger.error("Anthropic hatasi: %s", e)
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

        # Simule parcali yanitlar
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

    def _simulate_response(
        self, messages: list[dict[str, Any]], model: str
    ) -> str:
        """Simule edilmis yanit uretir.

        Args:
            messages: Mesaj listesi.
            model: Model adi.

        Returns:
            Simule yanit metni.
        """
        last_content = ""
        for msg in reversed(messages):
            c = msg.get("content", "")
            if isinstance(c, str) and c:
                last_content = c
                break
            elif isinstance(c, list):
                for item in c:
                    if isinstance(item, dict) and item.get("type") == "text":
                        last_content = item.get("text", "")
                        break

        return f"[Anthropic/{model}] Simulated response to: {last_content[:50]}"

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Maliyet hesaplar.

        Args:
            model: Model adi.
            prompt_tokens: Girdi token sayisi.
            completion_tokens: Cikti token sayisi.

        Returns:
            Maliyet (USD).
        """
        costs = {
            "claude-opus-4-20250514": (0.015, 0.075),
            "claude-sonnet-4-20250514": (0.003, 0.015),
            "claude-haiku-4-20250506": (0.0008, 0.004),
        }
        input_cost, output_cost = costs.get(model, (0.003, 0.015))
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
        }
