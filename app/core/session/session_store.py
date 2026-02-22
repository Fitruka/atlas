"""Session yonetim deposu.

Oturum olusturma, kilitleme, arsivleme ve atomik yazma islemleri.
Windows uyumlu temp+rename atomik yazma destegi saglar.
"""

import logging
import os
import tempfile
import time
from typing import Any, Optional

from app.models.session_models import (
    AtomicWriteResult,
    SessionEntry,
    SessionLockState,
    SessionState,
)

logger = logging.getLogger(__name__)


class SessionStore:
    """Oturum deposu.

    Oturum yaratma, kilitleme, arsivleme ve atomik dosya yazma
    islemlerini yonetir. Windows ortaminda guvenli temp+rename
    stratejisi kullanir.
    """

    def __init__(
        self,
        default_lock_ttl: float = 60.0,
        default_session_ttl: float = 3600.0,
    ) -> None:
        """SessionStore baslatici.

        Args:
            default_lock_ttl: Varsayilan kilit suresi (saniye).
            default_session_ttl: Varsayilan oturum suresi (saniye).
        """
        self._sessions: dict[str, SessionEntry] = {}
        self._default_lock_ttl = default_lock_ttl
        self._default_session_ttl = default_session_ttl
        self._history: list[dict[str, Any]] = []
        logger.info("SessionStore baslatildi")

    def _record_history(self, action: str, **kwargs: Any) -> None:
        """Gecmis kaydina olay ekler."""
        entry = {"action": action, "timestamp": time.time(), **kwargs}
        self._history.append(entry)
        if len(self._history) > 1000:
            self._history = self._history[-500:]

    def create_session(
        self,
        transcript_path: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> SessionEntry:
        """Yeni oturum olusturur.

        Args:
            transcript_path: Transkript dosya yolu.
            metadata: Ek meta veriler.

        Returns:
            Olusturulan SessionEntry.
        """
        now = time.time()
        session = SessionEntry(
            state=SessionState.ACTIVE,
            lock_state=SessionLockState.UNLOCKED,
            transcript_path=transcript_path,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._sessions[session.session_id] = session
        self._record_history("create_session", session_id=session.session_id)
        logger.info(f"Oturum olusturuldu: {session.session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[SessionEntry]:
        """Oturum bilgilerini dondurur."""
        return self._sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        metadata: Optional[dict[str, Any]] = None,
        transcript_path: Optional[str] = None,
    ) -> Optional[SessionEntry]:
        """Oturum bilgilerini gunceller."""
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Oturum bulunamadi: {session_id}")
            return None
        if metadata:
            session.metadata.update(metadata)
        if transcript_path is not None:
            session.transcript_path = transcript_path
        session.updated_at = time.time()
        self._record_history("update_session", session_id=session_id)
        logger.info(f"Oturum guncellendi: {session_id}")
        return session

    def delete_session(self, session_id: str) -> bool:
        """Oturumu siler."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._record_history("delete_session", session_id=session_id)
            logger.info(f"Oturum silindi: {session_id}")
            return True
        logger.warning(f"Silinecek oturum bulunamadi: {session_id}")
        return False

    def lock_session(
        self,
        session_id: str,
        holder: str,
        ttl: Optional[float] = None,
    ) -> bool:
        """Oturumu kilitler."""
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Kilitlenecek oturum bulunamadi: {session_id}")
            return False
        if session.lock_state == SessionLockState.LOCKED:
            now = time.time()
            if session.lock_expires_at > now:
                logger.warning(
                    f"Oturum zaten kilitli: {session_id} "
                    f"(holder={session.lock_holder})"
                )
                return False
            logger.info(f"Suresi dolmus kilit yeniden aliniyor: {session_id}")
        lock_ttl = ttl if ttl is not None else self._default_lock_ttl
        now = time.time()
        session.lock_state = SessionLockState.LOCKED
        session.lock_holder = holder
        session.lock_expires_at = now + lock_ttl
        session.state = SessionState.LOCKED
        session.updated_at = now
        self._record_history(
            "lock_session", session_id=session_id, holder=holder, ttl=lock_ttl
        )
        logger.info(f"Oturum kilitlendi: {session_id} (holder={holder})")
        return True

    def unlock_session(self, session_id: str, holder: str = "") -> bool:
        """Oturum kilidini acar."""
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Kilidi acilacak oturum bulunamadi: {session_id}")
            return False
        if session.lock_state != SessionLockState.LOCKED:
            return True
        if holder and session.lock_holder != holder:
            logger.warning(
                f"Kilit sahibi uyusmadi: {session_id} "
                f"(beklenen={session.lock_holder}, gelen={holder})"
            )
            return False
        session.lock_state = SessionLockState.UNLOCKED
        session.lock_holder = ""
        session.lock_expires_at = 0.0
        session.state = SessionState.ACTIVE
        session.updated_at = time.time()
        self._record_history("unlock_session", session_id=session_id)
        logger.info(f"Oturum kilidi acildi: {session_id}")
        return True

    def archive_session(self, session_id: str) -> Optional[SessionEntry]:
        """Oturumu arsivler."""
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Arsivlenecek oturum bulunamadi: {session_id}")
            return None
        now = time.time()
        session.state = SessionState.ARCHIVED
        session.lock_state = SessionLockState.UNLOCKED
        session.lock_holder = ""
        session.lock_expires_at = 0.0
        session.archived_at = now
        session.updated_at = now
        self._record_history("archive_session", session_id=session_id)
        logger.info(f"Oturum arsivlendi: {session_id}")
        return session

    def atomic_write(self, path: str, data: bytes) -> AtomicWriteResult:
        """Windows uyumlu atomik dosya yazma."""
        result = AtomicWriteResult(path=path)
        tmp_path = ""
        try:
            target_dir = os.path.dirname(path) or "."
            os.makedirs(target_dir, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(
                dir=target_dir, prefix=".atlas_tmp_", suffix=".tmp"
            )
            try:
                os.write(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.replace(tmp_path, path)
            result.success = True
            result.bytes_written = len(data)
            result.is_atomic = True
            self._record_history("atomic_write", path=path, bytes_count=len(data))
            logger.info(f"Atomik yazma basarili: {path} ({len(data)} byte)")
        except Exception as e:
            result.error = str(e)
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except OSError:
                pass
            logger.error(f"Atomik yazma hatasi: {path} - {e}")
        return result

    def lock_watchdog_check(self) -> list[str]:
        """Suresi dolmus kilitleri kontrol eder ve temizler."""
        expired: list[str] = []
        now = time.time()
        for sid, session in self._sessions.items():
            if (
                session.lock_state == SessionLockState.LOCKED
                and session.lock_expires_at > 0
                and session.lock_expires_at <= now
            ):
                session.lock_state = SessionLockState.WATCHDOG_EXPIRED
                session.state = SessionState.ACTIVE
                session.updated_at = now
                expired.append(sid)
                logger.warning(f"Kilit suresi doldu (watchdog): {sid}")
        if expired:
            self._record_history(
                "lock_watchdog_check", expired_count=len(expired), ids=expired
            )
        return expired

    def list_sessions(
        self,
        state: Optional[SessionState] = None,
        limit: int = 100,
    ) -> list[SessionEntry]:
        """Oturumlari listeler."""
        sessions = list(self._sessions.values())
        if state:
            sessions = [s for s in sessions if s.state == state]
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions[:limit]

    def prune_expired(self, ttl: Optional[float] = None) -> int:
        """Suresi dolmus oturumlari temizler."""
        session_ttl = ttl if ttl is not None else self._default_session_ttl
        now = time.time()
        to_remove: list[str] = []
        for sid, session in self._sessions.items():
            if session.state == SessionState.ARCHIVED:
                continue
            age = now - session.created_at
            if age > session_ttl:
                to_remove.append(sid)
        for sid in to_remove:
            self._sessions[sid].state = SessionState.EXPIRED
            del self._sessions[sid]
        if to_remove:
            self._record_history("prune_expired", count=len(to_remove))
            logger.info(f"Suresi dolmus {len(to_remove)} oturum temizlendi")
        return len(to_remove)

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Islem gecmisini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Depo istatistiklerini dondurur."""
        states: dict[str, int] = {}
        locked_count = 0
        for session in self._sessions.values():
            states[session.state.value] = states.get(session.state.value, 0) + 1
            if session.lock_state == SessionLockState.LOCKED:
                locked_count += 1
        return {
            "total_sessions": len(self._sessions),
            "states": states,
            "locked_count": locked_count,
            "history_size": len(self._history),
        }
