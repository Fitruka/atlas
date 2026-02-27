"""Sektörel şablon kayıt defteri.

Şablon kayıt, kaldırma, arama, listeleme,
sürüm yönetimi, kategori filtreleme.
"""

import logging
import time
from typing import Any

from app.models.industrytemplate_models import (
    IndustryTemplateDef,
    IndustryType,
    TemplateStatus,
)

logger = logging.getLogger(__name__)

_MAX_TEMPLATES = 100
_MAX_TAGS = 50


class TemplateRegistry:
    """Sektörel şablon kayıt defteri.

    Şablon CRUD, arama, filtreleme,
    sürüm yönetimi.

    Attributes:
        _templates: Kayıtlı şablonlar.
        _by_industry: Sektöre göre indeks.
    """

    def __init__(self) -> None:
        """TemplateRegistry başlatır."""
        self._templates: dict[str, IndustryTemplateDef] = {}
        self._by_industry: dict[str, list[str]] = {}
        self._total_registered: int = 0
        self._total_removed: int = 0

        logger.info("TemplateRegistry baslatildi")

    # ---- Kayıt İşlemleri ----

    def register(
        self,
        template: IndustryTemplateDef,
    ) -> bool:
        """Şablon kaydet.

        Args:
            template: Şablon tanımı.

        Returns:
            Başarılı ise True.
        """
        if not template.template_id:
            logger.warning("Bos template_id")
            return False

        if len(self._templates) >= _MAX_TEMPLATES:
            logger.warning("Max sablon limiti asildi: %d", _MAX_TEMPLATES)
            return False

        self._templates[template.template_id] = template

        industry = template.industry.value if isinstance(template.industry, IndustryType) else str(template.industry)
        if industry not in self._by_industry:
            self._by_industry[industry] = []
        if template.template_id not in self._by_industry[industry]:
            self._by_industry[industry].append(template.template_id)

        self._total_registered += 1
        logger.info("Sablon kaydedildi: %s (%s)", template.name, template.template_id)
        return True

    def unregister(self, template_id: str) -> bool:
        """Şablon kaldır.

        Args:
            template_id: Şablon ID.

        Returns:
            Başarılı ise True.
        """
        if template_id not in self._templates:
            logger.warning("Sablon bulunamadi: %s", template_id)
            return False

        template = self._templates.pop(template_id)
        industry = template.industry.value if isinstance(template.industry, IndustryType) else str(template.industry)
        if industry in self._by_industry:
            self._by_industry[industry] = [
                tid for tid in self._by_industry[industry]
                if tid != template_id
            ]

        self._total_removed += 1
        logger.info("Sablon kaldirildi: %s", template_id)
        return True

    # ---- Sorgulama İşlemleri ----

    def get(self, template_id: str) -> IndustryTemplateDef | None:
        """Şablon getir.

        Args:
            template_id: Şablon ID.

        Returns:
            Şablon veya None.
        """
        return self._templates.get(template_id)

    def get_by_name(self, name: str) -> IndustryTemplateDef | None:
        """İsme göre şablon getir.

        Args:
            name: Şablon adı.

        Returns:
            Şablon veya None.
        """
        for template in self._templates.values():
            if template.name == name:
                return template
        return None

    def get_by_industry(
        self,
        industry: str,
    ) -> list[IndustryTemplateDef]:
        """Sektöre göre şablonları getir.

        Args:
            industry: Sektör tipi.

        Returns:
            Şablon listesi.
        """
        template_ids = self._by_industry.get(industry, [])
        return [
            self._templates[tid]
            for tid in template_ids
            if tid in self._templates
        ]

    def search(
        self,
        query: str = "",
        industry: str = "",
        tags: list[str] | None = None,
        status: str = "",
    ) -> list[IndustryTemplateDef]:
        """Şablon ara.

        Args:
            query: Arama metni.
            industry: Sektör filtresi.
            tags: Etiket filtresi.
            status: Durum filtresi.

        Returns:
            Eşleşen şablonlar.
        """
        results: list[IndustryTemplateDef] = []
        query_lower = query.lower()

        for template in self._templates.values():
            if industry:
                t_industry = template.industry.value if isinstance(template.industry, IndustryType) else str(template.industry)
                if t_industry != industry:
                    continue

            if status:
                t_status = template.status.value if isinstance(template.status, TemplateStatus) else str(template.status)
                if t_status != status:
                    continue

            if tags:
                if not any(tag in template.tags for tag in tags):
                    continue

            if query_lower:
                name_match = query_lower in template.name.lower()
                desc_match = query_lower in template.description.lower()
                tag_match = any(query_lower in t.lower() for t in template.tags)
                if not (name_match or desc_match or tag_match):
                    continue

            results.append(template)

        return results

    def list_all(self) -> list[IndustryTemplateDef]:
        """Tüm şablonları listele.

        Returns:
            Tüm şablonlar.
        """
        return list(self._templates.values())

    def list_industries(self) -> list[str]:
        """Mevcut sektörleri listele.

        Returns:
            Sektör listesi.
        """
        return list(self._by_industry.keys())

    # ---- İstatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür.

        Returns:
            İstatistik sözlüğü.
        """
        by_industry: dict[str, int] = {}
        for industry, ids in self._by_industry.items():
            by_industry[industry] = len(ids)

        return {
            "total_templates": len(self._templates),
            "total_registered": self._total_registered,
            "total_removed": self._total_removed,
            "by_industry": by_industry,
            "industries": list(self._by_industry.keys()),
        }
