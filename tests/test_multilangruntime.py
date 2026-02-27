"""Multi-Language Skill Runtime sistemi testleri.

PythonSkillRunner, NodeJSSkillRunner, GoSkillRunner,
WASMSkillRunner, SkillSDK, SkillMarketplace,
SkillTestHarness, MultiLangRuntimeOrchestrator
testleri.
"""

import pytest

from app.core.multilangruntime import (
    GoSkillRunner,
    MultiLangRuntimeOrchestrator,
    NodeJSSkillRunner,
    PythonSkillRunner,
    SkillMarketplace,
    SkillSDK,
    SkillTestHarness,
    WASMSkillRunner,
)
from app.models.multilangruntime_models import (
    MarketplaceCategory,
    MarketplaceEntry,
    SDKConfig,
    SDKFeature,
    SecurityLevel,
    SecurityScanResult,
    SkillExecution,
    SkillLanguage,
    SkillPackage,
    SkillStatus,
    SkillTestReport,
    TestResult,
)


# =============================================
# Model Testleri
# =============================================


class TestMultiLangRuntimeModels:
    """Model testleri."""

    def test_skill_language_enum(self):
        """SkillLanguage enum degerleri."""
        assert SkillLanguage.PYTHON == "python"
        assert SkillLanguage.NODEJS == "nodejs"
        assert SkillLanguage.GO == "go"
        assert SkillLanguage.WASM == "wasm"
        assert SkillLanguage.RUST == "rust"
        assert SkillLanguage.RUBY == "ruby"

    def test_skill_status_enum(self):
        """SkillStatus enum degerleri."""
        assert SkillStatus.PENDING == "pending"
        assert SkillStatus.BUILDING == "building"
        assert SkillStatus.READY == "ready"
        assert SkillStatus.RUNNING == "running"
        assert SkillStatus.FAILED == "failed"
        assert SkillStatus.STOPPED == "stopped"

    def test_test_result_enum(self):
        """TestResult enum degerleri."""
        assert TestResult.PASSED == "passed"
        assert TestResult.FAILED == "failed"
        assert TestResult.SKIPPED == "skipped"
        assert TestResult.ERROR == "error"

    def test_sdk_feature_enum(self):
        """SDKFeature enum degerleri."""
        assert SDKFeature.HTTP_CLIENT == "http_client"
        assert SDKFeature.DB_ACCESS == "db_access"
        assert SDKFeature.FILE_IO == "file_io"
        assert SDKFeature.MESSAGING == "messaging"
        assert SDKFeature.CACHING == "caching"
        assert SDKFeature.LOGGING == "logging"

    def test_marketplace_category_enum(self):
        """MarketplaceCategory enum degerleri."""
        assert (
            MarketplaceCategory.AUTOMATION
            == "automation"
        )
        assert (
            MarketplaceCategory.ANALYTICS
            == "analytics"
        )
        assert (
            MarketplaceCategory.SECURITY
            == "security"
        )

    def test_security_level_enum(self):
        """SecurityLevel enum degerleri."""
        assert SecurityLevel.LOW == "low"
        assert SecurityLevel.MEDIUM == "medium"
        assert SecurityLevel.HIGH == "high"
        assert SecurityLevel.CRITICAL == "critical"

    def test_skill_package_model(self):
        """SkillPackage modeli."""
        pkg = SkillPackage(
            name="test_skill",
            language=SkillLanguage.PYTHON,
            version="1.0.0",
            entry_point="main",
        )
        assert pkg.id
        assert len(pkg.id) == 8
        assert pkg.name == "test_skill"
        assert pkg.language == SkillLanguage.PYTHON
        assert pkg.version == "1.0.0"
        assert pkg.status == SkillStatus.PENDING
        assert isinstance(pkg.dependencies, list)
        assert pkg.created_at > 0

    def test_skill_execution_model(self):
        """SkillExecution modeli."""
        ex = SkillExecution(
            skill_id="abc123",
            language=SkillLanguage.GO,
            exit_code=0,
            stdout="ok",
        )
        assert ex.id
        assert ex.skill_id == "abc123"
        assert ex.exit_code == 0
        assert ex.stdout == "ok"

    def test_skill_test_report_model(self):
        """SkillTestReport modeli."""
        r = SkillTestReport(
            skill_id="xyz",
            total_tests=10,
            passed=8,
            failed=2,
        )
        assert r.id
        assert r.total_tests == 10
        assert r.passed == 8
        assert r.failed == 2
        assert isinstance(r.results, list)

    def test_sdk_config_model(self):
        """SDKConfig modeli."""
        cfg = SDKConfig(
            language=SkillLanguage.NODEJS,
            sandbox_enabled=True,
            max_memory_mb=512,
        )
        assert cfg.id
        assert cfg.language == SkillLanguage.NODEJS
        assert cfg.sandbox_enabled is True
        assert cfg.max_memory_mb == 512

    def test_marketplace_entry_model(self):
        """MarketplaceEntry modeli."""
        e = MarketplaceEntry(
            skill_id="s1",
            name="test",
            author="dev",
            category=MarketplaceCategory.ANALYTICS,
        )
        assert e.id
        assert e.skill_id == "s1"
        assert (
            e.category
            == MarketplaceCategory.ANALYTICS
        )
        assert e.verified is False
        assert e.downloads == 0

    def test_security_scan_result_model(self):
        """SecurityScanResult modeli."""
        s = SecurityScanResult(
            skill_id="s2",
            language=SkillLanguage.PYTHON,
            risk_level=SecurityLevel.HIGH,
            passed=False,
        )
        assert s.id
        assert s.risk_level == SecurityLevel.HIGH
        assert s.passed is False
        assert isinstance(s.issues, list)


