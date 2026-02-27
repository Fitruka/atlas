"""Sektörel şablon doğrulayıcı.

Şablon tanımı doğrulama, beceri kontrolü,
iş akışı doğrulama, CRM alan kontrolü,
uyumluluk kuralı doğrulama.
"""

import logging
from typing import Any

from app.models.industrytemplate_models import (
    IndustryTemplateDef,
    IndustryType,
    WorkflowStepType,
    CRMFieldType,
    ComplianceLevel,
)

logger = logging.getLogger(__name__)

_MIN_SKILLS = 1
_MAX_SKILLS = 50
_MAX_WORKFLOWS = 20
_MAX_CRM_FIELDS = 100
_MAX_COMPLIANCE_RULES = 50
_VALID_STEP_TYPES = {e.value for e in WorkflowStepType}
_VALID_FIELD_TYPES = {e.value for e in CRMFieldType}


class TemplateValidator:
    """Sektörel şablon doğrulayıcı.

    Şablon tanımlarını doğrular,
    tutarlılık ve tamlık kontrolü yapar.

    Attributes:
        _validations_run: Toplam doğrulama sayısı.
        _validations_passed: Başarılı doğrulama sayısı.
    """

    def __init__(self) -> None:
        """TemplateValidator başlatır."""
        self._validations_run: int = 0
        self._validations_passed: int = 0
        self._validations_failed: int = 0

        logger.info("TemplateValidator baslatildi")

    def validate(
        self,
        template: IndustryTemplateDef,
    ) -> dict[str, Any]:
        """Şablonu tam doğrula.

        Args:
            template: Doğrulanacak şablon.

        Returns:
            Doğrulama sonucu.
        """
        self._validations_run += 1
        errors: list[str] = []
        warnings: list[str] = []

        # Temel alanlar
        if not template.name:
            errors.append("Sablon adi bos")
        if not template.description:
            warnings.append("Sablon aciklamasi bos")

        # Beceri doğrulama
        skill_result = self.check_skills(
            [s.model_dump() if hasattr(s, 'model_dump') else s for s in template.skills]
            if template.skills else []
        )
        errors.extend(skill_result.get("errors", []))
        warnings.extend(skill_result.get("warnings", []))

        # İş akışı doğrulama
        skill_names = set()
        for s in template.skills:
            name = s.name if hasattr(s, 'name') else s.get("name", "")
            if name:
                skill_names.add(name)

        wf_result = self.check_workflows(
            [w.model_dump() if hasattr(w, 'model_dump') else w for w in template.workflows]
            if template.workflows else [],
            skill_names,
        )
        errors.extend(wf_result.get("errors", []))
        warnings.extend(wf_result.get("warnings", []))

        # CRM alan doğrulama
        crm_result = self.check_crm_fields(
            [f.model_dump() if hasattr(f, 'model_dump') else f for f in template.crm_fields]
            if template.crm_fields else []
        )
        errors.extend(crm_result.get("errors", []))
        warnings.extend(crm_result.get("warnings", []))

        # Uyumluluk doğrulama
        comp_result = self.check_compliance(
            [r.model_dump() if hasattr(r, 'model_dump') else r for r in template.compliance_rules]
            if template.compliance_rules else []
        )
        errors.extend(comp_result.get("errors", []))
        warnings.extend(comp_result.get("warnings", []))

        valid = len(errors) == 0
        if valid:
            self._validations_passed += 1
        else:
            self._validations_failed += 1

        logger.info(
            "Sablon dogrulama: %s - %s (%d hata, %d uyari)",
            template.name,
            "GECTI" if valid else "BASARISIZ",
            len(errors),
            len(warnings),
        )

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "template_name": template.name,
        }

    def check_skills(
        self,
        skills: list[dict],
    ) -> dict[str, Any]:
        """Beceri listesini doğrula.

        Args:
            skills: Beceri tanımları.

        Returns:
            Doğrulama sonucu.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(skills) < _MIN_SKILLS:
            errors.append(f"En az {_MIN_SKILLS} beceri gerekli")
        if len(skills) > _MAX_SKILLS:
            errors.append(f"En fazla {_MAX_SKILLS} beceri olabilir")

        names = set()
        for skill in skills:
            name = skill.get("name", "")
            if not name:
                errors.append("Beceri adi bos")
                continue
            if name in names:
                errors.append(f"Tekrarlanan beceri adi: {name}")
            names.add(name)

            if not skill.get("description"):
                warnings.append(f"Beceri aciklamasi bos: {name}")
            if not skill.get("category"):
                warnings.append(f"Beceri kategorisi bos: {name}")

            # Bağımlılık kontrolü
            for dep in skill.get("dependencies", []):
                if dep not in names and dep not in [s.get("name", "") for s in skills]:
                    errors.append(f"Bilinmeyen bagimlilk: {name} -> {dep}")

        return {"errors": errors, "warnings": warnings}

    def check_workflows(
        self,
        workflows: list[dict],
        skill_names: set[str] | None = None,
    ) -> dict[str, Any]:
        """İş akışı listesini doğrula.

        Args:
            workflows: İş akışı tanımları.
            skill_names: Geçerli beceri isimleri.

        Returns:
            Doğrulama sonucu.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(workflows) > _MAX_WORKFLOWS:
            errors.append(f"En fazla {_MAX_WORKFLOWS} is akisi olabilir")

        wf_names = set()
        for wf in workflows:
            name = wf.get("name", "")
            if not name:
                errors.append("Is akisi adi bos")
                continue
            if name in wf_names:
                errors.append(f"Tekrarlanan is akisi: {name}")
            wf_names.add(name)

            steps = wf.get("steps", [])
            if not steps:
                warnings.append(f"Is akisi adimi yok: {name}")

            for step in steps:
                step_type = step.get("step_type", "")
                if step_type and step_type not in _VALID_STEP_TYPES:
                    errors.append(f"Gecersiz adim tipi: {step_type} ({name})")

                skill_ref = step.get("skill_ref", "")
                if skill_ref and skill_names and skill_ref not in skill_names:
                    warnings.append(f"Bilinmeyen beceri referansi: {skill_ref} ({name})")

        return {"errors": errors, "warnings": warnings}

    def check_crm_fields(
        self,
        fields: list[dict],
    ) -> dict[str, Any]:
        """CRM alan tanımlarını doğrula.

        Args:
            fields: CRM alan tanımları.

        Returns:
            Doğrulama sonucu.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(fields) > _MAX_CRM_FIELDS:
            errors.append(f"En fazla {_MAX_CRM_FIELDS} CRM alani olabilir")

        field_names = set()
        for field in fields:
            name = field.get("name", "")
            if not name:
                errors.append("CRM alan adi bos")
                continue
            if name in field_names:
                errors.append(f"Tekrarlanan CRM alani: {name}")
            field_names.add(name)

            field_type = field.get("field_type", "")
            if field_type and field_type not in _VALID_FIELD_TYPES:
                errors.append(f"Gecersiz alan tipi: {field_type} ({name})")

            if field_type in ("select", "multi_select"):
                if not field.get("options"):
                    warnings.append(f"Select alani icin secenekler bos: {name}")

        return {"errors": errors, "warnings": warnings}

    def check_compliance(
        self,
        rules: list[dict],
    ) -> dict[str, Any]:
        """Uyumluluk kurallarını doğrula.

        Args:
            rules: Uyumluluk kuralları.

        Returns:
            Doğrulama sonucu.
        """
        errors: list[str] = []
        warnings: list[str] = []

        if len(rules) > _MAX_COMPLIANCE_RULES:
            errors.append(f"En fazla {_MAX_COMPLIANCE_RULES} uyumluluk kurali olabilir")

        rule_names = set()
        for rule in rules:
            name = rule.get("name", "")
            if not name:
                errors.append("Uyumluluk kural adi bos")
                continue
            if name in rule_names:
                errors.append(f"Tekrarlanan kural: {name}")
            rule_names.add(name)

            if not rule.get("jurisdictions"):
                warnings.append(f"Yetki alani belirtilmemis: {name}")

        return {"errors": errors, "warnings": warnings}

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        return {
            "validations_run": self._validations_run,
            "validations_passed": self._validations_passed,
            "validations_failed": self._validations_failed,
        }
