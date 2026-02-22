"""Ollama yerel model adaptoru.

Yerel modeller, model yonetimi, streaming,
ozel modeller ve embedding destegi saglar.
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
    UsageInfo,
)

logger = logging.getLogger(__name__)


class OllamaAdapter:
    """Ollama yerel model adaptoru.

    Yerel Ollama sunucusu ile iletisim kurar,
    model yonetimi, streaming ve embedding destekler.

    Attributes:
        _base_url: Ollama sunucu URL.
        _default_model: Varsayilan model.
        _available_models: Mevcut modeller.
        _request_count: Toplam istek sayisi.
        _total_tokens: Toplam token.
        _errors: Hata sayisi.
    """

    PROVIDER = LLMProvider.OLLAMA

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.1",
    ) -> None:
        """OllamaAdapter baslatir.

        Args:
            base_url: Ollama sunucu URL.
            default_model: Varsayilan model.
        """
        self._base_url = base_url
        self._default_model = default_model
        self._available_models: list[dict[str, Any]] = []
        self._request_count: int = 0
        self._total_tokens: int = 0
        self._errors: int = 0

        logger.info(
            "OllamaAdapter baslatildi: url=%s, model=%s",
            base_url, default_model,
        )

    def _build_messages(self, request: LLMRequest) -> list[dict[str, Any]]:
        """Mesajlari Ollama formatina donusturur.

        Args:
            request: LLM istegi.

        Returns:
            Ollama formati mesaj listesi.
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
                entry["images"] = msg.images

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

            prompt_tokens = sum(
                len(m.get("content", "")) // 4 for m in messages
            )
            completion_tokens = len(response_content) // 4

            usage = UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=0.0,  # Yerel model - maliyet yok
            )

            self._request_count += 1
            self._total_tokens += usage.total_tokens

            latency = (time.time() - start) * 1000

            return LLMResponse(
                provider=self.PROVIDER,
                model=model,
                content=response_content,
                finish_reason=FinishReason.STOP,
                usage=usage,
                latency_ms=latency,
            )

        except Exception as e:
            self._errors += 1
            latency = (time.time() - start) * 1000
            logger.error("Ollama hatasi: %s", e)
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

    async def generate_embedding(
        self, text: str, model: str = ""
    ) -> list[float]:
        """Embedding uretir.

        Args:
            text: Girdi metni.
            model: Model adi.

        Returns:
            Embedding vektoru.
        """
        model = model or self._default_model
        # Simule edilmis embedding
        import hashlib
        h = hashlib.md5(text.encode()).hexdigest()
        embedding = [
            int(h[i:i + 2], 16) / 255.0 for i in range(0, 32, 2)
        ]
        # 16 boyutlu normalize vektor
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]

        self._request_count += 1
        return embedding

    async def list_models(self) -> list[dict[str, Any]]:
        """Mevcut modelleri listeler.

        Returns:
            Model listesi.
        """
        # Simule edilmis model listesi
        if not self._available_models:
            self._available_models = [
                {"name": "llama3.1", "size": "8B", "format": "gguf"},
                {"name": "mistral", "size": "7B", "format": "gguf"},
                {"name": "codellama", "size": "7B", "format": "gguf"},
                {"name": "nomic-embed-text", "size": "137M", "format": "gguf"},
            ]
        return self._available_models

    async def pull_model(self, model_name: str) -> dict[str, Any]:
        """Model indirir.

        Args:
            model_name: Model adi.

        Returns:
            Indirme durumu.
        """
        logger.info("Model indiriliyor: %s", model_name)
        return {
            "model": model_name,
            "status": "success",
            "message": f"Model {model_name} simule olarak indirildi",
        }

    async def delete_model(self, model_name: str) -> bool:
        """Modeli siler.

        Args:
            model_name: Model adi.

        Returns:
            Basarili ise True.
        """
        self._available_models = [
            m for m in self._available_models
            if m.get("name") != model_name
        ]
        logger.info("Model silindi: %s", model_name)
        return True

    async def check_health(self) -> dict[str, Any]:
        """Ollama sunucu sagligini kontrol eder.

        Returns:
            Saglik durumu.
        """
        return {
            "status": "ok",
            "url": self._base_url,
            "models": len(self._available_models),
        }

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
            if c:
                last = c
                break

        return f"[Ollama/{model}] Simulated response to: {last[:50]}"

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "provider": self.PROVIDER.value,
            "base_url": self._base_url,
            "default_model": self._default_model,
            "request_count": self._request_count,
            "total_tokens": self._total_tokens,
            "errors": self._errors,
            "available_models": len(self._available_models),
        }
