"""Komut yurutme guvenligi.

Guvenli calistirma, safeBins, tehlikeli bayrak
engelleme, argument sanitizasyonu.
"""

import logging
import os
import re
import shutil
from typing import Any

logger = logging.getLogger(__name__)

_DANGEROUS_FLAGS = {
    "sort": ["-o", "--output"],
    "jq": ["-f", "--from-file"],
    "grep": ["-f", "--file"],
    "sed": ["-f", "--file"],
    "awk": ["-f"],
}

_DEFAULT_SAFE_BINS = [
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "grep",
    "sort",
    "uniq",
    "cut",
    "tr",
    "echo",
    "date",
    "whoami",
    "hostname",
    "python",
    "python3",
    "pip",
    "pip3",
    "node",
    "npm",
    "npx",
    "git",
    "curl",
    "wget",
    "docker",
    "docker-compose",
]

_CRLF_PATTERN = re.compile(r"[\r\n]")
_WIN_META = re.compile(r"[&|<>^%!]")


class ExecGuard:
    """Komut yurutme guvenlik koruyucu."""

    def __init__(self, safe_bins=None, trusted_dirs=None):
        """ExecGuard baslatir."""
        self._safe_bins = set(safe_bins or _DEFAULT_SAFE_BINS)
        self._trusted_dirs = trusted_dirs or []
        self._exec_count = 0
        self._blocked_count = 0

    def resolve_safe_bin(self, command):
        """Guvenli binary cozumlemesi."""
        self._exec_count += 1
        base_cmd = os.path.basename(command)
        if base_cmd not in self._safe_bins:
            self._blocked_count += 1
            return None, f"Guvenli olmayan binary: {base_cmd}"
        if self._trusted_dirs:
            for tdir in self._trusted_dirs:
                full = os.path.join(tdir, base_cmd)
                if os.path.isfile(full):
                    return full, "OK"
        resolved = shutil.which(base_cmd)
        if resolved:
            return resolved, "OK"
        return None, f"Binary bulunamadi: {base_cmd}"

    def check_dangerous_flags(self, command, args):
        """Tehlikeli bayrak kontrolu."""
        base_cmd = os.path.basename(command)
        dangerous = _DANGEROUS_FLAGS.get(base_cmd, [])
        if not dangerous: return True, "OK"
        for arg in args:
            if arg in dangerous:
                self._blocked_count += 1
                return False, f"Tehlikeli bayrak: {base_cmd} {arg}"
        return True, "OK"

    def sanitize_arguments(self, args):
        """Arguman sanitizasyonu."""
        clean = []
        warnings = []
        for arg in args:
            if "\x00" in arg:
                warnings.append(f"Null byte temizlendi: {repr(arg[:20])}")
                arg = arg.replace("\x00", "")
            if _CRLF_PATTERN.search(arg):
                warnings.append(f"CR/LF temizlendi: {repr(arg[:20])}")
                arg = _CRLF_PATTERN.sub("", arg)
            if arg: clean.append(arg)
        return clean, warnings

    def escape_windows_meta(self, arg):
        """Windows meta karakter kacisi."""
        if not _WIN_META.search(arg): return arg
        escaped = arg.replace('"', '\\"')
        return f'"{escaped}"'

    def validate_env_vars(self, env):
        """Environment variable kontrolu."""
        issues = []
        for key, value in env.items():
            if _CRLF_PATTERN.search(key):
                issues.append(f"CR/LF env key: {repr(key[:20])}")
            if "=" in key:
                issues.append(f"= iceren env key: {key[:20]}")
            if _CRLF_PATTERN.search(value):
                issues.append(f"CR/LF env value: {key}={repr(value[:20])}")
        return len(issues) == 0, issues

    def add_safe_bin(self, binary):
        """Guvenli binary ekler."""
        self._safe_bins.add(binary)

    def remove_safe_bin(self, binary):
        """Guvenli binary siler."""
        self._safe_bins.discard(binary)

    def get_stats(self):
        """Istatistikleri dondurur."""
        return {
            "total_execs": self._exec_count,
            "blocked": self._blocked_count,
            "safe_bins": len(self._safe_bins),
            "trusted_dirs": len(self._trusted_dirs),
        }
