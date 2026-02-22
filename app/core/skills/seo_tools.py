"""SEO ve dijital pazarlama arac beceri modulu.

SEO analizi, anahtar kelime arastirmasi,
icerik planlama ve reklam optimizasyonu.
Beceriler: 131-150
"""

import math
import re
import time
import json
import hashlib
from typing import Any
from urllib.parse import (
    urlencode,
    urlparse,
    urlunparse,
    parse_qs,
)

from app.core.skills.base_skill import BaseSkill


# ─── 131: SEO Analyzer ───────────────────────────────────────────
class SeoAnalyzerSkill(BaseSkill):
    """Sayfa SEO analizini yapar ve puan verir."""

    SKILL_ID = "131"
    NAME = "seo_analyzer"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Sayfa SEO analizini yapar ve puan verir."
    PARAMETERS = {
        "url": "Analiz edilecek URL",
        "title": "Sayfa basligi",
        "description": "Meta aciklama",
        "content": "Sayfa icerigi (metin)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        url = params.get("url", "")
        title = params.get("title", "")
        description = params.get("description", "")
        content = params.get("content", "")

        issues: list[str] = []
        score = 100

        # Title checks
        if not title:
            issues.append("Sayfa basligi eksik")
            score -= 20
        elif len(title) < 30:
            issues.append("Baslik cok kisa (<30 karakter)")
            score -= 10
        elif len(title) > 60:
            issues.append("Baslik cok uzun (>60 karakter)")
            score -= 5

        # Description checks
        if not description:
            issues.append("Meta aciklama eksik")
            score -= 15
        elif len(description) < 120:
            issues.append("Meta aciklama cok kisa (<120)")
            score -= 5
        elif len(description) > 160:
            issues.append("Meta aciklama cok uzun (>160)")
            score -= 5

        # URL checks
        parsed = urlparse(url) if url else None
        if parsed and not parsed.scheme.startswith("https"):
            issues.append("HTTPS kullanilmiyor")
            score -= 10
        if parsed and len(parsed.path) > 100:
            issues.append("URL cok uzun")
            score -= 5

        # Content checks
        word_count = len(content.split()) if content else 0
        if word_count < 300:
            issues.append(f"Icerik cok kisa ({word_count} kelime, min 300)")
            score -= 15

        score = max(score, 0)
        grade = "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D"

        return {
            "status": "success",
            "score": score,
            "grade": grade,
            "issues": issues,
            "word_count": word_count,
            "title_length": len(title),
            "description_length": len(description),
        }


# ─── 132: Keyword Researcher ─────────────────────────────────────
class KeywordResearcherSkill(BaseSkill):
    """Anahtar kelime arastirmasi ve analiz."""

    SKILL_ID = "132"
    NAME = "keyword_researcher"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Anahtar kelime arastirmasi ve analiz yapar."
    PARAMETERS = {
        "keyword": "Ana anahtar kelime",
        "language": "Hedef dil (tr/en)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        keyword = params.get("keyword", "")
        language = params.get("language", "tr")

        words = keyword.lower().split()
        word_count = len(words)

        # Keyword type
        if word_count == 1:
            kw_type = "short_tail"
            competition = "high"
            difficulty = 85
        elif word_count <= 3:
            kw_type = "mid_tail"
            competition = "medium"
            difficulty = 55
        else:
            kw_type = "long_tail"
            competition = "low"
            difficulty = 25

        # Generate related keywords
        related = []
        if words:
            prefixes = ["en iyi", "ucuz", "nasil", "nerede"] if language == "tr" else ["best", "cheap", "how to", "where"]
            for p in prefixes:
                related.append(f"{p} {keyword}")
            suffixes = ["fiyat", "yorum", "karsilastirma"] if language == "tr" else ["price", "review", "comparison"]
            for s in suffixes:
                related.append(f"{keyword} {s}")

        # Simulated metrics based on keyword hash
        h = int(hashlib.md5(keyword.encode()).hexdigest()[:8], 16)
        volume = (h % 9000) + 100
        cpc = round((h % 500) / 100 + 0.1, 2)

        return {
            "status": "success",
            "keyword": keyword,
            "type": kw_type,
            "word_count": word_count,
            "competition": competition,
            "difficulty": difficulty,
            "estimated_volume": volume,
            "estimated_cpc": cpc,
            "related_keywords": related,
            "language": language,
        }


# ─── 133: Keyword Suggester ──────────────────────────────────────
class KeywordSuggesterSkill(BaseSkill):
    """Anahtar kelime onerileri uretir."""

    SKILL_ID = "133"
    NAME = "keyword_suggester"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Bir konuya dayali anahtar kelime onerileri uretir."
    PARAMETERS = {
        "topic": "Ana konu",
        "count": "Oneri sayisi (varsayilan: 10)",
        "language": "Dil (tr/en)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        topic = params.get("topic", "")
        count = int(params.get("count", 10))
        language = params.get("language", "tr")

        suggestions = []
        if language == "tr":
            patterns = [
                "{topic} nedir",
                "{topic} nasil yapilir",
                "{topic} fiyatlari",
                "{topic} yorumlari",
                "en iyi {topic}",
                "{topic} onerileri",
                "{topic} karsilastirma",
                "{topic} avantajlari",
                "{topic} dezavantajlari",
                "{topic} rehberi",
                "{topic} 2024",
                "{topic} alternatifleri",
                "{topic} kurulumu",
                "{topic} kullanimi",
                "{topic} ipuclari",
            ]
        else:
            patterns = [
                "what is {topic}",
                "how to {topic}",
                "{topic} pricing",
                "{topic} reviews",
                "best {topic}",
                "{topic} recommendations",
                "{topic} comparison",
                "{topic} benefits",
                "{topic} drawbacks",
                "{topic} guide",
                "{topic} 2024",
                "{topic} alternatives",
                "{topic} setup",
                "{topic} tutorial",
                "{topic} tips",
            ]

        for p in patterns[:count]:
            kw = p.format(topic=topic)
            h = int(hashlib.md5(kw.encode()).hexdigest()[:8], 16)
            suggestions.append({
                "keyword": kw,
                "estimated_volume": (h % 5000) + 50,
                "difficulty": (h % 80) + 10,
            })

        return {
            "status": "success",
            "topic": topic,
            "count": len(suggestions),
            "suggestions": suggestions,
        }


# ─── 134: Content Planner ────────────────────────────────────────
class ContentPlannerSkill(BaseSkill):
    """SEO odakli icerik plani olusturur."""

    SKILL_ID = "134"
    NAME = "content_planner"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Belirli bir konu icin SEO odakli icerik plani olusturur."
    PARAMETERS = {
        "topic": "Ana konu",
        "target_audience": "Hedef kitle",
        "content_type": "Icerik turu (blog/guide/review)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        topic = params.get("topic", "")
        audience = params.get("target_audience", "genel")
        content_type = params.get("content_type", "blog")

        templates = {
            "blog": {
                "structure": ["Giris", "Problem Tanimi", "Cozum Yollari", "Ornekler", "Sonuc"],
                "word_count": "1500-2500",
                "headings": 5,
            },
            "guide": {
                "structure": ["Giris", "Temel Kavramlar", "Adim Adim Rehber", "Ipuclari", "SSS", "Sonuc"],
                "word_count": "3000-5000",
                "headings": 8,
            },
            "review": {
                "structure": ["Ozet", "Ozellikler", "Artilari", "Eksileri", "Karsilastirma", "Sonuc"],
                "word_count": "2000-3500",
                "headings": 6,
            },
        }

        tpl = templates.get(content_type, templates["blog"])

        outline = []
        for i, section in enumerate(tpl["structure"]):
            outline.append({
                "order": i + 1,
                "heading": f"{section}: {topic}" if i > 0 else f"{topic} - {section}",
                "type": "h2",
                "notes": f"Bu bolumde {topic} hakkinda {section.lower()} bilgileri verin.",
            })

        return {
            "status": "success",
            "topic": topic,
            "audience": audience,
            "content_type": content_type,
            "recommended_word_count": tpl["word_count"],
            "recommended_headings": tpl["headings"],
            "outline": outline,
            "seo_tips": [
                f"Basliklarda '{topic}' anahtar kelimesini kullanin",
                "Ilk 100 kelimede anahtar kelimeyi gecirin",
                "Gorsellere alt etiket ekleyin",
                "Ic ve dis baglanti ekleyin",
                "Meta aciklama yazin (120-160 karakter)",
            ],
        }


# ─── 135: Title Generator ────────────────────────────────────────
class TitleGeneratorSkill(BaseSkill):
    """SEO uyumlu baslik uretir."""

    SKILL_ID = "135"
    NAME = "title_generator"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Bir konu icin SEO uyumlu baslik alternatifleri uretir."
    PARAMETERS = {
        "keyword": "Ana anahtar kelime",
        "style": "Baslik stili (informative/listicle/how_to/question)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        keyword = params.get("keyword", "")
        style = params.get("style", "informative")

        title_templates = {
            "informative": [
                "{keyword}: Bilmeniz Gereken Her Sey",
                "{keyword} Rehberi: Kapsamli Kilavuz",
                "{keyword} Hakkinda Bilmeniz Gerekenler",
                "2024 {keyword} Rehberi: Eksiksiz Kaynak",
            ],
            "listicle": [
                "En Iyi 10 {keyword} Onerisi",
                "7 {keyword} Ipucu ve Trik",
                "{keyword}: 5 Onemli Adim",
                "15 {keyword} Stratejisi",
            ],
            "how_to": [
                "{keyword} Nasil Yapilir? Adim Adim",
                "{keyword} Baslangicindan Sonuna",
                "{keyword}: Yeni Baslayanlar Icin Rehber",
                "{keyword} Yapmak Icin 5 Kolay Adim",
            ],
            "question": [
                "{keyword} Nedir ve Neden Onemlidir?",
                "{keyword} Nasil Calisir?",
                "{keyword} Gerekli mi? Avantaj ve Dezavantajlar",
                "Neden {keyword} Secmelisiniz?",
            ],
        }

        templates = title_templates.get(style, title_templates["informative"])
        titles = []
        for t in templates:
            generated = t.format(keyword=keyword)
            titles.append({
                "title": generated,
                "length": len(generated),
                "optimal": 30 <= len(generated) <= 60,
            })

        return {
            "status": "success",
            "keyword": keyword,
            "style": style,
            "titles": titles,
        }


# ─── 136: Meta Description ───────────────────────────────────────
class MetaDescriptionSkill(BaseSkill):
    """Meta aciklama uretir ve optimize eder."""

    SKILL_ID = "136"
    NAME = "meta_description"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Sayfa icin meta aciklama uretir veya mevcut olanini analiz eder."
    PARAMETERS = {
        "keyword": "Ana anahtar kelime",
        "description": "Mevcut aciklama (opsiyonel, analiz icin)",
        "page_type": "Sayfa turu (homepage/product/blog/category)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        keyword = params.get("keyword", "")
        desc = params.get("description", "")
        page_type = params.get("page_type", "blog")

        # Analyze existing
        if desc:
            length = len(desc)
            has_keyword = keyword.lower() in desc.lower() if keyword else False
            has_cta = any(w in desc.lower() for w in ["kesfet", "incele", "ogrenin", "basvur", "simdi", "hemen"])
            score = 100
            tips = []
            if length < 120:
                score -= 20
                tips.append("Aciklama cok kisa, 120-160 karakter ideal")
            elif length > 160:
                score -= 10
                tips.append("Aciklama cok uzun, 160 karakteri gecmeyin")
            if not has_keyword:
                score -= 15
                tips.append("Anahtar kelimeyi ekleyin")
            if not has_cta:
                score -= 10
                tips.append("Aksiyon cagrisi (CTA) ekleyin")

            return {
                "status": "success",
                "mode": "analyze",
                "length": length,
                "has_keyword": has_keyword,
                "has_cta": has_cta,
                "score": max(score, 0),
                "tips": tips,
            }

        # Generate new
        templates = {
            "homepage": "{keyword} hakkinda en guncel bilgiler, rehberler ve uzman onerileri. Hemen kesfet!",
            "product": "{keyword} - Detayli ozellikler, fiyat ve kullanici yorumlari. Simdi inceleyin.",
            "blog": "{keyword} rehberimizde her seyi ogrenin. Uzman ipuclari, en iyi uygulamalar ve daha fazlasi.",
            "category": "En iyi {keyword} seceneklerini karsilastirin. Fiyat, ozellik ve yorumlarla dogru secimi yapin.",
        }

        generated = templates.get(page_type, templates["blog"]).format(keyword=keyword)

        return {
            "status": "success",
            "mode": "generate",
            "description": generated,
            "length": len(generated),
            "optimal": 120 <= len(generated) <= 160,
        }


# ─── 137: Schema Markup ──────────────────────────────────────────
class SchemaMarkupSkill(BaseSkill):
    """Schema.org yapisal veri olusturur."""

    SKILL_ID = "137"
    NAME = "schema_markup"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Schema.org JSON-LD yapisal veri uretir."
    PARAMETERS = {
        "schema_type": "Sema turu (article/product/faq/organization/breadcrumb)",
        "data": "Sema verileri (dict)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        schema_type = params.get("schema_type", "article")
        data = params.get("data", {})

        schemas = {
            "article": {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": data.get("title", ""),
                "description": data.get("description", ""),
                "author": {"@type": "Person", "name": data.get("author", "")},
                "datePublished": data.get("date", ""),
                "image": data.get("image", ""),
            },
            "product": {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "brand": {"@type": "Brand", "name": data.get("brand", "")},
                "offers": {
                    "@type": "Offer",
                    "price": data.get("price", "0"),
                    "priceCurrency": data.get("currency", "TRY"),
                    "availability": "https://schema.org/InStock",
                },
            },
            "faq": {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q.get("question", ""),
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": q.get("answer", ""),
                        },
                    }
                    for q in data.get("questions", [])
                ],
            },
            "organization": {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": data.get("name", ""),
                "url": data.get("url", ""),
                "logo": data.get("logo", ""),
                "contactPoint": {
                    "@type": "ContactPoint",
                    "telephone": data.get("phone", ""),
                    "contactType": "customer service",
                },
            },
            "breadcrumb": {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": item.get("name", ""),
                        "item": item.get("url", ""),
                    }
                    for i, item in enumerate(data.get("items", []))
                ],
            },
        }

        schema = schemas.get(schema_type, schemas["article"])
        json_ld = json.dumps(schema, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "schema_type": schema_type,
            "json_ld": json_ld,
            "html_tag": f'<script type="application/ld+json">\n{json_ld}\n</script>',
        }


# ─── 138: Backlink Analyzer ──────────────────────────────────────
class BacklinkAnalyzerSkill(BaseSkill):
    """Geri baglanti (backlink) analizi yapar."""

    SKILL_ID = "138"
    NAME = "backlink_analyzer"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Backlink listesini analiz eder ve kalite puani verir."
    PARAMETERS = {
        "backlinks": "Backlink listesi [{'url': ..., 'anchor': ..., 'domain_authority': ...}]",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        backlinks = params.get("backlinks", [])

        if not backlinks:
            return {"status": "success", "total": 0, "message": "Backlink bulunamadi"}

        total = len(backlinks)
        domains = set()
        anchors: dict[str, int] = {}
        da_scores = []

        for bl in backlinks:
            url = bl.get("url", "")
            anchor = bl.get("anchor", "")
            da = bl.get("domain_authority", 0)

            parsed = urlparse(url)
            if parsed.netloc:
                domains.add(parsed.netloc)

            anchors[anchor] = anchors.get(anchor, 0) + 1
            da_scores.append(da)

        avg_da = sum(da_scores) / len(da_scores) if da_scores else 0
        high_quality = sum(1 for d in da_scores if d >= 50)
        low_quality = sum(1 for d in da_scores if d < 20)

        # Anchor text diversity
        unique_anchors = len(anchors)
        anchor_diversity = round(unique_anchors / max(total, 1) * 100, 1)

        return {
            "status": "success",
            "total_backlinks": total,
            "unique_domains": len(domains),
            "average_da": round(avg_da, 1),
            "high_quality_count": high_quality,
            "low_quality_count": low_quality,
            "anchor_diversity_percent": anchor_diversity,
            "top_anchors": sorted(anchors.items(), key=lambda x: x[1], reverse=True)[:5],
        }


# ─── 139: Page Speed ─────────────────────────────────────────────
class PageSpeedSkill(BaseSkill):
    """Sayfa hiz analizi ve optimizasyon onerileri."""

    SKILL_ID = "139"
    NAME = "page_speed"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Sayfa hiz metriklerini analiz eder ve iyilestirme onerir."
    PARAMETERS = {
        "metrics": "Hiz metrikleri {'lcp': ms, 'fid': ms, 'cls': float, 'ttfb': ms, 'fcp': ms}",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        metrics = params.get("metrics", {})

        lcp = metrics.get("lcp", 3000)  # ms
        fid = metrics.get("fid", 200)   # ms
        cls = metrics.get("cls", 0.15)  # score
        ttfb = metrics.get("ttfb", 800) # ms
        fcp = metrics.get("fcp", 2000)  # ms

        # Core Web Vitals scoring
        def score_lcp(v: float) -> str:
            return "good" if v <= 2500 else "needs_improvement" if v <= 4000 else "poor"

        def score_fid(v: float) -> str:
            return "good" if v <= 100 else "needs_improvement" if v <= 300 else "poor"

        def score_cls(v: float) -> str:
            return "good" if v <= 0.1 else "needs_improvement" if v <= 0.25 else "poor"

        results = {
            "lcp": {"value_ms": lcp, "rating": score_lcp(lcp)},
            "fid": {"value_ms": fid, "rating": score_fid(fid)},
            "cls": {"value": cls, "rating": score_cls(cls)},
            "ttfb": {"value_ms": ttfb, "rating": "good" if ttfb <= 600 else "needs_improvement" if ttfb <= 1500 else "poor"},
            "fcp": {"value_ms": fcp, "rating": "good" if fcp <= 1800 else "needs_improvement" if fcp <= 3000 else "poor"},
        }

        # Overall score
        ratings = [r["rating"] for r in results.values()]
        good_count = ratings.count("good")
        overall = round(good_count / len(ratings) * 100)

        recommendations = []
        if results["lcp"]["rating"] != "good":
            recommendations.append("Gorselleri optimize edin (WebP, lazy loading)")
        if results["fid"]["rating"] != "good":
            recommendations.append("JavaScript yukunu azaltin")
        if results["cls"]["rating"] != "good":
            recommendations.append("Gorsel ve reklam boyutlarini tanimlayin")
        if results["ttfb"]["rating"] != "good":
            recommendations.append("Sunucu yanit suresini iyilestirin (CDN, cache)")
        if results["fcp"]["rating"] != "good":
            recommendations.append("Kritik CSS'i satir ici yapin")

        return {
            "status": "success",
            "overall_score": overall,
            "core_web_vitals": results,
            "recommendations": recommendations,
        }


# ─── 140: Mobile Checker ─────────────────────────────────────────
class MobileCheckerSkill(BaseSkill):
    """Mobil uyumluluk kontrolu yapar."""

    SKILL_ID = "140"
    NAME = "mobile_checker"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Sayfa mobil uyumlulugunu kontrol eder."
    PARAMETERS = {
        "has_viewport": "Viewport meta etiketi var mi (bool)",
        "font_size_min": "Minimum font boyutu (px)",
        "tap_targets_ok": "Dokunma hedefleri yeterli mi (bool)",
        "no_horizontal_scroll": "Yatay kayma yok mu (bool)",
        "responsive_images": "Gorseller duyarli mi (bool)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        viewport = params.get("has_viewport", True)
        font_size = params.get("font_size_min", 16)
        tap_ok = params.get("tap_targets_ok", True)
        no_hscroll = params.get("no_horizontal_scroll", True)
        resp_images = params.get("responsive_images", True)

        issues = []
        score = 100

        if not viewport:
            issues.append("Viewport meta etiketi eksik")
            score -= 25
        if font_size < 16:
            issues.append(f"Font boyutu cok kucuk ({font_size}px, min 16px)")
            score -= 15
        if not tap_ok:
            issues.append("Dokunma hedefleri cok kucuk (min 48x48px)")
            score -= 20
        if not no_hscroll:
            issues.append("Yatay kayma tespit edildi")
            score -= 20
        if not resp_images:
            issues.append("Gorseller duyarli degil (srcset eksik)")
            score -= 10

        score = max(score, 0)

        return {
            "status": "success",
            "mobile_friendly": score >= 80,
            "score": score,
            "issues": issues,
            "checks": {
                "viewport": viewport,
                "font_size_ok": font_size >= 16,
                "tap_targets_ok": tap_ok,
                "no_horizontal_scroll": no_hscroll,
                "responsive_images": resp_images,
            },
        }


# ─── 141: Readability Checker ────────────────────────────────────
class ReadabilityCheckerSkill(BaseSkill):
    """Icerik okunabilirlik analizi yapar."""

    SKILL_ID = "141"
    NAME = "readability_checker"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Metin okunabilirligini Flesch skoru ile analiz eder."
    PARAMETERS = {
        "text": "Analiz edilecek metin",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        text = params.get("text", "")
        if not text:
            return {"status": "error", "message": "Metin bos"}

        # Count sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = max(len(sentences), 1)

        # Count words
        words = text.split()
        word_count = max(len(words), 1)

        # Count syllables (simplified)
        vowels = set("aeiouyAEIOUYaeiouöüçğışÖÜÇĞİŞ")

        def count_syllables(word: str) -> int:
            count = 0
            prev_vowel = False
            for ch in word:
                is_vowel = ch in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel
            return max(count, 1)

        total_syllables = sum(count_syllables(w) for w in words)

        # Flesch Reading Ease
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = total_syllables / word_count
        flesch = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        flesch = round(max(min(flesch, 100), 0), 1)

        if flesch >= 80:
            level = "cok_kolay"
            grade = "A"
        elif flesch >= 60:
            level = "kolay"
            grade = "B"
        elif flesch >= 40:
            level = "orta"
            grade = "C"
        elif flesch >= 20:
            level = "zor"
            grade = "D"
        else:
            level = "cok_zor"
            grade = "F"

        # Paragraph analysis
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        long_paragraphs = sum(1 for p in paragraphs if len(p.split()) > 150)

        return {
            "status": "success",
            "flesch_score": flesch,
            "level": level,
            "grade": grade,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "paragraph_count": len(paragraphs),
            "long_paragraphs": long_paragraphs,
        }


# ─── 142: Content Gap ────────────────────────────────────────────
class ContentGapSkill(BaseSkill):
    """Icerik eksikligi analizi yapar."""

    SKILL_ID = "142"
    NAME = "content_gap"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Mevcut icerik ile hedef anahtar kelimeler arasindaki bosluklari tespit eder."
    PARAMETERS = {
        "current_keywords": "Mevcut hedeflenen anahtar kelimeler listesi",
        "competitor_keywords": "Rakip anahtar kelimeleri listesi",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        current = set(params.get("current_keywords", []))
        competitor = set(params.get("competitor_keywords", []))

        # Gaps: competitor has but we don't
        gaps = competitor - current
        # Overlap
        overlap = current & competitor
        # Unique to us
        unique = current - competitor

        opportunities = []
        for kw in sorted(gaps):
            h = int(hashlib.md5(kw.encode()).hexdigest()[:8], 16)
            opportunities.append({
                "keyword": kw,
                "estimated_difficulty": (h % 70) + 10,
                "priority": "high" if (h % 3) == 0 else "medium",
            })

        return {
            "status": "success",
            "gap_count": len(gaps),
            "overlap_count": len(overlap),
            "unique_count": len(unique),
            "gaps": sorted(gaps),
            "overlap": sorted(overlap),
            "unique_to_you": sorted(unique),
            "opportunities": opportunities[:20],
        }


# ─── 143: SERP Previewer ─────────────────────────────────────────
class SerpPreviewerSkill(BaseSkill):
    """Google SERP onizleme olusturur."""

    SKILL_ID = "143"
    NAME = "serp_previewer"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Google arama sonuclari onizlemesi olusturur ve optimize eder."
    PARAMETERS = {
        "title": "Sayfa basligi",
        "url": "Sayfa URL'i",
        "description": "Meta aciklama",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        title = params.get("title", "")
        url = params.get("url", "")
        description = params.get("description", "")

        # Title analysis
        title_len = len(title)
        title_truncated = title[:60] + "..." if title_len > 60 else title
        title_ok = 30 <= title_len <= 60

        # URL analysis
        parsed = urlparse(url)
        display_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if len(display_url) > 80:
            display_url = display_url[:77] + "..."
        url_ok = len(parsed.path) < 80

        # Description analysis
        desc_len = len(description)
        desc_truncated = description[:160] + "..." if desc_len > 160 else description
        desc_ok = 120 <= desc_len <= 160

        # Pixel width estimation (rough: ~6px per char)
        title_pixel = title_len * 6
        title_pixel_ok = title_pixel <= 580

        preview = f"""┌─────────────────────────────────────────────┐
│ {title_truncated:<43} │
│ {display_url:<43} │
│ {desc_truncated[:43]:<43} │
│ {desc_truncated[43:86]:<43} │
└─────────────────────────────────────────────┘"""

        return {
            "status": "success",
            "preview_text": preview,
            "analysis": {
                "title": {"length": title_len, "optimal": title_ok, "truncated": title_len > 60},
                "url": {"display": display_url, "optimal": url_ok},
                "description": {"length": desc_len, "optimal": desc_ok, "truncated": desc_len > 160},
            },
        }


# ─── 144: Internal Link ──────────────────────────────────────────
class InternalLinkSkill(BaseSkill):
    """Ic baglanti analizi yapar."""

    SKILL_ID = "144"
    NAME = "internal_link"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Ic baglanti yapisini analiz eder ve oneri sunar."
    PARAMETERS = {
        "pages": "Sayfa listesi [{'url': ..., 'links_to': [...], 'title': ...}]",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        pages = params.get("pages", [])

        if not pages:
            return {"status": "success", "total_pages": 0, "message": "Sayfa bulunamadi"}

        total_pages = len(pages)
        total_links = 0
        orphan_pages: list[str] = []
        link_counts: dict[str, int] = {}

        all_urls = {p.get("url", "") for p in pages}

        for page in pages:
            url = page.get("url", "")
            links = page.get("links_to", [])
            total_links += len(links)
            for link in links:
                link_counts[link] = link_counts.get(link, 0) + 1

        # Find orphan pages (no incoming links)
        for url in all_urls:
            if link_counts.get(url, 0) == 0:
                orphan_pages.append(url)

        avg_links = round(total_links / max(total_pages, 1), 1)

        # Most linked pages
        top_linked = sorted(link_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        recommendations = []
        if orphan_pages:
            recommendations.append(f"{len(orphan_pages)} yetim sayfa bulundu, ic baglanti ekleyin")
        if avg_links < 3:
            recommendations.append("Ortalama ic baglanti sayisi dusuk, daha fazla baglanti ekleyin")

        return {
            "status": "success",
            "total_pages": total_pages,
            "total_internal_links": total_links,
            "avg_links_per_page": avg_links,
            "orphan_pages": orphan_pages,
            "top_linked_pages": [{"url": u, "incoming": c} for u, c in top_linked],
            "recommendations": recommendations,
        }


# ─── 145: Anchor Text ────────────────────────────────────────────
class AnchorTextSkill(BaseSkill):
    """Anchor text analizi yapar."""

    SKILL_ID = "145"
    NAME = "anchor_text"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Baglanti metinlerini (anchor text) analiz eder ve optimize eder."
    PARAMETERS = {
        "anchors": "Anchor text listesi [{'text': ..., 'url': ..., 'type': ...}]",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        anchors = params.get("anchors", [])

        if not anchors:
            return {"status": "success", "total": 0, "message": "Anchor text bulunamadi"}

        total = len(anchors)
        type_counts: dict[str, int] = {}
        text_counts: dict[str, int] = {}

        for a in anchors:
            text = a.get("text", "").strip()
            a_type = a.get("type", "unknown")

            # Auto-detect type
            if not text or text.lower() in ("", "buraya tikla", "tikla", "click here"):
                a_type = "generic"
            elif text.startswith("http"):
                a_type = "naked_url"
            elif len(text.split()) <= 2:
                a_type = "exact_match"
            else:
                a_type = "partial_match"

            type_counts[a_type] = type_counts.get(a_type, 0) + 1
            text_counts[text] = text_counts.get(text, 0) + 1

        # Distribution
        distribution = {t: round(c / total * 100, 1) for t, c in type_counts.items()}

        issues = []
        generic_pct = distribution.get("generic", 0)
        if generic_pct > 20:
            issues.append(f"Genel anchor text orani yuksek ({generic_pct}%)")
        exact_pct = distribution.get("exact_match", 0)
        if exact_pct > 60:
            issues.append(f"Birebir eslesen anchor text orani cok yuksek ({exact_pct}%), dogal gorunmuyor")

        return {
            "status": "success",
            "total": total,
            "type_distribution": distribution,
            "top_anchors": sorted(text_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "issues": issues,
            "healthy": len(issues) == 0,
        }


# ─── 146: Content Brief ──────────────────────────────────────────
class ContentBriefSkill(BaseSkill):
    """Icerik brifingi olusturur."""

    SKILL_ID = "146"
    NAME = "content_brief"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Yazarlar icin detayli icerik brifingi olusturur."
    PARAMETERS = {
        "keyword": "Hedef anahtar kelime",
        "secondary_keywords": "Ikincil anahtar kelimeler (liste)",
        "target_word_count": "Hedef kelime sayisi",
        "audience": "Hedef kitle",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        keyword = params.get("keyword", "")
        secondary = params.get("secondary_keywords", [])
        target_wc = int(params.get("target_word_count", 2000))
        audience = params.get("audience", "genel")

        brief = {
            "title_suggestions": [
                f"{keyword}: Kapsamli Rehber",
                f"{keyword} Hakkinda Bilmeniz Gereken Her Sey",
                f"2024 {keyword} Kilavuzu",
            ],
            "primary_keyword": keyword,
            "secondary_keywords": secondary,
            "target_word_count": target_wc,
            "target_audience": audience,
            "outline": [
                {"heading": "Giris", "word_count": int(target_wc * 0.1)},
                {"heading": f"{keyword} Nedir?", "word_count": int(target_wc * 0.15)},
                {"heading": "Neden Onemlidir?", "word_count": int(target_wc * 0.15)},
                {"heading": "Nasil Kullanilir?", "word_count": int(target_wc * 0.25)},
                {"heading": "En Iyi Uygulamalar", "word_count": int(target_wc * 0.2)},
                {"heading": "SSS", "word_count": int(target_wc * 0.1)},
                {"heading": "Sonuc", "word_count": int(target_wc * 0.05)},
            ],
            "seo_requirements": {
                "keyword_density": "1-2%",
                "keyword_in_title": True,
                "keyword_in_first_paragraph": True,
                "keyword_in_h2": True,
                "internal_links": "3-5",
                "external_links": "2-3",
                "images": "3-5 gorsel, alt etiketli",
                "meta_description": "120-160 karakter",
            },
            "tone": "bilgilendirici, akici, uzman",
        }

        return {"status": "success", "brief": brief}


# ─── 147: Local SEO ──────────────────────────────────────────────
class LocalSeoSkill(BaseSkill):
    """Yerel SEO analizi yapar."""

    SKILL_ID = "147"
    NAME = "local_seo"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Yerel SEO faktorlerini analiz eder ve puanlar."
    PARAMETERS = {
        "business_name": "Isletme adi",
        "address": "Adres",
        "phone": "Telefon",
        "google_my_business": "Google Isletme Profili var mi (bool)",
        "nap_consistent": "NAP (ad/adres/tel) tutarli mi (bool)",
        "reviews_count": "Yorum sayisi",
        "avg_rating": "Ortalama puan (1-5)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        name = params.get("business_name", "")
        address = params.get("address", "")
        phone = params.get("phone", "")
        gmb = params.get("google_my_business", False)
        nap = params.get("nap_consistent", True)
        reviews = int(params.get("reviews_count", 0))
        rating = float(params.get("avg_rating", 0))

        score = 0
        issues = []
        checks = {}

        # GMB
        if gmb:
            score += 25
            checks["google_my_business"] = True
        else:
            issues.append("Google Isletme Profili olusturun")
            checks["google_my_business"] = False

        # NAP
        if nap:
            score += 20
            checks["nap_consistent"] = True
        else:
            issues.append("NAP bilgilerini tum platformlarda tutarli yapin")
            checks["nap_consistent"] = False

        # Reviews
        if reviews >= 50:
            score += 20
        elif reviews >= 10:
            score += 10
            issues.append("Daha fazla yorum toplayin (hedef: 50+)")
        else:
            issues.append(f"Yorum sayisi cok dusuk ({reviews}), musteri yorumlari isteyin")

        # Rating
        if rating >= 4.5:
            score += 20
        elif rating >= 4.0:
            score += 15
        elif rating >= 3.5:
            score += 10
            issues.append("Musteri memnuniyetini arttirin")
        else:
            issues.append(f"Ortalama puan dusuk ({rating}), hizmet kalitesini arttirin")

        # Basic info
        if name and address and phone:
            score += 15
            checks["complete_info"] = True
        else:
            issues.append("Isletme bilgilerini tamamlayin")
            checks["complete_info"] = False

        return {
            "status": "success",
            "score": min(score, 100),
            "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D",
            "checks": checks,
            "issues": issues,
            "reviews_count": reviews,
            "avg_rating": rating,
        }


# ─── 148: Technical SEO ──────────────────────────────────────────
class TechnicalSeoSkill(BaseSkill):
    """Teknik SEO kontrolu yapar."""

    SKILL_ID = "148"
    NAME = "technical_seo"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Teknik SEO faktorlerini kontrol eder ve raporlar."
    PARAMETERS = {
        "has_ssl": "SSL sertifikasi var mi",
        "has_sitemap": "Sitemap.xml var mi",
        "has_robots_txt": "Robots.txt var mi",
        "is_mobile_friendly": "Mobil uyumlu mu",
        "page_speed_score": "Sayfa hiz puani (0-100)",
        "has_canonical": "Canonical URL tanimli mi",
        "has_hreflang": "Hreflang etiketi var mi",
        "http_status": "HTTP durum kodu",
        "redirect_chain": "Yonlendirme zinciri uzunlugu",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        checks = {
            "ssl": params.get("has_ssl", True),
            "sitemap": params.get("has_sitemap", True),
            "robots_txt": params.get("has_robots_txt", True),
            "mobile_friendly": params.get("is_mobile_friendly", True),
            "canonical": params.get("has_canonical", True),
            "hreflang": params.get("has_hreflang", False),
        }
        speed = int(params.get("page_speed_score", 50))
        http_status = int(params.get("http_status", 200))
        redirects = int(params.get("redirect_chain", 0))

        score = 0
        issues = []
        weights = {"ssl": 15, "sitemap": 10, "robots_txt": 10, "mobile_friendly": 15, "canonical": 10, "hreflang": 5}

        for check, passed in checks.items():
            if passed:
                score += weights.get(check, 5)
            else:
                issues.append(f"{check} eksik veya hatali")

        # Speed
        if speed >= 90:
            score += 20
        elif speed >= 50:
            score += 10
            issues.append(f"Sayfa hizi orta ({speed}/100)")
        else:
            issues.append(f"Sayfa hizi dusuk ({speed}/100)")

        # HTTP status
        if http_status == 200:
            score += 10
        else:
            issues.append(f"HTTP durum kodu: {http_status}")

        # Redirects
        if redirects > 2:
            issues.append(f"Yonlendirme zinciri cok uzun ({redirects} adim)")
            score -= 5

        score = max(min(score, 100), 0)

        return {
            "status": "success",
            "score": score,
            "grade": "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D",
            "checks": checks,
            "page_speed_score": speed,
            "http_status": http_status,
            "redirect_chain_length": redirects,
            "issues": issues,
        }


# ─── 149: Social SEO ─────────────────────────────────────────────
class SocialSeoSkill(BaseSkill):
    """Sosyal medya SEO analizi yapar."""

    SKILL_ID = "149"
    NAME = "social_seo"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Open Graph ve Twitter Card etiketlerini analiz eder."
    PARAMETERS = {
        "og_title": "Open Graph basligi",
        "og_description": "Open Graph aciklamasi",
        "og_image": "Open Graph gorseli URL'i",
        "og_type": "Open Graph turu",
        "twitter_card": "Twitter card turu",
        "twitter_title": "Twitter basligi",
        "twitter_description": "Twitter aciklamasi",
        "twitter_image": "Twitter gorseli URL'i",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        og_title = params.get("og_title", "")
        og_desc = params.get("og_description", "")
        og_image = params.get("og_image", "")
        og_type = params.get("og_type", "")
        tw_card = params.get("twitter_card", "")
        tw_title = params.get("twitter_title", "")
        tw_desc = params.get("twitter_description", "")
        tw_image = params.get("twitter_image", "")

        issues = []
        score = 100

        # Open Graph
        if not og_title:
            issues.append("og:title eksik")
            score -= 15
        if not og_desc:
            issues.append("og:description eksik")
            score -= 10
        if not og_image:
            issues.append("og:image eksik (paylasimda gorsel gorunmez)")
            score -= 15
        if not og_type:
            issues.append("og:type eksik")
            score -= 5

        # Twitter Card
        if not tw_card:
            issues.append("twitter:card eksik")
            score -= 10
        if not tw_title and not og_title:
            issues.append("Twitter basligi eksik (og:title de yok)")
            score -= 5

        score = max(score, 0)

        # Generate missing tags
        suggested_tags = []
        if not og_title:
            suggested_tags.append('<meta property="og:title" content="BASLIK" />')
        if not og_desc:
            suggested_tags.append('<meta property="og:description" content="ACIKLAMA" />')
        if not og_image:
            suggested_tags.append('<meta property="og:image" content="GORSEL_URL" />')
        if not tw_card:
            suggested_tags.append('<meta name="twitter:card" content="summary_large_image" />')

        return {
            "status": "success",
            "score": score,
            "open_graph": {
                "title": og_title or None,
                "description": og_desc or None,
                "image": og_image or None,
                "type": og_type or None,
            },
            "twitter_card": {
                "card": tw_card or None,
                "title": tw_title or og_title or None,
                "description": tw_desc or og_desc or None,
                "image": tw_image or og_image or None,
            },
            "issues": issues,
            "suggested_tags": suggested_tags,
        }


# ─── 150: Competitor Analyzer ────────────────────────────────────
class CompetitorAnalyzerSkill(BaseSkill):
    """Rakip SEO analizi yapar."""

    SKILL_ID = "150"
    NAME = "competitor_analyzer"
    CATEGORY = "seo_tools"
    RISK_LEVEL = "low"
    DESCRIPTION = "Rakip web sitelerinin SEO metriklerini karsilastirir."
    PARAMETERS = {
        "competitors": "Rakip listesi [{'domain': ..., 'da': ..., 'keywords': ..., 'backlinks': ..., 'traffic': ...}]",
        "my_domain": "Kendi domain bilgileri (ayni format)",
    }

    def _execute_impl(self, **params: Any) -> dict[str, Any]:
        competitors = params.get("competitors", [])
        my_domain = params.get("my_domain", {})

        if not competitors:
            return {"status": "success", "message": "Rakip verisi yok"}

        my_da = my_domain.get("da", 0)
        my_kw = my_domain.get("keywords", 0)
        my_bl = my_domain.get("backlinks", 0)
        my_traffic = my_domain.get("traffic", 0)

        analysis = []
        for comp in competitors:
            domain = comp.get("domain", "")
            c_da = comp.get("da", 0)
            c_kw = comp.get("keywords", 0)
            c_bl = comp.get("backlinks", 0)
            c_traffic = comp.get("traffic", 0)

            gaps = []
            if c_da > my_da:
                gaps.append(f"Domain Authority fark: {c_da - my_da}")
            if c_kw > my_kw:
                gaps.append(f"Anahtar kelime fark: {c_kw - my_kw}")
            if c_bl > my_bl:
                gaps.append(f"Backlink fark: {c_bl - my_bl}")

            strength = "weak" if c_da < my_da else "equal" if c_da == my_da else "strong"

            analysis.append({
                "domain": domain,
                "da": c_da,
                "keywords": c_kw,
                "backlinks": c_bl,
                "traffic": c_traffic,
                "relative_strength": strength,
                "gaps": gaps,
            })

        # Sort by DA
        analysis.sort(key=lambda x: x["da"], reverse=True)

        avg_da = sum(c.get("da", 0) for c in competitors) / len(competitors)
        avg_kw = sum(c.get("keywords", 0) for c in competitors) / len(competitors)

        return {
            "status": "success",
            "my_domain": my_domain.get("domain", ""),
            "competitor_count": len(competitors),
            "competitors": analysis,
            "market_avg_da": round(avg_da, 1),
            "market_avg_keywords": round(avg_kw),
            "my_position": "above_average" if my_da > avg_da else "below_average",
        }


# ─── Export ───────────────────────────────────────────────────────
ALL_SEO_SKILLS: list[type[BaseSkill]] = [
    SeoAnalyzerSkill,
    KeywordResearcherSkill,
    KeywordSuggesterSkill,
    ContentPlannerSkill,
    TitleGeneratorSkill,
    MetaDescriptionSkill,
    SchemaMarkupSkill,
    BacklinkAnalyzerSkill,
    PageSpeedSkill,
    MobileCheckerSkill,
    ReadabilityCheckerSkill,
    ContentGapSkill,
    SerpPreviewerSkill,
    InternalLinkSkill,
    AnchorTextSkill,
    ContentBriefSkill,
    LocalSeoSkill,
    TechnicalSeoSkill,
    SocialSeoSkill,
    CompetitorAnalyzerSkill,
]
