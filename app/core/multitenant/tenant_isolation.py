"""ATLAS Tenant Isolation modulu.

Kiraci izolasyonu, veri ayirma ve
erisim sinirlari yonetimi.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.multitenant_models import (
    BillingPlan,
    Tenant,
    TenantStatus,
)

logger = logging.getLogger(__name__)

_MAX_TENANTS = 10000
_DEFAULT_MAX_USERS = 10
_DEFAULT_MAX_AGENTS = 5

_PLAN_LIMITS: dict[str, dict[str, int]] = {
    BillingPlan.FREE: {
        "max_users": 5,
        "max_agents": 2,
        "max_storage_mb": 100,
    },
    BillingPlan.STARTER: {
        "max_users": 25,
        "max_agents": 10,
        "max_storage_mb": 1024,
    },
    BillingPlan.PROFESSIONAL: {
        "max_users": 100,
        "max_agents": 50,
        "max_storage_mb": 10240,
    },
    BillingPlan.ENTERPRISE: {
        "max_users": 1000,
        "max_agents": 500,
        "max_storage_mb": 102400,
    },
    BillingPlan.CUSTOM: {
        "max_users": 10000,
        "max_agents": 5000,
        "max_storage_mb": 1048576,
    },
}


class TenantIsolation:
    """Kiraci izolasyon yoneticisi.

    Kiracilari olusturur, yonetir ve
    veri izolasyonunu saglar.

    Attributes:
        _tenants: Kiraci kayitlari.
        _tenant_users: Kiraci-kullanici eslemeleri.
    """

    def __init__(self) -> None:
        """Kiraci izolasyonunu baslatir."""
        self._tenants: dict[str, Tenant] = {}
        self._slug_index: dict[str, str] = {}
        self._tenant_users: dict[
            str, set[str]
        ] = {}
        self._stats = {
            "created": 0,
            "suspended": 0,
            "deleted": 0,
            "access_checks": 0,
        }

        logger.info(
            "TenantIsolation baslatildi",
        )

    def create_tenant(
        self,
        name: str,
        slug: str,
        plan: BillingPlan = BillingPlan.FREE,
        owner_id: str = "",
        settings: dict[str, Any] | None = None,
    ) -> Tenant:
        """Yeni kiraci olusturur.

        Args:
            name: Kiraci adi.
            slug: Benzersiz slug.
            plan: Faturalandirma plani.
            owner_id: Sahip ID.
            settings: Ozel ayarlar.

        Returns:
            Olusturulan kiraci.
        """
        if slug in self._slug_index:
            logger.warning(
                "Slug zaten mevcut: %s", slug,
            )
            existing_id = self._slug_index[slug]
            return self._tenants[existing_id]

        limits = _PLAN_LIMITS.get(
            plan,
            _PLAN_LIMITS[BillingPlan.FREE],
        )

        tenant = Tenant(
            id=str(uuid4())[:8],
            name=name,
            slug=slug,
            status=TenantStatus.ACTIVE,
            plan=plan,
            owner_id=owner_id,
            settings=settings or {},
            max_users=limits["max_users"],
            max_agents=limits["max_agents"],
        )

        self._tenants[tenant.id] = tenant
        self._slug_index[slug] = tenant.id
        self._tenant_users[tenant.id] = set()

        if owner_id:
            self._tenant_users[tenant.id].add(
                owner_id,
            )

        self._stats["created"] += 1
        logger.info(
            "Kiraci olusturuldu: %s (%s)",
            name, tenant.id,
        )

        return tenant

    def get_tenant(
        self,
        tenant_id: str,
    ) -> Tenant | None:
        """Kiraci bilgisini getirir.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Kiraci veya None.
        """
        return self._tenants.get(tenant_id)

    def get_tenant_by_slug(
        self,
        slug: str,
    ) -> Tenant | None:
        """Slug ile kiraci getirir.

        Args:
            slug: Kiraci slug.

        Returns:
            Kiraci veya None.
        """
        tenant_id = self._slug_index.get(slug)
        if tenant_id:
            return self._tenants.get(tenant_id)
        return None

    def update_tenant(
        self,
        tenant_id: str,
        **updates: Any,
    ) -> Tenant | None:
        """Kiraci bilgilerini gunceller.

        Args:
            tenant_id: Kiraci ID.
            **updates: Guncellenecek alanlar.

        Returns:
            Guncellenmis kiraci veya None.
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None

        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        # Slug degistiyse indeksi guncelle
        if "slug" in updates:
            old_slugs = [
                s for s, tid
                in self._slug_index.items()
                if tid == tenant_id
            ]
            for old_slug in old_slugs:
                del self._slug_index[old_slug]
            self._slug_index[
                updates["slug"]
            ] = tenant_id

        logger.info(
            "Kiraci guncellendi: %s", tenant_id,
        )
        return tenant

    def suspend_tenant(
        self,
        tenant_id: str,
    ) -> bool:
        """Kiraciyi askiya alir.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Basarili mi.
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.SUSPENDED
        self._stats["suspended"] += 1

        logger.info(
            "Kiraci askiya alindi: %s",
            tenant_id,
        )
        return True

    def delete_tenant(
        self,
        tenant_id: str,
    ) -> bool:
        """Kiraciyi siler (soft delete).

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Basarili mi.
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False

        tenant.status = TenantStatus.DELETED
        self._stats["deleted"] += 1

        logger.info(
            "Kiraci silindi: %s", tenant_id,
        )
        return True

    def list_tenants(
        self,
        status: TenantStatus | None = None,
    ) -> list[Tenant]:
        """Kiracilari listeler.

        Args:
            status: Durum filtresi.

        Returns:
            Kiraci listesi.
        """
        tenants = list(self._tenants.values())
        if status:
            tenants = [
                t for t in tenants
                if t.status == status
            ]
        return tenants

    def validate_tenant_access(
        self,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """Kullanici erisimini dogrular.

        Args:
            tenant_id: Kiraci ID.
            user_id: Kullanici ID.

        Returns:
            Erisim izni var mi.
        """
        self._stats["access_checks"] += 1

        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False

        if tenant.status != TenantStatus.ACTIVE:
            return False

        users = self._tenant_users.get(
            tenant_id, set(),
        )
        return user_id in users

    def add_user_to_tenant(
        self,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """Kiraciya kullanici ekler.

        Args:
            tenant_id: Kiraci ID.
            user_id: Kullanici ID.

        Returns:
            Basarili mi.
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False

        users = self._tenant_users.setdefault(
            tenant_id, set(),
        )

        if len(users) >= tenant.max_users:
            logger.warning(
                "Maks kullanici limitine ulasildi: "
                "%s (%d)",
                tenant_id, tenant.max_users,
            )
            return False

        users.add(user_id)
        return True

    def remove_user_from_tenant(
        self,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """Kiracidan kullanici cikarir.

        Args:
            tenant_id: Kiraci ID.
            user_id: Kullanici ID.

        Returns:
            Basarili mi.
        """
        users = self._tenant_users.get(
            tenant_id, set(),
        )
        if user_id in users:
            users.discard(user_id)
            return True
        return False

    def get_tenant_data_scope(
        self,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Kiraci veri izolasyon sinirlarini dondurur.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Izolasyon sinirlari.
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return {}

        limits = _PLAN_LIMITS.get(
            tenant.plan,
            _PLAN_LIMITS[BillingPlan.FREE],
        )

        users = self._tenant_users.get(
            tenant_id, set(),
        )

        return {
            "tenant_id": tenant_id,
            "slug": tenant.slug,
            "plan": tenant.plan,
            "isolation_level": "schema",
            "data_prefix": f"t_{tenant.slug}_",
            "max_users": tenant.max_users,
            "current_users": len(users),
            "max_agents": tenant.max_agents,
            "max_storage_mb": limits[
                "max_storage_mb"
            ],
            "allowed_regions": tenant.settings.get(
                "regions", ["default"],
            ),
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        active = sum(
            1 for t in self._tenants.values()
            if t.status == TenantStatus.ACTIVE
        )
        return {
            "total_tenants": len(self._tenants),
            "active_tenants": active,
            "total_users": sum(
                len(u) for u
                in self._tenant_users.values()
            ),
            **self._stats,
            "timestamp": time.time(),
        }
