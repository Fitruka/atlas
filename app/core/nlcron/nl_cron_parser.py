"""Dogal dil cron ayristirici.

Zaman ifadesi ayristirma, cron donusumu,
saat dilimi yonetimi ve dogrulama.
"""

import logging
import re
import time
from typing import Any

from app.models.nlcron_models import (
    ParsedSchedule,
    RecurrenceType,
)

logger = logging.getLogger(__name__)

_MAX_HISTORY = 10000

# Turkce/Ingilizce gun eслемелери
_DAY_MAP: dict[str, int] = {
    "monday": 1, "tuesday": 2,
    "wednesday": 3, "thursday": 4,
    "friday": 5, "saturday": 6,
    "sunday": 0,
    "pazartesi": 1, "sali": 2,
    "carsamba": 3, "persembe": 4,
    "cuma": 5, "cumartesi": 6,
    "pazar": 0,
    "mon": 1, "tue": 2, "wed": 3,
    "thu": 4, "fri": 5, "sat": 6,
    "sun": 0,
    "pzt": 1, "sal": 2, "car": 3,
    "per": 4, "cum": 5, "cmt": 6,
    "paz": 0,
}

# Saat ifadeleri
_TIME_PATTERNS: list[
    tuple[re.Pattern[str], str]
] = [
    (
        re.compile(
            r"(\d{1,2}):(\d{2})",
        ),
        "time",
    ),
    (
        re.compile(
            r"saat\s+(\d{1,2})",
            re.IGNORECASE,
        ),
        "hour_tr",
    ),
    (
        re.compile(
            r"at\s+(\d{1,2})\s*(am|pm)?",
            re.IGNORECASE,
        ),
        "hour_en",
    ),
]

# Tekrar kaliplari
_RECURRENCE_PATTERNS: dict[
    str, RecurrenceType
] = {
    "every minute": RecurrenceType.MINUTELY,
    "her dakika": RecurrenceType.MINUTELY,
    "every hour": RecurrenceType.HOURLY,
    "her saat": RecurrenceType.HOURLY,
    "every day": RecurrenceType.DAILY,
    "her gun": RecurrenceType.DAILY,
    "daily": RecurrenceType.DAILY,
    "gunluk": RecurrenceType.DAILY,
    "every week": RecurrenceType.WEEKLY,
    "her hafta": RecurrenceType.WEEKLY,
    "weekly": RecurrenceType.WEEKLY,
    "haftalik": RecurrenceType.WEEKLY,
    "every month": RecurrenceType.MONTHLY,
    "her ay": RecurrenceType.MONTHLY,
    "monthly": RecurrenceType.MONTHLY,
    "aylik": RecurrenceType.MONTHLY,
    "every year": RecurrenceType.YEARLY,
    "her yil": RecurrenceType.YEARLY,
    "yearly": RecurrenceType.YEARLY,
    "yillik": RecurrenceType.YEARLY,
}


