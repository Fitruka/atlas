"""Sandbox ve konteyner guvenligi.

Docker yapilandirma kontrolu, SHA-256 hash,
sandbox opt-in dogrulamasi.
"""

import hashlib
import logging
import os
from typing import Any

logger = logging.getLogger("__name__")

_DANGEROUS_DOCKER_CONFIGS = [
    "privileged",
    "host",
    "pid:host",
    "ipc:host",
]

_DANGEROUS_MOUNTS = [
    "/var/run/docker.sock",
    "/etc/shadow",
    "/etc/passwd",
    "/proc",
    "/sys",
    "/dev",
    "/root",
]


class SandboxGuard:
    """Sandbox guvenlik koruyucu."""

    def __init__(self):
        """SandboxGuard baslatir."""
        self._check_count = 0
        self._blocked_count = 0

    def check_docker_config(self, config):
        """Docker yapilandirma kontrolu."""
        self._check_count += 1
        issues = []
        if not isinstance(config, dict):
            return False, ["Config dict olmali"]
        if config.get("privileged"):
            issues.append("Privileged mod aktif")
        network_mode = config.get("network_mode", "")
        if network_mode == "host":
            issues.append("Host network modu")
        pid_mode = config.get("pid_mode", "")
        if pid_mode == "host":
            issues.append("Host PID modu")
        ipc_mode = config.get("ipc_mode", "")
        if ipc_mode == "host":
            issues.append("Host IPC modu")
        mounts = config.get("mounts", [])
        for mount in mounts:
            src = mount if isinstance(mount, str) else mount.get("source", "")
            for dangerous in _DANGEROUS_MOUNTS:
                if src.startswith(dangerous):
                    issues.append(f"Tehlikeli mount: {src}")
        caps = config.get("cap_add", [])
        if "SYS_ADMIN" in caps:
            issues.append("SYS_ADMIN yetkisi")
        if "NET_ADMIN" in caps:
            issues.append("NET_ADMIN yetkisi")
        if "ALL" in caps:
            issues.append("ALL yetkisi")
        if issues:
            self._blocked_count += 1
        return len(issues) == 0, issues

    def hash_sha256(self, data):
        """SHA-256 hash hesaplar."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def hash_sha256_file(self, filepath):
        """Dosya SHA-256 hash hesaplar."""
        sha = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sha.update(chunk)
            return sha.hexdigest(), "OK"
        except OSError as e:
            return None, str(e)

    def check_no_sandbox_opt_in(self, args):
        """no-sandbox bayrak kontrolu."""
        self._check_count += 1
        dangerous_flags = ["--no-sandbox", "--disable-setuid-sandbox"]
        found = []
        for arg in args:
            for flag in dangerous_flags:
                if flag in arg:
                    found.append(flag)
        if found:
            self._blocked_count += 1
            return False, f"Sandbox devre disi bayraklar: {found}"
        return True, "OK"

    def check_cdp_source(self, url):
        """CDP kaynak URL kontrolu."""
        self._check_count += 1
        if not url:
            return True, "OK"
        if url.startswith("file://"):
            self._blocked_count += 1
            return False, "file:// protokolu CDP icin engellendi"
        if "localhost" in url or "127.0.0.1" in url:
            return True, "OK"
        self._blocked_count += 1
        return False, f"Uzak CDP baglantisi: {url}"

    def get_stats(self):
        """Istatistikleri dondurur."""
        return {
            "total_checks": self._check_count,
            "blocked": self._blocked_count,
        }
