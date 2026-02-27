"""Multi-Language Skill Runtime orkestratoru.

Tum cok dilli calisma zamani bilesenlerini
koordine eder: runner secimi, dagitim pipeline,
durum izleme ve birlestirme.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.core.multilangruntime.go_skill_runner import (
    GoSkillRunner,
)
from app.core.multilangruntime.nodejs_skill_runner import (
    NodeJSSkillRunner,
)
from app.core.multilangruntime.python_skill_runner import (
    PythonSkillRunner,
)
from app.core.multilangruntime.skill_marketplace import (
    SkillMarketplace,
)
from app.core.multilangruntime.skill_sdk import (
    SkillSDK,
)
from app.core.multilangruntime.skill_test_harness import (
    SkillTestHarness,
)
from app.core.multilangruntime.wasm_skill_runner import (
    WASMSkillRunner,
)
from app.models.multilangruntime_models import (
    MarketplaceCategory,
    MarketplaceEntry,
    SecurityScanResult,
    SkillExecution,
    SkillLanguage,
    SkillPackage,
    SkillTestReport,
)

logger = logging.getLogger(__name__)

_MAX_DEPLOY_HISTORY = 1000


class MultiLangRuntimeOrchestrator:
    """Multi-Language Runtime orkestratoru.

    Tum cok dilli beceri calisma zamani
    bilesenlerini koordine eder:
    Register -> Test -> Scan -> Publish pipeline.

    Attributes:
        python_runner: Python calistirici.
        nodejs_runner: Node.js calistirici.
        go_runner: Go calistirici.
        wasm_runner: WASM calistirici.
        sdk: Beceri SDK.
        marketplace: Pazar yeri.
        test_harness: Test donanimci.
    """

    def __init__(self) -> None:
        """MultiLangRuntimeOrchestrator baslatir."""
        self.python_runner = PythonSkillRunner()
        self.nodejs_runner = NodeJSSkillRunner()
        self.go_runner = GoSkillRunner()
        self.wasm_runner = WASMSkillRunner()
        self.sdk = SkillSDK()
        self.marketplace = SkillMarketplace()
        self.test_harness = SkillTestHarness()

        self._deploy_history: list[
            dict[str, Any]
        ] = []
        self._total_deploys: int = 0
        self._total_executions: int = 0
        self._total_failures: int = 0

        logger.info(
            "MultiLangRuntimeOrchestrator "
            "baslatildi"
        )

    # ---- Runner Eslestirme ----

    def _get_runner(
        self, language: SkillLanguage
    ) -> Any:
        """Dile uygun runner dondurur.

        Args:
            language: Programlama dili.

        Returns:
            Runner nesnesi veya None.
        """
        runner_map = {
            SkillLanguage.PYTHON: (
                self.python_runner
            ),
            SkillLanguage.NODEJS: (
                self.nodejs_runner
            ),
            SkillLanguage.GO: self.go_runner,
            SkillLanguage.WASM: self.wasm_runner,
        }
        return runner_map.get(language)

    # ---- Dagitim Pipeline ----

    def deploy_skill(
        self,
        name: str,
        language: SkillLanguage,
        code: str,
        dependencies: list[str] | None = None,
        entry_point: str = "",
        test_code: str = "",
        author: str = "",
        category: MarketplaceCategory = (
            MarketplaceCategory.UTILITY
        ),
    ) -> dict[str, Any]:
        """Tam dagitim pipeline'i calistirir.

        Register -> Test -> Security Scan -> Publish.

        Args:
            name: Beceri adi.
            language: Programlama dili.
            code: Kaynak kodu.
            dependencies: Bagimliliklar.
            entry_point: Giris noktasi.
            test_code: Test kodu (opsiyonel).
            author: Yazar.
            category: Pazar yeri kategorisi.

        Returns:
            Dagitim sonucu sozlugu.
        """
        deploy_id = str(uuid4())[:8]
        start = time.time()
        self._total_deploys += 1

        result: dict[str, Any] = {
            "deploy_id": deploy_id,
            "name": name,
            "language": language.value,
            "steps": {},
            "success": False,
        }

        # 1. Kayit
        runner = self._get_runner(language)
        if not runner:
            result["error"] = (
                f"Unsupported language: "
                f"{language.value}"
            )
            self._total_failures += 1
            self._record_deploy(result, start)
            return result

        try:
            ep = entry_point or ""
            if ep:
                pkg = runner.register_skill(
                    name, code, dependencies, ep
                )
            else:
                pkg = runner.register_skill(
                    name, code, dependencies
                )
            result["steps"]["register"] = {
                "success": True,
                "skill_id": pkg.id,
            }
            result["skill_id"] = pkg.id
        except Exception as e:
            result["steps"]["register"] = {
                "success": False,
                "error": str(e),
            }
            self._total_failures += 1
            self._record_deploy(result, start)
            return result

        # 2. Test (eger test kodu verilmisse)
        if test_code:
            try:
                report = (
                    self.test_harness.run_tests(
                        pkg.id, language, test_code
                    )
                )
                test_passed = report.failed == 0 and \
                    report.errors == 0
                result["steps"]["test"] = {
                    "success": test_passed,
                    "total": report.total_tests,
                    "passed": report.passed,
                    "failed": report.failed,
                    "report_id": report.id,
                }
                if not test_passed:
                    result["steps"]["test"][
                        "warning"
                    ] = "Some tests failed"
            except Exception as e:
                result["steps"]["test"] = {
                    "success": False,
                    "error": str(e),
                }
        else:
            result["steps"]["test"] = {
                "success": True,
                "skipped": True,
            }

        # 3. Guvenlik taramasi
        try:
            scan = (
                self.test_harness.run_security_scan(
                    pkg.id, language, code
                )
            )
            result["steps"]["security_scan"] = {
                "success": scan.passed,
                "risk_level": scan.risk_level.value,
                "issues": len(scan.issues),
                "scan_id": scan.id,
            }
        except Exception as e:
            result["steps"]["security_scan"] = {
                "success": False,
                "error": str(e),
            }

        # 4. Pazar yerine yayinla
        try:
            entry = self.marketplace.publish(
                skill_id=pkg.id,
                name=name,
                description=(
                    f"{name} skill ({language.value})"
                ),
                author=author,
                category=category,
                language=language,
            )
            result["steps"]["publish"] = {
                "success": True,
                "entry_id": entry.id,
            }
            result["marketplace_id"] = entry.id
        except Exception as e:
            result["steps"]["publish"] = {
                "success": False,
                "error": str(e),
            }

        result["success"] = True
        self._record_deploy(result, start)

        logger.info(
            "Beceri dagitildi: %s (id=%s, "
            "lang=%s)",
            name,
            pkg.id,
            language.value,
        )
        return result

    def _record_deploy(
        self,
        result: dict[str, Any],
        start: float,
    ) -> None:
        """Dagitim kaydini tutar.

        Args:
            result: Dagitim sonucu.
            start: Baslangic zamani.
        """
        result["duration_ms"] = round(
            (time.time() - start) * 1000, 2
        )
        self._deploy_history.append(result)

        if (
            len(self._deploy_history)
            > _MAX_DEPLOY_HISTORY
        ):
            self._deploy_history = (
                self._deploy_history[
                    -_MAX_DEPLOY_HISTORY:
                ]
            )

    # ---- Calistirma ----

    def execute_skill(
        self,
        skill_id: str,
        language: SkillLanguage,
        args: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> SkillExecution:
        """Beceriyi uygun runner ile calistirir.

        Args:
            skill_id: Beceri ID.
            language: Programlama dili.
            args: Calistirma argumanlari.
            timeout_ms: Zaman asimi (ms).

        Returns:
            Calistirma sonucu.
        """
        self._total_executions += 1

        runner = self._get_runner(language)
        if not runner:
            logger.error(
                "Desteklenmeyen dil: %s",
                language.value,
            )
            self._total_failures += 1
            return SkillExecution(
                skill_id=skill_id,
                language=language,
                exit_code=1,
                stderr=(
                    f"Unsupported language: "
                    f"{language.value}"
                ),
            )

        result = runner.run_skill(
            skill_id, args, timeout_ms
        )

        if result.exit_code != 0:
            self._total_failures += 1

        logger.info(
            "Beceri calistirildi: %s (lang=%s, "
            "exit=%d)",
            skill_id,
            language.value,
            result.exit_code,
        )
        return result

    # ---- Durum Sorgulama ----

    def get_runtime_status(
        self,
    ) -> dict[str, Any]:
        """Tum runner'larin durumunu dondurur.

        Returns:
            Runner durumlari sozlugu.
        """
        return {
            "python": self.python_runner.get_stats(),
            "nodejs": self.nodejs_runner.get_stats(),
            "go": self.go_runner.get_stats(),
            "wasm": self.wasm_runner.get_stats(),
            "sdk": self.sdk.get_stats(),
            "marketplace": (
                self.marketplace.get_stats()
            ),
            "test_harness": (
                self.test_harness.get_stats()
            ),
        }

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Birlestirillmis istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        py = self.python_runner.get_stats()
        nj = self.nodejs_runner.get_stats()
        go = self.go_runner.get_stats()
        wa = self.wasm_runner.get_stats()

        total_skills = (
            py["total_skills"]
            + nj["total_skills"]
            + go["total_skills"]
            + wa["total_skills"]
        )

        total_runs = (
            py["total_runs"]
            + nj["total_runs"]
            + go["total_runs"]
            + wa["total_runs"]
        )

        return {
            "total_skills": total_skills,
            "total_runs": total_runs,
            "total_deploys": self._total_deploys,
            "total_executions": (
                self._total_executions
            ),
            "total_failures": (
                self._total_failures
            ),
            "deploy_history_size": len(
                self._deploy_history
            ),
            "runners": {
                "python": py,
                "nodejs": nj,
                "go": go,
                "wasm": wa,
            },
            "sdk": self.sdk.get_stats(),
            "marketplace": (
                self.marketplace.get_stats()
            ),
            "test_harness": (
                self.test_harness.get_stats()
            ),
        }