# =============================================
# PythonSkillRunner Testleri
# =============================================


class TestPythonSkillRunner:
    """PythonSkillRunner testleri."""

    def setup_method(self):
        """Her test icin runner olustur."""
        self.runner = PythonSkillRunner()

    def test_init(self):
        """Baslatma testi."""
        assert self.runner is not None
        stats = self.runner.get_stats()
        assert stats["language"] == "python"
        assert stats["total_skills"] == 0

    def test_register_skill(self):
        """Beceri kayit testi."""
        pkg = self.runner.register_skill(
            name="hello",
            code='def main(): return "hello"',
            dependencies=["requests"],
            entry_point="main",
        )
        assert pkg.name == "hello"
        assert pkg.language == SkillLanguage.PYTHON
        assert pkg.status == SkillStatus.READY
        assert "requests" in pkg.dependencies
        assert pkg.checksum

    def test_register_no_deps(self):
        """Bagimliliksiz kayit testi."""
        pkg = self.runner.register_skill(
            name="simple",
            code='print("hi")',
        )
        assert pkg.status == SkillStatus.READY
        assert pkg.dependencies == []

    def test_run_skill(self):
        """Beceri calistirma testi."""
        pkg = self.runner.register_skill(
            name="runner_test",
            code='def main(): pass',
        )
        result = self.runner.run_skill(pkg.id)
        assert result.exit_code == 0
        assert result.stdout
        assert result.cpu_time_ms >= 0

    def test_run_missing_skill(self):
        """Olmayan beceri calistirma testi."""
        result = self.runner.run_skill("missing")
        assert result.exit_code == 1
        assert "not found" in result.stderr

    def test_run_failed_skill(self):
        """Basarisiz beceri calistirma testi."""
        pkg = self.runner.register_skill(
            name="fail_test",
            code="code",
        )
        pkg.status = SkillStatus.FAILED
        result = self.runner.run_skill(pkg.id)
        assert result.exit_code == 1

    def test_get_skill(self):
        """Beceri sorgulama testi."""
        pkg = self.runner.register_skill(
            name="get_test",
            code="pass",
        )
        found = self.runner.get_skill(pkg.id)
        assert found is not None
        assert found.name == "get_test"

    def test_get_skill_missing(self):
        """Olmayan beceri sorgulama testi."""
        assert self.runner.get_skill("nope") is None

    def test_list_skills(self):
        """Beceri listeleme testi."""
        self.runner.register_skill("a", "code_a")
        self.runner.register_skill("b", "code_b")
        skills = self.runner.list_skills()
        assert len(skills) == 2

    def test_list_skills_filter(self):
        """Durum filtreli listeleme testi."""
        self.runner.register_skill("c", "code_c")
        ready = self.runner.list_skills(
            status=SkillStatus.READY
        )
        assert len(ready) == 1
        stopped = self.runner.list_skills(
            status=SkillStatus.STOPPED
        )
        assert len(stopped) == 0

    def test_stop_skill(self):
        """Beceri durdurma testi."""
        pkg = self.runner.register_skill(
            name="stop_test",
            code="pass",
        )
        assert self.runner.stop_skill(pkg.id)
        assert (
            pkg.status == SkillStatus.STOPPED
        )

    def test_stop_missing(self):
        """Olmayan beceri durdurma testi."""
        assert not self.runner.stop_skill("nope")

    def test_unregister_skill(self):
        """Beceri silme testi."""
        pkg = self.runner.register_skill(
            name="del_test",
            code="pass",
        )
        assert self.runner.unregister_skill(pkg.id)
        assert self.runner.get_skill(pkg.id) is None

    def test_unregister_missing(self):
        """Olmayan beceri silme testi."""
        assert not self.runner.unregister_skill(
            "nope"
        )

    def test_stats(self):
        """Istatistik testi."""
        self.runner.register_skill("s", "code")
        stats = self.runner.get_stats()
        assert stats["total_skills"] == 1
        assert stats["total_runs"] == 0


# =============================================
# NodeJSSkillRunner Testleri
# =============================================


