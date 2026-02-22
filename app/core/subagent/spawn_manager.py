"""Sub-agent spawn yoneticisi.

Ic ice sub-agent olusturma, derinlik limiti kontrolu,
ebeveyn-cocuk iliskisi takibi ve yasam dongusu yonetimi saglar.
"""

import logging
import time
from typing import Any, Optional

from app.models.subagent_models import (
    SubagentConfig,
    SubagentInstance,
    SubagentStatus,
    ToolPolicy,
)

logger = logging.getLogger(__name__)


class SubagentSpawnManager:
    """Sub-agent spawn yoneticisi.

    Ic ice agent olusturma, derinlik kontrolu ve
    ebeveyn-cocuk iliskisi yonetimini saglar.
    """

    def __init__(self, config: Optional[SubagentConfig] = None) -> None:
        """SubagentSpawnManager baslatici."""
        self.config = config or SubagentConfig()
        self._agents: dict[str, SubagentInstance] = {}
        self._history: list[dict[str, Any]] = []
        logger.info("SubagentSpawnManager baslatildi")

    def _record_history(self, action: str, details: dict[str, Any]) -> None:
        """Gecmis kaydina islem ekler."""
        self._history.append({"action": action, "details": details, "timestamp": time.time()})

    def spawn(self, parent_id: str, name: str, model: str = "", context: Optional[dict[str, Any]] = None) -> SubagentInstance:
        """Yeni sub-agent olusturur.

        Args:
            parent_id: Ebeveyn agent ID (kok icin bos string).
            name: Sub-agent adi.
            model: Kullanilacak model adi.
            context: Baslangic baglam verisi.

        Returns:
            Olusturulan SubagentInstance.

        Raises:
            ValueError: Derinlik veya cocuk limiti asildiginda.
        """
        depth = self.get_depth(parent_id) + 1 if parent_id else 0
        self._check_spawn_limits(parent_id, depth)
        tool_policy = self.config.tool_policy_by_depth.get(depth, ToolPolicy.NONE)
        instance = SubagentInstance(
            parent_id=parent_id, name=name, depth=depth,
            status=SubagentStatus.RUNNING, model=model,
            tool_policy=tool_policy, context=context or {},
            created_at=time.time(),
        )
        self._agents[instance.agent_id] = instance
        if parent_id and parent_id in self._agents:
            self._agents[parent_id].children.append(instance.agent_id)
        self._record_history("spawn", {
            "agent_id": instance.agent_id, "parent_id": parent_id,
            "name": name, "depth": depth, "tool_policy": tool_policy.value,
        })
        logger.info(f"Sub-agent olusturuldu: {instance.agent_id} (ad={name}, derinlik={depth})")
        return instance

    def get_agent(self, agent_id: str) -> Optional[SubagentInstance]:
        """Agent bilgisini dondurur."""
        return self._agents.get(agent_id)

    def list_children(self, parent_id: str) -> list[SubagentInstance]:
        """Ebeveynin cocuk agent listesini dondurur."""
        return [a for a in self._agents.values() if a.parent_id == parent_id]

    def complete_agent(self, agent_id: str, result: dict[str, Any]) -> bool:
        """Agent gorevini basariyla tamamlar."""
        agent = self._agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent bulunamadi: {agent_id}")
            return False
        if agent.status != SubagentStatus.RUNNING:
            logger.warning(f"Agent calismiyor: {agent_id}")
            return False
        agent.status = SubagentStatus.COMPLETED
        agent.result = result
        agent.completed_at = time.time()
        self._record_history("complete", {"agent_id": agent_id, "duration": agent.completed_at - agent.created_at})
        logger.info(f"Sub-agent tamamlandi: {agent_id}")
        return True

    def fail_agent(self, agent_id: str, error: str) -> bool:
        """Agent gorevini basarisiz olarak isaretler."""
        agent = self._agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent bulunamadi: {agent_id}")
            return False
        if agent.status not in (SubagentStatus.RUNNING, SubagentStatus.PENDING):
            logger.warning(f"Agent aktif degil: {agent_id}")
            return False
        agent.status = SubagentStatus.FAILED
        agent.error = error
        agent.completed_at = time.time()
        self._record_history("fail", {"agent_id": agent_id, "error": error})
        logger.warning(f"Sub-agent basarisiz: {agent_id} - {error}")
        return True

    def cancel_agent(self, agent_id: str) -> bool:
        """Agent gorevini iptal eder."""
        agent = self._agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent bulunamadi: {agent_id}")
            return False
        if agent.status in (SubagentStatus.COMPLETED, SubagentStatus.FAILED, SubagentStatus.CANCELLED):
            logger.warning(f"Agent zaten sonlanmis: {agent_id}")
            return False
        agent.status = SubagentStatus.CANCELLED
        agent.completed_at = time.time()
        for child_id in agent.children:
            self.cancel_agent(child_id)
        self._record_history("cancel", {"agent_id": agent_id})
        logger.info(f"Sub-agent iptal edildi: {agent_id}")
        return True

    def get_depth(self, agent_id: str) -> int:
        """Agentin derinligini hesaplar."""
        if not agent_id:
            return -1
        agent = self._agents.get(agent_id)
        if not agent:
            return -1
        return agent.depth

    def _check_spawn_limits(self, parent_id: str, depth: int) -> None:
        """Spawn limitlerini kontrol eder."""
        if depth > self.config.max_spawn_depth:
            raise ValueError(f"Maksimum derinlik asildi: {depth} > {self.config.max_spawn_depth}")
        if parent_id:
            children = self.list_children(parent_id)
            active = [c for c in children if c.status in (SubagentStatus.PENDING, SubagentStatus.RUNNING)]
            if len(active) >= self.config.max_children_per_agent:
                raise ValueError(f"Maksimum cocuk sayisi asildi: {len(active)} >= {self.config.max_children_per_agent}")

    def get_ancestor_chain(self, agent_id: str) -> list[str]:
        """Agent icin ebeveyn zincirini dondurur."""
        chain: list[str] = []
        current_id = agent_id
        visited: set[str] = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            agent = self._agents.get(current_id)
            if not agent:
                break
            chain.append(current_id)
            current_id = agent.parent_id
        chain.reverse()
        return chain

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Gecmis kayitlarini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        status_counts: dict[str, int] = {}
        depth_counts: dict[int, int] = {}
        total_duration = 0.0
        completed_count = 0
        for agent in self._agents.values():
            sk = agent.status.value
            status_counts[sk] = status_counts.get(sk, 0) + 1
            depth_counts[agent.depth] = depth_counts.get(agent.depth, 0) + 1
            if agent.status == SubagentStatus.COMPLETED and agent.completed_at > 0:
                total_duration += agent.completed_at - agent.created_at
                completed_count += 1
        return {
            "total_agents": len(self._agents),
            "status_counts": status_counts,
            "depth_counts": depth_counts,
            "avg_duration": total_duration / completed_count if completed_count > 0 else 0.0,
            "max_spawn_depth": self.config.max_spawn_depth,
            "max_children_per_agent": self.config.max_children_per_agent,
            "history_size": len(self._history),
        }
