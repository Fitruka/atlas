"""Cost Control & Budget Engine testleri.

RealTimeCostTracker, BudgetLimiter,
CostAlertSystem, SmartModelRouter,
HeartbeatCostOptimizer, TokenCompressionEngine,
CostProjection, ProviderArbitrage,
CostPerTemplate, CostControlOrchestrator testleri.
"""

import pytest

from app.models.costcontrol_models import (
    CostPeriod,
    BudgetStatus,
    AlertSeverity,
    ModelTier,
    TaskComplexity,
    ProviderStatus,
    HeartbeatMode,
    CompressionStrategy,
    CostEntry,
    BudgetLimit,
    CostAlert,
    ModelRouteConfig,
    RouteDecision,
    HeartbeatConfig,
    CompressionResult,
    CostProjectionResult,
    ProviderInfo,
    ArbitrageDecision,
    TemplateCostReport,
)
from app.core.costcontrol import (
    RealTimeCostTracker,
    BudgetLimiter,
    CostAlertSystem,
    SmartModelRouter,
    HeartbeatCostOptimizer,
    TokenCompressionEngine,
    CostProjection,
    ProviderArbitrage,
    CostPerTemplate,
    CostControlOrchestrator,
)


# ============================================================
# Enum Testleri
# ============================================================


class TestCostControlEnums:
    """Enum testleri."""

    def test_cost_period_values(self):
        """Maliyet donemi degerleri."""
        assert CostPeriod.HOURLY == "hourly"
        assert CostPeriod.DAILY == "daily"
        assert CostPeriod.WEEKLY == "weekly"
        assert CostPeriod.MONTHLY == "monthly"

    def test_budget_status_values(self):
        """Butce durumu degerleri."""
        assert BudgetStatus.NORMAL == "normal"
        assert BudgetStatus.WARNING == "warning"
        assert BudgetStatus.CRITICAL == "critical"
        assert BudgetStatus.EXCEEDED == "exceeded"
        assert BudgetStatus.HARD_STOP == "hard_stop"

    def test_alert_severity_values(self):
        """Uyari siddeti degerleri."""
        assert AlertSeverity.INFO == "info"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.CRITICAL == "critical"
        assert AlertSeverity.EMERGENCY == "emergency"

    def test_model_tier_values(self):
        """Model katmani degerleri."""
        assert ModelTier.ECONOMY == "economy"
        assert ModelTier.STANDARD == "standard"
        assert ModelTier.PREMIUM == "premium"
        assert ModelTier.ULTRA == "ultra"

    def test_task_complexity_values(self):
        """Gorev karmasikligi degerleri."""
        assert TaskComplexity.TRIVIAL == "trivial"
        assert TaskComplexity.SIMPLE == "simple"
        assert TaskComplexity.MODERATE == "moderate"
        assert TaskComplexity.COMPLEX == "complex"
        assert TaskComplexity.EXPERT == "expert"

    def test_provider_status_values(self):
        """Saglayici durumu degerleri."""
        assert ProviderStatus.AVAILABLE == "available"
        assert ProviderStatus.DEGRADED == "degraded"
        assert ProviderStatus.UNAVAILABLE == "unavailable"
        assert ProviderStatus.RATE_LIMITED == "rate_limited"

    def test_heartbeat_mode_values(self):
        """Heartbeat modu degerleri."""
        assert HeartbeatMode.FULL == "full"
        assert HeartbeatMode.MINIMAL == "minimal"
        assert HeartbeatMode.BATCHED == "batched"
        assert HeartbeatMode.CONDITIONAL == "conditional"
        assert HeartbeatMode.DISABLED == "disabled"

    def test_compression_strategy_values(self):
        """Sikistirma stratejisi degerleri."""
        assert CompressionStrategy.NONE == "none"
        assert CompressionStrategy.SUMMARY == "summary"
        assert CompressionStrategy.TRUNCATE == "truncate"
        assert CompressionStrategy.SELECTIVE == "selective"
        assert CompressionStrategy.AGGRESSIVE == "aggressive"


# ============================================================
# Model Testleri
# ============================================================


class TestCostControlModels:
    """Model testleri."""

    def test_cost_entry_creation(self):
        """CostEntry olusturma."""
        e = CostEntry(session_id="s1", model_name="gpt-4o", input_tokens=100, output_tokens=200, cost_usd=0.005)
        assert e.session_id == "s1"
        assert e.model_name == "gpt-4o"
        assert e.entry_id
        assert e.input_tokens == 100
        assert e.output_tokens == 200
        assert e.cost_usd == 0.005

    def test_cost_entry_defaults(self):
        """CostEntry varsayilanlar."""
        e = CostEntry()
        assert e.session_id == ""
        assert e.model_name == ""
        assert e.provider == ""
        assert e.tool_name == ""
        assert e.input_tokens == 0
        assert e.output_tokens == 0
        assert e.total_tokens == 0
        assert e.cost_usd == 0.0
        assert e.duration_ms == 0.0
        assert e.task_type == ""
        assert e.template_id == ""
        assert e.timestamp > 0
        assert e.metadata == {}

    def test_budget_limit_creation(self):
        """BudgetLimit olusturma."""
        b = BudgetLimit(name="Gunluk", period=CostPeriod.DAILY, limit_usd=10.0)
        assert b.name == "Gunluk"
        assert b.period == CostPeriod.DAILY
        assert b.limit_usd == 10.0
        assert b.warning_threshold == 0.8
        assert b.critical_threshold == 0.95
        assert b.hard_stop is True
        assert b.status == BudgetStatus.NORMAL

    def test_budget_limit_defaults(self):
        """BudgetLimit varsayilanlar."""
        b = BudgetLimit()
        assert b.current_spend == 0.0
        assert b.reset_at == 0.0
        assert b.created_at > 0
        assert b.metadata == {}

    def test_cost_alert_creation(self):
        """CostAlert olusturma."""
        a = CostAlert(severity=AlertSeverity.CRITICAL, title="Butce uyarisi", message="Limit asildi", current_spend=9.5, limit_usd=10.0)
        assert a.severity == AlertSeverity.CRITICAL
        assert a.title == "Butce uyarisi"
        assert a.current_spend == 9.5
        assert a.acknowledged is False
        assert a.channels == ["telegram"]

    def test_model_route_config_creation(self):
        """ModelRouteConfig olusturma."""
        c = ModelRouteConfig(model_name="gpt-4o", provider="openai", tier=ModelTier.STANDARD, cost_per_1k_input=0.005, cost_per_1k_output=0.015)
        assert c.model_name == "gpt-4o"
        assert c.provider == "openai"
        assert c.tier == ModelTier.STANDARD
        assert c.enabled is True
        assert c.supported_tasks == []

    def test_route_decision_creation(self):
        """RouteDecision olusturma."""
        d = RouteDecision(task_type="analysis", complexity=TaskComplexity.COMPLEX, selected_model="claude-opus-4")
        assert d.task_type == "analysis"
        assert d.complexity == TaskComplexity.COMPLEX
        assert d.selected_model == "claude-opus-4"
        assert d.alternatives == []

    def test_heartbeat_config_creation(self):
        """HeartbeatConfig olusturma."""
        h = HeartbeatConfig(mode=HeartbeatMode.MINIMAL, interval_seconds=600)
        assert h.mode == HeartbeatMode.MINIMAL
        assert h.interval_seconds == 600
        assert h.skip_if_idle is True
        assert h.include_metrics is True

    def test_compression_result_creation(self):
        """CompressionResult olusturma."""
        r = CompressionResult(strategy=CompressionStrategy.SUMMARY, original_tokens=1000, compressed_tokens=300, savings_tokens=700)
        assert r.strategy == CompressionStrategy.SUMMARY
        assert r.original_tokens == 1000
        assert r.compressed_tokens == 300
        assert r.savings_tokens == 700

    def test_cost_projection_result_creation(self):
        """CostProjectionResult olusturma."""
        p = CostProjectionResult(period=CostPeriod.MONTHLY, current_spend=50.0, projected_spend=150.0, trend="increasing")
        assert p.period == CostPeriod.MONTHLY
        assert p.current_spend == 50.0
        assert p.projected_spend == 150.0
        assert p.trend == "increasing"
        assert p.recommendations == []
        assert p.breakdown_by_model == {}

    def test_provider_info_creation(self):
        """ProviderInfo olusturma."""
        p = ProviderInfo(name="anthropic", models=["claude-sonnet-4", "claude-opus-4"], cost_multiplier=1.0)
        assert p.name == "anthropic"
        assert len(p.models) == 2
        assert p.status == ProviderStatus.AVAILABLE
        assert p.reliability_score == 1.0
        assert p.cost_multiplier == 1.0

    def test_arbitrage_decision_creation(self):
        """ArbitrageDecision olusturma."""
        a = ArbitrageDecision(model_name="claude-sonnet-4", selected_provider="anthropic", cost_usd=0.003, savings_usd=0.001)
        assert a.model_name == "claude-sonnet-4"
        assert a.selected_provider == "anthropic"
        assert a.savings_usd == 0.001

    def test_template_cost_report_creation(self):
        """TemplateCostReport olusturma."""
        r = TemplateCostReport(template_id="t1", template_name="E-ticaret", total_cost=25.5, total_requests=500)
        assert r.template_id == "t1"
        assert r.template_name == "E-ticaret"
        assert r.total_cost == 25.5
        assert r.total_requests == 500
        assert r.optimization_suggestions == []
        assert r.cost_by_skill == {}
        assert r.cost_by_model == {}


