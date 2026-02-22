"""API anahtar rotasyonu ve yuk dengeleme.

Anahtar rotasyonu, yuk dengeleme, kota takibi,
failover ve maliyet dagitimi saglar.
"""

import logging
import time
from typing import Any

from app.models.unifiedllm_models import (
    APIKeyInfo,
    KeyState,
    LLMProvider,
)

logger = logging.getLogger(__name__)


class APIKeyRotator:
    """API anahtar rotasyonu ve yuk dengeleme.

    Birden fazla API anahtarini rotasyonla kullanir,
    kota takibi ve failover saglar.

    Attributes:
        _keys: Saglayici bazli anahtar listesi.
        _current_index: Her saglayici icin mevcut indeks.
        _rotation_count: Toplam rotasyon sayisi.
    """

    def __init__(self) -> None:
        """APIKeyRotator baslatir."""
        self._keys: dict[str, list[APIKeyInfo]] = {}
        self._current_index: dict[str, int] = {}
        self._rotation_count: int = 0

        logger.info("APIKeyRotator baslatildi")

    def add_key(
        self,
        provider: LLMProvider,
        api_key: str,
        key_id: str = "",
        quota_remaining: float = -1.0,
    ) -> APIKeyInfo:
        """API anahtari ekler.

        Args:
            provider: LLM saglayicisi.
            api_key: API anahtari.
            key_id: Anahtar ID'si.
            quota_remaining: Kalan kota.

        Returns:
            Eklenen anahtar bilgisi.
        """
        prov = provider.value

        if prov not in self._keys:
            self._keys[prov] = []
            self._current_index[prov] = 0

        # Maskelenmis anahtar
        masked = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"

        info = APIKeyInfo(
            key_id=key_id or f"key_{len(self._keys[prov])}",
            provider=provider,
            key_masked=masked,
            quota_remaining=quota_remaining,
        )

        # Gercek anahtari sakla (info'nun disinda)
        info._raw_key = api_key  # type: ignore[attr-defined]

        self._keys[prov].append(info)
        logger.info(
            "API anahtari eklendi: provider=%s, id=%s",
            prov, info.key_id,
        )
        return info

    def remove_key(self, provider: LLMProvider, key_id: str) -> bool:
        """API anahtarini siler.

        Args:
            provider: LLM saglayicisi.
            key_id: Anahtar ID'si.

        Returns:
            Basarili ise True.
        """
        prov = provider.value
        keys = self._keys.get(prov, [])

        for i, k in enumerate(keys):
            if k.key_id == key_id:
                keys.pop(i)
                if self._current_index.get(prov, 0) >= len(keys):
                    self._current_index[prov] = 0
                logger.info("API anahtari silindi: %s/%s", prov, key_id)
                return True

        return False

    def get_key(self, provider: LLMProvider) -> str | None:
        """Mevcut aktif anahtari getirir (round-robin).

        Args:
            provider: LLM saglayicisi.

        Returns:
            API anahtari veya None.
        """
        prov = provider.value
        keys = self._keys.get(prov, [])

        if not keys:
            return None

        # Aktif anahtar bul
        active_keys = [k for k in keys if k.state == KeyState.ACTIVE]
        if not active_keys:
            return None

        idx = self._current_index.get(prov, 0) % len(active_keys)
        key_info = active_keys[idx]

        # Sonraki rotasyon
        self._current_index[prov] = (idx + 1) % len(active_keys)
        self._rotation_count += 1

        return getattr(key_info, "_raw_key", None)

    def record_usage(
        self,
        provider: LLMProvider,
        key_id: str,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Kullanim kaydeder.

        Args:
            provider: LLM saglayicisi.
            key_id: Anahtar ID'si.
            tokens: Kullnilan token.
            cost: Maliyet (USD).
        """
        prov = provider.value
        for k in self._keys.get(prov, []):
            if k.key_id == key_id:
                k.total_requests += 1
                k.total_tokens += tokens
                k.total_cost += cost
                if k.quota_remaining > 0:
                    k.quota_remaining -= cost
                break

    def mark_rate_limited(
        self,
        provider: LLMProvider,
        key_id: str,
        reset_at: float = 0.0,
    ) -> None:
        """Anahtari hiz sinirli olarak isaretler.

        Args:
            provider: LLM saglayicisi.
            key_id: Anahtar ID'si.
            reset_at: Sifirlanma zamani (epoch).
        """
        prov = provider.value
        for k in self._keys.get(prov, []):
            if k.key_id == key_id:
                k.state = KeyState.RATE_LIMITED
                if reset_at > 0:
                    k.rate_limit_reset = reset_at
                else:
                    k.rate_limit_reset = time.time() + 60
                logger.warning(
                    "Anahtar hiz sinirli: %s/%s", prov, key_id,
                )
                break

    def mark_exhausted(
        self, provider: LLMProvider, key_id: str
    ) -> None:
        """Anahtari tukenmis olarak isaretler.

        Args:
            provider: LLM saglayicisi.
            key_id: Anahtar ID'si.
        """
        prov = provider.value
        for k in self._keys.get(prov, []):
            if k.key_id == key_id:
                k.state = KeyState.EXHAUSTED
                k.quota_remaining = 0.0
                logger.warning(
                    "Anahtar tukendi: %s/%s", prov, key_id,
                )
                break

    def mark_revoked(
        self, provider: LLMProvider, key_id: str
    ) -> None:
        """Anahtari iptal edilmis olarak isaretler.

        Args:
            provider: LLM saglayicisi.
            key_id: Anahtar ID'si.
        """
        prov = provider.value
        for k in self._keys.get(prov, []):
            if k.key_id == key_id:
                k.state = KeyState.REVOKED
                logger.warning(
                    "Anahtar iptal edildi: %s/%s", prov, key_id,
                )
                break

    def recover_rate_limited(self) -> int:
        """Hiz siniri kalkmis anahtarlari aktif yapar.

        Returns:
            Kurtarilan anahtar sayisi.
        """
        now = time.time()
        recovered = 0

        for keys in self._keys.values():
            for k in keys:
                if (
                    k.state == KeyState.RATE_LIMITED
                    and k.rate_limit_reset > 0
                    and now >= k.rate_limit_reset
                ):
                    k.state = KeyState.ACTIVE
                    k.rate_limit_reset = 0.0
                    recovered += 1

        if recovered > 0:
            logger.info("%d anahtar kurtarildi", recovered)

        return recovered

    def get_key_info(
        self, provider: LLMProvider, key_id: str
    ) -> APIKeyInfo | None:
        """Anahtar bilgisini getirir.

        Args:
            provider: LLM saglayicisi.
            key_id: Anahtar ID'si.

        Returns:
            Anahtar bilgisi veya None.
        """
        prov = provider.value
        for k in self._keys.get(prov, []):
            if k.key_id == key_id:
                return k
        return None

    def list_keys(
        self, provider: LLMProvider | None = None
    ) -> list[APIKeyInfo]:
        """Anahtarlari listeler.

        Args:
            provider: Saglayici filtresi.

        Returns:
            Anahtar listesi.
        """
        if provider:
            return list(self._keys.get(provider.value, []))

        result: list[APIKeyInfo] = []
        for keys in self._keys.values():
            result.extend(keys)
        return result

    def get_active_count(self, provider: LLMProvider) -> int:
        """Aktif anahtar sayisini dondurur.

        Args:
            provider: LLM saglayicisi.

        Returns:
            Aktif anahtar sayisi.
        """
        keys = self._keys.get(provider.value, [])
        return sum(1 for k in keys if k.state == KeyState.ACTIVE)

    def get_cheapest_key(
        self, provider: LLMProvider
    ) -> APIKeyInfo | None:
        """En az harcamis anahtari dondurur.

        Args:
            provider: LLM saglayicisi.

        Returns:
            En az harcamis anahtar veya None.
        """
        active = [
            k for k in self._keys.get(provider.value, [])
            if k.state == KeyState.ACTIVE
        ]
        if not active:
            return None

        return min(active, key=lambda k: k.total_cost)

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        total_keys = sum(len(v) for v in self._keys.values())
        active_keys = sum(
            sum(1 for k in v if k.state == KeyState.ACTIVE)
            for v in self._keys.values()
        )
        total_cost = sum(
            k.total_cost
            for keys in self._keys.values()
            for k in keys
        )

        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "rotation_count": self._rotation_count,
            "total_cost": total_cost,
            "providers": list(self._keys.keys()),
        }
