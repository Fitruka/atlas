"""Gerçek zamanlı maliyet takipçisi.

Session, model, araç bazlı anlık
token ve maliyet takibi, çalışan
toplamlar, geçmiş kayıtları.
"""

import logging
import time
from typing import Any

from app.models.costcontrol_models import CostEntry

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 100000
_MAX_SESSIONS = 1000

# Model fiyatları (USD / 1K token)
_MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4": {"input": 0.003, "output": 0.015},
    "claude-haiku-3.5": {"input": 0.0008, "output": 0.004},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "mistral-large": {"input": 0.002, "output": 0.006},
    "llama-3-70b": {"input": 0.00059, "output": 0.00079},
}


class RealTimeCostTracker:
    """Gerçek zamanlı maliyet takipçisi.

    Her API çağrısının token ve maliyet
    bilgisini anlık takip eder.

    Attributes:
        _entries: Maliyet kayıtları.
        _session_totals: Session bazlı toplamlar.
        _model_totals: Model bazlı toplamlar.
    """

    def __init__(self) -> None:
        """RealTimeCostTracker başlatır."""
        self._entries: list[CostEntry] = []
        self._session_totals: dict[str, dict[str, float]] = {}
        self._model_totals: dict[str, dict[str, float]] = {}
        self._tool_totals: dict[str, dict[str, float]] = {}
        self._total_cost: float = 0.0
        self._total_tokens: int = 0

        logger.info("RealTimeCostTracker baslatildi")

    def record(
        self,
        session_id: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        provider: str = "",
        tool_name: str = "",
        task_type: str = "",
        template_id: str = "",
    ) -> CostEntry:
        """Maliyet kaydı oluştur.

        Args:
            session_id: Oturum ID.
            model_name: Model adı.
            input_tokens: Girdi token sayısı.
            output_tokens: Çıktı token sayısı.
            provider: Sağlayıcı adı.
            tool_name: Araç adı.
            task_type: Görev tipi.
            template_id: Şablon ID.

        Returns:
            Maliyet kaydı.
        """
        total_tokens = input_tokens + output_tokens
        cost = self._calculate_cost(model_name, input_tokens, output_tokens)

        entry = CostEntry(
            session_id=session_id,
            model_name=model_name,
            provider=provider,
            tool_name=tool_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            task_type=task_type,
            template_id=template_id,
        )

        if len(self._entries) < _MAX_ENTRIES:
            self._entries.append(entry)

        # Session toplamları
        if session_id not in self._session_totals:
            self._session_totals[session_id] = {"cost": 0.0, "tokens": 0, "requests": 0}
        self._session_totals[session_id]["cost"] += cost
        self._session_totals[session_id]["tokens"] += total_tokens
        self._session_totals[session_id]["requests"] += 1

        # Model toplamları
        if model_name not in self._model_totals:
            self._model_totals[model_name] = {"cost": 0.0, "tokens": 0, "requests": 0}
        self._model_totals[model_name]["cost"] += cost
        self._model_totals[model_name]["tokens"] += total_tokens
        self._model_totals[model_name]["requests"] += 1

        # Tool toplamları
        if tool_name:
            if tool_name not in self._tool_totals:
                self._tool_totals[tool_name] = {"cost": 0.0, "tokens": 0, "requests": 0}
            self._tool_totals[tool_name]["cost"] += cost
            self._tool_totals[tool_name]["tokens"] += total_tokens
            self._tool_totals[tool_name]["requests"] += 1

        self._total_cost += cost
        self._total_tokens += total_tokens

        logger.debug(
            "Maliyet kaydedildi: %s/%s $%.6f (%d token)",
            session_id[:8],
            model_name,
            cost,
            total_tokens,
        )
        return entry

    def _calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Maliyet hesapla.

        Args:
            model_name: Model adı.
            input_tokens: Girdi token.
            output_tokens: Çıktı token.

        Returns:
            USD maliyet.
        """
        pricing = _MODEL_PRICING.get(model_name)
        if not pricing:
            # Bilinmeyen model için varsayılan
            pricing = {"input": 0.003, "output": 0.015}

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return round(input_cost + output_cost, 8)

    def get_session_cost(self, session_id: str) -> dict[str, float]:
        """Session maliyetini getir.

        Args:
            session_id: Oturum ID.

        Returns:
            Maliyet bilgisi.
        """
        return self._session_totals.get(
            session_id,
            {"cost": 0.0, "tokens": 0, "requests": 0},
        )

    def get_model_cost(self, model_name: str) -> dict[str, float]:
        """Model maliyetini getir.

        Args:
            model_name: Model adı.

        Returns:
            Maliyet bilgisi.
        """
        return self._model_totals.get(
            model_name,
            {"cost": 0.0, "tokens": 0, "requests": 0},
        )

    def get_total_cost(self) -> float:
        """Toplam maliyeti döndür.

        Returns:
            Toplam USD maliyet.
        """
        return round(self._total_cost, 6)

    def get_recent_entries(self, limit: int = 50) -> list[CostEntry]:
        """Son kayıtları getir.

        Args:
            limit: Kayıt limiti.

        Returns:
            Son maliyet kayıtları.
        """
        return self._entries[-limit:]

    def get_entries_by_session(self, session_id: str) -> list[CostEntry]:
        """Session kayıtlarını getir.

        Args:
            session_id: Oturum ID.

        Returns:
            Session maliyet kayıtları.
        """
        return [e for e in self._entries if e.session_id == session_id]

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_cost_usd": round(self._total_cost, 6),
            "total_tokens": self._total_tokens,
            "total_entries": len(self._entries),
            "total_sessions": len(self._session_totals),
            "by_model": dict(self._model_totals),
            "by_tool": dict(self._tool_totals),
        }
