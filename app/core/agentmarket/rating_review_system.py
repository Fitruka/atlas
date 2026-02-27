"""ATLAS Rating & Review System modulu.

Degerlendirme ve yorum sistemi: puan, yorum,
isaretleme, onaylama, faydali bulma, dagilim.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.agentmarket_models import (
    ReviewStatus,
    UserReview,
)

logger = logging.getLogger(__name__)

_MIN_RATING = 1.0
_MAX_RATING = 5.0
_DEFAULT_MIN_RATING = 0.0


class RatingReviewSystem:
    """Degerlendirme ve yorum sistemi.

    Kullanici puanlari, yorumlar ve
    moderasyon islemleri saglar.

    Attributes:
        _reviews: Yorum deposu.
        _listing_reviews: Listeleme yorum indeksi.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Degerlendirme sistemini baslatir."""
        self._reviews: dict[
            str, UserReview
        ] = {}
        self._listing_reviews: dict[
            str, list[str]
        ] = {}
        self._stats = {
            "reviews_added": 0,
            "reviews_flagged": 0,
            "reviews_approved": 0,
            "reviews_removed": 0,
            "helpful_marks": 0,
        }

        logger.info(
            "RatingReviewSystem baslatildi",
        )

    def add_review(
        self,
        listing_id: str,
        user_id: str,
        rating: float,
        title: str = "",
        comment: str = "",
    ) -> UserReview:
        """Yorum ekler.

        Args:
            listing_id: Listeleme ID.
            user_id: Kullanici ID.
            rating: Puan (1-5).
            title: Baslik.
            comment: Yorum.

        Returns:
            Olusan yorum.
        """
        # Puani sinirla
        clamped_rating = max(
            _MIN_RATING,
            min(_MAX_RATING, rating),
        )

        review = UserReview(
            listing_id=listing_id,
            user_id=user_id,
            rating=clamped_rating,
            title=title,
            comment=comment,
            status=ReviewStatus.PENDING,
        )

        self._reviews[review.id] = review

        if listing_id not in (
            self._listing_reviews
        ):
            self._listing_reviews[
                listing_id
            ] = []
        self._listing_reviews[
            listing_id
        ].append(review.id)

        self._stats["reviews_added"] += 1

        logger.info(
            "Yorum eklendi: %s, puan: %.1f",
            listing_id, clamped_rating,
        )
        return review

    def get_reviews(
        self,
        listing_id: str,
        status: ReviewStatus | None = None,
        min_rating: float = _DEFAULT_MIN_RATING,
    ) -> list[UserReview]:
        """Listeleme yorumlarini getirir.

        Args:
            listing_id: Listeleme ID.
            status: Durum filtresi.
            min_rating: Minimum puan.

        Returns:
            Yorum listesi.
        """
        review_ids = (
            self._listing_reviews.get(
                listing_id, [],
            )
        )

        results = []
        for rid in review_ids:
            review = self._reviews.get(rid)
            if not review:
                continue
            if (
                status
                and review.status != status
            ):
                continue
            if review.rating < min_rating:
                continue
            results.append(review)

        # Yeniden eskiye sirala
        results.sort(
            key=lambda r: r.created_at,
            reverse=True,
        )
        return results

    def get_review(
        self,
        review_id: str,
    ) -> UserReview | None:
        """Yorum getirir.

        Args:
            review_id: Yorum ID.

        Returns:
            Yorum veya None.
        """
        return self._reviews.get(review_id)

    def flag_review(
        self,
        review_id: str,
        reason: str = "",
    ) -> bool:
        """Yorumu isaretler.

        Args:
            review_id: Yorum ID.
            reason: Isaretleme nedeni.

        Returns:
            Basarili ise True.
        """
        review = self._reviews.get(review_id)
        if not review:
            return False

        review.status = ReviewStatus.FLAGGED
        self._stats["reviews_flagged"] += 1

        logger.info(
            "Yorum isaretlendi: %s, neden: %s",
            review_id, reason,
        )
        return True

    def approve_review(
        self,
        review_id: str,
    ) -> bool:
        """Yorumu onaylar.

        Args:
            review_id: Yorum ID.

        Returns:
            Basarili ise True.
        """
        review = self._reviews.get(review_id)
        if not review:
            return False

        review.status = ReviewStatus.APPROVED
        self._stats["reviews_approved"] += 1

        logger.info(
            "Yorum onaylandi: %s", review_id,
        )
        return True

    def remove_review(
        self,
        review_id: str,
    ) -> bool:
        """Yorumu kaldirir.

        Args:
            review_id: Yorum ID.

        Returns:
            Basarili ise True.
        """
        review = self._reviews.get(review_id)
        if not review:
            return False

        review.status = ReviewStatus.REMOVED
        self._stats["reviews_removed"] += 1

        logger.info(
            "Yorum kaldirildi: %s", review_id,
        )
        return True

    def mark_helpful(
        self,
        review_id: str,
    ) -> bool:
        """Yorumu faydali olarak isaretle.

        Args:
            review_id: Yorum ID.

        Returns:
            Basarili ise True.
        """
        review = self._reviews.get(review_id)
        if not review:
            return False

        review.helpful_count += 1
        self._stats["helpful_marks"] += 1

        return True

    def get_average_rating(
        self,
        listing_id: str,
    ) -> float:
        """Ortalama puani hesaplar.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Ortalama puan.
        """
        review_ids = (
            self._listing_reviews.get(
                listing_id, [],
            )
        )

        active_reviews = [
            self._reviews[rid]
            for rid in review_ids
            if rid in self._reviews
            and self._reviews[rid].status
            in (
                ReviewStatus.PENDING,
                ReviewStatus.APPROVED,
            )
        ]

        if not active_reviews:
            return 0.0

        total = sum(
            r.rating for r in active_reviews
        )
        return round(
            total / len(active_reviews), 2,
        )

    def get_rating_distribution(
        self,
        listing_id: str,
    ) -> dict[int, int]:
        """Puan dagilimini hesaplar.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Yildiz: sayi eslesmesi.
        """
        distribution = {
            1: 0, 2: 0, 3: 0, 4: 0, 5: 0,
        }

        review_ids = (
            self._listing_reviews.get(
                listing_id, [],
            )
        )

        for rid in review_ids:
            review = self._reviews.get(rid)
            if not review:
                continue
            if review.status == (
                ReviewStatus.REMOVED
            ):
                continue
            star = int(review.rating)
            star = max(1, min(5, star))
            distribution[star] += 1

        return distribution

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        total = len(self._reviews)
        active = sum(
            1 for r in self._reviews.values()
            if r.status in (
                ReviewStatus.PENDING,
                ReviewStatus.APPROVED,
            )
        )

        return {
            "total_reviews": total,
            "active_reviews": active,
            "listings_reviewed": len(
                self._listing_reviews,
            ),
            **self._stats,
        }
