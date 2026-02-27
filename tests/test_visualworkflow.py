"""Visual Workflow Builder (No-Code) testleri.

NodeType, TriggerType, ActionType, ConditionOperator,
WorkflowStatus, ConnectionType, PreviewStatus,
TriggerConfig, ActionConfig, ConditionConfig,
WorkflowNode, WorkflowConnection, VisualWorkflow,
WorkflowTemplate, PreviewResult, DeploymentResult,
DragDropWorkflowUI, TriggerLibrary, ActionLibrary,
ConditionalBranching, WorkflowTemplateStore,
LivePreview, OneClickDeploy,
VisualWorkflowOrchestrator testleri.
"""

import pytest

from app.models.visualworkflow_models import (
    ActionConfig,
    ActionType,
    ConditionConfig,
    ConditionOperator,
    ConnectionType,
    DeploymentResult,
    NodeType,
    PreviewResult,
    PreviewStatus,
    TriggerConfig,
    TriggerType,
    VisualWorkflow,
    WorkflowConnection,
    WorkflowNode,
    WorkflowStatus,
    WorkflowTemplate,
)
from app.core.visualworkflow.drag_drop_workflow_ui import (
    DragDropWorkflowUI,
)
from app.core.visualworkflow.trigger_library import (
    TriggerLibrary,
)
from app.core.visualworkflow.action_library import (
    ActionLibrary,
)
from app.core.visualworkflow.conditional_branching import (
    ConditionalBranching,
)
from app.core.visualworkflow.workflow_template_store import (
    WorkflowTemplateStore,
)
from app.core.visualworkflow.live_preview import (
    LivePreview,
)
from app.core.visualworkflow.one_click_deploy import (
    OneClickDeploy,
)
from app.core.visualworkflow.visualworkflow_orchestrator import (
    VisualWorkflowOrchestrator,
)


# ============================================================
# Enum Testleri
# ============================================================


class TestVisualWorkflowEnums:
    """Enum testleri."""

    def test_node_type_values(self):
        """Dugum turu degerleri."""
        assert NodeType.trigger == "trigger"
        assert NodeType.action == "action"
        assert NodeType.condition == "condition"
        assert NodeType.delay == "delay"
        assert NodeType.loop == "loop"
        assert NodeType.merge == "merge"
        assert NodeType.end == "end"

    def test_node_type_count(self):
        """Dugum turu sayisi."""
        assert len(NodeType) == 7

    def test_trigger_type_values(self):
        """Tetikleyici turu degerleri."""
        assert TriggerType.webhook == "webhook"
        assert TriggerType.schedule == "schedule"
        assert TriggerType.event == "event"
        assert TriggerType.manual == "manual"
        assert TriggerType.api_call == "api_call"
        assert TriggerType.message_received == "message_received"

    def test_trigger_type_count(self):
        """Tetikleyici turu sayisi."""
        assert len(TriggerType) == 6

    def test_action_type_values(self):
        """Aksiyon turu degerleri."""
        assert ActionType.send_message == "send_message"
        assert ActionType.api_request == "api_request"
        assert ActionType.database_query == "database_query"
        assert ActionType.transform_data == "transform_data"
        assert ActionType.notify == "notify"
        assert ActionType.assign_task == "assign_task"
        assert ActionType.run_skill == "run_skill"

    def test_action_type_count(self):
        """Aksiyon turu sayisi."""
        assert len(ActionType) == 7

    def test_condition_operator_values(self):
        """Kosul operatoru degerleri."""
        assert ConditionOperator.equals == "equals"
        assert ConditionOperator.not_equals == "not_equals"
        assert ConditionOperator.greater_than == "greater_than"
        assert ConditionOperator.less_than == "less_than"
        assert ConditionOperator.contains == "contains"
        assert ConditionOperator.matches_regex == "matches_regex"
        assert ConditionOperator.is_empty == "is_empty"
        assert ConditionOperator.is_not_empty == "is_not_empty"

    def test_condition_operator_count(self):
        """Kosul operatoru sayisi."""
        assert len(ConditionOperator) == 8

    def test_workflow_status_values(self):
        """Is akisi durumu degerleri."""
        assert WorkflowStatus.draft == "draft"
        assert WorkflowStatus.active == "active"
        assert WorkflowStatus.paused == "paused"
        assert WorkflowStatus.archived == "archived"
        assert WorkflowStatus.error == "error"

    def test_connection_type_values(self):
        """Baglanti turu degerleri."""
        assert ConnectionType.success == "success"
        assert ConnectionType.failure == "failure"
        assert ConnectionType.default == "default"
        assert ConnectionType.conditional == "conditional"

    def test_preview_status_values(self):
        """Onizleme durumu degerleri."""
        assert PreviewStatus.idle == "idle"
        assert PreviewStatus.running == "running"
        assert PreviewStatus.completed == "completed"
        assert PreviewStatus.error == "error"


# ============================================================
# Model Testleri
# ============================================================


class TestVisualWorkflowModels:
    """Model testleri."""

    def test_trigger_config_defaults(self):
        """TriggerConfig varsayilan degerler."""
        tc = TriggerConfig()
        assert tc.trigger_type == "manual"
        assert tc.schedule_cron == ""
        assert tc.webhook_path == ""
        assert tc.event_name == ""
        assert tc.filters == {}

    def test_trigger_config_custom(self):
        """TriggerConfig ozel degerler."""
        tc = TriggerConfig(
            trigger_type="webhook",
            webhook_path="/hook/test",
            filters={"key": "val"},
        )
        assert tc.trigger_type == "webhook"
        assert tc.webhook_path == "/hook/test"
        assert tc.filters == {"key": "val"}

    def test_action_config_defaults(self):
        """ActionConfig varsayilan degerler."""
        ac = ActionConfig()
        assert ac.action_type == "send_message"
        assert ac.target == ""
        assert ac.method == "POST"
        assert ac.payload_template == {}
        assert ac.timeout == 30
        assert ac.retry_count == 0

    def test_action_config_custom(self):
        """ActionConfig ozel degerler."""
        ac = ActionConfig(
            action_type="api_request",
            target="https://api.example.com",
            method="GET",
            timeout=60,
            retry_count=3,
        )
        assert ac.action_type == "api_request"
        assert ac.target == "https://api.example.com"
        assert ac.method == "GET"
        assert ac.timeout == 60
        assert ac.retry_count == 3

    def test_condition_config_defaults(self):
        """ConditionConfig varsayilan degerler."""
        cc = ConditionConfig()
        assert cc.left_operand == ""
        assert cc.operator == "equals"
        assert cc.right_operand == ""
        assert cc.combine_with == "and"

    def test_workflow_node_defaults(self):
        """WorkflowNode varsayilan degerler."""
        node = WorkflowNode()
        assert node.id
        assert node.node_type == "action"
        assert node.name == ""
        assert node.config == {}
        assert node.position_x == 0.0
        assert node.position_y == 0.0
        assert node.inputs == []
        assert node.outputs == []

    def test_workflow_node_custom(self):
        """WorkflowNode ozel degerler."""
        node = WorkflowNode(
            node_type="trigger",
            name="Test Trigger",
            config={"key": "val"},
            position_x=100.0,
            position_y=200.0,
        )
        assert node.node_type == "trigger"
        assert node.name == "Test Trigger"
        assert node.position_x == 100.0

    def test_workflow_connection_defaults(self):
        """WorkflowConnection varsayilan degerler."""
        conn = WorkflowConnection()
        assert conn.id
        assert conn.source_node_id == ""
        assert conn.source_port == "out"
        assert conn.target_node_id == ""
        assert conn.target_port == "in"
        assert conn.connection_type == "default"
        assert conn.condition_expr == ""

    def test_visual_workflow_defaults(self):
        """VisualWorkflow varsayilan degerler."""
        wf = VisualWorkflow()
        assert wf.id
        assert wf.name == ""
        assert wf.status == "draft"
        assert wf.nodes == []
        assert wf.connections == []
        assert wf.version == 1
        assert wf.tags == []
        assert wf.created_at is not None
        assert wf.updated_at is not None

    def test_workflow_template_defaults(self):
        """WorkflowTemplate varsayilan degerler."""
        tmpl = WorkflowTemplate()
        assert tmpl.id
        assert tmpl.name == ""
        assert tmpl.category == ""
        assert tmpl.industry == ""
        assert tmpl.workflow_def == {}
        assert tmpl.usage_count == 0
        assert tmpl.rating == 0.0

    def test_preview_result_defaults(self):
        """PreviewResult varsayilan degerler."""
        pr = PreviewResult()
        assert pr.id
        assert pr.workflow_id == ""
        assert pr.status == "idle"
        assert pr.executed_nodes == []
        assert pr.results == []
        assert pr.errors == []
        assert pr.duration_ms == 0.0

    def test_deployment_result_defaults(self):
        """DeploymentResult varsayilan degerler."""
        dr = DeploymentResult()
        assert dr.id
        assert dr.workflow_id == ""
        assert dr.version == 1
        assert dr.active is False
        assert dr.endpoint_url == ""
        assert dr.deployed_at is not None


