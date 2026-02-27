"""
Aksiyon kutuphanesi modulu.

Kullanilabilir gorsel aksiyonlarin
katalogu, kayit, arama, dogrulama.
"""

import logging
from typing import Any
from uuid import uuid4

from app.models.visualworkflow_models import (
    ActionConfig,
    ActionType,
    NodeType,
    WorkflowNode,
)

logger = logging.getLogger(__name__)

_MAX_ACTIONS = 200


class ActionLibrary:
    """Aksiyon kutuphanesi.

    Attributes:
        _actions: Kayitli aksiyonlar.
        _stats: Istatistikler.
    """

    _BUILTIN_ACTIONS: dict[str, dict] = {
        "send_message": {
            "name": "Mesaj Gonder",
            "action_type": ActionType.send_message.value,
            "description": "Telegram, email veya SMS mesaji gonder",
            "config_schema": {
                "target": {"type": "string", "required": True},
                "message_template": {"type": "string", "required": True},
                "channel": {"type": "string", "default": "telegram"},
            },
        },
        "api_request": {
            "name": "API Istegi",
            "action_type": ActionType.api_request.value,
            "description": "Dis API cagrisi yap",
            "config_schema": {
                "target": {"type": "string", "required": True},
                "method": {"type": "string", "default": "POST"},
                "headers": {"type": "object", "default": {}},
                "payload_template": {"type": "object", "default": {}},
            },
        },
        "database_query": {
            "name": "Veritabani Sorgusu",
            "action_type": ActionType.database_query.value,
            "description": "Veritabani sorgusu calistir",
            "config_schema": {
                "query_template": {"type": "string", "required": True},
                "database": {"type": "string", "default": "default"},
                "timeout": {"type": "integer", "default": 30},
            },
        },
        "transform_data": {
            "name": "Veri Donusturme",
            "action_type": ActionType.transform_data.value,
            "description": "Veriyi donustur ve filtrele",
            "config_schema": {
                "transform_type": {"type": "string", "required": True},
                "mapping": {"type": "object", "default": {}},
                "filter_expr": {"type": "string", "required": False},
            },
        },
        "notify": {
            "name": "Bildirim Gonder",
            "action_type": ActionType.notify.value,
            "description": "Sistem bildirimi gonder",
            "config_schema": {
                "target": {"type": "string", "required": True},
                "priority": {"type": "string", "default": "normal"},
                "title": {"type": "string", "required": True},
            },
        },
        "assign_task": {
            "name": "Gorev Ata",
            "action_type": ActionType.assign_task.value,
            "description": "Bir agent veya kisiye gorev ata",
            "config_schema": {
                "assignee": {"type": "string", "required": True},
                "task_description": {"type": "string", "required": True},
                "deadline": {"type": "string", "required": False},
            },
        },
        "run_skill": {
            "name": "Beceri Calistir",
            "action_type": ActionType.run_skill.value,
            "description": "ATLAS becerisini calistir",
            "config_schema": {
                "skill_name": {"type": "string", "required": True},
                "parameters": {"type": "object", "default": {}},
                "timeout": {"type": "integer", "default": 60},
            },
        },
    }

    def __init__(self) -> None:
        """Kutupaneyi baslatir."""
        self._actions: dict[str, dict] = {}
        self._stats: dict[str, int] = {
            "actions_registered": 0,
            "nodes_created": 0,
            "searches": 0,
        }

        # Yerlesik aksiyonlari yukle
        for key, defn in self._BUILTIN_ACTIONS.items():
            aid = f"act_{key}"
            self._actions[aid] = {
                "action_id": aid,
                **defn,
                "builtin": True,
            }
            self._stats["actions_registered"] += 1

        logger.info("ActionLibrary baslatildi")

    @property
    def action_count(self) -> int:
        """Aksiyon sayisi."""
        return len(self._actions)

    def register_action(
        self,
        name: str = "",
        action_type: str = "send_message",
        description: str = "",
        config_schema: dict | None = None,
    ) -> str:
        """Yeni aksiyon kaydeder.

        Args:
            name: Aksiyon adi.
            action_type: Aksiyon turu.
            description: Aciklama.
            config_schema: Yapilandirma semasi.

        Returns:
            Aksiyon ID.
        """
        try:
            if len(self._actions) >= _MAX_ACTIONS:
                logger.warning("Maksimum aksiyon siniri")
                return ""

            aid = f"act_{uuid4()!s:.8}"
            self._actions[aid] = {
                "action_id": aid,
                "name": name,
                "action_type": action_type,
                "description": description,
                "config_schema": config_schema or {},
                "builtin": False,
            }
            self._stats["actions_registered"] += 1
            logger.info(f"Aksiyon kaydedildi: {aid}")
            return aid
        except Exception as e:
            logger.error(
                f"Aksiyon kayit hatasi: {e}"
            )
            return ""

    def get_action(
        self,
        action_id: str,
    ) -> dict | None:
        """Aksiyon bilgisini getirir.

        Args:
            action_id: Aksiyon ID.

        Returns:
            Aksiyon bilgisi veya None.
        """
        return self._actions.get(action_id)

    def list_actions(
        self,
        action_type: str | None = None,
    ) -> list[dict]:
        """Aksiyonlari listeler.

        Args:
            action_type: Tur filtresi.

        Returns:
            Aksiyon listesi.
        """
        result = list(self._actions.values())
        if action_type:
            result = [
                a
                for a in result
                if a.get("action_type") == action_type
            ]
        return result

    def create_action_node(
        self,
        action_type: str = "send_message",
        config: dict | None = None,
    ) -> WorkflowNode:
        """Aksiyon dugumu olusturur.

        Args:
            action_type: Aksiyon turu.
            config: Yapilandirma.

        Returns:
            Olusturulan dugum.
        """
        try:
            cfg = dict(config or {})
            cfg.pop("action_type", None)
            action_config = ActionConfig(
                action_type=action_type,
                **cfg,
            )
            node = WorkflowNode(
                node_type=NodeType.action.value,
                name=f"Aksiyon: {action_type}",
                config=action_config.model_dump(),
            )
            self._stats["nodes_created"] += 1
            logger.info(
                f"Aksiyon dugumu olusturuldu: {node.id}"
            )
            return node
        except Exception as e:
            logger.error(
                f"Aksiyon dugumu olusturma hatasi: {e}"
            )
            return WorkflowNode(
                node_type=NodeType.action.value,
                name="Hata",
            )

    def validate_action_config(
        self,
        action_type: str = "",
        config: dict | None = None,
    ) -> dict[str, Any]:
        """Aksiyon yapilandirmasini dogrular.

        Args:
            action_type: Aksiyon turu.
            config: Yapilandirma.

        Returns:
            Dogrulama sonucu (is_valid, errors).
        """
        errors: list[str] = []
        config = config or {}

        valid_types = [a.value for a in ActionType]
        if action_type not in valid_types:
            errors.append(
                f"Gecersiz aksiyon turu: {action_type}"
            )

        # Tur bazli zorunlu alan kontrolu
        if action_type == ActionType.api_request.value:
            if not config.get("target"):
                errors.append("target (URL) zorunludur")
        elif action_type == ActionType.send_message.value:
            if not config.get("target"):
                errors.append("target (alici) zorunludur")
        elif action_type == ActionType.run_skill.value:
            if not config.get("skill_name"):
                errors.append("skill_name zorunludur")
        elif action_type == ActionType.assign_task.value:
            if not config.get("assignee"):
                errors.append("assignee zorunludur")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

    def search(
        self,
        query: str = "",
    ) -> list[dict]:
        """Aksiyonlari arar.

        Args:
            query: Arama sorgusu.

        Returns:
            Eslesen aksiyonlar.
        """
        self._stats["searches"] += 1
        query_lower = query.lower()
        return [
            a
            for a in self._actions.values()
            if query_lower in a.get("name", "").lower()
            or query_lower
            in a.get("description", "").lower()
        ]

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            **self._stats,
            "total_actions": len(self._actions),
        }
