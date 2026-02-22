"""Guvenli komut yurutme motoru.

Komut dogrulama, guvenli ikili cozumleme, ortam degiskeni enjeksiyon
tespiti ve onay mekanizmasi saglar.
"""

import hashlib
import logging
import os
import re
import shlex
import shutil
import subprocess
import time
from typing import Any, Optional

from app.models.execengine_models import (
    EnvInjectionResult,
    ExecMode,
    ExecResult,
    SafeBinConfig,
)

logger = logging.getLogger(__name__)


class SafeExecutor:
    """Guvenli komut yurutme motoru."""

    def __init__(self, config: Optional[SafeBinConfig] = None, default_timeout: float = 30.0) -> None:
        """SafeExecutor baslatici."""
        self._config = config or SafeBinConfig()
        self._default_timeout = default_timeout
        self._history: list[dict[str, Any]] = []
        self._approved_hashes: set[str] = set()
        logger.info("SafeExecutor baslatildi")

    def _record_history(self, action: str, **kwargs: Any) -> None:
        """Gecmis kaydina olay ekler."""
        entry = {"action": action, "timestamp": time.time(), **kwargs}
        self._history.append(entry)
        if len(self._history) > 1000:
            self._history = self._history[-500:]

    def execute(self, command: str, mode: ExecMode = ExecMode.SAFE, env: Optional[dict[str, str]] = None, timeout: Optional[float] = None) -> ExecResult:
        """Komutu yurutur."""
        result = ExecResult(command=command, mode=mode)
        exec_timeout = timeout or self._default_timeout
        start = time.time()
        if mode == ExecMode.SAFE:
            blocked = self.check_blocked_flags(command)
            if blocked:
                result.exit_code = -1
                result.stderr = blocked
                self._record_history("execute_blocked", command=command, reason=blocked)
                return result
            injection = self.detect_env_injection(command)
            if injection.detected:
                result.exit_code = -2
                result.stderr = f"Enjeksiyon tespiti: {injection.pattern}"
                self._record_history("execute_injection", command=command)
                return result
        if mode == ExecMode.ASK:
            cmd_hash = hashlib.sha256(command.encode()).hexdigest()[:16]
            if cmd_hash not in self._approved_hashes:
                result.exit_code = -3
                result.stderr = "Onay gerekiyor"
                result.was_approved = False
                self._record_history("execute_needs_approval", command=command)
                return result
            result.was_approved = True
        try:
            proc_env = os.environ.copy()
            if env:
                proc_env.update(env)
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=proc_env)
            try:
                stdout, stderr = proc.communicate(timeout=exec_timeout)
                result.exit_code = proc.returncode
                result.stdout = stdout.decode("utf-8", errors="replace")
                result.stderr = stderr.decode("utf-8", errors="replace")
            except subprocess.TimeoutExpired:
                self._sigterm_before_sigkill(proc.pid, timeout=5.0)
                result.exit_code = -4
                result.stderr = f"Zaman asimi: {exec_timeout}s"
        except Exception as e:
            result.exit_code = -5
            result.stderr = str(e)
            logger.error(f"Komut yurutme hatasi: {e}")
        result.duration_ms = (time.time() - start) * 1000
        self._record_history("execute", command=command, mode=mode.value, exit_code=result.exit_code, duration_ms=result.duration_ms)
        return result

    def resolve_safe_bin(self, name: str) -> Optional[str]:
        """Guvenli ikili dosya yolunu cozumler."""
        if os.path.sep in name:
            abs_path = os.path.abspath(name)
            for trusted in self._config.trusted_dirs:
                if abs_path.startswith(os.path.abspath(trusted)):
                    if os.path.isfile(abs_path) and os.access(abs_path, os.X_OK):
                        return abs_path
            logger.warning(f"Guvenilir olmayan yol: {name}")
            return None
        resolved = shutil.which(name)
        if resolved:
            abs_resolved = os.path.abspath(resolved)
            for trusted in self._config.trusted_dirs:
                if abs_resolved.startswith(os.path.abspath(trusted)):
                    return abs_resolved
            if os.name == "nt":
                return abs_resolved
        logger.warning(f"Ikili bulunamadi veya guvenli degil: {name}")
        return None

    def check_blocked_flags(self, command: str) -> Optional[str]:
        """Engellenen bayraklari kontrol eder."""
        try:
            parts = shlex.split(command)
        except ValueError:
            return "Komut ayristirilamadi"
        if not parts:
            return None
        bin_name = os.path.basename(parts[0])
        blocked = self._config.blocked_flags.get(bin_name, [])
        for flag in blocked:
            if flag in parts[1:]:
                msg = f"Engellenen bayrak: {bin_name} {flag}"
                logger.warning(msg)
                return msg
        return None

    def detect_env_injection(self, s: str) -> EnvInjectionResult:
        """Ortam degiskeni enjeksiyonunu tespit eder."""
        patterns = [
            (r"\$[A-Z_][A-Z0-9_]*", "variable_reference"),
            (r"\$\{[^}+\}", "shell_expansion"),
        ]
        for pat, name in patterns:
            m = re.search(pat, s)
            if m:
                return EnvInjectionResult(detected=True, variable_name=m.group(0), pattern=name)
        return EnvInjectionResult()

    def _sigterm_before_sigkill(self, pid: int, timeout: float = 5.0) -> None:
        """Once SIGTERM, sonra SIGKILL gonderir."""
        try:
            os.kill(pid, 15)
            time.sleep(min(timeout, 2.0))
            os.kill(pid, 9)
        except (OSError, ProcessLookupError):
            pass

    def approve_command(self, command: str) -> str:
        """Komutu onaylar ve hash kaydeder."""
        cmd_hash = hashlib.sha256(command.encode()).hexdigest()[:16]
        self._approved_hashes.add(cmd_hash)
        self._record_history("approve_command", command=command, hash_val=cmd_hash)
        logger.info(f"Komut onaylandi: {cmd_hash}")
        return cmd_hash

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Islem gecmisini dondurur."""
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        return {
            "total_executions": sum(1 for h in self._history if h["action"] == "execute"),
            "blocked_count": sum(1 for h in self._history if h["action"] == "execute_blocked"),
            "approved_commands": len(self._approved_hashes),
            "history_size": len(self._history),
        }
