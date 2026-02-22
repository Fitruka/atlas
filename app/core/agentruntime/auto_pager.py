"""Otomatik sayfalama modulu."""

import base64 as b64mod
import logging
import time
from typing import Any, Optional

from app.models.agentruntime_models import AutoPageConfig

logger = logging.getLogger(__name__)


class AutoPager:
    """Otomatik sayfalama yoneticisi."""

    def __init__(self, config: Optional[AutoPageConfig] = None) -> None:
        """AutoPager baslatici."""
        self._config = config or AutoPageConfig()
        self._history: list[dict[str, Any]] = []
        self._total_pages: int = 0
        logger.info("AutoPager baslatildi")

    def _record_history(self, action: str, **kwargs: Any) -> None:
        """Gecmis kaydina olay ekler."""
        entry = {"action": action, "timestamp": time.time(), **kwargs}
        self._history.append(entry)
        if len(self._history) > 1000:
            self._history = self._history[-500:]

    def page_content(self, content: str, chunk_size: Optional[int] = None) -> list[str]:
        """Icerigi sayfalara boler."""
        if not self._config.enabled:
            return [content] if content else []
        size = chunk_size or self._config.chunk_size
        if len(content) <= size:
            return [content]
        chunks: list[str] = []
        start = 0
        while start < len(content) and len(chunks) < self._config.max_chunks:
            end = start + size
            if end < len(content):
                nl = content.rfind(chr(10), start, end)
                if nl > start:
                    end = nl + 1
            chunk = content[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end
        self._total_pages += len(chunks)
        self._record_history("page_content", length=len(content), chunks=len(chunks))
        return chunks

    def scale_budget(self, context_window: int) -> int:
        """Baglam penceresi butcesini hesaplar."""
        if not self._config.budget_from_context:
            return self._config.chunk_size
        budget = int(context_window * 0.6)
        budget = max(budget, 1000)
        budget = min(budget, context_window - 1000)
        self._record_history("scale_budget", context_window=context_window, budget=budget)
        return budget

    def validate_base64(self, payload: str) -> bool:
        """Base64 verisini dogrular."""
        try:
            if not payload or not payload.strip():
                return False
            decoded = b64mod.b64decode(payload, validate=True)
            re_encoded = b64mod.b64encode(decoded).decode()
            valid = re_encoded == payload.strip()
            self._record_history("validate_base64", valid=valid)
            return valid
        except Exception:
            return False

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Islem gecmisini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        return {"total_pages": self._total_pages, "history_size": len(self._history)}
