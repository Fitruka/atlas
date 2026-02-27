"""ATLAS Cost Control & Budget Engine Orkestratörü.

Tam maliyet kontrol pipeline,
Track -> Limit -> Alert -> Optimize -> Project,
entegrasyon, analitik.
"""

import logging
import time
from typing import Any

from app.core.costcontrol.realtime_cost_tracker import RealTimeCostTracker
from app.core.costcontrol.budget_limiter import BudgetLimiter
from app.core.costcontrol.cost_alert_system import CostAlertSystem
from app.core.costcontrol.smart_model_router import SmartModelRouter
from app.core.costcontrol.heartbeat_cost_optimizer import HeartbeatCostOptimizer
from app.core.costcontrol.token_compression_engine import TokenCompressionEngine
from app.core.costcontrol.cost_projection import CostProjection
from app.core.costcontrol.provider_arbitrage import ProviderArbitrage
from app.core.costcontrol.cost_per_template import CostPerTemplate

logger = logging.getLogger(__name__)


class CostControlOrchestrator:
    """Cost Control & Budget Engine orkestratörü.

    Tüm maliyet kontrol bileşenlerini
    koordine eder:
    takip, limit, uyarı, yönlendirme, optimizasyon.

    Attributes:
        tracker: Gerçek zamanlı maliyet takipçisi.
        limiter: Bütçe sınırlayıcı.
        alerts: Maliyet uyarı sistemi.
        router: Akıllı model yönlendirici.
        heartbeat: Heartbeat optimizasyonu.
        compression: Token sıkıştırma.
        projection: Maliyet projeksiyonu.
        arbitrage: Sağlayıcı arbitrajı.
        template_cost: Şablon maliyet analizi.
    """

    def __init__(self) -> None:
        """Orkestratörü başlatır."""
        self.tracker = RealTimeCostTracker()
        self.limiter = BudgetLimiter()
        self.alerts = CostAlertSystem()
        self.router = SmartModelRouter()
        self.heartbeat = HeartbeatCostOptimizer()
        self.compression = TokenCompressionEngine()
        self.projection = CostProjection()
        self.arbitrage = ProviderArbitrage()
        self.template_cost = CostPerTemplate()

        self._stats = {
            "pipelines_run": 0,
            "requests_allowed": 0,
            "requests_blocked": 0,
        }

        logger.info("CostControlOrchestrator baslatildi")

    def process_request(
        self,
        session_id: str,
        task_type: str = "",
        complexity: str = "moderate",
        input_tokens: int = 0,
        output_tokens: int = 0,
        model_name: str = "",
        template_id: str = "",
    ) -> dict[str, Any]:
        """İsteği tam pipeline ile işle.

        Track -> Budget Check -> Route -> Record -> Alert.

        Args:
            session_id: Oturum ID.
            task_type: Görev tipi.
            complexity: Karmaşıklık.
            input_tokens: Girdi token.
            output_tokens: Çıktı token.
            model_name: Model adı (boşsa router seçer).
            template_id: Şablon ID.

        Returns:
            İşleme sonucu.
        """
        self._stats["pipelines_run"] += 1

        # 1. Model yönlendirme (model belirtilmemişse)
        route_info = None
        if not model_name:
            route = self.router.route(
                task_type=task_type,
                complexity=complexity,
            )
            model_name = route.selected_model or "claude-sonnet-4"
            route_info = {
                "model": route.selected_model,
                "provider": route.selected_provider,
                "estimated_cost": route.estimated_cost,
            }

        # 2. Bütçe kontrolü (tahmini maliyet ile)
        estimated_cost = 0.0
        if input_tokens > 0 or output_tokens > 0:
            entry = self.tracker.record(
                session_id=session_id,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                task_type=task_type,
                template_id=template_id,
            )
            estimated_cost = entry.cost_usd

        budget_check = self.limiter.check_budget(estimated_cost)

        if budget_check["blocked"]:
            self._stats["requests_blocked"] += 1
            # Uyarı oluştur
            self.alerts.create_alert(
                severity="emergency",
                title="Butce asimi - istek engellendi",
                message=f"Session {session_id}: ${estimated_cost:.4f} engellendi",
                current_spend=estimated_cost,
            )
            return {
                "allowed": False,
                "blocked": True,
                "reason": "budget_exceeded",
                "alerts": budget_check["alerts"],
            }

        # 3. Harcama kaydet
        if estimated_cost > 0:
            self.limiter.add_spend(estimated_cost)

        # 4. Şablon maliyet kaydı
        if template_id:
            self.template_cost.record_cost(
                template_id=template_id,
                template_name=template_id,
                cost_usd=estimated_cost,
                tokens=input_tokens + output_tokens,
                model_name=model_name,
            )

        # 5. Uyarı kontrolü
        total_cost = self.tracker.get_total_cost()
        alerts = self.alerts.check_and_alert(total_cost)

        self._stats["requests_allowed"] += 1

        return {
            "allowed": True,
            "blocked": False,
            "model": model_name,
            "cost_usd": estimated_cost,
            "total_cost": total_cost,
            "route": route_info,
            "alerts": [a.title for a in alerts] if alerts else [],
        }

    def setup_default_budgets(
        self,
        daily_limit: float = 10.0,
        monthly_limit: float = 200.0,
    ) -> dict[str, Any]:
        """Varsayılan bütçe limitleri kur.

        Args:
            daily_limit: Günlük limit (USD).
            monthly_limit: Aylık limit (USD).

        Returns:
            Kurulan bütçeler.
        """
        daily = self.limiter.set_limit(
            name="Gunluk Limit",
            period="daily",
            limit_usd=daily_limit,
        )

        monthly = self.limiter.set_limit(
            name="Aylik Limit",
            period="monthly",
            limit_usd=monthly_limit,
        )

        # Uyarı kuralları
        self.alerts.add_rule(
            name="Gunluk %80",
            threshold_usd=daily_limit * 0.8,
            severity="warning",
            period="daily",
        )
        self.alerts.add_rule(
            name="Gunluk %95",
            threshold_usd=daily_limit * 0.95,
            severity="critical",
            period="daily",
        )

        return {
            "daily_budget_id": daily.limit_id,
            "monthly_budget_id": monthly.limit_id,
        }

    def get_cost_summary(self) -> dict[str, Any]:
        """Maliyet özeti getir.

        Returns:
            Maliyet özeti.
        """
        tracker_stats = self.tracker.get_stats()
        return {
            "total_cost_usd": tracker_stats["total_cost_usd"],
            "total_tokens": tracker_stats["total_tokens"],
            "total_entries": tracker_stats["total_entries"],
            "by_model": tracker_stats["by_model"],
            "budgets": [b.model_dump() for b in self.limiter.list_budgets()],
            "pending_alerts": len(self.alerts.get_unacknowledged()),
            "heartbeat_savings": self.heartbeat.get_stats()["total_saved_usd"],
        }

    def get_stats(self) -> dict[str, Any]:
        """Tüm istatistikleri döndürür."""
        return {
            "orchestrator": self._stats,
            "tracker": self.tracker.get_stats(),
            "limiter": self.limiter.get_stats(),
            "alerts": self.alerts.get_stats(),
            "router": self.router.get_stats(),
            "heartbeat": self.heartbeat.get_stats(),
            "compression": self.compression.get_stats(),
            "projection": self.projection.get_stats(),
            "arbitrage": self.arbitrage.get_stats(),
            "template_cost": self.template_cost.get_stats(),
        }
