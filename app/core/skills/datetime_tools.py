"""Tarih ve zaman becerileri.

Tarih hesaplama, timezone cevirme,
takvim islemleri icin 10 beceri.
"""

import calendar
import time
from datetime import datetime, timedelta
from typing import Any

from app.core.skills.base_skill import BaseSkill

# ---- Timezone veritabani ----

_TIMEZONE_OFFSETS: dict[str, float] = {
    "UTC": 0, "GMT": 0, "EST": -5,
    "EDT": -4, "CST": -6, "CDT": -5,
    "MST": -7, "MDT": -6, "PST": -8,
    "PDT": -7, "CET": 1, "CEST": 2,
    "EET": 2, "EEST": 3, "IST": 5.5,
    "JST": 9, "KST": 9, "CST_CN": 8,
    "AEST": 10, "AEDT": 11, "NZST": 12,
    "NZDT": 13, "TRT": 3, "MSK": 3,
    "BRT": -3, "AST": 3, "GST": 4,
    "PKT": 5, "ICT": 7, "WIB": 7,
    "SGT": 8, "HKT": 8, "PHT": 8,
}

# ---- Resmi tatiller ----

_HOLIDAYS: dict[str, list[str]] = {
    "TR": [
        "01-01", "04-23", "05-01",
        "05-19", "07-15", "08-30",
        "10-29",
    ],
    "US": [
        "01-01", "07-04", "12-25",
    ],
    "GB": [
        "01-01", "12-25", "12-26",
    ],
}


