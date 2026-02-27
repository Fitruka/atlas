"""Industry Agent Template Engine testleri.

IndustryTemplateDef, TemplateRegistry,
TemplateValidator, SkillBundler,
WorkflowGenerator, CRMBuilder,
ComplianceLoader, IndustryTemplateEngine,
IndustryTemplateOrchestrator testleri.
"""

import pytest

from app.models.industrytemplate_models import (
    IndustryType,
    TemplateStatus,
    SkillStatus,
    WorkflowStepType,
    CRMFieldType,
    ComplianceLevel,
    DeploymentStatus,
    TemplateSkillDef,
    WorkflowStepDef,
    WorkflowDef,
    CRMFieldDef,
    CRMSegmentDef,
    ComplianceRuleDef,
    IndustryTemplateDef,
    TemplateDeployment,
    TemplateCustomization,
    SkillBundleEntry,
)
from app.core.industrytemplate import (
    IndustryTemplateEngine,
    TemplateRegistry,
    TemplateValidator,
    SkillBundler,
    WorkflowGenerator,
    CRMBuilder,
    ComplianceLoader,
    IndustryTemplateOrchestrator,
)
from app.core.industrytemplate.templates import (
    ECOMMERCE_TEMPLATE,
    MEDICAL_TOURISM_TEMPLATE,
    REAL_ESTATE_TEMPLATE,
    DIGITAL_AGENCY_TEMPLATE,
)


# ============================================================
# Enum Testleri
# ============================================================


class TestEnums:
    """Enum testleri."""

    def test_industry_type_values(self):
        """Sektor tipi degerleri."""
        assert IndustryType.ECOMMERCE == "ecommerce"
        assert IndustryType.MEDICAL_TOURISM == "medical_tourism"
        assert IndustryType.REAL_ESTATE == "real_estate"
        assert IndustryType.DIGITAL_AGENCY == "digital_agency"
        assert IndustryType.CUSTOM == "custom"

    def test_template_status_values(self):
        """Sablon durumu degerleri."""
        assert TemplateStatus.DRAFT == "draft"
        assert TemplateStatus.ACTIVE == "active"
        assert TemplateStatus.DEPRECATED == "deprecated"

    def test_skill_status_values(self):
        """Beceri durumu degerleri."""
        assert SkillStatus.PENDING == "pending"
        assert SkillStatus.CONFIGURED == "configured"
        assert SkillStatus.ACTIVE == "active"
        assert SkillStatus.ERROR == "error"

    def test_workflow_step_type_values(self):
        """Is akisi adim tipi degerleri."""
        assert WorkflowStepType.ACTION == "action"
        assert WorkflowStepType.CONDITION == "condition"
        assert WorkflowStepType.NOTIFICATION == "notification"
        assert WorkflowStepType.APPROVAL == "approval"

    def test_crm_field_type_values(self):
        """CRM alan tipi degerleri."""
        assert CRMFieldType.TEXT == "text"
        assert CRMFieldType.NUMBER == "number"
        assert CRMFieldType.CURRENCY == "currency"
        assert CRMFieldType.RATING == "rating"

    def test_compliance_level_values(self):
        """Uyumluluk seviyesi degerleri."""
        assert ComplianceLevel.REQUIRED == "required"
        assert ComplianceLevel.RECOMMENDED == "recommended"
        assert ComplianceLevel.OPTIONAL == "optional"

    def test_deployment_status_values(self):
        """Dagitim durumu degerleri."""
        assert DeploymentStatus.PENDING == "pending"
        assert DeploymentStatus.ACTIVE == "active"
        assert DeploymentStatus.FAILED == "failed"


# ============================================================
# Model Testleri
# ============================================================