class TestNodeJSSkillRunner:
    """NodeJSSkillRunner testleri."""

    def setup_method(self):
        """Her test icin runner olustur."""
        self.runner = NodeJSSkillRunner()

    def test_init(self):
        """Baslatma testi."""
        stats = self.runner.get_stats()
        assert stats["language"] == "nodejs"
        assert stats["node_version"] == "20"

    def test_register_skill(self):
        """Beceri kayit testi."""
        pkg = self.runner.register_skill(
            name="hello_node",
            code='console.log("hi")',
            dependencies=["express", "lodash"],
        )
        assert pkg.language == SkillLanguage.NODEJS
        assert pkg.status == SkillStatus.READY
        assert len(pkg.dependencies) == 2

    def test_run_skill(self):
        """Beceri calistirma testi."""
        pkg = self.runner.register_skill(
            name="node_run",
            code='module.exports = {}',
        )
        result = self.runner.run_skill(pkg.id)
        assert result.exit_code == 0
        assert result.language == SkillLanguage.NODEJS
        assert "Node.js" in result.stdout

    def test_run_missing(self):
        """Olmayan beceri calistirma testi."""
        result = self.runner.run_skill("nope")
        assert result.exit_code == 1

    def test_stop_and_unregister(self):
        """Durdurma ve silme testi."""
        pkg = self.runner.register_skill(
            "n1", "code"
        )
        assert self.runner.stop_skill(pkg.id)
        assert self.runner.unregister_skill(pkg.id)
        assert self.runner.get_skill(pkg.id) is None

    def test_list_skills(self):
        """Beceri listeleme testi."""
        self.runner.register_skill("a", "c1")
        self.runner.register_skill("b", "c2")
        assert len(self.runner.list_skills()) == 2

    def test_stats_after_run(self):
        """Calistirma sonrasi istatistik."""
        pkg = self.runner.register_skill(
            "stat_test", "code"
        )
        self.runner.run_skill(pkg.id)
        stats = self.runner.get_stats()
        assert stats["total_runs"] == 1
        assert stats["total_successes"] == 1
        assert stats["success_rate"] == 100.0


# =============================================
# GoSkillRunner Testleri
# =============================================


class TestGoSkillRunner:
    """GoSkillRunner testleri."""

    def setup_method(self):
        """Her test icin runner olustur."""
        self.runner = GoSkillRunner()

    def test_init(self):
        """Baslatma testi."""
        stats = self.runner.get_stats()
        assert stats["language"] == "go"
        assert stats["go_version"] == "1.22"

    def test_register_skill(self):
        """Beceri kayit testi."""
        pkg = self.runner.register_skill(
            name="hello_go",
            code='package main\nfunc main() {}',
            dependencies=["github.com/pkg/errors"],
        )
        assert pkg.language == SkillLanguage.GO
        assert pkg.status == SkillStatus.PENDING

    def test_compile_skill(self):
        """Derleme testi."""
        pkg = self.runner.register_skill(
            name="compile_test",
            code='package main\nfunc main() {}',
        )
        assert self.runner.compile_skill(pkg.id)
        assert pkg.status == SkillStatus.READY
        stats = self.runner.get_stats()
        assert stats["compiled_skills"] == 1

    def test_compile_missing(self):
        """Olmayan beceri derleme testi."""
        assert not self.runner.compile_skill("nope")

    def test_run_auto_compiles(self):
        """Otomatik derleme ile calistirma."""
        pkg = self.runner.register_skill(
            name="auto_compile",
            code='package main\nfunc main() {}',
        )
        result = self.runner.run_skill(pkg.id)
        assert result.exit_code == 0
        assert pkg.id in self.runner._compiled

    def test_run_missing(self):
        """Olmayan beceri calistirma."""
        result = self.runner.run_skill("nope")
        assert result.exit_code == 1

    def test_stop_and_unregister(self):
        """Durdurma ve silme testi."""
        pkg = self.runner.register_skill(
            "g1", "code"
        )
        self.runner.compile_skill(pkg.id)
        assert self.runner.stop_skill(pkg.id)
        assert self.runner.unregister_skill(pkg.id)
        assert pkg.id not in self.runner._compiled

    def test_list_skills(self):
        """Beceri listeleme testi."""
        self.runner.register_skill("a", "ca")
        self.runner.register_skill("b", "cb")
        assert len(self.runner.list_skills()) == 2

    def test_stats(self):
        """Istatistik testi."""
        pkg = self.runner.register_skill(
            "gs", "code"
        )
        self.runner.compile_skill(pkg.id)
        self.runner.run_skill(pkg.id)
        stats = self.runner.get_stats()
        assert stats["total_compiles"] >= 1
        assert stats["total_runs"] >= 1


# =============================================
# WASMSkillRunner Testleri
# =============================================