# ============================================================
# DragDropWorkflowUI Testleri
# ============================================================


class TestDragDropWorkflowUI:
    """Surukle birak is akisi arayuzu testleri."""

    def setup_method(self):
        """Her test oncesi temiz UI olustur."""
        self.ui = DragDropWorkflowUI()

    def test_init(self):
        """Baslatma testi."""
        assert self.ui.workflow_count == 0

    def test_create_workflow(self):
        """Is akisi olusturma."""
        wf = self.ui.create_workflow(
            name="Test WF",
            description="Aciklama",
            tags=["test"],
        )
        assert wf.name == "Test WF"
        assert wf.description == "Aciklama"
        assert wf.status == "draft"
        assert "test" in wf.tags
        assert self.ui.workflow_count == 1

    def test_create_workflow_empty_name(self):
        """Bos isimle is akisi olusturma."""
        wf = self.ui.create_workflow()
        assert wf.name == ""
        assert wf.id
        assert self.ui.workflow_count == 1

    def test_add_node(self):
        """Dugum ekleme."""
        wf = self.ui.create_workflow(name="WF1")
        node = self.ui.add_node(
            workflow_id=wf.id,
            node_type="trigger",
            name="Tetikleyici",
            config={"trigger_type": "webhook"},
            position_x=50.0,
            position_y=100.0,
        )
        assert node is not None
        assert node.node_type == "trigger"
        assert node.name == "Tetikleyici"
        assert node.position_x == 50.0
        assert len(wf.nodes) == 1

    def test_add_node_invalid_workflow(self):
        """Gecersiz is akisina dugum ekleme."""
        result = self.ui.add_node(
            workflow_id="nonexistent",
            node_type="action",
        )
        assert result is None

    def test_remove_node(self):
        """Dugum kaldirma."""
        wf = self.ui.create_workflow(name="WF1")
        node = self.ui.add_node(wf.id, name="N1")
        assert len(wf.nodes) == 1
        removed = self.ui.remove_node(wf.id, node.id)
        assert removed is True
        assert len(wf.nodes) == 0

    def test_remove_node_invalid_id(self):
        """Gecersiz dugum kaldirma."""
        wf = self.ui.create_workflow(name="WF1")
        result = self.ui.remove_node(wf.id, "nonexistent")
        assert result is False

    def test_remove_node_clears_connections(self):
        """Dugum kaldirma baglantilari da temizler."""
        wf = self.ui.create_workflow(name="WF1")
        n1 = self.ui.add_node(wf.id, name="N1")
        n2 = self.ui.add_node(wf.id, name="N2")
        self.ui.connect_nodes(wf.id, n1.id, target_id=n2.id)
        assert len(wf.connections) == 1
        self.ui.remove_node(wf.id, n1.id)
        assert len(wf.connections) == 0

    def test_connect_nodes(self):
        """Dugum baglama."""
        wf = self.ui.create_workflow(name="WF1")
        n1 = self.ui.add_node(wf.id, name="N1")
        n2 = self.ui.add_node(wf.id, name="N2")
        conn = self.ui.connect_nodes(
            wf.id, n1.id, target_id=n2.id
        )
        assert conn is not None
        assert conn.source_node_id == n1.id
        assert conn.target_node_id == n2.id
        assert len(wf.connections) == 1

    def test_connect_nodes_invalid_source(self):
        """Gecersiz kaynak dugum baglama."""
        wf = self.ui.create_workflow(name="WF1")
        n1 = self.ui.add_node(wf.id, name="N1")
        result = self.ui.connect_nodes(
            wf.id, "nonexistent", target_id=n1.id
        )
        assert result is None

    def test_connect_nodes_invalid_target(self):
        """Gecersiz hedef dugum baglama."""
        wf = self.ui.create_workflow(name="WF1")
        n1 = self.ui.add_node(wf.id, name="N1")
        result = self.ui.connect_nodes(
            wf.id, n1.id, target_id="nonexistent"
        )
        assert result is None

    def test_connect_nodes_invalid_workflow(self):
        """Gecersiz is akisinda baglanti olusturma."""
        result = self.ui.connect_nodes(
            "nonexistent", "a", target_id="b"
        )
        assert result is None

    def test_disconnect(self):
        """Baglanti koparma."""
        wf = self.ui.create_workflow(name="WF1")
        n1 = self.ui.add_node(wf.id, name="N1")
        n2 = self.ui.add_node(wf.id, name="N2")
        conn = self.ui.connect_nodes(
            wf.id, n1.id, target_id=n2.id
        )
        assert len(wf.connections) == 1
        removed = self.ui.disconnect(wf.id, conn.id)
        assert removed is True
        assert len(wf.connections) == 0

    def test_disconnect_invalid_id(self):
        """Gecersiz baglanti koparma."""
        wf = self.ui.create_workflow(name="WF1")
        result = self.ui.disconnect(wf.id, "nonexistent")
        assert result is False

    def test_move_node(self):
        """Dugum tasima."""
        wf = self.ui.create_workflow(name="WF1")
        node = self.ui.add_node(wf.id, name="N1")
        moved = self.ui.move_node(
            wf.id, node.id, new_x=200.0, new_y=300.0
        )
        assert moved is True
        assert node.position_x == 200.0
        assert node.position_y == 300.0

    def test_move_node_invalid_workflow(self):
        """Gecersiz is akisinda dugum tasima."""
        result = self.ui.move_node(
            "nonexistent", "n1", new_x=100.0
        )
        assert result is False

    def test_move_node_invalid_node(self):
        """Gecersiz dugum tasima."""
        wf = self.ui.create_workflow(name="WF1")
        result = self.ui.move_node(
            wf.id, "nonexistent", new_x=100.0
        )
        assert result is False

    def test_get_workflow(self):
        """Is akisi getirme."""
        wf = self.ui.create_workflow(name="WF1")
        found = self.ui.get_workflow(wf.id)
        assert found is not None
        assert found.id == wf.id

    def test_get_workflow_not_found(self):
        """Bulunamayan is akisi."""
        assert self.ui.get_workflow("nonexistent") is None

    def test_list_workflows(self):
        """Is akisi listeleme."""
        self.ui.create_workflow(name="WF1")
        self.ui.create_workflow(name="WF2")
        result = self.ui.list_workflows()
        assert len(result) == 2

    def test_list_workflows_filter_status(self):
        """Durum filtresiyle is akisi listeleme."""
        wf1 = self.ui.create_workflow(name="WF1")
        wf2 = self.ui.create_workflow(name="WF2")
        self.ui.update_status(wf1.id, "active")
        drafts = self.ui.list_workflows(status="draft")
        assert len(drafts) == 1
        actives = self.ui.list_workflows(status="active")
        assert len(actives) == 1

    def test_update_status(self):
        """Durum guncelleme."""
        wf = self.ui.create_workflow(name="WF1")
        assert wf.status == "draft"
        updated = self.ui.update_status(wf.id, "active")
        assert updated is True
        assert wf.status == "active"

    def test_update_status_invalid_workflow(self):
        """Gecersiz is akisi durum guncelleme."""
        result = self.ui.update_status("nonexistent", "active")
        assert result is False

    def test_validate_workflow_no_trigger(self):
        """Tetikleyicisi olmayan is akisi dogrulama."""
        wf = self.ui.create_workflow(name="WF1")
        self.ui.add_node(wf.id, node_type="action", name="A1")
        result = self.ui.validate_workflow(wf.id)
        assert result["is_valid"] is False
        assert any("tetikleyici" in e for e in result["errors"])

    def test_validate_workflow_valid(self):
        """Gecerli is akisi dogrulama."""
        wf = self.ui.create_workflow(name="WF1")
        t1 = self.ui.add_node(
            wf.id, node_type="trigger", name="T1"
        )
        a1 = self.ui.add_node(
            wf.id, node_type="action", name="A1"
        )
        self.ui.connect_nodes(wf.id, t1.id, target_id=a1.id)
        result = self.ui.validate_workflow(wf.id)
        assert result["is_valid"] is True
        assert result["errors"] == []

    def test_validate_workflow_disconnected_node(self):
        """Bagsiz dugum dogrulama."""
        wf = self.ui.create_workflow(name="WF1")
        self.ui.add_node(
            wf.id, node_type="trigger", name="T1"
        )
        self.ui.add_node(
            wf.id, node_type="action", name="A1"
        )
        # Baglanti yok
        result = self.ui.validate_workflow(wf.id)
        assert result["is_valid"] is False
        assert any("Bagsiz" in e for e in result["errors"])

    def test_validate_workflow_not_found(self):
        """Bulunamayan is akisi dogrulama."""
        result = self.ui.validate_workflow("nonexistent")
        assert result["is_valid"] is False

    def test_validate_workflow_cycle_detection(self):
        """Dongusel baglanti tespiti."""
        wf = self.ui.create_workflow(name="Cycle")
        n1 = self.ui.add_node(
            wf.id, node_type="trigger", name="N1"
        )
        n2 = self.ui.add_node(
            wf.id, node_type="action", name="N2"
        )
        n3 = self.ui.add_node(
            wf.id, node_type="action", name="N3"
        )
        self.ui.connect_nodes(wf.id, n1.id, target_id=n2.id)
        self.ui.connect_nodes(wf.id, n2.id, target_id=n3.id)
        self.ui.connect_nodes(wf.id, n3.id, target_id=n2.id)
        result = self.ui.validate_workflow(wf.id)
        assert result["is_valid"] is False
        assert any("Dongusel" in e for e in result["errors"])

    def test_export_workflow(self):
        """Is akisini disa aktarma."""
        wf = self.ui.create_workflow(
            name="Export Test", description="Test"
        )
        exported = self.ui.export_workflow(wf.id)
        assert "error" not in exported
        assert exported["name"] == "Export Test"
        assert "nodes" in exported
        assert "connections" in exported

    def test_export_workflow_not_found(self):
        """Bulunamayan is akisini disa aktarma."""
        result = self.ui.export_workflow("nonexistent")
        assert "error" in result

    def test_get_stats(self):
        """Istatistik getirme."""
        wf = self.ui.create_workflow(name="WF1")
        self.ui.add_node(wf.id, name="N1")
        stats = self.ui.get_stats()
        assert stats["workflows_created"] == 1
        assert stats["nodes_added"] == 1
        assert stats["total_workflows"] == 1
        assert "connections_made" in stats
        assert "validations_run" in stats


