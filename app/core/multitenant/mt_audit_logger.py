"""ATLAS Multi-Tenant Audit Logger modulu.

ISO 27001 uyumlu kiraciya ozel
denetim gunlugu.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.multitenant_models import (
    ComplianceStandard,
)

logger = logging.getLogger(__name__)

_MAX_LOGS_PER_TENANT = 100000
_DEFAULT_RETENTION_DAYS = 365


class MTAuditLogger:
    """Coklu kiraci denetim gunlugu.

    ISO 27001 uyumlu denetim kayitlari
    olusturur ve yonetir.

    Attributes:
        _logs: Denetim kayitlari.
        _tenant_logs: Kiraci-log eslemeleri.
    """

    def __init__(
        self,
        retention_days: int = (
            _DEFAULT_RETENTION_DAYS
        ),
    ) -> None:
        """Denetim gunlugunu baslatir.

        Args:
            retention_days: Saklama suresi (gun).
        """
        self._logs: dict[
            str, dict[str, Any]
        ] = {}
        self._tenant_logs: dict[
            str, list[str]
        ] = {}
        self._retention_days = retention_days
        self._stats = {
            "logged": 0,
            "exported": 0,
            "queries": 0,
        }

        logger.info(
            "MTAuditLogger baslatildi "
            "(retention=%d gun)",
            retention_days,
        )

    def log(
        self,
        tenant_id: str,
        actor: str,
        action: str,
        resource: str,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> str:
        """Denetim kaydi olusturur.

        Args:
            tenant_id: Kiraci ID.
            actor: Islemi yapan kullanici.
            action: Aksiyon (create, read, vb).
            resource: Kaynak adi.
            details: Ek detaylar.
            ip_address: IP adresi.

        Returns:
            Log ID.
        """
        log_id = str(uuid4())[:8]

        entry = {
            "log_id": log_id,
            "tenant_id": tenant_id,
            "actor": actor,
            "action": action,
            "resource": resource,
            "details": details or {},
            "ip_address": ip_address or "",
            "timestamp": datetime.now(
                timezone.utc,
            ).isoformat(),
            "severity": self._classify_severity(
                action,
            ),
        }

        self._logs[log_id] = entry
        self._tenant_logs.setdefault(
            tenant_id, [],
        ).append(log_id)

        # Limit kontrolu
        tenant_logs = self._tenant_logs.get(
            tenant_id, [],
        )
        if len(tenant_logs) > _MAX_LOGS_PER_TENANT:
            # En eski kayitlari sil
            to_remove = tenant_logs[
                : len(tenant_logs)
                - _MAX_LOGS_PER_TENANT
            ]
            for old_id in to_remove:
                self._logs.pop(old_id, None)
            self._tenant_logs[tenant_id] = (
                tenant_logs[
                    len(tenant_logs)
                    - _MAX_LOGS_PER_TENANT:
                ]
            )

        self._stats["logged"] += 1

        logger.debug(
            "Denetim kaydi: %s %s %s (%s)",
            actor, action, resource, tenant_id,
        )

        return log_id

    def _classify_severity(
        self,
        action: str,
    ) -> str:
        """Aksiyon ciddiyetini siniflandirir.

        Args:
            action: Aksiyon.

        Returns:
            Ciddiyet seviyesi.
        """
        high_actions = {
            "delete", "suspend", "revoke",
            "escalate", "override",
        }
        medium_actions = {
            "create", "update", "assign",
            "configure", "deploy",
        }

        if action in high_actions:
            return "high"
        if action in medium_actions:
            return "medium"
        return "low"

    def get_logs(
        self,
        tenant_id: str,
        start: datetime | None = None,
        end: datetime | None = None,
        actor: str | None = None,
        action: str | None = None,
    ) -> list[dict[str, Any]]:
        """Denetim kayitlarini sorgular.

        Args:
            tenant_id: Kiraci ID.
            start: Baslangic tarihi.
            end: Bitis tarihi.
            actor: Aktor filtresi.
            action: Aksiyon filtresi.

        Returns:
            Filtrelenmis log listesi.
        """
        self._stats["queries"] += 1

        log_ids = self._tenant_logs.get(
            tenant_id, [],
        )
        results = []

        for log_id in log_ids:
            entry = self._logs.get(log_id)
            if not entry:
                continue

            # Tarih filtresi
            if start or end:
                ts = datetime.fromisoformat(
                    entry["timestamp"],
                )
                if start and ts < start:
                    continue
                if end and ts > end:
                    continue

            # Aktor filtresi
            if actor and entry["actor"] != actor:
                continue

            # Aksiyon filtresi
            if (
                action
                and entry["action"] != action
            ):
                continue

            results.append(entry)

        return results

    def get_recent(
        self,
        tenant_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Son denetim kayitlarini getirir.

        Args:
            tenant_id: Kiraci ID.
            limit: Maks kayit sayisi.

        Returns:
            Son kayitlar.
        """
        log_ids = self._tenant_logs.get(
            tenant_id, [],
        )
        recent_ids = log_ids[-limit:]
        recent_ids.reverse()

        return [
            self._logs[lid]
            for lid in recent_ids
            if lid in self._logs
        ]

    def export_logs(
        self,
        tenant_id: str,
        format: str = "json",
    ) -> str:
        """Denetim kayitlarini disa aktarir.

        Args:
            tenant_id: Kiraci ID.
            format: Cikti formati (json, csv).

        Returns:
            Disa aktarilmis veri.
        """
        self._stats["exported"] += 1

        logs = self.get_logs(tenant_id)

        if format == "csv":
            if not logs:
                return (
                    "log_id,tenant_id,actor,"
                    "action,resource,timestamp"
                )
            header = (
                "log_id,tenant_id,actor,"
                "action,resource,timestamp"
            )
            rows = [header]
            for entry in logs:
                row = (
                    f"{entry['log_id']},"
                    f"{entry['tenant_id']},"
                    f"{entry['actor']},"
                    f"{entry['action']},"
                    f"{entry['resource']},"
                    f"{entry['timestamp']}"
                )
                rows.append(row)
            return "\n".join(rows)

        return json.dumps(
            logs, indent=2, default=str,
        )

    def get_compliance_report(
        self,
        tenant_id: str,
        standard: ComplianceStandard = (
            ComplianceStandard.ISO27001
        ),
    ) -> dict[str, Any]:
        """Uyumluluk raporu uretir.

        Args:
            tenant_id: Kiraci ID.
            standard: Uyumluluk standardi.

        Returns:
            Uyumluluk raporu.
        """
        logs = self.get_logs(tenant_id)
        total = len(logs)

        # Aksiyon dagilimi
        action_dist: dict[str, int] = {}
        severity_dist: dict[str, int] = {}
        actor_dist: dict[str, int] = {}

        for entry in logs:
            action = entry.get("action", "")
            action_dist[action] = (
                action_dist.get(action, 0) + 1
            )

            severity = entry.get(
                "severity", "low",
            )
            severity_dist[severity] = (
                severity_dist.get(severity, 0)
                + 1
            )

            actor = entry.get("actor", "")
            actor_dist[actor] = (
                actor_dist.get(actor, 0) + 1
            )

        high_count = severity_dist.get(
            "high", 0,
        )

        return {
            "tenant_id": tenant_id,
            "standard": standard.value,
            "total_entries": total,
            "action_distribution": action_dist,
            "severity_distribution": (
                severity_dist
            ),
            "unique_actors": len(actor_dist),
            "high_severity_count": high_count,
            "retention_days": (
                self._retention_days
            ),
            "compliant": total > 0,
            "generated_at": datetime.now(
                timezone.utc,
            ).isoformat(),
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        return {
            "total_logs": len(self._logs),
            "tenants_with_logs": len(
                self._tenant_logs,
            ),
            "retention_days": (
                self._retention_days
            ),
            **self._stats,
            "timestamp": time.time(),
        }