class TestModels:
    """Model testleri."""

    def test_template_skill_def_creation(self):
        """TemplateSkillDef olusturma."""
        s = TemplateSkillDef(name="TestSkill", description="Test beceri")
        assert s.name == "TestSkill"
        assert s.skill_id
        assert s.status == SkillStatus.PENDING
        assert s.required is True

    def test_template_skill_def_defaults(self):
        """TemplateSkillDef varsayilanlar."""
        s = TemplateSkillDef()
        assert s.name == ""
        assert s.config == {}
        assert s.dependencies == []
        assert s.enabled is True

    def test_workflow_step_def_creation(self):
        """WorkflowStepDef olusturma."""
        step = WorkflowStepDef(name="step1", step_type="action")
        assert step.name == "step1"
        assert step.step_id
        assert step.next_steps == []

    def test_workflow_def_creation(self):
        """WorkflowDef olusturma."""
        wf = WorkflowDef(name="test_flow", trigger="event")
        assert wf.name == "test_flow"
        assert wf.trigger == "event"
        assert wf.steps == []
        assert wf.enabled is True

    def test_crm_field_def_creation(self):
        """CRMFieldDef olusturma."""
        f = CRMFieldDef(name="email", field_type="email")
        assert f.name == "email"
        assert f.searchable is True
        assert f.sortable is True

    def test_crm_segment_def_creation(self):
        """CRMSegmentDef olusturma."""
        s = CRMSegmentDef(name="VIP", criteria={"ltv_gt": 5000})
        assert s.name == "VIP"
        assert s.criteria["ltv_gt"] == 5000

    def test_compliance_rule_def_creation(self):
        """ComplianceRuleDef olusturma."""
        r = ComplianceRuleDef(name="kvkk", level="required", jurisdictions=["TR"])
        assert r.name == "kvkk"
        assert r.jurisdictions == ["TR"]

    def test_industry_template_def_creation(self):
        """IndustryTemplateDef olusturma."""
        t = IndustryTemplateDef(
            name="Test Template",
            industry=IndustryType.ECOMMERCE,
        )
        assert t.name == "Test Template"
        assert t.industry == IndustryType.ECOMMERCE
        assert t.version == "1.0.0"
        assert t.status == TemplateStatus.DRAFT
        assert t.supported_languages == ["tr", "en"]

    def test_industry_template_def_defaults(self):
        """IndustryTemplateDef varsayilanlar."""
        t = IndustryTemplateDef()
        assert t.skills == []
        assert t.workflows == []
        assert t.crm_fields == []
        assert t.compliance_rules == []
        assert t.created_at > 0

    def test_template_deployment_creation(self):
        """TemplateDeployment olusturma."""
        d = TemplateDeployment(
            template_id="test",
            status=DeploymentStatus.ACTIVE,
        )
        assert d.template_id == "test"
        assert d.status == DeploymentStatus.ACTIVE
        assert d.active_skills == []

    def test_template_customization_creation(self):
        """TemplateCustomization olusturma."""
        c = TemplateCustomization(template_id="test")
        assert c.template_id == "test"
        assert c.skill_overrides == {}

    def test_skill_bundle_entry_creation(self):
        """SkillBundleEntry olusturma."""
        b = SkillBundleEntry(template_id="test", total_skills=5)
        assert b.template_id == "test"
        assert b.total_skills == 5
        assert b.active_count == 0


# ============================================================
# Template Tanim Testleri
# ============================================================


