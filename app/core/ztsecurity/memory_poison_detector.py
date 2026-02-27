"""ATLAS Hafiza Zehirleme Tespitcisi modulu.

Hafiza ve bilgi tabani kurcalama tespiti.
Hash tabanli butunluk kontrolu, otomatik
duzeltme ve zehirlenme kayitlari.
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    PoisonAttempt,
    ThreatSeverity,
)

logger = logging.getLogger(__name__)

_MAX_MEMORY_ENTRIES = 50000
_HASH_ALGORITHM = "sha256"


class MemoryPoisonDetector:
    """Hafiza zehirleme tespitcisi.

    Hafiza ve bilgi tabani kurcalama tespiti.
    Hash tabanli butunluk kontrolu ve otomatik
    duzeltme.

    Attributes:
        _hashes: Kayitli hafiza hash'leri.
        _values: Orijinal degerler (yedek).
        _attempts: Tespit edilen girişimler.
    """

    def __init__(
        self,
        hash_algorithm: str = _HASH_ALGORITHM,
    ) -> None:
        """Tespitciyi baslatir.

        Args:
            hash_algorithm: Hash algoritmasi.
        """
        self._hashes: dict[str, str] = {}
        self._values: dict[str, str] = {}
        self._attempts: dict[
            str, PoisonAttempt
        ] = {}
        self._hash_algorithm = hash_algorithm
        self._stats = {
            "registered": 0,
            "verified": 0,
            "tampered": 0,
            "remediated": 0,
            "scans": 0,
        }

        logger.info(
            "MemoryPoisonDetector baslatildi, "
            "algoritma: %s",
            hash_algorithm,
        )

    def _compute_hash(
        self,
        value: str,
    ) -> str:
        """Deger icin hash hesaplar.

        Args:
            value: Hash'lenecek deger.

        Returns:
            Hesaplanan hash.
        """
        hasher = hashlib.new(self._hash_algorithm)
        hasher.update(value.encode("utf-8"))
        return hasher.hexdigest()

    def register_memory(
        self,
        key: str,
        value: str,
    ) -> str:
        """Hafiza kaydini butunluk kontrolu icin kaydeder.

        Args:
            key: Hafiza anahtari.
            value: Hafiza degeri.

        Returns:
            Hesaplanan hash.
        """
        if len(self._hashes) >= _MAX_MEMORY_ENTRIES:
            logger.warning(
                "Hafiza kayit kapasitesi dolu"
            )
            oldest_key = next(iter(self._hashes))
            del self._hashes[oldest_key]
            self._values.pop(oldest_key, None)

        hash_value = self._compute_hash(value)
        self._hashes[key] = hash_value
        self._values[key] = value
        self._stats["registered"] += 1

        logger.debug(
            "Hafiza kaydedildi: %s (hash: %s...)",
            key,
            hash_value[:12],
        )
        return hash_value

    def verify_integrity(
        self,
        key: str,
        current_value: str | None = None,
    ) -> bool:
        """Hafiza kaydinin butunlugunu dogrular.

        Args:
            key: Hafiza anahtari.
            current_value: Mevcut deger (None ise yedek).

        Returns:
            Butunluk saglaniyorsa True.
        """
        self._stats["verified"] += 1

        original_hash = self._hashes.get(key)
        if original_hash is None:
            logger.warning(
                "Bilinmeyen hafiza anahtari: %s",
                key,
            )
            return True

        if current_value is None:
            current_value = self._values.get(key, "")

        current_hash = self._compute_hash(
            current_value
        )

        if current_hash != original_hash:
            self._stats["tampered"] += 1

            attempt = PoisonAttempt(
                memory_key=key,
                original_hash=original_hash,
                tampered_hash=current_hash,
                severity=ThreatSeverity.HIGH,
            )
            self._attempts[attempt.id] = attempt

            logger.warning(
                "Hafiza kurcalama tespit edildi: "
                "%s (orijinal: %s..., mevcut: %s...)",
                key,
                original_hash[:12],
                current_hash[:12],
            )
            return False

        return True

    def scan_all(self) -> list[PoisonAttempt]:
        """Tum kayitli hafizayi butunluk icin tarar.

        Returns:
            Tespit edilen zehirleme girisimleri.
        """
        self._stats["scans"] += 1
        found: list[PoisonAttempt] = []

        for key in list(self._hashes.keys()):
            stored_value = self._values.get(key)
            if stored_value is None:
                continue

            if not self.verify_integrity(
                key, stored_value
            ):
                attempt_id = None
                for aid, attempt in (
                    self._attempts.items()
                ):
                    if attempt.memory_key == key:
                        attempt_id = aid
                        break
                if attempt_id:
                    found.append(
                        self._attempts[attempt_id]
                    )

        logger.info(
            "Hafiza tarandi: %d kayit, "
            "%d kurcalama tespit edildi",
            len(self._hashes),
            len(found),
        )
        return found

    def remediate(
        self,
        attempt_id: str,
    ) -> bool:
        """Kurcalama girisimini duzeltir.

        Args:
            attempt_id: Girisim ID.

        Returns:
            Basarili ise True.
        """
        attempt = self._attempts.get(attempt_id)
        if not attempt:
            logger.warning(
                "Girisim bulunamadi: %s",
                attempt_id,
            )
            return False

        if attempt.remediated:
            return True

        key = attempt.memory_key
        original_value = self._values.get(key)
        if original_value:
            original_hash = self._compute_hash(
                original_value
            )
            self._hashes[key] = original_hash

        attempt.remediated = True
        self._stats["remediated"] += 1

        logger.info(
            "Hafiza duzeltildi: %s (girisim: %s)",
            key,
            attempt_id,
        )
        return True

    def get_tampered_count(self) -> int:
        """Kurcalanmis kayit sayisini dondurur.

        Returns:
            Kurcalanmis kayit sayisi.
        """
        return sum(
            1
            for a in self._attempts.values()
            if not a.remediated
        )

    def get_stats(self) -> dict[str, Any]:
        """Tespitci istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_entries": len(self._hashes),
            "total_attempts": len(self._attempts),
            "unremediated": self.get_tampered_count(),
            "hash_algorithm": self._hash_algorithm,
            **self._stats,
        }