class NaturalLanguageCronParser:
    """Dogal dil cron ayristirici.

    Zaman ifadesi ayristirma, cron donusumu,
    saat dilimi yonetimi ve dogrulama.

    Attributes:
        _default_tz: Varsayilan saat dilimi.
        _parse_history: Ayristirma gecmisi.
    """

    def __init__(
        self,
        default_timezone: str = "Europe/Istanbul",
    ) -> None:
        """NaturalLanguageCronParser baslatir.

        Args:
            default_timezone: Varsayilan saat dilimi.
        """
        self._default_tz: str = default_timezone
        self._parse_history: list[
            dict[str, Any]
        ] = []
        self._total_parsed: int = 0
        self._total_failed: int = 0

        logger.info(
            "NaturalLanguageCronParser baslatildi",
        )

    # ---- Zaman Ifadesi Ayristirma ----

    def parse(
        self,
        text: str,
        timezone: str = "",
    ) -> ParsedSchedule:
        """Dogal dil ifadesini ayristirir.

        Args:
            text: Dogal dil zamanlama.
            timezone: Saat dilimi.

        Returns:
            Ayristirilmis zamanlama.
        """
        tz = timezone or self._default_tz
        normalized = text.strip().lower()

        recurrence = self._detect_recurrence(
            normalized,
        )
        hour, minute = self._extract_time(
            normalized,
        )
        days = self._extract_days(normalized)
        cron_expr = self._build_cron(
            recurrence, hour, minute, days,
        )

        confidence = self._calculate_confidence(
            normalized, recurrence, hour, cron_expr,
        )

        schedule = ParsedSchedule(
            original_text=text,
            cron_expression=cron_expr,
            recurrence_type=recurrence,
            timezone=tz,
            next_run=0.0,
            confidence=confidence,
            parsed_at=time.time(),
        )

        self._total_parsed += 1
        self._record_parse(text, schedule)

        return schedule

    def parse_batch(
        self,
        texts: list[str],
        timezone: str = "",
    ) -> list[ParsedSchedule]:
        """Toplu ayristirma yapar.

        Args:
            texts: Metin listesi.
            timezone: Saat dilimi.

        Returns:
            Sonuc listesi.
        """
        results: list[ParsedSchedule] = []
        for t in texts:
            r = self.parse(t, timezone)
            results.append(r)
        return results

    # ---- Cron Donusumu ----

    def _build_cron(
        self,
        recurrence: RecurrenceType,
        hour: int,
        minute: int,
        days: list[int],
    ) -> str:
        """Cron ifadesi olusturur.

        Args:
            recurrence: Yinelenme tipi.
            hour: Saat.
            minute: Dakika.
            days: Gun listesi.

        Returns:
            Cron ifadesi.
        """
        if recurrence == RecurrenceType.MINUTELY:
            return "* * * * *"

        if recurrence == RecurrenceType.HOURLY:
            return f"{minute} * * * *"

        if recurrence == RecurrenceType.DAILY:
            return f"{minute} {hour} * * *"

        if recurrence == RecurrenceType.WEEKLY:
            if days:
                day_str = ",".join(
                    str(d) for d in days
                )
            else:
                day_str = "1"
            return (
                f"{minute} {hour} * * {day_str}"
            )

        if recurrence == RecurrenceType.MONTHLY:
            return f"{minute} {hour} 1 * *"

        if recurrence == RecurrenceType.YEARLY:
            return f"{minute} {hour} 1 1 *"

        # ONCE veya CUSTOM
        return f"{minute} {hour} * * *"

    def to_cron(self, text: str) -> str:
        """Metni cron ifadesine cevirir.

        Args:
            text: Dogal dil metni.

        Returns:
            Cron ifadesi.
        """
        schedule = self.parse(text)
        return schedule.cron_expression

    # ---- Saat Dilimi ----

    def set_timezone(
        self, timezone: str,
    ) -> None:
        """Varsayilan saat dilimini ayarlar.

        Args:
            timezone: Saat dilimi.
        """
        self._default_tz = timezone

    def get_timezone(self) -> str:
        """Saat dilimini dondurur.

        Returns:
            Saat dilimi.
        """
        return self._default_tz

    # ---- Dogrulama ----

    def validate_cron(
        self, cron_expr: str,
    ) -> tuple[bool, str]:
        """Cron ifadesini dogrular.

        Args:
            cron_expr: Cron ifadesi.

        Returns:
            (gecerli, neden) tuple.
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return (
                False,
                f"5 alan bekleniyor, "
                f"{len(parts)} bulundu",
            )

        labels = [
            "dakika", "saat", "gun",
            "ay", "haftanin_gunu",
        ]
        ranges = [
            (0, 59), (0, 23),
            (1, 31), (1, 12), (0, 7),
        ]

        for i, part in enumerate(parts):
            if part == "*":
                continue

            # Virgul ayirmali
            for val in part.split(","):
                # Aralik
                if "-" in val:
                    try:
                        lo, hi = val.split("-")
                        lo_i, hi_i = (
                            int(lo), int(hi),
                        )
                        if lo_i > hi_i:
                            return (
                                False,
                                f"{labels[i]}: "
                                f"gecersiz aralik "
                                f"{val}",
                            )
                    except ValueError:
                        return (
                            False,
                            f"{labels[i]}: "
                            f"gecersiz deger "
                            f"{val}",
                        )
                    continue

                # Step
                if "/" in val:
                    try:
                        base, step = (
                            val.split("/")
                        )
                        if base != "*":
                            int(base)
                        int(step)
                    except ValueError:
                        return (
                            False,
                            f"{labels[i]}: "
                            f"gecersiz step "
                            f"{val}",
                        )
                    continue

                # Tekil deger
                try:
                    v = int(val)
                    lo, hi = ranges[i]
                    if v < lo or v > hi:
                        return (
                            False,
                            f"{labels[i]}: "
                            f"{v} aralik disi "
                            f"({lo}-{hi})",
                        )
                except ValueError:
                    return (
                        False,
                        f"{labels[i]}: "
                        f"gecersiz deger "
                        f"{val}",
                    )

        return True, "Gecerli"

    def validate_text(
        self, text: str,
    ) -> tuple[bool, str]:
        """Dogal dil metnini dogrular.

        Args:
            text: Dogal dil metni.

        Returns:
            (gecerli, neden) tuple.
        """
        if not text or not text.strip():
            return False, "Bos metin"

        schedule = self.parse(text)
        if schedule.confidence < 0.3:
            return (
                False,
                f"Dusuk guven: "
                f"{schedule.confidence:.2f}",
            )

        return True, "Gecerli"

    # ---- Dahili ----

    def _detect_recurrence(
        self, text: str,
    ) -> RecurrenceType:
        """Yinelenme tipini tespit eder.

        Args:
            text: Normalize metin.

        Returns:
            Yinelenme tipi.
        """
        for pattern, rtype in (
            _RECURRENCE_PATTERNS.items()
        ):
            if pattern in text:
                return rtype

        # Gun ismi varsa haftalik
        for day in _DAY_MAP:
            if day in text:
                return RecurrenceType.WEEKLY

        return RecurrenceType.ONCE

    def _extract_time(
        self, text: str,
    ) -> tuple[int, int]:
        """Saat ve dakika cikarir.

        Args:
            text: Normalize metin.

        Returns:
            (saat, dakika) tuple.
        """
        for pattern, ptype in _TIME_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue

            if ptype == "time":
                h = int(match.group(1))
                m = int(match.group(2))
                if 0 <= h <= 23 and 0 <= m <= 59:
                    return h, m

            elif ptype == "hour_tr":
                h = int(match.group(1))
                if 0 <= h <= 23:
                    return h, 0

            elif ptype == "hour_en":
                h = int(match.group(1))
                ampm = match.group(2)
                if ampm:
                    ampm = ampm.lower()
                    if ampm == "pm" and h < 12:
                        h += 12
                    elif ampm == "am" and h == 12:
                        h = 0
                if 0 <= h <= 23:
                    return h, 0

        return 9, 0  # Varsayilan

    def _extract_days(
        self, text: str,
    ) -> list[int]:
        """Gun isimlerini cikarir.

        Args:
            text: Normalize metin.

        Returns:
            Gun numaralari listesi.
        """
        days: list[int] = []
        for name, num in _DAY_MAP.items():
            if name in text and num not in days:
                days.append(num)
        return sorted(days)

    def _calculate_confidence(
        self,
        text: str,
        recurrence: RecurrenceType,
        hour: int,
        cron_expr: str,
    ) -> float:
        """Guven puani hesaplar.

        Args:
            text: Normalize metin.
            recurrence: Yinelenme tipi.
            hour: Cikarilan saat.
            cron_expr: Cron ifadesi.

        Returns:
            Guven puani (0-1).
        """
        score = 0.3  # Temel

        # Yinelenme tespit edildi
        if recurrence != RecurrenceType.ONCE:
            score += 0.25

        # Saat belirtilmis
        has_time = any(
            p.search(text)
            for p, _ in _TIME_PATTERNS
        )
        if has_time:
            score += 0.25

        # Gun belirtilmis
        has_day = any(
            d in text for d in _DAY_MAP
        )
        if has_day:
            score += 0.1

        # Cron gecerli
        valid, _ = self.validate_cron(cron_expr)
        if valid:
            score += 0.1

        return min(score, 1.0)

    def _record_parse(
        self,
        text: str,
        schedule: ParsedSchedule,
    ) -> None:
        """Ayristirma kaydeder.

        Args:
            text: Orijinal metin.
            schedule: Sonuc.
        """
        self._parse_history.append({
            "text": text,
            "cron": schedule.cron_expression,
            "recurrence": (
                schedule.recurrence_type.value
            ),
            "confidence": schedule.confidence,
            "timestamp": time.time(),
        })

        if len(self._parse_history) > (
            _MAX_HISTORY
        ):
            self._parse_history = (
                self._parse_history[-5000:]
            )

    def get_history(
        self, limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Gecmisi dondurur.

        Args:
            limit: Maks sayi.

        Returns:
            Gecmis listesi.
        """
        return list(
            reversed(
                self._parse_history[-limit:],
            ),
        )

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        return {
            "total_parsed": self._total_parsed,
            "total_failed": self._total_failed,
            "default_timezone": self._default_tz,
            "history_size": len(
                self._parse_history,
            ),
        }
