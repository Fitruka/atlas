"""Beceri kayit defteri.

Tum becerilerin kaydedilmesi,
kesfedilmesi ve yonetilmesi.
"""

import logging
import os
import re
import time
from typing import Any
from uuid import uuid4

from app.core.skills.base_skill import (
    BaseSkill,
)
from app.models.skills_models import (
    SkillDefinition,
    SkillExecution,
    SkillRegistryEntry,
)

logger = logging.getLogger(__name__)

# Kod guvenlik tarama desenleri
_UNSAFE_PATTERNS: list[tuple[str, str]] = [
    (r"eval\s*\(", "eval() kullanimi"),
    (r"exec\s*\(", "exec() kullanimi"),
    (r"os\.system\s*\(", "os.system() kullanimi"),
    (r"subprocess\.call\s*\(", "subprocess.call()"),
    (r"__import__\s*\(", "__import__() kullanimi"),
    (r"rm\s+-rf\s+/", "rm -rf / komutu"),
    (r"sudo\s+", "sudo kullanimi"),
    (r"chmod\s+777", "chmod 777"),
    (r"curl\s+.*\|\s*sh", "curl pipe to sh"),
    (r"wget\s+.*\|\s*sh", "wget pipe to sh"),
]

_MAX_HISTORY = 10000


