"""Yinelenme isleyici.

Yinelenen kaliplar, atlama islemleri,
istisna tarihleri ve bitis kosullari.
"""

import logging
import time
from typing import Any

from app.models.nlcron_models import (
    RecurrenceRule,
    RecurrenceType,
)

logger = logging.getLogger(__name__)

_MAX_RULES = 10000

# Yinelenme suresi (saniye)
_INTERVALS: dict[RecurrenceType, float] = {
    RecurrenceType.MINUTELY: 60,
    RecurrenceType.HOURLY: 3600,
    RecurrenceType.DAILY: 86400,
    RecurrenceType.WEEKLY: 604800,
    RecurrenceType.MONTHLY: 2592000,
    RecurrenceType.YEARLY: 31536000,
}


class RecurrenceHandler:
    """Yinelenme isleyici.

    Yinelenen kaliplar, atlama islemleri,
    istisna tarihleri ve bitis kosullari.

    Attributes:
        _rules: Yinelenme kurallari.
        _run_counts: Calistirma sayaclari.
    """

    def __init__(self) -> None:
        """RecurrenceHandler baslatir."""
        self._rules: dict[
            str, RecurrenceRule
        ] = {}
        self._run_counts: dict[
            str, int
        ] = {}
        self._total_calculations: int = 0

        logger.info(
            "RecurrenceHandler baslatildi",
        )

    # ---- Yinelenme Kaliplari ----

    def add_rule(
        self, rule: RecurrenceRule,
    ) -> str:
        """Kural ekler.

        Args:
            rule: Yinelenme kurali.

        Returns:
            Kural ID.
        """
        self._rules[rule.rule_id] = rule
        self._run_counts.setdefault(
            rule.rule_id, 0,
        )

        logger.info(
            "Kural eklendi: %s (%s)",
            rule.rule_id,
            rule.recurrence_type.value,
        )
        return rule.rule_id

    def get_rule(
        self, rule_id: str,
    ) -> RecurrenceRule | None:
        """Kurali dondurur.

        Args:
            rule_id: Kural ID.

        Returns:
            Kural veya None.
        """
        return self._rules.get(rule_id)

    def remove_rule(
        self, rule_id: str,
    ) -> bool:
        """Kurali kaldirir.

        Args:
            rule_id: Kural ID.

        Returns:
            Basarili ise True.
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._run_counts.pop(
                rule_id, None,
            )
            return True
        return False

    def calculate_next(
        self,
        rule: RecurrenceRule,
        from_time: float = 0.0,
    ) -> float:
        """Sonraki calistirmayi hesaplar.

        Args:
            rule: Yinelenme kurali.
            from_time: Baslangic zamani.

        Returns:
            Sonraki zaman (epoch).
            0 ise bitti.
        """
        self._total_calculations += 1
        now = from_time or time.time()

        # Bitis kosulu kontrol
        if self._is_ended(rule):
            return 0.0

        # Once tipi
        if (
            rule.recurrence_type
            == RecurrenceType.ONCE
        ):
            return 0.0

        # Temel aralik
        base_interval = _INTERVALS.get(
            rule.recurrence_type, 86400,
        )
        interval = (
            base_interval * rule.interval
        )

        next_time = now + interval

        # Hafta sonu atlama
        if rule.skip_weekends:
            next_time = self._skip_weekends(
                next_time,
            )

        # Istisna tarihi atlama
        if rule.exception_dates:
            next_time = self._skip_exceptions(
                next_time,
                rule.exception_dates,
                interval,
            )

        return next_time

    def calculate_next_by_id(
        self,
        rule_id: str,
        from_time: float = 0.0,
    ) -> float:
        """ID ile sonraki hesaplar.

        Args:
            rule_id: Kural ID.
            from_time: Baslangic.

        Returns:
            Sonraki zaman veya 0.
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return 0.0
        return self.calculate_next(
            rule, from_time,
        )

    def get_schedule(
        self,
        rule: RecurrenceRule,
        count: int = 5,
        from_time: float = 0.0,
    ) -> list[float]:
        """Gelecek zamanlari dondurur.

        Args:
            rule: Yinelenme kurali.
            count: Kac adet.
            from_time: Baslangic.

        Returns:
            Zaman listesi.
        """
        times: list[float] = []
        current = from_time or time.time()

        for _ in range(count):
            next_t = self.calculate_next(
                rule, current,
            )
            if next_t <= 0:
                break
            times.append(next_t)
            current = next_t

        return times

    # ---- Atlama Islemleri ----

    def _skip_weekends(
        self, timestamp: float,
    ) -> float:
        """Hafta sonlarini atlar.

        Args:
            timestamp: Zaman damgasi.

        Returns:
            Duzeltilmis zaman.
        """
        import datetime

        dt = datetime.datetime.fromtimestamp(
            timestamp,
        )
        # 5=Cumartesi, 6=Pazar
        while dt.weekday() >= 5:
            dt += datetime.timedelta(days=1)

        return dt.timestamp()

    def _skip_exceptions(
        self,
        timestamp: float,
        exceptions: list[float],
        interval: float,
    ) -> float:
        """Istisna tarihlerini atlar.

        Args:
            timestamp: Zaman damgasi.
            exceptions: Istisna tarihleri.
            interval: Tekrar araligi.

        Returns:
            Duzeltilmis zaman.
        """
        max_attempts = 10
        current = timestamp

        for _ in range(max_attempts):
            is_exception = False
            for exc_date in exceptions:
                # Ayni gunde mi (86400 sn)
                if abs(current - exc_date) < 86400:
                    is_exception = True
                    break

            if not is_exception:
                return current

            current += interval

        return current

    def should_skip(
        self,
        rule: RecurrenceRule,
        timestamp: float,
    ) -> tuple[bool, str]:
        """Bu zamanda atlanmali mi.

        Args:
            rule: Yinelenme kurali.
            timestamp: Zaman damgasi.

        Returns:
            (atla, neden) tuple.
        """
        import datetime

        dt = datetime.datetime.fromtimestamp(
            timestamp,
        )

        # Hafta sonu
        if (
            rule.skip_weekends
            and dt.weekday() >= 5
        ):
            return True, "Hafta sonu"

        # Istisna tarihi
        for exc in rule.exception_dates:
            if abs(timestamp - exc) < 86400:
                return True, "Istisna tarihi"

        # Gun filtresi
        if (
            rule.days_of_week
            and dt.weekday() + 1
            not in rule.days_of_week
        ):
            return True, "Gun filtresi"

        # Ay gunu filtresi
        if (
            rule.days_of_month
            and dt.day
            not in rule.days_of_month
        ):
            return True, "Ay gunu filtresi"

        # Ay filtresi
        if (
            rule.months
            and dt.month not in rule.months
        ):
            return True, "Ay filtresi"

        return False, ""

    # ---- Istisna Tarihleri ----

    def add_exception(
        self,
        rule_id: str,
        exception_date: float,
    ) -> bool:
        """Istisna tarihi ekler.

        Args:
            rule_id: Kural ID.
            exception_date: Istisna zamani.

        Returns:
            Basarili ise True.
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return False

        if (
            exception_date
            not in rule.exception_dates
        ):
            rule.exception_dates.append(
                exception_date,
            )

        return True

    def remove_exception(
        self,
        rule_id: str,
        exception_date: float,
    ) -> bool:
        """Istisna tarihini kaldirir.

        Args:
            rule_id: Kural ID.
            exception_date: Istisna zamani.

        Returns:
            Basarili ise True.
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return False

        if (
            exception_date
            in rule.exception_dates
        ):
            rule.exception_dates.remove(
                exception_date,
            )
            return True

        return False

    def get_exceptions(
        self, rule_id: str,
    ) -> list[float]:
        """Istisna tarihlerini dondurur.

        Args:
            rule_id: Kural ID.

        Returns:
            Tarih listesi.
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return []
        return list(rule.exception_dates)

    # ---- Bitis Kosullari ----

    def _is_ended(
        self, rule: RecurrenceRule,
    ) -> bool:
        """Kural sona erdi mi.

        Args:
            rule: Yinelenme kurali.

        Returns:
            Bitti ise True.
        """
        # Calistirma sayisi limiti
        if rule.end_after_runs > 0:
            count = self._run_counts.get(
                rule.rule_id, 0,
            )
            if count >= rule.end_after_runs:
                return True

        # Bitis tarihi
        if rule.end_date > 0:
            if time.time() > rule.end_date:
                return True

        return False

    def record_run(
        self, rule_id: str,
    ) -> int:
        """Calistirma kaydeder.

        Args:
            rule_id: Kural ID.

        Returns:
            Guncel sayi.
        """
        count = self._run_counts.get(
            rule_id, 0,
        ) + 1
        self._run_counts[rule_id] = count
        return count

    def is_ended(
        self, rule_id: str,
    ) -> bool:
        """Kural sona erdi mi (ID ile).

        Args:
            rule_id: Kural ID.

        Returns:
            Bitti ise True.
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return True
        return self._is_ended(rule)

    def get_remaining_runs(
        self, rule_id: str,
    ) -> int:
        """Kalan calistirma sayisini dondurur.

        Args:
            rule_id: Kural ID.

        Returns:
            Kalan sayi. -1 ise sinirsiz.
        """
        rule = self._rules.get(rule_id)
        if not rule:
            return 0

        if rule.end_after_runs <= 0:
            return -1

        count = self._run_counts.get(
            rule_id, 0,
        )
        remaining = (
            rule.end_after_runs - count
        )
        return max(remaining, 0)

    # ---- Istatistikler ----

    def get_stats(self) -> dict[str, Any]:
        """Istatistikleri dondurur.

        Returns:
            Istatistik sozlugu.
        """
        type_counts: dict[str, int] = {}
        for rule in self._rules.values():
            t = rule.recurrence_type.value
            type_counts[t] = (
                type_counts.get(t, 0) + 1
            )

        return {
            "total_rules": len(self._rules),
            "type_counts": type_counts,
            "total_calculations": (
                self._total_calculations
            ),
            "active_run_counts": len(
                self._run_counts,
            ),
        }
