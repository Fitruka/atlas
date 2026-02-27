"""ATLAS Native Analytics & Reporting Dashboard Orkestratoru.

Tam analitik pipeline: Topla -> Analiz Et ->
Gorselleştir -> Disari Aktar.
Tum analitik bilesenlerini koordine eder.
"""

import logging
import time
from typing import Any

from app.core.analyticsdash.realtime_dashboard import RealtimeDashboard
from app.core.analyticsdash.conversation_analytics import ConversationAnalytics
from app.core.analyticsdash.cost_dashboard import CostDashboard
from app.core.analyticsdash.cron_monitor import CronMonitor
from app.core.analyticsdash.channel_performance import ChannelPerformance
from app.core.analyticsdash.template_dashboard import TemplateDashboard
from app.core.analyticsdash.export_engine import ExportEngine
from app.core.analyticsdash.custom_widgets import CustomWidgets

logger = logging.getLogger(__name__)


class AnalyticsDashOrchestrator:
    """Analytics Dashboard orkestratoru.

    Tum analitik bilesenlerini koordine eder:
    dashboard, konusma, maliyet, cron,
    kanal, sablon, disari aktarma, widget.

    Attributes:
        dashboard: Gercek zamanli dashboard.
        conversations: Konusma analitikleri.
        costs: Maliyet dashboard.
        cron: Cron izleyici.
        channels: Kanal performansi.
        templates: Sablon metrikleri.
        export_engine: Disari aktarma motoru.
        widgets: Ozel widgetlar.
    """

    def __init__(self) -> None:
        """Orkestratoru baslatir."""
        self.dashboard = RealtimeDashboard()
        self.conversations = ConversationAnalytics()
        self.costs = CostDashboard()
        self.cron = CronMonitor()
        self.channels = ChannelPerformance()
        self.templates = TemplateDashboard()
        self.export_engine = ExportEngine()
        self.widgets = CustomWidgets()

        self._stats: dict[str, Any] = {
            "dashboards_created": 0,
            "overviews_generated": 0,
            "exports_completed": 0,
            "errors": 0,
        }
        logger.info(
            "AnalyticsDashOrchestrator baslatildi",
        )

    def create_full_dashboard(
        self,
        name: str,
        owner: str | None = None,
    ) -> dict[str, Any]:
        """Tum varsayilan widgetlarla dashboard olusturur.

        Args:
            name: Dashboard adi.
            owner: Sahip.

        Returns:
            Dashboard olusturma sonucu.
        """
        start = time.time()
        result: dict[str, Any] = {
            "success": False,
            "dashboard_id": "",
            "widgets_added": 0,
        }

        try:
            dash = self.dashboard.create_dashboard(
                name=name,
                description=f"{name} - tam analitik paneli",
                layout="grid",
                owner=owner or "",
            )
            result["dashboard_id"] = dash.id

            # Varsayilan widgetlar ekle
            default_widgets = [
                ("metric_card", "Sistem Durumu", "system_status"),
                ("line_chart", "Maliyet Trendi", "cost_trend"),
                ("bar_chart", "Kanal Performansi", "channel_metrics"),
                ("pie_chart", "Model Maliyet Dagilimi", "cost_by_model"),
                ("table", "Cron Isler", "cron_jobs"),
                ("gauge", "Butce Kullanimi", "budget_usage"),
                ("timeline", "Son Olaylar", "recent_events"),
                ("heatmap", "Yogun Saatler", "busy_hours"),
            ]

            count = 0
            for wtype, title, source in default_widgets:
                self.dashboard.add_widget(
                    dashboard_id=dash.id,
                    widget_type=wtype,
                    title=title,
                    data_source=source,
                    size_x=1,
                    size_y=1,
                )
                count += 1

            result["widgets_added"] = count
            result["success"] = True
            self._stats["dashboards_created"] += 1
            logger.info(
                "Tam dashboard olusturuldu: %s (%d widget)",
                name, count,
            )

        except Exception as exc:
            self._stats["errors"] += 1
            result["error"] = str(exc)
            logger.error("Dashboard hatasi: %s", exc)

        result["elapsed_ms"] = round(
            (time.time() - start) * 1000, 2,
        )
        return result

    def get_system_overview(self) -> dict[str, Any]:
        """Tum anahtar metrikleri toplayip dondurur.

        Returns:
            Sistem geneli ozet.
        """
        start = time.time()
        self._stats["overviews_generated"] += 1

        overview: dict[str, Any] = {
            "system_status": self.dashboard.get_system_status(),
            "conversations": {},
            "costs": {},
            "cron": {},
            "channels": {},
            "templates": {},
        }

        # Konusma metrikleri
        try:
            conv_summary = self.conversations.get_channel_summary()
            overview["conversations"] = {
                "total_channels": len(conv_summary),
                "summaries": [
                    {
                        "channel": m.channel,
                        "messages": m.total_messages,
                        "avg_response": m.avg_response_time,
                    }
                    for m in conv_summary[:5]
                ],
            }
        except Exception:
            overview["conversations"] = {"error": "unavailable"}

        # Maliyet metrikleri
        try:
            cost_summary = self.costs.get_cost_summary()
            overview["costs"] = {
                "total_cost": cost_summary.total_cost,
                "budget_used_pct": cost_summary.budget_used_pct,
                "by_model": cost_summary.by_model,
            }
        except Exception:
            overview["costs"] = {"error": "unavailable"}

        # Cron metrikleri
        try:
            all_jobs = self.cron.get_all_jobs()
            failing = self.cron.get_failing_jobs()
            overview["cron"] = {
                "total_jobs": len(all_jobs),
                "failing_jobs": len(failing),
            }
        except Exception:
            overview["cron"] = {"error": "unavailable"}

        # Kanal metrikleri
        try:
            active = self.channels.get_most_active_channel()
            overview["channels"] = {
                "most_active": active,
                "response_times": (
                    self.channels.get_response_time_comparison()
                ),
            }
        except Exception:
            overview["channels"] = {"error": "unavailable"}

        # Sablon metrikleri
        try:
            top_templates = self.templates.get_top_templates(
                limit=3,
            )
            overview["templates"] = {
                "top_templates": [
                    {
                        "name": t.template_name,
                        "requests": t.total_requests,
                        "avg_cost": t.avg_cost,
                    }
                    for t in top_templates
                ],
            }
        except Exception:
            overview["templates"] = {"error": "unavailable"}

        overview["elapsed_ms"] = round(
            (time.time() - start) * 1000, 2,
        )
        return overview

    def export_dashboard(
        self,
        dashboard_id: str,
        format: str = "pdf",
    ) -> dict[str, Any]:
        """Dashboardu disa aktarir.

        Args:
            dashboard_id: Dashboard ID.
            format: Cikti formati.

        Returns:
            Disa aktarma sonucu.
        """
        result: dict[str, Any] = {
            "success": False,
            "dashboard_id": dashboard_id,
            "format": format,
        }

        dash = self.dashboard.get_dashboard(
            dashboard_id,
        )
        if not dash:
            result["error"] = "dashboard_not_found"
            return result

        try:
            # Dashboard verisini topla
            data = {
                "name": dash.name,
                "description": dash.description,
                "widgets": len(dash.widgets),
                "overview": self.get_system_overview(),
            }

            export = self.export_engine.export(
                dashboard_id=dashboard_id,
                format=format,
                data=data,
            )
            result["success"] = True
            result["export_id"] = export.id
            result["file_path"] = export.file_path
            self._stats["exports_completed"] += 1

        except Exception as exc:
            self._stats["errors"] += 1
            result["error"] = str(exc)

        return result

    def get_health_summary(self) -> dict[str, Any]:
        """Sistem saglik ozetini dondurur.

        Returns:
            Saglik ozeti.
        """
        cron_jobs = self.cron.get_all_jobs()
        failing = self.cron.get_failing_jobs()

        return {
            "status": "healthy" if not failing else "degraded",
            "cron_health": {
                "total": len(cron_jobs),
                "failing": len(failing),
                "failing_names": [
                    j.job_name for j in failing
                ],
            },
            "cost_health": self.costs.get_budget_status(),
            "system": self.dashboard.get_system_status(),
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Orkestrator istatistikleri.
        """
        return {
            **self._stats,
            "dashboard": self.dashboard.get_stats(),
            "conversations": self.conversations.get_stats(),
            "costs": self.costs.get_stats(),
            "cron": self.cron.get_stats(),
            "channels": self.channels.get_stats(),
            "templates": self.templates.get_stats(),
            "export_engine": self.export_engine.get_stats(),
            "widgets": self.widgets.get_stats(),
        }
