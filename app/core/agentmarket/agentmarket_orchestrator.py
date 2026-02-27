"""ATLAS Agent Market Orkestrator modulu.

Tum pazaryeri bilesenlerini koordine eder:
Submit > Audit > Approve/Reject > Install.
"""

import logging
import time
from typing import Any

from app.core.agentmarket.dependency_resolver import (
    DependencyResolver,
)
from app.core.agentmarket.rating_review_system import (
    RatingReviewSystem,
)
from app.core.agentmarket.revenue_sharing import (
    RevenueSharing,
)
from app.core.agentmarket.security_audit_pipeline import (
    SecurityAuditPipeline,
)
from app.core.agentmarket.skill_analytics import (
    SkillAnalytics,
)
from app.core.agentmarket.verified_marketplace import (
    VerifiedMarketplace,
)
from app.models.agentmarket_models import (
    ListingStatus,
    RevenueModel,
)

logger = logging.getLogger(__name__)


class AgentMarketOrchestrator:
    """Agent Market orkestrator.

    Tum pazaryeri bilesenlerini koordine eder.

    Attributes:
        marketplace: Dogrulanmis pazaryeri.
        audit_pipeline: Guvenlik denetim hatti.
        reviews: Degerlendirme sistemi.
        revenue: Gelir paylasimi.
        deps: Bagimlilik cozumleyici.
        analytics: Beceri analitigi.
    """

    def __init__(self) -> None:
        """Orkestratoru baslatir."""
        self.marketplace = VerifiedMarketplace()
        self.audit_pipeline = (
            SecurityAuditPipeline()
        )
        self.reviews = RatingReviewSystem()
        self.revenue = RevenueSharing()
        self.deps = DependencyResolver()
        self.analytics = SkillAnalytics()

        self._stats = {
            "submit_and_audit_count": 0,
            "installs_processed": 0,
            "auto_approved": 0,
            "auto_rejected": 0,
        }

        logger.info(
            "AgentMarketOrchestrator baslatildi",
        )

    def submit_and_audit(
        self,
        name: str,
        description: str,
        author_id: str,
        version: str = "1.0.0",
        category: str = "general",
        tags: list[str] | None = None,
        price: float = 0.0,
        code: str = "",
        language: str = "python",
        revenue_model: RevenueModel = RevenueModel.FREE,
    ) -> dict[str, Any]:
        """Gonderim ve denetim pipeline.

        1. Listeleme olusturulur
        2. Guvenlik denetimi yapilir
        3. Sonuca gore otomatik onay/red

        Args:
            name: Listeleme adi.
            description: Aciklama.
            author_id: Yazar ID.
            version: Surum.
            category: Kategori.
            tags: Etiketler.
            price: Fiyat.
            code: Denetlenecek kod.
            language: Programlama dili.
            revenue_model: Gelir modeli.

        Returns:
            Pipeline sonucu.
        """
        # 1. Listeleme olustur
        listing = self.marketplace.submit_listing(
            name=name,
            description=description,
            author_id=author_id,
            version=version,
            category=category,
            tags=tags,
            price=price,
            revenue_model=revenue_model,
        )

        # 2. Guvenlik denetimi
        audit_report = self.audit_pipeline.audit(
            listing_id=listing.id,
            code=code,
            language=language,
        )

        # 3. Sonuca gore onay/red
        if audit_report.passed:
            self.marketplace.update_listing(
                listing.id,
                status=ListingStatus.APPROVED,
            )
            self._stats["auto_approved"] += 1

            # Gelir yapilandirmasi
            if price > 0:
                self.revenue.configure(
                    listing.id,
                    author_id,
                )

            status = "approved"
        else:
            self.marketplace.update_listing(
                listing.id,
                status=ListingStatus.REJECTED,
            )
            self._stats["auto_rejected"] += 1
            status = "rejected"

        self._stats[
            "submit_and_audit_count"
        ] += 1

        logger.info(
            "Submit-and-audit tamamlandi: "
            "%s (%s) -> %s",
            name, listing.id, status,
        )

        return {
            "listing_id": listing.id,
            "listing_name": name,
            "status": status,
            "audit_result": (
                audit_report.result.value
            ),
            "audit_passed": audit_report.passed,
            "critical_issues": (
                audit_report.critical_count
            ),
            "warning_issues": (
                audit_report.warning_count
            ),
            "total_issues": len(
                audit_report.issues,
            ),
            "report_id": audit_report.id,
        }

    def install_listing(
        self,
        listing_id: str,
        user_id: str,
        dependencies: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Listeleme kurulumu.

        1. Listeleme kontrol edilir
        2. Bagimliliklar cozulur
        3. Kurulum kaydedilir
        4. Gelir islem edilir

        Args:
            listing_id: Listeleme ID.
            user_id: Kullanici ID.
            dependencies: Bagimlilik listesi.

        Returns:
            Kurulum sonucu.
        """
        # 1. Listeleme kontrol
        listing = self.marketplace.get_listing(
            listing_id,
        )
        if not listing:
            return {
                "success": False,
                "error": "listing_not_found",
            }

        if listing.status != (
            ListingStatus.PUBLISHED
        ):
            return {
                "success": False,
                "error": "listing_not_published",
                "current_status": (
                    listing.status.value
                ),
            }

        # 2. Bagimlilik cozumleme
        dep_result = None
        if dependencies:
            self.deps.analyze(
                listing_id, dependencies,
            )
            dep_result = self.deps.resolve(
                listing_id,
            )
            if not dep_result["fully_resolved"]:
                return {
                    "success": False,
                    "error": (
                        "dependency_resolution_failed"
                    ),
                    "unresolved": dep_result[
                        "unresolved"
                    ],
                }

        # 3. Kurulum kaydi
        self.analytics.record_install(
            listing_id,
        )

        # Download sayacini artir
        self.marketplace.update_listing(
            listing_id,
            download_count=(
                listing.download_count + 1
            ),
        )

        # 4. Gelir isleme (ucretli ise)
        revenue_record = None
        if listing.price > 0:
            revenue_record = (
                self.revenue.record_transaction(
                    listing_id,
                    listing.price,
                )
            )

        self._stats[
            "installs_processed"
        ] += 1

        logger.info(
            "Kurulum tamamlandi: %s, "
            "kullanici: %s",
            listing_id, user_id,
        )

        return {
            "success": True,
            "listing_id": listing_id,
            "listing_name": listing.name,
            "user_id": user_id,
            "version": listing.version,
            "dependencies_resolved": (
                dep_result is not None
                and dep_result["fully_resolved"]
            ) if dep_result else True,
            "revenue_recorded": (
                revenue_record is not None
            ),
        }

    def get_marketplace_overview(
        self,
    ) -> dict[str, Any]:
        """Pazaryeri genel gorunumu.

        Returns:
            Genel bilgi.
        """
        mp_stats = self.marketplace.get_stats()
        review_stats = self.reviews.get_stats()
        revenue_stats = self.revenue.get_stats()
        analytics_stats = (
            self.analytics.get_stats()
        )

        trending = self.analytics.get_trending(
            limit=5,
        )

        return {
            "listings": {
                "total": mp_stats.get(
                    "total_listings", 0,
                ),
                "published": mp_stats.get(
                    "status_distribution", {},
                ).get("published", 0),
                "pending": mp_stats.get(
                    "status_distribution", {},
                ).get("pending_review", 0),
            },
            "reviews": {
                "total": review_stats.get(
                    "total_reviews", 0,
                ),
                "active": review_stats.get(
                    "active_reviews", 0,
                ),
            },
            "revenue": {
                "total_gross": revenue_stats.get(
                    "total_gross", 0.0,
                ),
                "platform_fees": (
                    revenue_stats.get(
                        "total_platform_fee",
                        0.0,
                    )
                ),
                "transactions": (
                    revenue_stats.get(
                        "transactions", 0,
                    )
                ),
            },
            "analytics": {
                "total_installs": (
                    analytics_stats.get(
                        "total_installs", 0,
                    )
                ),
                "net_installs": (
                    analytics_stats.get(
                        "net_installs", 0,
                    )
                ),
                "tracked_listings": (
                    analytics_stats.get(
                        "tracked_listings", 0,
                    )
                ),
            },
            "trending": trending,
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        return {
            "marketplace": (
                self.marketplace.get_stats()
            ),
            "audit": (
                self.audit_pipeline.get_stats()
            ),
            "reviews": (
                self.reviews.get_stats()
            ),
            "revenue": (
                self.revenue.get_stats()
            ),
            "dependencies": (
                self.deps.get_stats()
            ),
            "analytics": (
                self.analytics.get_stats()
            ),
            "orchestrator": self._stats,
        }