class TestWASMSkillRunner:
    """WASMSkillRunner testleri."""

    def setup_method(self):
        """Her test icin runner olustur."""
        self.runner = WASMSkillRunner()

    def test_init(self):
        """Baslatma testi."""
        stats = self.runner.get_stats()
        assert stats["language"] == "wasm"
        assert stats["sandbox_enabled"] is True

    def test_register_skill(self):
        """Beceri kayit testi."""
        pkg = self.runner.register_skill(
            name="hello_wasm",
            code="(module (func (export \"_start\")))",
        )
        assert pkg.language == SkillLanguage.WASM
        assert pkg.status == SkillStatus.PENDING

    def test_load_module(self):
        """Modul yukleme testi."""
        pkg = self.runner.register_skill(
            name="load_test",
            code="(module (func $main (export \"_start\") nop))",
        )
        assert self.runner.load_module(pkg.id)
        assert pkg.status == SkillStatus.READY
        stats = self.runner.get_stats()
        assert stats["loaded_modules"] == 1

    def test_load_missing(self):
        """Olmayan modul yukleme testi."""
        assert not self.runner.load_module("nope")

    def test_run_auto_loads(self):
        """Otomatik yukleme ile calistirma."""
        pkg = self.runner.register_skill(
            name="auto_load",
            code="(module (memory 1))",
        )
        result = self.runner.run_skill(pkg.id)
        assert result.exit_code == 0
        assert (
            pkg.id in self.runner._loaded_modules
        )

    def test_run_missing(self):
        """Olmayan beceri calistirma."""
        result = self.runner.run_skill("nope")
        assert result.exit_code == 1

    def test_sandbox_output(self):
        """Sandbox cikti kontrolu."""
        pkg = self.runner.register_skill(
            name="sandbox_test",
            code="(module (memory 1))",
        )
        result = self.runner.run_skill(pkg.id)
        assert "sandboxed" in result.stdout

    def test_stop_and_unregister(self):
        """Durdurma ve silme testi."""
        pkg = self.runner.register_skill(
            "w1", "(module)"
        )
        self.runner.load_module(pkg.id)
        assert self.runner.stop_skill(pkg.id)
        assert self.runner.unregister_skill(pkg.id)
        assert (
            pkg.id
            not in self.runner._loaded_modules
        )

    def test_list_skills(self):
        """Beceri listeleme."""
        self.runner.register_skill(
            "a", "(module 1)"
        )
        self.runner.register_skill(
            "b", "(module 2)"
        )
        assert len(self.runner.list_skills()) == 2

    def test_stats(self):
        """Istatistik testi."""
        pkg = self.runner.register_skill(
            "ws", "(module)"
        )
        self.runner.load_module(pkg.id)
        self.runner.run_skill(pkg.id)
        stats = self.runner.get_stats()
        assert stats["total_loads"] >= 1
        assert stats["total_runs"] >= 1


# =============================================
# SkillSDK Testleri
# =============================================


