"""ATLAS Guvenli Guncelleme Zinciri modulu.

Imzalanmis ve dogrulanmis guncelleme paketleri.
SHA-256 checksum, imza dogrulama, guncelleme
uygulama ve geri alma islemleri.
"""

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    UpdateChannel,
    UpdatePackage,
)

logger = logging.getLogger(__name__)

_MAX_UPDATES = 5000
_SIGNING_KEY = "atlas-update-signing-key"


class SecureUpdateChain:
    """Guvenli guncelleme zinciri.

    Imzalanmis ve dogrulanmis guncelleme paketleri.
    SHA-256 checksum, imza dogrulama ve uygulama.

    Attributes:
        _updates: Kayitli guncellemeler.
        _applied: Uygulanmis guncelleme ID'leri.
        _signing_key: Imzalama anahtari.
    """

    def __init__(
        self,
        signing_key: str = _SIGNING_KEY,
    ) -> None:
        """Guncelleme zincirini baslatir.

        Args:
            signing_key: Imzalama anahtari.
        """
        self._updates: dict[
            str, UpdatePackage
        ] = {}
        self._applied: set[str] = set()
        self._rolled_back: set[str] = set()
        self._signing_key = signing_key
        self._stats = {
            "registered": 0,
            "verified": 0,
            "applied": 0,
            "rolled_back": 0,
            "verification_passed": 0,
            "verification_failed": 0,
        }

        logger.info(
            "SecureUpdateChain baslatildi"
        )

    def _compute_checksum(
        self,
        content: str,
    ) -> str:
        """Icerik icin SHA-256 checksum hesaplar.

        Args:
            content: Checksum hesaplanacak icerik.

        Returns:
            SHA-256 hash degeri.
        """
        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    def _compute_signature(
        self,
        version: str,
        checksum: str,
        channel: str,
    ) -> str:
        """Guncelleme paketi icin imza hesaplar.

        Args:
            version: Surum numarasi.
            checksum: Checksum degeri.
            channel: Guncelleme kanali.

        Returns:
            HMAC imzasi.
        """
        import hmac as hmac_mod

        message = (
            f"{version}|{checksum}|{channel}"
        )
        return hmac_mod.new(
            self._signing_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    def register_update(
        self,
        version: str,
        channel: UpdateChannel = UpdateChannel.STABLE,
        content: str = "",
        changelog: str = "",
    ) -> UpdatePackage:
        """Yeni guncelleme paketi kaydeder.

        Args:
            version: Surum numarasi.
            channel: Guncelleme kanali.
            content: Paket icerigi.
            changelog: Degisiklik notlari.

        Returns:
            Olusturulan guncelleme paketi.
        """
        if len(self._updates) >= _MAX_UPDATES:
            logger.warning(
                "Guncelleme kapasitesi dolu"
            )
            raise ValueError(
                "Guncelleme kapasitesi dolu"
            )

        checksum = self._compute_checksum(content)
        signature = self._compute_signature(
            version, checksum, channel.value
        )

        package = UpdatePackage(
            version=version,
            channel=channel,
            checksum_sha256=checksum,
            signature=signature,
            size_bytes=len(content.encode("utf-8")),
            changelog=changelog,
            verified=True,
        )

        self._updates[package.id] = package
        self._stats["registered"] += 1

        logger.info(
            "Guncelleme kaydedildi: v%s (%s) "
            "kanal=%s",
            version,
            package.id,
            channel.value,
        )
        return package

    def verify_update(
        self,
        update_id: str,
    ) -> bool:
        """Guncelleme paketinin imzasini dogrular.

        Args:
            update_id: Guncelleme ID.

        Returns:
            Imza gecerli ise True.
        """
        self._stats["verified"] += 1

        package = self._updates.get(update_id)
        if not package:
            logger.warning(
                "Guncelleme bulunamadi: %s",
                update_id,
            )
            return False

        expected_sig = self._compute_signature(
            package.version,
            package.checksum_sha256,
            package.channel.value,
        )

        import hmac as hmac_mod

        valid = hmac_mod.compare_digest(
            package.signature, expected_sig
        )

        if valid:
            self._stats[
                "verification_passed"
            ] += 1
            package.verified = True
        else:
            self._stats[
                "verification_failed"
            ] += 1
            package.verified = False
            logger.warning(
                "Guncelleme imzasi gecersiz: %s",
                update_id,
            )

        return valid

    def apply_update(
        self,
        update_id: str,
    ) -> dict[str, Any]:
        """Guncelleme paketini uygular.

        Args:
            update_id: Guncelleme ID.

        Returns:
            Uygulama sonucu.
        """
        package = self._updates.get(update_id)
        if not package:
            return {
                "success": False,
                "error": "Guncelleme bulunamadi",
            }

        if update_id in self._applied:
            return {
                "success": False,
                "error": "Guncelleme zaten uygulandi",
            }

        if not package.verified:
            verified = self.verify_update(
                update_id
            )
            if not verified:
                return {
                    "success": False,
                    "error": "Imza dogrulanamadi",
                }

        self._applied.add(update_id)
        self._stats["applied"] += 1

        logger.info(
            "Guncelleme uygulandi: v%s (%s)",
            package.version,
            update_id,
        )
        return {
            "success": True,
            "version": package.version,
            "channel": package.channel.value,
            "update_id": update_id,
        }

    def get_available_updates(
        self,
        channel: UpdateChannel | None = None,
    ) -> list[UpdatePackage]:
        """Mevcut guncellemeleri listeler.

        Args:
            channel: Kanal filtresi (None = hepsi).

        Returns:
            Mevcut guncelleme listesi.
        """
        results = []
        for package in self._updates.values():
            if package.id in self._applied:
                continue
            if package.id in self._rolled_back:
                continue
            if (
                channel
                and package.channel != channel
            ):
                continue
            results.append(package)

        results.sort(
            key=lambda p: p.released_at,
            reverse=True,
        )
        return results

    def rollback(
        self,
        update_id: str,
    ) -> bool:
        """Uygulanmis guncellemeyi geri alir.

        Args:
            update_id: Guncelleme ID.

        Returns:
            Basarili ise True.
        """
        if update_id not in self._applied:
            logger.warning(
                "Geri alinacak guncelleme "
                "uygulanmamis: %s",
                update_id,
            )
            return False

        self._applied.discard(update_id)
        self._rolled_back.add(update_id)
        self._stats["rolled_back"] += 1

        package = self._updates.get(update_id)
        version = (
            package.version if package else "?"
        )
        logger.info(
            "Guncelleme geri alindi: v%s (%s)",
            version,
            update_id,
        )
        return True

    def get_stats(self) -> dict[str, Any]:
        """Zincir istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_updates": len(self._updates),
            "applied_count": len(self._applied),
            "rolled_back_count": len(
                self._rolled_back
            ),
            **self._stats,
        }
