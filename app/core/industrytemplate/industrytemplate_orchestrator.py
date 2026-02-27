"""ATLAS Industry Agent Template Engine Orkestratörü.

Tam şablon dağıtım pipeline,
Register -> Validate -> Bundle -> Generate -> Build -> Deploy,
entegrasyon, analitik.
"""

import logging
import time
from typing import Any

from app.core.industrytemplate.template_engine import IndustryTemplateEngine
from app.core.industrytemplate.template_registry import TemplateRegistry
from app.core.industrytemplate.template_validator import TemplateValidator
from app.core.industrytemplate.skill_bundler import SkillBundler
from app.core.industrytemplate.workflow_generator import WorkflowGenerator
from app.core.industrytemplate.crm_builder import CRMBuilder
from app.core.industrytemplate.compliance_loader import ComplianceLoader
from app.models.industrytemplate_models import (
    IndustryTemplateDef,
    IndustryType,
    TemplateStatus,
)

logger = logging.getLogger(__name__)


class IndustryTemplateOrchestrator:
    """Industry Agent Template Engine orkestratoru.

    Tum sablon bilesenlerini koordine eder:
    kayit, dogrulama, paketleme, uretim, dagitim.

    Attributes:
        engine: Sablon motoru.
        registry: Sablon kayit defteri.
        validator: Sablon dogrulayici.
        bundler: Beceri paketleyici.
        workflow_gen: Is akisi uretici.
        crm_builder: CRM olusturucu.
        compliance: Uyumluluk yukleyici.
    """

    def __init__(self) -> None:
        """Orkestratoeru baslatir."""
        self.engine = IndustryTemplateEngine()
        self.registry = TemplateRegistry()
        self.validator = TemplateValidator()
        self.bundler = SkillBundler()
        self.workflow_gen = WorkflowGenerator()
        self.crm_builder = CRMBuilder()
        self.compliance = ComplianceLoader()

        self._stats = {
            "pipelines_run": 0,
            "deployments_success": 0,
            "deployments_failed": 0,
        }

        logger.info("IndustryTemplateOrchestrator baslatildi")

    def deploy_template(
        self,
        template_name: str,
        config_overrides: dict | None = None,
    ) -> dict[str, Any]:
        """Sablonu tam pipeline ile dagit.

        Register -> Validate -> Bundle -> Generate -> Build -> Deploy.

        Args:
            template_name: Sablon adi.
            config_overrides: Ozellestirmeler.

        Returns:
            Dagitim sonucu.
        """
        self._stats["pipelines_run"] += 1
        start = time.time()

        # 1. Sablon bilgisi al
        template_info = self.engine.get_template_info(template_name)
        if not template_info:
            self._stats["deployments_failed"] += 1
            return {"success": False, "error": f"Sablon bulunamadi: {template_name}"}

        # 2. Template model olustur ve dogrula
        industry_val = template_info.get("industry", "custom")
        try:
            industry_enum = IndustryType(industry_val)
        except ValueError:
            industry_enum = IndustryType.CUSTOM

        template_def = IndustryTemplateDef(
            name=template_info.get("name", template_name),
            industry=industry_enum,
            description=template_info.get("description", ""),
            status=TemplateStatus.ACTIVE,
            supported_languages=template_info.get("supported_languages", ["tr", "en"]),
            tags=template_info.get("tags", []),
        )

        # Skills
        for sd in template_info.get("skills", []):
            from app.models.industrytemplate_models import TemplateSkillDef
            template_def.skills.append(TemplateSkillDef(
                name=sd.get("name", ""),
                description=sd.get("description", ""),
                category=sd.get("category", ""),
                required=sd.get("required", True),
                config=sd.get("config", {}),
                dependencies=sd.get("dependencies", []),
            ))

        # Dogrulama
        validation = self.validator.validate(template_def)
        if not validation["valid"]:
            self._stats["deployments_failed"] += 1
            return {"success": False, "error": "Dogrulama basarisiz", "details": validation}

        # 3. Kayit
        self.registry.register(template_def)

        # 4. Beceri paketleme
        bundle = self.bundler.bundle(
            template_def.template_id,
            template_info.get("skills", []),
        )
        if bundle:
            self.bundler.activate_bundle(bundle.bundle_id)

        # 5. Is akisi uretimi
        workflows = self.workflow_gen.generate(
            template_def.template_id,
            template_info.get("workflows", []),
        )

        # 6. CRM olusturma
        crm_schema = self.crm_builder.build(
            template_def.template_id,
            template_info.get("crm_fields", []),
            template_info.get("crm_segments", []),
        )

        # 7. Uyumluluk yukleme
        compliance_rules = self.compliance.load(
            industry_val,
            template_info.get("compliance_rules", []),
        )

        # 8. Agent olusturma
        deployment = self.engine.create_agent(template_name, config_overrides)
        if not deployment:
            self._stats["deployments_failed"] += 1
            return {"success": False, "error": "Agent olusturulamadi"}

        elapsed = time.time() - start
        self._stats["deployments_success"] += 1

        logger.info(
            "Sablon dagitildi: %s (%.2fs)",
            template_name,
            elapsed,
        )

        return {
            "success": True,
            "deployment_id": deployment.deployment_id,
            "template_name": template_name,
            "skills_count": bundle.total_skills if bundle else 0,
            "workflows_count": len(workflows),
            "crm_fields_count": crm_schema.get("total_fields", 0),
            "compliance_rules_count": len(compliance_rules),
            "elapsed_seconds": round(elapsed, 3),
        }

    def list_available_templates(self) -> list[dict[str, Any]]:
        """Mevcut sablonlari listele.

        Returns:
            Sablon listesi.
        """
        return self.engine.list_templates()

    def get_stats(self) -> dict[str, Any]:
        """Tum istatistikleri dondurur."""
        return {
            "orchestrator": self._stats,
            "engine": self.engine.get_stats(),
            "registry": self.registry.get_stats(),
            "validator": self.validator.get_stats(),
            "bundler": self.bundler.get_stats(),
            "workflow_gen": self.workflow_gen.get_stats(),
            "crm_builder": self.crm_builder.get_stats(),
            "compliance": self.compliance.get_stats(),
        }