class TestSkillSDK:
    """SkillSDK testleri."""

    def setup_method(self):
        """Her test icin SDK olustur."""
        self.sdk = SkillSDK()

    def test_init(self):
        """Baslatma testi."""
        stats = self.sdk.get_stats()
        assert stats["total_configs"] == 0

    def test_create_config(self):
        """Config olusturma testi."""
        cfg = self.sdk.create_config(
            language=SkillLanguage.PYTHON,
            features=[SDKFeature.HTTP_CLIENT.value],
            sandbox=True,
            max_memory_mb=128,
        )
        assert cfg.language == SkillLanguage.PYTHON
        assert cfg.sandbox_enabled is True
        assert cfg.max_memory_mb == 128

    def test_get_config(self):
        """Config sorgulama testi."""
        self.sdk.create_config(
            language=SkillLanguage.GO,
        )
        found = self.sdk.get_config(
            SkillLanguage.GO
        )
        assert found is not None
        assert found.language == SkillLanguage.GO

    def test_get_config_missing(self):
        """Olmayan config sorgulama."""
        assert self.sdk.get_config(
            SkillLanguage.RUBY
        ) is None

    def test_list_configs(self):
        """Config listeleme testi."""
        self.sdk.create_config(
            language=SkillLanguage.PYTHON
        )
        self.sdk.create_config(
            language=SkillLanguage.NODEJS
        )
        configs = self.sdk.list_configs()
        assert len(configs) == 2

    def test_generate_boilerplate_python(self):
        """Python boilerplate uretimi."""
        result = self.sdk.generate_boilerplate(
            SkillLanguage.PYTHON, "my_skill"
        )
        assert result["language"] == "python"
        assert result["skill_name"] == "my_skill"
        assert "main.py" in result["files"]
        code = result["files"]["main.py"]
        assert "my_skill" in code

    def test_generate_boilerplate_nodejs(self):
        """Node.js boilerplate uretimi."""
        result = self.sdk.generate_boilerplate(
            SkillLanguage.NODEJS, "api_skill"
        )
        assert result["language"] == "nodejs"
        assert "index.js" in result["files"]

    def test_generate_boilerplate_go(self):
        """Go boilerplate uretimi."""
        result = self.sdk.generate_boilerplate(
            SkillLanguage.GO, "fast_skill"
        )
        assert result["language"] == "go"
        assert "main.go" in result["files"]

    def test_generate_boilerplate_wasm(self):
        """WASM boilerplate uretimi."""
        result = self.sdk.generate_boilerplate(
            SkillLanguage.WASM, "wasm_skill"
        )
        assert "module.wasm" in result["files"]

    def test_generate_boilerplate_rust(self):
        """Rust boilerplate uretimi."""
        result = self.sdk.generate_boilerplate(
            SkillLanguage.RUST, "rust_skill"
        )
        assert "src/main.rs" in result["files"]

    def test_generate_boilerplate_ruby(self):
        """Ruby boilerplate uretimi."""
        result = self.sdk.generate_boilerplate(
            SkillLanguage.RUBY, "ruby_skill"
        )
        assert "main.rb" in result["files"]

    def test_validate_structure_valid(self):
        """Gecerli yapi dogrulama."""
        result = self.sdk.validate_skill_structure(
            SkillLanguage.PYTHON,
            ["main.py", "requirements.txt"],
        )
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_structure_invalid(self):
        """Gecersiz yapi dogrulama."""
        result = self.sdk.validate_skill_structure(
            SkillLanguage.PYTHON,
            ["utils.py"],
        )
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_structure_nodejs(self):
        """Node.js yapi dogrulama."""
        result = self.sdk.validate_skill_structure(
            SkillLanguage.NODEJS,
            ["index.js", "package.json"],
        )
        assert result["valid"] is True

    def test_supported_languages(self):
        """Desteklenen diller testi."""
        langs = self.sdk.get_supported_languages()
        assert "python" in langs
        assert "nodejs" in langs
        assert "go" in langs
        assert "wasm" in langs
        assert "rust" in langs
        assert "ruby" in langs
        assert len(langs) == 6

    def test_stats(self):
        """Istatistik testi."""
        self.sdk.generate_boilerplate(
            SkillLanguage.PYTHON, "test"
        )
        self.sdk.validate_skill_structure(
            SkillLanguage.PYTHON, ["main.py"]
        )
        stats = self.sdk.get_stats()
        assert stats["total_generations"] == 1
        assert stats["total_validations"] == 1


# =============================================
# SkillMarketplace Testleri
# =============================================


