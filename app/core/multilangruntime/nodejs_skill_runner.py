"""Node.js beceri calistirici.

Node.js becerilerini kaydetme, npm kurulum,
calistirma, durdurma ve yasam dongusu yonetimi.
"""

import hashlib
import logging
import time
from typing import Any
from uuid import uuid4

from app.models.multilangruntime_models import (
    SkillExecution,
    SkillLanguage,
    SkillPackage,
    SkillStatus,
)

logger = logging.getLogger(__name__)

_MAX_SKILLS = 500
_MAX_EXECUTIONS = 5000
_DEFAULT_TIMEOUT_MS = 30000
_DEFAULT_MEMORY_MB = 512


class NodeJSSkillRunner:
    """Node.js beceri calistirici.

    Node.js becerilerini kaydetme, npm bagimlilik
    kurma, calistirma, durdurma ve izleme
    islemlerini yonetir.

    Attributes:
        _skills: Kayitli beceriler.
        _executions: Calistirma gecmisi.
    """

    def __init__(
        self,
        default_timeout_ms: int = _DEFAULT_TIMEOUT_MS,
        default_memory_mb: int = _DEFAULT_MEMORY_MB,
        node_version: str = "20",
    ) -> None:
        """NodeJSSkillRunner baslatir.

        Args:
            default_timeout_ms: Varsayilan zaman asimi (ms).
            default_memory_mb: Varsayilan bellek limiti (MB).
            node_version: Node.js surumu.
        """
        self._skills: dict[str, SkillPackage] = {}
        self._executions: dict[
            str, SkillExecution
        ] = {}
        self._running: set[str] = set()
        self._installed_deps: dict[
            str, list[str]
        ] = {}
        self._default_timeout_ms = default_timeout_ms
        self._default_memory_mb = default_memory_mb
        self._node_version = node_version
        self._total_runs: int = 0
        self._total_successes: int = 0
        self._total_failures: int = 0

        logger.info(
            "NodeJSSkillRunner baslatildi: "
            "node_version=%s",
            node_version,
        )

    # ---- Kayit Islemleri ----

    def register_skill(
        self,
        name: str,
        code: str,
        dependencies: list[str] | None = None,
        entry_point: str = "index.js",
    ) -> SkillPackage:
        """Yeni Node.js becerisi kaydeder.

        Args:
            name: Beceri adi.
            code: JavaScript kaynak kodu.
            dependencies: npm bagimliliklari.
            entry_point: Giris noktasi dosya adi.

        Returns:
            Olusturulan beceri paketi.
        """
        if len(self._skills) >= _MAX_SKILLS:
            logger.warning(
                "Maksimum beceri sayisina ulasildi: %d",
                _MAX_SKILLS,
            )
            oldest = min(
                self._skills.values(),
                key=lambda s: s.created_at,
            )
            del self._skills[oldest.id]

        deps = dependencies or []
        checksum = hashlib.sha256(
            code.encode()
        ).hexdigest()[:16]

        pkg = SkillPackage(
            name=name,
            language=SkillLanguage.NODEJS,
            entry_point=entry_point,
            dependencies=deps,
            size_bytes=len(code.encode()),
            checksum=checksum,
            code=code,
            status=SkillStatus.PENDING,
        )

        # npm install simulasyonu
        if deps:
            self._npm_install(pkg.id, deps)

        pkg.status = SkillStatus.READY
        self._skills[pkg.id] = pkg

        logger.info(
            "Node.js becerisi kaydedildi: %s (id=%s)",
            name,
            pkg.id,
        )
        return pkg

    def _npm_install(
        self,
        skill_id: str,
        deps: list[str],
    ) -> bool:
        """npm bagimlilik kurulumu (simulasyon).

        Args:
            skill_id: Beceri ID.
            deps: Bagimlilik listesi.

        Returns:
            Basarili ise True.
        """
        installed: list[str] = []
        for dep in deps:
            logger.debug(
                "npm install %s (skill=%s)",
                dep,
                skill_id,
            )
            installed.append(dep)

        self._installed_deps[skill_id] = installed
        logger.info(
            "npm install tamamlandi: %d paket "
            "(skill=%s)",
            len(installed),
            skill_id,
        )
        return True

    # ---- Calistirma ----

    def run_skill(
        self,
        skill_id: str,
        args: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> SkillExecution:
        """Beceri calistirir.

        Args:
            skill_id: Beceri ID.
            args: Calistirma argumanlari.
            timeout_ms: Zaman asimi (ms).

        Returns:
            Calistirma sonucu.
        """
        skill = self._skills.get(skill_id)
        if not skill:
            logger.error(
                "Beceri bulunamadi: %s", skill_id
            )
            return SkillExecution(
                skill_id=skill_id,
                language=SkillLanguage.NODEJS,
                exit_code=1,
                stderr=f"Skill not found: {skill_id}",
            )

        if skill.status == SkillStatus.FAILED:
            return SkillExecution(
                skill_id=skill_id,
                language=SkillLanguage.NODEJS,
                exit_code=1,
                stderr="Skill is in failed state",
            )

        timeout = (
            timeout_ms or self._default_timeout_ms
        )
        start = time.time()

        self._running.add(skill_id)
        skill.status = SkillStatus.RUNNING
        self._total_runs += 1

        try:
            exec_result = self._simulate_execution(
                skill, args or {}, timeout
            )
            skill.status = SkillStatus.READY
            self._total_successes += 1
        except Exception as e:
            exec_result = SkillExecution(
                skill_id=skill_id,
                language=SkillLanguage.NODEJS,
                exit_code=1,
                stderr=str(e),
            )
            skill.status = SkillStatus.FAILED
            self._total_failures += 1
        finally:
            self._running.discard(skill_id)

        elapsed = (time.time() - start) * 1000
        exec_result.cpu_time_ms = elapsed
        exec_result.end_time = time.time()

        self._executions[exec_result.id] = (
            exec_result
        )

        if len(self._executions) > _MAX_EXECUTIONS:
            oldest_key = next(
                iter(self._executions)
            )
            del self._executions[oldest_key]

        logger.info(
            "Node.js becerisi calistirildi: %s, "
            "exit=%d",
            skill_id,
            exec_result.exit_code,
        )
        return exec_result

    def _simulate_execution(
        self,
        skill: SkillPackage,
        args: dict[str, Any],
        timeout_ms: int,
    ) -> SkillExecution:
        """Node.js calistirma simulasyonu.

        Args:
            skill: Beceri paketi.
            args: Arguman dict.
            timeout_ms: Zaman asimi.

        Returns:
            Calistirma sonucu.
        """
        output_lines = [
            f"node {skill.entry_point}",
            f"Node.js v{self._node_version}",
            f"Running {skill.name}",
            f"Args: {args}",
            f"Modules: {skill.dependencies}",
            "Process exited with code 0",
        ]

        return SkillExecution(
            skill_id=skill.id,
            language=SkillLanguage.NODEJS,
            exit_code=0,
            stdout="\n".join(output_lines),
            stderr="",
            memory_used_mb=25.0,
        )

    # ---- Sorgulama ----

    def get_skill(
        self, skill_id: str
    ) -> SkillPackage | None:
        """Beceri bilgisi getirir.

        Args:
            skill_id: Beceri ID.

        Returns:
            Beceri paketi veya None.
        """
        return self._skills.get(skill_id)

    def list_skills(
        self, status: SkillStatus | None = None
    ) -> list[SkillPackage]:
        """Becerileri listeler.

        Args:
            status: Durum filtresi.

        Returns:
            Beceri listesi.
        """
        skills = list(self._skills.values())
        if status:
            skills = [
                s for s in skills
                if s.status == status
            ]
        return skills

    # ---- Durdurma / Silme ----

    def stop_skill(self, skill_id: str) -> bool:
        """Calisan beceriyi durdurur.

        Args:
            skill_id: Beceri ID.

        Returns:
            Basarili ise True.
        """
        skill = self._skills.get(skill_id)
        if not skill:
            return False

        self._running.discard(skill_id)
        skill.status = SkillStatus.STOPPED

        logger.info(
            "Node.js becerisi durduruldu: %s",
            skill_id,
        )
        return True

    def unregister_skill(
        self, skill_id: str
    ) -> bool:
        """Beceri kaydini siler.

        Args:
            skill_id: Beceri ID.

        Returns:
            Basarili ise True.
        """
        if skill_id not in self._skills:
            return False

        self._running.discard(skill_id)
        del self._skills[skill_id]
        self._installed_deps.pop(
            skill_id, None
        )

        logger.info(
            "Node.js becerisi silindi: %s",
            skill_id,
        )
        return True

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "language": "nodejs",
            "node_version": self._node_version,
            "total_skills": len(self._skills),
            "running_skills": len(self._running),
            "total_runs": self._total_runs,
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
            "total_executions": len(
                self._executions
            ),
            "success_rate": (
                round(
                    self._total_successes
                    / self._total_runs
                    * 100,
                    2,
                )
                if self._total_runs > 0
                else 0.0
            ),
        }
