"""Sektörel beceri paketleyici.

Şablon becerilerini paketleme, yapılandırma,
bağımlılık kontrolü, durum takibi.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.industrytemplate_models import (
    TemplateSkillDef,
    SkillBundleEntry,
    SkillStatus,
)

logger = logging.getLogger(__name__)

_MAX_BUNDLES = 200
_MAX_SKILLS_PER_BUNDLE = 50


class SkillBundler:
    """Sektörel beceri paketleyici.

    Şablon becerilerini paketler,
    yapılandırır, bağımlılık çözer.

    Attributes:
        _bundles: Oluşturulan paketler.
    """

    def __init__(self) -> None:
        """SkillBundler başlatır."""
        self._bundles: dict[str, SkillBundleEntry] = {}
        self._total_bundled: int = 0

        logger.info("SkillBundler baslatildi")

    def bundle(
        self,
        template_id: str,
        skill_defs: list[dict],
    ) -> SkillBundleEntry | None:
        """Beceri paketi oluştur.

        Args:
            template_id: Şablon ID.
            skill_defs: Beceri tanımları.

        Returns:
            Paket kaydı veya None.
        """
        if len(self._bundles) >= _MAX_BUNDLES:
            logger.warning("Max paket limiti: %d", _MAX_BUNDLES)
            return None

        if len(skill_defs) > _MAX_SKILLS_PER_BUNDLE:
            logger.warning("Max beceri limiti: %d", _MAX_SKILLS_PER_BUNDLE)
            return None

        skills: list[TemplateSkillDef] = []
        for sd in skill_defs:
            skill = TemplateSkillDef(
                name=sd.get("name", ""),
                description=sd.get("description", ""),
                category=sd.get("category", ""),
                required=sd.get("required", True),
                config=sd.get("config", {}),
                dependencies=sd.get("dependencies", []),
                status=SkillStatus.CONFIGURED,
                enabled=True,
            )
            skills.append(skill)

        ordered = self._resolve_dependencies(skills)

        bundle = SkillBundleEntry(
            template_id=template_id,
            skills=ordered,
            total_skills=len(ordered),
            configured_count=len(ordered),
        )

        self._bundles[bundle.bundle_id] = bundle
        self._total_bundled += 1

        logger.info(
            "Beceri paketi olusturuldu: %s (%d beceri)",
            bundle.bundle_id,
            len(ordered),
        )
        return bundle

    def _resolve_dependencies(
        self,
        skills: list[TemplateSkillDef],
    ) -> list[TemplateSkillDef]:
        """Bağımlılık sırasına göre sırala.

        Args:
            skills: Beceri listesi.

        Returns:
            Sıralı beceri listesi.
        """
        name_map = {s.name: s for s in skills}
        visited: set[str] = set()
        ordered: list[TemplateSkillDef] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            skill = name_map.get(name)
            if not skill:
                return
            for dep in skill.dependencies:
                visit(dep)
            ordered.append(skill)

        for skill in skills:
            visit(skill.name)

        return ordered

    def configure_skill(
        self,
        bundle_id: str,
        skill_name: str,
        config: dict,
    ) -> bool:
        """Paket içindeki beceriyi yapılandır.

        Args:
            bundle_id: Paket ID.
            skill_name: Beceri adı.
            config: Yapılandırma.

        Returns:
            Başarılı ise True.
        """
        bundle = self._bundles.get(bundle_id)
        if not bundle:
            logger.warning("Paket bulunamadi: %s", bundle_id)
            return False

        for skill in bundle.skills:
            if skill.name == skill_name:
                skill.config.update(config)
                logger.info("Beceri yapilandirildi: %s/%s", bundle_id, skill_name)
                return True

        logger.warning("Beceri bulunamadi: %s/%s", bundle_id, skill_name)
        return False

    def activate_bundle(self, bundle_id: str) -> bool:
        """Paketi aktifleştir.

        Args:
            bundle_id: Paket ID.

        Returns:
            Başarılı ise True.
        """
        bundle = self._bundles.get(bundle_id)
        if not bundle:
            return False

        active_count = 0
        for skill in bundle.skills:
            if skill.enabled:
                skill.status = SkillStatus.ACTIVE
                active_count += 1

        bundle.active_count = active_count
        logger.info("Paket aktif: %s (%d beceri)", bundle_id, active_count)
        return True

    def get_bundle(self, bundle_id: str) -> SkillBundleEntry | None:
        """Paket getir.

        Args:
            bundle_id: Paket ID.

        Returns:
            Paket veya None.
        """
        return self._bundles.get(bundle_id)

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_bundles": len(self._bundles),
            "total_bundled": self._total_bundled,
        }
