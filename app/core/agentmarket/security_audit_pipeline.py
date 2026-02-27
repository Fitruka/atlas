"""ATLAS Security Audit Pipeline modulu.

Guvenlik denetim hatti: kod tarama, kalip esleme,
zararli kod tespiti, bagimlilik guvenligi.
"""

import logging
import re
import time
from typing import Any
from uuid import uuid4

from app.models.agentmarket_models import (
    AuditResult,
    SecurityAuditReport,
)

logger = logging.getLogger(__name__)

_AUDITOR_VERSION = "1.2.0"

_DANGEROUS_PATTERNS = [
    (r"\beval\s*\(", "eval_usage",
     "Eval kullanimi tespit edildi", "critical"),
    (r"\bexec\s*\(", "exec_usage",
     "Exec kullanimi tespit edildi", "critical"),
    (r"\b__import__\s*\(", "dynamic_import",
     "Dinamik import tespit edildi", "warning"),
    (r"\bcompile\s*\(", "compile_usage",
     "Compile kullanimi tespit edildi", "warning"),
]

_SHELL_PATTERNS = [
    (r"\bos\.system\s*\(", "os_system",
     "OS system cagrisi tespit edildi", "critical"),
    (r"\bsubprocess\.", "subprocess",
     "Subprocess kullanimi tespit edildi", "critical"),
    (r"\bos\.popen\s*\(", "os_popen",
     "OS popen cagrisi tespit edildi", "critical"),
    (r"\bos\.exec", "os_exec",
     "OS exec cagrisi tespit edildi", "critical"),
]

_NETWORK_PATTERNS = [
    (r"\bsocket\.", "socket_usage",
     "Socket kullanimi tespit edildi", "warning"),
    (r"\brequests\.", "requests_usage",
     "Requests kutuphanesi kullanimi", "warning"),
    (r"\burllib\.", "urllib_usage",
     "Urllib kullanimi tespit edildi", "warning"),
    (r"\bhttpx\.", "httpx_usage",
     "Httpx kullanimi tespit edildi", "warning"),
]

_FILESYSTEM_PATTERNS = [
    (r"\bopen\s*\(", "file_open",
     "Dosya acma tespit edildi", "warning"),
    (r"\bos\.remove\s*\(", "file_delete",
     "Dosya silme tespit edildi", "critical"),
    (r"\bshutil\.rmtree\s*\(", "dir_delete",
     "Dizin silme tespit edildi", "critical"),
    (r"\bos\.chmod\s*\(", "chmod",
     "Dosya izin degisikligi tespit edildi", "warning"),
]

_ENV_PATTERNS = [
    (r"\bos\.environ", "env_access",
     "Ortam degiskeni erisimi", "warning"),
    (r"\bos\.getenv\s*\(", "env_read",
     "Ortam degiskeni okuma", "warning"),
    (r"\bdotenv\.", "dotenv_usage",
     "Dotenv kullanimi tespit edildi", "warning"),
]

_OBFUSCATION_PATTERNS = [
    (r"\\x[0-9a-fA-F]{2}", "hex_escape",
     "Hex kacis dizisi tespit edildi", "warning"),
    (r"\bbase64\.b64decode\s*\(", "base64_decode",
     "Base64 cozme tespit edildi", "warning"),
    (r"\bcodecs\.decode\s*\(", "codecs_decode",
     "Codecs cozme tespit edildi", "warning"),
]

_MALWARE_PATTERNS = [
    (r"\bkeylog", "keylogger",
     "Keylogger kalipli kod tespit edildi", "critical"),
    (r"\breverse.?shell", "reverse_shell",
     "Reverse shell kalipli kod tespit edildi", "critical"),
    (r"\bcrypto.?miner", "cryptominer",
     "Cryptominer kalipli kod tespit edildi", "critical"),
    (r"\bbackdoor", "backdoor",
     "Backdoor kalipli kod tespit edildi", "critical"),
]

_ALL_PATTERNS = (
    _DANGEROUS_PATTERNS
    + _SHELL_PATTERNS
    + _NETWORK_PATTERNS
    + _FILESYSTEM_PATTERNS
    + _ENV_PATTERNS
    + _OBFUSCATION_PATTERNS
    + _MALWARE_PATTERNS
)

_KNOWN_VULN_DEPS = {
    "pyyaml<5.4": "CVE-2020-14343",
    "requests<2.20": "CVE-2018-18074",
    "urllib3<1.26.5": "CVE-2021-33503",
    "pillow<8.3.2": "CVE-2021-34552",
    "jinja2<2.11.3": "CVE-2020-28493",
}


