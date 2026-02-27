"""WebAssembly beceri calistirici.

WASM becerilerini kaydetme, modul yukleme,
sandbox icinde calistirma ve yasam dongusu
yonetimi.
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
_DEFAULT_TIMEOUT_MS = 15000
_DEFAULT_MEMORY_MB = 64
_WASM_MAGIC = b"\x00asm"


class WASMSkillRunner:
    """WebAssembly beceri calistirici.

    WASM modullerini kaydetme, yukleme, dogrulama,
    sandbox icinde calistirma ve izleme islemlerini
    yonetir.

    Attributes:
        _skills: Kayitli beceriler.
        _executions: Calistirma gecmisi.
        _loaded_modules: Yuklu WASM modulleri.
    """

    def __init__(
        self,
        default_timeout_ms: int = _DEFAULT_TIMEOUT_MS,
        default_memory_mb: int = _DEFAULT_MEMORY_MB,
        sandbox_enabled: bool = True,
    ) -> None:
        """WASMSkillRunner baslatir.

        Args:
            default_timeout_ms: Varsayilan zaman asimi (ms).
            default_memory_mb: Varsayilan bellek limiti (MB).
            sandbox_enabled: Sandbox modu.
        """
        self._skills: dict[str, SkillPackage] = {}
        self._executions: dict[
            str, SkillExecution
        ] = {}
        self._running: set[str] = set()
        self._loaded_modules: set[str] = set()
        self._sandbox_enabled = sandbox_enabled
        self._default_timeout_ms = default_timeout_ms
        self._default_memory_mb = default_memory_mb
        self._total_runs: int = 0
        self._total_successes: int = 0
        self._total_failures: int = 0
        self._total_loads: int = 0

        logger.info(
            "WASMSkillRunner baslatildi: "
            "sandbox=%s",
            sandbox_enabled,
        )

    # ---- Kayit Islemleri ----

    def register_skill(
        self,
        name: str,
        code: str,
        dependencies: list[str] | None = None,
        entry_point: str = "_start",
    ) -> SkillPackage:
        """Yeni WASM becerisi kaydeder.

        Args:
            name: Beceri adi.
            code: WASM kodu (metin veya binary temsili).
            dependencies: WASI bagimliliklari.
            entry_point: Giris noktasi fonksiyon adi.

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
            self._loaded_modules.discard(oldest.id)

        deps = dependencies or []
        checksum = hashlib.sha256(
            code.encode()
        ).hexdigest()[:16]

        pkg = SkillPackage(
            name=name,
            language=SkillLanguage.WASM,
            entry_point=entry_point,
            dependencies=deps,
            size_bytes=len(code.encode()),
            checksum=checksum,
            code=code,
            status=SkillStatus.PENDING,
        )

        self._skills[pkg.id] = pkg

        logger.info(
            "WASM becerisi kaydedildi: %s (id=%s)",
            name,
            pkg.id,
        )
        return pkg

    # ---- Modul Yukleme ----

    def _validate_wasm_format(
        self, code: str
    ) -> bool:
        """WASM binary formatini dogrular.

        Args:
            code: Beceri kodu/temsili.

        Returns:
            Gecerli WASM formatinda ise True.
        """
        # Gercek ortamda binary magic number kontrolu
        # Simulasyonda icerik kontrolu
        if not code or len(code) < 4:
            return False

        # WASM WAT text formati veya binary
        if code.startswith("(module") or \
                code.startswith("\\x00asm") or \
                len(code) > 8:
            return True

        return False

    def load_module(
        self, skill_id: str
    ) -> bool:
        """WASM modulunu yukler ve dogrular.

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
        self._total_loads += 1

        # WASM format dogrulama
        if not self._validate_wasm_format(
            skill.code
        ):
            logger.warning(
                "WASM format dogrulamasi: "
                "yine de yukleniyor (skill=%s)",
                skill_id,
            )

        # Sandbox yapilandirmasi
        if self._sandbox_enabled:
            logger.debug(
                "WASM sandbox yapilandi: "
                "memory=%dMB (skill=%s)",
                self._default_memory_mb,
                skill_id,
            )

        self._loaded_modules.add(skill_id)
        skill.status = SkillStatus.READY

        logger.info(
            "WASM modulu yuklendi: %s", skill_id
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

        Yuklenmemis modulleri once yukler.

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
                language=SkillLanguage.WASM,
                exit_code=1,
                stderr=f"Skill not found: {skill_id}",
            )

        # Yuklenmemis ise once yukle
        if skill_id not in self._loaded_modules:
            success = self.load_module(skill_id)
            if not success:
                return SkillExecution(
                    skill_id=skill_id,
                    language=SkillLanguage.WASM,
                    exit_code=1,
                    stderr="Module load failed",
                )

        if skill.status == SkillStatus.FAILED:
            return SkillExecution(
                skill_id=skill_id,
                language=SkillLanguage.WASM,
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
                language=SkillLanguage.WASM,
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
            "WASM becerisi calistirildi: %s, "
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
        """WASM calistirma simulasyonu.

        Args:
            skill: Beceri paketi.
            args: Arguman dict.
            timeout_ms: Zaman asimi.

        Returns:
            Calistirma sonucu.
        """
        sandbox_str = (
            "sandboxed"
            if self._sandbox_enabled
            else "unrestricted"
        )
        output_lines = [
            f"wasm-runtime ({sandbox_str})",
            f"Module: {skill.name}",
            f"Entry: {skill.entry_point}",
            f"Args: {args}",
            f"Memory limit: "
            f"{self._default_memory_mb}MB",
            "Execution completed",
        ]

        return SkillExecution(
            skill_id=skill.id,
            language=SkillLanguage.WASM,
            exit_code=0,
            stdout="\n".join(output_lines),
            stderr="",
            memory_used_mb=4.0,
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
            "WASM becerisi durduruldu: %s",
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
        self._loaded_modules.discard(skill_id)
        del self._skills[skill_id]

        logger.info(
            "WASM becerisi silindi: %s",
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
            "language": "wasm",
            "sandbox_enabled": self._sandbox_enabled,
            "total_skills": len(self._skills),
            "loaded_modules": len(
                self._loaded_modules
            ),
            "running_skills": len(self._running),
            "total_runs": self._total_runs,
            "total_loads": self._total_loads,
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
