"""Sektörel iş akışı üretici.

Şablon iş akışı tanımlarından çalışır
iş akışları üretme, adım bağlama,
doğrulama.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.industrytemplate_models import (
    WorkflowDef,
    WorkflowStepDef,
    WorkflowStepType,
)

logger = logging.getLogger(__name__)

_MAX_WORKFLOWS = 50
_MAX_STEPS_PER_WORKFLOW = 30


class WorkflowGenerator:
    """Sektörel iş akışı üretici.

    Şablon tanımlarından iş akışı üretir,
    adımları bağlar, doğrular.

    Attributes:
        _workflows: Üretilen iş akışları.
    """

    def __init__(self) -> None:
        """WorkflowGenerator başlatır."""
        self._workflows: dict[str, WorkflowDef] = {}
        self._total_generated: int = 0

        logger.info("WorkflowGenerator baslatildi")

    def generate(
        self,
        template_id: str,
        workflow_defs: list[dict],
    ) -> list[WorkflowDef]:
        """İş akışları üret.

        Args:
            template_id: Şablon ID.
            workflow_defs: İş akışı tanımları.

        Returns:
            Üretilen iş akışları.
        """
        results: list[WorkflowDef] = []

        for wf_def in workflow_defs:
            if len(self._workflows) >= _MAX_WORKFLOWS:
                logger.warning("Max is akisi limiti")
                break

            workflow = self.create_flow(wf_def)
            if workflow:
                self._workflows[workflow.workflow_id] = workflow
                results.append(workflow)
                self._total_generated += 1

        logger.info(
            "Is akislari uretildi: %s (%d adet)",
            template_id,
            len(results),
        )
        return results

    def create_flow(self, flow_def: dict) -> WorkflowDef | None:
        """Tek iş akışı oluştur.

        Args:
            flow_def: İş akışı tanımı.

        Returns:
            İş akışı veya None.
        """
        name = flow_def.get("name", "")
        if not name:
            logger.warning("Is akisi adi bos")
            return None

        steps: list[WorkflowStepDef] = []
        for i, step_def in enumerate(flow_def.get("steps", [])):
            if len(steps) >= _MAX_STEPS_PER_WORKFLOW:
                break

            step = WorkflowStepDef(
                name=step_def.get("name", f"step_{i}"),
                step_type=step_def.get("step_type", "action"),
                skill_ref=step_def.get("skill_ref", ""),
                config=step_def.get("config", {}),
                next_steps=step_def.get("next_steps", []),
                timeout_seconds=step_def.get("timeout_seconds", 0),
                retry_count=step_def.get("retry_count", 0),
            )
            steps.append(step)

        steps = self._link_steps(steps)

        workflow = WorkflowDef(
            name=name,
            description=flow_def.get("description", ""),
            trigger=flow_def.get("trigger", ""),
            steps=steps,
            enabled=flow_def.get("enabled", True),
            tags=flow_def.get("tags", []),
        )

        return workflow

    def _link_steps(
        self,
        steps: list[WorkflowStepDef],
    ) -> list[WorkflowStepDef]:
        """Adımları sıralı bağla.

        Args:
            steps: Adım listesi.

        Returns:
            Bağlanmış adımlar.
        """
        for i, step in enumerate(steps):
            if not step.next_steps and i < len(steps) - 1:
                step.next_steps = [steps[i + 1].step_id]
        return steps

    def get_workflow(self, workflow_id: str) -> WorkflowDef | None:
        """İş akışı getir.

        Args:
            workflow_id: İş akışı ID.

        Returns:
            İş akışı veya None.
        """
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> list[WorkflowDef]:
        """Tüm iş akışlarını listele.

        Returns:
            İş akışı listesi.
        """
        return list(self._workflows.values())

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_workflows": len(self._workflows),
            "total_generated": self._total_generated,
        }