# ============================================================
# TriggerLibrary Testleri
# ============================================================


class TestTriggerLibrary:
    """Tetikleyici kutuphanesi testleri."""

    def setup_method(self):
        """Her test oncesi temiz kutuphane olustur."""
        self.lib = TriggerLibrary()

    def test_init_has_builtins(self):
        """Baslatma yerlesik tetikleyiciler yukler."""
        assert self.lib.trigger_count == 6

    def test_register_trigger(self):
        """Tetikleyici kaydetme."""
        tid = self.lib.register_trigger(
            name="Custom Trigger",
            trigger_type="manual",
            description="Test tetikleyici",
        )
        assert tid
        assert tid.startswith("trg_")
        assert self.lib.trigger_count == 7

    def test_register_trigger_with_schema(self):
        """Sema ile tetikleyici kaydetme."""
        tid = self.lib.register_trigger(
            name="Schema Trigger",
            trigger_type="webhook",
            config_schema={"url": {"type": "string"}},
        )
        info = self.lib.get_trigger(tid)
        assert info is not None
        assert info["config_schema"]["url"]["type"] == "string"

    def test_get_trigger_builtin(self):
        """Yerlesik tetikleyici getirme."""
        trigger = self.lib.get_trigger("trg_webhook_incoming")
        assert trigger is not None
        assert trigger["name"] == "Gelen Webhook"
        assert trigger["builtin"] is True

    def test_get_trigger_not_found(self):
        """Bulunamayan tetikleyici."""
        assert self.lib.get_trigger("nonexistent") is None

    def test_list_triggers_all(self):
        """Tum tetikleyicileri listeleme."""
        result = self.lib.list_triggers()
        assert len(result) == 6

    def test_list_triggers_by_type(self):
        """Ture gore tetikleyici listeleme."""
        result = self.lib.list_triggers(trigger_type="webhook")
        assert len(result) == 1
        assert result[0]["trigger_type"] == "webhook"

    def test_list_triggers_by_type_no_match(self):
        """Eslesmeyen tur filtresi."""
        result = self.lib.list_triggers(trigger_type="nonexistent")
        assert len(result) == 0

    def test_create_trigger_node(self):
        """Tetikleyici dugumu olusturma."""
        node = self.lib.create_trigger_node(
            trigger_type="webhook",
            config={"webhook_path": "/test"},
        )
        assert node.node_type == "trigger"
        assert "webhook" in node.name.lower() or "Tetikleyici" in node.name
        assert node.config["trigger_type"] == "webhook"

    def test_create_trigger_node_default(self):
        """Varsayilan tetikleyici dugumu olusturma."""
        node = self.lib.create_trigger_node()
        assert node.node_type == "trigger"
        assert node.config["trigger_type"] == "manual"

    def test_validate_trigger_config_valid_webhook(self):
        """Gecerli webhook tetikleyici dogrulama."""
        result = self.lib.validate_trigger_config(
            trigger_type="webhook",
            config={"webhook_path": "/hook"},
        )
        assert result["is_valid"] is True

    def test_validate_trigger_config_missing_webhook_path(self):
        """Eksik webhook_path dogrulama."""
        result = self.lib.validate_trigger_config(
            trigger_type="webhook",
            config={},
        )
        assert result["is_valid"] is False
        assert any("webhook_path" in e for e in result["errors"])

    def test_validate_trigger_config_invalid_type(self):
        """Gecersiz tetikleyici turu dogrulama."""
        result = self.lib.validate_trigger_config(
            trigger_type="nonexistent",
            config={},
        )
        assert result["is_valid"] is False
        assert any("Gecersiz" in e for e in result["errors"])

    def test_validate_trigger_config_schedule_missing_cron(self):
        """Eksik schedule_cron dogrulama."""
        result = self.lib.validate_trigger_config(
            trigger_type="schedule",
            config={},
        )
        assert result["is_valid"] is False
        assert any("schedule_cron" in e for e in result["errors"])

    def test_validate_trigger_config_event_missing_name(self):
        """Eksik event_name dogrulama."""
        result = self.lib.validate_trigger_config(
            trigger_type="event",
            config={},
        )
        assert result["is_valid"] is False
        assert any("event_name" in e for e in result["errors"])

    def test_validate_trigger_config_manual_valid(self):
        """Gecerli manual tetikleyici dogrulama."""
        result = self.lib.validate_trigger_config(
            trigger_type="manual",
            config={},
        )
        assert result["is_valid"] is True

    def test_search(self):
        """Tetikleyici arama."""
        results = self.lib.search("webhook")
        assert len(results) >= 1

    def test_search_no_match(self):
        """Eslesmeyen arama."""
        results = self.lib.search("zzzznonexistentzzzz")
        assert len(results) == 0

    def test_search_empty_query(self):
        """Bos sorgu ile arama tum sonuclari dondurur."""
        results = self.lib.search("")
        assert len(results) == 6

    def test_get_stats(self):
        """Istatistik getirme."""
        self.lib.register_trigger(name="Custom")
        self.lib.search("test")
        stats = self.lib.get_stats()
        assert stats["triggers_registered"] >= 7
        assert stats["searches"] == 1
        assert stats["total_triggers"] >= 7


