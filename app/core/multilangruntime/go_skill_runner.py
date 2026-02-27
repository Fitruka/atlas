"""Go beceri calistirici.

Go becerilerini kaydetme, derleme,
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
_DEFAULT_TIMEOUT_MS = 60000
_DEFAULT_MEMORY_MB = 128


class GoSkillRunner:
    """Go beceri calistirici.

    Go becerilerini kaydetme, derleme (go build),
    calistirma, durdurma ve izleme islemlerini
    yonetir.

    Attributes:
        _skills: Kayitli beceriler.
        _executions: Calistirma gecmisi.
        _compiled: Derlenmis beceri kimlikleri.
    """

    def __init__(
        self,
        default_timeout_ms: int = _DEFAULT_TIMEOUT_MS,
        default_memory_mb: int = _DEFAULT_MEMORY_MB,
        go_version: str = "1.22",
    ) -> None:
        """GoSkillRunner baslatir.

        Args:
            default_timeout_ms: Varsayilan zaman asimi (ms).
            default_memory_mb: Varsayilan bellek limiti (MB).
            go_version: Go surumu.
        """
        self._skills: dict[str, SkillPackage] = {}
        self._executions: dict[
            str, SkillExecution
        ] = {}
        self._running: set[str] = set()
        self._compiled: set[str] = set()
        self._default_timeout_ms = default_timeout_ms
        self._default_memory_mb = default_memory_mb
        self._go_version = go_version
        self._total_runs: int = 0
        self._total_successes: int = 0
        self._total_failures: int = 0
        self._total_compiles: int = 0

        logger.info(
            "GoSkillRunner baslatildi: "
            "go_version=%s",
            go_version,
        )

    # ---- Kayit Islemleri ----

    def register_skill(
        self,
        name: str,
        code: str,
        dependencies: list[str] | None = None,
        entry_point: str = "main.go",
    ) -> SkillPackage:
        """Yeni Go becerisi kaydeder.

        Args:
            name: Beceri adi.
            code: Go kaynak kodu.
            dependencies: go mod bagimliliklari.
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
            self._compiled.discard(oldest.id)

        deps = dependencies or []
        checksum = hashlib.sha256(
            code.encode()
        ).hexdigest()[:16]

        pkg = SkillPackage(
            name=name,
            language=SkillLanguage.GO,
            entry_point=entry_point,
            dependencies=deps,
            size_bytes=len(code.encode()),
            checksum=checksum,
            code=code,
            status=SkillStatus.PENDING,
        )

        self._skills[pkg.id] = pkg

        logger.info(
            "Go becerisi kaydedildi: %s (id=%s)",
            name,
            pkg.id,
        )
        return pkg

    # ---- Derleme ----

    def compile_skill(
        self, skill_id: str
    ) -> bool:
        """Go becerisini derler (simulasyon).

        Args:
            skill_id: Beceri ID.

        Returns:
            Basarili ise True.
        """
        skill = self._skills.get(skill_id)
        if not skill:
            logger.error(
                "Beceri bulunamadi: %s", skill_id
            )
            return False

        skill.status = SkillStatus.BUILDING
        self._total_compiles += 1

        # go mod tidy + go build simulasyonu
        if skill.dependencies:
            logger.debug(
                "go mod tidy: %d bagimlilik "
                "(skill=%s)",
                len(skill.dependencies),
                skill_id,
            )

        logger.debug(
            "go build -o %s %s (skill=%s)",
            skill.name,
            skill.entry_point,
            skill_id,
        )

        # Syntax kontrolu simulasyonu
        if "func main()" not in skill.code and \
                "func Main(" not in skill.code:
            logger.warning(
                "Go derlemesi: main fonksiyonu "
                "bulunamadi, devam ediliyor"
            )

        self._compiled.add(skill_id)
        skill.status = SkillStatus.READY

        logger.info(
            "Go becerisi derlendi: %s", skill_id
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

        Derlenmemis becerileri once derler.

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
                language=SkillLanguage.GO,
                exit_code=1,
                stderr=f"Skill not found: {skill_id}",
            )

        # Derlenmemis ise once derle
        if skill_id not in self._compiled:
            success = self.compile_skill(skill_id)
            if not success:
                return SkillExecution(
                    skill_id=skill_id,
                    language=SkillLanguage.GO,
                    exit_code=1,
                    stderr="Compilation failed",
                )

        if skill.status == SkillStatus.FAILED:
            return SkillExecution(
                skill_id=skill_id,
                language=SkillLanguage.GO,
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
                language=SkillLanguage.GO,
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
            "Go becerisi calistirildi: %s, exit=%d",
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
        """Go calistirma simulasyonu.

        Args:
            skill: Beceri paketi.
            args: Arguman dict.
            timeout_ms: Zaman asimi.

        Returns:
            Calistirma sonucu.
        """
        output_lines = [
            f"./{skill.name}",
            f"Go {self._go_version}",
            f"Args: {args}",
            f"Modules: {skill.dependencies}",
            "exit status 0",
        ]

        return SkillExecution(
            skill_id=skill.id,
            language=SkillLanguage.GO,
            exit_code=0,
            stdout="\n".join(output_lines),
            stderr="",
            memory_used_mb=8.0,
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
            "Go becerisi durduruldu: %s",
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
        self._compiled.discard(skill_id)
        del self._skills[skill_id]

        logger.info(
            "Go becerisi silindi: %s",
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
            "language": "go",
            "go_version": self._go_version,
            "total_skills": len(self._skills),
            "compiled_skills": len(self._compiled),
            "running_skills": len(self._running),
            "total_runs": self._total_runs,
            "total_compiles": self._total_compiles,
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