# ============================================================
# RealTimeCostTracker Testleri
# ============================================================


class TestRealTimeCostTracker:
    """RealTimeCostTracker testleri."""

    def test_init(self):
        """Baslama testi."""
        t = RealTimeCostTracker()
        assert t is not None
        assert t.get_total_cost() == 0.0

    def test_record_known_model(self):
        """Bilinen model maliyet kaydi."""
        t = RealTimeCostTracker()
        entry = t.record("s1", "claude-sonnet-4", 1000, 500)
        assert entry.session_id == "s1"
        assert entry.model_name == "claude-sonnet-4"
        assert entry.total_tokens == 1500
        assert entry.cost_usd > 0

    def test_record_unknown_model(self):
        """Bilinmeyen model varsayilan fiyat."""
        t = RealTimeCostTracker()
        entry = t.record("s1", "unknown-model", 1000, 500)
        assert entry.cost_usd > 0

    def test_record_with_tool(self):
        """Arac bazli kayit."""
        t = RealTimeCostTracker()
        t.record("s1", "gpt-4o-mini", 100, 50, tool_name="web_scraper")
        stats = t.get_stats()
        assert "web_scraper" in stats["by_tool"]
        assert stats["by_tool"]["web_scraper"]["requests"] == 1

    def test_record_with_template(self):
        """Sablon bazli kayit."""
        t = RealTimeCostTracker()
        entry = t.record("s1", "gpt-4o", 500, 200, template_id="tmpl-1")
        assert entry.template_id == "tmpl-1"

    def test_record_with_provider(self):
        """Saglayici bazli kayit."""
        t = RealTimeCostTracker()
        entry = t.record("s1", "gpt-4o", 100, 50, provider="openai")
        assert entry.provider == "openai"

    def test_session_cost_tracking(self):
        """Session maliyet takibi."""
        t = RealTimeCostTracker()
        t.record("s1", "claude-haiku-3.5", 100, 50)
        t.record("s1", "claude-haiku-3.5", 200, 100)
        cost = t.get_session_cost("s1")
        assert cost["cost"] > 0
        assert cost["tokens"] == 450
        assert cost["requests"] == 2

    def test_session_cost_unknown(self):
        """Bilinmeyen session maliyeti."""
        t = RealTimeCostTracker()
        cost = t.get_session_cost("unknown")
        assert cost["cost"] == 0.0
        assert cost["tokens"] == 0
        assert cost["requests"] == 0

    def test_model_cost_tracking(self):
        """Model bazli maliyet."""
        t = RealTimeCostTracker()
        t.record("s1", "gpt-4o", 1000, 500)
        cost = t.get_model_cost("gpt-4o")
        assert cost["cost"] > 0
        assert cost["requests"] == 1

    def test_model_cost_unknown(self):
        """Bilinmeyen model maliyeti."""
        t = RealTimeCostTracker()
        cost = t.get_model_cost("unknown")
        assert cost["cost"] == 0.0

    def test_total_cost_accumulation(self):
        """Toplam maliyet birikmesi."""
        t = RealTimeCostTracker()
        t.record("s1", "claude-sonnet-4", 500, 200)
        cost1 = t.get_total_cost()
        t.record("s2", "claude-sonnet-4", 500, 200)
        cost2 = t.get_total_cost()
        assert cost2 > cost1

    def test_get_recent_entries(self):
        """Son kayitlari getirme."""
        t = RealTimeCostTracker()
        for i in range(10):
            t.record(f"s{i}", "gpt-4o-mini", 100, 50)
        recent = t.get_recent_entries(5)
        assert len(recent) == 5

    def test_get_recent_entries_default_limit(self):
        """Varsayilan limitli son kayitlar."""
        t = RealTimeCostTracker()
        for i in range(3):
            t.record(f"s{i}", "gpt-4o-mini", 10, 5)
        recent = t.get_recent_entries()
        assert len(recent) == 3

    def test_get_entries_by_session(self):
        """Session bazli kayit filtreleme."""
        t = RealTimeCostTracker()
        t.record("s1", "gpt-4o", 100, 50)
        t.record("s2", "gpt-4o", 200, 100)
        t.record("s1", "gpt-4o", 300, 150)
        entries = t.get_entries_by_session("s1")
        assert len(entries) == 2

    def test_get_entries_by_session_empty(self):
        """Bos session kayitlari."""
        t = RealTimeCostTracker()
        entries = t.get_entries_by_session("nonexistent")
        assert entries == []

    def test_cost_calculation_haiku(self):
        """Haiku model maliyet hesabi."""
        t = RealTimeCostTracker()
        entry = t.record("s1", "claude-haiku-3.5", 1000, 1000)
        expected = (1000 / 1000) * 0.0008 + (1000 / 1000) * 0.004
        assert abs(entry.cost_usd - expected) < 0.0001

    def test_zero_tokens(self):
        """Sifir token kaydi."""
        t = RealTimeCostTracker()
        entry = t.record("s1", "gpt-4o", 0, 0)
        assert entry.cost_usd == 0.0
        assert entry.total_tokens == 0

    def test_stats(self):
        """Istatistikler."""
        t = RealTimeCostTracker()
        t.record("s1", "claude-sonnet-4", 500, 200)
        stats = t.get_stats()
        assert stats["total_cost_usd"] > 0
        assert stats["total_tokens"] == 700
        assert stats["total_entries"] == 1
        assert stats["total_sessions"] == 1
        assert "claude-sonnet-4" in stats["by_model"]