class TestSkillMarketplace:
    """SkillMarketplace testleri."""

    def setup_method(self):
        """Her test icin marketplace olustur."""
        self.mp = SkillMarketplace()

    def test_init(self):
        """Baslatma testi."""
        stats = self.mp.get_stats()
        assert stats["total_entries"] == 0

    def test_publish(self):
        """Yayinlama testi."""
        entry = self.mp.publish(
            skill_id="s1",
            name="Test Skill",
            description="Aciklama",
            author="dev",
            category=MarketplaceCategory.ANALYTICS,
        )
        assert entry.name == "Test Skill"
        assert entry.skill_id == "s1"
        assert (
            entry.category
            == MarketplaceCategory.ANALYTICS
        )
        assert entry.verified is False

    def test_search_by_query(self):
        """Sorgu ile arama testi."""
        self.mp.publish(
            "s1", "Data Analyzer", "Veri analizi"
        )
        self.mp.publish(
            "s2", "Code Formatter", "Kod formati"
        )
        results = self.mp.search("Data")
        assert len(results) == 1
        assert results[0].name == "Data Analyzer"

    def test_search_by_category(self):
        """Kategori ile arama testi."""
        self.mp.publish(
            "s1",
            "Sec Tool",
            category=MarketplaceCategory.SECURITY,
        )
        self.mp.publish(
            "s2",
            "Auto Tool",
            category=MarketplaceCategory.AUTOMATION,
        )
        results = self.mp.search(
            category=MarketplaceCategory.SECURITY
        )
        assert len(results) == 1

    def test_search_by_min_rating(self):
        """Minimum puan ile arama."""
        e1 = self.mp.publish("s1", "Low")
        e2 = self.mp.publish("s2", "High")
        self.mp.rate(e2.id, 5.0)
        results = self.mp.search(min_rating=3.0)
        assert len(results) == 1

    def test_search_empty(self):
        """Bos arama testi."""
        results = self.mp.search("nonexistent")
        assert len(results) == 0

    def test_get_entry(self):
        """Kayit sorgulama testi."""
        entry = self.mp.publish("s1", "Test")
        found = self.mp.get_entry(entry.id)
        assert found is not None
        assert found.name == "Test"

    def test_get_entry_missing(self):
        """Olmayan kayit sorgulama."""
        assert self.mp.get_entry("nope") is None

    def test_download(self):
        """Indirme testi."""
        entry = self.mp.publish("s1", "DL Test")
        result = self.mp.download(entry.id)
        assert result["success"] is True
        assert result["downloads"] == 1
        # Tekrar indir
        result2 = self.mp.download(entry.id)
        assert result2["downloads"] == 2

    def test_download_missing(self):
        """Olmayan kayit indirme."""
        result = self.mp.download("nope")
        assert result["success"] is False

    def test_rate(self):
        """Derecelendirme testi."""
        entry = self.mp.publish("s1", "Rate Test")
        assert self.mp.rate(entry.id, 4.0, "Iyi")
        found = self.mp.get_entry(entry.id)
        assert found.rating == 4.0
        assert found.rating_count == 1

    def test_rate_multiple(self):
        """Coklu derecelendirme testi."""
        entry = self.mp.publish("s1", "Multi Rate")
        self.mp.rate(entry.id, 4.0)
        self.mp.rate(entry.id, 2.0)
        found = self.mp.get_entry(entry.id)
        assert found.rating == 3.0
        assert found.rating_count == 2

    def test_rate_missing(self):
        """Olmayan kayit derecelendirme."""
        assert not self.mp.rate("nope", 5.0)

    def test_verify(self):
        """Dogrulama testi."""
        entry = self.mp.publish("s1", "Verify")
        assert self.mp.verify(entry.id)
        found = self.mp.get_entry(entry.id)
        assert found.verified is True

    def test_verify_missing(self):
        """Olmayan kayit dogrulama."""
        assert not self.mp.verify("nope")

    def test_list_entries(self):
        """Listeleme testi."""
        self.mp.publish(
            "s1",
            "A",
            category=MarketplaceCategory.SECURITY,
        )
        self.mp.publish(
            "s2",
            "B",
            category=MarketplaceCategory.UTILITY,
        )
        all_entries = self.mp.list_entries()
        assert len(all_entries) == 2

        sec = self.mp.list_entries(
            category=MarketplaceCategory.SECURITY
        )
        assert len(sec) == 1

    def test_list_verified_only(self):
        """Yalnizca dogrulananlar listesi."""
        e1 = self.mp.publish("s1", "V1")
        self.mp.publish("s2", "V2")
        self.mp.verify(e1.id)

        verified = self.mp.list_entries(
            verified_only=True
        )
        assert len(verified) == 1

    def test_get_popular(self):
        """Populer becerileri getirme."""
        e1 = self.mp.publish("s1", "Pop1")
        e2 = self.mp.publish("s2", "Pop2")
        # Pop2'ye daha fazla indirme
        self.mp.download(e2.id)
        self.mp.download(e2.id)
        self.mp.download(e1.id)

        popular = self.mp.get_popular(limit=2)
        assert len(popular) == 2
        assert popular[0].name == "Pop2"

    def test_stats(self):
        """Istatistik testi."""
        e = self.mp.publish("s1", "Stat")
        self.mp.download(e.id)
        self.mp.rate(e.id, 4.0)
        self.mp.verify(e.id)
        stats = self.mp.get_stats()
        assert stats["total_entries"] == 1
        assert stats["total_downloads"] == 1
        assert stats["total_ratings"] == 1
        assert stats["verified_entries"] == 1


# =============================================
# SkillTestHarness Testleri
# =============================================


