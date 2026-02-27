"""ATLAS Cloud Onboarding Sihirbazi modulu.

Yeni kullanicilari adim adim yonlendiren
interaktif kurulum sihirbazi, ilerleme
takibi ve yapilandirma onerileri.
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.models.atlascloud_models import (
    InstanceSize,
    Region,
    WizardStep,
)

logger = logging.getLogger(__name__)

_DEFAULT_STEPS = [
    {
        "step_number": 1,
        "title": "Account Setup",
        "description": (
            "Hesap bilgilerinizi yapilandirin"
        ),
    },
    {
        "step_number": 2,
        "title": "Choose Region",
        "description": (
            "Dagitim bolgenizi secin"
        ),
    },
    {
        "step_number": 3,
        "title": "Select Plan",
        "description": (
            "Ornek boyutunuzu secin"
        ),
    },
    {
        "step_number": 4,
        "title": "Configure Agent",
        "description": (
            "Agent ayarlarinizi yapilandirin"
        ),
    },
    {
        "step_number": 5,
        "title": "Deploy",
        "description": (
            "Dagitimi baslatin"
        ),
    },
    {
        "step_number": 6,
        "title": "Verify",
        "description": (
            "Dagitimi dogrulayin"
        ),
    },
]

_MAX_WIZARDS = 500


class OnboardingWizard:
    """Onboarding sihirbazi.

    Yeni kullanicilari adim adim Atlas Cloud
    kurulumundan geciren interaktif sihirbaz.

    Attributes:
        _wizards: Sihirbaz oturumlari.
        _stats: Istatistik sayaclari.
    """

    def __init__(self) -> None:
        """Sihirbazi baslatir."""
        self._wizards: dict[
            str, dict[str, Any]
        ] = {}
        self._stats: dict[str, int] = {
            "wizards_started": 0,
            "wizards_completed": 0,
            "steps_completed": 0,
            "steps_skipped": 0,
            "wizards_reset": 0,
        }

        logger.info("OnboardingWizard baslatildi")

    def start_wizard(
        self,
        tenant_id: str,
    ) -> dict[str, Any]:
        """Sihirbaz oturumu baslatir.

        Args:
            tenant_id: Kiralayici ID.

        Returns:
            Sihirbaz oturum bilgisi.
        """
        wizard_id = str(uuid4())[:8]

        steps = [
            WizardStep(
                step_number=s["step_number"],
                title=s["title"],
                description=s["description"],
            )
            for s in _DEFAULT_STEPS
        ]

        wizard = {
            "wizard_id": wizard_id,
            "tenant_id": tenant_id,
            "steps": steps,
            "current_step": 1,
            "completed": False,
            "started_at": datetime.now(
                timezone.utc,
            ).isoformat(),
            "completed_at": None,
        }

        self._wizards[wizard_id] = wizard
        self._stats["wizards_started"] += 1

        # Eski kayitlari temizle
        if len(self._wizards) > _MAX_WIZARDS:
            oldest = list(self._wizards.keys())[0]
            del self._wizards[oldest]

        logger.info(
            "Sihirbaz baslatildi: %s (tenant: %s)",
            wizard_id,
            tenant_id,
        )

        return {
            "wizard_id": wizard_id,
            "tenant_id": tenant_id,
            "total_steps": len(steps),
            "current_step": 1,
        }

    def complete_step(
        self,
        wizard_id: str,
        step_number: int,
        data: dict[str, Any] | None = None,
    ) -> WizardStep | None:
        """Adimi tamamlar.

        Args:
            wizard_id: Sihirbaz ID.
            step_number: Adim numarasi.
            data: Adim verileri.

        Returns:
            Tamamlanan adim veya None.
        """
        wizard = self._wizards.get(wizard_id)
        if not wizard:
            return None

        steps: list[WizardStep] = wizard["steps"]

        for step in steps:
            if step.step_number == step_number:
                step.completed = True
                step.data = data or {}
                self._stats["steps_completed"] += 1

                # Siraki adima gec
                wizard["current_step"] = min(
                    step_number + 1,
                    len(steps),
                )

                # Tum adimlar tamamlandi mi?
                all_done = all(
                    s.completed for s in steps
                )
                if all_done:
                    wizard["completed"] = True
                    wizard["completed_at"] = (
                        datetime.now(
                            timezone.utc,
                        ).isoformat()
                    )
                    self._stats[
                        "wizards_completed"
                    ] += 1

                logger.info(
                    "Adim tamamlandi: %s/%d",
                    wizard_id,
                    step_number,
                )

                return step

        return None

    def get_progress(
        self,
        wizard_id: str,
    ) -> dict[str, Any]:
        """Ilerleme durumunu getirir.

        Args:
            wizard_id: Sihirbaz ID.

        Returns:
            Ilerleme bilgisi.
        """
        wizard = self._wizards.get(wizard_id)
        if not wizard:
            return {
                "error": "wizard_not_found",
            }

        steps: list[WizardStep] = wizard["steps"]
        completed_count = sum(
            1 for s in steps if s.completed
        )
        total = len(steps)
        pct = (
            round(completed_count / total * 100, 1)
            if total > 0
            else 0.0
        )

        return {
            "wizard_id": wizard_id,
            "tenant_id": wizard["tenant_id"],
            "total_steps": total,
            "completed_steps": completed_count,
            "completion_pct": pct,
            "current_step": wizard["current_step"],
            "completed": wizard["completed"],
            "steps": [
                {
                    "step_number": s.step_number,
                    "title": s.title,
                    "completed": s.completed,
                    "data": s.data,
                }
                for s in steps
            ],
        }

    def skip_step(
        self,
        wizard_id: str,
        step_number: int,
    ) -> bool:
        """Adimi atlar.

        Args:
            wizard_id: Sihirbaz ID.
            step_number: Adim numarasi.

        Returns:
            Basarili ise True.
        """
        wizard = self._wizards.get(wizard_id)
        if not wizard:
            return False

        steps: list[WizardStep] = wizard["steps"]

        for step in steps:
            if step.step_number == step_number:
                step.completed = True
                step.data = {"skipped": True}
                self._stats["steps_skipped"] += 1

                wizard["current_step"] = min(
                    step_number + 1,
                    len(steps),
                )

                logger.info(
                    "Adim atlandi: %s/%d",
                    wizard_id,
                    step_number,
                )
                return True

        return False

    def reset_wizard(
        self,
        wizard_id: str,
    ) -> bool:
        """Sihirbazi sifirlar.

        Args:
            wizard_id: Sihirbaz ID.

        Returns:
            Basarili ise True.
        """
        wizard = self._wizards.get(wizard_id)
        if not wizard:
            return False

        steps: list[WizardStep] = wizard["steps"]
        for step in steps:
            step.completed = False
            step.data = {}

        wizard["current_step"] = 1
        wizard["completed"] = False
        wizard["completed_at"] = None

        self._stats["wizards_reset"] += 1

        logger.info(
            "Sihirbaz sifirlandi: %s", wizard_id,
        )
        return True

    def get_recommended_config(
        self,
        answers: dict[str, Any],
    ) -> dict[str, Any]:
        """Yapilandirma onerisi dondurur.

        Args:
            answers: Kullanici yanitlari.

        Returns:
            Onerilen yapilandirma.
        """
        # Bolge onerisi
        user_region = answers.get("region", "")
        if "europe" in user_region.lower():
            region = Region.EU_CENTRAL
        elif "asia" in user_region.lower():
            region = Region.ASIA_PACIFIC
        elif "west" in user_region.lower():
            region = Region.US_WEST
        else:
            region = Region.EU_WEST

        # Boyut onerisi
        expected_users = answers.get(
            "expected_users", 0,
        )
        if expected_users > 10000:
            size = InstanceSize.XLARGE
        elif expected_users > 1000:
            size = InstanceSize.LARGE
        elif expected_users > 100:
            size = InstanceSize.MEDIUM
        else:
            size = InstanceSize.SMALL

        # Ozellik onerileri
        features = ["health_monitoring", "backups"]
        if answers.get("auto_scale", False):
            features.append("auto_scaling")
        if answers.get("ha", False):
            features.append("high_availability")

        return {
            "region": region,
            "instance_size": size,
            "features": features,
            "replicas": (
                3 if "high_availability" in features
                else 1
            ),
            "backup_frequency": "daily",
        }

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        active = sum(
            1 for w in self._wizards.values()
            if not w["completed"]
        )

        return {
            "total_wizards": len(self._wizards),
            "active_wizards": active,
            "wizards_started": self._stats[
                "wizards_started"
            ],
            "wizards_completed": self._stats[
                "wizards_completed"
            ],
            "steps_completed": self._stats[
                "steps_completed"
            ],
            "steps_skipped": self._stats[
                "steps_skipped"
            ],
            "wizards_reset": self._stats[
                "wizards_reset"
            ],
        }
