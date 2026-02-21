"""OpenClaw beceri ekosistemi ithalat scripti.

/tmp/openclaw-skills deposundaki tum becerileri tarar,
guvenlik analizi yapar, guvenlileri ATLAS'a import eder,
awesome listeyi cross-reference yapar ve rapor uretir.
"""

import json
import os
import sys
import time

# Proje kokunu path'e ekle
sys.path.insert(0, os.path.dirname(__file__))

from app.core.openclaw.batch_import import (
    OpenClawBatchImporter,
)
from app.core.openclaw.awesome_list import (
    AwesomeListAnalyzer,
)
from app.core.openclaw.skill_converter import (
    reset_id_counter,
)
from app.core.skills.skill_registry import (
    SkillRegistry,
)


def main() -> None:
    """Ana ithalat pipeline'i calistirir."""
    start = time.time()

    # Yollar (Windows uyumlu)
    import tempfile
    tmp = tempfile.gettempdir()
    skills_dir = os.path.join(
        tmp, "openclaw-skills", "skills",
    )
    awesome_readme = os.path.join(
        tmp, "awesome-skills", "README.md",
    )
    reports_dir = os.path.join(
        os.path.dirname(__file__), "reports",
    )

    print("=" * 60)
    print("  ATLAS - OpenClaw Beceri Ekosistemi Ithalati")
    print("=" * 60)
    print()

    # 1. Registry ve Importer olustur
    reset_id_counter()
    registry = SkillRegistry()
    batch = OpenClawBatchImporter(
        registry=registry,
        min_score=70,
    )

    # 2. Repolari tara ve import et
    print("[1/4] Beceriler taraniyor ve import ediliyor...")
    print(f"      Kaynak: {skills_dir}")

    repos = [
        (skills_dir, "openclaw/skills"),
    ]

    stats = batch.import_all(repos)

    elapsed_import = time.time() - start
    print(f"      Tamamlandi: {elapsed_import:.1f}s")
    print()

    # 3. Awesome list cross-reference
    print("[2/4] Awesome list analiz ediliyor...")
    analyzer = AwesomeListAnalyzer()

    if os.path.exists(awesome_readme):
        analyzer.parse_file(awesome_readme)
        awesome_stats = analyzer.get_stats()
        print(f"      Awesome list: {awesome_stats['total_entries']} girdi, "
              f"{awesome_stats['total_categories']} kategori")

        # Cross-reference
        scan_results = batch.get_scan_results()
        analyzer.cross_reference(scan_results)
        premium = analyzer.get_premium_skills()
        print(f"      Premium (kurate + guvenli): {len(premium)}")
    else:
        print(f"      README bulunamadi: {awesome_readme}")
        premium = []

    print()

    # 4. Rapor olustur
    print("[3/4] Raporlar olusturuluyor...")
    report_path = batch.export_reports(
        output_dir=reports_dir,
    )

    # Awesome list raporunu da ekle
    awesome_report = {
        "awesome_list": {
            "total_entries": analyzer.get_stats().get("total_entries", 0),
            "total_categories": analyzer.get_stats().get("total_categories", 0),
            "total_premium": len(premium),
            "categories": analyzer.list_categories(),
            "premium_skills": [
                {
                    "name": p.name,
                    "url": p.url,
                    "description": p.description,
                    "category": p.category,
                    "security_score": p.security_score,
                }
                for p in premium[:50]  # Top 50
            ],
        },
    }

    awesome_path = os.path.join(
        reports_dir,
        "openclaw_awesome_report.json",
    )
    with open(awesome_path, "w", encoding="utf-8") as f:
        json.dump(awesome_report, f, indent=2, ensure_ascii=False)

    print(f"      Import raporu: {report_path}")
    print(f"      Awesome raporu: {awesome_path}")
    print()

    # 5. Sonuclari goster
    total_time = time.time() - start

    print("[4/4] Sonuclar")
    print("=" * 60)
    print()
    print(f"  Taranan beceri sayisi:    {stats.total_found:>6,}")
    print(f"  Basarili ayristirma:      {stats.parsed_ok:>6,}")
    print(f"  Guvenlik gecen (70+):     {stats.passed_security:>6,}")
    print(f"  Import edilen:            {stats.imported:>6,}")
    print(f"  Duplikat atlanan:         {stats.duplicates:>6,}")
    print(f"  Guvenlik reddeden:        {stats.skipped:>6,}")
    print(f"  Hata:                     {stats.failed:>6,}")
    print(f"  Ort. guvenlik puani:      {stats.avg_security_score:>9.1f}")
    print()

    print("  Risk Dagilimi:")
    for level, count in sorted(stats.by_risk_level.items()):
        bar = "#" * min(count // 20, 40)
        print(f"    {level:<10} {count:>6,}  {bar}")
    print()

    print("  Kategori Dagilimi (import edilen):")
    for cat, count in sorted(
        stats.by_category.items(),
        key=lambda x: -x[1],
    ):
        bar = "#" * min(count // 10, 40)
        print(f"    {cat:<20} {count:>5,}  {bar}")
    print()

    if premium:
        print(f"  Awesome List Premium:     {len(premium):>6,}")

    print(f"  Toplam sure:              {total_time:>8.1f}s")
    print()
    print("=" * 60)
    print("  Import tamamlandi!")
    print("=" * 60)


if __name__ == "__main__":
    main()
