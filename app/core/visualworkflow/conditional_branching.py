"""
Kosullu dallanma modulu.

If/else/switch gorsel dallanma mantigi,
kosul olusturma, degerlendirme, dogrulama.
"""

import logging
import re
from typing import Any
from uuid import uuid4

from app.models.visualworkflow_models import (
    ConditionConfig,
    ConditionOperator,
    ConnectionType,
    NodeType,
    WorkflowConnection,
    WorkflowNode,
)

logger = logging.getLogger(__name__)

_MAX_BRANCHES = 50


class ConditionalBranching:
    """Kosullu dallanma yoneticisi.

    Attributes:
        _conditions: Kayitli kosullar.
        _branches: Dal baglantilari.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Dallanma yoneticisini baslatir."""
        self._conditions: dict[str, ConditionConfig] = {}
        self._branches: dict[str, list[dict]] = {}
        self._stats: dict[str, int] = {
            "conditions_created": 0,
            "evaluations": 0,
            "branches_added": 0,
        }
        logger.info(
            "ConditionalBranching baslatildi"
        )

    @property
    def condition_count(self) -> int:
        """Kosul sayisi."""
        return len(self._conditions)

    def create_condition(
        self,
        left_operand: str = "",
        operator: str = "equals",
        right_operand: str = "",
    ) -> ConditionConfig:
        """Yeni kosul olusturur.

        Args:
            left_operand: Sol operand (degisken adi).
            operator: Operator (equals, contains vb.).
            right_operand: Sag operand (deger).

        Returns:
            Olusturulan kosul yapilandirmasi.
        """
        try:
            condition = ConditionConfig(
                left_operand=left_operand,
                operator=operator,
                right_operand=right_operand,
            )
            cid = f"cnd_{uuid4()!s:.8}"
            self._conditions[cid] = condition
            self._stats["conditions_created"] += 1
            logger.info(f"Kosul olusturuldu: {cid}")
            return condition
        except Exception as e:
            logger.error(
                f"Kosul olusturma hatasi: {e}"
            )
            return ConditionConfig()

    def evaluate(
        self,
        condition: ConditionConfig,
        context: dict | None = None,
    ) -> bool:
        """Kosulu degerlendirir.

        Args:
            condition: Kosul yapilandirmasi.
            context: Degisken baglamı.

        Returns:
            Degerlendirme sonucu.
        """
        try:
            self._stats["evaluations"] += 1
            ctx = context or {}

            left = ctx.get(
                condition.left_operand,
                condition.left_operand,
            )
            right = ctx.get(
                condition.right_operand,
                condition.right_operand,
            )

            op = condition.operator
            if op == ConditionOperator.equals.value:
                return str(left) == str(right)
            elif op == ConditionOperator.not_equals.value:
                return str(left) != str(right)
            elif op == ConditionOperator.greater_than.value:
                return float(left) > float(right)
            elif op == ConditionOperator.less_than.value:
                return float(left) < float(right)
            elif op == ConditionOperator.contains.value:
                return str(right) in str(left)
            elif op == ConditionOperator.matches_regex.value:
                return bool(
                    re.search(str(right), str(left))
                )
            elif op == ConditionOperator.is_empty.value:
                return (
                    left is None
                    or str(left).strip() == ""
                )
            elif op == ConditionOperator.is_not_empty.value:
                return (
                    left is not None
                    and str(left).strip() != ""
                )

            logger.warning(
                f"Bilinmeyen operator: {op}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Kosul degerlendirme hatasi: {e}"
            )
            return False

    def create_if_else_node(
        self,
        condition: ConditionConfig | None = None,
        name: str = "If/Else",
    ) -> WorkflowNode:
        """If/Else dallanma dugumu olusturur.

        Args:
            condition: Kosul yapilandirmasi.
            name: Dugum adi.

        Returns:
            Olusturulan dugum.
        """
        try:
            config = {}
            if condition:
                config = {
                    "condition": condition.model_dump(),
                    "branch_type": "if_else",
                }

            node = WorkflowNode(
                node_type=NodeType.condition.value,
                name=name,
                config=config,
                outputs=["true", "false"],
            )
            logger.info(
                f"If/Else dugumu olusturuldu: {node.id}"
            )
            return node
        except Exception as e:
            logger.error(
                f"If/Else dugum olusturma hatasi: {e}"
            )
            return WorkflowNode(
                node_type=NodeType.condition.value,
                name="Hata",
            )

    def create_switch_node(
        self,
        variable: str = "",
        cases: dict | None = None,
    ) -> WorkflowNode:
        """Switch dallanma dugumu olusturur.

        Args:
            variable: Kontrol edilecek degisken.
            cases: Deger-etiket eslestirmesi.

        Returns:
            Olusturulan dugum.
        """
        try:
            cases = cases or {}
            outputs = list(cases.keys()) + ["default"]

            config = {
                "variable": variable,
                "cases": cases,
                "branch_type": "switch",
            }

            node = WorkflowNode(
                node_type=NodeType.condition.value,
                name=f"Switch: {variable}",
                config=config,
                outputs=outputs,
            )
            logger.info(
                f"Switch dugumu olusturuldu: {node.id}"
            )
            return node
        except Exception as e:
            logger.error(
                f"Switch dugum olusturma hatasi: {e}"
            )
            return WorkflowNode(
                node_type=NodeType.condition.value,
                name="Hata",
            )

    def add_branch(
        self,
        workflow_id: str,
        node_id: str,
        condition: ConditionConfig | None = None,
        target_node_id: str = "",
    ) -> WorkflowConnection:
        """Dugume dal ekler.

        Args:
            workflow_id: Is akisi ID.
            node_id: Kaynak kosul dugumu ID.
            condition: Dallanma kosulu.
            target_node_id: Hedef dugum ID.

        Returns:
            Olusturulan baglanti.
        """
        try:
            conn = WorkflowConnection(
                source_node_id=node_id,
                source_port="true",
                target_node_id=target_node_id,
                target_port="in",
                connection_type=ConnectionType.conditional.value,
                condition_expr=(
                    condition.model_dump_json()
                    if condition
                    else ""
                ),
            )

            # Dallari takip et
            self._branches.setdefault(
                node_id, []
            ).append(
                {
                    "connection_id": conn.id,
                    "target": target_node_id,
                    "workflow_id": workflow_id,
                }
            )
            self._stats["branches_added"] += 1
            logger.info(
                f"Dal eklendi: {node_id} -> {target_node_id}"
            )
            return conn
        except Exception as e:
            logger.error(
                f"Dal ekleme hatasi: {e}"
            )
            return WorkflowConnection()

    def validate_branches(
        self,
        workflow_id: str,
        node_id: str,
    ) -> dict[str, Any]:
        """Dallanma dogrulamasi yapar.

        Args:
            workflow_id: Is akisi ID.
            node_id: Dugum ID.

        Returns:
            Dogrulama sonucu (is_valid, errors).
        """
        errors: list[str] = []

        branches = self._branches.get(node_id, [])
        wf_branches = [
            b
            for b in branches
            if b.get("workflow_id") == workflow_id
        ]

        if not wf_branches:
            errors.append(
                f"Dugum {node_id} icin dal bulunamadi"
            )

        # Ayni hedefe birden fazla dal kontrolu
        targets = [
            b.get("target") for b in wf_branches
        ]
        duplicates = [
            t for t in targets if targets.count(t) > 1
        ]
        if duplicates:
            errors.append(
                f"Yinelenen hedef dugumler: {set(duplicates)}"
            )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "branch_count": len(wf_branches),
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            **self._stats,
            "total_conditions": len(self._conditions),
            "total_branch_nodes": len(self._branches),
        }
