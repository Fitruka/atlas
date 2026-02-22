"""Derinlik bazli arac politikasi kontrolcusu.

Sub-agent derinligine gore hangi araclarin kullanilabilecegini
belirler ve politika yonetimi saglar.
"""

import logging
import time
from typing import Any, Optional

from app.models.subagent_models import SubagentConfig, ToolPolicy

logger = logging.getLogger(__name__)


class DepthController:
    """Derinlik bazli arac politikasi kontrolcusu.

    Sub-agent derinligine gore arac erisim politikasini
    yonetir ve uygular.
    """

    _restricted_tools: list[str] = ["write", "delete", "exec", "deploy"]
    _read_only_tools: list[str] = ["read", "search", "list", "get"]

    def __init__(self, config: Optional[SubagentConfig] = None) -> None:
        """DepthController baslatici."""
        self.config = config or SubagentConfig()
        self._custom_policies: dict[int, ToolPolicy] = {}
        self._history: list[dict[str, Any]] = []
        logger.info("DepthController baslatildi")

    def _record_history(self, action: str, details: dict[str, Any]) -> None:
        """Gecmis kaydina islem ekler."""
        self._history.append({"action": action, "details": details, "timestamp": time.time()})

    def get_tool_policy(self, depth: int) -> ToolPolicy:
        """Belirtilen derinlik icin arac politikasini dondurur."""
        if depth in self._custom_policies:
            policy = self._custom_policies[depth]
        else:
            policy = self.config.tool_policy_by_depth.get(depth, ToolPolicy.NONE)
        self._record_history("get_policy", {"depth": depth, "policy": policy.value})
        return policy

    def is_tool_allowed(self, depth: int, tool_name: str) -> bool:
        """Belirtilen derinlikte araca izin verilip verilmedigini kontrol eder."""
        policy = self.get_tool_policy(depth)
        tool_lower = tool_name.lower()
        if policy == ToolPolicy.FULL:
            allowed = True
        elif policy == ToolPolicy.RESTRICTED:
            allowed = tool_lower not in self._restricted_tools
        elif policy == ToolPolicy.READ_ONLY:
            allowed = any(ro in tool_lower for ro in self._read_only_tools)
        else:
            allowed = False
        self._record_history("check_tool", {"depth": depth, "tool_name": tool_name, "allowed": allowed})
        if not allowed:
            logger.warning(f"Arac engellendi: {tool_name} (derinlik={depth})")
        return allowed

    def get_max_depth(self) -> int:
        """Maksimum derinlik limitini dondurur."""
        return self.config.max_spawn_depth

    def set_policy(self, depth: int, policy: ToolPolicy) -> None:
        """Belirtilen derinlik icin ozel politika ayarlar."""
        self._custom_policies[depth] = policy
        self._record_history("set_policy", {"depth": depth, "policy": policy.value})
        logger.info(f"Politika ayarlandi: derinlik={depth}, politika={policy.value}")

    def get_allowed_tools(self, depth: int) -> list[str]:
        """Izin verilen arac kategorilerini dondurur."""
        policy = self.get_tool_policy(depth)
        if policy == ToolPolicy.FULL:
            return ["all"]
        elif policy == ToolPolicy.RESTRICTED:
            return list(self._read_only_tools)
        elif policy == ToolPolicy.READ_ONLY:
            return list(self._read_only_tools)
        return []

    def get_blocked_tools(self, depth: int) -> list[str]:
        """Engellenen arac kategorilerini dondurur."""
        policy = self.get_tool_policy(depth)
        if policy == ToolPolicy.FULL:
            return []
        elif policy == ToolPolicy.RESTRICTED:
            return list(self._restricted_tools)
        elif policy == ToolPolicy.READ_ONLY:
            return list(self._restricted_tools) + ["update", "create", "modify"]
        return ["all"]

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Gecmis kayitlarini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        checks = [h for h in self._history if h["action"] == "check_tool"]
        allowed_count = sum(1 for h in checks if h["details"].get("allowed", False))
        return {
            "max_depth": self.config.max_spawn_depth,
            "custom_policies": len(self._custom_policies),
            "total_checks": len(checks),
            "allowed_count": allowed_count,
            "blocked_count": len(checks) - allowed_count,
            "restricted_tools": list(self._restricted_tools),
            "read_only_tools": list(self._read_only_tools),
            "history_size": len(self._history),
        }