# ============================================================
# BudgetLimiter Testleri
# ============================================================


class TestBudgetLimiter:
    """BudgetLimiter testleri."""

    def test_init(self):
        """Baslama testi."""
        bl = BudgetLimiter()
        assert bl is not None
        assert bl.list_budgets() == []

    def test_set_limit(self):
        """Butce limiti tanimlama."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Gunluk", "daily", 10.0)
        assert budget.name == "Gunluk"
        assert budget.limit_usd == 10.0
        assert budget.reset_at > 0

    def test_set_limit_custom_thresholds(self):
        """Ozel esik butce limiti."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "weekly", 50.0, warning_threshold=0.7, critical_threshold=0.9)
        assert budget.warning_threshold == 0.7
        assert budget.critical_threshold == 0.9

    def test_set_limit_no_hard_stop(self):
        """Hard stop devre disi butce."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Flexible", "monthly", 100.0, hard_stop=False)
        assert budget.hard_stop is False

    def test_check_budget_normal(self):
        """Normal butce kontrolu."""
        bl = BudgetLimiter()
        bl.set_limit("Test", "daily", 10.0)
        result = bl.check_budget(1.0)
        assert result["allowed"] is True
        assert result["blocked"] is False
        assert result["alerts"] == []

    def test_check_budget_warning(self):
        """Uyari esigi butce kontrolu."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "daily", 10.0, warning_threshold=0.5)
        budget.current_spend = 4.0
        result = bl.check_budget(2.0)
        assert result["blocked"] is False
        assert len(result["alerts"]) > 0
        assert result["alerts"][0]["status"] == "warning"

    def test_check_budget_critical(self):
        """Kritik esik butce kontrolu."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "daily", 10.0, critical_threshold=0.9)
        budget.current_spend = 8.5
        result = bl.check_budget(1.0)
        assert result["blocked"] is False
        assert any(a["status"] == "critical" for a in result["alerts"])

    def test_check_budget_hard_stop(self):
        """Hard stop butce kontrolu."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "daily", 10.0, hard_stop=True)
        budget.current_spend = 9.5
        result = bl.check_budget(1.0)
        assert result["blocked"] is True
        assert result["allowed"] is False

    def test_check_budget_no_hard_stop_exceeded(self):
        """Hard stop yok, limit asildi."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "daily", 10.0, hard_stop=False)
        budget.current_spend = 9.5
        result = bl.check_budget(1.0)
        assert result["blocked"] is False

    def test_check_budget_specific_id(self):
        """Belirli butce ID ile kontrol."""
        bl = BudgetLimiter()
        b1 = bl.set_limit("B1", "daily", 10.0)
        bl.set_limit("B2", "monthly", 200.0)
        b1.current_spend = 9.5
        result = bl.check_budget(1.0, budget_id=b1.limit_id)
        assert result["blocked"] is True

    def test_check_budget_empty(self):
        """Butce olmadan kontrol."""
        bl = BudgetLimiter()
        result = bl.check_budget(1.0)
        assert result["allowed"] is True
        assert result["blocked"] is False

    def test_add_spend_allowed(self):
        """Izin verilen harcama."""
        bl = BudgetLimiter()
        bl.set_limit("Test", "daily", 10.0)
        result = bl.add_spend(5.0)
        assert result is True

    def test_add_spend_blocked(self):
        """Engellenen harcama."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "daily", 10.0)
        budget.current_spend = 9.5
        result = bl.add_spend(1.0)
        assert result is False

    def test_add_spend_accumulates(self):
        """Harcama biriktirme."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "daily", 10.0)
        bl.add_spend(3.0)
        bl.add_spend(2.0)
        assert budget.current_spend == 5.0

    def test_get_budget(self):
        """Butce getirme."""
        bl = BudgetLimiter()
        budget = bl.set_limit("Test", "daily", 10.0)
        found = bl.get_budget(budget.limit_id)
        assert found is not None
        assert found.name == "Test"

    def test_get_budget_unknown(self):
        """Bilinmeyen butce getirme."""
        bl = BudgetLimiter()
        assert bl.get_budget("unknown") is None

    def test_list_budgets(self):
        """Butce listeleme."""
        bl = BudgetLimiter()
        bl.set_limit("B1", "daily", 10.0)
        bl.set_limit("B2", "weekly", 50.0)
        budgets = bl.list_budgets()
        assert len(budgets) == 2

    def test_stats(self):
        """Istatistikler."""
        bl = BudgetLimiter()
        bl.set_limit("Test", "daily", 10.0)
        bl.check_budget(1.0)
        stats = bl.get_stats()
        assert stats["total_budgets"] == 1
        assert stats["total_checks"] == 1
        assert stats["total_blocks"] == 0


# ============================================================
# CostAlertSystem Testleri
# ============================================================


class TestCostAlertSystem:
    """CostAlertSystem testleri."""

    def test_init(self):
        """Baslama testi."""
        cas = CostAlertSystem()
        assert cas is not None
        assert cas.get_unacknowledged() == []

    def test_add_rule(self):
        """Uyari kurali ekleme."""
        cas = CostAlertSystem()
        rule = cas.add_rule("Test", 5.0, severity="warning")
        assert rule["name"] == "Test"
        assert rule["threshold_usd"] == 5.0
        assert rule["severity"] == "warning"
        assert rule["enabled"] is True
        assert rule["trigger_count"] == 0

    def test_add_rule_with_channels(self):
        """Kanalli uyari kurali."""
        cas = CostAlertSystem()
        rule = cas.add_rule("Test", 10.0, channels=["telegram", "email"])
        assert rule["channels"] == ["telegram", "email"]

    def test_add_rule_default_channels(self):
        """Varsayilan kanalli uyari kurali."""
        cas = CostAlertSystem()
        rule = cas.add_rule("Test", 5.0)
        assert rule["channels"] == ["telegram"]

    def test_check_and_alert_trigger(self):
        """Uyari tetikleme."""
        cas = CostAlertSystem()
        cas.add_rule("High Cost", 5.0, severity="warning", period="daily")
        alerts = cas.check_and_alert(6.0, budget_limit=10.0, period="daily")
        assert len(alerts) == 1
        assert alerts[0].severity == "warning"
        assert alerts[0].percentage == 60.0

    def test_check_and_alert_no_trigger(self):
        """Uyari tetiklenmemesi."""
        cas = CostAlertSystem()
        cas.add_rule("High Cost", 10.0, period="daily")
        alerts = cas.check_and_alert(5.0, period="daily")
        assert len(alerts) == 0

    def test_check_and_alert_period_mismatch(self):
        """Donem uyumsuzlugu."""
        cas = CostAlertSystem()
        cas.add_rule("Test", 5.0, period="daily")
        alerts = cas.check_and_alert(6.0, period="weekly")
        assert len(alerts) == 0

    def test_check_and_alert_disabled_rule(self):
        """Devre disi kural."""
        cas = CostAlertSystem()
        rule = cas.add_rule("Test", 5.0, period="daily")
        rule["enabled"] = False
        alerts = cas.check_and_alert(6.0, period="daily")
        assert len(alerts) == 0

    def test_check_and_alert_no_budget_limit(self):
        """Butce limiti olmadan uyari."""
        cas = CostAlertSystem()
        cas.add_rule("Test", 5.0, period="daily")
        alerts = cas.check_and_alert(6.0, budget_limit=0.0, period="daily")
        assert len(alerts) == 1
        assert alerts[0].percentage == 0.0

    def test_create_alert_manual(self):
        """Manuel uyari olusturma."""
        cas = CostAlertSystem()
        alert = cas.create_alert(
            severity="critical",
            title="Acil uyari",
            message="Butce asildi",
            current_spend=15.0,
            limit_usd=10.0,
        )
        assert alert.severity == "critical"
        assert alert.title == "Acil uyari"
        assert alert.percentage == 150.0

    def test_create_alert_no_limit(self):
        """Limitsiz uyari yuzde hesabi."""
        cas = CostAlertSystem()
        alert = cas.create_alert(severity="info", title="Bilgi", message="Test", current_spend=5.0, limit_usd=0.0)
        assert alert.percentage == 0.0

    def test_create_alert_custom_channels(self):
        """Ozel kanalli uyari olusturma."""
        cas = CostAlertSystem()
        alert = cas.create_alert("info", "Test", "Msg", channels=["email", "slack"])
        assert alert.channels == ["email", "slack"]

    def test_acknowledge(self):
        """Uyari onaylama."""
        cas = CostAlertSystem()
        alert = cas.create_alert("warning", "Test", "msg")
        result = cas.acknowledge(alert.alert_id)
        assert result is True
        assert len(cas.get_unacknowledged()) == 0

    def test_acknowledge_unknown(self):
        """Bilinmeyen uyari onaylama."""
        cas = CostAlertSystem()
        result = cas.acknowledge("unknown")
        assert result is False

    def test_get_unacknowledged(self):
        """Onaylanmamis uyarilar."""
        cas = CostAlertSystem()
        cas.create_alert("info", "A", "msg1")
        cas.create_alert("info", "B", "msg2")
        alert_c = cas.create_alert("info", "C", "msg3")
        cas.acknowledge(alert_c.alert_id)
        pending = cas.get_unacknowledged()
        assert len(pending) == 2

    def test_stats(self):
        """Istatistikler."""
        cas = CostAlertSystem()
        cas.add_rule("R1", 5.0, period="daily")
        cas.create_alert("info", "Manual", "Test")
        alert2 = cas.create_alert("info", "Manual2", "Test2")
        cas.acknowledge(alert2.alert_id)
        stats = cas.get_stats()
        assert stats["total_alerts"] == 2
        assert stats["total_acknowledged"] == 1
        assert stats["total_rules"] == 1
        assert stats["pending_alerts"] == 1


# ============================================================
# SmartModelRouter Testleri
# ============================================================


class TestSmartModelRouter:
    """SmartModelRouter testleri."""

    def test_init(self):
        """Baslama testi."""
        r = SmartModelRouter()
        assert r is not None
        stats = r.get_stats()
        assert stats["total_models"] >= 5

    def test_route_simple_task(self):
        """Basit gorev yonlendirme."""
        r = SmartModelRouter()
        decision = r.route(task_type="classification", complexity="simple")
        assert decision.selected_model != ""
        assert decision.selected_provider != ""

    def test_route_complex_task(self):
        """Karmasik gorev yonlendirme."""
        r = SmartModelRouter()
        decision = r.route(task_type="reasoning", complexity="complex")
        assert decision.selected_model != ""

    def test_route_moderate_task(self):
        """Orta seviye gorev yonlendirme."""
        r = SmartModelRouter()
        decision = r.route(task_type="analysis", complexity="moderate")
        assert decision.selected_model != ""
        assert decision.estimated_cost > 0

    def test_route_trivial_task(self):
        """Cok basit gorev yonlendirme."""
        r = SmartModelRouter()
        decision = r.route(complexity="trivial")
        assert decision.selected_model != ""

    def test_route_expert_task(self):
        """Uzman gorev yonlendirme."""
        r = SmartModelRouter()
        decision = r.route(complexity="expert")
        assert decision.selected_model != ""

    def test_route_with_preferred_provider(self):
        """Tercih edilen saglayici ile yonlendirme."""
        r = SmartModelRouter()
        decision = r.route(complexity="moderate", preferred_provider="anthropic")
        assert decision.selected_provider == "anthropic"

    def test_route_preferred_provider_no_match(self):
        """Uyumsuz tercih edilen saglayici - fallback."""
        r = SmartModelRouter()
        decision = r.route(complexity="moderate", preferred_provider="nonexistent_provider")
        assert decision.selected_model != ""

    def test_route_includes_alternatives(self):
        """Alternatif modeller icermeli."""
        r = SmartModelRouter()
        decision = r.route(complexity="moderate")
        assert isinstance(decision.alternatives, list)

    def test_route_has_reason(self):
        """Yonlendirme karari gerekce icermeli."""
        r = SmartModelRouter()
        decision = r.route(complexity="moderate")
        assert decision.reason != ""

    def test_register_model(self):
        """Yeni model kaydi."""
        r = SmartModelRouter()
        config = ModelRouteConfig(
            model_name="custom-model",
            provider="custom",
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.003,
            quality_score=0.8,
        )
        result = r.register_model(config)
        assert result is True
        assert r.get_stats()["total_models"] >= 6

    def test_register_disabled_model_excluded(self):
        """Devre disi model yonlendirmede harici."""
        r = SmartModelRouter()
        config = ModelRouteConfig(
            model_name="disabled-model",
            provider="custom",
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.0001,
            cost_per_1k_output=0.0001,
            quality_score=0.99,
            enabled=False,
        )
        r.register_model(config)
        decision = r.route(complexity="moderate")
        assert decision.selected_model != "disabled-model"

    def test_stats(self):
        """Istatistikler."""
        r = SmartModelRouter()
        r.route(complexity="simple")
        r.route(complexity="complex")
        stats = r.get_stats()
        assert stats["total_routes"] == 2
        assert stats["total_models"] >= 5


# ============================================================
# HeartbeatCostOptimizer Testleri
# ============================================================


class TestHeartbeatCostOptimizer:
    """HeartbeatCostOptimizer testleri."""

    def test_init(self):
        """Baslama testi."""
        h = HeartbeatCostOptimizer()
        assert h is not None
        config = h.get_config()
        assert config.mode == HeartbeatMode.CONDITIONAL

    def test_configure_minimal(self):
        """Minimal mod yapilandirma."""
        h = HeartbeatCostOptimizer()
        config = h.configure(mode="minimal", interval_seconds=600)
        assert config.interval_seconds == 600
        assert config.cost_per_heartbeat < 0.003

    def test_configure_disabled(self):
        """Devre disi mod yapilandirma."""
        h = HeartbeatCostOptimizer()
        config = h.configure(mode="disabled")
        assert config.cost_per_heartbeat == 0.0

    def test_configure_batched(self):
        """Toplu mod yapilandirma."""
        h = HeartbeatCostOptimizer()
        config = h.configure(mode="batched", batch_size=20)
        assert config.batch_size == 20

    def test_configure_full(self):
        """Tam mod yapilandirma."""
        h = HeartbeatCostOptimizer()
        config = h.configure(mode="full")
        assert config.cost_per_heartbeat == 0.003

    def test_configure_min_interval_clamping(self):
        """Minimum aralik sinirlamasi."""
        h = HeartbeatCostOptimizer()
        config = h.configure(interval_seconds=10)
        assert config.interval_seconds >= 60

    def test_configure_max_interval_clamping(self):
        """Maksimum aralik sinirlamasi."""
        h = HeartbeatCostOptimizer()
        config = h.configure(interval_seconds=99999)
        assert config.interval_seconds <= 3600

    def test_configure_monthly_savings(self):
        """Aylik tasarruf tahmini."""
        h = HeartbeatCostOptimizer()
        config = h.configure(mode="minimal")
        assert config.estimated_monthly_savings > 0

    def test_should_send_disabled(self):
        """Devre disi modda gonderilmemeli."""
        h = HeartbeatCostOptimizer()
        h.configure(mode="disabled")
        assert h.should_send() is False

    def test_should_send_conditional_idle(self):
        """Kosullu mod bosta iken atlanmali."""
        h = HeartbeatCostOptimizer()
        h.configure(mode="conditional", interval_seconds=60)
        h._last_heartbeat = 0
        result = h.should_send(is_idle=True)
        assert result is False

    def test_should_send_conditional_active(self):
        """Kosullu mod aktif iken gonderilmeli."""
        h = HeartbeatCostOptimizer()
        h.configure(mode="conditional", interval_seconds=60)
        h._last_heartbeat = 0
        result = h.should_send(is_idle=False)
        assert result is True

    def test_should_send_interval_not_elapsed(self):
        """Aralik henuz dolmadi."""
        h = HeartbeatCostOptimizer()
        h.configure(mode="full", interval_seconds=300)
        h.record_heartbeat()
        result = h.should_send()
        assert result is False

    def test_record_heartbeat(self):
        """Heartbeat kaydi."""
        h = HeartbeatCostOptimizer()
        h.record_heartbeat(cost=0.001)
        stats = h.get_stats()
        assert stats["total_heartbeats"] == 1
        assert stats["total_saved_usd"] > 0

    def test_record_heartbeat_default_cost(self):
        """Varsayilan maliyetli heartbeat kaydi."""
        h = HeartbeatCostOptimizer()
        h.configure(mode="minimal")
        h.record_heartbeat()
        stats = h.get_stats()
        assert stats["total_heartbeats"] == 1

    def test_get_config(self):
        """Yapilandirma getirme."""
        h = HeartbeatCostOptimizer()
        config = h.get_config()
        assert config is not None
        assert config.mode == HeartbeatMode.CONDITIONAL

    def test_stats(self):
        """Istatistikler."""
        h = HeartbeatCostOptimizer()
        h.configure(mode="conditional")
        stats = h.get_stats()
        assert "mode" in stats
        assert "total_heartbeats" in stats
        assert "total_skipped" in stats
        assert "total_saved_usd" in stats
        assert "monthly_savings_estimate" in stats


# ============================================================
# TokenCompressionEngine Testleri
# ============================================================


class TestTokenCompressionEngine:
    """TokenCompressionEngine testleri."""

    def test_init(self):
        """Baslama testi."""
        tce = TokenCompressionEngine()
        assert tce is not None

    def test_compress_short_text(self):
        """Kisa metin sikistirma atlanmali."""
        tce = TokenCompressionEngine()
        result = tce.compress("Kisa metin", strategy="selective")
        assert result.original_tokens == result.compressed_tokens
        assert result.savings_tokens == 0

    def test_compress_selective(self):
        """Secici strateji sikistirma."""
        tce = TokenCompressionEngine()
        text = "A" * 4000
        result = tce.compress(text, strategy="selective")
        assert result.compressed_tokens < result.original_tokens
        assert result.savings_tokens > 0
        assert result.savings_percent > 0
        assert result.quality_loss == 0.1

    def test_compress_summary(self):
        """Ozet strateji sikistirma."""
        tce = TokenCompressionEngine()
        text = "B" * 4000
        result = tce.compress(text, strategy="summary")
        assert result.compressed_tokens < result.original_tokens
        assert result.quality_loss == 0.15

    def test_compress_truncate(self):
        """Kesme strateji sikistirma."""
        tce = TokenCompressionEngine()
        text = "C" * 4000
        result = tce.compress(text, strategy="truncate", target_ratio=0.5)
        assert result.compressed_tokens < result.original_tokens
        assert result.quality_loss == 0.3

    def test_compress_aggressive(self):
        """Agresif strateji sikistirma."""
        tce = TokenCompressionEngine()
        text = "D" * 8000
        result = tce.compress(text, strategy="aggressive")
        assert result.compressed_tokens < result.original_tokens
        assert result.quality_loss == 0.4
        assert result.savings_percent > 50

    def test_compress_none_strategy(self):
        """None strateji sikistirma yok."""
        tce = TokenCompressionEngine()
        text = "E" * 4000
        result = tce.compress(text, strategy="none")
        assert result.compressed_tokens == result.original_tokens

    def test_compress_cost_saved(self):
        """Maliyet tasarrufu hesaplama."""
        tce = TokenCompressionEngine()
        text = "F" * 4000
        result = tce.compress(text, strategy="selective", model_cost_per_1k=0.01)
        assert result.cost_saved_usd > 0

    def test_recommend_strategy_small(self):
        """Kucuk token icin strateji onerisi."""
        tce = TokenCompressionEngine()
        assert tce.recommend_strategy(100) == "none"

    def test_recommend_strategy_high_importance(self):
        """Yuksek onemli icin strateji onerisi."""
        tce = TokenCompressionEngine()
        assert tce.recommend_strategy(1000, importance="high") == "selective"

    def test_recommend_strategy_low_importance(self):
        """Dusuk onemli icin strateji onerisi."""
        tce = TokenCompressionEngine()
        assert tce.recommend_strategy(1000, importance="low") == "aggressive"

    def test_recommend_strategy_large_medium(self):
        """Buyuk boyutlu orta onem strateji onerisi."""
        tce = TokenCompressionEngine()
        assert tce.recommend_strategy(15000, importance="medium") == "summary"

    def test_recommend_strategy_medium_default(self):
        """Orta boyutlu varsayilan onem."""
        tce = TokenCompressionEngine()
        assert tce.recommend_strategy(2000) == "selective"

    def test_stats(self):
        """Istatistikler."""
        tce = TokenCompressionEngine()
        tce.compress("G" * 4000, strategy="selective")
        stats = tce.get_stats()
        assert stats["total_compressed"] == 1
        assert stats["total_saved_tokens"] > 0


# ============================================================
# CostProjection Testleri
# ============================================================


class TestCostProjection:
    """CostProjection testleri."""

    def test_init(self):
        """Baslama testi."""
        cp = CostProjection()
        assert cp is not None

    def test_record_daily_cost(self):
        """Gunluk maliyet kaydi."""
        cp = CostProjection()
        cp.record_daily_cost(5.0)
        stats = cp.get_stats()
        assert stats["daily_records"] == 1

    def test_record_daily_cost_with_breakdown(self):
        """Dagilimli gunluk maliyet kaydi."""
        cp = CostProjection()
        cp.record_daily_cost(
            10.0,
            breakdown_by_model={"gpt-4o": 7.0, "claude-haiku-3.5": 3.0},
            breakdown_by_tool={"web_scraper": 4.0},
        )
        stats = cp.get_stats()
        assert stats["daily_records"] == 1

    def test_project_with_current_spend(self):
        """Mevcut harcamayla projeksiyon."""
        cp = CostProjection()
        result = cp.project(period="monthly", current_spend=30.0, days_elapsed=10)
        assert result.projected_spend == 90.0
        assert result.current_spend == 30.0

    def test_project_from_daily_costs(self):
        """Gunluk maliyet verilerinden projeksiyon."""
        cp = CostProjection()
        for _ in range(10):
            cp.record_daily_cost(5.0)
        result = cp.project(period="monthly")
        assert result.projected_spend > 0

    def test_project_weekly(self):
        """Haftalik projeksiyon."""
        cp = CostProjection()
        result = cp.project(period="weekly", current_spend=7.0, days_elapsed=7)
        assert result.projected_spend == 7.0

    def test_project_no_data(self):
        """Veri olmadan projeksiyon."""
        cp = CostProjection()
        result = cp.project(period="monthly", current_spend=10.0, days_elapsed=0)
        assert result.projected_spend == 10.0

    def test_project_trend_increasing(self):
        """Artan trend tespiti."""
        cp = CostProjection()
        for _ in range(7):
            cp.record_daily_cost(2.0)
        for _ in range(7):
            cp.record_daily_cost(5.0)
        result = cp.project(period="monthly")
        assert result.trend == "increasing"
        assert result.trend_percent > 0

    def test_project_trend_decreasing(self):
        """Azalan trend tespiti."""
        cp = CostProjection()
        for _ in range(7):
            cp.record_daily_cost(10.0)
        for _ in range(7):
            cp.record_daily_cost(3.0)
        result = cp.project(period="monthly")
        assert result.trend == "decreasing"
        assert result.trend_percent < 0

    def test_project_trend_stable(self):
        """Sabit trend tespiti."""
        cp = CostProjection()
        for _ in range(14):
            cp.record_daily_cost(5.0)
        result = cp.project(period="monthly")
        assert result.trend == "stable"

    def test_project_confidence_with_data(self):
        """Yeterli veri ile yuksek guven puani."""
        cp = CostProjection()
        for _ in range(20):
            cp.record_daily_cost(5.0)
        result = cp.project(period="monthly")
        assert result.confidence == 0.8

    def test_project_confidence_low_data(self):
        """Az veri ile dusuk guven puani."""
        cp = CostProjection()
        for _ in range(5):
            cp.record_daily_cost(5.0)
        result = cp.project(period="monthly")
        assert result.confidence == 0.5

    def test_project_recommendations_high_cost(self):
        """Yuksek maliyet onerileri."""
        cp = CostProjection()
        result = cp.project(period="monthly", current_spend=100.0, days_elapsed=10)
        assert len(result.recommendations) > 0

    def test_stats(self):
        """Istatistikler."""
        cp = CostProjection()
        cp.record_daily_cost(5.0)
        cp.project(period="monthly", current_spend=5.0, days_elapsed=1)
        stats = cp.get_stats()
        assert stats["total_projections"] == 1
        assert stats["daily_records"] == 1


# ============================================================
# ProviderArbitrage Testleri
# ============================================================


class TestProviderArbitrage:
    """ProviderArbitrage testleri."""

    def test_init(self):
        """Baslama testi."""
        pa = ProviderArbitrage()
        assert pa is not None

    def test_register_provider(self):
        """Saglayici kaydi."""
        pa = ProviderArbitrage()
        provider = pa.register_provider("openrouter", models=["claude-sonnet-4", "gpt-4o"], cost_multiplier=0.9)
        assert provider.name == "openrouter"
        assert len(provider.models) == 2
        assert provider.cost_multiplier == 0.9

    def test_register_provider_with_latency(self):
        """Gecikme bilgili saglayici kaydi."""
        pa = ProviderArbitrage()
        provider = pa.register_provider("fast", models=["model-a"], latency_ms=50.0)
        assert provider.latency_ms == 50.0

    def test_find_cheapest_single_provider(self):
        """Tek saglayici en ucuz."""
        pa = ProviderArbitrage()
        pa.register_provider("anthropic", ["claude-sonnet-4"], cost_multiplier=1.0)
        decision = pa.find_cheapest("claude-sonnet-4", base_cost=0.01)
        assert decision.selected_provider == "anthropic"
        assert decision.cost_usd == 0.01

    def test_find_cheapest_multiple_providers(self):
        """Coklu saglayici en ucuz secimi."""
        pa = ProviderArbitrage()
        pa.register_provider("anthropic", ["claude-sonnet-4"], cost_multiplier=1.0)
        pa.register_provider("openrouter", ["claude-sonnet-4"], cost_multiplier=0.8)
        pa.register_provider("azure", ["claude-sonnet-4"], cost_multiplier=1.2)
        decision = pa.find_cheapest("claude-sonnet-4", base_cost=0.01)
        assert decision.selected_provider == "openrouter"
        assert decision.savings_usd > 0
        assert decision.providers_compared == 3

    def test_find_cheapest_no_provider(self):
        """Saglayici bulunamadi."""
        pa = ProviderArbitrage()
        decision = pa.find_cheapest("unknown-model", base_cost=0.01)
        assert decision.selected_provider == ""
        assert "bulunamadi" in decision.reason

    def test_find_cheapest_reliability_filter(self):
        """Guvenilirlik filtresi."""
        pa = ProviderArbitrage()
        pa.register_provider("cheap", ["model-a"], cost_multiplier=0.5, reliability_score=0.3)
        pa.register_provider("reliable", ["model-a"], cost_multiplier=1.0, reliability_score=0.9)
        decision = pa.find_cheapest("model-a", base_cost=0.01, min_reliability=0.5)
        assert decision.selected_provider == "reliable"

    def test_find_cheapest_unavailable_excluded(self):
        """Kullanilamayanlar harici."""
        pa = ProviderArbitrage()
        p = pa.register_provider("down", ["model-a"], cost_multiplier=0.5)
        pa.update_status(p.provider_id, "unavailable")
        pa.register_provider("up", ["model-a"], cost_multiplier=1.0)
        decision = pa.find_cheapest("model-a", base_cost=0.01)
        assert decision.selected_provider == "up"

    def test_find_cheapest_degraded_included(self):
        """Bozulmus saglayici dahil edilmeli."""
        pa = ProviderArbitrage()
        p = pa.register_provider("degraded_p", ["model-a"], cost_multiplier=0.5)
        pa.update_status(p.provider_id, "degraded")
        decision = pa.find_cheapest("model-a", base_cost=0.01)
        assert decision.selected_provider == "degraded_p"

    def test_update_status(self):
        """Saglayici durumu guncelleme."""
        pa = ProviderArbitrage()
        p = pa.register_provider("test", ["model-a"])
        result = pa.update_status(p.provider_id, "degraded", latency_ms=500)
        assert result is True

    def test_update_status_unknown(self):
        """Bilinmeyen saglayici guncelleme."""
        pa = ProviderArbitrage()
        result = pa.update_status("unknown", "degraded")
        assert result is False

    def test_stats(self):
        """Istatistikler."""
        pa = ProviderArbitrage()
        pa.register_provider("test", ["model-a"])
        pa.find_cheapest("model-a", base_cost=0.01)
        stats = pa.get_stats()
        assert stats["total_providers"] == 1
        assert stats["total_decisions"] == 1
        assert stats["total_savings_usd"] >= 0


# ============================================================
# CostPerTemplate Testleri
# ============================================================


class TestCostPerTemplate:
    """CostPerTemplate testleri."""

    def test_init(self):
        """Baslama testi."""
        cpt = CostPerTemplate()
        assert cpt is not None

    def test_record_cost(self):
        """Sablon maliyet kaydi."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "E-ticaret", 0.05, tokens=500, model_name="gpt-4o")
        stats = cpt.get_stats()
        assert stats["tracked_templates"] == 1

    def test_record_cost_multiple(self):
        """Coklu maliyet kaydi."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "E-ticaret", 0.05, tokens=500)
        cpt.record_cost("t1", "E-ticaret", 0.10, tokens=1000)
        report = cpt.generate_report("t1")
        assert report is not None
        assert report.total_requests == 2
        assert report.total_cost > 0

    def test_record_cost_with_skill(self):
        """Beceri bazli maliyet kaydi."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "Test", 0.05, skill_name="OrderTracker")
        report = cpt.generate_report("t1")
        assert "OrderTracker" in report.cost_by_skill

    def test_record_cost_with_model(self):
        """Model bazli maliyet kaydi."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "Test", 0.05, model_name="gpt-4o")
        report = cpt.generate_report("t1")
        assert "gpt-4o" in report.cost_by_model

    def test_generate_report(self):
        """Rapor olusturma."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "E-ticaret", 0.05, tokens=500, model_name="gpt-4o")
        report = cpt.generate_report("t1")
        assert report is not None
        assert report.template_id == "t1"
        assert report.template_name == "E-ticaret"
        assert report.avg_cost_per_request > 0

    def test_generate_report_unknown(self):
        """Bilinmeyen sablon raporu."""
        cpt = CostPerTemplate()
        report = cpt.generate_report("unknown")
        assert report is None

    def test_generate_report_high_cost_suggestion(self):
        """Yuksek maliyet onerisi."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "Expensive", 60.0, model_name="claude-opus-4")
        report = cpt.generate_report("t1")
        assert any("Yuksek maliyet" in s for s in report.optimization_suggestions)

    def test_generate_report_expensive_model_suggestion(self):
        """En pahali model onerisi."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "Test", 10.0, model_name="claude-opus-4")
        cpt.record_cost("t1", "Test", 2.0, model_name="gpt-4o-mini")
        report = cpt.generate_report("t1")
        assert any("En pahali model" in s for s in report.optimization_suggestions)

    def test_generate_report_high_requests_suggestion(self):
        """Yuksek istek onerisi."""
        cpt = CostPerTemplate()
        for _ in range(1001):
            cpt.record_cost("t1", "Busy", 0.001)
        report = cpt.generate_report("t1")
        assert any("cache" in s for s in report.optimization_suggestions)

    def test_compare_templates(self):
        """Sablon karsilastirma."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "A", 10.0)
        cpt.record_cost("t2", "B", 5.0)
        cpt.record_cost("t3", "C", 15.0)
        comparison = cpt.compare_templates()
        assert len(comparison) == 3
        assert comparison[0]["total_cost"] >= comparison[1]["total_cost"]
        assert comparison[1]["total_cost"] >= comparison[2]["total_cost"]

    def test_compare_templates_empty(self):
        """Bos sablon karsilastirma."""
        cpt = CostPerTemplate()
        comparison = cpt.compare_templates()
        assert comparison == []

    def test_compare_templates_avg_cost(self):
        """Ortalama maliyet karsilastirma."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "A", 10.0)
        cpt.record_cost("t1", "A", 20.0)
        comparison = cpt.compare_templates()
        assert comparison[0]["avg_cost"] == 15.0

    def test_stats(self):
        """Istatistikler."""
        cpt = CostPerTemplate()
        cpt.record_cost("t1", "Test", 1.0)
        cpt.generate_report("t1")
        stats = cpt.get_stats()
        assert stats["tracked_templates"] == 1
        assert stats["total_reports"] == 1


