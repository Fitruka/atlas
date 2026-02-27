"""Beceri pazar yeri.

Cok dilli becerilerin yayinlama, arama, indirme,
derecelendirme ve dogrulama islemleri.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.multilangruntime_models import (
    MarketplaceCategory,
    MarketplaceEntry,
    SkillLanguage,
)

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 2000
_MAX_REVIEWS_PER_ENTRY = 500
_MIN_RATING = 1.0
_MAX_RATING = 5.0


class SkillMarketplace:
    """Beceri pazar yeri sinifi.

    Cok dilli becerilerin yayinlama, arama,
    indirme, derecelendirme ve dogrulama
    islemlerini yonetir.

    Attributes:
        _entries: Pazar yeri kayitlari.
    """

    def __init__(self) -> None:
        """SkillMarketplace baslatir."""
        self._entries: dict[
            str, MarketplaceEntry
        ] = {}
        self._total_downloads: int = 0
        self._total_ratings: int = 0
        self._total_verifications: int = 0

        logger.info(
            "SkillMarketplace baslatildi"
        )

    # ---- Yayinlama ----

    def publish(
        self,
        skill_id: str,
        name: str,
        description: str = "",
        author: str = "",
        category: MarketplaceCategory = (
            MarketplaceCategory.UTILITY
        ),
        language: SkillLanguage = (
            SkillLanguage.PYTHON
        ),
        price: float = 0.0,
    ) -> MarketplaceEntry:
        """Beceriyi pazar yerine yayinlar.

        Args:
            skill_id: Kaynak beceri ID.
            name: Gorunen ad.
            description: Aciklama.
            author: Yazar.
            category: Kategori.
            language: Programlama dili.
            price: Fiyat (0 = ucretsiz).

        Returns:
            Pazar yeri kaydi.
        """
        if len(self._entries) >= _MAX_ENTRIES:
            logger.warning(
                "Maksimum giris sayisina ulasildi: "
                "%d",
                _MAX_ENTRIES,
            )
            oldest = min(
                self._entries.values(),
                key=lambda e: e.created_at,
            )
            del self._entries[oldest.id]

        entry = MarketplaceEntry(
            skill_id=skill_id,
            name=name,
            description=description,
            author=author,
            category=category,
            language=language,
            price=price,
        )

        self._entries[entry.id] = entry

        logger.info(
            "Beceri yayinlandi: %s (id=%s, "
            "skill=%s)",
            name,
            entry.id,
            skill_id,
        )
        return entry

    # ---- Arama ----

    def search(
        self,
        query: str = "",
        category: MarketplaceCategory | None = None,
        language: SkillLanguage | None = None,
        min_rating: float = 0.0,
    ) -> list[MarketplaceEntry]:
        """Pazar yerinde arama yapar.

        Args:
            query: Arama sorgusu.
            category: Kategori filtresi.
            language: Dil filtresi.
            min_rating: Minimum puan.

        Returns:
            Eslesen kayitlar.
        """
        results: list[MarketplaceEntry] = []
        query_lower = query.lower()

        for entry in self._entries.values():
            # Metin aramasi
            if query_lower:
                text = (
                    f"{entry.name} "
                    f"{entry.description} "
                    f"{entry.author}"
                ).lower()
                if query_lower not in text:
                    continue

            # Kategori filtresi
            if (
                category
                and entry.category != category
            ):
                continue

            # Dil filtresi
            if (
                language
                and entry.language != language
            ):
                continue

            # Minimum puan filtresi
            if entry.rating < min_rating:
                continue

            results.append(entry)

        # Puana gore sirala
        results.sort(
            key=lambda e: e.rating, reverse=True
        )

        logger.info(
            "Arama: q='%s', sonuc=%d",
            query,
            len(results),
        )
        return results

    # ---- Sorgulama ----

    def get_entry(
        self, entry_id: str
    ) -> MarketplaceEntry | None:
        """Pazar yeri kaydi getirir.

        Args:
            entry_id: Kayit ID.

        Returns:
            Kayit veya None.
        """
        return self._entries.get(entry_id)

    # ---- Indirme ----

    def download(
        self, entry_id: str
    ) -> dict[str, Any]:
        """Beceriyi indirir.

        Args:
            entry_id: Kayit ID.

        Returns:
            Indirme bilgileri.
        """
        entry = self._entries.get(entry_id)
        if not entry:
            logger.error(
                "Kayit bulunamadi: %s", entry_id
            )
            return {
                "success": False,
                "error": f"Entry not found: {entry_id}",
            }

        entry.downloads += 1
        self._total_downloads += 1

        logger.info(
            "Beceri indirildi: %s (toplam=%d)",
            entry.name,
            entry.downloads,
        )
        return {
            "success": True,
            "entry_id": entry_id,
            "skill_id": entry.skill_id,
            "name": entry.name,
            "language": entry.language.value,
            "downloads": entry.downloads,
        }

    # ---- Derecelendirme ----

    def rate(
        self,
        entry_id: str,
        score: float,
        review: str = "",
    ) -> bool:
        """Beceriyi derecelendirir.

        Args:
            entry_id: Kayit ID.
            score: Puan (1-5).
            review: Yorum metni.

        Returns:
            Basarili ise True.
        """
        entry = self._entries.get(entry_id)
        if not entry:
            logger.error(
                "Kayit bulunamadi: %s", entry_id
            )
            return False

        # Puan sinirlamasi
        clamped = max(
            _MIN_RATING,
            min(_MAX_RATING, score),
        )

        # Ortalama puan guncelleme
        total = (
            entry.rating * entry.rating_count
        )
        entry.rating_count += 1
        entry.rating = round(
            (total + clamped)
            / entry.rating_count,
            2,
        )

        # Yorum kaydi
        if review:
            if (
                len(entry.reviews)
                < _MAX_REVIEWS_PER_ENTRY
            ):
                entry.reviews.append(
                    {
                        "id": str(uuid4())[:8],
                        "score": clamped,
                        "review": review,
                        "timestamp": time.time(),
                    }
                )

        self._total_ratings += 1

        logger.info(
            "Beceri derecelendirildi: %s, "
            "puan=%.1f, ort=%.2f",
            entry.name,
            clamped,
            entry.rating,
        )
        return True

    # ---- Dogrulama ----

    def verify(self, entry_id: str) -> bool:
        """Beceriyi dogrulanmis olarak isaretler.

        Args:
            entry_id: Kayit ID.

        Returns:
            Basarili ise True.
        """
        entry = self._entries.get(entry_id)
        if not entry:
            logger.error(
                "Kayit bulunamadi: %s", entry_id
            )
            return False

        entry.verified = True
        self._total_verifications += 1

        logger.info(
            "Beceri dogrulandi: %s (id=%s)",
            entry.name,
            entry_id,
        )
        return True

    # ---- Listeleme ----

    def list_entries(
        self,
        category: MarketplaceCategory | None = None,
        verified_only: bool = False,
    ) -> list[MarketplaceEntry]:
        """Pazar yeri kayitlarini listeler.

        Args:
            category: Kategori filtresi.
            verified_only: Yalnizca dogrulananlar.

        Returns:
            Kayit listesi.
        """
        entries = list(self._entries.values())

        if category:
            entries = [
                e for e in entries
                if e.category == category
            ]

        if verified_only:
            entries = [
                e for e in entries if e.verified
            ]

        return entries

    def get_popular(
        self, limit: int = 10
    ) -> list[MarketplaceEntry]:
        """En populer becerileri listeler.

        Args:
            limit: Maksimum kayit sayisi.

        Returns:
            Populer kayitlar.
        """
        entries = list(self._entries.values())
        entries.sort(
            key=lambda e: e.downloads,
            reverse=True,
        )
        return entries[:limit]

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        verified = sum(
            1
            for e in self._entries.values()
            if e.verified
        )
        free = sum(
            1
            for e in self._entries.values()
            if e.price == 0.0
        )

        return {
            "total_entries": len(self._entries),
            "verified_entries": verified,
            "free_entries": free,
            "paid_entries": (
                len(self._entries) - free
            ),
            "total_downloads": (
                self._total_downloads
            ),
            "total_ratings": self._total_ratings,
            "total_verifications": (
                self._total_verifications
            ),
        }
