"""
Canli onizleme modulu.

Gercek zamanli is akisi onizleme ve
simülasyonu, adim adim calistirma.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.visualworkflow_models import (
    NodeType,
    PreviewResult,
    PreviewStatus,
)

logger = logging.getLogger(__name__)

_MAX_PREVIEWS = 100
_MAX_STEPS = 500


class LivePreview:
    """Canli onizleme yoneticisi.

    Attributes:
        _previews: Aktif onizlemeler.
        _workflows: Is akisi referanslari.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Onizleme yoneticisini baslatir."""
        self._previews: dict[str, PreviewResult] = {}
        self._workflows: dict[str, dict] = {}
        self._step_results: dict[str, list[dict]] = {}
        self._stats: dict[str, int] = {
            "previews_started": 0,
            "steps_executed": 0,
            "full_runs": 0,
        }
        logger.info("LivePreview baslatildi")

    @property
    def active_preview_count(self) -> int:
        """Aktif onizleme sayisi."""
        return sum(
            1
            for p in self._previews.values()
            if p.status == PreviewStatus.running.value
        )

    def start_preview(
        self,
        workflow_id: str,
        test_data: dict | None = None,
    ) -> str:
        """Onizleme baslatir.

        Args:
            workflow_id: Is akisi ID.
            test_data: Test verisi.

        Returns:
            Onizleme ID.
        """
        try:
            if len(self._previews) >= _MAX_PREVIEWS:
                # En eski tamamlananlari temizle
                completed = [
                    pid
                    for pid, p in self._previews.items()
                    if p.status
                    in (
                        PreviewStatus.completed.value,
                        PreviewStatus.error.value,
                    )
                ]
                for pid in completed[:10]:
                    del self._previews[pid]
                    self._step_results.pop(pid, None)

            preview = PreviewResult(
                workflow_id=workflow_id,
                status=PreviewStatus.running.value,
            )
            self._previews[preview.id] = preview
            self._workflows[preview.id] = {
                "workflow_id": workflow_id,
                "test_data": test_data or {},
                "context": dict(test_data or {}),
            }
            self._step_results[preview.id] = []
            self._stats["previews_started"] += 1

            logger.info(
                f"Onizleme baslatildi: {preview.id} -> {workflow_id}"
            )
            return preview.id
        except Exception as e:
            logger.error(
                f"Onizleme baslatma hatasi: {e}"
            )
            return ""

    def execute_step(
        self,
        preview_id: str,
        node_id: str,
    ) -> dict[str, Any]:
        """Tek bir adimi calistirir.

        Args:
            preview_id: Onizleme ID.
            node_id: Calistirilacak dugum ID.

        Returns:
            Adim sonucu.
        """
        try:
            preview = self._previews.get(preview_id)
            if not preview:
                return {
                    "success": False,
                    "error": "Onizleme bulunamadi",
                }

            if preview.status != PreviewStatus.running.value:
                return {
                    "success": False,
                    "error": "Onizleme calismiyor",
                }

            steps = self._step_results.get(
                preview_id, []
            )
            if len(steps) >= _MAX_STEPS:
                return {
                    "success": False,
                    "error": "Maksimum adim siniri",
                }

            start_time = time.time()

            # Simule edilmis adim calistirma
            step_result = {
                "node_id": node_id,
                "status": "completed",
                "output": {"simulated": True},
                "duration_ms": round(
                    (time.time() - start_time) * 1000, 2
                ),
            }

            preview.executed_nodes.append(node_id)
            preview.results.append(step_result)
            steps.append(step_result)
            self._stats["steps_executed"] += 1

            logger.info(
                f"Adim calistirildi: {node_id} @ {preview_id}"
            )
            return {
                "success": True,
                **step_result,
            }
        except Exception as e:
            logger.error(
                f"Adim calistirma hatasi: {e}"
            )
            return {
                "success": False,
                "error": str(e),
            }

    def run_full(
        self,
        workflow_id: str,
        test_data: dict | None = None,
    ) -> PreviewResult:
        """Tam is akisini calistirir.

        Args:
            workflow_id: Is akisi ID.
            test_data: Test verisi.

        Returns:
            Onizleme sonucu.
        """
        try:
            start_time = time.time()
            preview_id = self.start_preview(
                workflow_id, test_data
            )
            if not preview_id:
                return PreviewResult(
                    workflow_id=workflow_id,
                    status=PreviewStatus.error.value,
                    errors=["Onizleme baslatilamadi"],
                )

            preview = self._previews[preview_id]

            # Simule edilmis tam calistirma
            simulated_nodes = [
                "trigger_node",
                "process_node",
                "output_node",
            ]
            for node_id in simulated_nodes:
                step = self.execute_step(
                    preview_id, node_id
                )
                if not step.get("success"):
                    preview.status = (
                        PreviewStatus.error.value
                    )
                    preview.errors.append(
                        step.get("error", "Bilinmeyen hata")
                    )
                    return preview

            elapsed = (time.time() - start_time) * 1000
            preview.duration_ms = round(elapsed, 2)
            preview.status = (
                PreviewStatus.completed.value
            )
            self._stats["full_runs"] += 1

            logger.info(
                f"Tam calistirma tamamlandi: {preview_id} ({elapsed:.0f}ms)"
            )
            return preview
        except Exception as e:
            logger.error(
                f"Tam calistirma hatasi: {e}"
            )
            return PreviewResult(
                workflow_id=workflow_id,
                status=PreviewStatus.error.value,
                errors=[str(e)],
            )

    def get_preview_status(
        self,
        preview_id: str,
    ) -> PreviewResult | None:
        """Onizleme durumunu getirir.

        Args:
            preview_id: Onizleme ID.

        Returns:
            Onizleme sonucu veya None.
        """
        return self._previews.get(preview_id)

    def stop_preview(
        self,
        preview_id: str,
    ) -> bool:
        """Onizlemeyi durdurur.

        Args:
            preview_id: Onizleme ID.

        Returns:
            Basarili ise True.
        """
        try:
            preview = self._previews.get(preview_id)
            if not preview:
                return False

            if preview.status == PreviewStatus.running.value:
                preview.status = (
                    PreviewStatus.completed.value
                )
                logger.info(
                    f"Onizleme durduruldu: {preview_id}"
                )
                return True
            return False
        except Exception as e:
            logger.error(
                f"Onizleme durdurma hatasi: {e}"
            )
            return False

    def get_execution_trace(
        self,
        preview_id: str,
    ) -> list[dict]:
        """Calistirma izini getirir.

        Args:
            preview_id: Onizleme ID.

        Returns:
            Adim sonuclari listesi.
        """
        return list(
            self._step_results.get(preview_id, [])
        )

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            **self._stats,
            "total_previews": len(self._previews),
            "active_previews": self.active_preview_count,
        }
