"""Yanit is parcacigi yoneticisi.

Kanal bazli yanit zincirlemesi, yapismali thread yonetimi ve
bayat thread temizligi saglar.
"""

import logging
import time
from typing import Any, Optional

from app.models.replythreading_models import ThreadContext

logger = logging.getLogger(__name__)


class ThreadManager:
    """Yanit is parcacigi yoneticisi.

    Kanal bazli yanit zincirlemesi, yapismali thread yonetimi
    ve bayat thread temizligi saglar.
    """

    def __init__(self) -> None:
        """ThreadManager baslatici."""
        self._threads: dict[str, ThreadContext] = {}
        self._active_by_channel: dict[str, str] = {}
        self._history: list[dict[str, Any]] = []
        logger.info("ThreadManager baslatildi")

    def _record_history(self, action: str, **kwargs: Any) -> None:
        """Gecmis kaydina olay ekler."""
        entry = {"action": action, "timestamp": time.time(), **kwargs}
        self._history.append(entry)
        if len(self._history) > 1000:
            self._history = self._history[-500:]

    def create_thread(
        self,
        channel: str,
        reply_to_id: str,
        original_msg_id: str,
        stale_threshold: int = 300,
    ) -> ThreadContext:
        """Yeni yanit is parcacigi olusturur.

        Args:
            channel: Kanal adi.
            reply_to_id: Yanitlanacak mesaj ID.
            original_msg_id: Orijinal mesaj ID.
            stale_threshold: Bayatlama esigi (saniye).

        Returns:
            Olusturulan ThreadContext.
        """
        now = time.time()
        ctx = ThreadContext(
            channel=channel,
            reply_to_id=reply_to_id,
            original_message_id=original_msg_id,
            created_at=now,
            last_used_at=now,
            stale_threshold_seconds=stale_threshold,
        )
        self._threads[ctx.thread_id] = ctx
        self._active_by_channel[channel] = ctx.thread_id
        self._record_history("create_thread", thread_id=ctx.thread_id, channel=channel)
        logger.info(f"Thread olusturuldu: {ctx.thread_id} (kanal={channel})")
        return ctx

    def get_thread(self, thread_id: str) -> Optional[ThreadContext]:
        """Thread bilgilerini dondurur."""
        return self._threads.get(thread_id)

    def get_active_thread(self, channel: str) -> Optional[ThreadContext]:
        """Kanaldaki aktif thread i dondurur."""
        tid = self._active_by_channel.get(channel)
        if tid:
            ctx = self._threads.get(tid)
            if ctx and not self.is_stale(tid):
                return ctx
            # Bayat ise temizle
            if tid in self._active_by_channel:
                del self._active_by_channel[channel]
        return None

    def add_chunk(self, thread_id: str, chunk_id: str) -> bool:
        """Thread e parca ekler.

        Args:
            thread_id: Thread kimlik numarasi.
            chunk_id: Eklenen parca ID.

        Returns:
            Ekleme basarili ise True.
        """
        ctx = self._threads.get(thread_id)
        if not ctx:
            return False
        ctx.chunk_ids.append(chunk_id)
        ctx.last_used_at = time.time()
        self._record_history("add_chunk", thread_id=thread_id, chunk_id=chunk_id)
        return True

    def is_stale(self, thread_id: str) -> bool:
        """Thread in bayat olup olmadigini kontrol eder."""
        ctx = self._threads.get(thread_id)
        if not ctx:
            return True
        elapsed = time.time() - ctx.last_used_at
        return elapsed > ctx.stale_threshold_seconds

    def cleanup_stale(self) -> int:
        """Bayat thread leri temizler.

        Returns:
            Temizlenen thread sayisi.
        """
        stale_ids: list[str] = []
        for tid in list(self._threads.keys()):
            if self.is_stale(tid):
                stale_ids.append(tid)
        for tid in stale_ids:
            ctx = self._threads.pop(tid, None)
            if ctx and self._active_by_channel.get(ctx.channel) == tid:
                del self._active_by_channel[ctx.channel]
        if stale_ids:
            self._record_history("cleanup_stale", count=len(stale_ids))
            logger.info(f"{len(stale_ids)} bayat thread temizlendi")
        return len(stale_ids)

    def preserve_reply_context(self, thread_id: str, new_chunk_id: str) -> str:
        """Yanit baglamini korur ve kullanilacak reply_to_id dondurur.

        Args:
            thread_id: Thread kimlik numarasi.
            new_chunk_id: Yeni parca ID.

        Returns:
            Kullanilacak reply_to_id.
        """
        ctx = self._threads.get(thread_id)
        if not ctx:
            return ""

        # Yapismali modda son parcaya yanit ver
        if ctx.is_sticky and ctx.chunk_ids:
            reply_to = ctx.chunk_ids[-1]
        else:
            reply_to = ctx.reply_to_id

        self.add_chunk(thread_id, new_chunk_id)
        self._record_history(
            "preserve_reply_context",
            thread_id=thread_id,
            reply_to=reply_to,
            new_chunk=new_chunk_id,
        )
        return reply_to

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Islem gecmisini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        stale_count = sum(1 for tid in self._threads if self.is_stale(tid))
        return {
            "total_threads": len(self._threads),
            "active_channels": len(self._active_by_channel),
            "stale_threads": stale_count,
            "history_size": len(self._history),
        }
