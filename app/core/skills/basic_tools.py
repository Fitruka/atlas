"""Temel araclar beceri modulu.

Web arama, hesaplama, cevirme,
metin isleme ve yardimci araclar.
Beceriler: 001-025
"""

import base64
import hashlib
import math
import random
import re
import secrets
import string
import time
from typing import Any

from app.core.skills.base_skill import (
    BaseSkill,
)


class WebSearchSkill(BaseSkill):
    """Web arama becerisi."""

    SKILL_ID = "001"
    NAME = "web_search"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Web arama motoru uzerinden arama"
    )
    PARAMETERS = {
        "query": "Arama sorgusu",
        "max_results": "Maks sonuc",
        "language": "Dil",
        "region": "Bolge",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Web aramasini yurutur."""
        query = p.get("query", "")
        mx = p.get("max_results", 10)
        lang = p.get("language", "tr")
        region = p.get("region", "TR")
        results = []
        for i in range(min(mx, 10)):
            results.append({
                "title": (
                    f"Sonuc {i+1}: {query}"
                ),
                "url": (
                    f"https://example.com/"
                    f"search?q={i+1}"
                ),
                "snippet": (
                    f"{query} ile ilgili "
                    f"sonuc {i+1}"
                ),
            })
        return {
            "query": query,
            "language": lang,
            "region": region,
            "total": len(results),
            "results": results,
        }


class UrlReaderSkill(BaseSkill):
    """URL icerik okuma becerisi."""

    SKILL_ID = "002"
    NAME = "url_reader"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "URL icerik cekme ve metin cikarma"
    )
    PARAMETERS = {
        "url": "Hedef URL",
        "extract_mode": "Cikarma modu",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """URL icerigini okur."""
        url = p.get("url", "")
        mode = p.get(
            "extract_mode", "text",
        )
        return {
            "url": url,
            "extract_mode": mode,
            "title": f"Page: {url}",
            "content": (
                f"Extracted content from {url}"
            ),
            "word_count": 500,
            "language": "tr",
        }


class CalculatorSkill(BaseSkill):
    """Matematiksel hesaplama becerisi."""

    SKILL_ID = "003"
    NAME = "calculator"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Matematiksel hesaplama"
    )
    PARAMETERS = {
        "expression": "Matematiksel ifade",
    }

    _SAFE = re.compile(
        r'^[\d\s\+\-\*/\(\)\.\,%\^]+$',
    )

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Hesaplar."""
        expr = p.get("expression", "0")
        if not self._SAFE.match(expr):
            raise ValueError(
                "Guvenli olmayan ifade",
            )
        safe = expr.replace("^", "**")
        safe = safe.replace("%", "/100")
        result = eval(  # noqa: S307
            safe,
            {"__builtins__": {}},
            {"math": math},
        )
        return {
            "expression": expr,
            "result": result,
            "type": type(result).__name__,
        }


class UnitConverterSkill(BaseSkill):
    """Birim cevirici becerisi."""

    SKILL_ID = "004"
    NAME = "unit_converter"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Birim cevirici"
    PARAMETERS = {
        "value": "Deger",
        "from_unit": "Kaynak birim",
        "to_unit": "Hedef birim",
    }

    _CONVERSIONS: dict[
        str, dict[str, float]
    ] = {
        "km_mi": {"factor": 0.621371},
        "mi_km": {"factor": 1.60934},
        "kg_lb": {"factor": 2.20462},
        "lb_kg": {"factor": 0.453592},
        "m_ft": {"factor": 3.28084},
        "ft_m": {"factor": 0.3048},
        "cm_in": {"factor": 0.393701},
        "in_cm": {"factor": 2.54},
        "l_gal": {"factor": 0.264172},
        "gal_l": {"factor": 3.78541},
        "gb_mb": {"factor": 1024},
        "mb_gb": {"factor": 1 / 1024},
        "tb_gb": {"factor": 1024},
        "gb_tb": {"factor": 1 / 1024},
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Birim cevirir."""
        val = float(p.get("value", 0))
        fr = p.get("from_unit", "")
        to = p.get("to_unit", "")
        key = f"{fr}_{to}"
        if key == "c_f":
            result = val * 9 / 5 + 32
        elif key == "f_c":
            result = (val - 32) * 5 / 9
        elif key in self._CONVERSIONS:
            result = (
                val
                * self._CONVERSIONS[key][
                    "factor"
                ]
            )
        else:
            result = val
        return {
            "input_value": val,
            "from_unit": fr,
            "to_unit": to,
            "result": round(result, 6),
        }


class CurrencyExchangeSkill(BaseSkill):
    """Doviz kuru becerisi."""

    SKILL_ID = "005"
    NAME = "currency_exchange"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Doviz kuru ve cevirme"
    PARAMETERS = {
        "amount": "Miktar",
        "from_currency": "Kaynak doviz",
        "to_currency": "Hedef doviz",
    }

    _RATES: dict[str, float] = {
        "USD": 1.0, "EUR": 0.92,
        "GBP": 0.79, "TRY": 32.5,
        "JPY": 149.5,
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Doviz cevirir."""
        amt = float(p.get("amount", 1))
        fr = p.get("from_currency", "USD")
        to = p.get("to_currency", "TRY")
        fr_rate = self._RATES.get(fr, 1.0)
        to_rate = self._RATES.get(to, 1.0)
        usd = amt / fr_rate
        result = usd * to_rate
        return {
            "amount": amt,
            "from": fr, "to": to,
            "rate": round(to_rate / fr_rate, 4),
            "result": round(result, 2),
        }


class WeatherSkill(BaseSkill):
    """Hava durumu becerisi."""

    SKILL_ID = "006"
    NAME = "weather"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Hava durumu bilgisi"
    PARAMETERS = {
        "city": "Sehir",
        "units": "Birim sistemi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Hava durumu getirir."""
        city = p.get("city", "Istanbul")
        units = p.get("units", "metric")
        return {
            "city": city,
            "temperature": 22,
            "feels_like": 20,
            "humidity": 65,
            "wind_speed": 12,
            "condition": "Parcali bulutlu",
            "units": units,
        }


class TranslatorSkill(BaseSkill):
    """Ceviri becerisi."""

    SKILL_ID = "007"
    NAME = "translator"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin cevirisi"
    PARAMETERS = {
        "text": "Cevrilecek metin",
        "source_lang": "Kaynak dil",
        "target_lang": "Hedef dil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Metin cevirir."""
        text = p.get("text", "")
        src = p.get("source_lang", "auto")
        tgt = p.get("target_lang", "en")
        return {
            "source_text": text,
            "source_lang": src,
            "target_lang": tgt,
            "translated_text": (
                f"[{tgt}] {text}"
            ),
            "confidence": 0.95,
        }


class LanguageDetectorSkill(BaseSkill):
    """Dil tespit becerisi."""

    SKILL_ID = "008"
    NAME = "language_detector"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metnin dilini tespit etme"
    PARAMETERS = {"text": "Metin"}

    _PATTERNS = {
        "tr": ["bir", "ve", "bu", "ile"],
        "en": ["the", "and", "is", "for"],
        "de": ["der", "die", "und", "ist"],
        "fr": ["le", "la", "les", "des"],
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Dil tespit eder."""
        text = p.get("text", "").lower()
        scores: dict[str, int] = {}
        for lang, words in (
            self._PATTERNS.items()
        ):
            scores[lang] = sum(
                1 for w in words
                if w in text.split()
            )
        detected = max(
            scores, key=scores.get,  # type: ignore[arg-type]
        ) if any(scores.values()) else "en"
        return {
            "text_sample": text[:100],
            "detected_language": detected,
            "confidence": 0.85,
            "scores": scores,
        }


class DictionarySkill(BaseSkill):
    """Sozluk becerisi."""

    SKILL_ID = "009"
    NAME = "dictionary"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kelime anlami ve ornekler"
    PARAMETERS = {
        "word": "Kelime",
        "language": "Dil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Kelime anlamini getirir."""
        word = p.get("word", "")
        lang = p.get("language", "en")
        return {
            "word": word,
            "language": lang,
            "definitions": [
                f"{word} anlami 1",
                f"{word} anlami 2",
            ],
            "examples": [
                f"Ornek cumle: {word}",
            ],
            "pronunciation": f"/{word}/",
        }


class ThesaurusSkill(BaseSkill):
    """Es anlamli kelime becerisi."""

    SKILL_ID = "010"
    NAME = "thesaurus"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Es anlamli kelimeler"
    PARAMETERS = {
        "word": "Kelime",
        "language": "Dil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Es anlamlilari getirir."""
        word = p.get("word", "")
        return {
            "word": word,
            "synonyms": [
                f"{word}_syn1",
                f"{word}_syn2",
            ],
            "antonyms": [
                f"{word}_ant1",
            ],
            "related": [
                f"{word}_rel1",
            ],
        }


class SpellCheckerSkill(BaseSkill):
    """Yazim kontrolu becerisi."""

    SKILL_ID = "011"
    NAME = "spell_checker"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Yazim kontrolu"
    PARAMETERS = {
        "text": "Metin",
        "language": "Dil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Yazim kontrol eder."""
        text = p.get("text", "")
        words = text.split()
        return {
            "original": text,
            "word_count": len(words),
            "errors_found": 0,
            "corrections": [],
            "corrected_text": text,
        }


class GrammarCheckerSkill(BaseSkill):
    """Dilbilgisi kontrolu becerisi."""

    SKILL_ID = "012"
    NAME = "grammar_checker"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Dilbilgisi kontrolu"
    PARAMETERS = {
        "text": "Metin",
        "language": "Dil",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Dilbilgisi kontrol eder."""
        text = p.get("text", "")
        return {
            "original": text,
            "issues": [],
            "suggestions": [],
            "score": 95,
        }


class TextSummarizerSkill(BaseSkill):
    """Metin ozetleme becerisi."""

    SKILL_ID = "013"
    NAME = "text_summarizer"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin ozetleme"
    PARAMETERS = {
        "text": "Metin",
        "length": "Uzunluk modu",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Metni ozetler."""
        text = p.get("text", "")
        length = p.get("length", "short")
        sents = [
            s.strip()
            for s in text.split(".")
            if s.strip()
        ]
        ratio = {
            "short": 0.3,
            "medium": 0.5,
            "detailed": 0.7,
        }.get(length, 0.3)
        keep = max(
            1, int(len(sents) * ratio),
        )
        summary = ". ".join(sents[:keep])
        if summary and not summary.endswith("."):
            summary += "."
        return {
            "original_length": len(text),
            "summary": summary,
            "summary_length": len(summary),
            "compression": round(ratio, 2),
        }


class TextParaphraserSkill(BaseSkill):
    """Metin yeniden yazma becerisi."""

    SKILL_ID = "014"
    NAME = "text_paraphraser"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metni farkli yazmak"
    PARAMETERS = {
        "text": "Metin",
        "tone": "Ton",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Metni yeniden yazar."""
        text = p.get("text", "")
        tone = p.get("tone", "formal")
        return {
            "original": text,
            "paraphrased": (
                f"[{tone}] {text}"
            ),
            "tone": tone,
        }


class SentimentAnalyzerSkill(BaseSkill):
    """Duygu analizi becerisi."""

    SKILL_ID = "015"
    NAME = "sentiment_analyzer"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Duygu analizi"
    PARAMETERS = {"text": "Metin"}

    _POS = {
        "good", "great", "love", "best",
        "happy", "iyi", "guzel", "harika",
        "mukemmel", "super",
    }
    _NEG = {
        "bad", "hate", "worst", "terrible",
        "kotu", "berbat", "felaket",
        "korkunc",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Duygu analizi yapar."""
        text = p.get("text", "").lower()
        words = set(text.split())
        pos = len(words & self._POS)
        neg = len(words & self._NEG)
        total = pos + neg
        if total == 0:
            score = 0.0
            label = "neutral"
        elif pos > neg:
            score = pos / total
            label = "positive"
        else:
            score = -(neg / total)
            label = "negative"
        return {
            "text_sample": text[:100],
            "sentiment": label,
            "score": round(score, 3),
            "positive_count": pos,
            "negative_count": neg,
            "confidence": 0.80,
        }


class KeywordExtractorSkill(BaseSkill):
    """Anahtar kelime cikarma becerisi."""

    SKILL_ID = "016"
    NAME = "keyword_extractor"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Anahtar kelime cikarma"
    PARAMETERS = {
        "text": "Metin",
        "max_keywords": "Maks anahtar",
    }

    _STOP = {
        "the", "a", "an", "is", "are",
        "was", "be", "to", "of", "and",
        "in", "that", "it", "for", "on",
        "bir", "ve", "bu", "ile", "de",
        "da", "icin", "o", "ben", "sen",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Anahtar kelime cikarir."""
        text = p.get("text", "")
        mx = p.get("max_keywords", 10)
        words = re.findall(
            r'\b\w{3,}\b', text.lower(),
        )
        freq: dict[str, int] = {}
        for w in words:
            if w not in self._STOP:
                freq[w] = freq.get(w, 0) + 1
        sorted_kw = sorted(
            freq.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:mx]
        return {
            "keywords": [
                {"word": w, "count": c}
                for w, c in sorted_kw
            ],
            "total_words": len(words),
        }


class TextClassifierSkill(BaseSkill):
    """Metin siniflandirma becerisi."""

    SKILL_ID = "017"
    NAME = "text_classifier"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin siniflandirma"
    PARAMETERS = {
        "text": "Metin",
        "categories": "Kategoriler",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Metni siniflandirir."""
        text = p.get("text", "")
        cats = p.get("categories", [])
        if not cats:
            cats = [
                "technology", "business",
                "sports", "entertainment",
            ]
        scores = {
            c: round(random.random(), 3)
            for c in cats
        }
        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        return {
            "text_sample": text[:100],
            "predicted": best,
            "scores": scores,
        }


class ReadabilityScorerSkill(BaseSkill):
    """Okunabilirlik skoru becerisi."""

    SKILL_ID = "018"
    NAME = "readability_scorer"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin okunabilirlik skoru"
    PARAMETERS = {"text": "Metin"}

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Okunabilirlik hesaplar."""
        text = p.get("text", "")
        words = text.split()
        sents = [
            s for s in re.split(
                r'[.!?]+', text,
            ) if s.strip()
        ]
        syllables = sum(
            max(1, len(re.findall(
                r'[aeiouyAEIOUY]', w,
            )))
            for w in words
        )
        wc = max(len(words), 1)
        sc = max(len(sents), 1)
        flesch = (
            206.835
            - 1.015 * (wc / sc)
            - 84.6 * (syllables / wc)
        )
        return {
            "flesch_score": round(flesch, 1),
            "word_count": wc,
            "sentence_count": sc,
            "syllable_count": syllables,
            "difficulty": (
                "easy" if flesch > 60
                else "medium" if flesch > 30
                else "hard"
            ),
        }


class WordCounterSkill(BaseSkill):
    """Kelime sayici becerisi."""

    SKILL_ID = "019"
    NAME = "word_counter"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kelime ve karakter sayma"
    PARAMETERS = {"text": "Metin"}

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Kelime sayar."""
        text = p.get("text", "")
        words = text.split()
        sents = [
            s for s in re.split(
                r'[.!?]+', text,
            ) if s.strip()
        ]
        paras = [
            pp for pp in text.split("\n\n")
            if pp.strip()
        ]
        wc = len(words)
        reading_min = round(wc / 200, 1)
        return {
            "characters": len(text),
            "characters_no_spaces": len(
                text.replace(" ", ""),
            ),
            "words": wc,
            "sentences": len(sents),
            "paragraphs": max(len(paras), 1),
            "reading_time_min": reading_min,
        }


class LoremIpsumSkill(BaseSkill):
    """Lorem ipsum uretme becerisi."""

    SKILL_ID = "020"
    NAME = "lorem_ipsum"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Dolgu metni uretme"
    PARAMETERS = {
        "paragraphs": "Paragraf sayisi",
    }

    _TEXT = (
        "Lorem ipsum dolor sit amet, "
        "consectetur adipiscing elit. "
        "Sed do eiusmod tempor incididunt "
        "ut labore et dolore magna aliqua. "
        "Ut enim ad minim veniam, quis "
        "nostrud exercitation ullamco "
        "laboris nisi ut aliquip ex ea "
        "commodo consequat."
    )

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Lorem ipsum uretir."""
        paras = p.get("paragraphs", 3)
        texts = [self._TEXT] * min(paras, 20)
        full = "\n\n".join(texts)
        return {
            "text": full,
            "paragraphs": len(texts),
            "word_count": len(full.split()),
        }


class RandomGeneratorSkill(BaseSkill):
    """Rastgele uretici becerisi."""

    SKILL_ID = "021"
    NAME = "random_generator"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Rastgele veri uretme"
    PARAMETERS = {
        "type": "Tur",
        "count": "Adet",
    }

    _NAMES = [
        "Ali", "Ayse", "Mehmet", "Fatma",
        "Can", "Elif", "Emre", "Zeynep",
    ]
    _DOMAINS = [
        "gmail.com", "hotmail.com",
        "yandex.com",
    ]

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Rastgele veri uretir."""
        typ = p.get("type", "number")
        count = min(p.get("count", 1), 100)
        results = []
        for _ in range(count):
            if typ == "number":
                results.append(
                    random.randint(1, 1000),
                )
            elif typ == "name":
                results.append(
                    random.choice(self._NAMES),
                )
            elif typ == "email":
                name = random.choice(
                    self._NAMES,
                ).lower()
                dom = random.choice(
                    self._DOMAINS,
                )
                results.append(
                    f"{name}{random.randint(1,99)}"
                    f"@{dom}",
                )
            elif typ == "uuid":
                from uuid import uuid4
                results.append(str(uuid4()))
            elif typ == "color":
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                results.append(
                    f"#{r:02x}{g:02x}{b:02x}",
                )
            else:
                results.append(
                    random.randint(1, 1000),
                )
        return {
            "type": typ,
            "count": count,
            "results": results,
        }


class PasswordGeneratorSkill(BaseSkill):
    """Sifre uretme becerisi."""

    SKILL_ID = "022"
    NAME = "password_generator"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Guvenli sifre uretme"
    PARAMETERS = {
        "length": "Uzunluk",
        "include_symbols": "Sembol ekle",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Sifre uretir."""
        length = max(
            p.get("length", 16), 8,
        )
        symbols = p.get(
            "include_symbols", True,
        )
        chars = (
            string.ascii_letters
            + string.digits
        )
        if symbols:
            chars += "!@#$%&*+-="
        pwd = "".join(
            secrets.choice(chars)
            for _ in range(length)
        )
        has_upper = any(
            c.isupper() for c in pwd
        )
        has_lower = any(
            c.islower() for c in pwd
        )
        has_digit = any(
            c.isdigit() for c in pwd
        )
        strength = sum([
            has_upper, has_lower,
            has_digit, symbols,
            length >= 12,
        ])
        return {
            "password": pwd,
            "length": length,
            "strength": min(strength, 5),
            "has_upper": has_upper,
            "has_lower": has_lower,
            "has_digit": has_digit,
            "has_symbols": symbols,
        }


class HashGeneratorSkill(BaseSkill):
    """Hash uretme becerisi."""

    SKILL_ID = "023"
    NAME = "hash_generator"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin hash uretme"
    PARAMETERS = {
        "input": "Girdi",
        "algorithm": "Algoritma",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Hash uretir."""
        inp = p.get("input", "")
        algo = p.get("algorithm", "sha256")
        data = inp.encode("utf-8")
        algos = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
        }
        fn = algos.get(algo, hashlib.sha256)
        h = fn(data).hexdigest()
        return {
            "input_length": len(inp),
            "algorithm": algo,
            "hash": h,
            "hash_length": len(h),
        }


class Base64EncoderSkill(BaseSkill):
    """Base64 kodlama becerisi."""

    SKILL_ID = "024"
    NAME = "base64_encoder"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Base64 encode/decode"
    PARAMETERS = {
        "input": "Girdi",
        "mode": "Mod (encode/decode)",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Base64 islem yapar."""
        inp = p.get("input", "")
        mode = p.get("mode", "encode")
        if mode == "encode":
            output = base64.b64encode(
                inp.encode("utf-8"),
            ).decode("utf-8")
        else:
            output = base64.b64decode(
                inp.encode("utf-8"),
            ).decode("utf-8")
        return {
            "input": inp,
            "mode": mode,
            "output": output,
        }


class UrlShortenerSkill(BaseSkill):
    """URL kisaltma becerisi."""

    SKILL_ID = "025"
    NAME = "url_shortener"
    CATEGORY = "basic_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "URL kisaltma"
    PARAMETERS = {"url": "URL"}

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """URL kisaltir."""
        url = p.get("url", "")
        short_id = hashlib.md5(
            url.encode(),
        ).hexdigest()[:8]
        return {
            "original_url": url,
            "short_url": (
                f"https://atl.as/{short_id}"
            ),
            "short_id": short_id,
        }


ALL_BASIC_SKILLS: list[type[BaseSkill]] = [
    WebSearchSkill,
    UrlReaderSkill,
    CalculatorSkill,
    UnitConverterSkill,
    CurrencyExchangeSkill,
    WeatherSkill,
    TranslatorSkill,
    LanguageDetectorSkill,
    DictionarySkill,
    ThesaurusSkill,
    SpellCheckerSkill,
    GrammarCheckerSkill,
    TextSummarizerSkill,
    TextParaphraserSkill,
    SentimentAnalyzerSkill,
    KeywordExtractorSkill,
    TextClassifierSkill,
    ReadabilityScorerSkill,
    WordCounterSkill,
    LoremIpsumSkill,
    RandomGeneratorSkill,
    PasswordGeneratorSkill,
    HashGeneratorSkill,
    Base64EncoderSkill,
    UrlShortenerSkill,
]
