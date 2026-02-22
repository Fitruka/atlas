"""
Yasam & Uretkenlik becerileri (201-225).

Todo yonetimi, aliskanlik takibi, pomodoro, karar verme, oneri sistemleri
ve yasam kalitesi araclari.
"""

from __future__ import annotations

import hashlib
import math
import random
import re
from datetime import datetime, timedelta
from typing import Any

from app.core.skills.base_skill import BaseSkill

# ── Yardimci sabitler ──────────────────────────────────────────────────────

_ZODIAC_SIGNS = [
    {"sign": "koc", "en": "aries", "start": (3, 21), "end": (4, 19),
     "element": "ates", "planet": "mars",
     "traits": ["cesur", "enerjik", "lider", "aceleci"]},
    {"sign": "boga", "en": "taurus", "start": (4, 20), "end": (5, 20),
     "element": "toprak", "planet": "venus",
     "traits": ["kararli", "sadik", "sabırli", "inatci"]},
    {"sign": "ikizler", "en": "gemini", "start": (5, 21), "end": (6, 20),
     "element": "hava", "planet": "merkur",
     "traits": ["iletisimci", "merakli", "uyumlu", "degisken"]},
    {"sign": "yengec", "en": "cancer", "start": (6, 21), "end": (7, 22),
     "element": "su", "planet": "ay",
     "traits": ["koruyucu", "duygusal", "sezgisel", "hassas"]},
    {"sign": "aslan", "en": "leo", "start": (7, 23), "end": (8, 22),
     "element": "ates", "planet": "gunes",
     "traits": ["karizmatik", "yaratici", "comert", "gurur"]},
    {"sign": "basak", "en": "virgo", "start": (8, 23), "end": (9, 22),
     "element": "toprak", "planet": "merkur",
     "traits": ["analizci", "titiz", "yardımsever", "elestirmen"]},
    {"sign": "terazi", "en": "libra", "start": (9, 23), "end": (10, 22),
     "element": "hava", "planet": "venus",
     "traits": ["adil", "diplomatik", "uyumlu", "kararsiz"]},
    {"sign": "akrep", "en": "scorpio", "start": (10, 23), "end": (11, 21),
     "element": "su", "planet": "pluto",
     "traits": ["tutkulu", "kararli", "sezgisel", "gizemli"]},
    {"sign": "yay", "en": "sagittarius", "start": (11, 22), "end": (12, 21),
     "element": "ates", "planet": "jupiter",
     "traits": ["maceracı", "iyimser", "felsefi", "sabırsız"]},
    {"sign": "oglak", "en": "capricorn", "start": (12, 22), "end": (1, 19),
     "element": "toprak", "planet": "saturn",
     "traits": ["disiplinli", "hırsli", "sorumlu", "mesafeli"]},
    {"sign": "kova", "en": "aquarius", "start": (1, 20), "end": (2, 18),
     "element": "hava", "planet": "uranus",
     "traits": ["yenilikci", "bagimsiz", "insancil", "asi"]},
    {"sign": "balik", "en": "pisces", "start": (2, 19), "end": (3, 20),
     "element": "su", "planet": "neptun",
     "traits": ["hayalperest", "empatik", "yaratici", "kacis"]},
]

_QUOTES_DB: dict[str, list[dict[str, str]]] = {
    "motivasyon": [
        {"quote": "Basarinin sirri, her gun biraz daha iyi olmaktir.", "author": "Anonim"},
        {"quote": "Buyuk isler, kucuk adimlarla baslar.", "author": "Lao Tzu"},
        {"quote": "Hayal edebildigin her sey gercektir.", "author": "Pablo Picasso"},
        {"quote": "Yapamam demeyi birak, nasil yaparim de.", "author": "Anonim"},
    ],
    "liderlik": [
        {"quote": "Liderlik bir konum degil, bir eylemdir.", "author": "Anonim"},
        {"quote": "Ornek olarak liderlik edin.", "author": "Mahatma Gandhi"},
        {"quote": "Iyi bir lider iyi bir dinleyicidir.", "author": "Anonim"},
    ],
    "basari": [
        {"quote": "Basari, hazirlik firsatla bulustiginda olusur.", "author": "Seneca"},
        {"quote": "Basarisizlik basarinin annebabasidir.", "author": "Anonim"},
        {"quote": "Her usta once ogrenciydi.", "author": "Anonim"},
    ],
    "yasam": [
        {"quote": "Hayat, nefes aldigin anlar degil, nefesini kesen anlardir.", "author": "Anonim"},
        {"quote": "Bugunu yasayin, yarin belli degil.", "author": "Horatius"},
        {"quote": "Mutluluk bir yolculuktur, varis noktasi degil.", "author": "Anonim"},
    ],
    "bilim": [
        {"quote": "Hayal gucu bilgiden daha onemlidir.", "author": "Albert Einstein"},
        {"quote": "Bilim, duzenli dusuncenin en guzel bicimidir.", "author": "Anonim"},
    ],
}

_RECIPE_DB = [
    {"name": "Menemen", "cuisine": "turk", "time": 15, "calories": 250,
     "ingredients": ["yumurta", "domates", "biber", "sogan"],
     "dietary": ["vegetarian"], "steps": ["Sogan kavur", "Biber ekle", "Domates ekle", "Yumurta kir"]},
    {"name": "Mercimek Corbasi", "cuisine": "turk", "time": 30, "calories": 180,
     "ingredients": ["kirmizi_mercimek", "sogan", "havuc", "patates"],
     "dietary": ["vegan", "vegetarian"], "steps": ["Kaynat", "Blend et", "Baharat ekle"]},
    {"name": "Tavuk Salata", "cuisine": "universal", "time": 15, "calories": 350,
     "ingredients": ["tavuk", "marul", "domates", "salatalik"],
     "dietary": ["gluten_free"], "steps": ["Tavugu pişir", "Sebzeleri dogra", "Karistir"]},
    {"name": "Makarna", "cuisine": "italyan", "time": 20, "calories": 400,
     "ingredients": ["makarna", "domates_sosu", "sarimsak", "zeytinyagi"],
     "dietary": ["vegetarian"], "steps": ["Makarna pisir", "Sos hazirla", "Birlestir"]},
    {"name": "Smoothie", "cuisine": "universal", "time": 5, "calories": 200,
     "ingredients": ["muz", "cilek", "sut", "bal"],
     "dietary": ["vegetarian", "gluten_free"], "steps": ["Hepsini blender'a koy", "Blend et"]},
]


# ────────────────────────────────────────────────────────────────────────────
# 201 — todo_manager
# ────────────────────────────────────────────────────────────────────────────
class TodoManager(BaseSkill):
    """Yapilacaklar listesi yonetimi."""

    SKILL_ID = "201"
    NAME = "todo_manager"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Yapilacaklar listesi (ekle, tamamla, listele, onceliklendir)"
    PARAMETERS = {
        "action": "Islem (add/complete/list/delete/prioritize)",
        "task": "Gorev metni",
        "priority": "Oncelik (high/medium/low)",
        "due_date": "Son tarih (YYYY-MM-DD)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        action = str(params.get("action", "list")).lower()
        task_text = str(params.get("task", ""))
        priority = str(params.get("priority", "medium")).lower()
        due_date = str(params.get("due_date", ""))

        if "todos" not in self.records:
            self.records["todos"] = []

        todos: list[dict[str, Any]] = self.records["todos"]

        if action == "add":
            if not task_text:
                return {"status": "error", "message": "Gorev metni gerekli"}
            item = {
                "id": len(todos) + 1,
                "task": task_text,
                "priority": priority,
                "due_date": due_date,
                "completed": False,
                "created_at": datetime.now().isoformat(),
            }
            todos.append(item)
            return {"status": "success", "action": "added", "item": item, "total": len(todos)}

        if action == "complete":
            task_id = int(params.get("task_id", params.get("id", 0)))
            for t in todos:
                if t["id"] == task_id:
                    t["completed"] = True
                    t["completed_at"] = datetime.now().isoformat()
                    return {"status": "success", "action": "completed", "item": t}
            return {"status": "error", "message": f"Gorev #{task_id} bulunamadi"}

        if action == "delete":
            task_id = int(params.get("task_id", params.get("id", 0)))
            for i, t in enumerate(todos):
                if t["id"] == task_id:
                    removed = todos.pop(i)
                    return {"status": "success", "action": "deleted", "item": removed}
            return {"status": "error", "message": f"Gorev #{task_id} bulunamadi"}

        if action == "prioritize":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            active = [t for t in todos if not t["completed"]]
            active.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 1))
            return {"status": "success", "action": "prioritized", "tasks": active}

        # list
        active = [t for t in todos if not t["completed"]]
        completed = [t for t in todos if t["completed"]]
        return {
            "status": "success",
            "active_count": len(active),
            "completed_count": len(completed),
            "active_tasks": active,
            "completed_tasks": completed,
        }


