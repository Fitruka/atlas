"""ATLAS RBAC Engine modulu.

Rol tabanli erisim kontrolu.
Roller, izinler ve kullanici yonetimi.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.multitenant_models import (
    Permission,
    PermissionAction,
    Role,
    RoleType,
    TenantUser,
)

logger = logging.getLogger(__name__)

_MAX_ROLES_PER_TENANT = 100
_MAX_PERMISSIONS_PER_ROLE = 200

_DEFAULT_ROLES: dict[
    RoleType, list[str]
] = {
    RoleType.OWNER: [
        "*.create", "*.read", "*.update",
        "*.delete", "*.execute", "*.manage",
    ],
    RoleType.ADMIN: [
        "*.create", "*.read", "*.update",
        "*.delete", "*.execute",
        "users.manage", "roles.manage",
        "settings.manage",
    ],
    RoleType.MANAGER: [
        "*.read", "*.create", "*.update",
        "tasks.execute", "reports.read",
        "team.manage",
    ],
    RoleType.MEMBER: [
        "*.read", "tasks.create",
        "tasks.update", "tasks.execute",
    ],
    RoleType.VIEWER: [
        "*.read",
    ],
    RoleType.GUEST: [
        "public.read",
    ],
}


class RBACEngine:
    """Rol tabanli erisim kontrolu motoru.

    Rolleri ve izinleri yonetir,
    erisim kontrolu yapar.

    Attributes:
        _roles: Rol kayitlari.
        _users: Kullanici kayitlari.
    """

    def __init__(self) -> None:
        """RBAC motorunu baslatir."""
        self._roles: dict[str, Role] = {}
        self._tenant_roles: dict[
            str, list[str]
        ] = {}
        self._users: dict[str, TenantUser] = {}
        self._tenant_users: dict[
            str, list[str]
        ] = {}
        self._stats = {
            "roles_created": 0,
            "roles_removed": 0,
            "users_added": 0,
            "users_removed": 0,
            "permission_checks": 0,
            "permission_granted": 0,
            "permission_denied": 0,
        }

        logger.info("RBACEngine baslatildi")

    def _init_default_roles(
        self,
        tenant_id: str,
    ) -> list[Role]:
        """Varsayilan rolleri olusturur.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Olusturulan roller.
        """
        roles = []
        for role_type, perms in (
            _DEFAULT_ROLES.items()
        ):
            role = self.create_role(
                tenant_id=tenant_id,
                name=f"default_{role_type.value}",
                role_type=role_type,
                permissions=list(perms),
                description=(
                    f"Varsayilan {role_type.value} "
                    f"rolu"
                ),
                is_system=True,
            )
            roles.append(role)
        return roles

    def create_role(
        self,
        tenant_id: str,
        name: str,
        role_type: RoleType = RoleType.MEMBER,
        permissions: list[str] | None = None,
        description: str = "",
        is_system: bool = False,
    ) -> Role:
        """Yeni rol olusturur.

        Args:
            tenant_id: Kiraci ID.
            name: Rol adi.
            role_type: Rol tipi.
            permissions: Izin listesi.
            description: Aciklama.
            is_system: Sistem rolu mu.

        Returns:
            Olusturulan rol.
        """
        role = Role(
            id=str(uuid4())[:8],
            tenant_id=tenant_id,
            name=name,
            role_type=role_type,
            permissions=permissions or [],
            description=description,
            is_system=is_system,
        )

        self._roles[role.id] = role
        self._tenant_roles.setdefault(
            tenant_id, [],
        ).append(role.id)

        self._stats["roles_created"] += 1
        logger.info(
            "Rol olusturuldu: %s (%s)",
            name, role.id,
        )

        return role

    def assign_role(
        self,
        tenant_id: str,
        user_id: str,
        role_id: str,
    ) -> TenantUser | None:
        """Kullaniciya rol atar.

        Args:
            tenant_id: Kiraci ID.
            user_id: Kullanici ID.
            role_id: Rol ID.

        Returns:
            Guncellenmis kullanici veya None.
        """
        # Kullaniciyi bul
        user_key = f"{tenant_id}:{user_id}"
        user = self._users.get(user_key)
        if not user:
            logger.warning(
                "Kullanici bulunamadi: %s",
                user_key,
            )
            return None

        # Rolu dogrula
        role = self._roles.get(role_id)
        if not role:
            logger.warning(
                "Rol bulunamadi: %s", role_id,
            )
            return None

        if role.tenant_id != tenant_id:
            logger.warning(
                "Rol baska kiraciya ait: %s",
                role_id,
            )
            return None

        user.role = role.role_type
        user.permissions = list(role.permissions)

        logger.info(
            "Rol atandi: %s -> %s",
            user_id, role.name,
        )
        return user

    def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        resource: str,
        action: str,
    ) -> bool:
        """Izin kontrolu yapar.

        Args:
            tenant_id: Kiraci ID.
            user_id: Kullanici ID.
            resource: Kaynak adi.
            action: Aksiyon.

        Returns:
            Izin var mi.
        """
        self._stats["permission_checks"] += 1

        user_key = f"{tenant_id}:{user_id}"
        user = self._users.get(user_key)
        if not user or not user.is_active:
            self._stats[
                "permission_denied"
            ] += 1
            return False

        # Owner her seyi yapabilir
        if user.role == RoleType.OWNER:
            self._stats[
                "permission_granted"
            ] += 1
            return True

        # Izinleri kontrol et
        required = f"{resource}.{action}"
        wildcard = f"*.{action}"

        for perm in user.permissions:
            if perm == required:
                self._stats[
                    "permission_granted"
                ] += 1
                return True
            if perm == wildcard:
                self._stats[
                    "permission_granted"
                ] += 1
                return True
            # Tam yildiz erisimi
            if perm == "*.*":
                self._stats[
                    "permission_granted"
                ] += 1
                return True

        self._stats["permission_denied"] += 1
        return False

    def get_user_permissions(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[Permission]:
        """Kullanici izinlerini getirir.

        Args:
            tenant_id: Kiraci ID.
            user_id: Kullanici ID.

        Returns:
            Izin listesi.
        """
        user_key = f"{tenant_id}:{user_id}"
        user = self._users.get(user_key)
        if not user:
            return []

        permissions = []
        for perm_str in user.permissions:
            parts = perm_str.split(".", 1)
            resource = parts[0] if parts else "*"
            action_str = (
                parts[1] if len(parts) > 1
                else "read"
            )

            try:
                action = PermissionAction(
                    action_str,
                )
            except ValueError:
                action = PermissionAction.READ

            permissions.append(
                Permission(
                    resource=resource,
                    action=action,
                    granted=True,
                ),
            )

        return permissions

    def list_roles(
        self,
        tenant_id: str,
    ) -> list[Role]:
        """Kiraci rollerini listeler.

        Args:
            tenant_id: Kiraci ID.

        Returns:
            Rol listesi.
        """
        role_ids = self._tenant_roles.get(
            tenant_id, [],
        )
        return [
            self._roles[rid]
            for rid in role_ids
            if rid in self._roles
        ]

    def remove_role(
        self,
        tenant_id: str,
        role_id: str,
    ) -> bool:
        """Rolu siler.

        Args:
            tenant_id: Kiraci ID.
            role_id: Rol ID.

        Returns:
            Basarili mi.
        """
        role = self._roles.get(role_id)
        if not role:
            return False

        if role.tenant_id != tenant_id:
            return False

        if role.is_system:
            logger.warning(
                "Sistem rolu silinemez: %s",
                role_id,
            )
            return False

        del self._roles[role_id]
        if tenant_id in self._tenant_roles:
            self._tenant_roles[
                tenant_id
            ] = [
                rid for rid
                in self._tenant_roles[tenant_id]
                if rid != role_id
            ]

        self._stats["roles_removed"] += 1
        logger.info(
            "Rol silindi: %s", role_id,
        )
        return True

    def add_user(
        self,
        tenant_id: str,
        user_id: str,
        email: str = "",
        role_type: RoleType = RoleType.MEMBER,
    ) -> TenantUser:
        """Kiraciya kullanici ekler.

        Args:
            tenant_id: Kiraci ID.
            user_id: Kullanici ID.
            email: E-posta.
            role_type: Rol tipi.

        Returns:
            Olusturulan kullanici.
        """
        # Varsayilan izinleri al
        perms = list(
            _DEFAULT_ROLES.get(
                role_type,
                _DEFAULT_ROLES[RoleType.MEMBER],
            ),
        )

        user = TenantUser(
            id=str(uuid4())[:8],
            tenant_id=tenant_id,
            user_id=user_id,
            email=email,
            role=role_type,
            permissions=perms,
        )

        user_key = f"{tenant_id}:{user_id}"
        self._users[user_key] = user
        self._tenant_users.setdefault(
            tenant_id, [],
        ).append(user_key)

        self._stats["users_added"] += 1
        logger.info(
            "Kullanici eklendi: %s -> %s",
            user_id, tenant_id,
        )

        return user

    def remove_user(
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
        user_key = f"{tenant_id}:{user_id}"
        if user_key not in self._users:
            return False

        del self._users[user_key]
        if tenant_id in self._tenant_users:
            self._tenant_users[
                tenant_id
            ] = [
                uk for uk
                in self._tenant_users[tenant_id]
                if uk != user_key
            ]

        self._stats["users_removed"] += 1
        logger.info(
            "Kullanici cikarildi: %s <- %s",
            user_id, tenant_id,
        )
        return True

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik bilgileri.
        """
        return {
            "total_roles": len(self._roles),
            "total_users": len(self._users),
            "tenants_with_roles": len(
                self._tenant_roles,
            ),
            **self._stats,
            "timestamp": time.time(),
        }