# ============================================================
# ActionLibrary Testleri
# ============================================================


class TestActionLibrary:
    """Aksiyon kutuphanesi testleri."""

    def setup_method(self):
        """Her test oncesi temiz kutuphane olustur."""
        self.lib = ActionLibrary()

    def test_init_has_builtins(self):
        """Baslatma yerlesik aksiyonlar yukler."""
        assert self.lib.action_count == 7

    def test_register_action(self):
        """Aksiyon kaydetme."""
        aid = self.lib.register_action(
            name="Custom Action",
            action_type="send_message",
            description="Test aksiyon",
        )
        assert aid
        assert aid.startswith("act_")
        assert self.lib.action_count == 8

    def test_get_action_builtin(self):
        """Yerlesik aksiyon getirme."""
        action = self.lib.get_action("act_send_message")
        assert action is not None
        assert action["name"] == "Mesaj Gonder"
        assert action["builtin"] is True

    def test_get_action_not_found(self):
        """Bulunamayan aksiyon."""
        assert self.lib.get_action("nonexistent") is None

    def test_list_actions_all(self):
        """Tum aksiyonlari listeleme."""
        result = self.lib.list_actions()
        assert len(result) == 7

    def test_list_actions_by_type(self):
        """Ture gore aksiyon listeleme."""
        result = self.lib.list_actions(action_type="notify")
        assert len(result) == 1
        assert result[0]["action_type"] == "notify"

    def test_list_actions_by_type_no_match(self):
        """Eslesmeyen tur filtresi."""
        result = self.lib.list_actions(action_type="nonexistent")
        assert len(result) == 0

    def test_create_action_node(self):
        """Aksiyon dugumu olusturma."""
        node = self.lib.create_action_node(
            action_type="api_request",
            config={"target": "https://api.example.com"},
        )
        assert node.node_type == "action"
        assert node.config["action_type"] == "api_request"

    def test_create_action_node_default(self):
        """Varsayilan aksiyon dugumu olusturma."""
        node = self.lib.create_action_node()
        assert node.node_type == "action"
        assert node.config["action_type"] == "send_message"

    def test_validate_action_config_valid(self):
        """Gecerli aksiyon yapilandirmasi dogrulama."""
        result = self.lib.validate_action_config(
            action_type="send_message",
            config={"target": "user@example.com"},
        )
        assert result["is_valid"] is True

    def test_validate_action_config_missing_target(self):
        """Eksik target dogrulama."""
        result = self.lib.validate_action_config(
            action_type="api_request",
            config={},
        )
        assert result["is_valid"] is False
        assert any("target" in e for e in result["errors"])

    def test_validate_action_config_invalid_type(self):
        """Gecersiz aksiyon turu dogrulama."""
        result = self.lib.validate_action_config(
            action_type="invalid_type",
            config={},
        )
        assert result["is_valid"] is False

    def test_validate_action_config_run_skill_missing(self):
        """Eksik skill_name dogrulama."""
        result = self.lib.validate_action_config(
            action_type="run_skill",
            config={},
        )
        assert result["is_valid"] is False
        assert any("skill_name" in e for e in result["errors"])

    def test_validate_action_config_assign_task_missing(self):
        """Eksik assignee dogrulama."""
        result = self.lib.validate_action_config(
            action_type="assign_task",
            config={},
        )
        assert result["is_valid"] is False
        assert any("assignee" in e for e in result["errors"])

    def test_search(self):
        """Aksiyon arama."""
        results = self.lib.search("mesaj")
        assert len(results) >= 1

    def test_search_empty_query(self):
        """Bos sorgu ile arama tum sonuclari dondurur."""
        results = self.lib.search("")
        assert len(results) == 7

    def test_get_stats(self):
        """Istatistik getirme."""
        self.lib.register_action(name="Custom")
        self.lib.create_action_node()
        stats = self.lib.get_stats()
        assert stats["actions_registered"] >= 8
        assert stats["nodes_created"] >= 1
        assert stats["total_actions"] >= 8


# ============================================================
# ConditionalBranching Testleri
# ============================================================