class TestTemplateDefinitions:
    """Sablon tanim testleri."""

    def test_ecommerce_template_structure(self):
        """E-ticaret sablonu yapisi."""
        t = ECOMMERCE_TEMPLATE
        assert t["name"] == "E-Commerce Agent"
        assert t["industry"] == "ecommerce"
        assert len(t["skills"]) == 10
        assert len(t["workflows"]) == 4
        assert len(t["crm_fields"]) >= 8
        assert "tr" in t["supported_languages"]

    def test_ecommerce_skills(self):
        """E-ticaret becerileri."""
        skills = ECOMMERCE_TEMPLATE["skills"]
        names = [s["name"] for s in skills]
        assert "OrderTracker" in names
        assert "CustomerSupportBot" in names
        assert "InventoryMonitor" in names
        assert "PriceOptimizer" in names
        assert "ReturnProcessor" in names

    def test_ecommerce_workflows(self):
        """E-ticaret is akislari."""
        workflows = ECOMMERCE_TEMPLATE["workflows"]
        names = [w["name"] for w in workflows]
        assert "new_order_flow" in names
        assert "return_flow" in names
        assert "restock_flow" in names

    def test_medical_tourism_template_structure(self):
        """Medikal turizm sablonu yapisi."""
        t = MEDICAL_TOURISM_TEMPLATE
        assert t["name"] == "Medical Tourism Agent"
        assert t["industry"] == "medical_tourism"
        assert len(t["skills"]) == 10
        assert len(t["supported_languages"]) >= 6

    def test_medical_tourism_skills(self):
        """Medikal turizm becerileri."""
        skills = MEDICAL_TOURISM_TEMPLATE["skills"]
        names = [s["name"] for s in skills]
        assert "PatientIntakeBot" in names
        assert "TreatmentQuoteGen" in names
        assert "TranslationBridge" in names
        assert "PostOpFollowUp" in names

    def test_medical_tourism_multilingual(self):
        """Medikal turizm cok dil destegi."""
        langs = MEDICAL_TOURISM_TEMPLATE["supported_languages"]
        assert "de" in langs
        assert "en" in langs
        assert "tr" in langs

    def test_real_estate_template_structure(self):
        """Gayrimenkul sablonu yapisi."""
        t = REAL_ESTATE_TEMPLATE
        assert t["name"] == "Real Estate Agent"
        assert t["industry"] == "real_estate"
        assert len(t["skills"]) == 10

    def test_real_estate_skills(self):
        """Gayrimenkul becerileri."""
        skills = REAL_ESTATE_TEMPLATE["skills"]
        names = [s["name"] for s in skills]
        assert "LeadCaptureBot" in names
        assert "PropertyMatcher" in names
        assert "ViewingScheduler" in names
        assert "PriceAnalyzer" in names

    def test_digital_agency_template_structure(self):
        """Dijital ajans sablonu yapisi."""
        t = DIGITAL_AGENCY_TEMPLATE
        assert t["name"] == "Digital Agency Agent"
        assert t["industry"] == "digital_agency"
        assert len(t["skills"]) == 10

    def test_digital_agency_skills(self):
        """Dijital ajans becerileri."""
        skills = DIGITAL_AGENCY_TEMPLATE["skills"]
        names = [s["name"] for s in skills]
        assert "ClientOnboarder" in names
        assert "CampaignManager" in names
        assert "ReportGenerator" in names
        assert "BudgetTracker" in names

    def test_all_templates_have_compliance(self):
        """Tum sablonlarda uyumluluk kurallari var."""
        for template in [ECOMMERCE_TEMPLATE, MEDICAL_TOURISM_TEMPLATE, REAL_ESTATE_TEMPLATE, DIGITAL_AGENCY_TEMPLATE]:
            assert len(template["compliance_rules"]) > 0

    def test_all_templates_have_crm_segments(self):
        """Tum sablonlarda CRM segmentleri var."""
        for template in [ECOMMERCE_TEMPLATE, MEDICAL_TOURISM_TEMPLATE, REAL_ESTATE_TEMPLATE, DIGITAL_AGENCY_TEMPLATE]:
            assert len(template["crm_segments"]) > 0

    def test_all_templates_have_default_config(self):
        """Tum sablonlarda varsayilan yapilandirma var."""
        for template in [ECOMMERCE_TEMPLATE, MEDICAL_TOURISM_TEMPLATE, REAL_ESTATE_TEMPLATE, DIGITAL_AGENCY_TEMPLATE]:
            assert "timezone" in template["default_config"]
            assert "currency" in template["default_config"]


# ============================================================
# TemplateRegistry Testleri
# ============================================================


