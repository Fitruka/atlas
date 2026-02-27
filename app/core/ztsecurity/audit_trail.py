"""ATLAS Denetim Izi modulu.

Imzalanmis degistirilemez denetim kaydi.
HMAC imzalama, dogrulama, arama,
disa aktarma islemleri.
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    AuditEntry,
    ZTSTrustLevel,
)

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 100000
_HMAC_KEY = "atlas-audit-hmac-secret-key"
_HASH_ALGORITHM = "sha256"


class AuditTrail:
    """Imzalanmis degistirilemez denetim kaydi.

    HMAC ile imzalanmis denetim kayitlari
    olusturma, dogrulama, arama ve disa aktarma.

    Attributes:
        _entries: Denetim kayitlari.
        _hmac_key: HMAC imzalama anahtari.
    """

    def __init__(
        self,
        hmac_key: str = _HMAC_KEY,
        max_entries: int = _MAX_ENTRIES,
    ) -> None:
        """Denetim izini baslatir.

        Args:
            hmac_key: HMAC imzalama anahtari.
            max_entries: Maksimum kayit sayisi.
        """
        self._entries: dict[
            str, AuditEntry
        ] = {}
        self._entry_order: list[str] = []
        self._hmac_key = hmac_key
        self._max_entries = max_entries
        self._stats = {
            "recorded": 0,
            "verified": 0,
            "verification_passed": 0,
            "verification_failed": 0,
            "searches": 0,
            "exports": 0,
        }

        logger.info("AuditTrail baslatildi")

    def _compute_signature(
        self,
        actor: str,
        action: str,
        resource: str,
        trust_level: str,
        ip_address: str,
        result: str,
        timestamp: str,
    ) -> str:
        """Kayit icin HMAC imzasi hesaplar.

        Args:
            actor: Aktor.
            action: Aksiyon.
            resource: Kaynak.
            trust_level: Guven seviyesi.
            ip_address: IP adresi.
            result: Sonuc.
            timestamp: Zaman damgasi.

        Returns:
            HMAC imzasi.
        """
        message = (
            f"{actor}|{action}|{resource}|"
            f"{trust_level}|{ip_address}|"
            f"{result}|{timestamp}"
        )
        signature = hmac.new(
            self._hmac_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def record(
        self,
        actor: str,
        action: str,
        resource: str,
        trust_level: ZTSTrustLevel = ZTSTrustLevel.NONE,
        ip_address: str = "",
        result: str = "success",
    ) -> AuditEntry:
        """Denetim kaydı olusturur.

        Args:
            actor: Aksiyonu gerceklestiren.
            action: Gerceklestirilen aksiyon.
            resource: Etkilenen kaynak.
            trust_level: Guven seviyesi.
            ip_address: IP adresi.
            result: Sonuc.

        Returns:
            Olusturulan denetim kaydi.
        """
        if len(self._entries) >= self._max_entries:
            oldest_id = self._entry_order.pop(0)
            self._entries.pop(oldest_id, None)

        now = datetime.now(timezone.utc)
        timestamp_str = now.isoformat()

        signature = self._compute_signature(
            actor,
            action,
            resource,
            trust_level.value,
            ip_address,
            result,
            timestamp_str,
        )

        entry = AuditEntry(
            actor=actor,
            action=action,
            resource=resource,
            timestamp=now,
            trust_level=trust_level,
            ip_address=ip_address,
            result=result,
            signature=signature,
        )

        self._entries[entry.id] = entry
        self._entry_order.append(entry.id)
        self._stats["recorded"] += 1

        logger.debug(
            "Denetim kaydi: %s -> %s (%s)",
            actor,
            action,
            resource,
        )
        return entry

    def verify_entry(
        self,
        entry_id: str,
    ) -> bool:
        """Kaydin imzasini dogrular.

        Args:
            entry_id: Kayit ID.

        Returns:
            Imza gecerli ise True.
        """
        self._stats["verified"] += 1

        entry = self._entries.get(entry_id)
        if not entry:
            logger.warning(
                "Denetim kaydi bulunamadi: %s",
                entry_id,
            )
            return False

        expected = self._compute_signature(
            entry.actor,
            entry.action,
            entry.resource,
            entry.trust_level.value,
            entry.ip_address,
            entry.result,
            entry.timestamp.isoformat(),
        )

        valid = hmac.compare_digest(
            entry.signature, expected
        )

        if valid:
            self._stats[
                "verification_passed"
            ] += 1
        else:
            self._stats[
                "verification_failed"
            ] += 1
            logger.warning(
                "Imza dogrulanamadi: %s",
                entry_id,
            )

        return valid

    def search(
        self,
        actor: str | None = None,
        action: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Denetim kayitlarini arar.

        Args:
            actor: Aktor filtresi.
            action: Aksiyon filtresi.
            start_time: Baslangic zamani.
            end_time: Bitis zamani.
            limit: Maksimum sonuc sayisi.

        Returns:
            Eslesen denetim kayitlari.
        """
        self._stats["searches"] += 1
        results: list[AuditEntry] = []

        for entry_id in reversed(
            self._entry_order
        ):
            if len(results) >= limit:
                break

            entry = self._entries.get(entry_id)
            if not entry:
                continue

            if actor and entry.actor != actor:
                continue
            if action and entry.action != action:
                continue
            if (
                start_time
                and entry.timestamp < start_time
            ):
                continue
            if (
                end_time
                and entry.timestamp > end_time
            ):
                continue

            results.append(entry)

        return results

    def get_recent(
        self,
        limit: int = 50,
    ) -> list[AuditEntry]:
        """Son kayitlari getirir.

        Args:
            limit: Maksimum kayit sayisi.

        Returns:
            Son denetim kayitlari.
        """
        recent_ids = self._entry_order[-limit:]
        results = []
        for entry_id in reversed(recent_ids):
            entry = self._entries.get(entry_id)
            if entry:
                results.append(entry)
        return results

    def export(
        self,
        format: str = "json",
    ) -> str:
        """Denetim kayitlarini disa aktarir.

        Args:
            format: Disa aktarma formati ('json').

        Returns:
            Disa aktarilmis veriler.
        """
        self._stats["exports"] += 1

        entries_data = []
        for entry_id in self._entry_order:
            entry = self._entries.get(entry_id)
            if entry:
                entries_data.append({
                    "id": entry.id,
                    "actor": entry.actor,
                    "action": entry.action,
                    "resource": entry.resource,
                    "timestamp": (
                        entry.timestamp.isoformat()
                    ),
                    "trust_level": (
                        entry.trust_level.value
                    ),
                    "ip_address": entry.ip_address,
                    "result": entry.result,
                    "signature": entry.signature,
                })

        if format == "json":
            return json.dumps(
                entries_data,
                indent=2,
                ensure_ascii=False,
            )

        lines = []
        for e in entries_data:
            lines.append(
                f"{e['timestamp']} | "
                f"{e['actor']} | "
                f"{e['action']} | "
                f"{e['resource']} | "
                f"{e['result']}"
            )
        return "\n".join(lines)

    def get_stats(self) -> dict[str, Any]:
        """Denetim izi istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_entries": len(self._entries),
            "max_entries": self._max_entries,
            **self._stats,
        }