class TestConditionalBranching:
    """Kosullu dallanma testleri."""

    def setup_method(self):
        """Her test oncesi temiz dallanma yoneticisi olustur."""
        self.branch = ConditionalBranching()

    def test_init(self):
        """Baslatma testi."""
        assert self.branch.condition_count == 0

    def test_create_condition(self):
        """Kosul olusturma."""
        cond = self.branch.create_condition(
            left_operand="status",
            operator="equals",
            right_operand="active",
        )
        assert cond.left_operand == "status"
        assert cond.operator == "equals"
        assert cond.right_operand == "active"
        assert self.branch.condition_count == 1

    def test_evaluate_equals_true(self):
        """Equals kosul degerlendirme - dogru."""
        cond = ConditionConfig(
            left_operand="x",
            operator="equals",
            right_operand="hello",
        )
        result = self.branch.evaluate(
            cond, context={"x": "hello"}
        )
        assert result is True

    def test_evaluate_equals_false(self):
        """Equals kosul degerlendirme - yanlis."""
        cond = ConditionConfig(
            left_operand="x",
            operator="equals",
            right_operand="hello",
        )
        result = self.branch.evaluate(
            cond, context={"x": "world"}
        )
        assert result is False

    def test_evaluate_not_equals(self):
        """Not equals kosul degerlendirme."""
        cond = ConditionConfig(
            left_operand="x",
            operator="not_equals",
            right_operand="a",
        )
        assert self.branch.evaluate(cond, {"x": "b"}) is True
        assert self.branch.evaluate(cond, {"x": "a"}) is False

    def test_evaluate_greater_than(self):
        """Greater than kosul degerlendirme."""
        cond = ConditionConfig(
            left_operand="x",
            operator="greater_than",
            right_operand="5",
        )
        assert self.branch.evaluate(cond, {"x": "10"}) is True
        assert self.branch.evaluate(cond, {"x": "3"}) is False

    def test_evaluate_less_than(self):
        """Less than kosul degerlendirme."""
        cond = ConditionConfig(
            left_operand="x",
            operator="less_than",
            right_operand="10",
        )
        assert self.branch.evaluate(cond, {"x": "5"}) is True
        assert self.branch.evaluate(cond, {"x": "15"}) is False

    def test_evaluate_contains(self):
        """Contains kosul degerlendirme."""
        cond = ConditionConfig(
            left_operand="text",
            operator="contains",
            right_operand="hello",
        )
        assert self.branch.evaluate(
            cond, {"text": "say hello world"}
        ) is True
        assert self.branch.evaluate(
            cond, {"text": "goodbye"}
        ) is False

    def test_evaluate_matches_regex(self):
        """Regex kosul degerlendirme."""
        cond = ConditionConfig(
            left_operand="email",
            operator="matches_regex",
            right_operand=r"^\w+@\w+\.\w+$",
        )
        assert self.branch.evaluate(
            cond, {"email": "a@b.com"}
        ) is True
        assert self.branch.evaluate(
            cond, {"email": "invalid"}
        ) is False

    def test_evaluate_is_empty(self):
        """Is empty kosul degerlendirme."""
        cond = ConditionConfig(
            left_operand="val",
            operator="is_empty",
        )
        assert self.branch.evaluate(cond, {"val": ""}) is True
        assert self.branch.evaluate(cond, {"val": "x"}) is False

    def test_evaluate_is_not_empty(self):
        """Is not empty kosul degerlendirme."""
        cond = ConditionConfig(
            left_operand="val",
            operator="is_not_empty",
        )
        assert self.branch.evaluate(cond, {"val": "x"}) is True
        assert self.branch.evaluate(cond, {"val": ""}) is False

    def test_evaluate_unknown_operator(self):
        """Bilinmeyen operator degerlendirme."""
        cond = ConditionConfig(
            left_operand="x",
            operator="unknown_op",
            right_operand="y",
        )
        result = self.branch.evaluate(cond, {"x": "y"})
        assert result is False

    def test_evaluate_no_context(self):
        """Bos baglam ile degerlendirme."""
        cond = ConditionConfig(
            left_operand="val",
            operator="equals",
            right_operand="val",
        )
        # Baglam bos oldugunda left_operand kendisi kullanilir
        result = self.branch.evaluate(cond, context=None)
        assert result is True

    def test_create_if_else_node(self):
        """If/Else dugumu olusturma."""
        cond = ConditionConfig(
            left_operand="x",
            operator="equals",
            right_operand="y",
        )
        node = self.branch.create_if_else_node(
            condition=cond, name="Test If"
        )
        assert node.node_type == "condition"
        assert node.name == "Test If"
        assert "true" in node.outputs
        assert "false" in node.outputs

    def test_create_if_else_node_without_condition(self):
        """Kosulsuz If/Else dugumu olusturma."""
        node = self.branch.create_if_else_node()
        assert node.node_type == "condition"
        assert node.name == "If/Else"

    def test_create_switch_node(self):
        """Switch dugumu olusturma."""
        node = self.branch.create_switch_node(
            variable="status",
            cases={"active": "Aktif", "paused": "Durdurulmus"},
        )
        assert node.node_type == "condition"
        assert "Switch" in node.name
        assert "active" in node.outputs
        assert "paused" in node.outputs
        assert "default" in node.outputs

    def test_create_switch_node_empty_cases(self):
        """Bos case ile switch dugumu olusturma."""
        node = self.branch.create_switch_node(variable="x")
        assert "default" in node.outputs

    def test_add_branch(self):
        """Dal ekleme."""
        conn = self.branch.add_branch(
            workflow_id="wf1",
            node_id="cond1",
            target_node_id="action1",
        )
        assert conn.source_node_id == "cond1"
        assert conn.target_node_id == "action1"
        assert conn.connection_type == "conditional"

    def test_add_branch_with_condition(self):
        """Kosullu dal ekleme."""
        cond = ConditionConfig(
            left_operand="x",
            operator="equals",
            right_operand="y",
        )
        conn = self.branch.add_branch(
            workflow_id="wf1",
            node_id="cond1",
            condition=cond,
            target_node_id="action1",
        )
        assert conn.condition_expr != ""

    def test_validate_branches_no_branches(self):
        """Dallanma olmadan dogrulama."""
        result = self.branch.validate_branches("wf1", "node1")
        assert result["is_valid"] is False
        assert result["branch_count"] == 0

    def test_validate_branches_valid(self):
        """Gecerli dallanma dogrulama."""
        self.branch.add_branch("wf1", "cond1", target_node_id="a1")
        self.branch.add_branch("wf1", "cond1", target_node_id="a2")
        result = self.branch.validate_branches("wf1", "cond1")
        assert result["is_valid"] is True
        assert result["branch_count"] == 2

    def test_validate_branches_duplicate_targets(self):
        """Ayni hedefe birden fazla dal dogrulama."""
        self.branch.add_branch("wf1", "cond1", target_node_id="a1")
        self.branch.add_branch("wf1", "cond1", target_node_id="a1")
        result = self.branch.validate_branches("wf1", "cond1")
        assert result["is_valid"] is False
        assert any("Yinelenen" in e for e in result["errors"])

    def test_get_stats(self):
        """Istatistik getirme."""
        self.branch.create_condition("x", "equals", "y")
        self.branch.add_branch("wf1", "n1", target_node_id="n2")
        cond = ConditionConfig(left_operand="a", operator="equals", right_operand="b")
        self.branch.evaluate(cond, {"a": "b"})
        stats = self.branch.get_stats()
        assert stats["conditions_created"] == 1
        assert stats["branches_added"] == 1
        assert stats["evaluations"] == 1
        assert stats["total_conditions"] == 1
        assert stats["total_branch_nodes"] == 1


# ============================================================
# WorkflowTemplateStore Testleri
# ============================================================