class SkillRegistry:
    """Beceri kayit defteri.

    Tum becerilerin kaydedilmesi,
    kesfedilmesi ve yonetilmesi.

    Attributes:
        _skills: Kayitli beceriler.
    """

    def __init__(self) -> None:
        """SkillRegistry baslatir."""
        self._skills: dict[
            str, BaseSkill
        ] = {}
        self._by_name: dict[
            str, BaseSkill
        ] = {}
        self._by_category: dict[
            str, list[str]
        ] = {}
        self._disabled: set[str] = set()
        self._total_ops: int = 0
        self._history: list[
            dict[str, Any]
        ] = []

        logger.info(
            "SkillRegistry baslatildi",
        )

    # ---- Kayit ----

    def register(
        self,
        skill: BaseSkill,
    ) -> bool:
        """Beceri kaydeder.

        Args:
            skill: Beceri ornegi.

        Returns:
            Basarili ise True.
        """
        sid = skill.SKILL_ID
        if not sid or not skill.NAME:
            return False

        self._skills[sid] = skill
        self._by_name[skill.NAME] = skill

        cat = skill.CATEGORY
        if cat not in self._by_category:
            self._by_category[cat] = []
        if sid not in self._by_category[cat]:
            self._by_category[cat].append(sid)

        self._total_ops += 1
        self._record_history(
            "register",
            sid,
            f"name={skill.NAME} "
            f"cat={cat}",
        )
        return True

    def register_many(
        self,
        skills: list[BaseSkill],
    ) -> int:
        """Toplu beceri kaydeder.

        Args:
            skills: Beceri listesi.

        Returns:
            Kaydedilen sayi.
        """
        count = 0
        for skill in skills:
            if self.register(skill):
                count += 1
        return count

    def unregister(
        self,
        skill_id: str,
    ) -> bool:
        """Beceri kaydini siler.

        Args:
            skill_id: Beceri ID.

        Returns:
            Basarili ise True.
        """
        skill = self._skills.pop(
            skill_id, None,
        )
        if not skill:
            return False

        self._by_name.pop(skill.NAME, None)
        self._disabled.discard(skill_id)

        cat = skill.CATEGORY
        if cat in self._by_category:
            ids = self._by_category[cat]
            if skill_id in ids:
                ids.remove(skill_id)

        self._total_ops += 1
        self._record_history(
            "unregister",
            skill_id,
            f"name={skill.NAME}",
        )
        return True

    def count(self) -> int:
        """Kayitli beceri sayisini dondurur."""
        return len(self._skills)

    def remove(
        self,
        skill_id: str,
    ) -> bool:
        """Beceri kaydini siler (unregister alias)."""
        return self.unregister(skill_id)

    def get_skill_info(
        self,
        skill_id: str,
    ) -> dict[str, Any] | None:
        """Beceri bilgilerini dict olarak dondurur."""
        skill = self._skills.get(skill_id)
        if not skill:
            return None
        defn = skill.get_definition()
        return {
            "skill_id": defn.skill_id,
            "name": defn.name,
            "description": defn.description,
            "category": defn.category,
            "risk_level": defn.risk_level,
            "parameters": defn.parameters,
            "version": defn.version,
        }

    # ---- Erisim ----

    def get(
        self,
        skill_id: str,
    ) -> BaseSkill | None:
        """Beceri dondurur.

        Args:
            skill_id: Beceri ID.

        Returns:
            Beceri veya None.
        """
        return self._skills.get(skill_id)

    def get_by_name(
        self,
        name: str,
    ) -> BaseSkill | None:
        """Isimle beceri dondurur.

        Args:
            name: Beceri adi.

        Returns:
            Beceri veya None.
        """
        return self._by_name.get(name)

    def get_by_category(
        self,
        category: str,
    ) -> list[BaseSkill]:
        """Kategoriye gore becerileri dondurur.

        Args:
            category: Kategori adi.

        Returns:
            Beceri listesi.
        """
        ids = self._by_category.get(
            category, [],
        )
        result: list[BaseSkill] = []
        for sid in ids:
            skill = self._skills.get(sid)
            if skill:
                result.append(skill)
        return result

    # ---- Durum ----

    def enable(
        self,
        skill_id: str,
    ) -> bool:
        """Beceriyi etkinlestirir.

        Args:
            skill_id: Beceri ID.

        Returns:
            Basarili ise True.
        """
        if skill_id not in self._skills:
            return False
        self._disabled.discard(skill_id)
        self._total_ops += 1
        return True

    def disable(
        self,
        skill_id: str,
    ) -> bool:
        """Beceriyi devre disi birakir.

        Args:
            skill_id: Beceri ID.

        Returns:
            Basarili ise True.
        """
        if skill_id not in self._skills:
            return False
        self._disabled.add(skill_id)
        self._total_ops += 1
        return True

    def is_enabled(
        self,
        skill_id: str,
    ) -> bool:
        """Beceri etkin mi kontrol eder.

        Args:
            skill_id: Beceri ID.

        Returns:
            Etkin ise True.
        """
        return (
            skill_id in self._skills
            and skill_id not in self._disabled
        )

    # ---- Yurutme ----

    def execute(
        self,
        skill_id: str,
        **params: Any,
    ) -> SkillExecution | None:
        """Beceriyi yurutur.

        Args:
            skill_id: Beceri ID.
            **params: Parametreler.

        Returns:
            Yurutme sonucu veya None.
        """
        skill = self._skills.get(skill_id)
        if not skill:
            return None
        if skill_id in self._disabled:
            return SkillExecution(
                execution_id=str(uuid4())[:8],
                skill_id=skill_id,
                skill_name=skill.NAME,
                parameters=params,
                success=False,
                error="skill is disabled",
                timestamp=time.time(),
            )

        result = skill.execute(**params)
        self._total_ops += 1
        self._record_history(
            "execute",
            skill_id,
            f"success={result.success}",
        )
        return result

    def execute_by_name(
        self,
        name: str,
        **params: Any,
    ) -> SkillExecution | None:
        """Isimle beceri yurutur.

        Args:
            name: Beceri adi.
            **params: Parametreler.

        Returns:
            Yurutme sonucu veya None.
        """
        skill = self._by_name.get(name)
        if not skill:
            return None
        return self.execute(
            skill.SKILL_ID, **params,
        )

    # ---- Listeleme ----

    def list_all(
        self,
    ) -> list[SkillDefinition]:
        """Tum becerileri listeler.

        Returns:
            Tanim listesi.
        """
        return [
            s.get_definition()
            for s in self._skills.values()
        ]

    def list_categories(
        self,
    ) -> list[dict[str, Any]]:
        """Kategorileri listeler.

        Returns:
            Kategori listesi.
        """
        result = []
        for cat, ids in (
            self._by_category.items()
        ):
            result.append({
                "category": cat,
                "skill_count": len(ids),
                "skill_ids": list(ids),
            })
        return result

    def list_entries(
        self,
    ) -> list[SkillRegistryEntry]:
        """Kayit girdilerini listeler.

        Returns:
            Girdi listesi.
        """
        result = []
        for sid, skill in (
            self._skills.items()
        ):
            stats = skill.get_stats()
            status = (
                "disabled"
                if sid in self._disabled
                else "active"
            )
            result.append(
                SkillRegistryEntry(
                    skill_id=sid,
                    name=skill.NAME,
                    category=skill.CATEGORY,
                    risk_level=(
                        skill.RISK_LEVEL
                    ),
                    status=status,
                    total_executions=(
                        stats["total_executions"]
                    ),
                    success_rate=(
                        stats["success_rate"]
                    ),
                    avg_execution_time=(
                        stats[
                            "avg_execution_time"
                        ]
                    ),
                ),
            )
        return result

    # ---- Arama ----

    def search(
        self,
        query: str,
        category: str = "",
        risk_level: str = "",
        limit: int = 50,
    ) -> list[SkillDefinition]:
        """Beceri arar.

        Args:
            query: Arama sorgusu.
            category: Kategori filtresi.
            risk_level: Risk filtresi.
            limit: Maks sayi.

        Returns:
            Eslesen beceriler.
        """
        q = query.lower()
        result: list[SkillDefinition] = []

        for skill in self._skills.values():
            if category and (
                skill.CATEGORY != category
            ):
                continue
            if risk_level and (
                skill.RISK_LEVEL != risk_level
            ):
                continue

            if (
                q in skill.NAME.lower()
                or q in skill.DESCRIPTION.lower()
                or q in skill.SKILL_ID
            ):
                result.append(
                    skill.get_definition(),
                )
                if len(result) >= limit:
                    break

        return result

    # ---- Gosterim ----

    def format_catalog(
        self,
        category: str = "",
    ) -> str:
        """Katalog formatlar.

        Args:
            category: Kategori filtresi.

        Returns:
            Formatlenmis metin.
        """
        parts: list[str] = []
        parts.append("=== Beceri Katalogu ===")
        parts.append(
            f"Toplam: "
            f"{len(self._skills)} beceri",
        )
        parts.append("")

        cats = (
            {category: self._by_category.get(
                category, [],
            )}
            if category
            else dict(self._by_category)
        )

        for cat, ids in cats.items():
            parts.append(f"[{cat}] ({len(ids)})")
            for sid in ids:
                skill = self._skills.get(sid)
                if skill:
                    status = (
                        "OFF"
                        if sid in self._disabled
                        else "ON"
                    )
                    parts.append(
                        f"  {sid} {skill.NAME} "
                        f"[{status}]",
                    )
            parts.append("")

        return "\n".join(parts)

    # ---- Temizlik ----

    def clear_all(self) -> int:
        """Tum kayitlari temizler.

        Returns:
            Silinen sayi.
        """
        count = len(self._skills)
        self._skills.clear()
        self._by_name.clear()
        self._by_category.clear()
        self._disabled.clear()
        self._total_ops += 1
        return count

    # ---- Dahili ----

    def _record_history(
        self,
        action: str,
        record_id: str,
        detail: str,
    ) -> None:
        """Aksiyonu kaydeder."""
        self._history.append({
            "action": action,
            "record_id": record_id,
            "detail": detail,
            "timestamp": time.time(),
        })
        if len(self._history) > _MAX_HISTORY:
            self._history = (
                self._history[-5000:]
            )

    def get_history(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Gecmisi dondurur."""
        return list(
            reversed(
                self._history[-limit:],
            ),
        )

    # ---- Guvenlik ----

    @staticmethod
    def compact_path(
        path: str,
    ) -> str:
        """Path'i ~ prefiksi ile kisaltir.

        Args:
            path: Dosya yolu.

        Returns:
            Kisaltilmis yol.
        """
        home = os.path.expanduser("~")
        if path.startswith(home):
            return "~" + path[len(home):]
        return path

    @staticmethod
    def is_symlink(path: str) -> bool:
        """Symlink kontrolu.

        Args:
            path: Dosya yolu.

        Returns:
            Symlink ise True.
        """
        return os.path.islink(path)

    @staticmethod
    def reject_symlinks(
        directory: str,
    ) -> list[str]:
        """Symlink dosyalari tespit eder.

        Args:
            directory: Dizin yolu.

        Returns:
            Symlink dosya yolları listesi.
        """
        symlinks: list[str] = []
        if not os.path.isdir(directory):
            return symlinks

        for root, dirs, files in os.walk(
            directory,
        ):
            for name in dirs + files:
                full_path = os.path.join(
                    root, name,
                )
                if os.path.islink(full_path):
                    symlinks.append(full_path)

        return symlinks

    @staticmethod
    def scan_code_safety(
        code: str,
    ) -> list[dict[str, str]]:
        """Kod guvenlik taramasi yapar.

        Args:
            code: Taranacak kod metni.

        Returns:
            Bulunan guvenlik sorunlari.
        """
        findings: list[dict[str, str]] = []

        for pattern, description in (
            _UNSAFE_PATTERNS
        ):
            matches = re.findall(
                pattern, code,
            )
            if matches:
                findings.append({
                    "pattern": pattern,
                    "description": description,
                    "count": str(len(matches)),
                })

        return findings

    def register_with_safety_check(
        self,
        skill: BaseSkill,
        source_code: str = "",
        source_path: str = "",
    ) -> tuple[bool, list[dict[str, str]]]:
        """Guvenlik kontrolu ile beceri kaydeder.

        Args:
            skill: Beceri ornegi.
            source_code: Kaynak kodu.
            source_path: Kaynak dosya yolu.

        Returns:
            (kayit_basarili, bulgular) tuple.
        """
        findings: list[dict[str, str]] = []

        # Symlink kontrolu
        if source_path and self.is_symlink(
            source_path,
        ):
            findings.append({
                "pattern": "symlink",
                "description": (
                    "Symlink beceri reddedildi"
                ),
                "count": "1",
            })
            return False, findings

        # Kod guvenlik taramasi
        if source_code:
            code_findings = (
                self.scan_code_safety(
                    source_code,
                )
            )
            findings.extend(code_findings)

        if findings:
            logger.warning(
                "Guvenlik sorunu: %s (%d bulgu)",
                skill.SKILL_ID,
                len(findings),
            )
            return False, findings

        success = self.register(skill)
        return success, findings

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur."""
        total_execs = sum(
            s.get_stats()["total_executions"]
            for s in self._skills.values()
        )
        return {
            "total_skills": len(
                self._skills,
            ),
            "total_categories": len(
                self._by_category,
            ),
            "total_disabled": len(
                self._disabled,
            ),
            "total_executions": total_execs,
            "total_ops": self._total_ops,
        }
