"""Announce mesaj yonlendiricisi.

Sub-agentlar arasi announce mesajlarini yonlendirir,
ebeveyn zincirine mesaj iletir ve suresi dolan mesajlari temizler.
"""

import logging
import time
from typing import Any, Optional

from app.models.subagent_models import AnnounceMessage, SubagentConfig

logger = logging.getLogger(__name__)


class AnnounceRouter:
    """Announce mesaj yonlendiricisi.

    Sub-agentlar arasi mesaj iletimini, yonlendirmeyi
    ve mesaj yasam dongusu yonetimini saglar.
    """

    def __init__(self, config: Optional[SubagentConfig] = None) -> None:
        """AnnounceRouter baslatici."""
        self.config = config or SubagentConfig()
        self._mailboxes: dict[str, list[AnnounceMessage]] = {}
        self._deferred: list[AnnounceMessage] = []
        self._parent_map: dict[str, str] = {}
        self._history: list[dict[str, Any]] = []
        logger.info("AnnounceRouter baslatildi")

    def _record_history(self, action: str, details: dict[str, Any]) -> None:
        """Gecmis kaydina islem ekler."""
        self._history.append({"action": action, "details": details, "timestamp": time.time()})

    def register_agent(self, agent_id: str, parent_id: str = "") -> None:
        """Agenti yonlendiriciye kaydeder."""
        if agent_id not in self._mailboxes:
            self._mailboxes[agent_id] = []
        if parent_id:
            self._parent_map[agent_id] = parent_id
        self._record_history("register", {"agent_id": agent_id, "parent_id": parent_id})

    def send(self, from_id: str, to_id: str, content: str, chain: Optional[list[str]] = None) -> AnnounceMessage:
        """Announce mesaji gonderir."""
        now = time.time()
        message = AnnounceMessage(
            from_agent=from_id, to_agent=to_id, content=content,
            chain=chain or [], created_at=now,
            expires_at=now + self.config.announce_expiry_seconds,
        )
        if to_id not in self._mailboxes:
            self._mailboxes[to_id] = []
        self._mailboxes[to_id].append(message)
        self._record_history("send", {"message_id": message.message_id, "from": from_id, "to": to_id})
        logger.info(f"Announce mesaji gonderildi: {from_id} -> {to_id}")
        return message

    def receive(self, agent_id: str) -> list[AnnounceMessage]:
        """Agentin bekleyen mesajlarini alir."""
        messages = self._mailboxes.get(agent_id, [])
        now = time.time()
        valid_messages = [m for m in messages if m.expires_at > now]
        self._mailboxes[agent_id] = []
        self._record_history("receive", {"agent_id": agent_id, "message_count": len(valid_messages)})
        return valid_messages

    def route_to_parent(self, agent_id: str, content: str) -> bool:
        """Mesaji agentin ebeveynine yonlendirir."""
        parent_id = self._parent_map.get(agent_id)
        if not parent_id:
            logger.warning(f"Ebeveyn bulunamadi: {agent_id}")
            return False
        self.send(agent_id, parent_id, content, chain=[agent_id])
        self._record_history("route_to_parent", {"agent_id": agent_id, "parent_id": parent_id})
        return True

    def defer_until_ready(self, message: AnnounceMessage) -> bool:
        """Mesaji ertelenmis mesajlar listesine ekler."""
        if message.retry_count >= self.config.max_announce_retries:
            logger.warning(f"Maksimum yeniden deneme asildi: {message.message_id}")
            return False
        message.retry_count += 1
        self._deferred.append(message)
        self._record_history("defer", {"message_id": message.message_id, "retry_count": message.retry_count})
        logger.info(f"Mesaj ertelendi: {message.message_id} (deneme={message.retry_count})")
        return True

    def retry_deferred(self) -> int:
        """Ertelenmis mesajlari yeniden gondermeyi dener."""
        retried = 0
        remaining: list[AnnounceMessage] = []
        now = time.time()
        for message in self._deferred:
            if message.expires_at <= now:
                continue
            if message.to_agent in self._mailboxes:
                self._mailboxes[message.to_agent].append(message)
                retried += 1
            else:
                remaining.append(message)
        self._deferred = remaining
        if retried > 0:
            self._record_history("retry_deferred", {"retried": retried})
            logger.info(f"Ertelenmis mesajlar yeniden gonderildi: {retried}")
        return retried

    def expire_old_messages(self) -> int:
        """Suresi dolan mesajlari temizler."""
        now = time.time()
        expired_count = 0
        for agent_id in list(self._mailboxes.keys()):
            messages = self._mailboxes[agent_id]
            valid = [m for m in messages if m.expires_at > now]
            expired_count += len(messages) - len(valid)
            self._mailboxes[agent_id] = valid
        deferred_before = len(self._deferred)
        self._deferred = [m for m in self._deferred if m.expires_at > now]
        expired_count += deferred_before - len(self._deferred)
        if expired_count > 0:
            self._record_history("expire", {"expired_count": expired_count})
            logger.info(f"Suresi dolan mesajlar temizlendi: {expired_count}")
        return expired_count

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Gecmis kayitlarini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        total_pending = sum(len(msgs) for msgs in self._mailboxes.values())
        sends = [h for h in self._history if h["action"] == "send"]
        receives = [h for h in self._history if h["action"] == "receive"]
        return {
            "registered_agents": len(self._mailboxes),
            "total_pending": total_pending,
            "deferred_count": len(self._deferred),
            "total_sent": len(sends),
            "total_received": len(receives),
            "parent_map_size": len(self._parent_map),
            "announce_expiry_seconds": self.config.announce_expiry_seconds,
            "max_announce_retries": self.config.max_announce_retries,
            "history_size": len(self._history),
        }