class TestWorkflowTemplateStore:
    """Is akisi sablon deposu testleri."""

    def setup_method(self):
        """Her test oncesi temiz depo olustur."""
        self.store = WorkflowTemplateStore()

    def test_init_has_builtins(self):
        """Baslatma yerlesik sablonlari yukler."""
        assert self.store.template_count == 5

    def test_add_template(self):
        """Sablon ekleme."""
        tmpl = self.store.add_template(
            name="Test Template",
            description="Aciklama",
            category="test",
            industry="general",
            workflow_def={"nodes": [], "connections": []},
        )
        assert tmpl.name == "Test Template"
        assert tmpl.category == "test"
        assert self.store.template_count == 6

    def test_get_template_builtin(self):
        """Yerlesik sablon getirme."""
        tmpl = self.store.get_template(
            "tmpl_customer_support_flow"
        )
        assert tmpl is not None
        assert tmpl.name == "Musteri Destek Akisi"

    def test_get_template_not_found(self):
        """Bulunamayan sablon."""
        assert self.store.get_template("nonexistent") is None

    def test_list_templates_all(self):
        """Tum sablonlari listeleme."""
        result = self.store.list_templates()
        assert len(result) == 5

    def test_list_templates_by_category(self):
        """Kategoriye gore listeleme."""
        result = self.store.list_templates(category="support")
        assert len(result) == 1
        assert result[0].category == "support"

    def test_list_templates_by_industry(self):
        """Sektore gore listeleme."""
        result = self.store.list_templates(industry="healthcare")
        assert len(result) == 1

    def test_list_templates_combined_filter(self):
        """Birlesik filtre ile listeleme."""
        result = self.store.list_templates(
            category="ecommerce", industry="retail"
        )
        assert len(result) == 1

    def test_search(self):
        """Sablon arama."""
        results = self.store.search("siparis")
        assert len(results) >= 1

    def test_search_by_category(self):
        """Kategoriye gore arama."""
        results = self.store.search("support")
        assert len(results) >= 1

    def test_search_no_match(self):
        """Eslesmeyen arama."""
        results = self.store.search("zzzznonexistentzzzz")
        assert len(results) == 0

    def test_use_template(self):
        """Sablondan is akisi olusturma."""
        wf = self.store.use_template(
            "tmpl_customer_support_flow"
        )
        assert wf is not None
        assert "(Kopya)" in wf.name
        assert len(wf.nodes) > 0
        assert len(wf.connections) > 0

    def test_use_template_increments_usage(self):
        """Sablon kullanimi kullanim sayisini arttirir."""
        tmpl = self.store.get_template(
            "tmpl_customer_support_flow"
        )
        initial = tmpl.usage_count
        self.store.use_template("tmpl_customer_support_flow")
        assert tmpl.usage_count == initial + 1

    def test_use_template_not_found(self):
        """Bulunamayan sablondan is akisi olusturma."""
        result = self.store.use_template("nonexistent")
        assert result is None

    def test_rate_template(self):
        """Sablon puanlama."""
        result = self.store.rate_template(
            "tmpl_customer_support_flow", 4.5
        )
        assert result is True
        tmpl = self.store.get_template(
            "tmpl_customer_support_flow"
        )
        assert tmpl.rating > 0

    def test_rate_template_clamp(self):
        """Sablon puanlama sinir degerleri."""
        self.store.rate_template(
            "tmpl_customer_support_flow", 10.0
        )
        tmpl = self.store.get_template(
            "tmpl_customer_support_flow"
        )
        assert tmpl.rating <= 5.0

    def test_rate_template_not_found(self):
        """Bulunamayan sablon puanlama."""
        result = self.store.rate_template("nonexistent", 4.0)
        assert result is False

    def test_get_popular(self):
        """Populer sablonlari getirme."""
        self.store.use_template("tmpl_order_processing")
        self.store.use_template("tmpl_order_processing")
        popular = self.store.get_popular(limit=3)
        assert len(popular) <= 3
        assert popular[0].usage_count >= popular[-1].usage_count

    def test_get_popular_limit(self):
        """Populer sablonlari limit ile getirme."""
        popular = self.store.get_popular(limit=2)
        assert len(popular) <= 2

    def test_get_stats(self):
        """Istatistik getirme."""
        self.store.add_template(name="New")
        self.store.use_template("tmpl_customer_support_flow")
        self.store.search("test")
        stats = self.store.get_stats()
        assert stats["templates_added"] >= 6
        assert stats["templates_used"] >= 1
        assert stats["searches"] >= 1
        assert stats["total_templates"] >= 6


# ============================================================
# LivePreview Testleri
# ============================================================


class TestLivePreview:
    """Canli onizleme testleri."""

    def setup_method(self):
        """Her test oncesi temiz onizleme olustur."""
        self.preview = LivePreview()

    def test_init(self):
        """Baslatma testi."""
        assert self.preview.active_preview_count == 0

    def test_start_preview(self):
        """Onizleme baslatma."""
        pid = self.preview.start_preview(
            workflow_id="wf1",
            test_data={"key": "val"},
        )
        assert pid
        assert self.preview.active_preview_count == 1

    def test_start_preview_no_test_data(self):
        """Test verisi olmadan onizleme baslatma."""
        pid = self.preview.start_preview(workflow_id="wf1")
        assert pid
        status = self.preview.get_preview_status(pid)
        assert status is not None
        assert status.status == "running"

    def test_execute_step(self):
        """Adim calistirma."""
        pid = self.preview.start_preview("wf1")
        result = self.preview.execute_step(pid, "node1")
        assert result["success"] is True
        assert result["node_id"] == "node1"
        assert result["status"] == "completed"

    def test_execute_step_invalid_preview(self):
        """Gecersiz onizlemede adim calistirma."""
        result = self.preview.execute_step("nonexistent", "n1")
        assert result["success"] is False
        assert "bulunamadi" in result["error"]

    def test_execute_step_stopped_preview(self):
        """Durdurulmus onizlemede adim calistirma."""
        pid = self.preview.start_preview("wf1")
        self.preview.stop_preview(pid)
        result = self.preview.execute_step(pid, "node1")
        assert result["success"] is False
        assert "calismiyor" in result["error"]

    def test_run_full(self):
        """Tam calistirma."""
        result = self.preview.run_full(
            workflow_id="wf1",
            test_data={"key": "val"},
        )
        assert result.status == "completed"
        assert len(result.executed_nodes) == 3
        assert result.duration_ms >= 0

    def test_run_full_no_test_data(self):
        """Test verisi olmadan tam calistirma."""
        result = self.preview.run_full(workflow_id="wf1")
        assert result.status == "completed"

    def test_get_preview_status(self):
        """Onizleme durumu getirme."""
        pid = self.preview.start_preview("wf1")
        status = self.preview.get_preview_status(pid)
        assert status is not None
        assert status.status == "running"
        assert status.workflow_id == "wf1"

    def test_get_preview_status_not_found(self):
        """Bulunamayan onizleme durumu."""
        assert self.preview.get_preview_status("nonexistent") is None

    def test_stop_preview(self):
        """Onizleme durdurma."""
        pid = self.preview.start_preview("wf1")
        stopped = self.preview.stop_preview(pid)
        assert stopped is True
        status = self.preview.get_preview_status(pid)
        assert status.status == "completed"

    def test_stop_preview_not_found(self):
        """Bulunamayan onizleme durdurma."""
        result = self.preview.stop_preview("nonexistent")
        assert result is False

    def test_stop_preview_already_stopped(self):
        """Zaten durdurulmus onizleme durdurma."""
        pid = self.preview.start_preview("wf1")
        self.preview.stop_preview(pid)
        result = self.preview.stop_preview(pid)
        assert result is False

    def test_get_execution_trace(self):
        """Calistirma izi getirme."""
        pid = self.preview.start_preview("wf1")
        self.preview.execute_step(pid, "n1")
        self.preview.execute_step(pid, "n2")
        trace = self.preview.get_execution_trace(pid)
        assert len(trace) == 2
        assert trace[0]["node_id"] == "n1"
        assert trace[1]["node_id"] == "n2"

    def test_get_execution_trace_not_found(self):
        """Bulunamayan onizleme calistirma izi."""
        trace = self.preview.get_execution_trace("nonexistent")
        assert trace == []

    def test_get_stats(self):
        """Istatistik getirme."""
        pid = self.preview.start_preview("wf1")
        self.preview.execute_step(pid, "n1")
        self.preview.run_full("wf2")
        stats = self.preview.get_stats()
        assert stats["previews_started"] >= 2
        assert stats["steps_executed"] >= 1
        assert stats["full_runs"] >= 1
        assert stats["total_previews"] >= 2
        assert "active_previews" in stats