class CurrentDatetimeSkill(BaseSkill):
    """Anlik tarih ve saat becerisi."""

    SKILL_ID = "026"
    NAME = "current_datetime"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Anlik tarih ve saat "
        "(herhangi bir timezone)"
    )
    PARAMETERS = {
        "timezone": "Saat dilimi (UTC, TRT, EST vb.)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        tz = p.get("timezone", "UTC")
        offset = _TIMEZONE_OFFSETS.get(
            tz.upper(), 0,
        )
        now = datetime.utcnow() + timedelta(
            hours=offset,
        )
        return {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timezone": tz,
            "offset": offset,
            "day_of_week": now.strftime("%A"),
            "unix_timestamp": time.time(),
        }


class TimezoneConverterSkill(BaseSkill):
    """Timezone cevirici becerisi."""

    SKILL_ID = "027"
    NAME = "timezone_converter"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = "Timezone cevirici"
    PARAMETERS = {
        "time": "Saat (HH:MM veya ISO)",
        "from_tz": "Kaynak timezone",
        "to_tz": "Hedef timezone",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        time_str = p.get("time", "12:00")
        from_tz = p.get("from_tz", "UTC")
        to_tz = p.get("to_tz", "TRT")

        from_off = _TIMEZONE_OFFSETS.get(
            from_tz.upper(), 0,
        )
        to_off = _TIMEZONE_OFFSETS.get(
            to_tz.upper(), 0,
        )
        diff = to_off - from_off

        parts = time_str.split(":")
        hour = int(parts[0]) if parts else 12
        minute = int(parts[1]) if len(parts) > 1 else 0

        total_min = hour * 60 + minute
        total_min += int(diff * 60)
        total_min %= 1440

        new_h = total_min // 60
        new_m = total_min % 60

        return {
            "original": f"{hour:02d}:{minute:02d}",
            "from_timezone": from_tz,
            "converted": f"{new_h:02d}:{new_m:02d}",
            "to_timezone": to_tz,
            "offset_diff": diff,
        }


class DateCalculatorSkill(BaseSkill):
    """Tarih hesaplama becerisi."""

    SKILL_ID = "028"
    NAME = "date_calculator"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Iki tarih arasi gun/ay/yil "
        "hesaplama, tarih ekleme/cikarma"
    )
    PARAMETERS = {
        "date1": "Birinci tarih (YYYY-MM-DD)",
        "date2": "Ikinci tarih (opsiyonel)",
        "days": "Eklenecek gun (opsiyonel)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        d1_str = p.get(
            "date1",
            datetime.utcnow().strftime("%Y-%m-%d"),
        )
        d1 = datetime.strptime(d1_str, "%Y-%m-%d")

        d2_str = p.get("date2", "")
        days = p.get("days", 0)

        if d2_str:
            d2 = datetime.strptime(
                d2_str, "%Y-%m-%d",
            )
            delta = abs((d2 - d1).days)
            years = delta // 365
            months = (delta % 365) // 30
            rem_days = (delta % 365) % 30
            return {
                "date1": d1_str,
                "date2": d2_str,
                "total_days": delta,
                "years": years,
                "months": months,
                "days": rem_days,
                "weeks": delta // 7,
            }

        result_date = d1 + timedelta(days=days)
        return {
            "original_date": d1_str,
            "days_added": days,
            "result_date": result_date.strftime(
                "%Y-%m-%d",
            ),
            "day_of_week": result_date.strftime(
                "%A",
            ),
        }


class CountdownTimerSkill(BaseSkill):
    """Geri sayim becerisi."""

    SKILL_ID = "029"
    NAME = "countdown_timer"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = "Geri sayim olustur"
    PARAMETERS = {
        "target_date": "Hedef tarih (YYYY-MM-DD)",
        "label": "Etiket",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        target_str = p.get(
            "target_date", "2026-12-31",
        )
        label = p.get("label", "Hedef")
        target = datetime.strptime(
            target_str, "%Y-%m-%d",
        )
        now = datetime.utcnow()
        delta = target - now
        total_sec = max(
            int(delta.total_seconds()), 0,
        )
        days = total_sec // 86400
        hours = (total_sec % 86400) // 3600
        minutes = (total_sec % 3600) // 60
        seconds = total_sec % 60

        return {
            "label": label,
            "target_date": target_str,
            "remaining_days": days,
            "remaining_hours": hours,
            "remaining_minutes": minutes,
            "remaining_seconds": seconds,
            "total_seconds": total_sec,
            "is_past": delta.total_seconds() < 0,
        }


class WorldClockSkill(BaseSkill):
    """Dunya saati becerisi."""

    SKILL_ID = "030"
    NAME = "world_clock"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Birden fazla sehrin "
        "anlik saatini goster"
    )
    PARAMETERS = {
        "cities": "Sehir listesi",
    }

    _CITY_TZ: dict[str, str] = {
        "istanbul": "TRT",
        "new_york": "EST",
        "london": "GMT",
        "tokyo": "JST",
        "dubai": "GST",
        "moscow": "MSK",
        "sydney": "AEST",
        "berlin": "CET",
        "paris": "CET",
        "los_angeles": "PST",
        "singapore": "SGT",
        "hong_kong": "HKT",
        "mumbai": "IST",
        "beijing": "CST_CN",
        "seoul": "KST",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        cities = p.get(
            "cities",
            ["istanbul", "london", "new_york"],
        )
        if isinstance(cities, str):
            cities = [
                c.strip() for c in
                cities.split(",")
            ]

        now_utc = datetime.utcnow()
        results = []
        for city in cities:
            tz = self._CITY_TZ.get(
                city.lower().replace(" ", "_"),
                "UTC",
            )
            offset = _TIMEZONE_OFFSETS.get(tz, 0)
            local = now_utc + timedelta(
                hours=offset,
            )
            results.append({
                "city": city,
                "timezone": tz,
                "time": local.strftime("%H:%M:%S"),
                "date": local.strftime("%Y-%m-%d"),
            })

        return {
            "clocks": results,
            "count": len(results),
        }


class CalendarLookupSkill(BaseSkill):
    """Takvim sorgulama becerisi."""

    SKILL_ID = "031"
    NAME = "calendar_lookup"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Belirli bir tarihin hangi gun "
        "oldugu, tatil mi kontrol"
    )
    PARAMETERS = {
        "date": "Tarih (YYYY-MM-DD)",
        "country": "Ulke kodu (TR, US, GB)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        date_str = p.get(
            "date",
            datetime.utcnow().strftime("%Y-%m-%d"),
        )
        country = p.get("country", "TR")
        dt = datetime.strptime(
            date_str, "%Y-%m-%d",
        )
        md = dt.strftime("%m-%d")
        holidays = _HOLIDAYS.get(
            country.upper(), [],
        )
        is_holiday = md in holidays
        is_weekend = dt.weekday() >= 5

        return {
            "date": date_str,
            "day_of_week": dt.strftime("%A"),
            "day_number": dt.weekday(),
            "week_number": dt.isocalendar()[1],
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "is_leap_year": calendar.isleap(
                dt.year,
            ),
            "days_in_month": calendar.monthrange(
                dt.year, dt.month,
            )[1],
            "country": country,
        }


class AgeCalculatorSkill(BaseSkill):
    """Yas hesaplama becerisi."""

    SKILL_ID = "032"
    NAME = "age_calculator"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Dogum tarihinden yas hesaplama "
        "(yil/ay/gun detayinda)"
    )
    PARAMETERS = {
        "birth_date": "Dogum tarihi (YYYY-MM-DD)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        bd_str = p.get(
            "birth_date", "2000-01-01",
        )
        bd = datetime.strptime(
            bd_str, "%Y-%m-%d",
        )
        now = datetime.utcnow()
        delta = now - bd
        total_days = delta.days

        years = total_days // 365
        rem = total_days % 365
        months = rem // 30
        days = rem % 30

        next_bd = bd.replace(year=now.year)
        if next_bd < now:
            next_bd = bd.replace(
                year=now.year + 1,
            )
        days_to_bd = (next_bd - now).days

        return {
            "birth_date": bd_str,
            "age_years": years,
            "age_months": months,
            "age_days": days,
            "total_days": total_days,
            "total_weeks": total_days // 7,
            "days_to_next_birthday": max(
                days_to_bd, 0,
            ),
        }


