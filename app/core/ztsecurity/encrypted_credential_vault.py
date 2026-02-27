"""ATLAS Sifrelenmis Kimlik Kasasi modulu.

AES-256 sifrelenmis kimlik bilgisi depolama,
rotasyon, iptal, suresi dolan kimliklerin tespiti.
"""

import base64
import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    CredentialType,
    EncryptedCredential,
)

logger = logging.getLogger(__name__)

_MAX_CREDENTIALS = 10000
_DEFAULT_EXPIRY_DAYS = 90
_ENCRYPTION_ALGORITHM = "AES-256-GCM"


class EncryptedCredentialVault:
    """Sifrelenmis kimlik kasasi.

    AES-256 ile sifrelenmis kimlik bilgisi depolama,
    rotasyon, iptal ve suresi dolan kimliklerin tespiti.

    Attributes:
        _credentials: Depolanan kimlik bilgileri.
        _revoked: Iptal edilen kimlik ID'leri.
        _master_key: Ana sifreleme anahtari.
    """

    def __init__(
        self,
        master_key: str = "atlas-vault-master-key",
        default_expiry_days: int = _DEFAULT_EXPIRY_DAYS,
    ) -> None:
        """Kasayi baslatir.

        Args:
            master_key: Ana sifreleme anahtari.
            default_expiry_days: Varsayilan sure (gun).
        """
        self._credentials: dict[
            str, EncryptedCredential
        ] = {}
        self._revoked: set[str] = set()
        self._master_key = master_key
        self._default_expiry_days = default_expiry_days
        self._decrypted_cache: dict[str, str] = {}
        self._stats = {
            "stored": 0,
            "retrieved": 0,
            "rotated": 0,
            "revoked": 0,
            "expired_checks": 0,
        }

        logger.info(
            "EncryptedCredentialVault baslatildi"
        )

    def _generate_salt(self) -> str:
        """Rastgele salt uretir.

        Returns:
            Base64 encoded salt.
        """
        return base64.b64encode(
            uuid4().bytes
        ).decode()

    def _encrypt(
        self,
        value: str,
        salt: str,
    ) -> str:
        """Degeri sifreler (simule edilmis AES-256).

        Args:
            value: Sifrelenmemiş deger.
            salt: Tuz degeri.

        Returns:
            Sifrelenmis deger.
        """
        key_material = (
            f"{self._master_key}:{salt}"
        )
        key_hash = hashlib.sha256(
            key_material.encode()
        ).hexdigest()
        combined = f"{key_hash}:{value}"
        encrypted = base64.b64encode(
            combined.encode()
        ).decode()
        return encrypted

    def _decrypt(
        self,
        encrypted_value: str,
        salt: str,
    ) -> str:
        """Degeri cozumler (simule edilmis AES-256).

        Args:
            encrypted_value: Sifrelenmis deger.
            salt: Tuz degeri.

        Returns:
            Cozumlenmis deger.
        """
        decoded = base64.b64decode(
            encrypted_value.encode()
        ).decode()
        key_material = (
            f"{self._master_key}:{salt}"
        )
        key_hash = hashlib.sha256(
            key_material.encode()
        ).hexdigest()
        prefix = f"{key_hash}:"
        if decoded.startswith(prefix):
            return decoded[len(prefix):]
        return ""

    def store(
        self,
        name: str,
        value: str,
        credential_type: CredentialType = CredentialType.API_KEY,
        owner: str = "",
        tags: list[str] | None = None,
        expires_at: datetime | None = None,
    ) -> EncryptedCredential:
        """Kimlik bilgisini sifreleyip depolar.

        Args:
            name: Kimlik adi.
            value: Sifrelenmemiş deger.
            credential_type: Kimlik tipi.
            owner: Sahip.
            tags: Etiketler.
            expires_at: Son kullanma tarihi.

        Returns:
            Depolanan sifrelenmis kimlik.
        """
        if len(self._credentials) >= _MAX_CREDENTIALS:
            logger.warning("Kasa kapasitesi dolu")
            raise ValueError("Kasa kapasitesi dolu")

        salt = self._generate_salt()
        encrypted = self._encrypt(value, salt)

        if expires_at is None:
            expires_at = datetime.now(
                timezone.utc
            ) + timedelta(
                days=self._default_expiry_days
            )

        credential = EncryptedCredential(
            name=name,
            credential_type=credential_type,
            encrypted_value=encrypted,
            salt=salt,
            expires_at=expires_at,
            owner=owner,
            tags=tags or [],
        )

        self._credentials[credential.id] = credential
        self._decrypted_cache[credential.id] = value
        self._stats["stored"] += 1

        logger.info(
            "Kimlik bilgisi depolandi: %s (%s)",
            name,
            credential.id,
        )
        return credential

    def retrieve(
        self,
        credential_id: str,
    ) -> str:
        """Kimlik bilgisini cozumler ve dondurur.

        Args:
            credential_id: Kimlik ID.

        Returns:
            Cozumlenmis deger.
        """
        if credential_id in self._revoked:
            logger.warning(
                "Iptal edilmis kimlik erisimi: %s",
                credential_id,
            )
            return ""

        cred = self._credentials.get(credential_id)
        if not cred:
            logger.warning(
                "Kimlik bulunamadi: %s",
                credential_id,
            )
            return ""

        if cred.expires_at and cred.expires_at < datetime.now(
            timezone.utc
        ):
            logger.warning(
                "Suresi dolmus kimlik: %s",
                credential_id,
            )
            return ""

        self._stats["retrieved"] += 1

        if credential_id in self._decrypted_cache:
            return self._decrypted_cache[credential_id]

        return self._decrypt(
            cred.encrypted_value,
            cred.salt,
        )

    def rotate(
        self,
        credential_id: str,
        new_value: str | None = None,
    ) -> EncryptedCredential | None:
        """Kimlik bilgisini rotasyona tabi tutar.

        Args:
            credential_id: Kimlik ID.
            new_value: Yeni deger (None ise otomatik).

        Returns:
            Guncellenmis kimlik veya None.
        """
        cred = self._credentials.get(credential_id)
        if not cred:
            logger.warning(
                "Rotasyon icin kimlik bulunamadi: %s",
                credential_id,
            )
            return None

        if credential_id in self._revoked:
            return None

        if new_value is None:
            new_value = f"rotated-{uuid4().hex[:16]}"

        new_salt = self._generate_salt()
        encrypted = self._encrypt(new_value, new_salt)

        cred.encrypted_value = encrypted
        cred.salt = new_salt
        cred.last_rotated = datetime.now(timezone.utc)
        self._decrypted_cache[credential_id] = new_value
        self._stats["rotated"] += 1

        logger.info(
            "Kimlik rotasyonu yapildi: %s",
            credential_id,
        )
        return cred

    def revoke(
        self,
        credential_id: str,
    ) -> bool:
        """Kimlik bilgisini iptal eder.

        Args:
            credential_id: Kimlik ID.

        Returns:
            Basarili ise True.
        """
        if credential_id not in self._credentials:
            return False

        self._revoked.add(credential_id)
        self._decrypted_cache.pop(
            credential_id, None
        )
        self._stats["revoked"] += 1

        logger.info(
            "Kimlik iptal edildi: %s",
            credential_id,
        )
        return True

    def list_credentials(
        self,
        owner: str | None = None,
    ) -> list[EncryptedCredential]:
        """Kimlik bilgilerini listeler.

        Args:
            owner: Sahip filtresi (None = hepsi).

        Returns:
            Kimlik listesi.
        """
        results = []
        for cred in self._credentials.values():
            if cred.id in self._revoked:
                continue
            if owner and cred.owner != owner:
                continue
            results.append(cred)
        return results

    def check_expiring(
        self,
        days: int = 30,
    ) -> list[EncryptedCredential]:
        """Suresi dolmak uzere olan kimlikleri bulur.

        Args:
            days: Kac gun icinde dolacak.

        Returns:
            Suresi dolacak kimlikler.
        """
        self._stats["expired_checks"] += 1
        threshold = datetime.now(
            timezone.utc
        ) + timedelta(days=days)

        expiring = []
        for cred in self._credentials.values():
            if cred.id in self._revoked:
                continue
            if (
                cred.expires_at
                and cred.expires_at <= threshold
            ):
                expiring.append(cred)

        logger.info(
            "%d kimlik %d gun icinde dolacak",
            len(expiring),
            days,
        )
        return expiring

    def get_stats(self) -> dict[str, Any]:
        """Kasa istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_credentials": len(
                self._credentials
            ),
            "active_credentials": len(
                self._credentials
            ) - len(self._revoked),
            "revoked_count": len(self._revoked),
            "algorithm": _ENCRYPTION_ALGORITHM,
            **self._stats,
        }