class TestTemplateRegistry:
    """TemplateRegistry testleri."""

    def test_init(self):
        """Baslama testi."""
        r = TemplateRegistry()
        assert r is not None
        assert r.list_all() == []

    def test_register(self):
        """Sablon kayit."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="Test", industry=IndustryType.ECOMMERCE)
        result = r.register(t)
        assert result is True
        assert len(r.list_all()) == 1

    def test_register_duplicate(self):
        """Ayni sablon tekrar kayit."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="Test", industry=IndustryType.ECOMMERCE)
        r.register(t)
        # Ayni ID ile tekrar kayit uzerine yazmali
        result = r.register(t)
        assert result is True

    def test_unregister(self):
        """Sablon kaldirma."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="Test", industry=IndustryType.ECOMMERCE)
        r.register(t)
        result = r.unregister(t.template_id)
        assert result is True
        assert len(r.list_all()) == 0

    def test_unregister_unknown(self):
        """Bilinmeyen sablon kaldirma."""
        r = TemplateRegistry()
        result = r.unregister("unknown")
        assert result is False

    def test_get(self):
        """Sablon getirme."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="Test", industry=IndustryType.ECOMMERCE)
        r.register(t)
        found = r.get(t.template_id)
        assert found is not None
        assert found.name == "Test"

    def test_get_unknown(self):
        """Bilinmeyen sablon getirme."""
        r = TemplateRegistry()
        assert r.get("unknown") is None

    def test_get_by_name(self):
        """Isme gore sablon getirme."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="MyTemplate")
        r.register(t)
        found = r.get_by_name("MyTemplate")
        assert found is not None
        assert found.name == "MyTemplate"

    def test_get_by_industry(self):
        """Sektore gore sablon getirme."""
        r = TemplateRegistry()
        t1 = IndustryTemplateDef(name="T1", industry=IndustryType.ECOMMERCE)
        t2 = IndustryTemplateDef(name="T2", industry=IndustryType.ECOMMERCE)
        t3 = IndustryTemplateDef(name="T3", industry=IndustryType.REAL_ESTATE)
        r.register(t1)
        r.register(t2)
        r.register(t3)
        ecom = r.get_by_industry("ecommerce")
        assert len(ecom) == 2

    def test_search_by_query(self):
        """Metin aramasi."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="E-Commerce Agent", description="Online magaza")
        r.register(t)
        results = r.search(query="commerce")
        assert len(results) == 1

    def test_search_by_tags(self):
        """Etiket aramasi."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="Test", tags=["ecommerce", "retail"])
        r.register(t)
        results = r.search(tags=["retail"])
        assert len(results) == 1

    def test_search_no_match(self):
        """Eslesme olmayan arama."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="Test")
        r.register(t)
        results = r.search(query="xyz")
        assert len(results) == 0

    def test_list_industries(self):
        """Sektor listeleme."""
        r = TemplateRegistry()
        t1 = IndustryTemplateDef(name="T1", industry=IndustryType.ECOMMERCE)
        t2 = IndustryTemplateDef(name="T2", industry=IndustryType.REAL_ESTATE)
        r.register(t1)
        r.register(t2)
        industries = r.list_industries()
        assert "ecommerce" in industries
        assert "real_estate" in industries

    def test_stats(self):
        """Istatistikler."""
        r = TemplateRegistry()
        t = IndustryTemplateDef(name="Test")
        r.register(t)
        stats = r.get_stats()
        assert stats["total_templates"] == 1
        assert stats["total_registered"] == 1


# ============================================================
# TemplateValidator Testleri
# ============================================================


class TestTemplateValidator:
    """TemplateValidator testleri."""

    def test_init(self):
        """Baslama testi."""
        v = TemplateValidator()
        assert v is not None

    def test_validate_valid_template(self):
        """Gecerli sablon dogrulama."""
        v = TemplateValidator()
        t = IndustryTemplateDef(
            name="Test Template",
            description="Aciklama",
            skills=[TemplateSkillDef(name="Skill1", description="Test", category="test")],
        )
        result = v.validate(t)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_empty_name(self):
        """Bos isimli sablon."""
        v = TemplateValidator()
        t = IndustryTemplateDef(
            skills=[TemplateSkillDef(name="Skill1")],
        )
        result = v.validate(t)
        assert result["valid"] is False

    def test_validate_no_skills(self):
        """Becerisiz sablon."""
        v = TemplateValidator()
        t = IndustryTemplateDef(name="Test")
        result = v.validate(t)
        assert result["valid"] is False

    def test_check_skills_valid(self):
        """Gecerli beceri listesi."""
        v = TemplateValidator()
        skills = [
            {"name": "Skill1", "description": "Test", "category": "cat1"},
            {"name": "Skill2", "description": "Test", "category": "cat2"},
        ]
        result = v.check_skills(skills)
        assert len(result["errors"]) == 0

    def test_check_skills_duplicate_name(self):
        """Tekrarlanan beceri adi."""
        v = TemplateValidator()
        skills = [
            {"name": "Skill1", "description": "A"},
            {"name": "Skill1", "description": "B"},
        ]
        result = v.check_skills(skills)
        assert len(result["errors"]) > 0

    def test_check_skills_empty_name(self):
        """Bos beceri adi."""
        v = TemplateValidator()
        skills = [{"name": "", "description": "Test"}]
        result = v.check_skills(skills)
        assert len(result["errors"]) > 0

    def test_check_workflows_valid(self):
        """Gecerli is akisi."""
        v = TemplateValidator()
        workflows = [
            {"name": "flow1", "steps": [{"step_type": "action", "name": "s1"}]},
        ]
        result = v.check_workflows(workflows)
        assert len(result["errors"]) == 0

    def test_check_workflows_invalid_step_type(self):
        """Gecersiz adim tipi."""
        v = TemplateValidator()
        workflows = [
            {"name": "flow1", "steps": [{"step_type": "invalid_type", "name": "s1"}]},
        ]
        result = v.check_workflows(workflows)
        assert len(result["errors"]) > 0

    def test_check_crm_fields_valid(self):
        """Gecerli CRM alanlari."""
        v = TemplateValidator()
        fields = [
            {"name": "email", "field_type": "email"},
            {"name": "score", "field_type": "number"},
        ]
        result = v.check_crm_fields(fields)
        assert len(result["errors"]) == 0

    def test_check_crm_fields_invalid_type(self):
        """Gecersiz CRM alan tipi."""
        v = TemplateValidator()
        fields = [{"name": "field1", "field_type": "invalid_type"}]
        result = v.check_crm_fields(fields)
        assert len(result["errors"]) > 0

    def test_check_compliance_valid(self):
        """Gecerli uyumluluk kurallari."""
        v = TemplateValidator()
        rules = [
            {"name": "kvkk", "jurisdictions": ["TR"]},
        ]
        result = v.check_compliance(rules)
        assert len(result["errors"]) == 0

    def test_validator_stats(self):
        """Dogrulayici istatistikleri."""
        v = TemplateValidator()
        t = IndustryTemplateDef(
            name="Test",
            skills=[TemplateSkillDef(name="S1")],
        )
        v.validate(t)
        stats = v.get_stats()
        assert stats["validations_run"] == 1


