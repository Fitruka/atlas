"""Finans ve is becerileri.

Kredi, yatirim, vergi, fatura, butce
ve is planlama icin 25 beceri.
"""

import math
from typing import Any

from app.core.skills.base_skill import BaseSkill


class StockPriceSkill(BaseSkill):
    """Hisse senedi fiyat becerisi."""

    SKILL_ID = "151"
    NAME = "stock_price"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Hisse senedi fiyati, grafik, "
        "temel veriler"
    )
    PARAMETERS = {
        "symbol": "Hisse senedi sembol",
        "period": "Donem",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        symbol = p.get("symbol", "AAPL")
        period = p.get("period", "1d")
        return {
            "symbol": symbol,
            "period": period,
            "price": 150.0,
            "change": 2.5,
            "change_percent": 1.69,
            "volume": 50000000,
            "market_cap": "2.4T",
            "pe_ratio": 28.5,
        }


class CryptoPriceSkill(BaseSkill):
    """Kripto para fiyat becerisi."""

    SKILL_ID = "152"
    NAME = "crypto_price"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Kripto para fiyati, piyasa degeri"
    )
    PARAMETERS = {
        "symbol": "Kripto sembol",
        "vs_currency": "Karsilastirma para",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        symbol = p.get("symbol", "BTC")
        vs = p.get("vs_currency", "USD")
        return {
            "symbol": symbol,
            "vs_currency": vs,
            "price": 45000.0,
            "market_cap": "850B",
            "volume_24h": "25B",
            "change_24h": -1.2,
        }


class LoanCalculatorSkill(BaseSkill):
    """Kredi hesaplama becerisi."""

    SKILL_ID = "153"
    NAME = "loan_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Kredi hesaplama (aylik taksit, "
        "toplam faiz, amortisman)"
    )
    PARAMETERS = {
        "amount": "Kredi tutari",
        "rate": "Yillik faiz orani (%)",
        "term_months": "Vade (ay)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        amount = float(p.get("amount", 100000))
        rate = float(p.get("rate", 2.5))
        months = int(p.get("term_months", 12))

        monthly_rate = rate / 100 / 12
        if monthly_rate > 0:
            payment = amount * (
                monthly_rate
                * (1 + monthly_rate) ** months
            ) / (
                (1 + monthly_rate) ** months - 1
            )
        else:
            payment = amount / months

        total = payment * months
        total_interest = total - amount

        return {
            "amount": amount,
            "annual_rate": rate,
            "term_months": months,
            "monthly_payment": round(
                payment, 2,
            ),
            "total_payment": round(total, 2),
            "total_interest": round(
                total_interest, 2,
            ),
        }


class MortgageCalculatorSkill(BaseSkill):
    """Konut kredisi hesaplama becerisi."""

    SKILL_ID = "154"
    NAME = "mortgage_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Konut kredisi hesaplama"
    PARAMETERS = {
        "home_price": "Ev fiyati",
        "down_payment": "Pesinat",
        "rate": "Yillik faiz (%)",
        "term_years": "Vade (yil)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        price = float(p.get("home_price", 1000000))
        down = float(p.get("down_payment", 200000))
        rate = float(p.get("rate", 1.5))
        years = int(p.get("term_years", 15))

        loan = price - down
        months = years * 12
        mr = rate / 100 / 12
        if mr > 0:
            pmt = loan * (
                mr * (1 + mr) ** months
            ) / ((1 + mr) ** months - 1)
        else:
            pmt = loan / months

        total = pmt * months
        return {
            "home_price": price,
            "down_payment": down,
            "loan_amount": loan,
            "monthly_payment": round(pmt, 2),
            "total_payment": round(total, 2),
            "total_interest": round(
                total - loan, 2,
            ),
            "ltv_ratio": round(
                loan / price * 100, 1,
            ),
        }


class CompoundInterestSkill(BaseSkill):
    """Bilesik faiz hesaplama becerisi."""

    SKILL_ID = "155"
    NAME = "compound_interest"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Bilesik faiz hesaplama"
    PARAMETERS = {
        "principal": "Anapara",
        "rate": "Yillik faiz (%)",
        "period": "Sure (yil)",
        "compound_frequency": "Bilesik frekans",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        principal = float(
            p.get("principal", 10000),
        )
        rate = float(p.get("rate", 10))
        period = int(p.get("period", 5))
        freq = int(
            p.get("compound_frequency", 12),
        )

        r = rate / 100
        amount = principal * (
            1 + r / freq
        ) ** (freq * period)
        interest = amount - principal

        return {
            "principal": principal,
            "rate": rate,
            "period_years": period,
            "compound_frequency": freq,
            "final_amount": round(amount, 2),
            "total_interest": round(
                interest, 2,
            ),
            "growth_factor": round(
                amount / principal, 4,
            ),
        }


class RoiCalculatorSkill(BaseSkill):
    """ROI hesaplama becerisi."""

    SKILL_ID = "156"
    NAME = "roi_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Yatirim getirisi hesaplama"
    PARAMETERS = {
        "investment": "Yatirim tutari",
        "revenue": "Gelir",
        "period": "Donem",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        inv = float(p.get("investment", 10000))
        rev = float(p.get("revenue", 15000))
        period = p.get("period", "1 yil")

        profit = rev - inv
        roi = (profit / inv) * 100 if inv else 0

        return {
            "investment": inv,
            "revenue": rev,
            "profit": profit,
            "roi_percent": round(roi, 2),
            "period": period,
        }


class BreakEvenCalculatorSkill(BaseSkill):
    """Basa bas noktasi becerisi."""

    SKILL_ID = "157"
    NAME = "break_even_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Basa bas noktasi hesaplama"
    PARAMETERS = {
        "fixed_costs": "Sabit maliyetler",
        "variable_cost_per_unit": "Birim degisken maliyet",
        "price_per_unit": "Birim satis fiyati",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        fixed = float(
            p.get("fixed_costs", 50000),
        )
        var_cost = float(
            p.get("variable_cost_per_unit", 30),
        )
        price = float(
            p.get("price_per_unit", 100),
        )

        margin = price - var_cost
        if margin > 0:
            units = math.ceil(fixed / margin)
            revenue = units * price
        else:
            units = 0
            revenue = 0

        return {
            "fixed_costs": fixed,
            "variable_cost": var_cost,
            "price_per_unit": price,
            "contribution_margin": margin,
            "break_even_units": units,
            "break_even_revenue": revenue,
        }


class ProfitMarginSkill(BaseSkill):
    """Kar marji hesaplama becerisi."""

    SKILL_ID = "158"
    NAME = "profit_margin"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Kar marji hesaplama "
        "(brut, net, operasyonel)"
    )
    PARAMETERS = {
        "revenue": "Gelir",
        "costs": "Maliyetler",
        "type": "brut/net/operasyonel",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        revenue = float(
            p.get("revenue", 100000),
        )
        costs = float(p.get("costs", 60000))
        mtype = p.get("type", "brut")

        profit = revenue - costs
        margin = (
            (profit / revenue * 100)
            if revenue else 0
        )

        return {
            "revenue": revenue,
            "costs": costs,
            "profit": profit,
            "margin_percent": round(margin, 2),
            "type": mtype,
        }


class TaxCalculatorSkill(BaseSkill):
    """Gelir vergisi hesaplama becerisi."""

    SKILL_ID = "159"
    NAME = "tax_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Gelir vergisi tahmini"
    PARAMETERS = {
        "income": "Gelir",
        "country": "Ulke",
        "year": "Yil",
        "deductions": "Indirimler",
    }

    _TR_BRACKETS = [
        (110000, 0.15),
        (230000, 0.20),
        (580000, 0.27),
        (3000000, 0.35),
        (float("inf"), 0.40),
    ]

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        income = float(p.get("income", 500000))
        country = p.get("country", "TR")
        deductions = float(
            p.get("deductions", 0),
        )

        taxable = max(income - deductions, 0)
        tax = 0.0
        prev = 0

        brackets = self._TR_BRACKETS
        for limit, rate in brackets:
            if taxable <= prev:
                break
            band = min(taxable, limit) - prev
            tax += band * rate
            prev = limit

        effective = (
            (tax / income * 100)
            if income else 0
        )

        return {
            "income": income,
            "deductions": deductions,
            "taxable_income": taxable,
            "tax_amount": round(tax, 2),
            "effective_rate": round(
                effective, 2,
            ),
            "country": country,
        }


class VatCalculatorSkill(BaseSkill):
    """KDV hesaplama becerisi."""

    SKILL_ID = "160"
    NAME = "vat_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "KDV hesaplama (dahil/haric)"
    PARAMETERS = {
        "amount": "Tutar",
        "vat_rate": "KDV orani (%)",
        "mode": "inclusive/exclusive",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        amount = float(p.get("amount", 1000))
        rate = float(p.get("vat_rate", 20))
        mode = p.get("mode", "exclusive")

        if mode == "inclusive":
            base = amount / (1 + rate / 100)
            vat = amount - base
            total = amount
        else:
            base = amount
            vat = amount * rate / 100
            total = amount + vat

        return {
            "base_amount": round(base, 2),
            "vat_amount": round(vat, 2),
            "total_amount": round(total, 2),
            "vat_rate": rate,
            "mode": mode,
        }


class InvoiceGeneratorSkill(BaseSkill):
    """Fatura olusturma becerisi."""

    SKILL_ID = "161"
    NAME = "invoice_generator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Fatura PDF olusturma"
    PARAMETERS = {
        "seller": "Satici bilgisi",
        "buyer": "Alici bilgisi",
        "items": "Kalem listesi",
        "tax_rate": "Vergi orani",
        "currency": "Para birimi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        items = p.get("items", [])
        tax_rate = float(
            p.get("tax_rate", 20),
        )
        currency = p.get("currency", "TRY")

        subtotal = sum(
            float(i.get("total", 0))
            for i in items
            if isinstance(i, dict)
        )
        tax = subtotal * tax_rate / 100
        total = subtotal + tax

        return {
            "invoice_number": "INV-001",
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "total": round(total, 2),
            "currency": currency,
            "item_count": len(items),
            "output": "invoice.pdf",
        }


class ReceiptScannerSkill(BaseSkill):
    """Fis tarama becerisi."""

    SKILL_ID = "162"
    NAME = "receipt_scanner"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Fis/fatura fotografindan "
        "veri cikarma (OCR + parsing)"
    )
    PARAMETERS = {
        "image_path": "Goruntu yolu",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        img = p.get("image_path", "")
        return {
            "image_path": img,
            "vendor": "Unknown",
            "date": "Unknown",
            "items": [],
            "total": 0.0,
            "currency": "TRY",
            "confidence": 0.85,
        }


class ExpenseTrackerSkill(BaseSkill):
    """Harcama kayit becerisi."""

    SKILL_ID = "163"
    NAME = "expense_tracker"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Harcama kaydi ve kategorileme"
    )
    PARAMETERS = {
        "amount": "Tutar",
        "category": "Kategori",
        "description": "Aciklama",
        "date": "Tarih",
    }

    _expenses: list[dict[str, Any]] = []

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        action = p.get("action", "add")
        if action == "list":
            total = sum(
                e["amount"]
                for e in self._expenses
            )
            return {
                "expenses": list(
                    self._expenses,
                ),
                "total": total,
                "count": len(self._expenses),
            }

        expense = {
            "amount": float(
                p.get("amount", 0),
            ),
            "category": p.get(
                "category", "diger",
            ),
            "description": p.get(
                "description", "",
            ),
            "date": p.get("date", ""),
        }
        self._expenses.append(expense)
        return {
            "expense": expense,
            "total_count": len(self._expenses),
        }


class BudgetPlannerSkill(BaseSkill):
    """Butce planlama becerisi."""

    SKILL_ID = "164"
    NAME = "budget_planner"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Butce plani olusturma "
        "(50/30/20 kurali veya ozel)"
    )
    PARAMETERS = {
        "income": "Gelir",
        "method": "50/30/20 veya ozel",
        "categories": "Kategoriler",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        income = float(
            p.get("income", 50000),
        )
        method = p.get("method", "50/30/20")

        if method == "50/30/20":
            needs = income * 0.50
            wants = income * 0.30
            savings = income * 0.20
            return {
                "income": income,
                "method": method,
                "needs": round(needs, 2),
                "wants": round(wants, 2),
                "savings": round(savings, 2),
                "categories": {
                    "Ihtiyaclar (50%)": needs,
                    "Istekler (30%)": wants,
                    "Birikim (20%)": savings,
                },
            }

        return {
            "income": income,
            "method": "custom",
            "categories": p.get(
                "categories", {},
            ),
        }


class SalaryCalculatorSkill(BaseSkill):
    """Brut-net maas hesaplama becerisi."""

    SKILL_ID = "165"
    NAME = "salary_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Brut-net maas hesaplama "
        "(SGK, gelir vergisi, damga)"
    )
    PARAMETERS = {
        "gross_salary": "Brut maas",
        "country": "Ulke",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        gross = float(
            p.get("gross_salary", 50000),
        )
        country = p.get("country", "TR")

        sgk_worker = gross * 0.14
        unemployment = gross * 0.01
        income_tax = (
            gross - sgk_worker - unemployment
        ) * 0.15
        stamp_tax = gross * 0.00759
        deductions = (
            sgk_worker + unemployment
            + income_tax + stamp_tax
        )
        net = gross - deductions

        return {
            "gross_salary": gross,
            "sgk_worker": round(sgk_worker, 2),
            "unemployment": round(
                unemployment, 2,
            ),
            "income_tax": round(
                income_tax, 2,
            ),
            "stamp_tax": round(stamp_tax, 2),
            "total_deductions": round(
                deductions, 2,
            ),
            "net_salary": round(net, 2),
            "country": country,
        }


class TipCalculatorSkill(BaseSkill):
    """Bahsis hesaplama becerisi."""

    SKILL_ID = "166"
    NAME = "tip_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Bahsis hesaplama ve bolusturme"
    )
    PARAMETERS = {
        "bill_amount": "Hesap tutari",
        "tip_percentage": "Bahsis yuzdesi",
        "split_count": "Kisi sayisi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        bill = float(
            p.get("bill_amount", 500),
        )
        tip_pct = float(
            p.get("tip_percentage", 10),
        )
        split = int(p.get("split_count", 1))

        tip = bill * tip_pct / 100
        total = bill + tip
        per_person = total / max(split, 1)

        return {
            "bill_amount": bill,
            "tip_percentage": tip_pct,
            "tip_amount": round(tip, 2),
            "total": round(total, 2),
            "split_count": split,
            "per_person": round(
                per_person, 2,
            ),
        }


class DiscountCalculatorSkill(BaseSkill):
    """Indirim hesaplama becerisi."""

    SKILL_ID = "167"
    NAME = "discount_calculator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Indirim hesaplama "
        "(yuzde, tutar, zincirleme)"
    )
    PARAMETERS = {
        "original_price": "Orijinal fiyat",
        "discounts": "Indirim listesi (%)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        price = float(
            p.get("original_price", 1000),
        )
        discounts = p.get("discounts", [10])

        current = price
        applied = []
        for d in discounts:
            d = float(d)
            reduction = current * d / 100
            current -= reduction
            applied.append({
                "discount": d,
                "reduction": round(reduction, 2),
                "after": round(current, 2),
            })

        return {
            "original_price": price,
            "final_price": round(current, 2),
            "total_discount": round(
                price - current, 2,
            ),
            "total_discount_pct": round(
                (price - current) / price * 100,
                2,
            ),
            "steps": applied,
        }


class BusinessNameGeneratorSkill(BaseSkill):
    """Is adi onerisi becerisi."""

    SKILL_ID = "168"
    NAME = "business_name_generator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Is adi onerileri"
    PARAMETERS = {
        "industry": "Sektor",
        "keywords": "Anahtar kelimeler",
        "style": "Stil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        industry = p.get("industry", "tech")
        keywords = p.get("keywords", [])
        kw = keywords[0] if keywords else industry
        kw_cap = kw.capitalize()
        names = [
            f"{kw_cap}Hub",
            f"{kw_cap}Pro",
            f"{kw_cap}Labs",
            f"{kw_cap}Flow",
            f"Smart{kw_cap}",
            f"{kw_cap}ify",
            f"Neo{kw_cap}",
            f"{kw_cap}Wave",
        ]
        return {
            "industry": industry,
            "suggestions": names,
            "count": len(names),
        }


class PitchDeckHelperSkill(BaseSkill):
    """Sunum yardimcisi becerisi."""

    SKILL_ID = "169"
    NAME = "pitch_deck_helper"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Sunum yapisi ve icerik onerisi"
    )
    PARAMETERS = {
        "company": "Sirket adi",
        "stage": "Asama",
        "audience": "Hedef kitle",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        company = p.get("company", "Startup")
        slides = [
            "Kapak", "Problem", "Cozum",
            "Pazar Buyuklugu", "Is Modeli",
            "Traction", "Takim", "Finansallar",
            "Yatirim Talebi", "Iletisim",
        ]
        return {
            "company": company,
            "slides": slides,
            "slide_count": len(slides),
            "tips": [
                "10-15 slayt ideal",
                "Her slaytta tek mesaj",
                "Veri ile destekle",
            ],
        }


class MeetingAgendaSkill(BaseSkill):
    """Toplanti gundemi becerisi."""

    SKILL_ID = "170"
    NAME = "meeting_agenda"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Toplanti gundemi olusturma"
    PARAMETERS = {
        "topic": "Konu",
        "participants": "Katilimcilar",
        "duration": "Sure (dk)",
        "goals": "Hedefler",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        topic = p.get("topic", "Genel")
        duration = int(
            p.get("duration", 60),
        )
        items = [
            {"item": "Acilis", "duration": 5},
            {
                "item": "Guncel durum",
                "duration": duration // 4,
            },
            {
                "item": topic,
                "duration": duration // 2,
            },
            {
                "item": "Sorular",
                "duration": duration // 6,
            },
            {"item": "Kapanis", "duration": 5},
        ]
        return {
            "topic": topic,
            "total_duration": duration,
            "agenda_items": items,
        }


class MeetingNotesSkill(BaseSkill):
    """Toplanti notlari becerisi."""

    SKILL_ID = "171"
    NAME = "meeting_notes"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Toplanti notlarini yapilandirma"
    )
    PARAMETERS = {
        "raw_notes": "Ham notlar",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        raw = p.get("raw_notes", "")
        lines = [
            l.strip() for l in raw.split("\n")
            if l.strip()
        ]
        return {
            "summary": raw[:200] if raw else "",
            "decisions": [],
            "action_items": [],
            "participants": [],
            "line_count": len(lines),
        }


class SwotAnalysisSkill(BaseSkill):
    """SWOT analizi becerisi."""

    SKILL_ID = "172"
    NAME = "swot_analysis"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "SWOT analizi olusturma"
    PARAMETERS = {
        "subject": "Konu",
        "context": "Baglam",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        subject = p.get("subject", "")
        return {
            "subject": subject,
            "strengths": [
                "Guclu yonler analizi gerekli",
            ],
            "weaknesses": [
                "Zayif yonler analizi gerekli",
            ],
            "opportunities": [
                "Firsatlar analizi gerekli",
            ],
            "threats": [
                "Tehditler analizi gerekli",
            ],
        }


class OkrGeneratorSkill(BaseSkill):
    """OKR olusturma becerisi."""

    SKILL_ID = "173"
    NAME = "okr_generator"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "OKR olusturma"
    PARAMETERS = {
        "goal": "Hedef",
        "timeframe": "Zaman dilimi",
        "team": "Takim",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        goal = p.get("goal", "Buyume")
        timeframe = p.get("timeframe", "Q1")
        return {
            "objective": goal,
            "timeframe": timeframe,
            "key_results": [
                {
                    "kr": f"KR1: {goal} metrigi %20 artir",
                    "target": "20%",
                },
                {
                    "kr": f"KR2: {goal} icin 3 yeni inisiyatif",
                    "target": "3",
                },
                {
                    "kr": f"KR3: Musteri memnuniyeti >90%",
                    "target": "90%",
                },
            ],
        }


class KpiTrackerSkill(BaseSkill):
    """KPI takip becerisi."""

    SKILL_ID = "174"
    NAME = "kpi_tracker"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "KPI tanimlama ve takip"
    PARAMETERS = {
        "kpis": "KPI listesi",
        "current_values": "Mevcut degerler",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        kpis = p.get("kpis", [])
        values = p.get("current_values", [])

        results = []
        for i, kpi in enumerate(kpis):
            val = (
                values[i]
                if i < len(values) else 0
            )
            results.append({
                "kpi": kpi,
                "value": val,
                "status": (
                    "on_track"
                    if val > 0 else "at_risk"
                ),
            })

        return {
            "kpis": results,
            "total_tracked": len(results),
        }


class BusinessPlanOutlineSkill(BaseSkill):
    """Is plani taslagi becerisi."""

    SKILL_ID = "175"
    NAME = "business_plan_outline"
    CATEGORY = "finance"
    RISK_LEVEL = "low"
    DESCRIPTION = "Is plani taslagi olusturma"
    PARAMETERS = {
        "business_type": "Is tipi",
        "market": "Pazar",
        "revenue_model": "Gelir modeli",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        btype = p.get("business_type", "SaaS")
        market = p.get("market", "")
        sections = [
            "Yonetici Ozeti",
            "Sirket Tanimi",
            "Pazar Analizi",
            "Organizasyon",
            "Urun/Hizmet",
            "Pazarlama Stratejisi",
            "Finansal Tahminler",
            "Fon Talebi",
        ]
        return {
            "business_type": btype,
            "market": market,
            "sections": sections,
            "section_count": len(sections),
        }


ALL_FINANCE_SKILLS: list[type[BaseSkill]] = [
    StockPriceSkill,
    CryptoPriceSkill,
    LoanCalculatorSkill,
    MortgageCalculatorSkill,
    CompoundInterestSkill,
    RoiCalculatorSkill,
    BreakEvenCalculatorSkill,
    ProfitMarginSkill,
    TaxCalculatorSkill,
    VatCalculatorSkill,
    InvoiceGeneratorSkill,
    ReceiptScannerSkill,
    ExpenseTrackerSkill,
    BudgetPlannerSkill,
    SalaryCalculatorSkill,
    TipCalculatorSkill,
    DiscountCalculatorSkill,
    BusinessNameGeneratorSkill,
    PitchDeckHelperSkill,
    MeetingAgendaSkill,
    MeetingNotesSkill,
    SwotAnalysisSkill,
    OkrGeneratorSkill,
    KpiTrackerSkill,
    BusinessPlanOutlineSkill,
]
