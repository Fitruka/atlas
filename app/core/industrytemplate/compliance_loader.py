"""Sektörel uyumluluk kuralı yükleyici.

Sektöre özel uyumluluk kuralları yükleme,
kontrol, güncelleme.
"""

import logging
from typing import Any

from app.models.industrytemplate_models import (
    ComplianceRuleDef,
    ComplianceLevel,
)

logger = logging.getLogger(__name__)

_MAX_RULES = 500


class ComplianceLoader:
    """Sektörel uyumluluk kuralı yükleyici.

    Sektöre özel uyumluluk kurallarını
    yükler, kontrol eder, günceller.

    Attributes:
        _rules: Yüklenen kurallar.
        _by_industry: Sektöre göre indeks.
    """

    def __init__(self) -> None:
        """ComplianceLoader başlatır."""
        self._rules: dict[str, ComplianceRuleDef] = {}
        self._by_industry: dict[str, list[str]] = {}
        self._total_loaded: int = 0

        logger.info("ComplianceLoader baslatildi")

    def load(
        self,
        industry: str,
        rule_defs: list[dict],
    ) -> list[ComplianceRuleDef]:
        """Sektöre özel kuralları yükle.

        Args:
            industry: Sektör.
            rule_defs: Kural tanımları.

        Returns:
            Yüklenen kurallar.
        """
        rules: list[ComplianceRuleDef] = []

        for rd in rule_defs:
            if len(self._rules) >= _MAX_RULES:
                break

            rule = ComplianceRuleDef(
                name=rd.get("name", ""),
                description=rd.get("description", ""),
                level=rd.get("level", "recommended"),
                category=rd.get("category", ""),
                check_function=rd.get("check_function", ""),
                remediation=rd.get("remediation", ""),
                jurisdictions=rd.get("jurisdictions", []),
            )
            self._rules[rule.rule_id] = rule
            rules.append(rule)

            if industry not in self._by_industry:
                self._by_industry[industry] = []
            self._by_industry[industry].append(rule.rule_id)

        self._total_loaded += len(rules)
        logger.info(
            "Uyumluluk kurallari yuklendi: %s (%d kural)",
            industry,
            len(rules),
        )
        return rules

    def check_compliance(
        self,
        industry: str,
        config: dict,
    ) -> dict[str, Any]:
        """Uyumluluk kontrolü yap.

        Args:
            industry: Sektör.
            config: Kontrol edilecek yapılandırma.

        Returns:
            Kontrol sonucu.
        """
        rule_ids = self._by_industry.get(industry, [])
        results: list[dict] = []
        required_met = 0
        required_total = 0

        for rid in rule_ids:
            rule = self._rules.get(rid)
            if not rule:
                continue

            level = rule.level.value if isinstance(rule.level, ComplianceLevel) else str(rule.level)
            is_required = level == "required"

            if is_required:
                required_total += 1

            passed = True
            if rule.check_function:
                passed = config.get(rule.check_function, False)

            if is_required and passed:
                required_met += 1

            results.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "level": level,
                "passed": passed,
                "remediation": rule.remediation if not passed else "",
            })

        compliant = required_met == required_total

        return {
            "compliant": compliant,
            "required_met": required_met,
            "required_total": required_total,
            "results": results,
            "industry": industry,
        }

    def get_rules(self, industry: str) -> list[ComplianceRuleDef]:
        """Sektör kurallarını getir.

        Args:
            industry: Sektör.

        Returns:
            Kural listesi.
        """
        rule_ids = self._by_industry.get(industry, [])
        return [
            self._rules[rid]
            for rid in rule_ids
            if rid in self._rules
        ]

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_rules": len(self._rules),
            "total_loaded": self._total_loaded,
            "industries": list(self._by_industry.keys()),
        }
