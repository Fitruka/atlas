"""Dongu tespitcisi.

Agent cagrilarinda tekrarlayan kaliplari (ayni cagri, ping-pong, devre kesici)
tespit eder ve uyari veya engelleme seviyesi dondurur.
"""

import logging
import time
from typing import Any, Optional

from app.models.agentruntime_models import (
    LoopDetectionLevel,
    LoopDetectionResult,
    LoopType,
    RuntimeConfig,
)

logger = logging.getLogger(__name__)


class LoopDetector:
    """Agent dongu tespitcisi.

    Ayni arac cagrilarini, ping-pong kaliplarini ve devre kesici
    durumlarini tespit ederek uyari veya engelleme sonucu dondurur.
    """

    def __init__(self, config: Optional[RuntimeConfig] = None) -> None:
        """LoopDetector baslatici.

        Args:
            config: Calisma zamani yapilandirmasi.
        """
        self._config = config or RuntimeConfig()
        self._calls: list[dict[str, Any]] = []
        self._no_progress_count: int = 0
        self._history: list[dict[str, Any]] = []
        logger.info("LoopDetector baslatildi")

    def _record_history(self, action: str, **kwargs: Any) -> None:
        """Gecmis kaydina olay ekler."""
        entry = {"action": action, "timestamp": time.time(), **kwargs}
        self._history.append(entry)
        if len(self._history) > 1000:
            self._history = self._history[-500:]

    def check_call(self, tool_name: str, args: Optional[dict[str, Any]] = None) -> LoopDetectionResult:
        """Arac cagrisini dongu acisindan kontrol eder.

        Args:
            tool_name: Arac adi.
            args: Arac argumanlari.

        Returns:
            LoopDetectionResult sonucu.
        """
        call_entry = {"tool": tool_name, "args": args or {}, "ts": time.time()}
        self._calls.append(call_entry)

        # Ayni cagri tespiti
        result = self._detect_identical(self._calls)
        if result.detected:
            self._record_history("loop_detected", loop_type=result.loop_type.value,
                               repeat_count=result.repeat_count)
            return result

        # Ping-pong tespiti
        result = self._detect_ping_pong(self._calls)
        if result.detected:
            self._record_history("loop_detected", loop_type=result.loop_type.value,
                               repeat_count=result.repeat_count)
            return result

        # Devre kesici kontrolu
        result = self._circuit_breaker_check(self._no_progress_count)
        if result.detected:
            self._record_history("circuit_breaker", count=self._no_progress_count)
            return result

        self._record_history("check_call", tool_name=tool_name)
        return LoopDetectionResult()

    def _detect_identical(self, calls: list[dict[str, Any]]) -> LoopDetectionResult:
        """Ayni arac cagrilarini tespit eder."""
        if len(calls) < 2:
            return LoopDetectionResult()

        last = calls[-1]
        identical_count = 0
        for c in reversed(calls[:-1]):
            if c["tool"] == last["tool"] and c["args"] == last["args"]:
                identical_count += 1
            else:
                break

        if identical_count >= self._config.identical_call_warn:
            level = LoopDetectionLevel.WARN
            if identical_count >= self._config.circuit_breaker_limit:
                level = LoopDetectionLevel.BLOCK
            return LoopDetectionResult(
                detected=True,
                loop_type=LoopType.IDENTICAL_CALL,
                level=level,
                repeat_count=identical_count,
                message=f"Ayni cagri {identical_count} kez tekrarlandi: {last['tool']}",
            )
        return LoopDetectionResult()

    def _detect_ping_pong(self, calls: list[dict[str, Any]]) -> LoopDetectionResult:
        """Ping-pong kalibini tespit eder."""
        if len(calls) < 4:
            return LoopDetectionResult()

        # Son 4 cagrida A-B-A-B kalibini ara
        tools = [c["tool"] for c in calls[-4:]]
        if tools[0] == tools[2] and tools[1] == tools[3] and tools[0] != tools[1]:
            # Kac kez tekrarlaniyor say
            ping_pong_count = 2
            i = len(calls) - 5
            while i >= 1:
                if calls[i]["tool"] == calls[i+2]["tool"]:
                    ping_pong_count += 1
                    i -= 1
                else:
                    break

            if ping_pong_count >= self._config.ping_pong_block:
                level = LoopDetectionLevel.BLOCK
            elif ping_pong_count >= self._config.ping_pong_warn:
                level = LoopDetectionLevel.WARN
            else:
                return LoopDetectionResult()

            return LoopDetectionResult(
                detected=True,
                loop_type=LoopType.PING_PONG,
                level=level,
                repeat_count=ping_pong_count,
                message=f"Ping-pong kalibi tespiti: {tools[0]} <-> {tools[1]} ({ping_pong_count}x)",
            )
        return LoopDetectionResult()

    def _circuit_breaker_check(self, no_progress_count: int) -> LoopDetectionResult:
        """Devre kesici kontrolu yapar."""
        if no_progress_count >= self._config.circuit_breaker_limit:
            return LoopDetectionResult(
                detected=True,
                loop_type=LoopType.CIRCUIT_BREAKER,
                level=LoopDetectionLevel.BLOCK,
                repeat_count=no_progress_count,
                message=f"Devre kesici aktif: {no_progress_count} cagri ilerleme yok",
            )
        return LoopDetectionResult()

    def reset(self) -> None:
        """Tespitciyi sifirlar."""
        self._calls.clear()
        self._no_progress_count = 0
        self._record_history("reset")
        logger.info("LoopDetector sifirlandi")

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Islem gecmisini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        return {
            "total_calls": len(self._calls),
            "no_progress_count": self._no_progress_count,
            "loops_detected": sum(1 for h in self._history if h["action"] == "loop_detected"),
            "history_size": len(self._history),
        }
