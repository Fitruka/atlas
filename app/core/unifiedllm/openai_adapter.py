"""OpenAI GPT API adaptoru.

GPT API, chat completions, streaming, function calling
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


class OpenAIAdapter:
    """OpenAI GPT API adaptoru.

    GPT Chat Completions API ile iletisim kurar,
    streaming, function calling ve vision destekler.

    Attributes:
        _api_key: API anahtari.
        _base_url: API temel URL.
        _default_model: Varsayilan model.
        _request_count: Toplam istek sayisi.
        _total_tokens: Toplam token.
        _total_cost: Toplam maliyet.
        _errors: Hata sayisi.
    """

    PROVIDER = LLMProvider.OPENAI

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o",
    ) -> None:
        """OpenAIAdapter baslatir.

        Args:
            api_key: OpenAI API anahtari.
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

        logger.info("OpenAIAdapter baslatildi: model=%s", default_model)

    def _build_messages(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Mesajlari OpenAI formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            OpenAI formati mesaj listesi.
        """
        messages = []

        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt,
            })

        for msg in request.messages:
            entry: dict[str, Any] = {"role": msg.role.value}

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
            else:
                entry["content"] = msg.content

            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id

            if msg.tool_calls:
                entry["tool_calls"] = msg.tool_calls

            messages.append(entry)

        return messages

    def _build_tools(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Araclari OpenAI formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            OpenAI formati arac listesi.
        """
        tools = []
        for tool in request.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            })
        return tools

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
            logger.error("OpenAI hatasi: %s", e)
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
        last = ""
        for msg in reversed(messages):
            c = msg.get("content", "")
            if isinstance(c, str) and c:
                last = c
                break
            elif isinstance(c, list):
                for item in c:
                    if isinstance(item, dict) and item.get("type") == "text":
                        last = item.get("text", "")
                        break
                if last:
                    break

        return f"[OpenAI/{model}] Simulated response to: {last[:50]}"

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
            "gpt-4o": (0.005, 0.015),
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-4": (0.03, 0.06),
            "gpt-3.5-turbo": (0.0005, 0.0015),
        }
        input_cost, output_cost = costs.get(model, (0.005, 0.015))
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
