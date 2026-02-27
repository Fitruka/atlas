"""ATLAS Verified Marketplace modulu.

Dogrulanmis agent pazaryeri: listeleme, arama,
yayinlama, askiya alma, arsivleme, one cikanlar.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.agentmarket_models import (
    ListingStatus,
    MarketplaceListing,
    RevenueModel,
)

logger = logging.getLogger(__name__)

_DEFAULT_FEATURED_LIMIT = 10
_MIN_RATING_FOR_FEATURED = 4.0
_MIN_DOWNLOADS_FOR_FEATURED = 50


class VerifiedMarketplace:
    """Dogrulanmis agent pazaryeri.

    Listeleme, arama, yayinlama ve
    yasam dongusu yonetimi saglar.

    Attributes:
        _listings: Listeleme deposu.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Pazaryerini baslatir."""
        self._listings: dict[
            str, MarketplaceListing
        ] = {}
        self._stats = {
            "submitted": 0,
            "published": 0,
            "suspended": 0,
            "archived": 0,
            "searches": 0,
        }

        logger.info(
            "VerifiedMarketplace baslatildi",
        )

    def submit_listing(
        self,
        name: str,
        description: str,
        author_id: str,
        version: str = "1.0.0",
        category: str = "general",
        tags: list[str] | None = None,
        price: float = 0.0,
        revenue_model: RevenueModel = RevenueModel.FREE,
    ) -> MarketplaceListing:
        """Yeni listeleme gonderir.

        Args:
            name: Listeleme adi.
            description: Aciklama.
            author_id: Yazar ID.
            version: Surum.
            category: Kategori.
            tags: Etiketler.
            price: Fiyat.
            revenue_model: Gelir modeli.

        Returns:
            Olusturulan listeleme.
        """
        listing = MarketplaceListing(
            name=name,
            description=description,
            author_id=author_id,
            version=version,
            category=category,
            tags=tags or [],
            price=price,
            revenue_model=revenue_model,
            status=ListingStatus.PENDING_REVIEW,
        )

        self._listings[listing.id] = listing
        self._stats["submitted"] += 1

        logger.info(
            "Listeleme gonderildi: %s (%s)",
            name, listing.id,
        )
        return listing

    def get_listing(
        self,
        listing_id: str,
    ) -> MarketplaceListing | None:
        """Listeleme getirir.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Listeleme veya None.
        """
        return self._listings.get(listing_id)

    def update_listing(
        self,
        listing_id: str,
        **updates: Any,
    ) -> MarketplaceListing | None:
        """Listeleme gunceller.

        Args:
            listing_id: Listeleme ID.
            **updates: Guncellenecek alanlar.

        Returns:
            Guncellenmis listeleme veya None.
        """
        listing = self._listings.get(
            listing_id,
        )
        if not listing:
            return None

        allowed = {
            "name", "description", "version",
            "category", "tags", "price",
            "revenue_model", "status",
            "avg_rating", "download_count",
        }

        for key, value in updates.items():
            if key in allowed and hasattr(
                listing, key,
            ):
                setattr(listing, key, value)

        listing.updated_at = datetime.now(
            timezone.utc,
        )

        logger.info(
            "Listeleme guncellendi: %s",
            listing_id,
        )
        return listing

    def search(
        self,
        query: str = "",
        category: str | None = None,
        tags: list[str] | None = None,
        min_rating: float = 0.0,
        max_price: float | None = None,
        status: ListingStatus | None = None,
    ) -> list[MarketplaceListing]:
        """Listeleme arar.

        Args:
            query: Arama sorgusu.
            category: Kategori filtresi.
            tags: Etiket filtresi.
            min_rating: Minimum puan.
            max_price: Maksimum fiyat.
            status: Durum filtresi.

        Returns:
            Eslesen listeler.
        """
        self._stats["searches"] += 1
        results = []

        for listing in self._listings.values():
            # Durum filtresi
            if status and listing.status != status:
                continue

            # Sadece yayinlanmis goster (varsayilan)
            if not status and listing.status != (
                ListingStatus.PUBLISHED
            ):
                continue

            # Sorgu filtresi
            if query:
                q_lower = query.lower()
                if (
                    q_lower not in listing.name.lower()
                    and q_lower not in listing.description.lower()
                ):
                    continue

            # Kategori filtresi
            if category and listing.category != category:
                continue

            # Etiket filtresi
            if tags:
                if not any(
                    t in listing.tags
                    for t in tags
                ):
                    continue

            # Puan filtresi
            if listing.avg_rating < min_rating:
                continue

            # Fiyat filtresi
            if (
                max_price is not None
                and listing.price > max_price
            ):
                continue

            results.append(listing)

        # Puana gore sirala
        results.sort(
            key=lambda l: l.avg_rating,
            reverse=True,
        )

        return results

    def publish(
        self,
        listing_id: str,
    ) -> bool:
        """Listelemeyi yayinlar.

        Sadece APPROVED durumundakiler
        yayinlanabilir.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Basarili ise True.
        """
        listing = self._listings.get(
            listing_id,
        )
        if not listing:
            return False

        if listing.status != (
            ListingStatus.APPROVED
        ):
            logger.warning(
                "Yayinlanamaz, durum: %s",
                listing.status,
            )
            return False

        listing.status = ListingStatus.PUBLISHED
        listing.updated_at = datetime.now(
            timezone.utc,
        )
        self._stats["published"] += 1

        logger.info(
            "Listeleme yayinlandi: %s",
            listing_id,
        )
        return True

    def suspend(
        self,
        listing_id: str,
        reason: str = "",
    ) -> bool:
        """Listelemeyi askiya alir.

        Args:
            listing_id: Listeleme ID.
            reason: Askiya alma nedeni.

        Returns:
            Basarili ise True.
        """
        listing = self._listings.get(
            listing_id,
        )
        if not listing:
            return False

        listing.status = ListingStatus.SUSPENDED
        listing.updated_at = datetime.now(
            timezone.utc,
        )
        self._stats["suspended"] += 1

        logger.info(
            "Listeleme askiya alindi: %s, neden: %s",
            listing_id, reason,
        )
        return True

    def archive(
        self,
        listing_id: str,
    ) -> bool:
        """Listelemeyi arsivler.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Basarili ise True.
        """
        listing = self._listings.get(
            listing_id,
        )
        if not listing:
            return False

        listing.status = ListingStatus.ARCHIVED
        listing.updated_at = datetime.now(
            timezone.utc,
        )
        self._stats["archived"] += 1

        logger.info(
            "Listeleme arsivlendi: %s",
            listing_id,
        )
        return True

    def get_featured(
        self,
        limit: int = _DEFAULT_FEATURED_LIMIT,
    ) -> list[MarketplaceListing]:
        """One cikan listelemeler getirir.

        Args:
            limit: Maksimum sonuc.

        Returns:
            One cikan listeler.
        """
        featured = [
            l for l in self._listings.values()
            if (
                l.status == ListingStatus.PUBLISHED
                and l.avg_rating
                >= _MIN_RATING_FOR_FEATURED
                and l.download_count
                >= _MIN_DOWNLOADS_FOR_FEATURED
            )
        ]

        featured.sort(
            key=lambda l: (
                l.avg_rating * l.download_count
            ),
            reverse=True,
        )

        return featured[:limit]

    def get_by_author(
        self,
        author_id: str,
    ) -> list[MarketplaceListing]:
        """Yazar listelemeleri getirir.

        Args:
            author_id: Yazar ID.

        Returns:
            Yazar listeleri.
        """
        return [
            l for l in self._listings.values()
            if l.author_id == author_id
        ]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        status_counts: dict[str, int] = {}
        for listing in self._listings.values():
            s = listing.status.value
            status_counts[s] = (
                status_counts.get(s, 0) + 1
            )

        return {
            "total_listings": len(
                self._listings,
            ),
            "status_distribution": status_counts,
            **self._stats,
        }
