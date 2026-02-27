"""Beceri test donanimci.

Beceri test calistirma, guvenlik taramasi,
performans testi ve raporlama.
"""

import logging
import re
import time
from typing import Any
from uuid import uuid4

from app.models.multilangruntime_models import (
    SecurityLevel,
    SecurityScanResult,
    SkillLanguage,
    SkillTestReport,
    TestResult,
)

logger = logging.getLogger(__name__)

_MAX_REPORTS = 2000
_MAX_SCAN_RESULTS = 2000

# Dile gore tehlikeli kaliplar
_DANGEROUS_PATTERNS: dict[
    SkillLanguage, list[tuple[str, str, str]]
] = {
    SkillLanguage.PYTHON: [
        (
            r"\beval\s*\(",
            "eval() usage",
            "critical",
        ),
        (
            r"\bexec\s*\(",
            "exec() usage",
            "critical",
        ),
        (
            r"\bos\.system\s*\(",
            "os.system() usage",
            "high",
        ),
        (
            r"\bsubprocess\.",
            "subprocess usage",
            "high",
        ),
        (
            r"\b__import__\s*\(",
            "__import__() usage",
            "medium",
        ),
        (
            r"\bopen\s*\(.+,\s*['\"]w",
            "file write operation",
            "medium",
        ),
        (
            r"\bos\.remove\s*\(",
            "file deletion",
            "high",
        ),
        (
            r"\bshutil\.rmtree\s*\(",
            "directory deletion",
            "critical",
        ),
        (
            r"\bsocket\.",
            "raw socket usage",
            "medium",
        ),
        (
            r"\bpickle\.",
            "pickle usage (deserialization)",
            "medium",
        ),
    ],
    SkillLanguage.NODEJS: [
        (
            r"\beval\s*\(",
            "eval() usage",
            "critical",
        ),
        (
            r"\bFunction\s*\(",
            "Function constructor",
            "critical",
        ),
        (
            r"\bchild_process",
            "child_process usage",
            "high",
        ),
        (
            r"\bfs\.writeFile",
            "file write operation",
            "medium",
        ),
        (
            r"\bfs\.unlink",
            "file deletion",
            "high",
        ),
        (
            r"\brequire\s*\(\s*['\"]net['\"]",
            "net module usage",
            "medium",
        ),
        (
            r"\bprocess\.exit",
            "process.exit usage",
            "medium",
        ),
    ],
    SkillLanguage.GO: [
        (
            r"\bos/exec\b",
            "exec package",
            "high",
        ),
        (
            r"\bunsafe\.",
            "unsafe package",
            "critical",
        ),
        (
            r"\bos\.Remove",
            "file deletion",
            "high",
        ),
        (
            r"\bsyscall\.",
            "syscall usage",
            "high",
        ),
        (
            r"\breflect\.",
            "reflect usage",
            "medium",
        ),
    ],
    SkillLanguage.WASM: [
        (
            r"\bfd_write\b",
            "WASI file write",
            "medium",
        ),
        (
            r"\bsock_\w+",
            "WASI socket usage",
            "high",
        ),
    ],
    SkillLanguage.RUST: [
        (
            r"\bunsafe\s*\{",
            "unsafe block",
            "high",
        ),
        (
            r"\bstd::process::Command",
            "command execution",
            "high",
        ),
        (
            r"\bstd::fs::remove",
            "file deletion",
            "high",
        ),
    ],
    SkillLanguage.RUBY: [
        (
            r"\beval\s*\(",
            "eval() usage",
            "critical",
        ),
        (
            r"\bsystem\s*\(",
            "system() usage",
            "high",
        ),
        (
            r"`[^`]+`",
            "backtick execution",
            "high",
        ),
        (
            r"\bFile\.delete",
            "file deletion",
            "high",
        ),
    ],
}