class TestSkillTestHarness:
    """SkillTestHarness testleri."""

    def setup_method(self):
        """Her test icin harness olustur."""
        self.harness = SkillTestHarness()

    def test_init(self):
        """Baslatma testi."""
        stats = self.harness.get_stats()
        assert stats["total_test_runs"] == 0

    def test_run_tests_python(self):
        """Python test calistirma."""
        code = """
def test_add():
    assert 1 + 1 == 2

def test_sub():
    assert 2 - 1 == 1
"""
        report = self.harness.run_tests(
            "s1", SkillLanguage.PYTHON, code
        )
        assert report.skill_id == "s1"
        assert report.total_tests == 2
        assert report.passed == 2
        assert report.failed == 0

    def test_run_tests_nodejs(self):
        """Node.js test calistirma."""
        code = """
it("should add", () => { expect(1+1).toBe(2) });
it("should sub", () => { expect(2-1).toBe(1) });
"""
        report = self.harness.run_tests(
            "s2", SkillLanguage.NODEJS, code
        )
        assert report.total_tests == 2
        assert report.passed == 2

    def test_run_tests_with_failures(self):
        """Basarisiz test calistirma."""
        code = """
def test_ok():
    pass

def test_fail_case():
    assert False
"""
        report = self.harness.run_tests(
            "s3", SkillLanguage.PYTHON, code
        )
        assert report.total_tests == 2
        assert report.passed == 1
        assert report.failed == 1

    def test_run_tests_with_skip(self):
        """Atlanan test calistirma."""
        code = """
def test_ok():
    pass

def test_skip_reason():
    pass
"""
        report = self.harness.run_tests(
            "s4", SkillLanguage.PYTHON, code
        )
        assert report.skipped == 1

    def test_security_scan_clean(self):
        """Temiz kod guvenlik taramasi."""
        code = """
def process(data):
    return data.upper()
"""
        result = self.harness.run_security_scan(
            "s1", SkillLanguage.PYTHON, code
        )
        assert result.passed is True
        assert result.risk_level == SecurityLevel.LOW
        assert len(result.issues) == 0

    def test_security_scan_eval(self):
        """eval() iceren kod taramasi."""
        code = """
result = eval(user_input)
"""
        result = self.harness.run_security_scan(
            "s2", SkillLanguage.PYTHON, code
        )
        assert result.passed is False
        assert (
            result.risk_level
            == SecurityLevel.CRITICAL
        )
        assert len(result.issues) > 0

    def test_security_scan_subprocess(self):
        """subprocess iceren kod taramasi."""
        code = """
import subprocess
subprocess.run(["ls"])
"""
        result = self.harness.run_security_scan(
            "s3", SkillLanguage.PYTHON, code
        )
        assert result.risk_level in (
            SecurityLevel.HIGH,
            SecurityLevel.CRITICAL,
        )

    def test_security_scan_os_system(self):
        """os.system iceren kod taramasi."""
        code = """
import os
os.system("rm -rf /")
"""
        result = self.harness.run_security_scan(
            "s4", SkillLanguage.PYTHON, code
        )
        assert result.passed is False

    def test_security_scan_nodejs(self):
        """Node.js guvenlik taramasi."""
        code = """
const result = eval(input);
const cp = require("child_process");
"""
        result = self.harness.run_security_scan(
            "s5", SkillLanguage.NODEJS, code
        )
        assert len(result.issues) >= 2

    def test_security_scan_go(self):
        """Go guvenlik taramasi."""
        code = """
import "unsafe"
unsafe.Pointer(nil)
"""
        result = self.harness.run_security_scan(
            "s6", SkillLanguage.GO, code
        )
        assert len(result.issues) > 0

    def test_performance_test(self):
        """Performans testi."""
        result = self.harness.run_performance_test(
            "s1", iterations=50
        )
        assert result["skill_id"] == "s1"
        assert result["iterations"] == 50
        assert result["total_ms"] > 0
        assert result["avg_ms"] >= 0
        assert result["throughput_per_sec"] > 0

    def test_get_report(self):
        """Rapor sorgulama testi."""
        report = self.harness.run_tests(
            "s1",
            SkillLanguage.PYTHON,
            "def test_a(): pass",
        )
        found = self.harness.get_report(report.id)
        assert found is not None
        assert found.skill_id == "s1"

    def test_get_report_missing(self):
        """Olmayan rapor sorgulama."""
        assert (
            self.harness.get_report("nope") is None
        )

    def test_list_reports(self):
        """Raporlari listeleme."""
        self.harness.run_tests(
            "s1",
            SkillLanguage.PYTHON,
            "def test_a(): pass",
        )
        self.harness.run_tests(
            "s1",
            SkillLanguage.PYTHON,
            "def test_b(): pass",
        )
        reports = self.harness.list_reports("s1")
        assert len(reports) == 2

    def test_stats(self):
        """Istatistik testi."""
        self.harness.run_tests(
            "s1",
            SkillLanguage.PYTHON,
            "def test_x(): pass",
        )
        self.harness.run_security_scan(
            "s1", SkillLanguage.PYTHON, "pass"
        )
        self.harness.run_performance_test("s1", 10)
        stats = self.harness.get_stats()
        assert stats["total_test_runs"] == 1
        assert stats["total_scans"] == 1
        assert stats["total_perf_tests"] == 1


# =============================================
# MultiLangRuntimeOrchestrator Testleri
# =============================================


