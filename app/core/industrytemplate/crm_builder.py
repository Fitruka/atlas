"""Sektörel CRM yapı oluşturucu.

CRM alan tanımları, segment oluşturma,
şema dışa aktarma.
"""

import logging
import time
from typing import Any

from app.models.industrytemplate_models import (
    CRMFieldDef,
    CRMSegmentDef,
    CRMFieldType,
)

logger = logging.getLogger(__name__)

_MAX_FIELDS = 200
_MAX_SEGMENTS = 50


class CRMBuilder:
    """Sektörel CRM yapı oluşturucu.

    CRM alanlarını ve segmentleri
    şablon tanımlarından oluşturur.

    Attributes:
        _schemas: Oluşturulan CRM şemaları.
    """

    def __init__(self) -> None:
        """CRMBuilder başlatır."""
        self._schemas: dict[str, dict[str, Any]] = {}
        self._total_built: int = 0

        logger.info("CRMBuilder baslatildi")

    def build(
        self,
        template_id: str,
        field_defs: list[dict],
        segment_defs: list[dict] | None = None,
    ) -> dict[str, Any]:
        """CRM yapısı oluştur.

        Args:
            template_id: Şablon ID.
            field_defs: Alan tanımları.
            segment_defs: Segment tanımları.

        Returns:
            CRM şema sözlüğü.
        """
        fields: list[CRMFieldDef] = []
        for fd in field_defs:
            if len(fields) >= _MAX_FIELDS:
                break
            field = CRMFieldDef(
                name=fd.get("name", ""),
                label=fd.get("label", ""),
                field_type=fd.get("field_type", "text"),
                required=fd.get("required", False),
                default_value=fd.get("default_value", ""),
                options=fd.get("options", []),
                searchable=fd.get("searchable", True),
                sortable=fd.get("sortable", True),
                category=fd.get("category", ""),
            )
            fields.append(field)

        segments: list[CRMSegmentDef] = []
        for sd in (segment_defs or []):
            if len(segments) >= _MAX_SEGMENTS:
                break
            segment = CRMSegmentDef(
                name=sd.get("name", ""),
                description=sd.get("description", ""),
                criteria=sd.get("criteria", {}),
                auto_assign=sd.get("auto_assign", False),
            )
            segments.append(segment)

        schema = {
            "template_id": template_id,
            "fields": [f.model_dump() for f in fields],
            "segments": [s.model_dump() for s in segments],
            "total_fields": len(fields),
            "total_segments": len(segments),
            "categories": list(set(f.category for f in fields if f.category)),
        }

        self._schemas[template_id] = schema
        self._total_built += 1

        logger.info(
            "CRM yapisi olusturuldu: %s (%d alan, %d segment)",
            template_id,
            len(fields),
            len(segments),
        )
        return schema

    def add_field(
        self,
        template_id: str,
        field_def: dict,
    ) -> bool:
        """CRM alanı ekle.

        Args:
            template_id: Şablon ID.
            field_def: Alan tanımı.

        Returns:
            Başarılı ise True.
        """
        schema = self._schemas.get(template_id)
        if not schema:
            logger.warning("Sema bulunamadi: %s", template_id)
            return False

        if schema["total_fields"] >= _MAX_FIELDS:
            logger.warning("Max alan limiti")
            return False

        field = CRMFieldDef(
            name=field_def.get("name", ""),
            label=field_def.get("label", ""),
            field_type=field_def.get("field_type", "text"),
            category=field_def.get("category", ""),
        )

        schema["fields"].append(field.model_dump())
        schema["total_fields"] += 1
        return True

    def get_schema(self, template_id: str) -> dict[str, Any] | None:
        """CRM şeması getir.

        Args:
            template_id: Şablon ID.

        Returns:
            Şema veya None.
        """
        return self._schemas.get(template_id)

    def export_schema(
        self,
        template_id: str,
        fmt: str = "dict",
    ) -> Any:
        """CRM şemasını dışa aktar.

        Args:
            template_id: Şablon ID.
            fmt: Format (dict, json, list).

        Returns:
            Dışa aktarılan şema.
        """
        schema = self._schemas.get(template_id)
        if not schema:
            return None

        if fmt == "list":
            return schema.get("fields", [])
        return schema

    def get_stats(self) -> dict[str, Any]:
        """İstatistikleri döndürür."""
        return {
            "total_schemas": len(self._schemas),
            "total_built": self._total_built,
        }
