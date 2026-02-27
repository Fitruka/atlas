"""ATLAS Managed Cloud Deployment test suite."""

import pytest
from unittest.mock import patch

from app.core.atlascloud import (
    AtlasCloudOrchestrator,
    AutoScaler,
    ManagedUpdates,
    BackupRestore,
    HealthMonitoring,
    OnboardingWizard,
    AtlasCloudFullOrchestrator,
)
from app.models.atlascloud_models import (
    BackupType,
    CloudBackup,
    CloudDeployment,
    CloudUpdate,
    DeploymentStatus,
    HealthCheck,
    HealthStatus,
    InstanceSize,
    Region,
    ScaleDirection,
    ScaleEvent,
    UpdateStrategy,
    WizardStep,
)


# ------------------------------------------------------------------ #
#  Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def orchestrator():
    """AtlasCloudOrchestrator ornegi."""
    return AtlasCloudOrchestrator()


@pytest.fixture
def scaler():
    """AutoScaler ornegi."""
    return AutoScaler()


@pytest.fixture
def updates():
    """ManagedUpdates ornegi."""
    return ManagedUpdates()


@pytest.fixture
def backup_restore():
    """BackupRestore ornegi."""
    return BackupRestore()


@pytest.fixture
def health():
    """HealthMonitoring ornegi."""
    return HealthMonitoring()


@pytest.fixture
def wizard():
    """OnboardingWizard ornegi."""
    return OnboardingWizard()


@pytest.fixture
def full_orchestrator():
    """AtlasCloudFullOrchestrator ornegi."""
    return AtlasCloudFullOrchestrator()


# ------------------------------------------------------------------ #
#  Model Enum Tests
# ------------------------------------------------------------------ #


class TestModels:
    """Model ve enum degerlerini dogrulayan testler."""

    def test_deployment_status_values(self):
        assert DeploymentStatus.PENDING == "pending"
        assert DeploymentStatus.PROVISIONING == "provisioning"
        assert DeploymentStatus.RUNNING == "running"
        assert DeploymentStatus.UPDATING == "updating"
        assert DeploymentStatus.STOPPING == "stopping"
        assert DeploymentStatus.STOPPED == "stopped"
        assert DeploymentStatus.FAILED == "failed"

    def test_scale_direction_values(self):
        assert ScaleDirection.UP == "up"
        assert ScaleDirection.DOWN == "down"
        assert ScaleDirection.NONE == "none"

    def test_update_strategy_values(self):
        assert UpdateStrategy.ROLLING == "rolling"
        assert UpdateStrategy.BLUE_GREEN == "blue_green"
        assert UpdateStrategy.CANARY == "canary"

    def test_backup_type_values(self):
        assert BackupType.FULL == "full"
        assert BackupType.INCREMENTAL == "incremental"
        assert BackupType.SNAPSHOT == "snapshot"

    def test_health_status_values(self):
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"

    def test_instance_size_values(self):
        assert InstanceSize.SMALL == "small"
        assert InstanceSize.MEDIUM == "medium"
        assert InstanceSize.LARGE == "large"
        assert InstanceSize.XLARGE == "xlarge"

    def test_region_values(self):
        assert Region.US_EAST == "us_east"
        assert Region.US_WEST == "us_west"
        assert Region.EU_WEST == "eu_west"
        assert Region.EU_CENTRAL == "eu_central"
        assert Region.ASIA_PACIFIC == "asia_pacific"

    def test_cloud_deployment_defaults(self):
        dep = CloudDeployment()
        assert dep.id != ""
        assert dep.name == ""
        assert dep.tenant_id == ""
        assert dep.region == Region.EU_CENTRAL
        assert dep.instance_size == InstanceSize.MEDIUM
        assert dep.status == DeploymentStatus.PENDING
        assert dep.version == "1.0.0"
        assert dep.replicas == 1
        assert dep.url == ""
        assert dep.created_at is not None
        assert dep.updated_at is not None

    def test_scale_event_defaults(self):
        evt = ScaleEvent()
        assert evt.id != ""
        assert evt.deployment_id == ""
        assert evt.direction == ScaleDirection.NONE
        assert evt.from_replicas == 1
        assert evt.to_replicas == 1
        assert evt.reason == ""
        assert evt.triggered_at is not None

    def test_cloud_update_defaults(self):
        upd = CloudUpdate()
        assert upd.id != ""
        assert upd.deployment_id == ""
        assert upd.from_version == ""
        assert upd.to_version == ""
        assert upd.strategy == UpdateStrategy.ROLLING
        assert upd.status == DeploymentStatus.PENDING
        assert upd.completed_at is None
        assert upd.rollback_available is True

    def test_cloud_backup_defaults(self):
        bak = CloudBackup()
        assert bak.id != ""
        assert bak.deployment_id == ""
        assert bak.backup_type == BackupType.FULL
        assert bak.size_mb == 0.0
        assert bak.storage_path == ""
        assert bak.expires_at is None
        assert bak.verified is False

    def test_health_check_defaults(self):
        hc = HealthCheck()
        assert hc.id != ""
        assert hc.deployment_id == ""
        assert hc.status == HealthStatus.UNKNOWN
        assert hc.cpu_pct == 0.0
        assert hc.memory_pct == 0.0
        assert hc.disk_pct == 0.0
        assert hc.response_time_ms == 0.0

    def test_wizard_step_defaults(self):
        ws = WizardStep()
        assert ws.id != ""
        assert ws.step_number == 0
        assert ws.title == ""
        assert ws.description == ""
        assert ws.completed is False
        assert ws.data == {}

    def test_unique_model_ids(self):
        ids = {CloudDeployment().id for _ in range(20)}
        assert len(ids) == 20


# ------------------------------------------------------------------ #
#  AtlasCloudOrchestrator Tests
# ------------------------------------------------------------------ #


