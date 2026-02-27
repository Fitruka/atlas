"""
Surukle birak is akisi arayuzu modulu.

Gorsel is akisi tuval durumu yonetimi,
dugum ekleme/cikarma, baglanti, dogrulama.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.visualworkflow_models import (
    ConnectionType,
    NodeType,
    VisualWorkflow,
    WorkflowConnection,
    WorkflowNode,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

_MAX_NODES = 200
_MAX_CONNECTIONS = 500


class DragDropWorkflowUI:
    """Surukle birak is akisi arayuzu.

    Attributes:
        _workflows: Is akisi kayitlari.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Arayuzu baslatir."""
        self._workflows: dict[str, VisualWorkflow] = {}
        self._stats: dict[str, int] = {
            "workflows_created": 0,
            "nodes_added": 0,
            "connections_made": 0,
            "validations_run": 0,
        }
        logger.info("DragDropWorkflowUI baslatildi")

    @property
    def workflow_count(self) -> int:
        """Is akisi sayisi."""
        return len(self._workflows)

    def create_workflow(
        self,
        name: str = "",
        description: str = "",
        tags: list[str] | None = None,
    ) -> VisualWorkflow:
        """Yeni is akisi olusturur.

        Args:
            name: Is akisi adi.
            description: Aciklama.
            tags: Etiketler.

        Returns:
            Olusturulan is akisi.
        """
        try:
            wf = VisualWorkflow(
                name=name,
                description=description,
                status=WorkflowStatus.draft.value,
                tags=tags or [],
            )
            self._workflows[wf.id] = wf
            self._stats["workflows_created"] += 1
            logger.info(
                f"Is akisi olusturuldu: {wf.id}"
            )
            return wf
        except Exception as e:
            logger.error(
                f"Is akisi olusturma hatasi: {e}"
            )
            raise

    def add_node(
        self,
        workflow_id: str,
        node_type: str = "action",
        name: str = "",
        config: dict | None = None,
        position_x: float = 0.0,
        position_y: float = 0.0,
    ) -> WorkflowNode | None:
        """Is akisina dugum ekler.

        Args:
            workflow_id: Is akisi ID.
            node_type: Dugum turu.
            name: Dugum adi.
            config: Yapilandirma.
            position_x: X konumu.
            position_y: Y konumu.

        Returns:
            Eklenen dugum veya None.
        """
        try:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return None
            if len(wf.nodes) >= _MAX_NODES:
                logger.warning("Maksimum dugum siniri")
                return None

            node = WorkflowNode(
                node_type=node_type,
                name=name,
                config=config or {},
                position_x=position_x,
                position_y=position_y,
            )
            wf.nodes.append(node)
            wf.updated_at = datetime.now(timezone.utc)
            self._stats["nodes_added"] += 1
            logger.info(
                f"Dugum eklendi: {node.id} -> {workflow_id}"
            )
            return node
        except Exception as e:
            logger.error(f"Dugum ekleme hatasi: {e}")
            return None

    def remove_node(
        self,
        workflow_id: str,
        node_id: str,
    ) -> bool:
        """Is akisindan dugum kaldirir.

        Args:
            workflow_id: Is akisi ID.
            node_id: Dugum ID.

        Returns:
            Basarili ise True.
        """
        try:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return False

            original_len = len(wf.nodes)
            wf.nodes = [
                n for n in wf.nodes if n.id != node_id
            ]
            if len(wf.nodes) == original_len:
                return False

            # Bagli baglantilari da kaldir
            wf.connections = [
                c
                for c in wf.connections
                if c.source_node_id != node_id
                and c.target_node_id != node_id
            ]
            wf.updated_at = datetime.now(timezone.utc)
            logger.info(f"Dugum kaldirildi: {node_id}")
            return True
        except Exception as e:
            logger.error(
                f"Dugum kaldirma hatasi: {e}"
            )
            return False

    def connect_nodes(
        self,
        workflow_id: str,
        source_id: str,
        source_port: str = "out",
        target_id: str = "",
        target_port: str = "in",
        connection_type: str = "default",
    ) -> WorkflowConnection | None:
        """Iki dugumu baglar.

        Args:
            workflow_id: Is akisi ID.
            source_id: Kaynak dugum ID.
            source_port: Kaynak port.
            target_id: Hedef dugum ID.
            target_port: Hedef port.
            connection_type: Baglanti turu.

        Returns:
            Olusturulan baglanti veya None.
        """
        try:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return None
            if len(wf.connections) >= _MAX_CONNECTIONS:
                logger.warning("Maksimum baglanti siniri")
                return None

            # Dugumlerin varligini kontrol et
            node_ids = {n.id for n in wf.nodes}
            if (
                source_id not in node_ids
                or target_id not in node_ids
            ):
                return None

            conn = WorkflowConnection(
                source_node_id=source_id,
                source_port=source_port,
                target_node_id=target_id,
                target_port=target_port,
                connection_type=connection_type,
            )
            wf.connections.append(conn)
            wf.updated_at = datetime.now(timezone.utc)
            self._stats["connections_made"] += 1
            logger.info(
                f"Baglanti olusturuldu: {source_id} -> {target_id}"
            )
            return conn
        except Exception as e:
            logger.error(
                f"Baglanti olusturma hatasi: {e}"
            )
            return None

    def disconnect(
        self,
        workflow_id: str,
        connection_id: str,
    ) -> bool:
        """Baglantiyi koparir.

        Args:
            workflow_id: Is akisi ID.
            connection_id: Baglanti ID.

        Returns:
            Basarili ise True.
        """
        try:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return False

            original_len = len(wf.connections)
            wf.connections = [
                c
                for c in wf.connections
                if c.id != connection_id
            ]
            removed = len(wf.connections) < original_len
            if removed:
                wf.updated_at = datetime.now(timezone.utc)
            return removed
        except Exception as e:
            logger.error(
                f"Baglanti koparma hatasi: {e}"
            )
            return False

    def move_node(
        self,
        workflow_id: str,
        node_id: str,
        new_x: float = 0.0,
        new_y: float = 0.0,
    ) -> bool:
        """Dugum konumunu gunceller.

        Args:
            workflow_id: Is akisi ID.
            node_id: Dugum ID.
            new_x: Yeni X konumu.
            new_y: Yeni Y konumu.

        Returns:
            Basarili ise True.
        """
        try:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return False

            for node in wf.nodes:
                if node.id == node_id:
                    node.position_x = new_x
                    node.position_y = new_y
                    wf.updated_at = datetime.now(
                        timezone.utc
                    )
                    return True
            return False
        except Exception as e:
            logger.error(
                f"Dugum tasima hatasi: {e}"
            )
            return False

    def get_workflow(
        self,
        workflow_id: str,
    ) -> VisualWorkflow | None:
        """Is akisini getirir.

        Args:
            workflow_id: Is akisi ID.

        Returns:
            Is akisi veya None.
        """
        return self._workflows.get(workflow_id)

    def list_workflows(
        self,
        status: str | None = None,
    ) -> list[VisualWorkflow]:
        """Is akislarini listeler.

        Args:
            status: Durum filtresi.

        Returns:
            Is akisi listesi.
        """
        workflows = list(self._workflows.values())
        if status:
            workflows = [
                w for w in workflows if w.status == status
            ]
        return workflows

    def update_status(
        self,
        workflow_id: str,
        status: str = "active",
    ) -> bool:
        """Is akisi durumunu gunceller.

        Args:
            workflow_id: Is akisi ID.
            status: Yeni durum.

        Returns:
            Basarili ise True.
        """
        try:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return False
            wf.status = status
            wf.updated_at = datetime.now(timezone.utc)
            logger.info(
                f"Durum guncellendi: {workflow_id} -> {status}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Durum guncelleme hatasi: {e}"
            )
            return False

    def validate_workflow(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Is akisini dogrular.

        Args:
            workflow_id: Is akisi ID.

        Returns:
            Dogrulama sonucu (is_valid, errors).
        """
        try:
            self._stats["validations_run"] += 1
            wf = self._workflows.get(workflow_id)
            if not wf:
                return {
                    "is_valid": False,
                    "errors": ["Is akisi bulunamadi"],
                }

            errors: list[str] = []

            # En az bir tetikleyici dugum olmali
            triggers = [
                n
                for n in wf.nodes
                if n.node_type == NodeType.trigger.value
            ]
            if not triggers:
                errors.append(
                    "En az bir tetikleyici dugum gerekli"
                )

            # Bagsiz dugum kontrolu
            connected_ids: set[str] = set()
            for c in wf.connections:
                connected_ids.add(c.source_node_id)
                connected_ids.add(c.target_node_id)

            for node in wf.nodes:
                if (
                    node.id not in connected_ids
                    and len(wf.nodes) > 1
                ):
                    errors.append(
                        f"Bagsiz dugum: {node.name or node.id}"
                    )

            # Dongusel baglanti kontrolu
            adj: dict[str, list[str]] = {}
            for c in wf.connections:
                adj.setdefault(
                    c.source_node_id, []
                ).append(c.target_node_id)

            visited: set[str] = set()
            in_stack: set[str] = set()
            has_cycle = False

            def _dfs(nid: str) -> None:
                nonlocal has_cycle
                if has_cycle:
                    return
                visited.add(nid)
                in_stack.add(nid)
                for nb in adj.get(nid, []):
                    if nb in in_stack:
                        has_cycle = True
                        return
                    if nb not in visited:
                        _dfs(nb)
                in_stack.discard(nid)

            for n in wf.nodes:
                if n.id not in visited:
                    _dfs(n.id)
            if has_cycle:
                errors.append(
                    "Dongusel baglanti tespit edildi"
                )

            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
            }
        except Exception as e:
            logger.error(
                f"Dogrulama hatasi: {e}"
            )
            return {
                "is_valid": False,
                "errors": [str(e)],
            }

    def export_workflow(
        self,
        workflow_id: str,
    ) -> dict[str, Any]:
        """Is akisini JSON olarak disa aktarir.

        Args:
            workflow_id: Is akisi ID.

        Returns:
            JSON-uyumlu sozluk.
        """
        try:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return {"error": "Is akisi bulunamadi"}

            return wf.model_dump(mode="json")
        except Exception as e:
            logger.error(
                f"Disa aktarma hatasi: {e}"
            )
            return {"error": str(e)}

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            **self._stats,
            "total_workflows": len(self._workflows),
        }