# ────────────────────────────────────────────────────────────────────────────
# 202 — habit_tracker
# ────────────────────────────────────────────────────────────────────────────
class HabitTracker(BaseSkill):
    """Aliskanlik takibi."""

    SKILL_ID = "202"
    NAME = "habit_tracker"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Aliskanlik takibi (streak, istatistik, hatirlatma)"
    PARAMETERS = {
        "habit": "Aliskanlik adi",
        "action": "Islem (check/stats/list/add)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        action = str(params.get("action", "list")).lower()
        habit_name = str(params.get("habit", ""))

        if "habits" not in self.records:
            self.records["habits"] = {}

        habits: dict[str, dict[str, Any]] = self.records["habits"]

        if action == "add":
            if not habit_name:
                return {"status": "error", "message": "Aliskanlik adi gerekli"}
            habits[habit_name] = {
                "name": habit_name,
                "checks": [],
                "streak": 0,
                "best_streak": 0,
                "created_at": datetime.now().isoformat(),
            }
            return {"status": "success", "action": "added", "habit": habit_name}

        if action == "check":
            if habit_name not in habits:
                habits[habit_name] = {
                    "name": habit_name, "checks": [],
                    "streak": 0, "best_streak": 0,
                    "created_at": datetime.now().isoformat(),
                }
            h = habits[habit_name]
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in h["checks"]:
                h["checks"].append(today)
                # Streak hesapla
                streak = 1
                checks_sorted = sorted(h["checks"], reverse=True)
                for i in range(1, len(checks_sorted)):
                    d1 = datetime.strptime(checks_sorted[i - 1], "%Y-%m-%d")
                    d2 = datetime.strptime(checks_sorted[i], "%Y-%m-%d")
                    if (d1 - d2).days == 1:
                        streak += 1
                    else:
                        break
                h["streak"] = streak
                h["best_streak"] = max(h["best_streak"], streak)
            return {
                "status": "success", "action": "checked", "habit": habit_name,
                "streak": h["streak"], "best_streak": h["best_streak"],
                "total_checks": len(h["checks"]),
            }

        if action == "stats":
            if habit_name not in habits:
                return {"status": "error", "message": f"'{habit_name}' bulunamadi"}
            h = habits[habit_name]
            total = len(h["checks"])
            created = h.get("created_at", datetime.now().isoformat())
            days_since = max(1, (datetime.now() - datetime.fromisoformat(created)).days)
            return {
                "status": "success", "habit": habit_name,
                "total_checks": total, "streak": h["streak"],
                "best_streak": h["best_streak"],
                "completion_rate": round(total / days_since * 100, 1),
                "days_tracked": days_since,
            }

        # list
        return {
            "status": "success",
            "habits": [
                {"name": n, "streak": h["streak"], "total": len(h["checks"])}
                for n, h in habits.items()
            ],
            "count": len(habits),
        }


# ────────────────────────────────────────────────────────────────────────────
# 203 — pomodoro_timer
# ────────────────────────────────────────────────────────────────────────────
class PomodoroTimer(BaseSkill):
    """Pomodoro teknigi zamanlayici."""

    SKILL_ID = "203"
    NAME = "pomodoro_timer"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Pomodoro teknigi zamanlayici (25 dk calisma + 5 dk mola)"
    PARAMETERS = {
        "work_minutes": "Calisma suresi (varsayilan 25)",
        "break_minutes": "Mola suresi (varsayilan 5)",
        "sessions": "Oturum sayisi (varsayilan 4)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        work = int(params.get("work_minutes", 25))
        brk = int(params.get("break_minutes", 5))
        sessions = int(params.get("sessions", 4))
        long_break = brk * 3  # 4 oturum sonrasi uzun mola

        schedule: list[dict[str, Any]] = []
        now = datetime.now()
        current = now

        for i in range(1, sessions + 1):
            # Calisma
            work_start = current
            work_end = current + timedelta(minutes=work)
            schedule.append({
                "session": i, "type": "work",
                "start": work_start.strftime("%H:%M"),
                "end": work_end.strftime("%H:%M"),
                "duration_min": work,
            })
            current = work_end
            # Mola
            if i < sessions:
                break_dur = brk
            else:
                break_dur = long_break
            break_end = current + timedelta(minutes=break_dur)
            schedule.append({
                "session": i, "type": "long_break" if i == sessions else "break",
                "start": current.strftime("%H:%M"),
                "end": break_end.strftime("%H:%M"),
                "duration_min": break_dur,
            })
            current = break_end

        total_work = work * sessions
        total_break = brk * (sessions - 1) + long_break
        finish_time = now + timedelta(minutes=total_work + total_break)

        return {
            "status": "success",
            "sessions": sessions,
            "work_minutes": work,
            "break_minutes": brk,
            "long_break_minutes": long_break,
            "total_work_minutes": total_work,
            "total_break_minutes": total_break,
            "total_duration_minutes": total_work + total_break,
            "start_time": now.strftime("%H:%M"),
            "finish_time": finish_time.strftime("%H:%M"),
            "schedule": schedule,
        }


# ────────────────────────────────────────────────────────────────────────────
# 204 — decision_maker
# ────────────────────────────────────────────────────────────────────────────
class DecisionMaker(BaseSkill):
    """Karar verme yardimcisi."""

    SKILL_ID = "204"
    NAME = "decision_maker"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Karar verme yardimcisi (pros-cons, MECE, karar matrisi)"
    PARAMETERS = {
        "options": "Secenekler listesi",
        "criteria": "Degerlendirme kriterleri",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        options = params.get("options", [])
        criteria = params.get("criteria", [])

        if isinstance(options, str):
            options = [o.strip() for o in options.split(",") if o.strip()]
        if isinstance(criteria, str):
            criteria = [c.strip() for c in criteria.split(",") if c.strip()]

        if not options:
            return {"status": "error", "message": "En az bir secenek gerekli"}

        if not criteria:
            criteria = ["maliyet", "zaman", "kalite", "risk"]

        # Deterministik skor ureti
        matrix: list[dict[str, Any]] = []
        for opt in options:
            scores: dict[str, float] = {}
            seed = int(hashlib.md5(opt.encode()).hexdigest()[:8], 16)
            rng = random.Random(seed)
            total = 0.0
            for c in criteria:
                score = round(rng.uniform(3.0, 10.0), 1)
                scores[c] = score
                total += score
            avg = round(total / len(criteria), 2)
            matrix.append({"option": opt, "scores": scores, "average": avg})

        matrix.sort(key=lambda x: x["average"], reverse=True)
        winner = matrix[0]

        return {
            "status": "success",
            "method": "decision_matrix",
            "criteria": criteria,
            "evaluation": matrix,
            "recommendation": winner["option"],
            "recommendation_score": winner["average"],
            "note": "Puanlar ornek icin uretilmistir. Gercek puanlari kendiniz girebilirsiniz.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 205 — brainstorm_helper
# ────────────────────────────────────────────────────────────────────────────
class BrainstormHelper(BaseSkill):
    """Beyin firtinasi asistani."""

    SKILL_ID = "205"
    NAME = "brainstorm_helper"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Beyin firtinasi asistani (SCAMPER, 6 sapka, mind map)"
    PARAMETERS = {
        "topic": "Konu",
        "method": "Yontem (scamper/six_hats/random/mind_map)",
        "count": "Fikir sayisi",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        topic = str(params.get("topic", "yeni urun"))
        method = str(params.get("method", "scamper")).lower()
        count = int(params.get("count", 7))

        if method == "scamper":
            scamper = {
                "S - Substitute (Degistir)": f"'{topic}' icinde neyi baska bir seyle degistirebiliriz?",
                "C - Combine (Birlestir)": f"'{topic}' ile baska neyi birlestirebiliriz?",
                "A - Adapt (Uyarla)": f"'{topic}' baska hangi alandan ilham alabilir?",
                "M - Modify (Duzelt)": f"'{topic}' nasil buyutulup/kucultulup/sekil degistirilebilir?",
                "P - Put to other use (Baska amac)": f"'{topic}' baska ne icin kullanilabilir?",
                "E - Eliminate (Cikar)": f"'{topic}' icinden ne cikarilabilir?",
                "R - Reverse (Ters cevir)": f"'{topic}' ters cevirilse nasil olur?",
            }
            return {"status": "success", "method": "SCAMPER", "topic": topic, "prompts": scamper}

        if method == "six_hats":
            hats = {
                "Beyaz Sapka (Veri)": f"'{topic}' hakkinda elimizdeki veriler neler?",
                "Kirmizi Sapka (Duygu)": f"'{topic}' hakkinda ne hissediyoruz?",
                "Siyah Sapka (Elestiri)": f"'{topic}' ile ilgili riskler ve sorunlar neler?",
                "Sari Sapka (Iyimserlik)": f"'{topic}' en iyi senaryoda nasil olur?",
                "Yesil Sapka (Yaraticilik)": f"'{topic}' icin en yaratici cozum ne?",
                "Mavi Sapka (Kontrol)": f"'{topic}' surecini nasil yonetmeliyiz?",
            }
            return {"status": "success", "method": "6_sapka", "topic": topic, "perspectives": hats}

        if method == "mind_map":
            branches = [
                {"branch": "Sorun", "sub": ["mevcut_durum", "kisitlar", "firsatlar"]},
                {"branch": "Hedef Kitle", "sub": ["demografik", "ihtiyaclar", "beklentiler"]},
                {"branch": "Cozumler", "sub": ["teknoloji", "surec", "insan"]},
                {"branch": "Kaynaklar", "sub": ["butce", "zaman", "ekip"]},
                {"branch": "Sonraki Adimlar", "sub": ["prototip", "test", "lansman"]},
            ]
            return {"status": "success", "method": "mind_map", "topic": topic, "branches": branches}

        # random
        templates = [
            f"Ya '{topic}' tam tersini yapsak?",
            f"'{topic}' 10 yil sonra nasil olur?",
            f"'{topic}' bir cocuk nasil cozerdi?",
            f"'{topic}' icin en ucuz cozum ne?",
            f"'{topic}' icin en luks cozum ne?",
            f"'{topic}' baska bir sektorde nasil uygulanir?",
            f"'{topic}' 5 dakikada nasil cozulur?",
            f"'{topic}' icin teknolojiyi kaldırsak ne olur?",
            f"'{topic}' hakkinda en cılgin fikir ne?",
            f"'{topic}' icin doga nasil bir cozum sunar?",
        ]
        seed = int(hashlib.md5(topic.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        ideas = rng.sample(templates, min(count, len(templates)))
        return {"status": "success", "method": "random_prompts", "topic": topic, "ideas": ideas}


# ────────────────────────────────────────────────────────────────────────────
# 206 — goal_setter
# ────────────────────────────────────────────────────────────────────────────
class GoalSetter(BaseSkill):
    """SMART hedef olusturma."""

    SKILL_ID = "206"
    NAME = "goal_setter"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "SMART hedef olusturma"
    PARAMETERS = {"rough_goal": "Kaba hedef ifadesi"}

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        rough = str(params.get("rough_goal", "daha iyi olmak"))

        smart = {
            "original": rough,
            "S_specific": f"'{rough}' hedefini somut olarak tanimlayın: Ne yapmak istiyorsunuz?",
            "M_measurable": "Basariyi nasil olceceksiniz? Hangi metrikler?",
            "A_achievable": "Bu hedefe ulasmak icin kaynaklar ve yetenekler yeterli mi?",
            "R_relevant": "Bu hedef daha buyuk vizyonunuzla nasil baglantili?",
            "T_time_bound": "Son tarih nedir? Kilometre taslari neler?",
            "example_smart": f"Ornek: '3 ay icinde {rough} hedefine yonelik haftalik 3 saat calisarak, X metrigini Y'den Z'ye cikarmak'",
            "milestones": [
                {"week": 1, "action": "Mevcut durumu analiz et"},
                {"week": 2, "action": "Aksiyon plani olustur"},
                {"week": 4, "action": "Ilk ilerlemeyi olc"},
                {"week": 8, "action": "Ortasi degerlendirme"},
                {"week": 12, "action": "Son degerlendirme"},
            ],
        }
        return {"status": "success", "smart_framework": smart}


# ────────────────────────────────────────────────────────────────────────────
# 207 — priority_matrix
# ────────────────────────────────────────────────────────────────────────────
class PriorityMatrix(BaseSkill):
    """Eisenhower matrisi ile onceliklendirme."""

    SKILL_ID = "207"
    NAME = "priority_matrix"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Eisenhower matrisi ile onceliklendirme"
    PARAMETERS = {"tasks": "Gorev listesi (virgul ile ayrilmis veya dizi)"}

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        tasks = params.get("tasks", [])
        if isinstance(tasks, str):
            tasks = [t.strip() for t in tasks.split(",") if t.strip()]

        if not tasks:
            return {"status": "error", "message": "En az bir gorev gerekli"}

        # Deterministik atama
        quadrants: dict[str, list[str]] = {
            "Q1_urgent_important": [],
            "Q2_not_urgent_important": [],
            "Q3_urgent_not_important": [],
            "Q4_not_urgent_not_important": [],
        }
        q_names = list(quadrants.keys())

        for i, task in enumerate(tasks):
            seed = int(hashlib.md5(task.encode()).hexdigest()[:8], 16)
            q = q_names[seed % 4]
            quadrants[q].append(task)

        return {
            "status": "success",
            "method": "eisenhower_matrix",
            "matrix": {
                "Q1 - Yap (Acil + Onemli)": quadrants["Q1_urgent_important"],
                "Q2 - Planla (Onemli + Acil Degil)": quadrants["Q2_not_urgent_important"],
                "Q3 - Delege Et (Acil + Onemli Degil)": quadrants["Q3_urgent_not_important"],
                "Q4 - Eleme (Acil Degil + Onemli Degil)": quadrants["Q4_not_urgent_not_important"],
            },
            "total_tasks": len(tasks),
            "recommendation": "Oncelikle Q1 gorevlerine odaklanin, ardindan Q2 icin plan yapin.",
            "note": "Gorevleri dogru kadrana siz atayabilirsiniz, bu ornek dagilimdir.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 208 — journal_prompt
# ────────────────────────────────────────────────────────────────────────────
class JournalPrompt(BaseSkill):
    """Gunluk yazma soruları ve yonlendirmeleri."""

    SKILL_ID = "208"
    NAME = "journal_prompt"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Gunluk yazma sorulari ve yonlendirmeleri"
    PARAMETERS = {
        "mood": "Ruh hali (happy/sad/anxious/grateful/neutral)",
        "focus_area": "Odak alani (growth/relationships/career/health/creativity)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        mood = str(params.get("mood", "neutral")).lower()
        focus = str(params.get("focus_area", "growth")).lower()

        prompts_by_mood = {
            "happy": [
                "Bugun seni en cok ne mutlu etti?",
                "Bu mutlulugu nasil surdurebilirsin?",
                "Kime tesekkur etmek istersin?",
            ],
            "sad": [
                "Simdi nasil hissediyorsun? Duygularini tanimla.",
                "Kendine ne soylemek istersin?",
                "Kucuk bir sey yap: bir bardak su ic, pencereden bak.",
            ],
            "anxious": [
                "Endiseni somutlastir: tam olarak ne seni kaygilandiriyor?",
                "Bu kayginin gerceklesme olasiligi ne?",
                "Simdi kontrol edebildigin bir sey ne?",
            ],
            "grateful": [
                "Bugun minnettarlik duydugu 3 sey yaz.",
                "Hayatindaki kim icin minnettarsin ve neden?",
                "Sahip oldugunu ama gormezden geldigin bir nimet ne?",
            ],
            "neutral": [
                "Bugun nasil bir gun gecirdin?",
                "Onumuzdeki haftanin en onemli hedefi ne?",
                "Simdi ne yapmak istiyorsun?",
            ],
        }

        prompts_by_focus = {
            "growth": ["Bu ay ne ogrendin?", "Hangi aliskanligini degistirmek istiyorsun?"],
            "relationships": ["En yakin iliskilerinde nasil daha iyi olabilirsin?", "Kimi arayabilirsin bugun?"],
            "career": ["Kariyerinde bir sonraki adim ne?", "En buyuk is zorlugun ne?"],
            "health": ["Bu hafta bedenine nasil baktin?", "Uyku duzenin nasil?"],
            "creativity": ["Son zamanlarda ilham veren sey ne?", "Yeni bir sey deneseydin ne olurdu?"],
        }

        selected_mood = prompts_by_mood.get(mood, prompts_by_mood["neutral"])
        selected_focus = prompts_by_focus.get(focus, prompts_by_focus["growth"])

        return {
            "status": "success",
            "mood": mood,
            "focus_area": focus,
            "prompts": selected_mood + selected_focus,
            "writing_tip": "En az 5 dakika kesintisiz yaz. Dilbilgisi ve imla dusunme.",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }


# ────────────────────────────────────────────────────────────────────────────
# 209 — affirmation_generator
# ────────────────────────────────────────────────────────────────────────────
class AffirmationGenerator(BaseSkill):
    """Pozitif olumlama cumleleri."""

    SKILL_ID = "209"
    NAME = "affirmation_generator"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Pozitif olumlama cumleleri"
    PARAMETERS = {
        "theme": "Tema (confidence/success/health/love/wealth/peace)",
        "count": "Sayi (varsayilan 5)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        theme = str(params.get("theme", "confidence")).lower()
        count = int(params.get("count", 5))

        affirmations_db: dict[str, list[str]] = {
            "confidence": [
                "Ben degerli ve yeterliyim.",
                "Kendime guveniyorum.",
                "Her gun daha guclu oluyorum.",
                "Zorluklari firsata cevirebilirim.",
                "Sesimi duyurmaya hakkim var.",
                "Hatalarim beni tanimlamaz, ogretir.",
            ],
            "success": [
                "Basari benim dogal halim.",
                "Her adim beni hedefe yaklastiriyor.",
                "Firsatlar beni buluyor.",
                "Cok calisiyorum ve karsiligi geliyor.",
                "Buyuk hedefler koyabilir ve basarabilirim.",
                "Bugunku eylemlerim yarinin basarisini insa ediyor.",
            ],
            "health": [
                "Bedenim guclu ve saglikli.",
                "Saglığıma yatirim yapıyorum.",
                "Iyi secimler yapiyorum.",
                "Kendime bakmak oncelik.",
                "Her gun biraz daha iyi hissediyorum.",
            ],
            "love": [
                "Sevgi vermeye ve almaya layigim.",
                "Etrafimda sevgi dolu insanlar var.",
                "Iliskilerime deger katiyorum.",
                "Empati ve anlayis gosteriyorum.",
                "Kendimi oldugum gibi seviyorum.",
            ],
            "wealth": [
                "Bolluğu hak ediyorum.",
                "Para bana kolaylikla geliyor.",
                "Finansal ozgurluge dogru ilerliyorum.",
                "Akilli yatirimlar yapiyorum.",
                "Degere deger katiyorum.",
            ],
            "peace": [
                "Ic huzur icindeyim.",
                "Kontrolum disindaki seyleri birakiyorum.",
                "Bu an icin minnettarim.",
                "Nefes aliyorum ve rahatim.",
                "Hayat benim icin akiyor.",
            ],
        }

        pool = affirmations_db.get(theme, affirmations_db["confidence"])
        selected = pool[:min(count, len(pool))]

        return {
            "status": "success",
            "theme": theme,
            "affirmations": selected,
            "tip": "Her sabah ayna karsisinda sesli oku. 21 gun tekrarla.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 210 — recipe_finder
# ────────────────────────────────────────────────────────────────────────────
class RecipeFinder(BaseSkill):
    """Tarif bulma."""

    SKILL_ID = "210"
    NAME = "recipe_finder"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Tarif bulma (malzemeye gore, kisitlamaya gore)"
    PARAMETERS = {
        "ingredients": "Mevcut malzemeler",
        "dietary_restrictions": "Diyet kisitlari (vegan/vegetarian/gluten_free)",
        "cuisine": "Mutfak (turk/italyan/universal)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        ingredients = params.get("ingredients", [])
        dietary = str(params.get("dietary_restrictions", "")).lower()
        cuisine = str(params.get("cuisine", "")).lower()

        if isinstance(ingredients, str):
            ingredients = [i.strip().lower() for i in ingredients.split(",") if i.strip()]

        results = []
        for recipe in _RECIPE_DB:
            # Mutfak filtresi
            if cuisine and recipe["cuisine"] != cuisine and recipe["cuisine"] != "universal":
                continue
            # Diyet filtresi
            if dietary and dietary not in recipe.get("dietary", []):
                continue
            # Malzeme eslesmesi
            if ingredients:
                match_count = sum(1 for ing in ingredients if any(ing in r for r in recipe["ingredients"]))
                match_pct = match_count / len(recipe["ingredients"]) * 100
            else:
                match_pct = 100.0

            if match_pct > 0 or not ingredients:
                results.append({
                    **recipe,
                    "match_percentage": round(match_pct, 1),
                })

        results.sort(key=lambda x: x["match_percentage"], reverse=True)

        return {
            "status": "success",
            "query": {"ingredients": ingredients, "dietary": dietary, "cuisine": cuisine},
            "recipes": results[:10],
            "total_found": len(results),
        }


# ────────────────────────────────────────────────────────────────────────────
# 211 — meal_planner
# ────────────────────────────────────────────────────────────────────────────
class MealPlanner(BaseSkill):
    """Haftalik yemek plani."""

    SKILL_ID = "211"
    NAME = "meal_planner"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Haftalik yemek plani"
    PARAMETERS = {
        "preferences": "Tercihler",
        "restrictions": "Kisitlamalar",
        "budget": "Butce seviyesi (low/medium/high)",
        "people_count": "Kisi sayisi",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        people = int(params.get("people_count", 1))
        budget = str(params.get("budget", "medium")).lower()

        days = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]
        meals_db = {
            "kahvalti": ["Yumurta & peynir", "Yulaf lapasi", "Tost", "Menemen", "Musli", "Pankek", "Acma & cay"],
            "ogle": ["Tavuk salata", "Mercimek corbasi", "Makarna", "Pilav & fasulye", "Sandvic", "Wrap", "Pizza"],
            "aksam": ["Izgara tavuk", "Kofte", "Sebze sote", "Balik", "Etli nohut", "Karniyarik", "Lahmacun"],
        }

        plan: list[dict[str, Any]] = []
        daily_cal = 2000 if budget != "low" else 1800
        for i, day in enumerate(days):
            plan.append({
                "day": day,
                "kahvalti": meals_db["kahvalti"][i % len(meals_db["kahvalti"])],
                "ogle": meals_db["ogle"][i % len(meals_db["ogle"])],
                "aksam": meals_db["aksam"][i % len(meals_db["aksam"])],
                "estimated_calories": daily_cal,
            })

        budget_map = {"low": 50, "medium": 100, "high": 200}
        weekly_budget = budget_map.get(budget, 100) * people

        return {
            "status": "success",
            "people_count": people,
            "budget_level": budget,
            "estimated_weekly_cost_tl": weekly_budget,
            "weekly_plan": plan,
            "shopping_tip": "Haftalik toplu alisveris yaparak %20-30 tasarruf edebilirsiniz.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 212 — calorie_calculator
# ────────────────────────────────────────────────────────────────────────────
class CalorieCalculator(BaseSkill):
    """Kalori hesaplama."""

    SKILL_ID = "212"
    NAME = "calorie_calculator"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kalori hesaplama (yemek veya gunluk ihtiyac)"
    PARAMETERS = {
        "food": "Yemek adi (opsiyonel)",
        "age": "Yas", "weight": "Kilo (kg)", "height": "Boy (cm)",
        "activity_level": "Aktivite (sedentary/light/moderate/active/very_active)",
        "gender": "Cinsiyet (male/female)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        food = params.get("food")
        if food:
            # Basit yemek kalori veritabani
            food_db: dict[str, int] = {
                "elma": 95, "muz": 105, "portakal": 62, "yumurta": 78,
                "ekmek": 79, "pilav": 206, "tavuk_gogsu": 165, "makarna": 220,
                "salata": 50, "corba": 120, "peynir": 113, "sut": 149,
                "yogurt": 100, "bal": 64, "cay": 2, "kahve": 5,
            }
            food_lower = str(food).lower().replace(" ", "_")
            cal = food_db.get(food_lower)
            if cal:
                return {"status": "success", "food": food, "calories": cal, "unit": "1 porsiyon"}
            return {"status": "success", "food": food, "calories": "bilinmiyor",
                    "available_foods": list(food_db.keys())}

        # BMR hesaplama (Mifflin-St Jeor)
        age = int(params.get("age", 30))
        weight = float(params.get("weight", 70))
        height = float(params.get("height", 170))
        gender = str(params.get("gender", "male")).lower()
        activity = str(params.get("activity_level", "moderate")).lower()

        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        multipliers = {
            "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
            "active": 1.725, "very_active": 1.9,
        }
        mult = multipliers.get(activity, 1.55)
        tdee = round(bmr * mult)

        return {
            "status": "success",
            "bmr": round(bmr),
            "tdee": tdee,
            "activity_level": activity,
            "maintain_weight": tdee,
            "lose_weight": tdee - 500,
            "gain_weight": tdee + 500,
            "macros_balanced": {
                "protein_g": round(tdee * 0.3 / 4),
                "carbs_g": round(tdee * 0.4 / 4),
                "fat_g": round(tdee * 0.3 / 9),
            },
        }


# ────────────────────────────────────────────────────────────────────────────
# 213 — bmi_calculator
# ────────────────────────────────────────────────────────────────────────────
class BmiCalculator(BaseSkill):
    """Vucut kitle indeksi."""

    SKILL_ID = "213"
    NAME = "bmi_calculator"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Vucut kitle indeksi"
    PARAMETERS = {"weight_kg": "Kilo (kg)", "height_cm": "Boy (cm)"}

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        weight = float(params.get("weight_kg", 70))
        height_cm = float(params.get("height_cm", 170))
        height_m = height_cm / 100

        bmi = round(weight / (height_m ** 2), 1)

        if bmi < 18.5:
            category = "Zayif"
            advice = "Saglikli kilo almak icin beslenme uzmani ile gorusun."
        elif bmi < 25:
            category = "Normal"
            advice = "Saglikli araliktasiniz. Dengenizi koruyun."
        elif bmi < 30:
            category = "Fazla Kilolu"
            advice = "Duzenlı egzersiz ve dengeli beslenme onerilir."
        else:
            category = "Obez"
            advice = "Bir saglik uzmani ile gorusmeniz onerilir."

        ideal_min = round(18.5 * (height_m ** 2), 1)
        ideal_max = round(24.9 * (height_m ** 2), 1)

        return {
            "status": "success",
            "bmi": bmi,
            "category": category,
            "weight_kg": weight,
            "height_cm": height_cm,
            "ideal_weight_range_kg": {"min": ideal_min, "max": ideal_max},
            "advice": advice,
            "note": "BMI genel bir gostergedir. Kas kutlesi, yas ve cinsiyet etkileyebilir.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 214 — workout_generator
# ────────────────────────────────────────────────────────────────────────────
class WorkoutGenerator(BaseSkill):
    """Egzersiz programi olusturma."""

    SKILL_ID = "214"
    NAME = "workout_generator"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Egzersiz programi olusturma"
    PARAMETERS = {
        "goal": "Hedef (lose_weight/build_muscle/cardio/flexibility)",
        "experience_level": "Seviye (beginner/intermediate/advanced)",
        "equipment": "Ekipman (none/basic/full_gym)",
        "duration": "Sure (dakika)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        goal = str(params.get("goal", "lose_weight")).lower()
        level = str(params.get("experience_level", "beginner")).lower()
        equip = str(params.get("equipment", "none")).lower()
        duration = int(params.get("duration", 30))

        exercises_db = {
            "lose_weight": {
                "none": [
                    {"name": "Jumping Jack", "sets": 3, "reps": "30 sn"},
                    {"name": "Squat", "sets": 3, "reps": 15},
                    {"name": "Burpee", "sets": 3, "reps": 10},
                    {"name": "Mountain Climber", "sets": 3, "reps": "30 sn"},
                    {"name": "Plank", "sets": 3, "reps": "30 sn"},
                ],
                "basic": [
                    {"name": "Jump Rope", "sets": 3, "reps": "1 dk"},
                    {"name": "Kettlebell Swing", "sets": 3, "reps": 15},
                    {"name": "Dumbbell Squat", "sets": 3, "reps": 12},
                    {"name": "Band Row", "sets": 3, "reps": 12},
                ],
            },
            "build_muscle": {
                "none": [
                    {"name": "Push-up", "sets": 4, "reps": 12},
                    {"name": "Diamond Push-up", "sets": 3, "reps": 10},
                    {"name": "Squat", "sets": 4, "reps": 15},
                    {"name": "Lunge", "sets": 3, "reps": "12 per leg"},
                    {"name": "Plank", "sets": 3, "reps": "45 sn"},
                ],
                "full_gym": [
                    {"name": "Bench Press", "sets": 4, "reps": 10},
                    {"name": "Squat", "sets": 4, "reps": 10},
                    {"name": "Deadlift", "sets": 3, "reps": 8},
                    {"name": "Pull-up", "sets": 3, "reps": 8},
                    {"name": "Shoulder Press", "sets": 3, "reps": 10},
                ],
            },
            "cardio": {
                "none": [
                    {"name": "Yerinde Kosu", "sets": 1, "reps": "5 dk"},
                    {"name": "High Knees", "sets": 3, "reps": "30 sn"},
                    {"name": "Burpee", "sets": 3, "reps": 10},
                    {"name": "Jumping Jack", "sets": 3, "reps": "1 dk"},
                ],
            },
            "flexibility": {
                "none": [
                    {"name": "Hamstring Stretch", "sets": 2, "reps": "30 sn"},
                    {"name": "Quad Stretch", "sets": 2, "reps": "30 sn"},
                    {"name": "Cat-Cow", "sets": 2, "reps": 10},
                    {"name": "Child's Pose", "sets": 2, "reps": "30 sn"},
                    {"name": "Downward Dog", "sets": 2, "reps": "30 sn"},
                ],
            },
        }

        goal_exercises = exercises_db.get(goal, exercises_db["lose_weight"])
        workout = goal_exercises.get(equip, goal_exercises.get("none", []))

        # Seviyeye gore ayarla
        if level == "beginner":
            for ex in workout:
                if isinstance(ex["reps"], int):
                    ex["reps"] = max(5, ex["reps"] - 3)
                ex["sets"] = max(2, ex["sets"] - 1)
        elif level == "advanced":
            for ex in workout:
                if isinstance(ex["reps"], int):
                    ex["reps"] += 5
                ex["sets"] += 1

        return {
            "status": "success",
            "goal": goal,
            "level": level,
            "equipment": equip,
            "duration_minutes": duration,
            "warmup": "5 dakika hafif kosu veya yuruyus",
            "exercises": workout,
            "cooldown": "5 dakika germe hareketleri",
            "estimated_calories_burned": duration * (8 if goal == "cardio" else 6),
            "frequency": "Haftada 3-4 gun",
        }


# ────────────────────────────────────────────────────────────────────────────
# 215 — sleep_calculator
# ────────────────────────────────────────────────────────────────────────────
class SleepCalculator(BaseSkill):
    """Uyku dongusu hesaplama."""

    SKILL_ID = "215"
    NAME = "sleep_calculator"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Uyku dongusu hesaplama (ideal yatis/kalkis saati)"
    PARAMETERS = {
        "wake_time": "Kalkis saati (HH:MM)",
        "bed_time": "Yatis saati (HH:MM, opsiyonel)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        cycle_min = 90  # Bir uyku dongusu
        fall_asleep_min = 15  # Uykuya dalma suresi

        wake_time = params.get("wake_time")
        bed_time = params.get("bed_time")

        if wake_time:
            # Kalkis saatine gore yatis saatleri hesapla
            parts = str(wake_time).split(":")
            wake_h, wake_m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            wake_total = wake_h * 60 + wake_m

            suggestions = []
            for cycles in [6, 5, 4]:
                sleep_needed = cycles * cycle_min + fall_asleep_min
                bed_total = (wake_total - sleep_needed) % 1440
                bed_h, bed_m = divmod(bed_total, 60)
                suggestions.append({
                    "cycles": cycles,
                    "sleep_hours": round(cycles * cycle_min / 60, 1),
                    "bed_time": f"{bed_h:02d}:{bed_m:02d}",
                    "quality": "ideal" if cycles == 6 else ("iyi" if cycles == 5 else "minimum"),
                })

            return {
                "status": "success",
                "wake_time": wake_time,
                "suggestions": suggestions,
                "recommendation": f"Ideal: {suggestions[0]['bed_time']} yatis = {suggestions[0]['sleep_hours']} saat uyku",
            }

        if bed_time:
            parts = str(bed_time).split(":")
            bed_h, bed_m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            bed_total = bed_h * 60 + bed_m + fall_asleep_min

            suggestions = []
            for cycles in [4, 5, 6]:
                sleep_dur = cycles * cycle_min
                wake_total = (bed_total + sleep_dur) % 1440
                wake_h, wake_m2 = divmod(wake_total, 60)
                suggestions.append({
                    "cycles": cycles,
                    "sleep_hours": round(sleep_dur / 60, 1),
                    "wake_time": f"{wake_h:02d}:{wake_m2:02d}",
                })

            return {
                "status": "success",
                "bed_time": bed_time,
                "fall_asleep_time": f"{fall_asleep_min} dk",
                "suggestions": suggestions,
            }

        return {"status": "error", "message": "wake_time veya bed_time gerekli"}


# ────────────────────────────────────────────────────────────────────────────
# 216 — packing_list
# ────────────────────────────────────────────────────────────────────────────
class PackingList(BaseSkill):
    """Seyahat/etkinlik icin esya listesi."""

    SKILL_ID = "216"
    NAME = "packing_list"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Seyahat/etkinlik icin esya listesi"
    PARAMETERS = {
        "destination": "Hedef",
        "duration": "Sure (gun)",
        "season": "Mevsim (summer/winter/spring/fall)",
        "activities": "Aktiviteler",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        duration = int(params.get("duration", 3))
        season = str(params.get("season", "summer")).lower()
        destination = str(params.get("destination", ""))
        activities = str(params.get("activities", ""))

        essentials = [
            "Pasaport / Kimlik", "Telefon sarj aleti", "Ilac (varsa)",
            "Nakit / Kredi karti", "Seyahat sigortasi belgesi",
        ]

        clothing_base = [
            f"Ic camasiri x{duration}", f"Corap x{duration}",
            "Pijama", "Rahat ayakkabi",
        ]

        season_items: dict[str, list[str]] = {
            "summer": ["Gunes kremi", "Gunes gozlugu", "Sapka", "Sort x2", "Tisort x3", "Sandalet"],
            "winter": ["Mont", "Atki", "Bere", "Eldiven", "Kazak x2", "Bot", "Termal ic camasir"],
            "spring": ["Yagmurluk", "Hafif ceket", "Semsiye", "Uzun pantolon x2"],
            "fall": ["Ceket", "Kazak", "Semsiye", "Bot", "Uzun pantolon x2"],
        }

        toiletries = ["Dis fircasi", "Dis macunu", "Sampuan", "Deodorant", "Nemlendirici"]

        tech = ["Telefon", "Sarj kablosu", "Powerbank", "Kulaklik"]

        activity_items: list[str] = []
        if "yuzme" in activities.lower() or "beach" in activities.lower():
            activity_items.extend(["Mayo", "Havlu", "Terlik"])
        if "hiking" in activities.lower() or "dogayuruyusu" in activities.lower():
            activity_items.extend(["Yuruyus ayakkabisi", "Su sisesi", "Sirt cantasi"])
        if "is" in activities.lower() or "business" in activities.lower():
            activity_items.extend(["Takim elbise", "Kravat", "Resmi ayakkabi", "Laptop"])

        packing = {
            "temel": essentials,
            "giyim": clothing_base + season_items.get(season, []),
            "kisisel_bakim": toiletries,
            "teknoloji": tech,
        }
        if activity_items:
            packing["aktivite"] = activity_items

        total = sum(len(v) for v in packing.values())

        return {
            "status": "success",
            "destination": destination,
            "duration_days": duration,
            "season": season,
            "packing_list": packing,
            "total_items": total,
            "tip": "Listeyi yazdir ve her esyayi isaretleyerek pack et.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 217 — gift_suggester
# ────────────────────────────────────────────────────────────────────────────
class GiftSuggester(BaseSkill):
    """Hediye onerisi."""

    SKILL_ID = "217"
    NAME = "gift_suggester"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Hediye onerisi"
    PARAMETERS = {
        "recipient_age": "Alici yasi",
        "relationship": "Iliski (friend/family/partner/colleague)",
        "interests": "Ilgi alanlari",
        "budget": "Butce (TL)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        age = int(params.get("recipient_age", 30))
        relationship = str(params.get("relationship", "friend")).lower()
        interests = str(params.get("interests", ""))
        budget = float(params.get("budget", 200))

        gifts_db = {
            "friend": [
                {"name": "Kitap", "price_range": (30, 100), "note": "Sevdigi turde bir kitap"},
                {"name": "Kisisel kupa", "price_range": (50, 150), "note": "Ozel tasarim"},
                {"name": "Deneyim hediyesi", "price_range": (100, 500), "note": "Etkinlik bileti"},
                {"name": "Hediye karti", "price_range": (50, 300), "note": "Favori magaza"},
            ],
            "family": [
                {"name": "Aile fotograf cercevesi", "price_range": (50, 200), "note": "Dijital veya klasik"},
                {"name": "Ev aksesuari", "price_range": (100, 500), "note": "Dekoratif obje"},
                {"name": "Yemek sepeti", "price_range": (100, 400), "note": "Gurme urunler"},
            ],
            "partner": [
                {"name": "Parfum", "price_range": (150, 600), "note": "Favori markasi"},
                {"name": "Taki", "price_range": (100, 1000), "note": "Kolye, bileklik"},
                {"name": "Romantik yemek", "price_range": (200, 800), "note": "Ozel restoran"},
                {"name": "Hafta sonu tatili", "price_range": (500, 3000), "note": "Kisa kacamak"},
            ],
            "colleague": [
                {"name": "Ofis aksesuar", "price_range": (30, 150), "note": "Kalem seti, organizer"},
                {"name": "Kahve/Cay seti", "price_range": (50, 200), "note": "Premium markalar"},
                {"name": "Hediye karti", "price_range": (50, 200), "note": "Kitapci veya kafe"},
            ],
        }

        all_gifts = gifts_db.get(relationship, gifts_db["friend"])
        suitable = [g for g in all_gifts if g["price_range"][0] <= budget]

        if age < 18:
            suitable.append({"name": "Oyun/Oyuncak", "price_range": (50, 300), "note": "Yasa uygun"})
        if age > 60:
            suitable.append({"name": "Saglik seti", "price_range": (100, 400), "note": "Wellness urunleri"})

        return {
            "status": "success",
            "recipient_age": age,
            "relationship": relationship,
            "budget_tl": budget,
            "suggestions": suitable[:6],
            "tip": "En iyi hediye dusuncelidir, pahali degil.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 218 — movie_recommender
# ────────────────────────────────────────────────────────────────────────────
class MovieRecommender(BaseSkill):
    """Film/dizi onerisi."""

    SKILL_ID = "218"
    NAME = "movie_recommender"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Film/dizi onerisi"
    PARAMETERS = {
        "genre": "Tur (action/comedy/drama/scifi/horror/thriller/romance)",
        "mood": "Ruh hali (happy/sad/excited/relaxed)",
        "watched_recently": "Son izlenenler",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        genre = str(params.get("genre", "drama")).lower()
        mood = str(params.get("mood", "")).lower()

        movies_db: dict[str, list[dict[str, Any]]] = {
            "action": [
                {"title": "Inception", "year": 2010, "rating": 8.8, "director": "Christopher Nolan"},
                {"title": "Mad Max: Fury Road", "year": 2015, "rating": 8.1, "director": "George Miller"},
                {"title": "John Wick", "year": 2014, "rating": 7.4, "director": "Chad Stahelski"},
            ],
            "comedy": [
                {"title": "The Grand Budapest Hotel", "year": 2014, "rating": 8.1, "director": "Wes Anderson"},
                {"title": "Superbad", "year": 2007, "rating": 7.6, "director": "Greg Mottola"},
                {"title": "CODA", "year": 2021, "rating": 8.0, "director": "Sian Heder"},
            ],
            "drama": [
                {"title": "The Shawshank Redemption", "year": 1994, "rating": 9.3, "director": "Frank Darabont"},
                {"title": "Parasite", "year": 2019, "rating": 8.5, "director": "Bong Joon-ho"},
                {"title": "Kis Uykusu", "year": 2014, "rating": 8.0, "director": "Nuri Bilge Ceylan"},
            ],
            "scifi": [
                {"title": "Interstellar", "year": 2014, "rating": 8.6, "director": "Christopher Nolan"},
                {"title": "Blade Runner 2049", "year": 2017, "rating": 8.0, "director": "Denis Villeneuve"},
                {"title": "Arrival", "year": 2016, "rating": 7.9, "director": "Denis Villeneuve"},
            ],
            "horror": [
                {"title": "Get Out", "year": 2017, "rating": 7.7, "director": "Jordan Peele"},
                {"title": "Hereditary", "year": 2018, "rating": 7.3, "director": "Ari Aster"},
            ],
            "thriller": [
                {"title": "Se7en", "year": 1995, "rating": 8.6, "director": "David Fincher"},
                {"title": "Gone Girl", "year": 2014, "rating": 8.1, "director": "David Fincher"},
            ],
            "romance": [
                {"title": "Before Sunrise", "year": 1995, "rating": 8.1, "director": "Richard Linklater"},
                {"title": "La La Land", "year": 2016, "rating": 8.0, "director": "Damien Chazelle"},
            ],
        }

        recommendations = movies_db.get(genre, movies_db["drama"])

        return {
            "status": "success",
            "genre": genre,
            "mood": mood,
            "recommendations": recommendations,
            "count": len(recommendations),
        }


# ────────────────────────────────────────────────────────────────────────────
# 219 — book_recommender
# ────────────────────────────────────────────────────────────────────────────
class BookRecommender(BaseSkill):
    """Kitap onerisi."""

    SKILL_ID = "219"
    NAME = "book_recommender"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kitap onerisi"
    PARAMETERS = {
        "genre": "Tur (fiction/nonfiction/selfhelp/business/science/history)",
        "favorite_books": "Sevilen kitaplar",
        "mood": "Ruh hali",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        genre = str(params.get("genre", "fiction")).lower()

        books_db: dict[str, list[dict[str, str]]] = {
            "fiction": [
                {"title": "Yüzüklerin Efendisi", "author": "J.R.R. Tolkien", "pages": "1200"},
                {"title": "1984", "author": "George Orwell", "pages": "328"},
                {"title": "Tutunamayanlar", "author": "Oğuz Atay", "pages": "724"},
            ],
            "nonfiction": [
                {"title": "Sapiens", "author": "Yuval Noah Harari", "pages": "443"},
                {"title": "Cosmos", "author": "Carl Sagan", "pages": "432"},
            ],
            "selfhelp": [
                {"title": "Atomic Habits", "author": "James Clear", "pages": "320"},
                {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "pages": "499"},
            ],
            "business": [
                {"title": "Zero to One", "author": "Peter Thiel", "pages": "224"},
                {"title": "The Lean Startup", "author": "Eric Ries", "pages": "336"},
            ],
            "science": [
                {"title": "A Brief History of Time", "author": "Stephen Hawking", "pages": "256"},
                {"title": "The Selfish Gene", "author": "Richard Dawkins", "pages": "360"},
            ],
            "history": [
                {"title": "Guns, Germs, and Steel", "author": "Jared Diamond", "pages": "480"},
                {"title": "Nutuk", "author": "Mustafa Kemal Atatürk", "pages": "543"},
            ],
        }

        recommendations = books_db.get(genre, books_db["fiction"])
        return {
            "status": "success",
            "genre": genre,
            "recommendations": recommendations,
            "reading_tip": "Hergün en az 20 dakika oku. Yilda 20+ kitap bitirebilirsin.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 220 — music_recommender
# ────────────────────────────────────────────────────────────────────────────
class MusicRecommender(BaseSkill):
    """Muzik/playlist onerisi."""

    SKILL_ID = "220"
    NAME = "music_recommender"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Muzik/playlist onerisi"
    PARAMETERS = {
        "mood": "Ruh hali (happy/sad/energetic/calm/focus)",
        "genre": "Tur (pop/rock/jazz/classical/electronic/hiphop)",
        "activity": "Aktivite (workout/study/sleep/driving/cooking)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        mood = str(params.get("mood", "happy")).lower()
        activity = str(params.get("activity", "")).lower()
        genre = str(params.get("genre", "")).lower()

        playlists = {
            "happy": {"name": "Mutlu Anlar", "bpm": "120-140", "tracks": [
                "Pharrell Williams - Happy", "Katrina & The Waves - Walking on Sunshine",
                "Mark Ronson ft. Bruno Mars - Uptown Funk"]},
            "sad": {"name": "Huzunlu Anlar", "bpm": "60-80", "tracks": [
                "Adele - Someone Like You", "Radiohead - Creep",
                "Mazhar Alanson - Ah Bu Ben"]},
            "energetic": {"name": "Enerji Patlamasi", "bpm": "140-170", "tracks": [
                "Survivor - Eye of the Tiger", "Eminem - Lose Yourself",
                "AC/DC - Thunderstruck"]},
            "calm": {"name": "Rahatlatici", "bpm": "60-80", "tracks": [
                "Norah Jones - Come Away with Me", "Ludovico Einaudi - Nuvole Bianche",
                "Enya - Only Time"]},
            "focus": {"name": "Odak Modu", "bpm": "100-120", "tracks": [
                "Lo-fi Hip Hop - ChilledCow", "Hans Zimmer - Time",
                "Brian Eno - Music for Airports"]},
        }

        selected = playlists.get(mood, playlists["happy"])

        return {
            "status": "success",
            "mood": mood,
            "genre": genre,
            "activity": activity,
            "playlist": selected,
            "tip": "Spotify veya YouTube Music'te benzer playlist'ler bulabilirsiniz.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 221 — trivia_quiz
# ────────────────────────────────────────────────────────────────────────────
class TriviaQuiz(BaseSkill):
    """Bilgi yarismasi soruları uretme."""

    SKILL_ID = "221"
    NAME = "trivia_quiz"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Bilgi yarismasi sorulari uretme"
    PARAMETERS = {
        "category": "Kategori (science/history/geography/sports/art/general)",
        "difficulty": "Zorluk (easy/medium/hard)",
        "count": "Soru sayisi",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        category = str(params.get("category", "general")).lower()
        difficulty = str(params.get("difficulty", "medium")).lower()
        count = int(params.get("count", 5))

        questions_db: dict[str, list[dict[str, Any]]] = {
            "science": [
                {"q": "Suyun kimyasal formulu nedir?", "a": "H2O", "d": "easy"},
                {"q": "Isik hizi saniyede kac km?", "a": "~300.000 km/s", "d": "medium"},
                {"q": "DNA'nin tam acilimi nedir?", "a": "Deoksiribonukleik Asit", "d": "medium"},
                {"q": "Planck sabiti nedir?", "a": "6.626 × 10⁻³⁴ J·s", "d": "hard"},
            ],
            "history": [
                {"q": "Istanbul ne zaman fethedildi?", "a": "1453", "d": "easy"},
                {"q": "Cumhuriyet ne zaman ilan edildi?", "a": "29 Ekim 1923", "d": "easy"},
                {"q": "Magna Carta ne zaman imzalandi?", "a": "1215", "d": "medium"},
                {"q": "Canakkale Savasi hangi yil basladi?", "a": "1915", "d": "medium"},
            ],
            "geography": [
                {"q": "Dunyanin en buyuk okyanusu hangisi?", "a": "Buyuk Okyanus (Pasifik)", "d": "easy"},
                {"q": "Turkiye'nin en uzun nehri?", "a": "Kızılırmak", "d": "medium"},
                {"q": "Dunyanin en yuksek dagi?", "a": "Everest (8848m)", "d": "easy"},
            ],
            "general": [
                {"q": "Bir yilda kac gun var?", "a": "365 (artik yil 366)", "d": "easy"},
                {"q": "Pi sayisinin ilk 5 basamagi?", "a": "3.14159", "d": "medium"},
                {"q": "Internette www ne anlama gelir?", "a": "World Wide Web", "d": "easy"},
                {"q": "Bitcoin'in yaraticisi kim?", "a": "Satoshi Nakamoto (takim adi)", "d": "medium"},
            ],
        }

        pool = questions_db.get(category, questions_db["general"])
        if difficulty != "all":
            pool = [q for q in pool if q.get("d", "medium") == difficulty] or pool

        selected = pool[:min(count, len(pool))]

        return {
            "status": "success",
            "category": category,
            "difficulty": difficulty,
            "questions": [{"question": q["q"], "answer": q["a"], "difficulty": q["d"]} for q in selected],
            "count": len(selected),
        }


# ────────────────────────────────────────────────────────────────────────────
# 222 — riddle_generator
# ────────────────────────────────────────────────────────────────────────────
class RiddleGenerator(BaseSkill):
    """Bilmece/bulmaca olusturma."""

    SKILL_ID = "222"
    NAME = "riddle_generator"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Bilmece/bulmaca olusturma"
    PARAMETERS = {
        "difficulty": "Zorluk (easy/medium/hard)",
        "type": "Tip (riddle/math/logic/wordplay)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        difficulty = str(params.get("difficulty", "medium")).lower()
        rtype = str(params.get("type", "riddle")).lower()

        riddles_db = {
            "riddle": [
                {"q": "Anahtar olmadan acilan sey nedir?", "a": "Yumurta", "d": "easy"},
                {"q": "Ne kadar cok alirsan o kadar cok birakırsin. Nedir?", "a": "Ayak izi", "d": "medium"},
                {"q": "Gozleri var ama goremez. Nedir?", "a": "Igne", "d": "easy"},
            ],
            "math": [
                {"q": "3 kedi 3 fareyi 3 dakikada yakalar. 100 kedi 100 fareyi kac dakikada yakalar?", "a": "3 dakika", "d": "medium"},
                {"q": "1+1=? ama 11+11=?", "a": "2 ve 22", "d": "easy"},
                {"q": "Bir coban 17 koyun var. 9'u haric hepsi olur. Kac koyun kalir?", "a": "9", "d": "easy"},
            ],
            "logic": [
                {"q": "Bir adam yagmurda semsiyesiz yurur ama saclari islanmaz. Neden?", "a": "Kel", "d": "easy"},
                {"q": "Bir odada kibrit, mum, gaz lambasi var. Hangisini ilk yakarsın?", "a": "Kibriti", "d": "medium"},
            ],
            "wordplay": [
                {"q": "Hangi soru asla 'evet' ile cevaplanamaz?", "a": "Uyuyor musun?", "d": "medium"},
                {"q": "Hangi kelime her dilde ayni sekilde yazılır?", "a": "SOS", "d": "hard"},
            ],
        }

        pool = riddles_db.get(rtype, riddles_db["riddle"])
        seed = int(hashlib.md5(f"{difficulty}{rtype}{datetime.now().strftime('%Y-%m-%d')}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        rng.shuffle(pool)
        selected = pool[0] if pool else {"q": "Bilmece bulunamadi", "a": "N/A", "d": "N/A"}

        return {
            "status": "success",
            "type": rtype,
            "difficulty": difficulty,
            "riddle": selected["q"],
            "answer": selected["a"],
            "hint": "Dusun... Cevap basit olabilir!",
        }


# ────────────────────────────────────────────────────────────────────────────
# 223 — name_generator
# ────────────────────────────────────────────────────────────────────────────
class NameGenerator(BaseSkill):
    """Bebek/karakter/pet/marka isim onerileri."""

    SKILL_ID = "223"
    NAME = "name_generator"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Bebek/karakter/pet/marka isim onerileri"
    PARAMETERS = {
        "type": "Tip (baby/character/pet/brand/username)",
        "origin": "Koken (turkish/english/arabic/universal)",
        "style": "Stil (modern/classic/unique/funny)",
        "count": "Sayi",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        ntype = str(params.get("type", "baby")).lower()
        origin = str(params.get("origin", "turkish")).lower()
        style = str(params.get("style", "modern")).lower()
        count = int(params.get("count", 10))

        names_db: dict[str, dict[str, list[str]]] = {
            "baby": {
                "turkish": ["Ada", "Deniz", "Ege", "Defne", "Yigit", "Mira", "Atlas", "Luna", "Alp", "Ela"],
                "english": ["Oliver", "Emma", "Liam", "Sophia", "Noah", "Ava", "Ethan", "Mia", "Lucas", "Lily"],
            },
            "pet": {
                "turkish": ["Boncuk", "Pamuk", "Tekir", "Findik", "Karamel", "Duman", "Safran", "Tarcin"],
                "english": ["Buddy", "Luna", "Max", "Bella", "Charlie", "Daisy", "Rocky", "Milo"],
            },
            "brand": {
                "turkish": ["Zirve", "Ufuk", "Akis", "Cinar", "Yildiz", "Deniz", "Atlas", "Pars"],
                "english": ["Apex", "Nova", "Spark", "Bloom", "Zenith", "Pulse", "Flux", "Orbit"],
            },
            "character": {
                "turkish": ["Kaan", "Zehra", "Timur", "Aysel", "Arda", "Selin"],
                "english": ["Raven", "Storm", "Blaze", "Crystal", "Phoenix", "Shadow"],
            },
            "username": {
                "universal": ["ByteWizard", "CodeNinja", "PixelMaster", "DataStar", "CyberWolf",
                              "TechSage", "CloudRider", "NeonFox", "QuantumLeap", "BinaryBoss"],
            },
        }

        type_names = names_db.get(ntype, names_db["baby"])
        pool = type_names.get(origin, type_names.get("turkish", type_names.get("universal", ["Atlas"])))

        selected = pool[:min(count, len(pool))]

        return {
            "status": "success",
            "type": ntype,
            "origin": origin,
            "style": style,
            "names": selected,
            "count": len(selected),
        }


# ────────────────────────────────────────────────────────────────────────────
# 224 — zodiac_info
# ────────────────────────────────────────────────────────────────────────────
class ZodiacInfo(BaseSkill):
    """Burc bilgisi, gunluk yorum (eglence amacli)."""

    SKILL_ID = "224"
    NAME = "zodiac_info"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Burc bilgisi, gunluk yorum (eglence amacli)"
    PARAMETERS = {
        "sign": "Burc adi (koc/boga/ikizler/yengec/aslan/basak/terazi/akrep/yay/oglak/kova/balik)",
        "birth_date": "Dogum tarihi (YYYY-MM-DD, opsiyonel)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        sign = str(params.get("sign", "")).lower()
        birth_date = str(params.get("birth_date", ""))

        # Dogum tarihinden burc bul
        if birth_date and not sign:
            try:
                dt = datetime.strptime(birth_date, "%Y-%m-%d")
                month, day = dt.month, dt.day
                for z in _ZODIAC_SIGNS:
                    s_m, s_d = z["start"]
                    e_m, e_d = z["end"]
                    if z["sign"] == "oglak":  # Yil gecisi
                        if (month == 12 and day >= 22) or (month == 1 and day <= 19):
                            sign = z["sign"]
                            break
                    else:
                        if (month == s_m and day >= s_d) or (month == e_m and day <= e_d):
                            sign = z["sign"]
                            break
            except ValueError:
                pass

        if not sign:
            return {"status": "error", "message": "Burc adi veya dogum tarihi gerekli",
                    "valid_signs": [z["sign"] for z in _ZODIAC_SIGNS]}

        zodiac = None
        for z in _ZODIAC_SIGNS:
            if z["sign"] == sign or z["en"] == sign:
                zodiac = z
                break

        if not zodiac:
            return {"status": "error", "message": f"'{sign}' bulunamadi"}

        # Gunluk yorum (deterministik)
        today = datetime.now().strftime("%Y-%m-%d")
        seed = int(hashlib.md5(f"{sign}{today}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        daily_themes = [
            "Bugun enerji seviyeniz yuksek. Onemli kararlari bu gun alin.",
            "Yaraticiliginiz zirvede. Yeni projelere baslama zamani.",
            "Iliski ve iletisim on planda. Yakinlariniza zaman ayirin.",
            "Finansal konularda dikkatli olun. Butcenizi gozden gecirin.",
            "Sagliginiza onem verin. Stres yonetimi onemli.",
            "Is hayatinda basarili bir gun. Firsatlari degerlendirin.",
            "Ic huzur ve meditasyon zamani. Kendinize zaman ayirin.",
        ]

        return {
            "status": "success",
            "sign": zodiac["sign"],
            "english": zodiac["en"],
            "element": zodiac["element"],
            "ruling_planet": zodiac["planet"],
            "traits": zodiac["traits"],
            "date_range": f"{zodiac['start'][1]}/{zodiac['start'][0]} - {zodiac['end'][1]}/{zodiac['end'][0]}",
            "daily_horoscope": {
                "date": today,
                "message": rng.choice(daily_themes),
                "lucky_number": rng.randint(1, 49),
                "lucky_color": rng.choice(["kirmizi", "mavi", "yesil", "mor", "turuncu", "beyaz"]),
            },
            "disclaimer": "Eglence amaclidir, bilimsel gecerliligi yoktur.",
        }


# ────────────────────────────────────────────────────────────────────────────
# 225 — quote_finder
# ────────────────────────────────────────────────────────────────────────────
class QuoteFinder(BaseSkill):
    """Konuya gore meshur soz/alinti bulma."""

    SKILL_ID = "225"
    NAME = "quote_finder"
    CATEGORY = "productivity"
    RISK_LEVEL = "low"
    DESCRIPTION = "Konuya gore meshur soz/alinti bulma"
    PARAMETERS = {
        "topic": "Konu (motivasyon/liderlik/basari/yasam/bilim)",
        "author": "Yazar (opsiyonel)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        topic = str(params.get("topic", "motivasyon")).lower()
        author = str(params.get("author", "")).lower()

        # Tum konulari biriktir
        all_quotes: list[dict[str, str]] = []
        if topic in _QUOTES_DB:
            all_quotes = _QUOTES_DB[topic]
        else:
            for quotes in _QUOTES_DB.values():
                all_quotes.extend(quotes)

        # Yazar filtresi
        if author:
            filtered = [q for q in all_quotes if author in q["author"].lower()]
            if filtered:
                all_quotes = filtered

        return {
            "status": "success",
            "topic": topic,
            "author_filter": author or None,
            "quotes": all_quotes,
            "count": len(all_quotes),
            "available_topics": list(_QUOTES_DB.keys()),
        }


# ────────────────────────────────────────────────────────────────────────────
# Modul disa aktarma
# ────────────────────────────────────────────────────────────────────────────

ALL_PRODUCTIVITY_SKILLS: list[type[BaseSkill]] = [
    TodoManager,           # 201
    HabitTracker,          # 202
    PomodoroTimer,         # 203
    DecisionMaker,         # 204
    BrainstormHelper,      # 205
    GoalSetter,            # 206
    PriorityMatrix,        # 207
    JournalPrompt,         # 208
    AffirmationGenerator,  # 209
    RecipeFinder,          # 210
    MealPlanner,           # 211
    CalorieCalculator,     # 212
    BmiCalculator,         # 213
    WorkoutGenerator,      # 214
    SleepCalculator,       # 215
    PackingList,           # 216
    GiftSuggester,         # 217
    MovieRecommender,      # 218
    BookRecommender,       # 219
    MusicRecommender,      # 220
    TriviaQuiz,            # 221
    RiddleGenerator,       # 222
    NameGenerator,         # 223
    ZodiacInfo,            # 224
    QuoteFinder,           # 225
]
