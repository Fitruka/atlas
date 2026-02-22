"""
Skills Orchestrator - Beceri sistemi orkestratoru.

Tum 250 beceriyi merkezi olarak yonetir, calistirir ve izler.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from app.core.skills.base_skill import BaseSkill
from app.core.skills.skill_registry import SkillRegistry
from app.core.skills import register_all_skills

logger = logging.getLogger(__name__)


class SkillsOrchestrator:
    """
    Beceri sistemi ana orkestratoru.

    Sorumluluklar:
    - 250 becerinin kaydi ve yaşam dongusu
    - Beceri calistirma (ID, isim, veya dogal dil ile)
    - Kategori ve arama islemleri
    - Calistirma gecmisi ve istatistikler
    - Toplu islemler ve raporlama
    """

    def __init__(self) -> None:
        """Orkestratoru baslatir."""
        self.registry = SkillRegistry()
        self._initialized = False
        self._execution_log: list[dict[str, Any]] = []
        self._max_log = 10000
        self.created_at = datetime.now()

    async def initialize(self) -> dict[str, Any]:
        """Tum becerileri yukle ve kaydet."""
        if self._initialized:
            return {"status": "already_initialized", "skill_count": self.registry.count()}

        self.registry = register_all_skills(self.registry)
        self._initialized = True

        count = self.registry.count()
        logger.info(f"Skills Orchestrator baslatildi: {count} beceri yuklendi")

        return {
            "status": "initialized",
            "skill_count": count,
            "categories": self.registry.list_categories(),
            "timestamp": datetime.now().isoformat(),
        }

    async def execute_skill(
        self,
        skill_identifier: str,
        params: dict[str, Any] | None = None,
        *,
        by_name: bool = False,
    ) -> dict[str, Any]:
        """
        Bir beceriyi calistirir.

        Args:
            skill_identifier: Beceri ID veya adi
            params: Beceri parametreleri
            by_name: True ise isme gore arar
        """
        if not self._initialized:
            await self.initialize()

        params = params or {}
        start = datetime.now()

        try:
            if by_name:
                execution = self.registry.execute_by_name(skill_identifier, **params)
            else:
                execution = self.registry.execute(skill_identifier, **params)

            elapsed = (datetime.now() - start).total_seconds()

            if execution is None:
                result = {"status": "error", "message": "Beceri bulunamadi", "skill": skill_identifier}
                status = "error"
            else:
                result = execution.result if execution.success else {"status": "error", "message": execution.error}
                if execution.success and "status" not in result:
                    result["status"] = "success"
                status = result.get("status", "success" if execution.success else "error")

            log_entry = {
                "skill": skill_identifier,
                "by_name": by_name,
                "params_keys": list(params.keys()),
                "status": status,
                "elapsed_seconds": round(elapsed, 4),
                "timestamp": datetime.now().isoformat(),
            }
            self._execution_log.append(log_entry)
            if len(self._execution_log) > self._max_log:
                self._execution_log = self._execution_log[-self._max_log:]

            return result

        except Exception as e:
            logger.error(f"Beceri calistirma hatasi ({skill_identifier}): {e}")
            return {"status": "error", "message": str(e), "skill": skill_identifier}

    async def search_skills(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Becerileri arar."""
        if not self._initialized:
            await self.initialize()

        definitions = self.registry.search(query)

        results = []
        for d in definitions:
            entry = {
                "skill_id": d.skill_id,
                "name": d.name,
                "description": d.description,
                "category": d.category,
            }
            if category and entry["category"] != category:
                continue
            results.append(entry)

        return results[:limit]

    async def get_skill_info(self, skill_id: str) -> dict[str, Any] | None:
        """Beceri detaylarini dondurur."""
        if not self._initialized:
            await self.initialize()

        return self.registry.get_skill_info(skill_id)

    async def list_categories(self) -> list[dict[str, Any]]:
        """Kategorileri listeler."""
        if not self._initialized:
            await self.initialize()

        return self.registry.list_categories()

    async def get_category_skills(self, category: str) -> list[dict[str, Any]]:
        """Bir kategorideki becerileri listeler."""
        if not self._initialized:
            await self.initialize()

        return self.registry.get_by_category(category)

    async def get_stats(self) -> dict[str, Any]:
        """Orkestrator istatistiklerini dondurur."""
        if not self._initialized:
            await self.initialize()

        total_executions = len(self._execution_log)
        success_count = sum(1 for e in self._execution_log if e.get("status") == "success")
        error_count = sum(1 for e in self._execution_log if e.get("status") == "error")
        avg_elapsed = 0.0
        if self._execution_log:
            avg_elapsed = sum(e.get("elapsed_seconds", 0) for e in self._execution_log) / total_executions

        # En cok kullanilan beceriler
        skill_usage: dict[str, int] = {}
        for entry in self._execution_log:
            sk = entry.get("skill", "?")
            skill_usage[sk] = skill_usage.get(sk, 0) + 1
        top_skills = sorted(skill_usage.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "status": "success",
            "initialized": self._initialized,
            "total_skills": self.registry.count(),
            "total_executions": total_executions,
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": round(success_count / max(total_executions, 1) * 100, 1),
            "avg_execution_time": round(avg_elapsed, 4),
            "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
            "uptime_seconds": (datetime.now() - self.created_at).total_seconds(),
        }

    async def execute_batch(
        self,
        tasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Birden fazla beceriyi toplu calistirir.

        Args:
            tasks: [{"skill_id": "001", "params": {...}}, ...]
        """
        results = []
        for task in tasks:
            skill_id = task.get("skill_id", task.get("skill_name", ""))
            params = task.get("params", {})
            by_name = "skill_name" in task

            result = await self.execute_skill(skill_id, params, by_name=by_name)
            results.append({
                "skill": skill_id,
                "result": result,
            })

        return results

    async def get_catalog(self) -> str:
        """Tum becerilerin katalog metnini dondurur."""
        if not self._initialized:
            await self.initialize()

        return self.registry.format_catalog()

    async def enable_skill(self, skill_id: str) -> dict[str, Any]:
        """Bir beceriyi aktiflestirir."""
        success = self.registry.enable(skill_id)
        return {"status": "success" if success else "error", "skill_id": skill_id, "enabled": success}

    async def disable_skill(self, skill_id: str) -> dict[str, Any]:
        """Bir beceriyi pasiflestirir."""
        success = self.registry.disable(skill_id)
        return {"status": "success" if success else "error", "skill_id": skill_id, "disabled": success}

    async def get_execution_log(
        self,
        limit: int = 50,
        skill_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Calistirma logunu dondurur."""
        log = self._execution_log
        if skill_filter:
            log = [e for e in log if e.get("skill") == skill_filter]
        return log[-limit:]

    async def health_check(self) -> dict[str, Any]:
        """Sistem saglik kontrolu."""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "total_skills": self.registry.count() if self._initialized else 0,
            "initialized": self._initialized,
            "timestamp": datetime.now().isoformat(),
        }
