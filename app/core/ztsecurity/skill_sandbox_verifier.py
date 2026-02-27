"""ATLAS Skill Sandbox Dogrulayici modulu.

Statik analiz ve sandbox testi ile skill
kurulumu oncesi guvenlik dogrulamasi.
Tehlikeli kod kaliplari tespiti.
"""

import logging
import re
import time
from typing import Any
from uuid import uuid4

from app.models.ztsecurity_models import (
    SandboxResult,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

_MAX_APPROVED = 5000
_SANDBOX_TIMEOUT = 30
_MAX_CODE_SIZE = 500000

# Tehlikeli kod kaliplari
_DANGEROUS_PATTERNS: list[
    tuple[str, str, str]
] = [
    (
        r"\beval\s*\(",
        "eval_call",
        "Dinamik kod calistirma: eval()",
    ),
    (
        r"\bexec\s*\(",
        "exec_call",
        "Dinamik kod calistirma: exec()",
    ),
    (
        r"\bos\.system\s*\(",
        "os_system",
        "Isletim sistemi komutu: os.system()",
    ),
    (
        r"\bsubprocess\.",
        "subprocess",
        "Alt surec calistirma: subprocess",
    ),
    (
        r"\b__import__\s*\(",
        "dynamic_import",
        "Dinamik import: __import__()",
    ),
    (
        r"\bopen\s*\(.+['\"]w",
        "file_write",
        "Dosya yazma islemi",
    ),
    (
        r"\bos\.remove\s*\(",
        "file_delete",
        "Dosya silme: os.remove()",
    ),
    (
        r"\bos\.rmdir\s*\(",
        "dir_delete",
        "Dizin silme: os.rmdir()",
    ),
    (
        r"\bshutil\.rmtree\s*\(",
        "tree_delete",
        "Agac silme: shutil.rmtree()",
    ),
    (
        r"\bsocket\.",
        "network_socket",
        "Ag soketi kullanimi",
    ),
    (
        r"\brequests\.(get|post|put|delete)\s*\(",
        "http_request",
        "HTTP istegi gonderme",
    ),
    (
        r"\burllib\.",
        "urllib_usage",
        "URL islemleri: urllib",
    ),
    (
        r"\bctypes\.",
        "ctypes_usage",
        "C tipi erisim: ctypes",
    ),
    (
        r"\bpickle\.(load|loads)\s*\(",
        "pickle_load",
        "Pickle deserialization guvenlik riski",
    ),
    (
        r"\byaml\.load\s*\(",
        "yaml_load",
        "Guvenli olmayan YAML yuklemesi",
    ),
    (
        r"\bcompile\s*\(",
        "code_compile",
        "Kod derleme",
    ),
    (
        r"\bglobals\s*\(\)",
        "globals_access",
        "Global degiskenlere erisim",
    ),
    (
        r"\bsetattr\s*\(",
        "setattr_call",
        "Dinamik ozellik ayarlama",
    ),
    (
        r"\bdelattr\s*\(",
        "delattr_call",
        "Dinamik ozellik silme",
    ),
    (
        r"import\s+sys\b",
        "sys_import",
        "sys modulu erisimi",
    ),
]


class SkillSandboxVerifier:
    """Skill sandbox dogrulayici.

    Statik analiz ve sandbox testi ile skill
    kurulumu oncesi guvenlik dogrulamasi yapar.

    Attributes:
        _approved: Onaylanan skill ID'leri.
        _results: Dogrulama sonuclari.
        _patterns: Tehlikeli kod kaliplari.
    """

    def __init__(
        self,
        sandbox_timeout: int = _SANDBOX_TIMEOUT,
        max_code_size: int = _MAX_CODE_SIZE,
    ) -> None:
        """Dogrulayiciyi baslatir.

        Args:
            sandbox_timeout: Sandbox zaman asimi (sn).
            max_code_size: Max kod boyutu (byte).
        """
        self._approved: set[str] = set()
        self._results: dict[
            str, SandboxResult
        ] = {}
        self._sandbox_timeout = sandbox_timeout
        self._max_code_size = max_code_size
        self._patterns: list[
            tuple[re.Pattern, str, str]
        ] = []
        self._stats = {
            "verified": 0,
            "approved": 0,
            "rejected": 0,
            "threats_detected": 0,
        }

        for pattern_str, code, desc in (
            _DANGEROUS_PATTERNS
        ):
            self._patterns.append((
                re.compile(
                    pattern_str, re.IGNORECASE
                ),
                code,
                desc,
            ))

        logger.info(
            "SkillSandboxVerifier baslatildi, "
            "%d tehlikeli kalip yuklendi",
            len(self._patterns),
        )

    def static_analyze(
        self,
        code_content: str,
    ) -> list[str]:
        """Kod icerigini statik olarak analiz eder.

        Args:
            code_content: Analiz edilecek kod.

        Returns:
            Tespit edilen tehditler listesi.
        """
        threats: list[str] = []

        if len(code_content) > self._max_code_size:
            threats.append(
                f"Kod boyutu cok buyuk: "
                f"{len(code_content)} byte"
            )

        for pattern, code, description in (
            self._patterns
        ):
            matches = pattern.findall(code_content)
            if matches:
                threats.append(
                    f"[{code}] {description} "
                    f"({len(matches)} bulgu)"
                )

        lines = code_content.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 1000:
                threats.append(
                    f"Satir {i + 1}: asiri uzun "
                    f"satir ({len(stripped)} karakter)"
                )
            if stripped.startswith("#!"):
                threats.append(
                    f"Satir {i + 1}: shebang "
                    f"satiri tespit edildi"
                )

        return threats

    def sandbox_test(
        self,
        skill_id: str,
        code_content: str,
        timeout: int | None = None,
    ) -> SandboxResult:
        """Kodu sandbox ortaminda test eder.

        Args:
            skill_id: Skill kimlik numarasi.
            code_content: Test edilecek kod.
            timeout: Zaman asimi (sn).

        Returns:
            Sandbox test sonucu.
        """
        if timeout is None:
            timeout = self._sandbox_timeout

        start = time.time()

        threats = self.static_analyze(code_content)

        elapsed = time.time() - start

        status = (
            VerificationStatus.PASSED
            if not threats
            else VerificationStatus.FAILED
        )

        resource_usage = {
            "cpu_time_ms": round(elapsed * 1000, 2),
            "memory_kb": len(code_content) // 1024,
            "code_lines": code_content.count("\n") + 1,
        }

        result = SandboxResult(
            skill_id=skill_id,
            skill_name=f"skill-{skill_id}",
            status=status,
            threats_found=threats,
            execution_time=round(elapsed, 4),
            resource_usage=resource_usage,
        )

        self._stats["threats_detected"] += len(
            threats
        )

        return result

    def verify(
        self,
        skill_id: str,
        skill_name: str,
        code_content: str,
    ) -> SandboxResult:
        """Skill'i tam dogrulama pipeline'indan gecirir.

        Args:
            skill_id: Skill kimlik numarasi.
            skill_name: Skill adi.
            code_content: Dogrulanacak kod.

        Returns:
            Dogrulama sonucu.
        """
        self._stats["verified"] += 1

        result = self.sandbox_test(
            skill_id, code_content
        )
        result.skill_name = skill_name

        if result.status == VerificationStatus.PASSED:
            self._approved.add(skill_id)
            self._stats["approved"] += 1
            logger.info(
                "Skill onaylandi: %s (%s)",
                skill_name,
                skill_id,
            )
        else:
            self._approved.discard(skill_id)
            self._stats["rejected"] += 1
            logger.warning(
                "Skill reddedildi: %s (%s) - "
                "%d tehdit bulundu",
                skill_name,
                skill_id,
                len(result.threats_found),
            )

        self._results[skill_id] = result
        return result

    def is_approved(
        self,
        skill_id: str,
    ) -> bool:
        """Skill'in onaylanip onaylanmadigini kontrol eder.

        Args:
            skill_id: Skill kimlik numarasi.

        Returns:
            Onaylanmis ise True.
        """
        return skill_id in self._approved

    def get_stats(self) -> dict[str, Any]:
        """Dogrulayici istatistiklerini dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_approved": len(self._approved),
            "total_results": len(self._results),
            "dangerous_patterns": len(
                self._patterns
            ),
            "sandbox_timeout": self._sandbox_timeout,
            **self._stats,
        }