class WorkDaysCalculatorSkill(BaseSkill):
    """Is gunu hesaplama becerisi."""

    SKILL_ID = "033"
    NAME = "work_days_calculator"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Iki tarih arasi is gunu "
        "hesaplama (tatilleri cikararak)"
    )
    PARAMETERS = {
        "start_date": "Baslangic tarihi",
        "end_date": "Bitis tarihi",
        "country": "Ulke kodu",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        s_str = p.get("start_date", "2026-01-01")
        e_str = p.get("end_date", "2026-12-31")
        country = p.get("country", "TR")

        start = datetime.strptime(
            s_str, "%Y-%m-%d",
        )
        end = datetime.strptime(
            e_str, "%Y-%m-%d",
        )
        holidays = _HOLIDAYS.get(
            country.upper(), [],
        )

        total = 0
        weekends = 0
        holiday_count = 0
        work_days = 0
        current = start

        while current <= end:
            total += 1
            md = current.strftime("%m-%d")
            if current.weekday() >= 5:
                weekends += 1
            elif md in holidays:
                holiday_count += 1
            else:
                work_days += 1
            current += timedelta(days=1)

        return {
            "start_date": s_str,
            "end_date": e_str,
            "total_days": total,
            "work_days": work_days,
            "weekends": weekends,
            "holidays": holiday_count,
            "country": country,
        }


class UnixTimestampSkill(BaseSkill):
    """Unix timestamp cevirici becerisi."""

    SKILL_ID = "034"
    NAME = "unix_timestamp"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Unix timestamp <-> tarih cevirici"
    )
    PARAMETERS = {
        "input": "Timestamp veya tarih",
        "mode": "to_unix veya from_unix",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        inp = p.get("input", "")
        mode = p.get("mode", "to_unix")

        if mode == "from_unix":
            ts = float(inp) if inp else time.time()
            dt = datetime.utcfromtimestamp(ts)
            return {
                "unix_timestamp": ts,
                "datetime": dt.isoformat(),
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M:%S"),
                "day_of_week": dt.strftime("%A"),
            }

        if inp:
            dt = datetime.strptime(
                inp, "%Y-%m-%d",
            )
        else:
            dt = datetime.utcnow()

        ts = dt.timestamp()
        return {
            "datetime": dt.isoformat(),
            "unix_timestamp": ts,
            "unix_ms": int(ts * 1000),
        }


class ReminderSkill(BaseSkill):
    """Hatirlatici becerisi."""

    SKILL_ID = "035"
    NAME = "reminder"
    CATEGORY = "datetime"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Hatirlatici olustur, listele, iptal et"
    )
    PARAMETERS = {
        "message": "Hatirlatma mesaji",
        "time": "Zaman (dakika veya tarih)",
        "action": "create/list/cancel",
    }

    _reminders: list[dict[str, Any]] = []

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        action = p.get("action", "create")
        message = p.get("message", "")
        rem_time = p.get("time", "30")

        if action == "list":
            return {
                "reminders": list(
                    self._reminders,
                ),
                "count": len(self._reminders),
            }

        if action == "cancel":
            idx = p.get("index", 0)
            if 0 <= idx < len(self._reminders):
                removed = self._reminders.pop(idx)
                return {
                    "cancelled": removed,
                    "remaining": len(
                        self._reminders,
                    ),
                }
            return {"error": "invalid index"}

        reminder = {
            "message": message,
            "time": rem_time,
            "created_at": time.time(),
            "id": len(self._reminders),
        }
        self._reminders.append(reminder)
        return {
            "reminder": reminder,
            "total": len(self._reminders),
        }


ALL_DATETIME_SKILLS: list[type[BaseSkill]] = [
    CurrentDatetimeSkill,
    TimezoneConverterSkill,
    DateCalculatorSkill,
    CountdownTimerSkill,
    WorldClockSkill,
    CalendarLookupSkill,
    AgeCalculatorSkill,
    WorkDaysCalculatorSkill,
    UnixTimestampSkill,
    ReminderSkill,
]