# ============================================================
# SkillBundler Testleri
# ============================================================


class TestSkillBundler:
    """SkillBundler testleri."""

    def test_init(self):
        """Baslama testi."""
        b = SkillBundler()
        assert b is not None

    def test_bundle(self):
        """Paket olusturma."""
        b = SkillBundler()
        skills = [
            {"name": "Skill1", "description": "Test1", "category": "cat1", "dependencies": []},
            {"name": "Skill2", "description": "Test2", "category": "cat2", "dependencies": ["Skill1"]},
        ]
        bundle = b.bundle("template1", skills)
        assert bundle is not None
        assert bundle.total_skills == 2

    def test_bundle_dependency_order(self):
        """Bagimlilk sirasi."""
        b = SkillBundler()
        skills = [
            {"name": "B", "description": "B", "dependencies": ["A"]},
            {"name": "A", "description": "A", "dependencies": []},
        ]
        bundle = b.bundle("t1", skills)
        assert bundle is not None
        names = [s.name for s in bundle.skills]
        assert names.index("A") < names.index("B")

    def test_configure_skill(self):
        """Beceri yapilandirma."""
        b = SkillBundler()
        skills = [{"name": "S1", "description": "Test", "dependencies": []}]
        bundle = b.bundle("t1", skills)
        result = b.configure_skill(bundle.bundle_id, "S1", {"key": "value"})
        assert result is True

    def test_configure_skill_unknown(self):
        """Bilinmeyen beceri yapilandirma."""
        b = SkillBundler()
        result = b.configure_skill("unknown", "S1", {})
        assert result is False

    def test_activate_bundle(self):
        """Paket aktif etme."""
        b = SkillBundler()
        skills = [{"name": "S1", "description": "Test", "dependencies": []}]
        bundle = b.bundle("t1", skills)
        result = b.activate_bundle(bundle.bundle_id)
        assert result is True
        updated = b.get_bundle(bundle.bundle_id)
        assert updated.active_count > 0

    def test_get_bundle(self):
        """Paket getirme."""
        b = SkillBundler()
        skills = [{"name": "S1", "description": "Test", "dependencies": []}]
        bundle = b.bundle("t1", skills)
        found = b.get_bundle(bundle.bundle_id)
        assert found is not None

    def test_get_bundle_unknown(self):
        """Bilinmeyen paket getirme."""
        b = SkillBundler()
        assert b.get_bundle("unknown") is None

    def test_stats(self):
        """Istatistikler."""
        b = SkillBundler()
        skills = [{"name": "S1", "description": "Test", "dependencies": []}]
        b.bundle("t1", skills)
        stats = b.get_stats()
        assert stats["total_bundles"] == 1
        assert stats["total_bundled"] == 1


# ============================================================
# WorkflowGenerator Testleri
# ============================================================