class SecurityAuditPipeline:
    """Guvenlik denetim hatti.

    Kod analizi, kalip esleme ve
    bagimlilik guvenlik kontrolu yapar.

    Attributes:
        _reports: Denetim raporlari.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Denetim hattini baslatir."""
        self._reports: dict[
            str, SecurityAuditReport
        ] = {}
        self._listing_reports: dict[
            str, list[str]
        ] = {}
        self._stats = {
            "audits_run": 0,
            "passed": 0,
            "failed": 0,
            "critical_found": 0,
            "warnings_found": 0,
        }

        logger.info(
            "SecurityAuditPipeline baslatildi",
        )

    def audit(
        self,
        listing_id: str,
        code: str,
        language: str = "python",
    ) -> SecurityAuditReport:
        """Guvenlik denetimi yapar.

        Args:
            listing_id: Listeleme ID.
            code: Denetlenecek kod.
            language: Programlama dili.

        Returns:
            Denetim raporu.
        """
        issues: list[dict[str, Any]] = []

        # Kalip taramasi
        for (
            pattern, issue_id, desc, severity,
        ) in _ALL_PATTERNS:
            matches = re.findall(
                pattern, code, re.IGNORECASE,
            )
            if matches:
                issues.append({
                    "id": issue_id,
                    "description": desc,
                    "severity": severity,
                    "occurrences": len(matches),
                    "pattern": pattern,
                })

        # Bagimlilik guvenlik kontrolu
        dep_issues = (
            self._check_dependency_vulns(code)
        )
        issues.extend(dep_issues)

        # Sonuclari hesapla
        critical_count = sum(
            1 for i in issues
            if i["severity"] == "critical"
        )
        warning_count = sum(
            1 for i in issues
            if i["severity"] == "warning"
        )

        # Sonuc belirleme
        if critical_count > 0:
            result = AuditResult.CRITICAL
            passed = False
        elif warning_count > 3:
            result = AuditResult.WARNING
            passed = False
        elif warning_count > 0:
            result = AuditResult.WARNING
            passed = True
        else:
            result = AuditResult.PASS
            passed = True

        report = SecurityAuditReport(
            listing_id=listing_id,
            result=result,
            issues=issues,
            critical_count=critical_count,
            warning_count=warning_count,
            auditor_version=_AUDITOR_VERSION,
            passed=passed,
        )

        self._reports[report.id] = report

        if listing_id not in self._listing_reports:
            self._listing_reports[listing_id] = []
        self._listing_reports[
            listing_id
        ].append(report.id)

        # Istatistikleri guncelle
        self._stats["audits_run"] += 1
        if passed:
            self._stats["passed"] += 1
        else:
            self._stats["failed"] += 1
        self._stats["critical_found"] += (
            critical_count
        )
        self._stats["warnings_found"] += (
            warning_count
        )

        logger.info(
            "Denetim tamamlandi: %s, sonuc: %s, "
            "kritik: %d, uyari: %d",
            listing_id, result.value,
            critical_count, warning_count,
        )
        return report

    def _check_dependency_vulns(
        self,
        code: str,
    ) -> list[dict[str, Any]]:
        """Bagimlilik guvenligi kontrol eder.

        Args:
            code: Kontrol edilecek kod.

        Returns:
            Bulunan guvenlik sorunlari.
        """
        issues = []
        code_lower = code.lower()

        for dep, cve in _KNOWN_VULN_DEPS.items():
            pkg_name = dep.split("<")[0]
            if pkg_name in code_lower:
                issues.append({
                    "id": f"vuln_{pkg_name}",
                    "description": (
                        f"Savunmasiz bagimlilik: "
                        f"{dep} ({cve})"
                    ),
                    "severity": "warning",
                    "occurrences": 1,
                    "cve": cve,
                })

        return issues

    def get_report(
        self,
        report_id: str,
    ) -> SecurityAuditReport | None:
        """Rapor getirir.

        Args:
            report_id: Rapor ID.

        Returns:
            Rapor veya None.
        """
        return self._reports.get(report_id)

    def list_reports(
        self,
        listing_id: str,
    ) -> list[SecurityAuditReport]:
        """Listeleme raporlarini getirir.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Rapor listesi.
        """
        report_ids = self._listing_reports.get(
            listing_id, [],
        )
        return [
            self._reports[rid]
            for rid in report_ids
            if rid in self._reports
        ]

    def get_failed_audits(
        self,
        limit: int = 50,
    ) -> list[SecurityAuditReport]:
        """Basarisiz denetimleri getirir.

        Args:
            limit: Maksimum sonuc.

        Returns:
            Basarisiz denetim listesi.
        """
        failed = [
            r for r in self._reports.values()
            if not r.passed
        ]
        failed.sort(
            key=lambda r: r.critical_count,
            reverse=True,
        )
        return failed[:limit]

    def re_audit(
        self,
        listing_id: str,
        code: str = "",
        language: str = "python",
    ) -> SecurityAuditReport:
        """Yeniden denetim yapar.

        Args:
            listing_id: Listeleme ID.
            code: Kod (bos ise onceki kod).
            language: Programlama dili.

        Returns:
            Yeni denetim raporu.
        """
        logger.info(
            "Yeniden denetim: %s", listing_id,
        )
        return self.audit(
            listing_id, code, language,
        )

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        return {
            "total_reports": len(self._reports),
            **self._stats,
            "pass_rate": round(
                self._stats["passed"]
                / max(
                    self._stats["audits_run"], 1,
                )
                * 100,
                1,
            ),
        }
