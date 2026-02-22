"""Baglam koruyucu.

Model cagrilarindan once baglam boyutunu kontrol eder,
arac ciktilarini kirpar ve eski mesajlari sikistirir.
"""

import logging
import time
from typing import Any, Optional

from app.models.subagent_models import CompactionResult, SubagentConfig

logger = logging.getLogger(__name__)


class ContextGuard:
    """Baglam koruyucu.

    Model cagrilarindan once baglam boyutunu kontrol eder,
    gerektiginde arac ciktilarini kirpar ve mesajlari sikistirir.
    """

    def __init__(self, config: Optional[SubagentConfig] = None) -> None:
        """ContextGuard baslatici."""
        self.config = config or SubagentConfig()
        self._history: list[dict[str, Any]] = []
        logger.info("ContextGuard baslatildi")

    def _record_history(self, action: str, details: dict[str, Any]) -> None:
        """Gecmis kaydina islem ekler."""
        self._history.append({"action": action, "details": details, "timestamp": time.time()})

    def check_context(self, messages: list[dict[str, Any]], max_chars: int = 0) -> CompactionResult:
        """Baglam boyutunu kontrol eder ve gerekirse sikistirir."""
        if max_chars <= 0:
            max_chars = self.config.max_tool_output_chars
        original_chars = self._estimate_chars(messages)
        truncated_outputs = 0
        messages_compacted = 0
        for msg in messages:
            if msg.get("role") == "tool" and isinstance(msg.get("content"), str):
                content = msg["content"]
                if len(content) > max_chars:
                    msg["content"] = self.truncate_tool_output(content, max_chars)
                    truncated_outputs += 1
        compacted_chars = self._estimate_chars(messages)
        total_limit = max_chars * 3
        if compacted_chars > total_limit:
            messages_list = self.compact_old_messages(messages, total_limit)
            messages.clear()
            messages.extend(messages_list)
            messages_compacted = len(messages_list)
            compacted_chars = self._estimate_chars(messages)
        result = CompactionResult(
            original_chars=original_chars, compacted_chars=compacted_chars,
            messages_compacted=messages_compacted, truncated_outputs=truncated_outputs,
        )
        self._record_history("check_context", {"original_chars": original_chars, "compacted_chars": compacted_chars, "truncated": truncated_outputs})
        if truncated_outputs > 0 or messages_compacted > 0:
            logger.info(f"Baglam sikistirildi: {original_chars} -> {compacted_chars} karakter")
        return result

    def truncate_tool_output(self, output: str, max_chars: int = 0) -> str:
        """Arac ciktisini belirtilen limite kirpar."""
        if max_chars <= 0:
            max_chars = self.config.max_tool_output_chars
        if len(output) <= max_chars:
            return output
        head_size = max_chars * 2 // 3
        tail_size = max_chars - head_size - 50
        truncated_count = len(output) - head_size - tail_size
        truncated = (
            output[:head_size]
            + f"\n\n... [{truncated_count} karakter kirpildi] ...\n\n"
            + output[-tail_size:]
        )
        self._record_history("truncate", {"original_len": len(output), "truncated_len": len(truncated)})
        return truncated

    def compact_old_messages(self, messages: list[dict[str, Any]], target_chars: int) -> list[dict[str, Any]]:
        """Eski arac sonuclarini sikistirarak mesaj listesini kucultir."""
        if not messages:
            return messages
        current_chars = self._estimate_chars(messages)
        if current_chars <= target_chars:
            return messages
        result: list[dict[str, Any]] = []
        compacted = 0
        preserve_count = min(5, len(messages))
        old_messages = messages[:-preserve_count] if preserve_count < len(messages) else []
        recent_messages = messages[-preserve_count:]
        for msg in old_messages:
            if msg.get("role") == "tool" and isinstance(msg.get("content"), str):
                content = msg["content"]
                if len(content) > 200:
                    msg = dict(msg)
                    msg["content"] = content[:100] + f"... [{len(content) - 100} karakter kirpildi]"
                    compacted += 1
            result.append(msg)
        result.extend(recent_messages)
        self._record_history("compact", {"original_count": len(messages), "compacted": compacted})
        return result

    def _estimate_chars(self, messages: list[dict[str, Any]]) -> int:
        """Mesaj listesinin toplam karakter sayisini tahmin eder."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        total += len(str(item.get("text", "")))
                    elif isinstance(item, str):
                        total += len(item)
            total += len(str(msg.get("role", "")))
        return total

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Gecmis kayitlarini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        truncations = [h for h in self._history if h["action"] == "truncate"]
        compactions = [h for h in self._history if h["action"] == "compact"]
        checks = [h for h in self._history if h["action"] == "check_context"]
        total_saved = sum(h["details"].get("original_chars", 0) - h["details"].get("compacted_chars", 0) for h in checks)
        return {
            "total_checks": len(checks),
            "total_truncations": len(truncations),
            "total_compactions": len(compactions),
            "total_chars_saved": total_saved,
            "max_tool_output_chars": self.config.max_tool_output_chars,
            "history_size": len(self._history),
        }