class SkillTestHarness:
    """Beceri test donanimci sinifi.

    Beceri test calistirma, guvenlik taramasi,
    performans testi ve raporlama islemlerini
    yonetir.

    Attributes:
        _reports: Test raporlari.
        _scan_results: Guvenlik tarama sonuclari.
    """

    def __init__(self) -> None:
        """SkillTestHarness baslatir."""
        self._reports: dict[
            str, SkillTestReport
        ] = {}
        self._scan_results: dict[
            str, SecurityScanResult
        ] = {}
        self._total_test_runs: int = 0
        self._total_scans: int = 0
        self._total_perf_tests: int = 0

        logger.info(
            "SkillTestHarness baslatildi"
        )

    # ---- Test Calistirma ----

    def run_tests(
        self,
        skill_id: str,
        language: SkillLanguage,
        test_code: str,
    ) -> SkillTestReport:
        """Beceri testlerini calistirir.

        Args:
            skill_id: Beceri ID.
            language: Programlama dili.
            test_code: Test kaynak kodu.

        Returns:
            Test raporu.
        """
        start = time.time()
        self._total_test_runs += 1

        # Test fonksiyonlarini tespit et
        test_functions = self._detect_tests(
            language, test_code
        )

        # Her testi calistir (simulasyon)
        results: list[dict[str, Any]] = []
        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        for test_name in test_functions:
            result = self._run_single_test(
                test_name, language
            )
            results.append(result)

            status = result.get("status", "error")
            if status == TestResult.PASSED.value:
                passed += 1
            elif status == TestResult.FAILED.value:
                failed += 1
            elif status == TestResult.SKIPPED.value:
                skipped += 1
            else:
                errors += 1

        elapsed = (time.time() - start) * 1000
        total = len(test_functions)

        # Kapsam tahmini
        coverage = (
            round(passed / total * 85, 1)
            if total > 0
            else 0.0
        )

        report = SkillTestReport(
            skill_id=skill_id,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            coverage_pct=coverage,
            duration_ms=elapsed,
            results=results,
        )

        self._reports[report.id] = report

        if len(self._reports) > _MAX_REPORTS:
            oldest_key = next(
                iter(self._reports)
            )
            del self._reports[oldest_key]

        logger.info(
            "Test calistirildi: skill=%s, "
            "total=%d, passed=%d, failed=%d",
            skill_id,
            total,
            passed,
            failed,
        )
        return report

    def _detect_tests(
        self,
        language: SkillLanguage,
        test_code: str,
    ) -> list[str]:
        """Test fonksiyonlarini tespit eder.

        Args:
            language: Programlama dili.
            test_code: Test kaynak kodu.

        Returns:
            Test fonksiyon adlari.
        """
        patterns: dict[SkillLanguage, str] = {
            SkillLanguage.PYTHON: (
                r"def\s+(test_\w+)"
            ),
            SkillLanguage.NODEJS: (
                r"(?:it|test)\s*\(\s*['\"]([^'\"]+)"
            ),
            SkillLanguage.GO: (
                r"func\s+(Test\w+)"
            ),
            SkillLanguage.RUST: (
                r"fn\s+(test_\w+)"
            ),
            SkillLanguage.RUBY: (
                r"def\s+(test_\w+)"
            ),
        }

        pattern = patterns.get(
            language,
            r"(?:test|it)\s*[\(]?\s*['\"]?(\w+)",
        )
        matches = re.findall(
            pattern, test_code
        )

        if not matches:
            # En az bir test varsayimi
            matches = ["test_default"]

        return matches

    def _run_single_test(
        self,
        test_name: str,
        language: SkillLanguage,
    ) -> dict[str, Any]:
        """Tek bir test calistirir (simulasyon).

        Args:
            test_name: Test adi.
            language: Programlama dili.

        Returns:
            Test sonucu dict.
        """
        # Deterministik sonuc: skip iceriyorsa skip
        if "skip" in test_name.lower():
            status = TestResult.SKIPPED.value
        elif "fail" in test_name.lower():
            status = TestResult.FAILED.value
        elif "error" in test_name.lower():
            status = TestResult.ERROR.value
        else:
            status = TestResult.PASSED.value

        return {
            "name": test_name,
            "status": status,
            "duration_ms": 1.5,
            "language": language.value,
        }

    # ---- Guvenlik Taramasi ----

    def run_security_scan(
        self,
        skill_id: str,
        language: SkillLanguage,
        code: str,
    ) -> SecurityScanResult:
        """Guvenlik taramasi calistirir.

        Args:
            skill_id: Beceri ID.
            language: Programlama dili.
            code: Kaynak kodu.

        Returns:
            Guvenlik tarama sonucu.
        """
        start = time.time()
        self._total_scans += 1

        patterns = _DANGEROUS_PATTERNS.get(
            language, []
        )
        issues: list[dict[str, Any]] = []

        for pattern, desc, severity in patterns:
            matches = re.findall(pattern, code)
            if matches:
                issues.append(
                    {
                        "pattern": pattern,
                        "description": desc,
                        "severity": severity,
                        "occurrences": len(matches),
                    }
                )

        # Risk seviyesi hesapla
        risk_level = self._calculate_risk(issues)
        passed = risk_level in (
            SecurityLevel.LOW,
            SecurityLevel.MEDIUM,
        )

        elapsed = (time.time() - start) * 1000

        result = SecurityScanResult(
            skill_id=skill_id,
            language=language,
            issues=issues,
            risk_level=risk_level,
            passed=passed,
            scan_duration_ms=elapsed,
        )

        self._scan_results[result.id] = result

        if (
            len(self._scan_results)
            > _MAX_SCAN_RESULTS
        ):
            oldest_key = next(
                iter(self._scan_results)
            )
            del self._scan_results[oldest_key]

        logger.info(
            "Guvenlik taramasi: skill=%s, "
            "sorunlar=%d, risk=%s, passed=%s",
            skill_id,
            len(issues),
            risk_level.value,
            passed,
        )
        return result

    def _calculate_risk(
        self, issues: list[dict[str, Any]]
    ) -> SecurityLevel:
        """Sorunlardan risk seviyesi hesaplar.

        Args:
            issues: Tespit edilen sorunlar.

        Returns:
            Risk seviyesi.
        """
        if not issues:
            return SecurityLevel.LOW

        severities = [
            i.get("severity", "low")
            for i in issues
        ]

        if "critical" in severities:
            return SecurityLevel.CRITICAL
        if "high" in severities:
            return SecurityLevel.HIGH
        if "medium" in severities:
            return SecurityLevel.MEDIUM
        return SecurityLevel.LOW

    # ---- Performans Testi ----

    def run_performance_test(
        self,
        skill_id: str,
        iterations: int = 100,
    ) -> dict[str, Any]:
        """Performans testi calistirir.

        Args:
            skill_id: Beceri ID.
            iterations: Tekrar sayisi.

        Returns:
            Performans metrikleri.
        """
        self._total_perf_tests += 1
        start = time.time()

        # Iterasyon basina simulasyon
        times: list[float] = []
        for i in range(iterations):
            iter_start = time.time()
            # Minimal simulasyon islemi
            _ = hashlib_noop(i)
            iter_time = (
                time.time() - iter_start
            ) * 1000
            times.append(iter_time)

        total_time = (
            time.time() - start
        ) * 1000

        avg_time = (
            sum(times) / len(times)
            if times
            else 0.0
        )
        min_time = min(times) if times else 0.0
        max_time = max(times) if times else 0.0

        result = {
            "skill_id": skill_id,
            "iterations": iterations,
            "total_ms": round(total_time, 2),
            "avg_ms": round(avg_time, 4),
            "min_ms": round(min_time, 4),
            "max_ms": round(max_time, 4),
            "throughput_per_sec": round(
                iterations / (total_time / 1000)
                if total_time > 0
                else 0,
                2,
            ),
        }

        logger.info(
            "Performans testi: skill=%s, "
            "iterations=%d, avg=%.4fms",
            skill_id,
            iterations,
            avg_time,
        )
        return result

    # ---- Rapor Sorgulama ----

    def get_report(
        self, report_id: str
    ) -> SkillTestReport | None:
        """Test raporunu getirir.

        Args:
            report_id: Rapor ID.

        Returns:
            Test raporu veya None.
        """
        return self._reports.get(report_id)

    def list_reports(
        self, skill_id: str
    ) -> list[SkillTestReport]:
        """Beceriye ait raporlari listeler.

        Args:
            skill_id: Beceri ID.

        Returns:
            Rapor listesi.
        """
        return [
            r
            for r in self._reports.values()
            if r.skill_id == skill_id
        ]

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_reports": len(self._reports),
            "total_scan_results": len(
                self._scan_results
            ),
            "total_test_runs": (
                self._total_test_runs
            ),
            "total_scans": self._total_scans,
            "total_perf_tests": (
                self._total_perf_tests
            ),
        }


def hashlib_noop(i: int) -> int:
    """Performans testi icin minimal islem.

    Args:
        i: Iterasyon numarasi.

    Returns:
        Hash degeri.
    """
    return hash(str(i))
