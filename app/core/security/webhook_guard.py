"""Webhook guvenlik koruyucu.

HMAC imza dogrulamasi, icerik tipi kontrolu,
replay saldirisi onleme.
"""

import hashlib
import hmac
import logging
import time
from typing import Any

logger = logging.getLogger("__name__")


class WebhookGuard:
    """Webhook guvenlik koruyucu sinifi."""

    def __init__(self, replay_window=300):
        """WebhookGuard baslatir."""
        self._replay_window = replay_window
        self._seen_nonces = {}
        self._verify_count = 0
        self._failed_count = 0
        self._anomaly_counters = {}

    def constant_time_compare(self, a, b):
        """Sabit zamanli karsilastirma."""
        if isinstance(a, str):
            a = a.encode("utf-8")
        if isinstance(b, str):
            b = b.encode("utf-8")
        return hmac.compare_digest(a, b)

    def verify_hmac_signature(self, payload, signature, secret, algorithm="sha256"):
        """HMAC imza dogrulamasi."""
        self._verify_count += 1
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        try:
            expected = hmac.new(secret, payload, algorithm).hexdigest()
        except (ValueError, TypeError) as e:
            self._failed_count += 1
            return False, str(e)
        if self.constant_time_compare(expected, signature):
            return True, "OK"
        self._failed_count += 1
        return False, "Imza eslesmiyor"

    def enforce_content_type(self, content_type, allowed=None):
        """Icerik tipi kontrolu."""
        if allowed is None:
            allowed = ["application/json", "application/x-www-form-urlencoded"]
        if not content_type:
            return False, "Content-Type eksik"
        ct_lower = content_type.lower().split(";")[0].strip()
        if ct_lower in allowed:
            return True, "OK"
        return False, f"Gecersiz Content-Type: {content_type}"

    def check_replay(self, nonce, timestamp=None):
        """Replay saldirisi kontrolu."""
        now = time.time()
        if timestamp is not None:
            age = abs(now - timestamp)
            if age > self._replay_window:
                return False, f"Zaman asimi: {age:.0f}s"
        expired = [k for k, v in self._seen_nonces.items() if now - v > self._replay_window]
        for k in expired:
            del self._seen_nonces[k]
        if nonce in self._seen_nonces:
            return False, "Tekrarlanan nonce"
        self._seen_nonces[nonce] = now
        return True, "OK"

    def _increment_anomaly(self, category):
        """Anomali sayacini arttirir."""
        self._anomaly_counters[category] = self._anomaly_counters.get(category, 0) + 1

    def get_anomaly_counters(self):
        """Anomali sayaclarini dondurur."""
        return dict(self._anomaly_counters)

    def reset_anomaly_counters(self):
        """Anomali sayaclarini sifirlar."""
        self._anomaly_counters = {}

    def get_stats(self):
        """Istatistikleri dondurur."""
        return {
            "verify_count": self._verify_count,
            "failed_count": self._failed_count,
            "seen_nonces": len(self._seen_nonces),
            "anomaly_counters": len(self._anomaly_counters),
        }