class TestMultiLangRuntimeOrchestrator:
    """MultiLangRuntimeOrchestrator testleri."""

    def setup_method(self):
        """Her test icin orkestrator olustur."""
        self.orch = MultiLangRuntimeOrchestrator()

    def test_init(self):
        """Baslatma testi."""
        stats = self.orch.get_stats()
        assert stats["total_skills"] == 0
        assert stats["total_deploys"] == 0

    def test_deploy_python(self):
        """Python beceri dagitimi."""
        result = self.orch.deploy_skill(
            name="py_skill",
            language=SkillLanguage.PYTHON,
            code='def main(): return "ok"',
            dependencies=["requests"],
            author="dev",
        )
        assert result["success"] is True
        assert result["skill_id"]
        assert (
            result["steps"]["register"]["success"]
        )
        assert (
            result["steps"]["security_scan"][
                "success"
            ]
        )
        assert (
            result["steps"]["publish"]["success"]
        )

    def test_deploy_nodejs(self):
        """Node.js beceri dagitimi."""
        result = self.orch.deploy_skill(
            name="node_skill",
            language=SkillLanguage.NODEJS,
            code='module.exports = { run: () => "ok" }',
            author="dev",
        )
        assert result["success"] is True

    def test_deploy_go(self):
        """Go beceri dagitimi."""
        result = self.orch.deploy_skill(
            name="go_skill",
            language=SkillLanguage.GO,
            code='package main\nfunc main() {}',
            author="dev",
        )
        assert result["success"] is True

    def test_deploy_wasm(self):
        """WASM beceri dagitimi."""
        result = self.orch.deploy_skill(
            name="wasm_skill",
            language=SkillLanguage.WASM,
            code="(module (memory 1))",
            author="dev",
        )
        assert result["success"] is True

    def test_deploy_with_tests(self):
        """Testli dagitim."""
        result = self.orch.deploy_skill(
            name="tested_skill",
            language=SkillLanguage.PYTHON,
            code='def main(): return True',
            test_code="def test_main(): assert True",
        )
        assert result["success"] is True
        assert "test" in result["steps"]
        assert (
            result["steps"]["test"]["total"] == 1
        )

    def test_deploy_unsupported_language(self):
        """Desteklenmeyen dil dagitimi."""
        result = self.orch.deploy_skill(
            name="ruby_skill",
            language=SkillLanguage.RUBY,
            code="puts 'hi'",
        )
        assert result["success"] is False
        assert "error" in result

    def test_deploy_with_dangerous_code(self):
        """Tehlikeli kod dagitimi."""
        result = self.orch.deploy_skill(
            name="danger",
            language=SkillLanguage.PYTHON,
            code='eval("dangerous")',
        )
        # Dagitilir ama guvenlik uyarisi verir
        assert result["success"] is True
        scan = result["steps"]["security_scan"]
        assert scan["issues"] > 0

    def test_execute_python(self):
        """Python beceri calistirma."""
        deploy = self.orch.deploy_skill(
            name="exec_py",
            language=SkillLanguage.PYTHON,
            code='def main(): pass',
        )
        result = self.orch.execute_skill(
            deploy["skill_id"],
            SkillLanguage.PYTHON,
        )
        assert result.exit_code == 0

    def test_execute_nodejs(self):
        """Node.js beceri calistirma."""
        deploy = self.orch.deploy_skill(
            name="exec_node",
            language=SkillLanguage.NODEJS,
            code='exports.run = () => {}',
        )
        result = self.orch.execute_skill(
            deploy["skill_id"],
            SkillLanguage.NODEJS,
        )
        assert result.exit_code == 0

    def test_execute_go(self):
        """Go beceri calistirma."""
        deploy = self.orch.deploy_skill(
            name="exec_go",
            language=SkillLanguage.GO,
            code='package main\nfunc main() {}',
        )
        result = self.orch.execute_skill(
            deploy["skill_id"],
            SkillLanguage.GO,
        )
        assert result.exit_code == 0

    def test_execute_unsupported(self):
        """Desteklenmeyen dil calistirma."""
        result = self.orch.execute_skill(
            "fake_id",
            SkillLanguage.RUBY,
        )
        assert result.exit_code == 1

    def test_runtime_status(self):
        """Runtime durum sorgulama."""
        status = self.orch.get_runtime_status()
        assert "python" in status
        assert "nodejs" in status
        assert "go" in status
        assert "wasm" in status
        assert "sdk" in status
        assert "marketplace" in status

    def test_stats_combined(self):
        """Birlestirillmis istatistikler."""
        self.orch.deploy_skill(
            "s1", SkillLanguage.PYTHON, "code"
        )
        self.orch.deploy_skill(
            "s2", SkillLanguage.NODEJS, "code"
        )
        stats = self.orch.get_stats()
        assert stats["total_deploys"] == 2
        assert stats["total_skills"] >= 2
        assert "runners" in stats
        assert "sdk" in stats
        assert "marketplace" in stats
        assert "test_harness" in stats

    def test_full_pipeline(self):
        """Tam pipeline testi."""
        # 1. Dagit
        deploy = self.orch.deploy_skill(
            name="full_test",
            language=SkillLanguage.PYTHON,
            code='def main(): return {"ok": True}',
            test_code="def test_ok(): pass",
            author="atlas",
            category=MarketplaceCategory.AUTOMATION,
        )
        assert deploy["success"]

        # 2. Calistir
        result = self.orch.execute_skill(
            deploy["skill_id"],
            SkillLanguage.PYTHON,
            args={"key": "value"},
        )
        assert result.exit_code == 0

        # 3. Marketplace kontrol
        mp_stats = (
            self.orch.marketplace.get_stats()
        )
        assert mp_stats["total_entries"] >= 1

        # 4. SDK boilerplate
        bp = self.orch.sdk.generate_boilerplate(
            SkillLanguage.PYTHON, "new_skill"
        )
        assert bp["files"]

        # 5. Genel istatistik
        stats = self.orch.get_stats()
        assert stats["total_deploys"] >= 1
        assert stats["total_executions"] >= 1