# ============================================================
# OneClickDeploy Testleri
# ============================================================


class TestOneClickDeploy:
    """Tek tikla dagitim testleri."""

    def setup_method(self):
        """Her test oncesi temiz dagitim yoneticisi olustur."""
        self.deployer = OneClickDeploy()

    def test_init(self):
        """Baslatma testi."""
        assert self.deployer.active_count == 0

    def test_deploy(self):
        """Dagitim."""
        result = self.deployer.deploy("wf1")
        assert result.workflow_id == "wf1"
        assert result.active is True
        assert result.version == 1
        assert "/api/workflows/wf1/v1" in result.endpoint_url
        assert self.deployer.active_count == 1

    def test_deploy_auto_activate_false(self):
        """Otomatik aktivasyon kapatma."""
        result = self.deployer.deploy("wf1", auto_activate=False)
        assert result.active is False
        assert self.deployer.active_count == 0

    def test_deploy_version_increment(self):
        """Dagitim surum artirma."""
        d1 = self.deployer.deploy("wf1")
        d2 = self.deployer.deploy("wf1")
        assert d1.version == 1
        assert d2.version == 2

    def test_deploy_deactivates_previous(self):
        """Yeni dagitim oncekini deaktif eder."""
        d1 = self.deployer.deploy("wf1")
        d2 = self.deployer.deploy("wf1")
        assert d1.active is False
        assert d2.active is True

    def test_undeploy(self):
        """Dagitim kaldirma."""
        dep = self.deployer.deploy("wf1")
        result = self.deployer.undeploy(dep.id)
        assert result is True
        assert dep.active is False

    def test_undeploy_not_found(self):
        """Bulunamayan dagitim kaldirma."""
        result = self.deployer.undeploy("nonexistent")
        assert result is False

    def test_activate(self):
        """Dagitim aktivasyon."""
        dep = self.deployer.deploy("wf1", auto_activate=False)
        assert dep.active is False
        result = self.deployer.activate(dep.id)
        assert result is True
        assert dep.active is True

    def test_activate_deactivates_others(self):
        """Aktivasyon diger ayn is akisi dagitimlarini deaktif eder."""
        d1 = self.deployer.deploy("wf1")
        d2 = self.deployer.deploy("wf1")
        self.deployer.activate(d1.id)
        assert d1.active is True
        assert d2.active is False

    def test_activate_not_found(self):
        """Bulunamayan dagitim aktivasyon."""
        result = self.deployer.activate("nonexistent")
        assert result is False

    def test_deactivate(self):
        """Dagitim deaktivasyon."""
        dep = self.deployer.deploy("wf1")
        result = self.deployer.deactivate(dep.id)
        assert result is True
        assert dep.active is False

    def test_deactivate_not_found(self):
        """Bulunamayan dagitim deaktivasyon."""
        result = self.deployer.deactivate("nonexistent")
        assert result is False

    def test_get_deployment(self):
        """Dagitim bilgisi getirme."""
        dep = self.deployer.deploy("wf1")
        found = self.deployer.get_deployment(dep.id)
        assert found is not None
        assert found.id == dep.id

    def test_get_deployment_not_found(self):
        """Bulunamayan dagitim bilgisi."""
        assert self.deployer.get_deployment("nonexistent") is None

    def test_list_deployments(self):
        """Dagitim listeleme."""
        self.deployer.deploy("wf1")
        self.deployer.deploy("wf2")
        result = self.deployer.list_deployments()
        assert len(result) == 2

    def test_list_deployments_active_only(self):
        """Yalnizca aktif dagitim listeleme."""
        self.deployer.deploy("wf1")
        self.deployer.deploy("wf2", auto_activate=False)
        result = self.deployer.list_deployments(active_only=True)
        assert len(result) == 1

    def test_rollback(self):
        """Geri alma."""
        d1 = self.deployer.deploy("wf1")
        d2 = self.deployer.deploy("wf1")
        assert d2.active is True
        assert d1.active is False
        result = self.deployer.rollback(d2.id)
        assert result is True
        assert d2.active is False
        assert d1.active is True

    def test_rollback_no_previous_version(self):
        """Onceki surum olmadan geri alma."""
        d1 = self.deployer.deploy("wf1")
        result = self.deployer.rollback(d1.id)
        assert result is False

    def test_rollback_not_found(self):
        """Bulunamayan dagitim geri alma."""
        result = self.deployer.rollback("nonexistent")
        assert result is False

    def test_get_stats(self):
        """Istatistik getirme."""
        d1 = self.deployer.deploy("wf1")
        d2 = self.deployer.deploy("wf1")
        self.deployer.undeploy(d2.id)
        self.deployer.activate(d1.id)
        self.deployer.deactivate(d1.id)
        stats = self.deployer.get_stats()
        assert stats["deployments"] == 2
        assert stats["undeployments"] == 1
        assert stats["activations"] >= 1
        assert stats["deactivations"] >= 1
        assert stats["total_deployments"] == 2
        assert "active_deployments" in stats
        assert "history_entries" in stats


# ============================================================
# VisualWorkflowOrchestrator Testleri
# ============================================================


