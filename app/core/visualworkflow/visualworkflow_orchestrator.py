"""
Gorsel is akisi orkestrator modulu.

Tam pipeline: Design -> Configure -> Preview -> Deploy,
tum alt bilesenleri koordine eder.
"""

import logging
from typing import Any

from app.core.visualworkflow.action_library import (
    ActionLibrary,
)
from app.core.visualworkflow.conditional_branching import (
    ConditionalBranching,
)
from app.core.visualworkflow.drag_drop_workflow_ui import (
    DragDropWorkflowUI,
)
from app.core.visualworkflow.live_preview import (
    LivePreview,
)
from app.core.visualworkflow.one_click_deploy import (
    OneClickDeploy,
)
from app.core.visualworkflow.trigger_library import (
    TriggerLibrary,
)
from app.core.visualworkflow.workflow_template_store import (
    WorkflowTemplateStore,
)

logger = logging.getLogger(__name__)


class VisualWorkflowOrchestrator:
    """Gorsel is akisi orkestratoru.

    Design -> Configure -> Preview -> Deploy
    pipeline'ini koordine eder.

    Attributes:
        _ui: Surukle birak arayuzu.
        _triggers: Tetikleyici kutuphanesi.
        _actions: Aksiyon kutuphanesi.
        _branching: Kosullu dallanma.
        _templates: Sablon deposu.
        _preview: Canli onizleme.
        _deploy: Tek tikla dagitim.
    """

    def __init__(self) -> None:
        """Orkestratoru baslatir."""
        self._ui = DragDropWorkflowUI()
        self._triggers = TriggerLibrary()
        self._actions = ActionLibrary()
        self._branching = ConditionalBranching()
        self._templates = WorkflowTemplateStore()
        self._preview = LivePreview()
        self._deploy = OneClickDeploy()
        self._stats: dict[str, int] = {
            "workflows_designed": 0,
            "templates_used": 0,
            "previews_run": 0,
            "deployments_done": 0,
        }
        logger.info(
            "VisualWorkflowOrchestrator baslatildi"
        )

    def create_from_template(
        self,
        template_id: str,
        name: str = "",
        overrides: dict | None = None,
    ) -> dict[str, Any]:
        """Sablondan is akisi olusturur.

        Args:
            template_id: Sablon ID.
            name: Ozel is akisi adi.
            overrides: Ust yazim degerleri.

        Returns:
            Olusturma sonucu.
        """
        try:
            wf = self._templates.use_template(
                template_id
            )
            if not wf:
                return {
                    "success": False,
                    "error": "Sablon bulunamadi",
                }

            if name:
                wf.name = name

            # Ust yazim degerlerini uygula
            if overrides:
                if "description" in overrides:
                    wf.description = overrides[
                        "description"
                    ]
                if "tags" in overrides:
                    wf.tags = overrides["tags"]

            # UI'a kaydet
            self._ui._workflows[wf.id] = wf
            self._stats["templates_used"] += 1

            logger.info(
                f"Sablondan olusturuldu: {template_id} -> {wf.id}"
            )
            return {
                "success": True,
                "workflow_id": wf.id,
                "name": wf.name,
                "node_count": len(wf.nodes),
                "connection_count": len(wf.connections),
                "template_id": template_id,
            }
        except Exception as e:
            logger.error(
                f"Sablondan olusturma hatasi: {e}"
            )
            return {
                "success": False,
                "error": str(e),
            }

    def design_workflow(
        self,
        name: str = "",
        description: str = "",
        nodes_config: list[dict] | None = None,
        connections_config: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Is akisi tasarlar.

        Args:
            name: Is akisi adi.
            description: Aciklama.
            nodes_config: Dugum yapilandirmalari.
            connections_config: Baglanti yapilandirmalari.

        Returns:
            Tasarim sonucu.
        """
        try:
            wf = self._ui.create_workflow(
                name=name,
                description=description,
            )

            node_map: dict[str, str] = {}
            nodes_config = nodes_config or []
            connections_config = connections_config or []

            # Dugumleri ekle
            for nc in nodes_config:
                node_type = nc.get("node_type", "action")
                node_name = nc.get("name", "")
                config = nc.get("config", {})
                temp_id = nc.get("temp_id", "")

                # Dugum turune gore olustur
                if node_type == "trigger":
                    trigger_type = config.get(
                        "trigger_type", "manual"
                    )
                    node = self._triggers.create_trigger_node(
                        trigger_type=trigger_type,
                        config=config,
                    )
                elif node_type == "condition":
                    cond_cfg = config.get("condition", {})
                    from app.models.visualworkflow_models import (
                        ConditionConfig,
                    )
                    cond = ConditionConfig(**cond_cfg) if cond_cfg else None
                    node = self._branching.create_if_else_node(
                        condition=cond,
                        name=node_name or "If/Else",
                    )
                else:
                    action_type = config.get(
                        "action_type", "send_message"
                    )
                    node = self._actions.create_action_node(
                        action_type=action_type,
                        config=config,
                    )

                if node_name:
                    node.name = node_name
                node.position_x = nc.get(
                    "position_x", 0.0
                )
                node.position_y = nc.get(
                    "position_y", 0.0
                )

                wf.nodes.append(node)
                if temp_id:
                    node_map[temp_id] = node.id

            # Baglantilari ekle
            for cc in connections_config:
                source_temp = cc.get("source", "")
                target_temp = cc.get("target", "")
                source_id = node_map.get(
                    source_temp, source_temp
                )
                target_id = node_map.get(
                    target_temp, target_temp
                )
                conn_type = cc.get("type", "default")
                source_port = cc.get(
                    "source_port", "out"
                )
                target_port = cc.get(
                    "target_port", "in"
                )

                self._ui.connect_nodes(
                    workflow_id=wf.id,
                    source_id=source_id,
                    source_port=source_port,
                    target_id=target_id,
                    target_port=target_port,
                    connection_type=conn_type,
                )

            # Dogrula
            validation = self._ui.validate_workflow(
                wf.id
            )
            self._stats["workflows_designed"] += 1

            logger.info(
                f"Is akisi tasarlandi: {wf.id} "
                f"({len(wf.nodes)} dugum, {len(wf.connections)} baglanti)"
            )
            return {
                "success": True,
                "workflow_id": wf.id,
                "name": wf.name,
                "node_count": len(wf.nodes),
                "connection_count": len(wf.connections),
                "node_map": node_map,
                "validation": validation,
            }
        except Exception as e:
            logger.error(
                f"Is akisi tasarim hatasi: {e}"
            )
            return {
                "success": False,
                "error": str(e),
            }

    def preview_workflow(
        self,
        workflow_id: str,
        test_data: dict | None = None,
    ) -> dict[str, Any]:
        """Is akisini onizler.

        Args:
            workflow_id: Is akisi ID.
            test_data: Test verisi.

        Returns:
            Onizleme sonucu.
        """
        try:
            # Once dogrula
            validation = self._ui.validate_workflow(
                workflow_id
            )
            if not validation.get("is_valid"):
                return {
                    "success": False,
                    "error": "Is akisi gecersiz",
                    "validation_errors": validation.get(
                        "errors", []
                    ),
                }

            result = self._preview.run_full(
                workflow_id=workflow_id,
                test_data=test_data,
            )
            self._stats["previews_run"] += 1

            logger.info(
                f"Onizleme tamamlandi: {workflow_id} -> {result.status}"
            )
            return {
                "success": result.status == "completed",
                "preview_id": result.id,
                "status": result.status,
                "executed_nodes": result.executed_nodes,
                "duration_ms": result.duration_ms,
                "errors": result.errors,
            }
        except Exception as e:
            logger.error(
                f"Onizleme hatasi: {e}"
            )
            return {
                "success": False,
                "error": str(e),
            }

    def deploy_workflow(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Is akisini dagitir.

        Args:
            workflow_id: Is akisi ID.

        Returns:
            Dagitim sonucu.
        """
        try:
            # Dogrula
            validation = self._ui.validate_workflow(
                workflow_id
            )
            if not validation.get("is_valid"):
                return {
                    "success": False,
                    "error": "Is akisi gecersiz",
                    "validation_errors": validation.get(
                        "errors", []
                    ),
                }

            # Dagit
            result = self._deploy.deploy(
                workflow_id=workflow_id,
                auto_activate=True,
            )

            # Durumu guncelle
            self._ui.update_status(
                workflow_id, "active"
            )
            self._stats["deployments_done"] += 1

            logger.info(
                f"Is akisi dagitildi: {workflow_id} -> {result.id}"
            )
            return {
                "success": True,
                "deployment_id": result.id,
                "version": result.version,
                "active": result.active,
                "endpoint_url": result.endpoint_url,
            }
        except Exception as e:
            logger.error(
                f"Dagitim hatasi: {e}"
            )
            return {
                "success": False,
                "error": str(e),
            }

    def get_workflow_summary(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Is akisi ozetini getirir.

        Args:
            workflow_id: Is akisi ID.

        Returns:
            Ozet bilgisi.
        """
        try:
            wf = self._ui.get_workflow(workflow_id)
            if not wf:
                return {
                    "success": False,
                    "error": "Is akisi bulunamadi",
                }

            # Dugum turleri dagilimi
            type_counts: dict[str, int] = {}
            for node in wf.nodes:
                nt = node.node_type
                type_counts[nt] = (
                    type_counts.get(nt, 0) + 1
                )

            # Aktif dagitim bilgisi
            active_deps = [
                d
                for d in self._deploy.list_deployments(
                    active_only=True
                )
                if d.workflow_id == workflow_id
            ]

            return {
                "success": True,
                "workflow_id": wf.id,
                "name": wf.name,
                "description": wf.description,
                "status": wf.status,
                "version": wf.version,
                "node_count": len(wf.nodes),
                "connection_count": len(wf.connections),
                "node_types": type_counts,
                "tags": wf.tags,
                "active_deployment": (
                    active_deps[0].id if active_deps else None
                ),
                "created_at": wf.created_at.isoformat(),
                "updated_at": wf.updated_at.isoformat(),
            }
        except Exception as e:
            logger.error(
                f"Ozet getirme hatasi: {e}"
            )
            return {
                "success": False,
                "error": str(e),
            }

    def list_available_templates(
        self,
    ) -> list[dict[str, Any]]:
        """Kullanilabilir sablonlari listeler.

        Returns:
            Sablon bilgileri listesi.
        """
        templates = self._templates.list_templates()
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "industry": t.industry,
                "usage_count": t.usage_count,
                "rating": t.rating,
            }
            for t in templates
        ]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Birlesmis istatistik sozlugu.
        """
        return {
            "orchestrator": self._stats,
            "ui": self._ui.get_stats(),
            "triggers": self._triggers.get_stats(),
            "actions": self._actions.get_stats(),
            "branching": self._branching.get_stats(),
            "templates": self._templates.get_stats(),
            "preview": self._preview.get_stats(),
            "deploy": self._deploy.get_stats(),
        }
