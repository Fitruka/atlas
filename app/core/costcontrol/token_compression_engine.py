"""Token sıkıştırma motoru.

Context sıkıştırma ile token tasarrufu,
özet tabanlı sıkıştırma, seçici sıkıştırma.
"""

import logging
from typing import Any

from app.models.costcontrol_models import (
    CompressionResult,
    CompressionStrategy,
)

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 4  # Yaklaşık
_MIN_TOKENS_TO_COMPRESS = 500
_MAX_COMPRESSION_RATIO = 0.9


class TokenCompressionEngine:
    """Token sıkıştırma motoru.

    Context boyutunu küçülterek token
    tasarrufu sağlar.

    Attributes:
        _results: Sıkıştırma sonuçları.
        _total_saved: Toplam tasarruf.
    """

    def __init__(self) -> None:
        """TokenCompressionEngine başlatır."""
        self._results: list[CompressionResult] = []
        self._total_saved_tokens: int = 0
        self._total_compressed: int = 0

        logger.info("TokenCompressionEngine baslatildi")

    def compress(
        self,
        text: str,
        strategy: str = "selective",
        target_ratio: float = 0.5,
        model_cost_per_1k: float = 0.003,
    ) -> CompressionResult:
        """Metni sıkıştır.

        Args:
            text: Sıkıştırılacak metin.
            strategy: Sıkıştırma stratejisi.
            target_ratio: Hedef sıkıştırma oranı.
            model_cost_per_1k: Model token maliyeti.

        Returns:
            Sıkıştırma sonucu.
        """
        original_tokens = self._estimate_tokens(text)

        if original_tokens < _MIN_TOKENS_TO_COMPRESS:
            return CompressionResult(
                strategy=strategy,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
            )

        if strategy == "truncate":
            compressed_tokens = int(original_tokens * target_ratio)
        elif strategy == "summary":
            compressed_tokens = int(original_tokens * 0.3)
        elif strategy == "selective":
            compressed_tokens = int(original_tokens * 0.5)
        elif strategy == "aggressive":
            compressed_tokens = int(original_tokens * 0.2)
        else:
            compressed_tokens = original_tokens

        compressed_tokens = max(
            int(original_tokens * (1 - _MAX_COMPRESSION_RATIO)),
            compressed_tokens,
        )

        savings = original_tokens - compressed_tokens
        savings_percent = round((savings / original_tokens) * 100, 1) if original_tokens > 0 else 0.0
        cost_saved = round((savings / 1000) * model_cost_per_1k, 6)

        quality_loss_map = {
            "none": 0.0,
            "truncate": 0.3,
            "summary": 0.15,
            "selective": 0.1,
            "aggressive": 0.4,
        }
        quality_loss = quality_loss_map.get(strategy, 0.1)

        result = CompressionResult(
            strategy=strategy,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            savings_tokens=savings,
            savings_percent=savings_percent,
            quality_loss=quality_loss,
            cost_saved_usd=cost_saved,
        )

        self._results.append(result)
        self._total_saved_tokens += savings
        self._total_compressed += 1

        logger.info(
            "Token sikistirildi: %d -> %d (%%%s tasarruf, strateji: %s)",
            original_tokens,
            compressed_tokens,
            savings_percent,
            strategy,
        )
        return result

    def _estimate_tokens(self, text: str) -> int:
        """Token sayısı tahmin et.

        Args:
            text: Metin.

        Returns:
            Tahmini token sayısı.
        """
        return max(1, len(text) // _CHARS_PER_TOKEN)

    def recommend_strategy(
        self,
        token_count: int,
        importance: str = "medium",
    ) -> str:
        """Sıkıştırma stratejisi öner.

        Args:
            token_count: Token sayısı.
            importance: Önem seviyesi.

        Returns:
            Önerilen strateji.
        """
        if token_count < _MIN_TOKENS_TO_COMPRESS:
            return "none"

        if importance == "high":
            return "selective"
        elif importance == "low":
            return "aggressive"
        elif token_count > 10000:
            return "summary"
        return "selective"

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_compressed": self._total_compressed,
            "total_saved_tokens": self._total_saved_tokens,
        }
