"""Kimlik bilgisi koruma.

Hassas veri tespiti, redaksiyon, guvenli dosya
izinleri, gecici dosya yonetimi.
"""

import logging
import os
import re
import secrets
import stat
from typing import Any

logger = logging.getLogger(__name__)

_SENSITIVE_SUFFIXES = [
    "password", "passwd", "secret", "token",
    "api_key", "apikey", "api-key",
    "auth", "credential", "private_key", "privatekey",
    "access_key", "accesskey", "client_secret",
    "webhook_secret", "bot_token", "encryption_key",
]

REDACTED = "***REDACTED***"

_TELEGRAM_TOKEN_PATTERN = re.compile(r"\d+:[A-Za-z0-9_-]{35,}")


class CredentialGuard:
    """Kimlik bilgisi koruma sinifi."""

    def __init__(self, extra_suffixes=None):
        """CredentialGuard baslatir."""
        self._suffixes = list(_SENSITIVE_SUFFIXES)
        if extra_suffixes:
            self._suffixes.extend(extra_suffixes)
        self._redact_count = 0

    def is_sensitive_key(self, key):
        """Hassas anahtar kontrolu."""
        lower_key = key.lower().replace("-", "_")
        for suffix in self._suffixes:
            if lower_key.endswith(suffix) or lower_key == suffix:
                return True
        return False

    def redact_dict(self, data, depth=0):
        """Dict icerisindeki hassas verileri maskeler."""
        if depth > 10:
            return data
        if not isinstance(data, dict):
            return data
        result = {}
        for key, value in data.items():
            if self.is_sensitive_key(str(key)):
                result[key] = REDACTED
                self._redact_count += 1
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value, depth + 1)
            elif isinstance(value, list):
                result[key] = [
                    self.redact_dict(item, depth + 1)
                    if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def redact_telegram_token(self, text):
        """Telegram token redaksiyonu."""
        if not isinstance(text, str):
            return text
        result = _TELEGRAM_TOKEN_PATTERN.sub(REDACTED, text)
        if result != text:
            self._redact_count += 1
        return result

    def redact_path_prefix(self, path, keep_levels=2):
        """Dosya yolunun hassas kismini gizler."""
        parts = path.replace("\\", "/").split("/")
        if len(parts) <= keep_levels:
            return path
        hidden = ["***"] * (len(parts) - keep_levels)
        visible = parts[-keep_levels:]
        return "/".join(hidden + visible)

    def secure_file_permissions(self, filepath):
        """Dosya izinlerini guvenli yapar (600)."""
        try:
            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)
            return True, "OK"
        except OSError as e:
            return False, str(e)

    def generate_secure_temp_name(self, prefix="tmp_", suffix=""):
        """Guvenli gecici dosya adi uretir."""
        token = secrets.token_hex(16)
        return f"{prefix}{token}{suffix}"

    def add_sensitive_suffix(self, suffix):
        """Yeni hassas anahtar son eki ekler."""
        if suffix not in self._suffixes:
            self._suffixes.append(suffix)

    def get_stats(self):
        """Istatistikleri dondurur."""
        return {
            "redacted_count": self._redact_count,
            "sensitive_suffixes": len(self._suffixes),
        }
