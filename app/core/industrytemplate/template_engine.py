"""Sektörel agent şablon motoru.

Şablondan agent oluşturma, özelleştirme,
şablon yönetimi, dağıtım.
"""

import logging
import time
from typing import Any

from app.models.industrytemplate_models import (
    IndustryTemplateDef,
    IndustryType,
    TemplateStatus,
    TemplateDeployment,
    TemplateCustomization,
    DeploymentStatus,
)
from app.core.industrytemplate.templates.ecommerce import ECOMMERCE_TEMPLATE
from app.core.industrytemplate.templates.medical_tourism import MEDICAL_TOURISM_TEMPLATE
from app.core.industrytemplate.templates.real_estate import REAL_ESTATE_TEMPLATE
from app.core.industrytemplate.templates.digital_agency import DIGITAL_AGENCY_TEMPLATE

logger = logging.getLogger(__name__)

_BUILTIN_TEMPLATES = {
    "ecommerce": ECOMMERCE_TEMPLATE,
    "medical_tourism": MEDICAL_TOURISM_TEMPLATE,
    "real_estate": REAL_ESTATE_TEMPLATE,
    "digital_agency": DIGITAL_AGENCY_TEMPLATE,
}

_MAX_DEPLOYMENTS = 100


class IndustryTemplateEngine:
    """Sektörel agent şablon motoru.

    Şablonlardan agent oluşturur,
    özelleştirme ve dağıtım yönetir.

    Attributes:
        _deployments: Dağıtım kayıtları.
        _customizations: Özelleştirme kayıtları.
    """

    def __init__(self) -> None:
        """IndustryTemplateEngine başlatır."""
        self._deployments: dict[str, TemplateDeployment] = {}
        self._customizations: dict[str, TemplateCustomization] = {}
        self._total_created: int = 0

        logger.info("IndustryTemplateEngine baslatildi")

    def create_agent(
        self,
        template_name: str,
        config_overrides: dict | None = None,
    ) -> TemplateDeployment | None:
        """Şablondan agent oluştur.

        Args:
            template_name: Şablon adı (ecommerce, medical_tourism vb.).
            config_overrides: Özelleştirme yapılandırması.

        Returns:
            Dağıtım kaydı veya None.
        """
        if template_name not in _BUILTIN_TEMPLATES:
            logger.warning("Bilinmeyen sablon: %s", template_name)
            return None

        if len(self._deployments) >= _MAX_DEPLOYMENTS:
            logger.warning("Max dagitim limiti: %d", _MAX_DEPLOYMENTS)
            return None

        template_data = _BUILTIN_TEMPLATES[template_name]

        active_skills = [
            s["name"]
            for s in template_data.get("skills", [])
            if s.get("required", True) or s.get("enabled", True)
        ]

        active_workflows = [
            w["name"]
            for w in template_data.get("workflows", [])
        ]

        industry_val = template_data.get("industry", "custom")
        try:
            industry_enum = IndustryType(industry_val)
        except ValueError:
            industry_enum = IndustryType.CUSTOM

        deployment = TemplateDeployment(
            template_id=template_name,
            template_name=template_data.get("name", template_name),
            industry=industry_enum,
            status=DeploymentStatus.ACTIVE,
            config_overrides=config_overrides or {},
            active_skills=active_skills,
            active_workflows=active_workflows,
            completed_at=time.time(),
        )

        self._deployments[deployment.deployment_id] = deployment
        self._total_created += 1

        logger.info(
            "Agent olusturuldu: %s (%s, %d beceri, %d is akisi)",
            deployment.deployment_id,
            template_name,
            len(active_skills),
            len(active_workflows),
        )
        return deployment

    def list_templates(self) -> list[dict[str, Any]]:
        """Mevcut şablonları listele.

        Returns:
            Şablon özet listesi.
        """
        results = []
        for key, data in _BUILTIN_TEMPLATES.items():
            results.append({
                "key": key,
                "name": data.get("name", key),
                "industry": data.get("industry", "custom"),
                "description": data.get("description", ""),
                "skills_count": len(data.get("skills", [])),
                "workflows_count": len(data.get("workflows", [])),
                "supported_languages": data.get("supported_languages", []),
                "tags": data.get("tags", []),
            })
        return results

    def get_template_info(self, template_name: str) -> dict[str, Any] | None:
        """Şablon detayını getir.

        Args:
            template_name: Şablon adı.

        Returns:
            Şablon detayı veya None.
        """
        data = _BUILTIN_TEMPLATES.get(template_name)
        if not data:
            return None
        return dict(data)

    def customize_template(
        self,
        template_name: str,
        overrides: dict,
    ) -> TemplateCustomization | None:
        """Şablonu özelleştir.

        Args:
            template_name: Şablon adı.
            overrides: Özelleştirmeler.

        Returns:
            Özelleştirme kaydı veya None.
        """
        if template_name not in _BUILTIN_TEMPLATES:
            logger.warning("Bilinmeyen sablon: %s", template_name)
            return None

        customization = TemplateCustomization(
            template_id=template_name,
            skill_overrides=overrides.get("skills", {}),
            workflow_overrides=overrides.get("workflows", {}),
            language_config=overrides.get("languages", {}),
        )

        self._customizations[customization.customization_id] = customization
        logger.info("Sablon ozellestirme: %s", template_name)
        return customization

    def get_deployment(self, deployment_id: str) -> TemplateDeployment | None:
        """Dağıtım kaydı getir.

        Args:
            deployment_id: Dağıtım ID.

        Returns:
            Dağıtım kaydı veya None.
        """
        return self._deployments.get(deployment_id)

    def list_deployments(self) -> list[TemplateDeployment]:
        """Tüm dağıtımları listele.

        Returns:
            Dağıtım listesi.
        """
        return list(self._deployments.values())

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        by_template: dict[str, int] = {}
        for dep in self._deployments.values():
            by_template[dep.template_id] = by_template.get(dep.template_id, 0) + 1

        return {
            "available_templates": len(_BUILTIN_TEMPLATES),
            "total_deployments": len(self._deployments),
            "total_created": self._total_created,
            "total_customizations": len(self._customizations),
            "by_template": by_template,
        }
