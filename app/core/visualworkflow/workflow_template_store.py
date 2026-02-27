"""
Is akisi sablon deposu modulu.

Hazir is akisi sablonlari, kategori,
sektorel filtreleme, puanlama.
"""

import logging
from typing import Any
from uuid import uuid4

from app.models.visualworkflow_models import (
    VisualWorkflow,
    WorkflowTemplate,
)

logger = logging.getLogger(__name__)

_MAX_TEMPLATES = 500


class WorkflowTemplateStore:
    """Is akisi sablon deposu.

    Attributes:
        _templates: Kayitli sablonlar.
        _stats: Istatistikler.
    """

    _BUILTIN_TEMPLATES: dict[str, dict] = {
        "customer_support_flow": {
            "name": "Musteri Destek Akisi",
            "description": "Gelen musteri taleplerini otomatik siniflandir ve yonlendir",
            "category": "support",
            "industry": "general",
            "workflow_def": {
                "nodes": [
                    {
                        "id": "t1",
                        "node_type": "trigger",
                        "name": "Mesaj Alindi",
                        "config": {"trigger_type": "message_received"},
                        "position_x": 100,
                        "position_y": 200,
                    },
                    {
                        "id": "c1",
                        "node_type": "condition",
                        "name": "Aciliyet Kontrolu",
                        "config": {"condition": {"left_operand": "priority", "operator": "equals", "right_operand": "high"}},
                        "position_x": 300,
                        "position_y": 200,
                    },
                    {
                        "id": "a1",
                        "node_type": "action",
                        "name": "Acil Bildirim",
                        "config": {"action_type": "notify", "target": "support_team"},
                        "position_x": 500,
                        "position_y": 100,
                    },
                    {
                        "id": "a2",
                        "node_type": "action",
                        "name": "Kuyruga Ekle",
                        "config": {"action_type": "assign_task"},
                        "position_x": 500,
                        "position_y": 300,
                    },
                ],
                "connections": [
                    {"source_node_id": "t1", "target_node_id": "c1"},
                    {"source_node_id": "c1", "source_port": "true", "target_node_id": "a1"},
                    {"source_node_id": "c1", "source_port": "false", "target_node_id": "a2"},
                ],
            },
        },
        "order_processing": {
            "name": "Siparis Isleme",
            "description": "Yeni siparisleri otomatik isle ve takip et",
            "category": "ecommerce",
            "industry": "retail",
            "workflow_def": {
                "nodes": [
                    {"id": "t1", "node_type": "trigger", "name": "Yeni Siparis", "config": {"trigger_type": "webhook"}, "position_x": 100, "position_y": 200},
                    {"id": "a1", "node_type": "action", "name": "Stok Kontrol", "config": {"action_type": "database_query"}, "position_x": 300, "position_y": 200},
                    {"id": "c1", "node_type": "condition", "name": "Stok Var mi?", "config": {}, "position_x": 500, "position_y": 200},
                    {"id": "a2", "node_type": "action", "name": "Siparis Onayla", "config": {"action_type": "send_message"}, "position_x": 700, "position_y": 100},
                    {"id": "a3", "node_type": "action", "name": "Stok Uyarisi", "config": {"action_type": "notify"}, "position_x": 700, "position_y": 300},
                ],
                "connections": [
                    {"source_node_id": "t1", "target_node_id": "a1"},
                    {"source_node_id": "a1", "target_node_id": "c1"},
                    {"source_node_id": "c1", "source_port": "true", "target_node_id": "a2"},
                    {"source_node_id": "c1", "source_port": "false", "target_node_id": "a3"},
                ],
            },
        },
        "lead_qualification": {
            "name": "Lead Degerlendirme",
            "description": "Potansiyel musterileri otomatik puanla ve yonlendir",
            "category": "sales",
            "industry": "general",
            "workflow_def": {
                "nodes": [
                    {"id": "t1", "node_type": "trigger", "name": "Form Gonderimi", "config": {"trigger_type": "webhook"}, "position_x": 100, "position_y": 200},
                    {"id": "a1", "node_type": "action", "name": "Lead Puanla", "config": {"action_type": "transform_data"}, "position_x": 300, "position_y": 200},
                    {"id": "c1", "node_type": "condition", "name": "Puan >= 70?", "config": {}, "position_x": 500, "position_y": 200},
                    {"id": "a2", "node_type": "action", "name": "Satis Ekibine Ata", "config": {"action_type": "assign_task"}, "position_x": 700, "position_y": 100},
                    {"id": "a3", "node_type": "action", "name": "Nurture Kampanyasina Ekle", "config": {"action_type": "api_request"}, "position_x": 700, "position_y": 300},
                ],
                "connections": [
                    {"source_node_id": "t1", "target_node_id": "a1"},
                    {"source_node_id": "a1", "target_node_id": "c1"},
                    {"source_node_id": "c1", "source_port": "true", "target_node_id": "a2"},
                    {"source_node_id": "c1", "source_port": "false", "target_node_id": "a3"},
                ],
            },
        },
        "appointment_booking": {
            "name": "Randevu Planlama",
            "description": "Otomatik randevu alma ve onaylama akisi",
            "category": "scheduling",
            "industry": "healthcare",
            "workflow_def": {
                "nodes": [
                    {"id": "t1", "node_type": "trigger", "name": "Randevu Talebi", "config": {"trigger_type": "message_received"}, "position_x": 100, "position_y": 200},
                    {"id": "a1", "node_type": "action", "name": "Musaitlik Kontrol", "config": {"action_type": "database_query"}, "position_x": 300, "position_y": 200},
                    {"id": "c1", "node_type": "condition", "name": "Slot Var mi?", "config": {}, "position_x": 500, "position_y": 200},
                    {"id": "a2", "node_type": "action", "name": "Randevu Onayla", "config": {"action_type": "send_message"}, "position_x": 700, "position_y": 100},
                    {"id": "a3", "node_type": "action", "name": "Alternatif Oner", "config": {"action_type": "send_message"}, "position_x": 700, "position_y": 300},
                ],
                "connections": [
                    {"source_node_id": "t1", "target_node_id": "a1"},
                    {"source_node_id": "a1", "target_node_id": "c1"},
                    {"source_node_id": "c1", "source_port": "true", "target_node_id": "a2"},
                    {"source_node_id": "c1", "source_port": "false", "target_node_id": "a3"},
                ],
            },
        },
        "feedback_collection": {
            "name": "Geri Bildirim Toplama",
            "description": "Musteri geri bildirimlerini topla ve analiz et",
            "category": "feedback",
            "industry": "general",
            "workflow_def": {
                "nodes": [
                    {"id": "t1", "node_type": "trigger", "name": "Islem Tamamlandi", "config": {"trigger_type": "event"}, "position_x": 100, "position_y": 200},
                    {"id": "d1", "node_type": "delay", "name": "24 Saat Bekle", "config": {"delay_hours": 24}, "position_x": 300, "position_y": 200},
                    {"id": "a1", "node_type": "action", "name": "Anket Gonder", "config": {"action_type": "send_message"}, "position_x": 500, "position_y": 200},
                    {"id": "a2", "node_type": "action", "name": "Sonuclari Kaydet", "config": {"action_type": "database_query"}, "position_x": 700, "position_y": 200},
                ],
                "connections": [
                    {"source_node_id": "t1", "target_node_id": "d1"},
                    {"source_node_id": "d1", "target_node_id": "a1"},
                    {"source_node_id": "a1", "target_node_id": "a2"},
                ],
            },
        },
    }

    def __init__(self) -> None:
        """Sablon deposunu baslatir."""
        self._templates: dict[str, WorkflowTemplate] = {}
        self._stats: dict[str, int] = {
            "templates_added": 0,
            "templates_used": 0,
            "searches": 0,
        }

        # Yerlesik sablonlari yukle
        for key, defn in self._BUILTIN_TEMPLATES.items():
            tmpl = WorkflowTemplate(
                id=f"tmpl_{key}",
                name=defn["name"],
                description=defn["description"],
                category=defn["category"],
                industry=defn["industry"],
                workflow_def=defn["workflow_def"],
            )
            self._templates[tmpl.id] = tmpl
            self._stats["templates_added"] += 1

        logger.info("WorkflowTemplateStore baslatildi")

    @property
    def template_count(self) -> int:
        """Sablon sayisi."""
        return len(self._templates)

    def add_template(
        self,
        name: str = "",
        description: str = "",
        category: str = "",
        industry: str = "",
        workflow_def: dict | None = None,
    ) -> WorkflowTemplate:
        """Yeni sablon ekler.

        Args:
            name: Sablon adi.
            description: Aciklama.
            category: Kategori.
            industry: Sektor.
            workflow_def: Is akisi tanimi.

        Returns:
            Olusturulan sablon.
        """
        try:
            if len(self._templates) >= _MAX_TEMPLATES:
                logger.warning("Maksimum sablon siniri")
                return WorkflowTemplate()

            tmpl = WorkflowTemplate(
                name=name,
                description=description,
                category=category,
                industry=industry,
                workflow_def=workflow_def or {},
            )
            self._templates[tmpl.id] = tmpl
            self._stats["templates_added"] += 1
            logger.info(
                f"Sablon eklendi: {tmpl.id}"
            )
            return tmpl
        except Exception as e:
            logger.error(
                f"Sablon ekleme hatasi: {e}"
            )
            return WorkflowTemplate()

    def get_template(
        self,
        template_id: str,
    ) -> WorkflowTemplate | None:
        """Sablonu getirir.

        Args:
            template_id: Sablon ID.

        Returns:
            Sablon veya None.
        """
        return self._templates.get(template_id)

    def list_templates(
        self,
        category: str | None = None,
        industry: str | None = None,
    ) -> list[WorkflowTemplate]:
        """Sablonlari listeler.

        Args:
            category: Kategori filtresi.
            industry: Sektor filtresi.

        Returns:
            Sablon listesi.
        """
        result = list(self._templates.values())
        if category:
            result = [
                t for t in result if t.category == category
            ]
        if industry:
            result = [
                t for t in result if t.industry == industry
            ]
        return result

    def search(
        self,
        query: str = "",
    ) -> list[WorkflowTemplate]:
        """Sablonlari arar.

        Args:
            query: Arama sorgusu.

        Returns:
            Eslesen sablonlar.
        """
        self._stats["searches"] += 1
        query_lower = query.lower()
        return [
            t
            for t in self._templates.values()
            if query_lower in t.name.lower()
            or query_lower in t.description.lower()
            or query_lower in t.category.lower()
        ]

    def use_template(
        self,
        template_id: str,
    ) -> VisualWorkflow | None:
        """Sablondan yeni is akisi olusturur.

        Args:
            template_id: Sablon ID.

        Returns:
            Olusturulan is akisi veya None.
        """
        try:
            tmpl = self._templates.get(template_id)
            if not tmpl:
                return None

            wf = VisualWorkflow(
                name=f"{tmpl.name} (Kopya)",
                description=tmpl.description,
                tags=[tmpl.category, tmpl.industry],
            )

            # Sablon dugumleri ve baglantilari yukle
            wf_def = tmpl.workflow_def
            from app.models.visualworkflow_models import (
                WorkflowConnection,
                WorkflowNode,
            )

            for n_def in wf_def.get("nodes", []):
                node = WorkflowNode(**n_def)
                wf.nodes.append(node)

            for c_def in wf_def.get("connections", []):
                conn = WorkflowConnection(**c_def)
                wf.connections.append(conn)

            tmpl.usage_count += 1
            self._stats["templates_used"] += 1
            logger.info(
                f"Sablon kullanildi: {template_id} -> {wf.id}"
            )
            return wf
        except Exception as e:
            logger.error(
                f"Sablon kullanim hatasi: {e}"
            )
            return None

    def rate_template(
        self,
        template_id: str,
        rating: float = 5.0,
    ) -> bool:
        """Sablona puan verir.

        Args:
            template_id: Sablon ID.
            rating: Puan (0-5).

        Returns:
            Basarili ise True.
        """
        try:
            tmpl = self._templates.get(template_id)
            if not tmpl:
                return False

            rating = max(0.0, min(5.0, rating))
            # Kayan ortalama
            if tmpl.rating == 0.0:
                tmpl.rating = rating
            else:
                tmpl.rating = (
                    tmpl.rating * 0.7 + rating * 0.3
                )
            logger.info(
                f"Sablon puanlandi: {template_id} -> {tmpl.rating:.1f}"
            )
            return True
        except Exception as e:
            logger.error(
                f"Puanlama hatasi: {e}"
            )
            return False

    def get_popular(
        self,
        limit: int = 10,
    ) -> list[WorkflowTemplate]:
        """Populer sablonlari getirir.

        Args:
            limit: Maksimum sonuc sayisi.

        Returns:
            Populer sablonlar.
        """
        sorted_templates = sorted(
            self._templates.values(),
            key=lambda t: t.usage_count,
            reverse=True,
        )
        return sorted_templates[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            **self._stats,
            "total_templates": len(self._templates),
        }
