"""Iletisim ve yazi becerileri.

Email, blog, makale, sozlesme,
profesyonel yazi sablonlari
icin 25 beceri.
"""

from typing import Any

from app.core.skills.base_skill import BaseSkill


class EmailWriterSkill(BaseSkill):
    """Email yazma becerisi."""

    SKILL_ID = "176"
    NAME = "email_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Profesyonel email yazma "
        "(resmi, samimi, acil)"
    )
    PARAMETERS = {
        "purpose": "Amac",
        "recipient": "Alici",
        "tone": "Ton",
        "key_points": "Ana noktalar",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        purpose = p.get("purpose", "")
        recipient = p.get("recipient", "")
        tone = p.get("tone", "formal")
        points = p.get("key_points", [])

        greeting = (
            "Sayin" if tone == "formal"
            else "Merhaba"
        )
        body = ". ".join(
            points if isinstance(points, list)
            else [str(points)]
        )

        return {
            "subject": f"Re: {purpose}",
            "greeting": f"{greeting} {recipient},",
            "body": body,
            "closing": (
                "Saygilarimla"
                if tone == "formal"
                else "Iyi gunler"
            ),
            "tone": tone,
            "word_count": len(body.split()),
        }


class EmailReplySuggesterSkill(BaseSkill):
    """Email yanit onerisi becerisi."""

    SKILL_ID = "177"
    NAME = "email_reply_suggester"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Gelen emaile yanit onerisi"
    PARAMETERS = {
        "original_email": "Orijinal email",
        "desired_tone": "Istenen ton",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        original = p.get("original_email", "")
        tone = p.get("desired_tone", "formal")
        return {
            "original_length": len(original),
            "tone": tone,
            "suggestions": [
                f"[{tone} yanit onerisi 1]",
                f"[{tone} yanit onerisi 2]",
                f"[{tone} yanit onerisi 3]",
            ],
        }


class CoverLetterWriterSkill(BaseSkill):
    """On yazi becerisi."""

    SKILL_ID = "178"
    NAME = "cover_letter_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Is basvurusu on yazi"
    PARAMETERS = {
        "job_title": "Pozisyon",
        "company": "Sirket",
        "skills": "Beceriler",
        "experience": "Deneyim",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        job = p.get("job_title", "")
        company = p.get("company", "")
        skills = p.get("skills", [])
        return {
            "job_title": job,
            "company": company,
            "sections": [
                "Giris",
                "Neden bu pozisyon",
                "Beceriler ve deneyim",
                "Motivasyon",
                "Kapanis",
            ],
            "skills_highlighted": skills,
        }


class ResumeBulletWriterSkill(BaseSkill):
    """Ozgecmis madde becerisi."""

    SKILL_ID = "179"
    NAME = "resume_bullet_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Ozgecmis madde isaretleri yazma "
        "(STAR yontemi)"
    )
    PARAMETERS = {
        "role": "Pozisyon",
        "achievement": "Basari",
        "metrics": "Metrikler",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        role = p.get("role", "")
        achievement = p.get("achievement", "")
        metrics = p.get("metrics", "")
        bullet = (
            f"{achievement}"
            + (f", {metrics}" if metrics else "")
        )
        return {
            "role": role,
            "bullet": bullet,
            "method": "STAR",
            "components": {
                "situation": "Baglam",
                "task": "Gorev",
                "action": achievement,
                "result": metrics,
            },
        }


class LinkedinProfileOptimizerSkill(BaseSkill):
    """LinkedIn profil becerisi."""

    SKILL_ID = "180"
    NAME = "linkedin_profile_optimizer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "LinkedIn profil metni optimizasyonu"
    )
    PARAMETERS = {
        "current_headline": "Mevcut baslik",
        "current_summary": "Mevcut ozet",
        "target_role": "Hedef pozisyon",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        target = p.get("target_role", "")
        return {
            "headline_suggestions": [
                f"{target} | Innovation",
                f"Experienced {target}",
            ],
            "summary_tips": [
                "Ilk 3 satir kritik",
                "Rakamlarla destekle",
                "Anahtar kelime ekle",
            ],
            "target_role": target,
        }


class BlogPostWriterSkill(BaseSkill):
    """Blog yazisi becerisi."""

    SKILL_ID = "181"
    NAME = "blog_post_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Blog yazisi olusturma (SEO uyumlu)"
    )
    PARAMETERS = {
        "topic": "Konu",
        "keywords": "Anahtar kelimeler",
        "length": "Uzunluk",
        "tone": "Ton",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        topic = p.get("topic", "")
        length = p.get("length", "medium")
        word_target = {
            "short": 500,
            "medium": 1000,
            "long": 2000,
        }.get(length, 1000)
        return {
            "topic": topic,
            "outline": [
                "Giris", "Ana bolum 1",
                "Ana bolum 2", "Sonuc",
            ],
            "target_words": word_target,
            "seo_tips": [
                "Baslikta anahtar kelime",
                "Ilk 100 kelimede keyword",
                "Alt basliklar kullan",
            ],
        }


class ArticleOutlineSkill(BaseSkill):
    """Makale taslagi becerisi."""

    SKILL_ID = "182"
    NAME = "article_outline"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Makale taslagi olusturma"
    PARAMETERS = {
        "topic": "Konu",
        "sections_count": "Bolum sayisi",
        "depth": "Derinlik",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        topic = p.get("topic", "")
        sections = int(
            p.get("sections_count", 5),
        )
        outline = [
            f"Bolum {i+1}: {topic} - Alt konu {i+1}"
            for i in range(sections)
        ]
        return {
            "topic": topic,
            "outline": outline,
            "sections": sections,
        }


class PressReleaseWriterSkill(BaseSkill):
    """Basin bulteni becerisi."""

    SKILL_ID = "183"
    NAME = "press_release_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Basin bulteni yazma"
    PARAMETERS = {
        "news": "Haber",
        "company": "Sirket",
        "quotes": "Alintilar",
        "contact": "Iletisim",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        news = p.get("news", "")
        company = p.get("company", "")
        return {
            "headline": f"{company}: {news}",
            "sections": [
                "Baslik", "Alt baslik",
                "Giris paragrafi", "Detaylar",
                "Alintilar", "Hakkinda",
                "Iletisim",
            ],
            "word_count_target": 400,
        }


class ProductDescriptionSkill(BaseSkill):
    """Urun aciklamasi becerisi."""

    SKILL_ID = "184"
    NAME = "product_description"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Urun aciklamasi yazma "
        "(e-ticaret uyumlu)"
    )
    PARAMETERS = {
        "product_name": "Urun adi",
        "features": "Ozellikler",
        "benefits": "Faydalar",
        "target_audience": "Hedef kitle",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        name = p.get("product_name", "")
        features = p.get("features", [])
        benefits = p.get("benefits", [])
        return {
            "product_name": name,
            "title": f"{name} - Premium",
            "feature_count": len(features),
            "benefit_count": len(benefits),
            "sections": [
                "Kisa aciklama",
                "Ozellikler",
                "Faydalar",
                "Teknik detaylar",
            ],
        }


class SloganGeneratorSkill(BaseSkill):
    """Slogan onerisi becerisi."""

    SKILL_ID = "185"
    NAME = "slogan_generator"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Marka/urun slogani onerileri"
    PARAMETERS = {
        "brand": "Marka",
        "values": "Degerler",
        "target": "Hedef kitle",
        "count": "Oneri sayisi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        brand = p.get("brand", "ATLAS")
        count = int(p.get("count", 5))
        templates = [
            f"{brand} - Gelecegin Cozumu",
            f"{brand} ile Basariya Ulasin",
            f"Daha Iyisi Icin {brand}",
            f"{brand}: Akilli Secim",
            f"{brand} - Fark Yaratin",
            f"Guvenin Adi: {brand}",
            f"{brand} ile Her Sey Mumkun",
            f"Kalite = {brand}",
        ]
        return {
            "brand": brand,
            "slogans": templates[:count],
            "count": min(count, len(templates)),
        }


class SpeechWriterSkill(BaseSkill):
    """Konusma metni becerisi."""

    SKILL_ID = "186"
    NAME = "speech_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Konusma metni yazma"
    PARAMETERS = {
        "occasion": "Vesile",
        "audience": "Dinleyici",
        "duration": "Sure (dk)",
        "key_message": "Ana mesaj",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        duration = int(p.get("duration", 5))
        words = duration * 130
        return {
            "occasion": p.get("occasion", ""),
            "target_words": words,
            "duration_minutes": duration,
            "structure": [
                "Dikkat cekici acilis",
                "Ana mesaj",
                "Destekleyici noktalar",
                "Kapanis",
            ],
        }


class ToastWriterSkill(BaseSkill):
    """Kadeh kaldirma metni becerisi."""

    SKILL_ID = "187"
    NAME = "toast_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kadeh kaldirma metni"
    PARAMETERS = {
        "occasion": "Vesile",
        "honoree": "Onurlandirilan",
        "relationship": "Iliski",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        occasion = p.get("occasion", "")
        honoree = p.get("honoree", "")
        return {
            "occasion": occasion,
            "honoree": honoree,
            "structure": [
                "Selamlama",
                "Kisisel hikaye",
                "Dilek",
                "Kadeh kaldirma",
            ],
            "target_duration": "1-2 dakika",
        }


class ApologyLetterSkill(BaseSkill):
    """Ozur mektubu becerisi."""

    SKILL_ID = "188"
    NAME = "apology_letter"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Ozur mektubu yazma"
    PARAMETERS = {
        "situation": "Durum",
        "recipient": "Alici",
        "tone": "Ton",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        situation = p.get("situation", "")
        tone = p.get("tone", "sincere")
        return {
            "situation": situation,
            "tone": tone,
            "sections": [
                "Ozur ifadesi",
                "Sorumluluk kabulu",
                "Duzeltme plani",
                "Gelecek taahhut",
            ],
        }


class ThankYouNoteSkill(BaseSkill):
    """Tesekkur notu becerisi."""

    SKILL_ID = "189"
    NAME = "thank_you_note"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Tesekkur notu yazma"
    PARAMETERS = {
        "occasion": "Vesile",
        "recipient": "Alici",
        "specific_thanks": "Ozel tesekkur",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        return {
            "occasion": p.get("occasion", ""),
            "recipient": p.get("recipient", ""),
            "structure": [
                "Tesekkur ifadesi",
                "Ozel detay",
                "Etkisi",
                "Kapanis",
            ],
        }


class ComplaintLetterSkill(BaseSkill):
    """Sikayet mektubu becerisi."""

    SKILL_ID = "190"
    NAME = "complaint_letter"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Sikayet mektubu yazma"
    PARAMETERS = {
        "issue": "Sorun",
        "company": "Sirket",
        "desired_resolution": "Istenen cozum",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        return {
            "issue": p.get("issue", ""),
            "company": p.get("company", ""),
            "structure": [
                "Sorun tanimi",
                "Tarihce",
                "Etki",
                "Istenen cozum",
                "Son tarih",
            ],
        }


class ContractTemplateSkill(BaseSkill):
    """Sozlesme sablonu becerisi."""

    SKILL_ID = "191"
    NAME = "contract_template"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Temel sozlesme sablonlari "
        "(NDA, freelance, kiralama)"
    )
    PARAMETERS = {
        "type": "Sozlesme tipi",
        "parties": "Taraflar",
        "terms": "Kosullar",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        ctype = p.get("type", "NDA")
        sections_map = {
            "NDA": [
                "Taraflar", "Tanimlar",
                "Gizlilik yukumlulukleri",
                "Sure", "Istisnalar",
                "Ihlal sonuclari",
            ],
            "freelance": [
                "Taraflar", "Is tanimi",
                "Odeme kosullari", "Teslimat",
                "Fikri mulkiyet", "Fesih",
            ],
            "kiralama": [
                "Taraflar", "Konu",
                "Kira bedeli", "Sure",
                "Depozito", "Bakim",
            ],
        }
        sections = sections_map.get(
            ctype,
            ["Taraflar", "Kosullar", "Sure"],
        )
        return {
            "type": ctype,
            "sections": sections,
            "disclaimer": (
                "Bu bir sablon olup "
                "hukuki danismanlik degildir"
            ),
        }


class TermsOfServiceSkill(BaseSkill):
    """Kullanim kosullari becerisi."""

    SKILL_ID = "192"
    NAME = "terms_of_service"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Kullanim kosullari taslagi"
    PARAMETERS = {
        "company": "Sirket",
        "service_type": "Hizmet tipi",
        "jurisdiction": "Yetki alani",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        return {
            "company": p.get("company", ""),
            "sections": [
                "Kabul", "Hesap kosullari",
                "Kullanim kurallari",
                "Fikri mulkiyet",
                "Sorumluluk siniri",
                "Fesih", "Degisiklikler",
                "Iletisim",
            ],
        }


class PrivacyPolicySkill(BaseSkill):
    """Gizlilik politikasi becerisi."""

    SKILL_ID = "193"
    NAME = "privacy_policy"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Gizlilik politikasi taslagi "
        "(GDPR/KVKK uyumlu)"
    )
    PARAMETERS = {
        "company": "Sirket",
        "data_collected": "Toplanan veriler",
        "jurisdiction": "Yetki alani",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        jurisdiction = p.get(
            "jurisdiction", "TR",
        )
        framework = (
            "KVKK" if jurisdiction == "TR"
            else "GDPR"
        )
        return {
            "company": p.get("company", ""),
            "framework": framework,
            "sections": [
                "Toplanan veriler",
                "Kullanim amaci",
                "Veri saklama",
                "Ucuncu taraflar",
                "Guvenlik",
                "Haklariniz",
                "Cerezler",
                "Iletisim",
            ],
        }


class FaqGeneratorSkill(BaseSkill):
    """SSS olusturma becerisi."""

    SKILL_ID = "194"
    NAME = "faq_generator"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Sik sorulan sorular olusturma"
    PARAMETERS = {
        "product_or_service": "Urun/hizmet",
        "target_audience": "Hedef kitle",
        "count": "Soru sayisi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        product = p.get(
            "product_or_service", "",
        )
        count = int(p.get("count", 10))
        templates = [
            f"{product} nedir?",
            f"{product} nasil kullanilir?",
            f"{product} fiyati nedir?",
            "Iade politikasi nedir?",
            "Destek nasil alinir?",
            "Ucretsiz deneme var mi?",
            "Hangi odeme yontemleri kabul?",
            "Guvenlik nasil saglanir?",
            "Mobil uygulama var mi?",
            "Entegrasyonlar nelerdir?",
        ]
        return {
            "product": product,
            "faqs": templates[:count],
            "count": min(count, len(templates)),
        }


class ChatbotScriptSkill(BaseSkill):
    """Chatbot akisi becerisi."""

    SKILL_ID = "195"
    NAME = "chatbot_script"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Chatbot konusma akisi tasarlama"
    )
    PARAMETERS = {
        "purpose": "Amac",
        "scenarios": "Senaryolar",
        "tone": "Ton",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        purpose = p.get("purpose", "destek")
        return {
            "purpose": purpose,
            "flows": [
                "Karsilama",
                "Niyet tespiti",
                "Bilgi toplama",
                "Cozum sunma",
                "Onay/Eskalasyon",
                "Kapanis",
            ],
        }


class SurveyCreatorSkill(BaseSkill):
    """Anket olusturma becerisi."""

    SKILL_ID = "196"
    NAME = "survey_creator"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Anket sorulari olusturma"
    PARAMETERS = {
        "topic": "Konu",
        "question_count": "Soru sayisi",
        "types": "Soru tipleri",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        topic = p.get("topic", "")
        count = int(
            p.get("question_count", 10),
        )
        return {
            "topic": topic,
            "question_count": count,
            "question_types": [
                "multiple_choice",
                "open_ended",
                "scale",
                "yes_no",
            ],
            "estimated_time": f"{count * 30} sn",
        }


class NewsletterWriterSkill(BaseSkill):
    """Bulten yazma becerisi."""

    SKILL_ID = "197"
    NAME = "newsletter_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Email bulten icerigi yazma"
    PARAMETERS = {
        "topics": "Konular",
        "audience": "Hedef kitle",
        "tone": "Ton",
        "cta": "Aksiyon cagrisi",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        topics = p.get("topics", [])
        return {
            "sections": [
                "Baslik", "Giris",
                *[f"Konu: {t}" for t in topics],
                "CTA", "Footer",
            ],
            "topic_count": len(topics),
        }


class CaseStudyWriterSkill(BaseSkill):
    """Vaka calismasi becerisi."""

    SKILL_ID = "198"
    NAME = "case_study_writer"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Vaka calismasi yazma"
    PARAMETERS = {
        "client": "Musteri",
        "challenge": "Zorluk",
        "solution": "Cozum",
        "results": "Sonuclar",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        return {
            "client": p.get("client", ""),
            "structure": [
                "Musteri tanitimi",
                "Zorluk/Problem",
                "Cozum yaklasimi",
                "Uygulama",
                "Sonuclar ve metrikler",
                "Musteri yorumu",
            ],
        }


class WhitePaperOutlineSkill(BaseSkill):
    """White paper taslagi becerisi."""

    SKILL_ID = "199"
    NAME = "white_paper_outline"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = (
        "Teknik dokuman / white paper taslagi"
    )
    PARAMETERS = {
        "topic": "Konu",
        "audience": "Hedef kitle",
        "depth": "Derinlik",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        topic = p.get("topic", "")
        return {
            "topic": topic,
            "sections": [
                "Yonetici Ozeti",
                "Problem Tanimi",
                "Mevcut Durum",
                "Onerilen Cozum",
                "Teknik Detaylar",
                "Vaka Calismalari",
                "Sonuc",
                "Kaynaklar",
            ],
            "target_pages": "8-15",
        }


class GrantProposalHelperSkill(BaseSkill):
    """Hibe basvuru yardimcisi becerisi."""

    SKILL_ID = "200"
    NAME = "grant_proposal_helper"
    CATEGORY = "communication"
    RISK_LEVEL = "low"
    DESCRIPTION = "Hibe basvurusu yardimcisi"
    PARAMETERS = {
        "project": "Proje",
        "funder": "Fon saglayici",
        "budget": "Butce",
        "impact": "Etki",
    }

    def _execute_impl(
        self, **p: Any,
    ) -> dict[str, Any]:
        """Beceriyi yurutur."""
        return {
            "project": p.get("project", ""),
            "funder": p.get("funder", ""),
            "sections": [
                "Proje ozeti",
                "Problem tanimi",
                "Amac ve hedefler",
                "Yontem",
                "Zaman cizelgesi",
                "Butce",
                "Beklenen etki",
                "Surdurulebilirlik",
            ],
        }


ALL_COMMUNICATION_SKILLS: list[
    type[BaseSkill]
] = [
    EmailWriterSkill,
    EmailReplySuggesterSkill,
    CoverLetterWriterSkill,
    ResumeBulletWriterSkill,
    LinkedinProfileOptimizerSkill,
    BlogPostWriterSkill,
    ArticleOutlineSkill,
    PressReleaseWriterSkill,
    ProductDescriptionSkill,
    SloganGeneratorSkill,
    SpeechWriterSkill,
    ToastWriterSkill,
    ApologyLetterSkill,
    ThankYouNoteSkill,
    ComplaintLetterSkill,
    ContractTemplateSkill,
    TermsOfServiceSkill,
    PrivacyPolicySkill,
    FaqGeneratorSkill,
    ChatbotScriptSkill,
    SurveyCreatorSkill,
    NewsletterWriterSkill,
    CaseStudyWriterSkill,
    WhitePaperOutlineSkill,
    GrantProposalHelperSkill,
]