# ============================================================
# CostControlOrchestrator Testleri
# ============================================================


class TestCostControlOrchestrator:
    """CostControlOrchestrator testleri."""

    def test_init(self):
        """Baslama testi."""
        orch = CostControlOrchestrator()
        assert orch is not None
        assert orch.tracker is not None
        assert orch.limiter is not None
        assert orch.alerts is not None
        assert orch.router is not None
        assert orch.heartbeat is not None
        assert orch.compression is not None
        assert orch.projection is not None
        assert orch.arbitrage is not None
        assert orch.template_cost is not None

    def test_process_request_allowed(self):
        """Izin verilen istek isleme."""
        orch = CostControlOrchestrator()
        result = orch.process_request(
            session_id="s1",
            model_name="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
        )
        assert result["allowed"] is True
        assert result["blocked"] is False
        assert result["cost_usd"] > 0

    def test_process_request_with_routing(self):
        """Model yonlendirmeli istek isleme."""
        orch = CostControlOrchestrator()
        result = orch.process_request(
            session_id="s1",
            task_type="analysis",
            complexity="moderate",
            input_tokens=500,
            output_tokens=200,
        )
        assert result["allowed"] is True
        assert result["model"] != ""
        assert result["route"] is not None
        assert "model" in result["route"]
        assert "provider" in result["route"]

    def test_process_request_blocked(self):
        """Engellenen istek isleme."""
        orch = CostControlOrchestrator()
        budget = orch.limiter.set_limit("Test", "daily", 0.001, hard_stop=True)
        budget.current_spend = 0.001
        result = orch.process_request(
            session_id="s1",
            model_name="claude-opus-4",
            input_tokens=10000,
            output_tokens=5000,
        )
        assert result["blocked"] is True
        assert result["allowed"] is False
        assert result["reason"] == "budget_exceeded"

    def test_process_request_with_template(self):
        """Sablonlu istek isleme."""
        orch = CostControlOrchestrator()
        result = orch.process_request(
            session_id="s1",
            model_name="gpt-4o-mini",
            input_tokens=100,
            output_tokens=50,
            template_id="tmpl-1",
        )
        assert result["allowed"] is True
        stats = orch.template_cost.get_stats()
        assert stats["tracked_templates"] == 1

    def test_process_request_zero_tokens(self):
        """Sifir tokenli istek isleme."""
        orch = CostControlOrchestrator()
        result = orch.process_request(session_id="s1", model_name="gpt-4o")
        assert result["allowed"] is True
        assert result["cost_usd"] == 0.0

    def test_setup_default_budgets(self):
        """Varsayilan butce kurulumu."""
        orch = CostControlOrchestrator()
        budgets = orch.setup_default_budgets(daily_limit=20.0, monthly_limit=500.0)
        assert "daily_budget_id" in budgets
        assert "monthly_budget_id" in budgets
        assert orch.limiter.get_stats()["total_budgets"] == 2
        assert orch.alerts.get_stats()["total_rules"] == 2

    def test_get_cost_summary(self):
        """Maliyet ozeti."""
        orch = CostControlOrchestrator()
        orch.process_request("s1", model_name="gpt-4o-mini", input_tokens=100, output_tokens=50)
        summary = orch.get_cost_summary()
        assert "total_cost_usd" in summary
        assert "total_tokens" in summary
        assert "total_entries" in summary
        assert "by_model" in summary
        assert "budgets" in summary
        assert "pending_alerts" in summary
        assert "heartbeat_savings" in summary

    def test_get_stats(self):
        """Istatistikler."""
        orch = CostControlOrchestrator()
        orch.process_request("s1", model_name="gpt-4o-mini", input_tokens=100, output_tokens=50)
        stats = orch.get_stats()
        assert "orchestrator" in stats
        assert "tracker" in stats
        assert "limiter" in stats
        assert "alerts" in stats
        assert "router" in stats
        assert "heartbeat" in stats
        assert "compression" in stats
        assert "projection" in stats
        assert "arbitrage" in stats
        assert "template_cost" in stats
        assert stats["orchestrator"]["pipelines_run"] == 1
        assert stats["orchestrator"]["requests_allowed"] == 1
        assert stats["orchestrator"]["requests_blocked"] == 0

    def test_multiple_requests(self):
        """Coklu istek isleme."""
        orch = CostControlOrchestrator()
        for i in range(5):
            result = orch.process_request(
                session_id=f"s{i}",
                model_name="claude-haiku-3.5",
                input_tokens=100,
                output_tokens=50,
            )
            assert result["allowed"] is True
        stats = orch.get_stats()
        assert stats["orchestrator"]["requests_allowed"] == 5

    def test_template_cost_tracking(self):
        """Sablon maliyet takibi."""
        orch = CostControlOrchestrator()
        orch.process_request(
            session_id="s1",
            model_name="claude-sonnet-4",
            input_tokens=500,
            output_tokens=200,
            template_id="ecommerce",
        )
        report = orch.template_cost.generate_report("ecommerce")
        assert report is not None
        assert report.total_cost > 0

    def test_heartbeat_optimization(self):
        """Heartbeat optimizasyonu entegrasyonu."""
        orch = CostControlOrchestrator()
        config = orch.heartbeat.configure(mode="minimal", interval_seconds=600)
        assert config.estimated_monthly_savings > 0

    def test_token_compression(self):
        """Token sikistirma entegrasyonu."""
        orch = CostControlOrchestrator()
        result = orch.compression.compress("A" * 10000, strategy="selective")
        assert result.savings_tokens > 0

    def test_provider_arbitrage(self):
        """Saglayici arbitraji entegrasyonu."""
        orch = CostControlOrchestrator()
        orch.arbitrage.register_provider("cheap", ["claude-sonnet-4"], cost_multiplier=0.8)
        orch.arbitrage.register_provider("expensive", ["claude-sonnet-4"], cost_multiplier=1.5)
        decision = orch.arbitrage.find_cheapest("claude-sonnet-4", 0.01)
        assert decision.selected_provider == "cheap"

    def test_full_pipeline_integration(self):
        """Tam pipeline entegrasyonu."""
        orch = CostControlOrchestrator()
        orch.setup_default_budgets(daily_limit=10.0, monthly_limit=200.0)
        for i in range(5):
            result = orch.process_request(
                session_id=f"s{i}",
                model_name="gpt-4o-mini",
                input_tokens=100,
                output_tokens=50,
            )
            assert result["allowed"] is True
        summary = orch.get_cost_summary()
        assert summary["total_cost_usd"] > 0
        assert summary["total_tokens"] == 750
        stats = orch.get_stats()
        assert stats["orchestrator"]["requests_allowed"] == 5