class TestWorkflowGenerator:
    """WorkflowGenerator testleri."""

    def test_init(self):
        """Baslama testi."""
        g = WorkflowGenerator()
        assert g is not None

    def test_generate(self):
        """Is akisi uretimi."""
        g = WorkflowGenerator()
        wf_defs = [
            {
                "name": "test_flow",
                "description": "Test is akisi",
                "trigger": "event",
                "steps": [
                    {"name": "step1", "step_type": "action"},
                    {"name": "step2", "step_type": "notification"},
                ],
            },
        ]
        results = g.generate("t1", wf_defs)
        assert len(results) == 1
        assert results[0].name == "test_flow"
        assert len(results[0].steps) == 2

    def test_create_flow(self):
        """Tek is akisi olusturma."""
        g = WorkflowGenerator()
        flow = g.create_flow({
            "name": "my_flow",
            "trigger": "start",
            "steps": [{"name": "s1", "step_type": "action"}],
        })
        assert flow is not None
        assert flow.name == "my_flow"

    def test_create_flow_empty_name(self):
        """Bos isimli is akisi."""
        g = WorkflowGenerator()
        flow = g.create_flow({"name": ""})
        assert flow is None

    def test_step_linking(self):
        """Adim baglama."""
        g = WorkflowGenerator()
        flow = g.create_flow({
            "name": "flow1",
            "steps": [
                {"name": "s1", "step_type": "action"},
                {"name": "s2", "step_type": "action"},
                {"name": "s3", "step_type": "action"},
            ],
        })
        assert flow is not None
        assert len(flow.steps[0].next_steps) == 1
        assert len(flow.steps[-1].next_steps) == 0

    def test_list_workflows(self):
        """Is akisi listeleme."""
        g = WorkflowGenerator()
        g.generate("t1", [{"name": "f1", "steps": []}, {"name": "f2", "steps": []}])
        assert len(g.list_workflows()) == 2

    def test_stats(self):
        """Istatistikler."""
        g = WorkflowGenerator()
        g.generate("t1", [{"name": "f1", "steps": []}])
        stats = g.get_stats()
        assert stats["total_generated"] == 1


# ============================================================
# CRMBuilder Testleri
# ============================================================


class TestCRMBuilder:
    """CRMBuilder testleri."""

    def test_init(self):
        """Baslama testi."""
        c = CRMBuilder()
        assert c is not None

    def test_build(self):
        """CRM yapisi olusturma."""
        c = CRMBuilder()
        fields = [
            {"name": "email", "label": "Email", "field_type": "email"},
            {"name": "score", "label": "Puan", "field_type": "number"},
        ]
        segments = [
            {"name": "VIP", "description": "VIP musteriler", "criteria": {"ltv_gt": 5000}},
        ]
        schema = c.build("t1", fields, segments)
        assert schema["total_fields"] == 2
        assert schema["total_segments"] == 1

    def test_add_field(self):
        """CRM alani ekleme."""
        c = CRMBuilder()
        c.build("t1", [{"name": "email", "label": "Email", "field_type": "email"}])
        result = c.add_field("t1", {"name": "phone", "label": "Telefon", "field_type": "phone"})
        assert result is True
        schema = c.get_schema("t1")
        assert schema["total_fields"] == 2

    def test_add_field_unknown_template(self):
        """Bilinmeyen sablona alan ekleme."""
        c = CRMBuilder()
        result = c.add_field("unknown", {"name": "field1"})
        assert result is False

    def test_get_schema(self):
        """CRM semasi getirme."""
        c = CRMBuilder()
        c.build("t1", [{"name": "f1", "label": "F1", "field_type": "text"}])
        schema = c.get_schema("t1")
        assert schema is not None

    def test_export_schema(self):
        """CRM semasi disa aktarma."""
        c = CRMBuilder()
        c.build("t1", [{"name": "f1", "label": "F1", "field_type": "text"}])
        exported = c.export_schema("t1")
        assert exported is not None

    def test_export_schema_list(self):
        """CRM semasi liste olarak disa aktarma."""
        c = CRMBuilder()
        c.build("t1", [{"name": "f1", "label": "F1", "field_type": "text"}])
        exported = c.export_schema("t1", fmt="list")
        assert isinstance(exported, list)

    def test_stats(self):
        """Istatistikler."""
        c = CRMBuilder()
        c.build("t1", [{"name": "f1", "label": "F1", "field_type": "text"}])
        stats = c.get_stats()
        assert stats["total_schemas"] == 1


