"""
ATLAS Skills Sistemi.

250 beceri, 11 kategori, merkezi kayit ve orkestrasyon.
"""

from app.core.skills.base_skill import BaseSkill
from app.core.skills.skill_registry import SkillRegistry

__all__ = [
    "BaseSkill",
    "SkillRegistry",
    "register_all_skills",
    "get_default_registry",
]

_default_registry: SkillRegistry | None = None


def _import_all_skill_lists() -> list[type[BaseSkill]]:
    """Tum kategori modullerinden beceri siniflarini topla."""
    all_skills: list[type[BaseSkill]] = []

    from app.core.skills.basic_tools import ALL_BASIC_SKILLS
    all_skills.extend(ALL_BASIC_SKILLS)

    from app.core.skills.datetime_tools import ALL_DATETIME_SKILLS
    all_skills.extend(ALL_DATETIME_SKILLS)

    from app.core.skills.document_tools import ALL_DOCUMENT_SKILLS
    all_skills.extend(ALL_DOCUMENT_SKILLS)

    from app.core.skills.media_tools import ALL_MEDIA_SKILLS
    all_skills.extend(ALL_MEDIA_SKILLS)

    try:
        from app.core.skills.web_tools import ALL_WEB_SKILLS
        all_skills.extend(ALL_WEB_SKILLS)
    except ImportError:
        pass

    try:
        from app.core.skills.developer_tools import ALL_DEVELOPER_SKILLS
        all_skills.extend(ALL_DEVELOPER_SKILLS)
    except ImportError:
        pass

    try:
        from app.core.skills.seo_tools import ALL_SEO_SKILLS
        all_skills.extend(ALL_SEO_SKILLS)
    except ImportError:
        pass

    from app.core.skills.finance_tools import ALL_FINANCE_SKILLS
    all_skills.extend(ALL_FINANCE_SKILLS)

    from app.core.skills.communication_tools import ALL_COMMUNICATION_SKILLS
    all_skills.extend(ALL_COMMUNICATION_SKILLS)

    from app.core.skills.productivity_tools import ALL_PRODUCTIVITY_SKILLS
    all_skills.extend(ALL_PRODUCTIVITY_SKILLS)

    from app.core.skills.data_science_tools import ALL_DATA_SCIENCE_SKILLS
    all_skills.extend(ALL_DATA_SCIENCE_SKILLS)

    return all_skills


def register_all_skills(registry: SkillRegistry | None = None) -> SkillRegistry:
    """Tum becerileri kayit defterine kaydet."""
    if registry is None:
        registry = SkillRegistry()

    skills = _import_all_skill_lists()
    for skill_cls in skills:
        try:
            registry.register(skill_cls())
        except Exception:
            pass  # Duplikat veya hata durumunda atla

    return registry


def get_default_registry() -> SkillRegistry:
    """Varsayilan singleton registry'yi dondur."""
    global _default_registry
    if _default_registry is None:
        _default_registry = register_all_skills()
    return _default_registry
