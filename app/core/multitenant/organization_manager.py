"""ATLAS Organization Manager modulu.

Sirket ve takim yonetimi.
Hiyerarsik organizasyon yapisi.
"""

import logging
import time
from typing import Any
from uuid import uuid4

from app.models.multitenant_models import (
    Organization,
)

logger = logging.getLogger(__name__)

_MAX_ORGS_PER_TENANT = 500
_MAX_HIERARCHY_DEPTH = 10


class OrganizationManager:
    """Organizasyon yoneticisi.

    Sirket ve takim yapisini yonetir.

    Attributes:
        _orgs: Organizasyon kayitlari.
        _tenant_orgs: Kiraci-organizasyon eslemeleri.
    """

    def __init__(self) -> None:
        """Organizasyon yoneticisini baslatir."""
        self._orgs: dict[
            str, Organization
        ] = {}
        self._tenant_orgs: dict[
            str, list[str]
        ] = {}
        self._stats = {
            "created": 0,
            "deleted": 0,
            "members_added": 0,
            "members_removed": 0,
        }

        logger.info(
            "OrganizationManager baslatildi",
        )

    def create_org(
        self,
        name: str,
        tenant_id: str,
        parent_org_id: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Organization:
        """Yeni organizasyon olusturur.

        Args:
            name: Organizasyon adi.
            tenant_id: Kiraci ID.
            parent_org_id: Ust organizasyon ID.
            settings: Ozel ayarlar.

        Returns:
            Olusturulan organizasyon.
        """
        # Hiyerarsi derinlik kontrolu
        if parent_org_id:
            depth = self._get_depth(
                parent_org_id,
            )
            if depth >= _MAX_HIERARCHY_DEPTH:
                logger.warning(
                    "Maks hiyerarsi derinligine "
                    "ulasildi: %d",
                    depth,
                )
                # Yine de olustur ama uyar
                parent_org_id = None

        org = Organization(
            id=str(uuid4())[:8],
            name=name,
            tenant_id=tenant_id,
            parent_org_id=parent_org_id,
            settings=settings or {},
        )

        self._orgs[org.id] = org
        self._tenant_orgs.setdefault(
            tenant_id, [],
        ).append(org.id)

        self._stats["created"] += 1
        logger.info(
            "Organizasyon olusturuldu: %s (%s)",
            name, org.id,
        )

        return org

    def get_org(
        self,
        org_id: str,
    ) -> Organization | None:
        """Organizasyon bilgisini getirir.

        Args:
            org_id: Organizasyon ID.

        Returns:
            Organizasyon veya None.
        """
        return self._orgs.get(org_id)

    def add_member(
        self,
        org_id: str,
        user_id: str,
    ) -> bool:
        """Organizasyona uye ekler.

        Args:
            org_id: Organizasyon ID.
            user_id: Kullanici ID.

        Returns:
            Basarili mi.
        """
        org = self._orgs.get(org_id)
        if not org:
            return False

        if user_id not in org.members:
            org.members.append(user_id)
            self._stats["members_added"] += 1
            logger.info(
                "Uye eklendi: %s -> %s",
                user_id, org_id,
            )

        return True

    def remove_member(
        self,
        org_id: str,
        user_id: str,
    ) -> bool:
        """Organizasyondan uye cikarir.

        Args:
            org_id: Organizasyon ID.
            user_id: Kullanici ID.

        Returns:
            Basarili mi.
        """
        org = self._orgs.get(org_id)
        if not org:
            return False

        if user_id in org.members:
            org.members.remove(user_id)
            self._stats[
                "members_removed"
            ] += 1
            logger.info(
                "Uye cikarildi: %s <- %s",
                user_id, org_id,
            )
            return True

        return False

    def list_orgs(
        self,
        tenant_id: str,
    ) -> list[Organization]:
        """Kiraci organizasyonlarini listeler.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Organizasyon listesi.
        """
        org_ids = self._tenant_orgs.get(
            tenant_id, [],
        )
        return [
            self._orgs[oid]
            for oid in org_ids
            if oid in self._orgs
        ]

    def get_hierarchy(
        self,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Organizasyon hiyerarsisini dondurur.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Agac yapisi.
        """
        orgs = self.list_orgs(tenant_id)
        if not orgs:
            return {"roots": [], "tree": {}}

        # Kok organizasyonlari bul
        roots = [
            o for o in orgs
            if not o.parent_org_id
        ]

        # Agac yapisini olustur
        tree: dict[str, Any] = {}
        for root in roots:
            tree[root.id] = self._build_tree(
                root.id, orgs,
            )

        return {
            "roots": [r.id for r in roots],
            "tree": tree,
            "total_orgs": len(orgs),
        }

    def _build_tree(
        self,
        org_id: str,
        all_orgs: list[Organization],
    ) -> dict[str, Any]:
        """Alt agaci olusturur (recursive).

        Args:
            org_id: Kok organizasyon ID.
            all_orgs: Tum organizasyonlar.

        Returns:
            Alt agac yapisi.
        """
        org = self._orgs.get(org_id)
        if not org:
            return {}

        children = [
            o for o in all_orgs
            if o.parent_org_id == org_id
        ]

        return {
            "id": org.id,
            "name": org.name,
            "members": list(org.members),
            "member_count": len(org.members),
            "children": [
                self._build_tree(
                    c.id, all_orgs,
                )
                for c in children
            ],
        }

    def _get_depth(
        self,
        org_id: str,
    ) -> int:
        """Organizasyon derinligini hesaplar.

        Args:
            org_id: Organizasyon ID.

        Returns:
            Derinlik seviyesi.
        """
        depth = 0
        current_id: str | None = org_id
        visited: set[str] = set()

        while current_id:
            if current_id in visited:
                break  # Dongusel referans
            visited.add(current_id)

            org = self._orgs.get(current_id)
            if not org or not org.parent_org_id:
                break
            current_id = org.parent_org_id
            depth += 1

        return depth

    def delete_org(
        self,
        org_id: str,
    ) -> bool:
        """Organizasyonu siler.

        Args:
            org_id: Organizasyon ID.

        Returns:
            Basarili mi.
        """
        org = self._orgs.get(org_id)
        if not org:
            return False

        # Alt organizasyonlarin parent'ini
        # temizle
        for child in self._orgs.values():
            if child.parent_org_id == org_id:
                child.parent_org_id = (
                    org.parent_org_id
                )

        # Kiraci indeksinden cikar
        tenant_id = org.tenant_id
        if tenant_id in self._tenant_orgs:
            self._tenant_orgs[
                tenant_id
            ] = [
                oid for oid
                in self._tenant_orgs[tenant_id]
                if oid != org_id
            ]

        del self._orgs[org_id]
        self._stats["deleted"] += 1

        logger.info(
            "Organizasyon silindi: %s", org_id,
        )
        return True

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        total_members = sum(
            len(o.members)
            for o in self._orgs.values()
        )
        return {
            "total_orgs": len(self._orgs),
            "total_members": total_members,
            "tenants_with_orgs": len(
                self._tenant_orgs,
            ),
            **self._stats,
            "timestamp": time.time(),
        }