# ============================================================
# ComplianceLoader Testleri
# ============================================================


class TestComplianceLoader:
    """ComplianceLoader testleri."""

    def test_init(self):
        """Baslama testi."""
        cl = ComplianceLoader()
        assert cl is not None

    def test_load(self):
        """Kural yukleme."""
        cl = ComplianceLoader()
        rules = [
            {"name": "kvkk", "description": "KVKK", "level": "required", "jurisdictions": ["TR"]},
            {"name": "gdpr", "description": "GDPR", "level": "required", "jurisdictions": ["EU"]},
        ]
        loaded = cl.load("ecommerce", rules)
        assert len(loaded) == 2

    def test_check_compliance(self):
        """Uyumluluk kontrolu."""
        cl = ComplianceLoader()
        rules = [
            {"name": "rule1", "description": "R1", "level": "required", "check_function": "has_consent"},
        ]
        cl.load("ecommerce", rules)
        result = cl.check_compliance("ecommerce", {"has_consent": True})
        assert result["compliant"] is True

    def test_check_compliance_fail(self):
        """Basarisiz uyumluluk kontrolu."""
        cl = ComplianceLoader()
        rules = [
            {"name": "rule1", "description": "R1", "level": "required", "check_function": "has_consent"},
        ]
        cl.load("ecommerce", rules)
        result = cl.check_compliance("ecommerce", {"has_consent": False})
        assert result["compliant"] is False

    def test_get_rules(self):
        """Kural getirme."""
        cl = ComplianceLoader()
        cl.load("ecommerce", [{"name": "r1", "description": "R1"}])
        rules = cl.get_rules("ecommerce")
        assert len(rules) == 1

    def test_get_rules_unknown_industry(self):
        """Bilinmeyen sektor kurallari."""
        cl = ComplianceLoader()
        rules = cl.get_rules("unknown")
        assert len(rules) == 0

    def test_stats(self):
        """Istatistikler."""
        cl = ComplianceLoader()
        cl.load("ecommerce", [{"name": "r1"}])
        stats = cl.get_stats()
        assert stats["total_rules"] == 1
        assert "ecommerce" in stats["industries"]


# ============================================================
# IndustryTemplateEngine Testleri
# ============================================================


class TestIndustryTemplateEngine:
    """IndustryTemplateEngine testleri."""

    def test_init(self):
        """Baslama testi."""
        e = IndustryTemplateEngine()
        assert e is not None

    def test_create_agent_ecommerce(self):
        """E-ticaret agent olusturma."""
        e = IndustryTemplateEngine()
        deployment = e.create_agent("ecommerce")
        assert deployment is not None
        assert deployment.template_id == "ecommerce"
        assert deployment.status == DeploymentStatus.ACTIVE
        assert len(deployment.active_skills) > 0

    def test_create_agent_medical_tourism(self):
        """Medikal turizm agent olusturma."""
        e = IndustryTemplateEngine()
        deployment = e.create_agent("medical_tourism")
        assert deployment is not None
        assert deployment.template_id == "medical_tourism"

    def test_create_agent_real_estate(self):
        """Gayrimenkul agent olusturma."""
        e = IndustryTemplateEngine()
        deployment = e.create_agent("real_estate")
        assert deployment is not None

    def test_create_agent_digital_agency(self):
        """Dijital ajans agent olusturma."""
        e = IndustryTemplateEngine()
        deployment = e.create_agent("digital_agency")
        assert deployment is not None

    def test_create_agent_unknown(self):
        """Bilinmeyen sablon ile agent olusturma."""
        e = IndustryTemplateEngine()
        deployment = e.create_agent("unknown")
        assert deployment is None

    def test_create_agent_with_overrides(self):
        """Ozellestirme ile agent olusturma."""
        e = IndustryTemplateEngine()
        deployment = e.create_agent("ecommerce", {"currency": "USD"})
        assert deployment is not None
        assert deployment.config_overrides["currency"] == "USD"

    def test_list_templates(self):
        """Sablon listeleme."""
        e = IndustryTemplateEngine()
        templates = e.list_templates()
        assert len(templates) == 4
        names = [t["key"] for t in templates]
        assert "ecommerce" in names
        assert "medical_tourism" in names
        assert "real_estate" in names
        assert "digital_agency" in names

    def test_get_template_info(self):
        """Sablon detayi."""
        e = IndustryTemplateEngine()
        info = e.get_template_info("ecommerce")
        assert info is not None
        assert info["name"] == "E-Commerce Agent"
        assert "skills" in info

    def test_get_template_info_unknown(self):
        """Bilinmeyen sablon detayi."""
        e = IndustryTemplateEngine()
        info = e.get_template_info("unknown")
        assert info is None

    def test_customize_template(self):
        """Sablon ozellestirme."""
        e = IndustryTemplateEngine()
        custom = e.customize_template("ecommerce", {"skills": {"PriceOptimizer": {"enabled": False}}})
        assert custom is not None

    def test_list_deployments(self):
        """Dagitim listeleme."""
        e = IndustryTemplateEngine()
        e.create_agent("ecommerce")
        e.create_agent("medical_tourism")
        deps = e.list_deployments()
        assert len(deps) == 2

    def test_stats(self):
        """Istatistikler."""
        e = IndustryTemplateEngine()
        e.create_agent("ecommerce")
        stats = e.get_stats()
        assert stats["available_templates"] == 4
        assert stats["total_created"] == 1


