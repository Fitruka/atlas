"""Prototype pollution onleme.

Dict birlestirme guvenligi, tehlikeli anahtar
engelleme, YAML bool zorlama tespiti.
"""

import logging
import re
from typing import Any

logger = logging.getLogger("__name__")

_DANGEROUS_KEYS = {
    "__proto__",
    "prototype",
    "constructor",
    "__class__",
    "__bases__",
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__import__",
}

_YAML_BOOL_PATTERN = re.compile(r"^(on|off|yes|no|true|false|y|n)$", re.IGNORECASE)


class PrototypeGuard:
    """Prototype pollution koruyucu."""

    def __init__(self, extra_blocked=None):
        """PrototypeGuard baslatir."""
        self._blocked_keys = set(_DANGEROUS_KEYS)
        if extra_blocked:
            self._blocked_keys.update(extra_blocked)
        self._block_count = 0

    def safe_merge(self, base, override, depth=0):
        """Guvenli dict birlestirme."""
        if depth > 10:
            return base
        if not isinstance(base, dict) or not isinstance(override, dict):
            return override
        result = dict(base)
        for key, value in override.items():
            if key in self._blocked_keys:
                self._block_count += 1
                continue
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.safe_merge(result[key], value, depth + 1)
            else:
                result[key] = value
        return result

    def check_dict_keys(self, data, depth=0):
        """Dict anahtarlarini kontrol eder."""
        if depth > 10:
            return True, []
        if not isinstance(data, dict):
            return True, []
        found = []
        for key, value in data.items():
            if key in self._blocked_keys:
                found.append(key)
            if isinstance(value, dict):
                _, sub = self.check_dict_keys(value, depth + 1)
                found.extend(sub)
        return len(found) == 0, found

    def sanitize_yaml_value(self, value):
        """YAML deger sanitizasyonu."""
        if not isinstance(value, str):
            return value
        if _YAML_BOOL_PATTERN.match(value):
            return '"' + value + '"'
        return value

    def is_yaml_bool_coercion(self, value):
        """YAML bool zorlama tespiti."""
        if not isinstance(value, str):
            return False
        return bool(_YAML_BOOL_PATTERN.match(value))

    def get_stats(self):
        """Istatistikleri dondurur."""
        return {
            "blocked_count": self._block_count,
            "blocked_keys": len(self._blocked_keys),
        }
