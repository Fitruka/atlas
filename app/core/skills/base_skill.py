"""Temel beceri sinifi.

Tum becerilerin miras aldigi
ortak islevsellik.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.skills_models import (
    SkillDefinition,
    SkillExecution,
)

logger = logging.getLogger(__name__)

_MAX_RECORDS = 10000
_MAX_HISTORY = 10000


class BaseSkill:
    """Temel beceri sinifi.

    Tum becerilerin miras aldigi
    ortak islevsellik.

    Attributes:
        _records: Yurutme kayit deposu.
    """

    SKILL_ID: str = ""
    NAME: str = ""
    CATEGORY: str = ""
    RISK_LEVEL: str = "low"
    DESCRIPTION: str = ""
    PARAMETERS: dict[str, str] = {}
    REQUIRES_APPROVAL: list[str] = []
    VERSION: str = "1.0.0"

    def __init__(self) -> None:
        """BaseSkill baslatir."""
        self._records: dict[
            str, SkillExecution
        ] = {}
        self._record_order: list[str] = []
        self._total_ops: int = 0
        self._total_success: int = 0
        self._total_failed: int = 0
        self._total_time: float = 0.0
        self._history: list[
            dict[str, Any]
        ] = []

    @property
    def records(self) -> dict[str, Any]:
        """Dahili kayit deposuna erisim."""
        return self._records

    # ---- Yurutme ----

    def execute(
        self,
        **params: Any,
    ) -> SkillExecution:
        """Beceriyi yurutur.

        Args:
            **params: Beceri parametreleri.

        Returns:
            Yurutme sonucu.
        """
        if len(self._records) >= _MAX_RECORDS:
            self._rotate()

        exec_id = str(uuid4())[:8]
        now = time.time()
        self._total_ops += 1

        try:
            result = self._execute_impl(
                **params,
            )
            success = True
            error = ""
            self._total_success += 1
        except Exception as e:
            result = {}
            success = False
            error = str(e)
            self._total_failed += 1
            logger.warning(
                "Beceri hatasi %s: %s",
                self.NAME,
                error,
            )

        elapsed = time.time() - now
        self._total_time += elapsed

        execution = SkillExecution(
            execution_id=exec_id,
            skill_id=self.SKILL_ID,
            skill_name=self.NAME,
            parameters=params,
            result=result,
            success=success,
            error=error,
            execution_time=elapsed,
            timestamp=now,
        )

        self._records[exec_id] = execution
        self._record_order.append(exec_id)

        self._record_history(
            "execute",
            exec_id,
            f"success={success}",
        )

        return execution

    def _execute_impl(
        self,
        **params: Any,
    ) -> dict[str, Any]:
        """Alt sinif tarafindan uygulanir.

        Args:
            **params: Beceri parametreleri.

        Returns:
            Sonuc sozlugu.
        """
        raise NotImplementedError

    # ---- Tanim ----

    def get_definition(
        self,
    ) -> SkillDefinition:
        """Beceri tanimini dondurur.

        Returns:
            Beceri tanimi.
        """
        return SkillDefinition(
            skill_id=self.SKILL_ID,
            name=self.NAME,
            description=self.DESCRIPTION,
            category=self.CATEGORY,
            risk_level=self.RISK_LEVEL,
            parameters=self.PARAMETERS,
            requires_approval=(
                self.REQUIRES_APPROVAL
            ),
            version=self.VERSION,
        )

    # ---- Sorgulama ----

    def get_execution(
        self,
        execution_id: str,
    ) -> SkillExecution | None:
        """Yurutme kaydini dondurur.

        Args:
            execution_id: Yurutme ID.

        Returns:
            Kayit veya None.
        """
        return self._records.get(execution_id)

    def list_executions(
        self,
        limit: int = 50,
        success_only: bool = False,
    ) -> list[SkillExecution]:
        """Yurutme kayitlarini listeler.

        Args:
            limit: Maks sayi.
            success_only: Sadece basarili.

        Returns:
            Kayit listesi.
        """
        ids = list(
            reversed(self._record_order),
        )
        result: list[SkillExecution] = []

        for rid in ids:
            r = self._records.get(rid)
            if not r:
                continue
            if success_only and not r.success:
                continue
            result.append(r)
            if len(result) >= limit:
                break

        return result

    # ---- Temizlik ----

    def clear_records(self) -> int:
        """Kayitlari temizler.

        Returns:
            Silinen sayi.
        """
        count = len(self._records)
        self._records.clear()
        self._record_order.clear()
        return count

    # ---- Dahili ----

    def _rotate(self) -> int:
        """Eski kayitlari temizler."""
        keep = _MAX_RECORDS // 2
        if len(self._record_order) <= keep:
            return 0

        to_remove = self._record_order[:-keep]
        for rid in to_remove:
            self._records.pop(rid, None)

        self._record_order = (
            self._record_order[-keep:]
        )
        return len(to_remove)

    def _record_history(
        self,
        action: str,
        record_id: str,
        detail: str,
    ) -> None:
        """Aksiyonu kaydeder."""
        self._history.append({
            "action": action,
            "record_id": record_id,
            "detail": detail,
            "timestamp": time.time(),
        })
        if len(self._history) > _MAX_HISTORY:
            self._history = (
                self._history[-5000:]
            )

    def get_history(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Gecmisi dondurur."""
        return list(
            reversed(
                self._history[-limit:],
            ),
        )

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        avg_time = (
            self._total_time / self._total_ops
            if self._total_ops > 0
            else 0.0
        )
        success_rate = (
            self._total_success
            / self._total_ops
            if self._total_ops > 0
            else 1.0
        )
        return {
            "skill_id": self.SKILL_ID,
            "skill_name": self.NAME,
            "category": self.CATEGORY,
            "total_executions": (
                self._total_ops
            ),
            "total_success": (
                self._total_success
            ),
            "total_failed": (
                self._total_failed
            ),
            "success_rate": round(
                success_rate, 4,
            ),
            "avg_execution_time": round(
                avg_time, 6,
            ),
            "total_records": len(
                self._records,
            ),
        }