# ============================================================
# IndustryTemplateOrchestrator Testleri
# ============================================================


class TestIndustryTemplateOrchestrator:
    """IndustryTemplateOrchestrator testleri."""

    def test_init(self):
        """Baslama testi."""
        o = IndustryTemplateOrchestrator()
        assert o is not None
        assert o.engine is not None
        assert o.registry is not None
        assert o.validator is not None

    def test_deploy_ecommerce(self):
        """E-ticaret sablon dagitimi."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("ecommerce")
        assert result["success"] is True
        assert result["template_name"] == "ecommerce"
        assert result["skills_count"] > 0
        assert result["workflows_count"] > 0
        assert result["crm_fields_count"] > 0

    def test_deploy_medical_tourism(self):
        """Medikal turizm sablon dagitimi."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("medical_tourism")
        assert result["success"] is True

    def test_deploy_real_estate(self):
        """Gayrimenkul sablon dagitimi."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("real_estate")
        assert result["success"] is True

    def test_deploy_digital_agency(self):
        """Dijital ajans sablon dagitimi."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("digital_agency")
        assert result["success"] is True

    def test_deploy_unknown(self):
        """Bilinmeyen sablon dagitimi."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("unknown")
        assert result["success"] is False

    def test_deploy_with_overrides(self):
        """Ozellestirmeli dagitim."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("ecommerce", {"timezone": "UTC"})
        assert result["success"] is True

    def test_list_available(self):
        """Mevcut sablonlari listeleme."""
        o = IndustryTemplateOrchestrator()
        templates = o.list_available_templates()
        assert len(templates) == 4

    def test_deploy_all_templates(self):
        """Tum sablonlari dagit."""
        o = IndustryTemplateOrchestrator()
        for name in ["ecommerce", "medical_tourism", "real_estate", "digital_agency"]:
            result = o.deploy_template(name)
            assert result["success"] is True, f"{name} dagitimi basarisiz"

    def test_stats(self):
        """Istatistikler."""
        o = IndustryTemplateOrchestrator()
        o.deploy_template("ecommerce")
        stats = o.get_stats()
        assert stats["orchestrator"]["pipelines_run"] == 1
        assert stats["orchestrator"]["deployments_success"] == 1

    def test_stats_after_failure(self):
        """Basarisiz dagitim sonrasi istatistikler."""
        o = IndustryTemplateOrchestrator()
        o.deploy_template("unknown")
        stats = o.get_stats()
        assert stats["orchestrator"]["deployments_failed"] == 1

    def test_full_pipeline_ecommerce(self):
        """E-ticaret tam pipeline testi."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("ecommerce")
        assert result["success"] is True
        assert result["deployment_id"]
        assert result["skills_count"] == 10
        assert result["workflows_count"] == 4
        assert result["compliance_rules_count"] > 0
        assert result["elapsed_seconds"] >= 0

    def test_full_pipeline_medical_tourism(self):
        """Medikal turizm tam pipeline testi."""
        o = IndustryTemplateOrchestrator()
        result = o.deploy_template("medical_tourism")
        assert result["success"] is True
        assert result["skills_count"] == 10
        assert result["workflows_count"] == 4