class TestAtlasCloudOrchestrator:
    """Bulut dagitim orkestratoru testleri."""

    def test_deploy_creates_running_deployment(self, orchestrator):
        dep = orchestrator.deploy("app1", "t1")
        assert dep.name == "app1"
        assert dep.tenant_id == "t1"
        assert dep.status == DeploymentStatus.RUNNING

    def test_deploy_sets_default_region_and_size(self, orchestrator):
        dep = orchestrator.deploy("app1", "t1")
        assert dep.region == Region.EU_CENTRAL
        assert dep.instance_size == InstanceSize.MEDIUM

    def test_deploy_with_custom_region_and_size(self, orchestrator):
        dep = orchestrator.deploy(
            "app2", "t2",
            region=Region.US_WEST,
            size=InstanceSize.XLARGE,
        )
        assert dep.region == Region.US_WEST
        assert dep.instance_size == InstanceSize.XLARGE

    def test_deploy_generates_url(self, orchestrator):
        dep = orchestrator.deploy("myservice", "t1")
        assert dep.url == "https://myservice.atlas-cloud.io"

    def test_deploy_sets_version(self, orchestrator):
        dep = orchestrator.deploy("app1", "t1", version="2.5.0")
        assert dep.version == "2.5.0"

    def test_deploy_replicas_default_one(self, orchestrator):
        dep = orchestrator.deploy("app1", "t1")
        assert dep.replicas == 1

    def test_deploy_increments_stats(self, orchestrator):
        orchestrator.deploy("a1", "t1")
        orchestrator.deploy("a2", "t1")
        stats = orchestrator.get_stats()
        assert stats["deployments_created"] == 2

    def test_get_deployment_returns_existing(self, orchestrator):
        dep = orchestrator.deploy("app1", "t1")
        fetched = orchestrator.get_deployment(dep.id)
        assert fetched is not None
        assert fetched.id == dep.id

    def test_get_deployment_returns_none_missing(self, orchestrator):
        assert orchestrator.get_deployment("nonexistent") is None

    def test_list_deployments_all(self, orchestrator):
        orchestrator.deploy("a1", "t1")
        orchestrator.deploy("a2", "t2")
        result = orchestrator.list_deployments()
        assert len(result) == 2

    def test_list_deployments_filter_by_tenant(self, orchestrator):
        orchestrator.deploy("a1", "tenant_a")
        orchestrator.deploy("a2", "tenant_b")
        orchestrator.deploy("a3", "tenant_a")
        result = orchestrator.list_deployments(tenant_id="tenant_a")
        assert len(result) == 2

    def test_list_deployments_filter_by_status(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        orchestrator.deploy("a2", "t1")
        orchestrator.stop_deployment(dep.id)
        running = orchestrator.list_deployments(status=DeploymentStatus.RUNNING)
        assert len(running) == 1
        stopped = orchestrator.list_deployments(status=DeploymentStatus.STOPPED)
        assert len(stopped) == 1

    def test_list_deployments_filter_tenant_and_status(self, orchestrator):
        orchestrator.deploy("a1", "t1")
        d2 = orchestrator.deploy("a2", "t1")
        orchestrator.deploy("a3", "t2")
        orchestrator.stop_deployment(d2.id)
        result = orchestrator.list_deployments(
            tenant_id="t1", status=DeploymentStatus.RUNNING,
        )
        assert len(result) == 1

    def test_update_deployment_changes_version(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1", version="1.0.0")
        update = orchestrator.update_deployment(dep.id, "2.0.0")
        assert update is not None
        assert update.from_version == "1.0.0"
        assert update.to_version == "2.0.0"
        refreshed = orchestrator.get_deployment(dep.id)
        assert refreshed.version == "2.0.0"

    def test_update_deployment_rolling_strategy(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        update = orchestrator.update_deployment(
            dep.id, "2.0.0", strategy=UpdateStrategy.ROLLING,
        )
        assert update.strategy == UpdateStrategy.ROLLING

    def test_update_deployment_blue_green_strategy(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        update = orchestrator.update_deployment(
            dep.id, "2.0.0", strategy=UpdateStrategy.BLUE_GREEN,
        )
        assert update.strategy == UpdateStrategy.BLUE_GREEN

    def test_update_deployment_nonexistent_returns_none(self, orchestrator):
        assert orchestrator.update_deployment("bad", "2.0.0") is None

    def test_update_deployment_increments_stats(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        orchestrator.update_deployment(dep.id, "2.0.0")
        stats = orchestrator.get_stats()
        assert stats["updates_applied"] == 1

    def test_update_deployment_sets_completed_at(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        update = orchestrator.update_deployment(dep.id, "2.0.0")
        assert update.completed_at is not None

    def test_stop_deployment_success(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        result = orchestrator.stop_deployment(dep.id)
        assert result is True
        assert orchestrator.get_deployment(dep.id).status == DeploymentStatus.STOPPED

    def test_stop_deployment_nonexistent_returns_false(self, orchestrator):
        assert orchestrator.stop_deployment("nope") is False

    def test_stop_increments_stats(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        orchestrator.stop_deployment(dep.id)
        assert orchestrator.get_stats()["deployments_stopped"] == 1

    def test_destroy_deployment_success(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        result = orchestrator.destroy_deployment(dep.id)
        assert result is True
        assert orchestrator.get_deployment(dep.id) is None

    def test_destroy_deployment_nonexistent_returns_false(self, orchestrator):
        assert orchestrator.destroy_deployment("nope") is False

    def test_destroy_increments_stats(self, orchestrator):
        dep = orchestrator.deploy("a1", "t1")
        orchestrator.destroy_deployment(dep.id)
        assert orchestrator.get_stats()["deployments_destroyed"] == 1

    def test_get_deployment_url(self, orchestrator):
        dep = orchestrator.deploy("myapp", "t1")
        url = orchestrator.get_deployment_url(dep.id)
        assert url == "https://myapp.atlas-cloud.io"

    def test_get_deployment_url_missing(self, orchestrator):
        assert orchestrator.get_deployment_url("bad") is None

    def test_get_stats_running_count(self, orchestrator):
        orchestrator.deploy("a1", "t1")
        orchestrator.deploy("a2", "t1")
        d3 = orchestrator.deploy("a3", "t1")
        orchestrator.stop_deployment(d3.id)
        stats = orchestrator.get_stats()
        assert stats["running_deployments"] == 2
        assert stats["total_deployments"] == 3

    def test_get_stats_initial_values(self, orchestrator):
        stats = orchestrator.get_stats()
        assert stats["total_deployments"] == 0
        assert stats["deployments_created"] == 0
        assert stats["updates_applied"] == 0


# ------------------------------------------------------------------ #
#  AutoScaler Tests
# ------------------------------------------------------------------ #


class TestAutoScaler:
    """Otomatik olcekleyici testleri."""

    def test_configure_returns_config(self, scaler):
        cfg = scaler.configure("d1")
        assert cfg["deployment_id"] == "d1"
        assert cfg["min_replicas"] == 1
        assert cfg["max_replicas"] == 10
        assert cfg["target_cpu"] == 70.0
        assert cfg["target_memory"] == 75.0
        assert cfg["cooldown_seconds"] == 300
        assert "configured_at" in cfg

    def test_configure_custom_values(self, scaler):
        cfg = scaler.configure(
            "d1", min_replicas=2, max_replicas=20,
            target_cpu=60.0, target_memory=80.0,
            cooldown_seconds=120,
        )
        assert cfg["min_replicas"] == 2
        assert cfg["max_replicas"] == 20
        assert cfg["target_cpu"] == 60.0
        assert cfg["target_memory"] == 80.0
        assert cfg["cooldown_seconds"] == 120

    def test_configure_increments_stats(self, scaler):
        scaler.configure("d1")
        scaler.configure("d2")
        assert scaler.get_stats()["configs_set"] == 2

    def test_configure_sets_initial_replicas(self, scaler):
        scaler.configure("d1", min_replicas=3)
        assert scaler._current_replicas["d1"] == 3

    def test_configure_does_not_overwrite_current_replicas(self, scaler):
        scaler.configure("d1", min_replicas=1)
        scaler._current_replicas["d1"] = 5
        scaler.configure("d1", min_replicas=2)
        assert scaler._current_replicas["d1"] == 5

    def test_evaluate_no_config_returns_none(self, scaler):
        result = scaler.evaluate("no_config", 90, 90)
        assert result is None
        assert scaler.get_stats()["evaluations"] == 1

    def test_evaluate_scale_up_high_cpu(self, scaler):
        scaler.configure("d1", cooldown_seconds=0)
        event = scaler.evaluate("d1", current_cpu=90, current_memory=50)
        assert event is not None
        assert event.direction == ScaleDirection.UP

    def test_evaluate_scale_up_high_memory(self, scaler):
        scaler.configure("d1", cooldown_seconds=0)
        event = scaler.evaluate("d1", current_cpu=50, current_memory=90)
        assert event is not None
        assert event.direction == ScaleDirection.UP

    def test_evaluate_scale_down_low_utilization(self, scaler):
        scaler.configure("d1", cooldown_seconds=0, min_replicas=1)
        scaler._current_replicas["d1"] = 5
        event = scaler.evaluate("d1", current_cpu=10, current_memory=10)
        assert event is not None
        assert event.direction == ScaleDirection.DOWN

    def test_evaluate_no_scale_moderate_load(self, scaler):
        scaler.configure("d1", cooldown_seconds=0)
        event = scaler.evaluate("d1", current_cpu=50, current_memory=50)
        assert event is None

    def test_evaluate_respects_cooldown(self, scaler):
        scaler.configure("d1", cooldown_seconds=9999)
        # First evaluation triggers scale
        evt1 = scaler.evaluate("d1", current_cpu=90, current_memory=90)
        assert evt1 is not None
        # Second evaluation within cooldown returns None
        evt2 = scaler.evaluate("d1", current_cpu=90, current_memory=90)
        assert evt2 is None

    def test_evaluate_max_replicas_cap(self, scaler):
        scaler.configure("d1", max_replicas=2, cooldown_seconds=0)
        scaler._current_replicas["d1"] = 2
        # Already at max, should not scale up
        event = scaler.evaluate("d1", current_cpu=95, current_memory=95)
        assert event is None

    def test_evaluate_min_replicas_floor(self, scaler):
        scaler.configure("d1", min_replicas=1, cooldown_seconds=0)
        scaler._current_replicas["d1"] = 1
        # Already at min, should not scale down
        event = scaler.evaluate("d1", current_cpu=5, current_memory=5)
        assert event is None

    def test_scale_up(self, scaler):
        scaler.configure("d1")
        event = scaler.scale("d1", ScaleDirection.UP, 2)
        assert event.direction == ScaleDirection.UP
        assert event.from_replicas == 1
        assert event.to_replicas == 3
        assert event.reason == "cpu_or_memory_threshold_exceeded"

    def test_scale_down(self, scaler):
        scaler.configure("d1", min_replicas=1)
        scaler._current_replicas["d1"] = 5
        event = scaler.scale("d1", ScaleDirection.DOWN, 2)
        assert event.direction == ScaleDirection.DOWN
        assert event.from_replicas == 5
        assert event.to_replicas == 3
        assert event.reason == "resources_underutilized"

    def test_scale_none_direction(self, scaler):
        scaler.configure("d1")
        event = scaler.scale("d1", ScaleDirection.NONE)
        assert event.to_replicas == event.from_replicas
        assert event.reason == "no_change"

    def test_scale_up_capped_at_max(self, scaler):
        scaler.configure("d1", max_replicas=3)
        scaler._current_replicas["d1"] = 2
        event = scaler.scale("d1", ScaleDirection.UP, 5)
        assert event.to_replicas == 3

    def test_scale_down_floored_at_min(self, scaler):
        scaler.configure("d1", min_replicas=2)
        scaler._current_replicas["d1"] = 3
        event = scaler.scale("d1", ScaleDirection.DOWN, 5)
        assert event.to_replicas == 2

    def test_scale_updates_current_replicas(self, scaler):
        scaler.configure("d1")
        scaler.scale("d1", ScaleDirection.UP, 3)
        assert scaler._current_replicas["d1"] == 4

    def test_scale_records_last_scale_time(self, scaler):
        scaler.configure("d1")
        scaler.scale("d1", ScaleDirection.UP)
        assert "d1" in scaler._last_scale
        assert scaler._last_scale["d1"] > 0

    def test_scale_increments_stats(self, scaler):
        scaler.configure("d1")
        scaler.scale("d1", ScaleDirection.UP)
        scaler.scale("d1", ScaleDirection.DOWN)
        stats = scaler.get_stats()
        assert stats["scale_ups"] == 1
        assert stats["scale_downs"] == 1

    def test_get_config_existing(self, scaler):
        scaler.configure("d1")
        cfg = scaler.get_config("d1")
        assert cfg is not None
        assert cfg["deployment_id"] == "d1"

    def test_get_config_missing(self, scaler):
        assert scaler.get_config("nope") is None

    def test_get_history_filters_by_deployment(self, scaler):
        scaler.configure("d1")
        scaler.configure("d2")
        scaler.scale("d1", ScaleDirection.UP)
        scaler.scale("d2", ScaleDirection.DOWN)
        scaler.scale("d1", ScaleDirection.UP)
        history = scaler.get_history("d1")
        assert len(history) == 2
        assert all(e.deployment_id == "d1" for e in history)

    def test_get_history_empty(self, scaler):
        assert scaler.get_history("d1") == []

    def test_get_stats_initial(self, scaler):
        stats = scaler.get_stats()
        assert stats["total_configs"] == 0
        assert stats["total_events"] == 0
        assert stats["scale_ups"] == 0
        assert stats["scale_downs"] == 0
        assert stats["evaluations"] == 0
        assert stats["configs_set"] == 0

    def test_scale_without_config_uses_defaults(self, scaler):
        event = scaler.scale("unconfigured", ScaleDirection.UP, 2)
        assert event.from_replicas == 1
        assert event.to_replicas == 3


# ------------------------------------------------------------------ #
#  ManagedUpdates Tests
# ------------------------------------------------------------------ #


class TestManagedUpdates:
    """Yonetilen guncelleme testleri."""

    def test_plan_update_creates_pending(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        assert upd.deployment_id == "d1"
        assert upd.to_version == "2.0.0"
        assert upd.status == DeploymentStatus.PENDING
        assert upd.rollback_available is True

    def test_plan_update_default_strategy(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        assert upd.strategy == UpdateStrategy.ROLLING

    def test_plan_update_canary_strategy(self, updates):
        upd = updates.plan_update("d1", "2.0.0", strategy=UpdateStrategy.CANARY)
        assert upd.strategy == UpdateStrategy.CANARY

    def test_plan_update_blue_green_strategy(self, updates):
        upd = updates.plan_update("d1", "2.0.0", strategy=UpdateStrategy.BLUE_GREEN)
        assert upd.strategy == UpdateStrategy.BLUE_GREEN

    def test_plan_update_increments_stats(self, updates):
        updates.plan_update("d1", "2.0.0")
        assert updates.get_stats()["updates_planned"] == 1

    def test_execute_update_transitions_to_running(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        result = updates.execute_update(upd.id)
        assert result is not None
        assert result.status == DeploymentStatus.RUNNING
        assert result.completed_at is not None

    def test_execute_update_nonexistent_returns_none(self, updates):
        assert updates.execute_update("bad_id") is None

    def test_execute_update_not_pending_returns_update(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        updates.execute_update(upd.id)
        # Already running, call execute again
        result = updates.execute_update(upd.id)
        assert result is not None
        assert result.status == DeploymentStatus.RUNNING

    def test_execute_update_increments_stats(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        updates.execute_update(upd.id)
        assert updates.get_stats()["updates_executed"] == 1

    def test_execute_update_canary_strategy_works(self, updates):
        upd = updates.plan_update("d1", "2.0.0", strategy=UpdateStrategy.CANARY)
        result = updates.execute_update(upd.id)
        assert result.status == DeploymentStatus.RUNNING

    def test_execute_update_blue_green_strategy_works(self, updates):
        upd = updates.plan_update("d1", "2.0.0", strategy=UpdateStrategy.BLUE_GREEN)
        result = updates.execute_update(upd.id)
        assert result.status == DeploymentStatus.RUNNING

    def test_rollback_success(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        updates.execute_update(upd.id)
        result = updates.rollback(upd.id)
        assert result is True
        assert updates.get_stats()["rollbacks_performed"] == 1

    def test_rollback_disables_further_rollback(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        updates.execute_update(upd.id)
        updates.rollback(upd.id)
        # Second rollback should fail
        result = updates.rollback(upd.id)
        assert result is False

    def test_rollback_nonexistent_returns_false(self, updates):
        assert updates.rollback("bad") is False

    def test_rollback_increments_failed_stats(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        updates.execute_update(upd.id)
        updates.rollback(upd.id)
        updates.rollback(upd.id)  # fails
        stats = updates.get_stats()
        assert stats["rollbacks_performed"] == 1
        assert stats["rollbacks_failed"] == 1

    def test_rollback_records_history(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        updates.execute_update(upd.id)
        updates.rollback(upd.id)
        assert len(updates._rollbacks) == 1
        rec = updates._rollbacks[0]
        assert rec["update_id"] == upd.id
        assert rec["from_version"] == "2.0.0"

    def test_get_update_existing(self, updates):
        upd = updates.plan_update("d1", "2.0.0")
        fetched = updates.get_update(upd.id)
        assert fetched is not None
        assert fetched.id == upd.id

    def test_get_update_nonexistent(self, updates):
        assert updates.get_update("nope") is None

    def test_list_updates_by_deployment(self, updates):
        updates.plan_update("d1", "2.0.0")
        updates.plan_update("d2", "3.0.0")
        updates.plan_update("d1", "2.1.0")
        result = updates.list_updates("d1")
        assert len(result) == 2
        assert all(u.deployment_id == "d1" for u in result)

    def test_list_updates_empty(self, updates):
        assert updates.list_updates("d1") == []

    def test_get_available_versions(self, updates):
        versions = updates.get_available_versions()
        assert isinstance(versions, list)
        assert "1.0.0" in versions
        assert "3.0.0" in versions
        assert len(versions) == 7

    def test_get_stats_initial(self, updates):
        stats = updates.get_stats()
        assert stats["total_updates"] == 0
        assert stats["updates_planned"] == 0
        assert stats["updates_executed"] == 0
        assert stats["rollbacks_performed"] == 0
        assert stats["rollbacks_failed"] == 0
        assert stats["available_versions"] == 7

    def test_multiple_plans_and_executions(self, updates):
        u1 = updates.plan_update("d1", "2.0.0")
        u2 = updates.plan_update("d1", "3.0.0")
        updates.execute_update(u1.id)
        updates.execute_update(u2.id)
        stats = updates.get_stats()
        assert stats["total_updates"] == 2
        assert stats["updates_executed"] == 2


# ------------------------------------------------------------------ #
#  BackupRestore Tests
# ------------------------------------------------------------------ #


class TestBackupRestore:
    """Yedekleme ve geri yukleme testleri."""

    def test_create_backup_full(self, backup_restore):
        bak = backup_restore.create_backup("d1", BackupType.FULL)
        assert bak.deployment_id == "d1"
        assert bak.backup_type == BackupType.FULL
        assert bak.size_mb > 0
        assert bak.verified is False
        assert "/backups/atlas-cloud/d1/" in bak.storage_path
        assert bak.expires_at is not None

    def test_create_backup_incremental(self, backup_restore):
        bak = backup_restore.create_backup("d1", BackupType.INCREMENTAL)
        assert bak.backup_type == BackupType.INCREMENTAL
        assert bak.size_mb > 0

    def test_create_backup_snapshot(self, backup_restore):
        bak = backup_restore.create_backup("d1", BackupType.SNAPSHOT)
        assert bak.backup_type == BackupType.SNAPSHOT

    def test_create_backup_increments_stats(self, backup_restore):
        backup_restore.create_backup("d1")
        backup_restore.create_backup("d1")
        assert backup_restore.get_stats()["backups_created"] == 2

    def test_create_backup_default_retention(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        diff = bak.expires_at - bak.created_at
        assert diff.days == 30

    def test_create_backup_custom_retention(self, backup_restore):
        backup_restore.set_retention("d1", 7)
        bak = backup_restore.create_backup("d1")
        diff = bak.expires_at - bak.created_at
        assert diff.days == 7

    def test_restore_success(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        result = backup_restore.restore(bak.id)
        assert result["success"] is True
        assert result["backup_id"] == bak.id
        assert result["target_deployment_id"] == "d1"

    def test_restore_auto_verifies(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        assert bak.verified is False
        backup_restore.restore(bak.id)
        assert bak.verified is True

    def test_restore_to_different_target(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        result = backup_restore.restore(bak.id, target_deployment_id="d2")
        assert result["target_deployment_id"] == "d2"

    def test_restore_nonexistent_backup(self, backup_restore):
        result = backup_restore.restore("bad_id")
        assert result["success"] is False
        assert result["error"] == "backup_not_found"

    def test_restore_increments_stats(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        backup_restore.restore(bak.id)
        assert backup_restore.get_stats()["restores_performed"] == 1

    def test_get_backup_existing(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        fetched = backup_restore.get_backup(bak.id)
        assert fetched is not None
        assert fetched.id == bak.id

    def test_get_backup_missing(self, backup_restore):
        assert backup_restore.get_backup("bad") is None

    def test_list_backups_by_deployment(self, backup_restore):
        backup_restore.create_backup("d1")
        backup_restore.create_backup("d2")
        backup_restore.create_backup("d1")
        result = backup_restore.list_backups("d1")
        assert len(result) == 2

    def test_list_backups_filter_by_type(self, backup_restore):
        backup_restore.create_backup("d1", BackupType.FULL)
        backup_restore.create_backup("d1", BackupType.INCREMENTAL)
        backup_restore.create_backup("d1", BackupType.FULL)
        result = backup_restore.list_backups("d1", backup_type=BackupType.FULL)
        assert len(result) == 2
        assert all(b.backup_type == BackupType.FULL for b in result)

    def test_list_backups_sorted_by_date_desc(self, backup_restore):
        b1 = backup_restore.create_backup("d1")
        b2 = backup_restore.create_backup("d1")
        result = backup_restore.list_backups("d1")
        assert result[0].created_at >= result[1].created_at

    def test_list_backups_empty(self, backup_restore):
        assert backup_restore.list_backups("d1") == []

    def test_delete_backup_success(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        result = backup_restore.delete_backup(bak.id)
        assert result is True
        assert backup_restore.get_backup(bak.id) is None

    def test_delete_backup_nonexistent(self, backup_restore):
        assert backup_restore.delete_backup("bad") is False

    def test_delete_backup_increments_stats(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        backup_restore.delete_backup(bak.id)
        assert backup_restore.get_stats()["backups_deleted"] == 1

    def test_verify_backup_success(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        result = backup_restore.verify_backup(bak.id)
        assert result is True
        assert bak.verified is True

    def test_verify_backup_nonexistent(self, backup_restore):
        assert backup_restore.verify_backup("bad") is False

    def test_verify_backup_increments_stats(self, backup_restore):
        bak = backup_restore.create_backup("d1")
        backup_restore.verify_backup(bak.id)
        assert backup_restore.get_stats()["backups_verified"] == 1

    def test_set_retention(self, backup_restore):
        result = backup_restore.set_retention("d1", 60)
        assert result["deployment_id"] == "d1"
        assert result["retention_days"] == 60
        assert "set_at" in result

    def test_set_retention_affects_new_backups(self, backup_restore):
        backup_restore.set_retention("d1", 14)
        bak = backup_restore.create_backup("d1")
        diff = bak.expires_at - bak.created_at
        assert diff.days == 14

    def test_get_stats_total_size(self, backup_restore):
        backup_restore.create_backup("d1")
        backup_restore.create_backup("d1")
        stats = backup_restore.get_stats()
        assert stats["total_size_mb"] > 0
        assert stats["total_backups"] == 2

    def test_get_stats_verified_count(self, backup_restore):
        b1 = backup_restore.create_backup("d1")
        backup_restore.create_backup("d1")
        backup_restore.verify_backup(b1.id)
        stats = backup_restore.get_stats()
        assert stats["verified_backups"] == 1

    def test_get_stats_initial(self, backup_restore):
        stats = backup_restore.get_stats()
        assert stats["total_backups"] == 0
        assert stats["total_size_mb"] == 0.0
        assert stats["retention_policies"] == 0

    def test_get_stats_retention_policies_count(self, backup_restore):
        backup_restore.set_retention("d1", 30)
        backup_restore.set_retention("d2", 60)
        assert backup_restore.get_stats()["retention_policies"] == 2


# ------------------------------------------------------------------ #
#  HealthMonitoring Tests
# ------------------------------------------------------------------ #


class TestHealthMonitoring:
    """Saglik izleme testleri."""

    def test_check_health_returns_health_check(self, health):
        check = health.check_health("d1")
        assert isinstance(check, HealthCheck)
        assert check.deployment_id == "d1"
        assert check.cpu_pct > 0
        assert check.memory_pct > 0
        assert check.disk_pct > 0
        assert check.response_time_ms > 0

    def test_check_health_increments_stats(self, health):
        health.check_health("d1")
        health.check_health("d2")
        stats = health.get_stats()
        assert stats["checks_performed"] == 2

    def test_check_health_appends_to_history(self, health):
        health.check_health("d1")
        health.check_health("d1")
        history = health.get_history("d1")
        assert len(history) == 2

    def test_check_health_healthy_status(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [20.0, 30.0, 25.0, 100.0]
            check = health.check_health("d1")
            assert check.status == HealthStatus.HEALTHY

    def test_check_health_unhealthy_high_cpu(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [95.0, 30.0, 25.0, 100.0]
            check = health.check_health("d1")
            assert check.status == HealthStatus.UNHEALTHY

    def test_check_health_unhealthy_high_memory(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [30.0, 95.0, 25.0, 100.0]
            check = health.check_health("d1")
            assert check.status == HealthStatus.UNHEALTHY

    def test_check_health_unhealthy_high_response(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [30.0, 30.0, 25.0, 3000.0]
            check = health.check_health("d1")
            assert check.status == HealthStatus.UNHEALTHY

    def test_check_health_degraded_status(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            # CPU at 80% of 85 = 68, so 70 should trigger degraded
            mock_rand.side_effect = [70.0, 50.0, 30.0, 100.0]
            check = health.check_health("d1")
            assert check.status == HealthStatus.DEGRADED

    def test_check_health_generates_alert_for_unhealthy(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [95.0, 95.0, 50.0, 100.0]
            health.check_health("d1")
            alerts = health.get_alerts("d1")
            assert len(alerts) == 1
            assert alerts[0]["status"] == HealthStatus.UNHEALTHY

    def test_check_health_generates_alert_for_degraded(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [70.0, 50.0, 30.0, 100.0]
            health.check_health("d1")
            alerts = health.get_alerts("d1")
            assert len(alerts) == 1

    def test_check_health_no_alert_for_healthy(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [20.0, 20.0, 20.0, 50.0]
            health.check_health("d1")
            alerts = health.get_alerts("d1")
            assert len(alerts) == 0

    def test_get_latest_returns_last_check(self, health):
        health.check_health("d1")
        health.check_health("d1")
        latest = health.get_latest("d1")
        assert latest is not None
        history = health.get_history("d1")
        assert latest.id == history[-1].id

    def test_get_latest_no_history(self, health):
        assert health.get_latest("d1") is None

    def test_get_history_default_limit(self, health):
        for _ in range(5):
            health.check_health("d1")
        history = health.get_history("d1")
        assert len(history) == 5

    def test_get_history_with_limit(self, health):
        for _ in range(10):
            health.check_health("d1")
        history = health.get_history("d1", limit=3)
        assert len(history) == 3

    def test_get_history_empty(self, health):
        assert health.get_history("d1") == []

    def test_get_alerts_empty(self, health):
        assert health.get_alerts("d1") == []

    def test_configure_alerts(self, health):
        result = health.configure_alerts(
            "d1", cpu_threshold=50.0,
            memory_threshold=60.0,
            response_threshold=1000.0,
        )
        assert result["cpu_threshold"] == 50.0
        assert result["memory_threshold"] == 60.0
        assert result["response_threshold"] == 1000.0
        assert "configured_at" in result

    def test_configure_alerts_affects_health_check(self, health):
        health.configure_alerts(
            "d1", cpu_threshold=10.0,
            memory_threshold=10.0,
            response_threshold=10.0,
        )
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [20.0, 20.0, 20.0, 50.0]
            check = health.check_health("d1")
            assert check.status == HealthStatus.UNHEALTHY

    def test_get_overall_status_empty(self, health):
        status = health.get_overall_status()
        assert status["total_deployments_monitored"] == 0
        assert status["health_rate"] == 0.0

    def test_get_overall_status_with_deployments(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [20.0, 20.0, 20.0, 50.0]
            health.check_health("d1")
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [95.0, 95.0, 50.0, 100.0]
            health.check_health("d2")
        status = health.get_overall_status()
        assert status["total_deployments_monitored"] == 2

    def test_get_overall_status_health_rate(self, health):
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [20.0, 20.0, 20.0, 50.0]
            health.check_health("d1")
        with patch("app.core.atlascloud.health_monitoring.random.uniform") as mock_rand:
            mock_rand.side_effect = [20.0, 20.0, 20.0, 50.0]
            health.check_health("d2")
        status = health.get_overall_status()
        assert status["healthy"] == 2
        assert status["health_rate"] == 100.0

    def test_get_stats_initial(self, health):
        stats = health.get_stats()
        assert stats["deployments_monitored"] == 0
        assert stats["checks_performed"] == 0
        assert stats["alerts_triggered"] == 0
        assert stats["healthy_checks"] == 0
        assert stats["unhealthy_checks"] == 0
        assert stats["alert_configs"] == 0

    def test_get_stats_alert_configs_count(self, health):
        health.configure_alerts("d1")
        health.configure_alerts("d2")
        assert health.get_stats()["alert_configs"] == 2

    def test_history_limit_enforcement(self, health):
        for _ in range(120):
            health.check_health("d1")
        history = health._checks["d1"]
        assert len(history) <= 100

    def test_determine_status_directly(self, health):
        config = {
            "cpu_threshold": 85.0,
            "memory_threshold": 90.0,
            "response_threshold": 2000.0,
        }
        assert health._determine_status(10, 10, 100, config) == HealthStatus.HEALTHY
        assert health._determine_status(90, 10, 100, config) == HealthStatus.UNHEALTHY
        assert health._determine_status(70, 10, 100, config) == HealthStatus.DEGRADED


# ------------------------------------------------------------------ #
#  OnboardingWizard Tests
# ------------------------------------------------------------------ #


class TestOnboardingWizard:
    """Onboarding sihirbazi testleri."""

    def test_start_wizard_returns_info(self, wizard):
        result = wizard.start_wizard("t1")
        assert "wizard_id" in result
        assert result["tenant_id"] == "t1"
        assert result["total_steps"] == 6
        assert result["current_step"] == 1

    def test_start_wizard_creates_default_steps(self, wizard):
        result = wizard.start_wizard("t1")
        wiz = wizard._wizards[result["wizard_id"]]
        steps = wiz["steps"]
        assert len(steps) == 6
        assert steps[0].title == "Account Setup"
        assert steps[-1].title == "Verify"

    def test_start_wizard_increments_stats(self, wizard):
        wizard.start_wizard("t1")
        wizard.start_wizard("t2")
        assert wizard.get_stats()["wizards_started"] == 2

    def test_complete_step_marks_completed(self, wizard):
        result = wizard.start_wizard("t1")
        step = wizard.complete_step(result["wizard_id"], 1, {"name": "Test"})
        assert step is not None
        assert step.completed is True
        assert step.data == {"name": "Test"}

    def test_complete_step_advances_current_step(self, wizard):
        result = wizard.start_wizard("t1")
        wizard.complete_step(result["wizard_id"], 1)
        wiz = wizard._wizards[result["wizard_id"]]
        assert wiz["current_step"] == 2

    def test_complete_step_no_data(self, wizard):
        result = wizard.start_wizard("t1")
        step = wizard.complete_step(result["wizard_id"], 1)
        assert step.data == {}

    def test_complete_step_invalid_wizard(self, wizard):
        assert wizard.complete_step("bad", 1) is None

    def test_complete_step_invalid_step_number(self, wizard):
        result = wizard.start_wizard("t1")
        assert wizard.complete_step(result["wizard_id"], 99) is None

    def test_complete_all_steps_marks_wizard_completed(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        for i in range(1, 7):
            wizard.complete_step(wid, i)
        wiz = wizard._wizards[wid]
        assert wiz["completed"] is True
        assert wiz["completed_at"] is not None

    def test_complete_all_steps_increments_completed_stats(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        for i in range(1, 7):
            wizard.complete_step(wid, i)
        assert wizard.get_stats()["wizards_completed"] == 1

    def test_complete_step_increments_steps_completed(self, wizard):
        result = wizard.start_wizard("t1")
        wizard.complete_step(result["wizard_id"], 1)
        wizard.complete_step(result["wizard_id"], 2)
        assert wizard.get_stats()["steps_completed"] == 2

    def test_get_progress(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        wizard.complete_step(wid, 1)
        wizard.complete_step(wid, 2)
        progress = wizard.get_progress(wid)
        assert progress["total_steps"] == 6
        assert progress["completed_steps"] == 2
        assert progress["completion_pct"] == pytest.approx(33.3, abs=0.1)
        assert progress["current_step"] == 3
        assert progress["completed"] is False

    def test_get_progress_full_completion(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        for i in range(1, 7):
            wizard.complete_step(wid, i)
        progress = wizard.get_progress(wid)
        assert progress["completion_pct"] == 100.0
        assert progress["completed"] is True

    def test_get_progress_nonexistent_wizard(self, wizard):
        progress = wizard.get_progress("bad")
        assert "error" in progress

    def test_get_progress_includes_steps_detail(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        wizard.complete_step(wid, 1, {"key": "val"})
        progress = wizard.get_progress(wid)
        assert len(progress["steps"]) == 6
        assert progress["steps"][0]["completed"] is True
        assert progress["steps"][0]["data"] == {"key": "val"}

    def test_skip_step_success(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        skipped = wizard.skip_step(wid, 2)
        assert skipped is True
        wiz = wizard._wizards[wid]
        steps = wiz["steps"]
        assert steps[1].completed is True
        assert steps[1].data == {"skipped": True}

    def test_skip_step_increments_stats(self, wizard):
        result = wizard.start_wizard("t1")
        wizard.skip_step(result["wizard_id"], 1)
        assert wizard.get_stats()["steps_skipped"] == 1

    def test_skip_step_advances_current(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        wizard.skip_step(wid, 1)
        wiz = wizard._wizards[wid]
        assert wiz["current_step"] == 2

    def test_skip_step_nonexistent_wizard(self, wizard):
        assert wizard.skip_step("bad", 1) is False

    def test_skip_step_invalid_step_number(self, wizard):
        result = wizard.start_wizard("t1")
        assert wizard.skip_step(result["wizard_id"], 99) is False

    def test_reset_wizard(self, wizard):
        result = wizard.start_wizard("t1")
        wid = result["wizard_id"]
        wizard.complete_step(wid, 1)
        wizard.complete_step(wid, 2)
        reset_ok = wizard.reset_wizard(wid)
        assert reset_ok is True
        wiz = wizard._wizards[wid]
        assert wiz["current_step"] == 1
        assert wiz["completed"] is False
        assert wiz["completed_at"] is None
        assert all(not s.completed for s in wiz["steps"])

    def test_reset_wizard_nonexistent(self, wizard):
        assert wizard.reset_wizard("bad") is False

    def test_reset_wizard_increments_stats(self, wizard):
        result = wizard.start_wizard("t1")
        wizard.reset_wizard(result["wizard_id"])
        assert wizard.get_stats()["wizards_reset"] == 1

    def test_get_recommended_config_europe(self, wizard):
        cfg = wizard.get_recommended_config({"region": "europe"})
        assert cfg["region"] == Region.EU_CENTRAL

    def test_get_recommended_config_asia(self, wizard):
        cfg = wizard.get_recommended_config({"region": "asia"})
        assert cfg["region"] == Region.ASIA_PACIFIC

    def test_get_recommended_config_west(self, wizard):
        cfg = wizard.get_recommended_config({"region": "west"})
        assert cfg["region"] == Region.US_WEST

    def test_get_recommended_config_default_region(self, wizard):
        cfg = wizard.get_recommended_config({"region": "anywhere"})
        assert cfg["region"] == Region.EU_WEST

    def test_get_recommended_config_small_users(self, wizard):
        cfg = wizard.get_recommended_config({"expected_users": 50})
        assert cfg["instance_size"] == InstanceSize.SMALL

    def test_get_recommended_config_medium_users(self, wizard):
        cfg = wizard.get_recommended_config({"expected_users": 500})
        assert cfg["instance_size"] == InstanceSize.MEDIUM

    def test_get_recommended_config_large_users(self, wizard):
        cfg = wizard.get_recommended_config({"expected_users": 5000})
        assert cfg["instance_size"] == InstanceSize.LARGE

    def test_get_recommended_config_xlarge_users(self, wizard):
        cfg = wizard.get_recommended_config({"expected_users": 50000})
        assert cfg["instance_size"] == InstanceSize.XLARGE

    def test_get_recommended_config_auto_scale(self, wizard):
        cfg = wizard.get_recommended_config({"auto_scale": True})
        assert "auto_scaling" in cfg["features"]

    def test_get_recommended_config_ha(self, wizard):
        cfg = wizard.get_recommended_config({"ha": True})
        assert "high_availability" in cfg["features"]
        assert cfg["replicas"] == 3

    def test_get_recommended_config_no_ha_replicas(self, wizard):
        cfg = wizard.get_recommended_config({})
        assert cfg["replicas"] == 1

    def test_get_recommended_config_default_features(self, wizard):
        cfg = wizard.get_recommended_config({})
        assert "health_monitoring" in cfg["features"]
        assert "backups" in cfg["features"]
        assert cfg["backup_frequency"] == "daily"

    def test_get_stats_initial(self, wizard):
        stats = wizard.get_stats()
        assert stats["total_wizards"] == 0
        assert stats["active_wizards"] == 0
        assert stats["wizards_started"] == 0
        assert stats["wizards_completed"] == 0

    def test_get_stats_active_wizards(self, wizard):
        wizard.start_wizard("t1")
        r2 = wizard.start_wizard("t2")
        for i in range(1, 7):
            wizard.complete_step(r2["wizard_id"], i)
        stats = wizard.get_stats()
        assert stats["active_wizards"] == 1
        assert stats["total_wizards"] == 2


# ------------------------------------------------------------------ #
#  AtlasCloudFullOrchestrator Tests
# ------------------------------------------------------------------ #


class TestAtlasCloudFullOrchestrator:
    """Tam Atlas Cloud orkestratoru testleri."""

    def test_full_deploy_success(self, full_orchestrator):
        result = full_orchestrator.full_deploy("app1", "t1")
        assert result["success"] is True
        assert result["deployment"]["name"] == "app1"
        assert result["deployment"]["status"] == DeploymentStatus.RUNNING
        assert result["deployment"]["url"] == "https://app1.atlas-cloud.io"
        assert result["backup"]["type"] == BackupType.FULL
        assert result["scale_config"]["deployment_id"] is not None

    def test_full_deploy_custom_params(self, full_orchestrator):
        result = full_orchestrator.full_deploy(
            "app2", "t2",
            region=Region.US_EAST,
            size=InstanceSize.LARGE,
            version="2.0.0",
        )
        assert result["deployment"]["region"] == Region.US_EAST
        assert result["deployment"]["version"] == "2.0.0"

    def test_full_deploy_creates_scaler_config(self, full_orchestrator):
        result = full_orchestrator.full_deploy("app1", "t1")
        dep_id = result["deployment"]["id"]
        cfg = full_orchestrator.scaler.get_config(dep_id)
        assert cfg is not None
        assert cfg["min_replicas"] == 1
        assert cfg["max_replicas"] == 10

    def test_full_deploy_creates_backup(self, full_orchestrator):
        result = full_orchestrator.full_deploy("app1", "t1")
        dep_id = result["deployment"]["id"]
        backups = full_orchestrator.backups.list_backups(dep_id)
        assert len(backups) == 1

    def test_full_deploy_runs_health_check(self, full_orchestrator):
        result = full_orchestrator.full_deploy("app1", "t1")
        dep_id = result["deployment"]["id"]
        latest = full_orchestrator.health.get_latest(dep_id)
        assert latest is not None

    def test_full_deploy_configures_alerts(self, full_orchestrator):
        result = full_orchestrator.full_deploy("app1", "t1")
        dep_id = result["deployment"]["id"]
        assert dep_id in full_orchestrator.health._alert_configs

    def test_full_deploy_increments_stats(self, full_orchestrator):
        full_orchestrator.full_deploy("app1", "t1")
        assert full_orchestrator.get_stats()["full_deploys"] == 1

    def test_full_update_success(self, full_orchestrator):
        deploy = full_orchestrator.full_deploy("app1", "t1")
        dep_id = deploy["deployment"]["id"]
        result = full_orchestrator.full_update(dep_id, "2.0.0")
        assert result["success"] is True
        assert result["deployment_id"] == dep_id
        assert result["update"]["to_version"] == "2.0.0"
        assert result["pre_backup"]["type"] == BackupType.SNAPSHOT

    def test_full_update_nonexistent_deployment(self, full_orchestrator):
        result = full_orchestrator.full_update("bad", "2.0.0")
        assert result["success"] is False
        assert result["error"] == "deployment_not_found"

    def test_full_update_creates_pre_backup(self, full_orchestrator):
        deploy = full_orchestrator.full_deploy("app1", "t1")
        dep_id = deploy["deployment"]["id"]
        full_orchestrator.full_update(dep_id, "2.0.0")
        backups = full_orchestrator.backups.list_backups(dep_id)
        # 1 from full_deploy (FULL) + 1 from full_update (SNAPSHOT)
        assert len(backups) == 2
        types = {b.backup_type for b in backups}
        assert BackupType.SNAPSHOT in types

    def test_full_update_with_strategy(self, full_orchestrator):
        deploy = full_orchestrator.full_deploy("app1", "t1")
        dep_id = deploy["deployment"]["id"]
        result = full_orchestrator.full_update(
            dep_id, "2.0.0", strategy=UpdateStrategy.CANARY,
        )
        assert result["success"] is True

    def test_full_update_runs_health_check(self, full_orchestrator):
        deploy = full_orchestrator.full_deploy("app1", "t1")
        dep_id = deploy["deployment"]["id"]
        full_orchestrator.full_update(dep_id, "2.0.0")
        history = full_orchestrator.health.get_history(dep_id)
        # 1 from full_deploy + 1 from full_update
        assert len(history) >= 2

    def test_full_update_increments_stats(self, full_orchestrator):
        deploy = full_orchestrator.full_deploy("app1", "t1")
        dep_id = deploy["deployment"]["id"]
        full_orchestrator.full_update(dep_id, "2.0.0")
        assert full_orchestrator.get_stats()["full_updates"] == 1

    def test_get_cloud_overview_empty(self, full_orchestrator):
        overview = full_orchestrator.get_cloud_overview()
        assert overview["total_deployments"] == 0
        assert overview["deployments"] == []

    def test_get_cloud_overview_with_deployments(self, full_orchestrator):
        full_orchestrator.full_deploy("app1", "t1")
        full_orchestrator.full_deploy("app2", "t2")
        overview = full_orchestrator.get_cloud_overview()
        assert overview["total_deployments"] == 2
        assert len(overview["deployments"]) == 2

    def test_get_cloud_overview_includes_health(self, full_orchestrator):
        full_orchestrator.full_deploy("app1", "t1")
        overview = full_orchestrator.get_cloud_overview()
        dep_info = overview["deployments"][0]
        # Health check was run during full_deploy
        assert dep_info["health"] != "unknown"

    def test_get_cloud_overview_includes_overall_health(self, full_orchestrator):
        full_orchestrator.full_deploy("app1", "t1")
        overview = full_orchestrator.get_cloud_overview()
        assert "overall_health" in overview
        assert overview["overall_health"]["total_deployments_monitored"] == 1

    def test_get_cloud_overview_increments_stats(self, full_orchestrator):
        full_orchestrator.get_cloud_overview()
        full_orchestrator.get_cloud_overview()
        assert full_orchestrator.get_stats()["overviews_generated"] == 2

    def test_get_cloud_overview_includes_cloud_stats(self, full_orchestrator):
        full_orchestrator.full_deploy("app1", "t1")
        overview = full_orchestrator.get_cloud_overview()
        assert "cloud_stats" in overview
        assert overview["cloud_stats"]["deployments_created"] == 1

    def test_get_stats_includes_all_sub_stats(self, full_orchestrator):
        stats = full_orchestrator.get_stats()
        assert "cloud" in stats
        assert "scaler" in stats
        assert "updates" in stats
        assert "backups" in stats
        assert "health" in stats
        assert "wizard" in stats
        assert "full_deploys" in stats
        assert "full_updates" in stats
        assert "overviews_generated" in stats

    def test_get_stats_initial_values(self, full_orchestrator):
        stats = full_orchestrator.get_stats()
        assert stats["full_deploys"] == 0
        assert stats["full_updates"] == 0
        assert stats["overviews_generated"] == 0

    def test_sub_components_are_accessible(self, full_orchestrator):
        assert isinstance(full_orchestrator.cloud, AtlasCloudOrchestrator)
        assert isinstance(full_orchestrator.scaler, AutoScaler)
        assert isinstance(full_orchestrator.updates, ManagedUpdates)
        assert isinstance(full_orchestrator.backups, BackupRestore)
        assert isinstance(full_orchestrator.health, HealthMonitoring)
        assert isinstance(full_orchestrator.wizard, OnboardingWizard)

    def test_full_deploy_then_stop(self, full_orchestrator):
        deploy = full_orchestrator.full_deploy("app1", "t1")
        dep_id = deploy["deployment"]["id"]
        stopped = full_orchestrator.cloud.stop_deployment(dep_id)
        assert stopped is True
        dep = full_orchestrator.cloud.get_deployment(dep_id)
        assert dep.status == DeploymentStatus.STOPPED

    def test_full_deploy_then_destroy(self, full_orchestrator):
        deploy = full_orchestrator.full_deploy("app1", "t1")
        dep_id = deploy["deployment"]["id"]
        destroyed = full_orchestrator.cloud.destroy_deployment(dep_id)
        assert destroyed is True
        assert full_orchestrator.cloud.get_deployment(dep_id) is None

    def test_wizard_through_full_orchestrator(self, full_orchestrator):
        result = full_orchestrator.wizard.start_wizard("t1")
        assert result["total_steps"] == 6
        wid = result["wizard_id"]
        step = full_orchestrator.wizard.complete_step(wid, 1)
        assert step is not None
        assert step.completed is True
