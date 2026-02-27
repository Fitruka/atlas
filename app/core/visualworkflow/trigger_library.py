"""
Tetikleyici kutuphanesi modulu.

Kullanilabilir gorsel tetikleyicilerin
katalogu, kayit, arama, dogrulama.
"""

import logging
from typing import Any
from uuid import uuid4

from app.models.visualworkflow_models import (
    NodeType,
    TriggerConfig,
    TriggerType,
    WorkflowNode,
)

logger = logging.getLogger(__name__)

_MAX_TRIGGERS = 200


class TriggerLibrary:
    """Tetikleyici kutuphanesi.

    Attributes:
        _triggers: Kayitli tetikleyiciler.
        _stats: Istatistikler.
    """

    _BUILTIN_TRIGGERS: dict[str, dict] = {
        "webhook_incoming": {
            "name": "Gelen Webhook",
            "trigger_type": TriggerType.webhook.value,
            "description": "HTTP webhook ile tetikleme",
            "config_schema": {
                "webhook_path": {"type": "string", "required": True},
                "method": {"type": "string", "default": "POST"},
                "secret": {"type": "string", "required": False},
            },
        },
        "cron_schedule": {
            "name": "Zamanlanmis Calistirma",
            "trigger_type": TriggerType.schedule.value,
            "description": "Cron ifadesi ile periyodik tetikleme",
            "config_schema": {
                "schedule_cron": {"type": "string", "required": True},
                "timezone": {"type": "string", "default": "UTC"},
            },
        },
        "event_listener": {
            "name": "Olay Dinleyici",
            "trigger_type": TriggerType.event.value,
            "description": "Sistem olaylarina tepki verme",
            "config_schema": {
                "event_name": {"type": "string", "required": True},
                "filters": {"type": "object", "default": {}},
            },
        },
        "manual_trigger": {
            "name": "Manuel Tetikleme",
            "trigger_type": TriggerType.manual.value,
            "description": "Kullanici tarafindan elle tetikleme",
            "config_schema": {
                "confirm": {"type": "boolean", "default": False},
            },
        },
        "api_call_trigger": {
            "name": "API Cagri Tetikleyici",
            "trigger_type": TriggerType.api_call.value,
            "description": "Dis API cagrisi ile tetikleme",
            "config_schema": {
                "endpoint": {"type": "string", "required": True},
                "auth_type": {"type": "string", "default": "bearer"},
            },
        },
        "message_trigger": {
            "name": "Mesaj Alindi",
            "trigger_type": TriggerType.message_received.value,
            "description": "Yeni mesaj alindiginda tetikleme",
            "config_schema": {
                "channel": {"type": "string", "required": True},
                "keyword_filter": {"type": "string", "required": False},
            },
        },
    }

    def __init__(self) -> None:
        """Kutupaneyi baslatir."""
        self._triggers: dict[str, dict] = {}
        self._stats: dict[str, int] = {
            "triggers_registered": 0,
            "nodes_created": 0,
            "searches": 0,
        }

        # Yerlesik tetikleyicileri yukle
        for key, defn in self._BUILTIN_TRIGGERS.items():
            tid = f"trg_{key}"
            self._triggers[tid] = {
                "trigger_id": tid,
                **defn,
                "builtin": True,
            }
            self._stats["triggers_registered"] += 1

        logger.info("TriggerLibrary baslatildi")

    @property
    def trigger_count(self) -> int:
        """Tetikleyici sayisi."""
        return len(self._triggers)

    def register_trigger(
        self,
        name: str = "",
        trigger_type: str = "manual",
        description: str = "",
        config_schema: dict | None = None,
    ) -> str:
        """Yeni tetikleyici kaydeder.

        Args:
            name: Tetikleyici adi.
            trigger_type: Tetikleyici turu.
            description: Aciklama.
            config_schema: Yapilandirma semasi.

        Returns:
            Tetikleyici ID.
        """
        try:
            if len(self._triggers) >= _MAX_TRIGGERS:
                logger.warning("Maksimum tetikleyici siniri")
                return ""

            tid = f"trg_{uuid4()!s:.8}"
            self._triggers[tid] = {
                "trigger_id": tid,
                "name": name,
                "trigger_type": trigger_type,
                "description": description,
                "config_schema": config_schema or {},
                "builtin": False,
            }
            self._stats["triggers_registered"] += 1
            logger.info(f"Tetikleyici kaydedildi: {tid}")
            return tid
        except Exception as e:
            logger.error(
                f"Tetikleyici kayit hatasi: {e}"
            )
            return ""

    def get_trigger(
        self,
        trigger_id: str,
    ) -> dict | None:
        """Tetikleyici bilgisini getirir.

        Args:
            trigger_id: Tetikleyici ID.

        Returns:
            Tetikleyici bilgisi veya None.
        """
        return self._triggers.get(trigger_id)

    def list_triggers(
        self,
        trigger_type: str | None = None,
    ) -> list[dict]:
        """Tetikleyicileri listeler.

        Args:
            trigger_type: Tur filtresi.

        Returns:
            Tetikleyici listesi.
        """
        result = list(self._triggers.values())
        if trigger_type:
            result = [
                t
                for t in result
                if t.get("trigger_type") == trigger_type
            ]
        return result

    def create_trigger_node(
        self,
        trigger_type: str = "manual",
        config: dict | None = None,
    ) -> WorkflowNode:
        """Tetikleyici dugumu olusturur.

        Args:
            trigger_type: Tetikleyici turu.
            config: Yapilandirma.

        Returns:
            Olusturulan dugum.
        """
        try:
            cfg = dict(config or {})
            cfg.pop("trigger_type", None)
            trigger_config = TriggerConfig(
                trigger_type=trigger_type,
                **cfg,
            )
            node = WorkflowNode(
                node_type=NodeType.trigger.value,
                name=f"Tetikleyici: {trigger_type}",
                config=trigger_config.model_dump(),
            )
            self._stats["nodes_created"] += 1
            logger.info(
                f"Tetikleyici dugumu olusturuldu: {node.id}"
            )
            return node
        except Exception as e:
            logger.error(
                f"Tetikleyici dugumu olusturma hatasi: {e}"
            )
            return WorkflowNode(
                node_type=NodeType.trigger.value,
                name="Hata",
            )

    def validate_trigger_config(
        self,
        trigger_type: str = "",
        config: dict | None = None,
    ) -> dict[str, Any]:
        """Tetikleyici yapilandirmasini dogrular.

        Args:
            trigger_type: Tetikleyici turu.
            config: Yapilandirma.

        Returns:
            Dogrulama sonucu (is_valid, errors).
        """
        errors: list[str] = []
        config = config or {}

        valid_types = [t.value for t in TriggerType]
        if trigger_type not in valid_types:
            errors.append(
                f"Gecersiz tetikleyici turu: {trigger_type}"
            )

        # Tur bazli zorunlu alan kontrolu
        if trigger_type == TriggerType.webhook.value:
            if not config.get("webhook_path"):
                errors.append("webhook_path zorunludur")
        elif trigger_type == TriggerType.schedule.value:
            if not config.get("schedule_cron"):
                errors.append("schedule_cron zorunludur")
        elif trigger_type == TriggerType.event.value:
            if not config.get("event_name"):
                errors.append("event_name zorunludur")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

    def search(
        self,
        query: str = "",
    ) -> list[dict]:
        """Tetikleyicileri arar.

        Args:
            query: Arama sorgusu.

        Returns:
            Eslesen tetikleyiciler.
        """
        self._stats["searches"] += 1
        query_lower = query.lower()
        return [
            t
            for t in self._triggers.values()
            if query_lower in t.get("name", "").lower()
            or query_lower
            in t.get("description", "").lower()
        ]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            **self._stats,
            "total_triggers": len(self._triggers),
        }
