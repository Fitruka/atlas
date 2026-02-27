"""ATLAS Proactive Intelligence Engine Orkestratoru.

Tam proaktif istihbarat pipeline:
Tara -> Tespit Et -> Uyar -> Ozet Olustur.
Tum proaktif istihbarat bilesenlerini
koordine eder.
"""

import logging
import time
from typing import Any

from app.core.proactiveintel.context_aware_heartbeat import ContextAwareHeartbeat
from app.core.proactiveintel.predictive_alerts import PredictiveAlerts
from app.core.proactiveintel.pi_opportunity_detector import PIOpportunityDetector
from app.core.proactiveintel.pi_competitor_tracker import PICompetitorTracker
from app.core.proactiveintel.pi_sentiment_monitor import PISentimentMonitor
from app.core.proactiveintel.smart_digest import SmartDigest
from app.core.proactiveintel.pi_trend_analyzer import PITrendAnalyzer
from app.models.proactiveintel_models import (
    AlertPriority,
    DigestFrequency,
)

logger = logging.getLogger(__name__)


class ProactiveIntelOrchestrator:
    """Proactive Intelligence orkestratoru.

    Tum proaktif istihbarat bilesenlerini
    koordine eder: heartbeat, uyarilar,
    firsatlar, rakip, duygu, ozet, trend.

    Attributes:
        heartbeat: Baglama duyarli heartbeat.
        alerts: Tahminsel uyarilar.
        opportunity: Firsat tespiti.
        competitor: Rakip takibi.
        sentiment: Duygu izleme.
        digest: Akilli ozet.
        trends: Trend analizi.
    """

    def __init__(self) -> None:
        """Orkestratoru baslatir."""
        self.heartbeat = ContextAwareHeartbeat()
        self.alerts = PredictiveAlerts()
        self.opportunity = PIOpportunityDetector()
        self.competitor = PICompetitorTracker()
        self.sentiment = PISentimentMonitor()
        self.digest = SmartDigest()
        self.trends = PITrendAnalyzer()

        self._stats: dict[str, Any] = {
            "scans_run": 0,
            "digests_generated": 0,
            "total_opportunities": 0,
            "total_alerts": 0,
            "errors": 0,
        }
        logger.info(
            "ProactiveIntelOrchestrator baslatildi",
        )

    def run_scan(
        self,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Tam proaktif tarama calistirir.

        Args:
            context: Tarama baglami.

        Returns:
            Tarama sonuclari.
        """
        start = time.time()
        self._stats["scans_run"] += 1
        result: dict[str, Any] = {
            "success": False,
            "opportunities": [],
            "alerts": [],
            "competitor_events": [],
            "sentiment": {},
            "trends": [],
        }

        try:
            # 1. Firsat taramasi
            opportunities = self.opportunity.get_opportunities()
            result["opportunities"] = [
                {
                    "id": o.id,
                    "type": o.opportunity_type,
                    "title": o.title,
                    "value": o.estimated_value,
                    "confidence": o.confidence,
                }
                for o in opportunities
            ]
            self._stats["total_opportunities"] = len(
                opportunities,
            )

            # 2. Aktif uyarilar
            alerts = self.alerts.get_active_alerts()
            result["alerts"] = [
                {
                    "id": a.id,
                    "title": a.title,
                    "priority": a.priority,
                    "confidence": a.confidence,
                }
                for a in alerts
            ]
            self._stats["total_alerts"] = len(alerts)

            # 3. Rakip olaylari
            events = self.competitor.get_recent_activity(
                limit=10,
            )
            result["competitor_events"] = [
                {
                    "id": e.get("id", ""),
                    "competitor": e.get(
                        "competitor_name", "",
                    ),
                    "action": e.get("action", ""),
                    "impact": e.get(
                        "impact_level", "",
                    ),
                }
                for e in events
            ]

            # 4. Duygu ozeti
            try:
                avg_sent = (
                    self.sentiment.get_average_sentiment()
                )
                result["sentiment"] = {
                    "average_score": avg_sent,
                    "status": (
                        "positive" if avg_sent > 0.2
                        else "negative" if avg_sent < -0.2
                        else "neutral"
                    ),
                }
            except Exception:
                result["sentiment"] = {
                    "average_score": 0.0,
                    "status": "unknown",
                }

            # 5. Trend ozeti
            rising = self.trends.get_rising_trends()
            declining = self.trends.get_declining_trends()
            result["trends"] = {
                "rising_count": len(rising),
                "declining_count": len(declining),
                "rising": [
                    {"name": t.name, "momentum": t.momentum}
                    for t in rising[:5]
                ],
                "declining": [
                    {"name": t.name, "momentum": t.momentum}
                    for t in declining[:5]
                ],
            }

            # 6. Heartbeat kontrolu
            if context:
                should_send = self.heartbeat.should_send(
                    context,
                )
                result["heartbeat_due"] = should_send

            result["success"] = True
            logger.info(
                "Proaktif tarama tamamlandi: "
                "%d firsat, %d uyari",
                len(opportunities), len(alerts),
            )

        except Exception as exc:
            self._stats["errors"] += 1
            result["error"] = str(exc)
            logger.error("Tarama hatasi: %s", exc)

        result["elapsed_ms"] = round(
            (time.time() - start) * 1000, 2,
        )
        return result

    def generate_daily_digest(
        self,
        recipient: str | None = None,
    ) -> dict[str, Any]:
        """Gunluk ozet raporu olusturur.

        Args:
            recipient: Alici.

        Returns:
            Ozet sonucu.
        """
        start = time.time()
        self._stats["digests_generated"] += 1
        result: dict[str, Any] = {
            "success": False,
        }

        try:
            # Firsatlari ekle
            for opp in self.opportunity.get_opportunities():
                self.digest.add_entry(
                    title=opp.title,
                    summary=opp.description,
                    category="opportunity",
                    priority=AlertPriority.MEDIUM,
                    action_required=True,
                    data={"value": opp.estimated_value},
                )

            # Uyarilari ekle
            for alert in self.alerts.get_active_alerts():
                self.digest.add_entry(
                    title=alert.title,
                    summary=alert.description,
                    category="alert",
                    priority=alert.priority,
                    action_required=True,
                    data={
                        "confidence": alert.confidence,
                    },
                )

            # Rakip olaylarini ekle
            for event in self.competitor.get_recent_activity(
                limit=5,
            ):
                self.digest.add_entry(
                    title=(
                        f"{event.get('competitor_name', '')}: "
                        f"{event.get('action', '')}"
                    ),
                    summary=event.get(
                        "description", "",
                    ),
                    category="competitor",
                    priority=AlertPriority.LOW,
                )

            # Ozet olustur
            digest = self.digest.generate(
                frequency=DigestFrequency.DAILY,
                recipient=recipient,
            )

            result["success"] = True
            result["digest_id"] = digest.id
            result["entries_count"] = len(
                digest.entries,
            )
            result["highlights_count"] = len(
                digest.highlights,
            )

        except Exception as exc:
            self._stats["errors"] += 1
            result["error"] = str(exc)
            logger.error("Ozet hatasi: %s", exc)

        result["elapsed_ms"] = round(
            (time.time() - start) * 1000, 2,
        )
        return result

    def get_intelligence_summary(
        self,
    ) -> dict[str, Any]:
        """Tum istihbarat ozetini dondurur.

        Returns:
            Birlesik istihbarat ozeti.
        """
        return {
            "opportunities": {
                "total": len(
                    self.opportunity.get_opportunities(),
                ),
                "top": [
                    {
                        "title": o.title,
                        "value": o.estimated_value,
                    }
                    for o in self.opportunity.get_opportunities()[:3]
                ],
            },
            "alerts": {
                "active": len(
                    self.alerts.get_active_alerts(),
                ),
                "critical": len(
                    self.alerts.get_active_alerts(
                        priority=AlertPriority.CRITICAL,
                    ),
                ),
            },
            "competitors": {
                "tracked": len(
                    self.competitor.list_competitors(),
                ),
                "recent_events": len(
                    self.competitor.get_recent_activity(
                        limit=100,
                    ),
                ),
            },
            "sentiment": {
                "average": (
                    self.sentiment.get_average_sentiment()
                ),
            },
            "trends": {
                "total": len(
                    self.trends.get_all_trends(),
                ),
                "rising": len(
                    self.trends.get_rising_trends(),
                ),
                "declining": len(
                    self.trends.get_declining_trends(),
                ),
            },
        }

    def check_health(self) -> dict[str, Any]:
        """Sistem sagligini kontrol eder.

        Returns:
            Saglik durumu.
        """
        critical_alerts = self.alerts.get_active_alerts(
            priority=AlertPriority.CRITICAL,
        )
        negative = self.sentiment.get_negative_alerts(
            threshold=-0.5,
        )
        volatile = self.trends.get_volatile_trends()

        issues: list[str] = []
        if critical_alerts:
            issues.append(
                f"{len(critical_alerts)} kritik uyari",
            )
        if negative:
            issues.append(
                f"{len(negative)} negatif duygu",
            )
        if volatile:
            issues.append(
                f"{len(volatile)} oynak trend",
            )

        return {
            "status": (
                "healthy" if not issues else "attention_needed"
            ),
            "issues": issues,
            "critical_alerts": len(critical_alerts),
            "negative_sentiment": len(negative),
            "volatile_trends": len(volatile),
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Orkestrator istatistikleri.
        """
        return {
            **self._stats,
            "heartbeat": self.heartbeat.get_stats(),
            "alerts": self.alerts.get_stats(),
            "opportunity": self.opportunity.get_stats(),
            "competitor": self.competitor.get_stats(),
            "sentiment": self.sentiment.get_stats(),
            "digest": self.digest.get_stats(),
            "trends": self.trends.get_stats(),
        }