class TestVisualWorkflowOrchestrator:
    """Gorsel is akisi orkestratoru testleri."""

    def setup_method(self):
        """Her test oncesi temiz orkestrator olustur."""
        self.orch = VisualWorkflowOrchestrator()

    def test_init(self):
        """Baslatma testi."""
        assert self.orch._ui is not None
        assert self.orch._triggers is not None
        assert self.orch._actions is not None
        assert self.orch._branching is not None
        assert self.orch._templates is not None
        assert self.orch._preview is not None
        assert self.orch._deploy is not None

    def test_create_from_template(self):
        """Sablondan is akisi olusturma."""
        result = self.orch.create_from_template(
            template_id="tmpl_customer_support_flow"
        )
        assert result["success"] is True
        assert result["workflow_id"]
        assert result["node_count"] > 0
        assert result["connection_count"] > 0

    def test_create_from_template_with_name(self):
        """Sablondan ozel isimle is akisi olusturma."""
        result = self.orch.create_from_template(
            template_id="tmpl_customer_support_flow",
            name="Benim Akisim",
        )
        assert result["success"] is True
        assert result["name"] == "Benim Akisim"

    def test_create_from_template_with_overrides(self):
        """Sablondan ust yazim ile is akisi olusturma."""
        result = self.orch.create_from_template(
            template_id="tmpl_order_processing",
            overrides={
                "description": "Ozel aciklama",
                "tags": ["custom"],
            },
        )
        assert result["success"] is True
        wf = self.orch._ui.get_workflow(result["workflow_id"])
        assert wf.description == "Ozel aciklama"
        assert "custom" in wf.tags

    def test_create_from_template_not_found(self):
        """Bulunamayan sablondan olusturma."""
        result = self.orch.create_from_template("nonexistent")
        assert result["success"] is False
        assert "error" in result

    def test_design_workflow(self):
        """Is akisi tasarlama."""
        result = self.orch.design_workflow(
            name="Test Design",
            description="Test aciklama",
            nodes_config=[
                {
                    "temp_id": "t1",
                    "node_type": "trigger",
                    "name": "Start",
                    "config": {"trigger_type": "manual"},
                    "position_x": 100,
                    "position_y": 200,
                },
                {
                    "temp_id": "a1",
                    "node_type": "action",
                    "name": "Send",
                    "config": {"action_type": "send_message"},
                    "position_x": 300,
                    "position_y": 200,
                },
            ],
            connections_config=[
                {
                    "source": "t1",
                    "target": "a1",
                    "type": "default",
                },
            ],
        )
        assert result["success"] is True
        assert result["node_count"] == 2
        assert result["connection_count"] == 1
        assert "node_map" in result
        assert "validation" in result

    def test_design_workflow_empty(self):
        """Bos is akisi tasarlama."""
        result = self.orch.design_workflow(name="Empty")
        assert result["success"] is True
        assert result["node_count"] == 0

    def test_design_workflow_with_condition(self):
        """Kosullu is akisi tasarlama."""
        result = self.orch.design_workflow(
            name="Conditional",
            nodes_config=[
                {
                    "temp_id": "t1",
                    "node_type": "trigger",
                    "name": "Start",
                    "config": {"trigger_type": "manual"},
                },
                {
                    "temp_id": "c1",
                    "node_type": "condition",
                    "name": "Check",
                    "config": {
                        "condition": {
                            "left_operand": "x",
                            "operator": "equals",
                            "right_operand": "y",
                        }
                    },
                },
            ],
            connections_config=[
                {"source": "t1", "target": "c1"},
            ],
        )
        assert result["success"] is True
        assert result["node_count"] == 2

    def test_preview_workflow(self):
        """Is akisi onizleme."""
        # Once gecerli bir is akisi olustur
        tmpl_result = self.orch.create_from_template(
            "tmpl_customer_support_flow"
        )
        wf_id = tmpl_result["workflow_id"]

        result = self.orch.preview_workflow(
            workflow_id=wf_id,
            test_data={"priority": "high"},
        )
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["duration_ms"] >= 0

    def test_preview_workflow_invalid(self):
        """Gecersiz is akisi onizleme."""
        # Bos is akisi tetikleyici yok
        wf = self.orch._ui.create_workflow(name="Invalid")
        result = self.orch.preview_workflow(wf.id)
        assert result["success"] is False

    def test_preview_workflow_not_found(self):
        """Bulunamayan is akisi onizleme."""
        result = self.orch.preview_workflow("nonexistent")
        assert result["success"] is False

    def test_deploy_workflow(self):
        """Is akisi dagitimi."""
        tmpl_result = self.orch.create_from_template(
            "tmpl_customer_support_flow"
        )
        wf_id = tmpl_result["workflow_id"]

        result = self.orch.deploy_workflow(wf_id)
        assert result["success"] is True
        assert result["deployment_id"]
        assert result["version"] == 1
        assert result["active"] is True
        assert result["endpoint_url"]

    def test_deploy_workflow_invalid(self):
        """Gecersiz is akisi dagitimi."""
        wf = self.orch._ui.create_workflow(name="Invalid")
        result = self.orch.deploy_workflow(wf.id)
        assert result["success"] is False

    def test_deploy_workflow_not_found(self):
        """Bulunamayan is akisi dagitimi."""
        result = self.orch.deploy_workflow("nonexistent")
        assert result["success"] is False

    def test_get_workflow_summary(self):
        """Is akisi ozeti getirme."""
        tmpl_result = self.orch.create_from_template(
            "tmpl_customer_support_flow"
        )
        wf_id = tmpl_result["workflow_id"]

        summary = self.orch.get_workflow_summary(wf_id)
        assert summary["success"] is True
        assert summary["workflow_id"] == wf_id
        assert "node_count" in summary
        assert "connection_count" in summary
        assert "node_types" in summary
        assert "created_at" in summary
        assert "updated_at" in summary

    def test_get_workflow_summary_with_deployment(self):
        """Dagitimli is akisi ozeti."""
        tmpl_result = self.orch.create_from_template(
            "tmpl_customer_support_flow"
        )
        wf_id = tmpl_result["workflow_id"]
        self.orch.deploy_workflow(wf_id)

        summary = self.orch.get_workflow_summary(wf_id)
        assert summary["success"] is True
        assert summary["active_deployment"] is not None

    def test_get_workflow_summary_not_found(self):
        """Bulunamayan is akisi ozeti."""
        result = self.orch.get_workflow_summary("nonexistent")
        assert result["success"] is False

    def test_list_available_templates(self):
        """Kullanilabilir sablonlari listeleme."""
        templates = self.orch.list_available_templates()
        assert len(templates) == 5
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "description" in t
            assert "category" in t
            assert "industry" in t
            assert "usage_count" in t
            assert "rating" in t

    def test_get_stats(self):
        """Istatistik getirme."""
        self.orch.create_from_template(
            "tmpl_customer_support_flow"
        )
        stats = self.orch.get_stats()
        assert "orchestrator" in stats
        assert "ui" in stats
        assert "triggers" in stats
        assert "actions" in stats
        assert "branching" in stats
        assert "templates" in stats
        assert "preview" in stats
        assert "deploy" in stats
        assert stats["orchestrator"]["templates_used"] >= 1

    def test_full_pipeline_design_preview_deploy(self):
        """Tam pipeline: tasarim -> onizleme -> dagitim."""
        # 1. Tasarla
        design = self.orch.design_workflow(
            name="Pipeline Test",
            nodes_config=[
                {
                    "temp_id": "t1",
                    "node_type": "trigger",
                    "name": "Trigger",
                    "config": {"trigger_type": "manual"},
                },
                {
                    "temp_id": "a1",
                    "node_type": "action",
                    "name": "Action",
                    "config": {"action_type": "send_message"},
                },
            ],
            connections_config=[
                {"source": "t1", "target": "a1"},
            ],
        )
        assert design["success"] is True
        wf_id = design["workflow_id"]

        # 2. Onizle
        preview = self.orch.preview_workflow(wf_id)
        assert preview["success"] is True

        # 3. Dagit
        deploy = self.orch.deploy_workflow(wf_id)
        assert deploy["success"] is True
        assert deploy["active"] is True
