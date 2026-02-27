"""ATLAS Dependency Resolver modulu.

Bagimlilik cozumleme: analiz, catisma tespiti,
cozumleme, agac gorselleme, alternatif onerisi.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.agentmarket_models import (
    DependencyNode,
    DependencyStatus,
)

logger = logging.getLogger(__name__)

_KNOWN_ALTERNATIVES: dict[
    str, list[str]
] = {
    "requests": [
        "httpx", "aiohttp", "urllib3",
    ],
    "flask": [
        "fastapi", "django", "bottle",
    ],
    "sqlalchemy": [
        "peewee", "tortoise-orm", "databases",
    ],
    "celery": [
        "dramatiq", "huey", "rq",
    ],
    "redis": [
        "memcached", "etcd", "valkey",
    ],
    "pillow": [
        "opencv-python", "wand", "scikit-image",
    ],
    "numpy": [
        "jax", "torch",
    ],
    "pandas": [
        "polars", "dask", "vaex",
    ],
}

_LATEST_VERSIONS: dict[str, str] = {
    "requests": "2.31.0",
    "flask": "3.0.0",
    "fastapi": "0.109.0",
    "sqlalchemy": "2.0.25",
    "celery": "5.3.6",
    "redis": "5.0.1",
    "pydantic": "2.5.3",
    "numpy": "1.26.3",
    "pandas": "2.1.4",
    "httpx": "0.26.0",
}


class DependencyResolver:
    """Bagimlilik cozumleyici.

    Listeleme bagimlilik analizi, catisma
    tespiti ve cozumleme islemleri.

    Attributes:
        _nodes: Bagimlilik dugumleri.
        _listing_deps: Listeleme bagimlilik indeksi.
        _stats: Istatistikler.
    """

    def __init__(self) -> None:
        """Bagimlilik cozumleyiciyi baslatir."""
        self._nodes: dict[
            str, DependencyNode
        ] = {}
        self._listing_deps: dict[
            str, list[str]
        ] = {}
        self._stats = {
            "analyzed": 0,
            "resolved": 0,
            "conflicts_found": 0,
            "alternatives_suggested": 0,
        }

        logger.info(
            "DependencyResolver baslatildi",
        )

    def analyze(
        self,
        listing_id: str,
        dependencies: list[dict[str, str]],
    ) -> list[DependencyNode]:
        """Bagimliliklari analiz eder.

        Args:
            listing_id: Listeleme ID.
            dependencies: Bagimlilik listesi.
                Her biri {name, version, required_version}.

        Returns:
            Bagimlilik dugum listesi.
        """
        nodes = []

        for dep in dependencies:
            name = dep.get("name", "")
            version = dep.get("version", "")
            required = dep.get(
                "required_version", "",
            )

            # Durum belirle
            status = self._determine_status(
                name, version, required,
            )

            # Alternatifler
            alternatives = (
                _KNOWN_ALTERNATIVES.get(
                    name, [],
                )
            )

            node = DependencyNode(
                listing_id=listing_id,
                name=name,
                version=version,
                required_version=required,
                status=status,
                alternatives=alternatives,
            )

            self._nodes[node.id] = node
            nodes.append(node)

        # Indeksle
        self._listing_deps[listing_id] = [
            n.id for n in nodes
        ]

        self._stats["analyzed"] += len(nodes)

        logger.info(
            "Bagimlilik analizi: %s, %d bagimlilik",
            listing_id, len(nodes),
        )
        return nodes

    def _determine_status(
        self,
        name: str,
        version: str,
        required_version: str,
    ) -> DependencyStatus:
        """Bagimlilik durumunu belirler.

        Args:
            name: Paket adi.
            version: Mevcut surum.
            required_version: Gereken surum.

        Returns:
            Bagimlilik durumu.
        """
        if not version:
            return DependencyStatus.MISSING

        latest = _LATEST_VERSIONS.get(name)

        if (
            required_version
            and version != required_version
        ):
            return DependencyStatus.CONFLICT

        if latest and version < latest:
            return DependencyStatus.OUTDATED

        return DependencyStatus.RESOLVED

    def check_conflicts(
        self,
        listing_id: str,
    ) -> list[dict[str, Any]]:
        """Catismalari kontrol eder.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Catisma listesi.
        """
        dep_ids = self._listing_deps.get(
            listing_id, [],
        )
        conflicts = []

        for dep_id in dep_ids:
            node = self._nodes.get(dep_id)
            if not node:
                continue
            if node.status in (
                DependencyStatus.CONFLICT,
                DependencyStatus.MISSING,
            ):
                conflicts.append({
                    "dependency": node.name,
                    "status": node.status.value,
                    "version": node.version,
                    "required": (
                        node.required_version
                    ),
                    "alternatives": (
                        node.alternatives
                    ),
                })
                self._stats[
                    "conflicts_found"
                ] += 1

        return conflicts

    def resolve(
        self,
        listing_id: str,
    ) -> dict[str, Any]:
        """Bagimliliklari cozumler.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Cozumleme sonucu.
        """
        dep_ids = self._listing_deps.get(
            listing_id, [],
        )

        resolved = []
        unresolved = []

        for dep_id in dep_ids:
            node = self._nodes.get(dep_id)
            if not node:
                continue

            if node.status == (
                DependencyStatus.RESOLVED
            ):
                resolved.append({
                    "name": node.name,
                    "version": node.version,
                })
            elif node.status == (
                DependencyStatus.OUTDATED
            ):
                # Guncellenebilir, cozulmus sayilir
                latest = _LATEST_VERSIONS.get(
                    node.name, node.version,
                )
                resolved.append({
                    "name": node.name,
                    "version": node.version,
                    "update_to": latest,
                })
                node.status = (
                    DependencyStatus.RESOLVED
                )
            else:
                unresolved.append({
                    "name": node.name,
                    "status": (
                        node.status.value
                    ),
                    "alternatives": (
                        node.alternatives
                    ),
                })

        self._stats["resolved"] += len(resolved)

        return {
            "listing_id": listing_id,
            "total": len(dep_ids),
            "resolved": resolved,
            "resolved_count": len(resolved),
            "unresolved": unresolved,
            "unresolved_count": len(unresolved),
            "fully_resolved": (
                len(unresolved) == 0
            ),
        }

    def get_dependency_tree(
        self,
        listing_id: str,
    ) -> dict[str, Any]:
        """Bagimlilik agaci getirir.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Agac yapisi.
        """
        dep_ids = self._listing_deps.get(
            listing_id, [],
        )

        children = []
        for dep_id in dep_ids:
            node = self._nodes.get(dep_id)
            if not node:
                continue
            children.append({
                "name": node.name,
                "version": node.version,
                "required": (
                    node.required_version
                ),
                "status": node.status.value,
                "alternatives": (
                    node.alternatives
                ),
            })

        return {
            "listing_id": listing_id,
            "dependencies": children,
            "total": len(children),
            "resolved": sum(
                1 for c in children
                if c["status"] == "resolved"
            ),
            "issues": sum(
                1 for c in children
                if c["status"] != "resolved"
            ),
        }

    def suggest_alternatives(
        self,
        dependency_name: str,
    ) -> list[str]:
        """Alternatif paketler onerir.

        Args:
            dependency_name: Paket adi.

        Returns:
            Alternatif listesi.
        """
        alternatives = (
            _KNOWN_ALTERNATIVES.get(
                dependency_name, [],
            )
        )

        if alternatives:
            self._stats[
                "alternatives_suggested"
            ] += 1

        logger.info(
            "Alternatif onerisi: %s -> %s",
            dependency_name, alternatives,
        )
        return alternatives

    def check_updates(
        self,
        listing_id: str,
    ) -> list[dict[str, Any]]:
        """Guncelleme kontrolu yapar.

        Args:
            listing_id: Listeleme ID.

        Returns:
            Guncelleme listesi.
        """
        dep_ids = self._listing_deps.get(
            listing_id, [],
        )
        updates = []

        for dep_id in dep_ids:
            node = self._nodes.get(dep_id)
            if not node:
                continue

            latest = _LATEST_VERSIONS.get(
                node.name,
            )
            if (
                latest
                and node.version
                and node.version < latest
            ):
                updates.append({
                    "name": node.name,
                    "current_version": (
                        node.version
                    ),
                    "latest_version": latest,
                    "status": (
                        node.status.value
                    ),
                })

        return updates

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        status_counts: dict[str, int] = {}
        for node in self._nodes.values():
            s = node.status.value
            status_counts[s] = (
                status_counts.get(s, 0) + 1
            )

        return {
            "total_nodes": len(self._nodes),
            "listings_tracked": len(
                self._listing_deps,
            ),
            "status_distribution": status_counts,
            **self._stats,
        }
