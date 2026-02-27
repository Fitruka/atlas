"""ATLAS Secure Agent Marketplace test suite."""

import pytest

from app.core.agentmarket import (
    AgentMarketOrchestrator,
    DependencyResolver,
    RatingReviewSystem,
    RevenueSharing,
    SecurityAuditPipeline,
    SkillAnalytics,
    VerifiedMarketplace,
)
from app.models.agentmarket_models import (
    AnalyticsPeriod,
    AuditResult,
    DependencyNode,
    DependencyStatus,
    ListingStatus,
    MarketplaceListing,
    RevenueModel,
    RevenueRecord,
    ReviewStatus,
    SecurityAuditReport,
    UsageMetric,
    UserReview,
)


# ------------------------------------------------------------------ #
#  Model enum ve default deger testleri
# ------------------------------------------------------------------ #


class TestModels:
    """Model enum ve varsayilan deger testleri."""

    def test_listing_status_values(self):
        assert ListingStatus.DRAFT == "draft"
        assert ListingStatus.PENDING_REVIEW == "pending_review"
        assert ListingStatus.APPROVED == "approved"
        assert ListingStatus.REJECTED == "rejected"
        assert ListingStatus.PUBLISHED == "published"
        assert ListingStatus.SUSPENDED == "suspended"
        assert ListingStatus.ARCHIVED == "archived"

    def test_audit_result_values(self):
        assert AuditResult.PASS == "pass"
        assert AuditResult.FAIL == "fail"
        assert AuditResult.WARNING == "warning"
        assert AuditResult.CRITICAL == "critical"

    def test_review_status_values(self):
        assert ReviewStatus.PENDING == "pending"
        assert ReviewStatus.APPROVED == "approved"
        assert ReviewStatus.FLAGGED == "flagged"
        assert ReviewStatus.REMOVED == "removed"

    def test_revenue_model_values(self):
        assert RevenueModel.FREE == "free"
        assert RevenueModel.ONE_TIME == "one_time"
        assert RevenueModel.SUBSCRIPTION == "subscription"
        assert RevenueModel.USAGE_BASED == "usage_based"

    def test_dependency_status_values(self):
        assert DependencyStatus.RESOLVED == "resolved"
        assert DependencyStatus.MISSING == "missing"
        assert DependencyStatus.CONFLICT == "conflict"
        assert DependencyStatus.OUTDATED == "outdated"

    def test_analytics_period_values(self):
        assert AnalyticsPeriod.HOURLY == "hourly"
        assert AnalyticsPeriod.DAILY == "daily"
        assert AnalyticsPeriod.WEEKLY == "weekly"
        assert AnalyticsPeriod.MONTHLY == "monthly"

    def test_marketplace_listing_defaults(self):
        listing = MarketplaceListing()
        assert listing.name == ""
        assert listing.description == ""
        assert listing.author_id == ""
        assert listing.version == "1.0.0"
        assert listing.category == ""
        assert listing.tags == []
        assert listing.status == ListingStatus.DRAFT
        assert listing.price == 0.0
        assert listing.revenue_model == RevenueModel.FREE
        assert listing.download_count == 0
        assert listing.avg_rating == 0.0
        assert listing.id  # uuid generated

    def test_security_audit_report_defaults(self):
        report = SecurityAuditReport()
        assert report.listing_id == ""
        assert report.result == AuditResult.PASS
        assert report.issues == []
        assert report.critical_count == 0
        assert report.warning_count == 0
        assert report.auditor_version == "1.0.0"
        assert report.passed is True

    def test_user_review_defaults(self):
        review = UserReview()
        assert review.listing_id == ""
        assert review.user_id == ""
        assert review.rating == 5.0
        assert review.title == ""
        assert review.comment == ""
        assert review.status == ReviewStatus.PENDING
        assert review.helpful_count == 0

    def test_revenue_record_defaults(self):
        record = RevenueRecord()
        assert record.listing_id == ""
        assert record.author_id == ""
        assert record.period == ""
        assert record.gross_amount == 0.0
        assert record.platform_fee_pct == 30.0
        assert record.net_amount == 0.0
        assert record.currency == "USD"
        assert record.transactions_count == 0

    def test_dependency_node_defaults(self):
        node = DependencyNode()
        assert node.listing_id == ""
        assert node.name == ""
        assert node.version == ""
        assert node.required_version == ""
        assert node.status == DependencyStatus.RESOLVED
        assert node.alternatives == []

    def test_usage_metric_defaults(self):
        metric = UsageMetric()
        assert metric.listing_id == ""
        assert metric.period == AnalyticsPeriod.DAILY
        assert metric.installs == 0
        assert metric.uninstalls == 0
        assert metric.active_users == 0
        assert metric.api_calls == 0
        assert metric.error_rate == 0.0
        assert metric.avg_response_ms == 0.0

    def test_model_ids_are_unique(self):
        a = MarketplaceListing()
        b = MarketplaceListing()
        assert a.id != b.id


# ------------------------------------------------------------------ #
#  VerifiedMarketplace testleri
# ------------------------------------------------------------------ #


class TestVerifiedMarketplace:
    """Dogrulanmis agent pazaryeri testleri."""

    def test_submit_listing_basic(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing(
            name="TestAgent",
            description="A test agent",
            author_id="author1",
        )
        assert listing.name == "TestAgent"
        assert listing.description == "A test agent"
        assert listing.author_id == "author1"
        assert listing.status == ListingStatus.PENDING_REVIEW

    def test_submit_listing_with_all_params(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing(
            name="PaidAgent",
            description="Premium agent",
            author_id="author2",
            version="2.0.0",
            category="analytics",
            tags=["data", "ml"],
            price=29.99,
            revenue_model=RevenueModel.ONE_TIME,
        )
        assert listing.version == "2.0.0"
        assert listing.category == "analytics"
        assert listing.tags == ["data", "ml"]
        assert listing.price == 29.99
        assert listing.revenue_model == RevenueModel.ONE_TIME

    def test_submit_listing_increments_stat(self):
        mp = VerifiedMarketplace()
        mp.submit_listing("A", "d", "a1")
        mp.submit_listing("B", "d", "a2")
        stats = mp.get_stats()
        assert stats["submitted"] == 2

    def test_get_listing_found(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("X", "d", "a1")
        result = mp.get_listing(listing.id)
        assert result is not None
        assert result.name == "X"

    def test_get_listing_not_found(self):
        mp = VerifiedMarketplace()
        assert mp.get_listing("nonexistent") is None

    def test_update_listing_name(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("Old", "d", "a1")
        updated = mp.update_listing(listing.id, name="New")
        assert updated is not None
        assert updated.name == "New"

    def test_update_listing_multiple_fields(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        updated = mp.update_listing(
            listing.id,
            description="new desc",
            version="3.0.0",
            price=9.99,
        )
        assert updated.description == "new desc"
        assert updated.version == "3.0.0"
        assert updated.price == 9.99

    def test_update_listing_disallowed_field(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        updated = mp.update_listing(
            listing.id, author_id="hacker",
        )
        assert updated.author_id == "a1"

    def test_update_listing_not_found(self):
        mp = VerifiedMarketplace()
        assert mp.update_listing("nope") is None

    def test_update_listing_updates_timestamp(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        old_ts = listing.updated_at
        mp.update_listing(listing.id, name="B")
        assert listing.updated_at >= old_ts

    def test_search_returns_published_only_by_default(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("Agent", "d", "a1")
        # pending_review, not published
        results = mp.search(query="Agent")
        assert len(results) == 0

    def test_search_with_status_filter(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("Agent", "d", "a1")
        results = mp.search(
            query="Agent",
            status=ListingStatus.PENDING_REVIEW,
        )
        assert len(results) == 1

    def test_search_by_query_in_name(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("DataBot", "desc", "a1")
        mp.update_listing(
            listing.id,
            status=ListingStatus.PUBLISHED,
        )
        results = mp.search(query="data")
        assert len(results) == 1

    def test_search_by_query_in_description(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("Bot", "analytics tool", "a1")
        mp.update_listing(
            listing.id,
            status=ListingStatus.PUBLISHED,
        )
        results = mp.search(query="analytics")
        assert len(results) == 1

    def test_search_by_category(self):
        mp = VerifiedMarketplace()
        l1 = mp.submit_listing("A", "d", "a1", category="ml")
        l2 = mp.submit_listing("B", "d", "a1", category="web")
        mp.update_listing(l1.id, status=ListingStatus.PUBLISHED)
        mp.update_listing(l2.id, status=ListingStatus.PUBLISHED)
        results = mp.search(category="ml")
        assert len(results) == 1
        assert results[0].name == "A"

    def test_search_by_tags(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing(
            "A", "d", "a1", tags=["nlp", "ai"],
        )
        mp.update_listing(
            listing.id,
            status=ListingStatus.PUBLISHED,
        )
        results = mp.search(tags=["nlp"])
        assert len(results) == 1

    def test_search_by_tags_no_match(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing(
            "A", "d", "a1", tags=["nlp"],
        )
        mp.update_listing(
            listing.id,
            status=ListingStatus.PUBLISHED,
        )
        results = mp.search(tags=["web"])
        assert len(results) == 0

    def test_search_min_rating(self):
        mp = VerifiedMarketplace()
        l1 = mp.submit_listing("A", "d", "a1")
        l2 = mp.submit_listing("B", "d", "a1")
        mp.update_listing(l1.id, status=ListingStatus.PUBLISHED, avg_rating=4.5)
        mp.update_listing(l2.id, status=ListingStatus.PUBLISHED, avg_rating=2.0)
        results = mp.search(min_rating=4.0)
        assert len(results) == 1
        assert results[0].name == "A"

    def test_search_max_price(self):
        mp = VerifiedMarketplace()
        l1 = mp.submit_listing("A", "d", "a1", price=5.0)
        l2 = mp.submit_listing("B", "d", "a1", price=50.0)
        mp.update_listing(l1.id, status=ListingStatus.PUBLISHED)
        mp.update_listing(l2.id, status=ListingStatus.PUBLISHED)
        results = mp.search(max_price=10.0)
        assert len(results) == 1
        assert results[0].name == "A"

    def test_search_increments_stat(self):
        mp = VerifiedMarketplace()
        mp.search()
        mp.search()
        assert mp.get_stats()["searches"] == 2

    def test_search_sorted_by_rating_desc(self):
        mp = VerifiedMarketplace()
        l1 = mp.submit_listing("Low", "d", "a1")
        l2 = mp.submit_listing("High", "d", "a1")
        mp.update_listing(l1.id, status=ListingStatus.PUBLISHED, avg_rating=2.0)
        mp.update_listing(l2.id, status=ListingStatus.PUBLISHED, avg_rating=5.0)
        results = mp.search()
        assert results[0].name == "High"

    def test_publish_requires_approved(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        # status is PENDING_REVIEW
        assert mp.publish(listing.id) is False

    def test_publish_approved_listing(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        mp.update_listing(listing.id, status=ListingStatus.APPROVED)
        assert mp.publish(listing.id) is True
        assert listing.status == ListingStatus.PUBLISHED

    def test_publish_not_found(self):
        mp = VerifiedMarketplace()
        assert mp.publish("nope") is False

    def test_publish_increments_stat(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        mp.update_listing(listing.id, status=ListingStatus.APPROVED)
        mp.publish(listing.id)
        assert mp.get_stats()["published"] == 1

    def test_suspend_listing(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        assert mp.suspend(listing.id, reason="spam") is True
        assert listing.status == ListingStatus.SUSPENDED

    def test_suspend_not_found(self):
        mp = VerifiedMarketplace()
        assert mp.suspend("nope") is False

    def test_suspend_increments_stat(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        mp.suspend(listing.id)
        assert mp.get_stats()["suspended"] == 1

    def test_archive_listing(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        assert mp.archive(listing.id) is True
        assert listing.status == ListingStatus.ARCHIVED

    def test_archive_not_found(self):
        mp = VerifiedMarketplace()
        assert mp.archive("nope") is False

    def test_archive_increments_stat(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        mp.archive(listing.id)
        assert mp.get_stats()["archived"] == 1

    def test_get_featured_empty(self):
        mp = VerifiedMarketplace()
        assert mp.get_featured() == []

    def test_get_featured_with_qualifying_listing(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("Star", "d", "a1")
        mp.update_listing(
            listing.id,
            status=ListingStatus.PUBLISHED,
            avg_rating=4.5,
            download_count=100,
        )
        featured = mp.get_featured()
        assert len(featured) == 1
        assert featured[0].name == "Star"

    def test_get_featured_excludes_low_rating(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        mp.update_listing(
            listing.id,
            status=ListingStatus.PUBLISHED,
            avg_rating=3.0,
            download_count=100,
        )
        assert mp.get_featured() == []

    def test_get_featured_excludes_low_downloads(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        mp.update_listing(
            listing.id,
            status=ListingStatus.PUBLISHED,
            avg_rating=4.5,
            download_count=10,
        )
        assert mp.get_featured() == []

    def test_get_featured_limit(self):
        mp = VerifiedMarketplace()
        for i in range(5):
            listing = mp.submit_listing(f"A{i}", "d", "a1")
            mp.update_listing(
                listing.id,
                status=ListingStatus.PUBLISHED,
                avg_rating=4.5,
                download_count=100 + i,
            )
        assert len(mp.get_featured(limit=3)) == 3

    def test_get_featured_sorted_by_score(self):
        mp = VerifiedMarketplace()
        l1 = mp.submit_listing("Low", "d", "a1")
        l2 = mp.submit_listing("High", "d", "a1")
        mp.update_listing(
            l1.id,
            status=ListingStatus.PUBLISHED,
            avg_rating=4.0,
            download_count=50,
        )
        mp.update_listing(
            l2.id,
            status=ListingStatus.PUBLISHED,
            avg_rating=5.0,
            download_count=200,
        )
        featured = mp.get_featured()
        assert featured[0].name == "High"

    def test_get_by_author(self):
        mp = VerifiedMarketplace()
        mp.submit_listing("A", "d", "author1")
        mp.submit_listing("B", "d", "author1")
        mp.submit_listing("C", "d", "author2")
        results = mp.get_by_author("author1")
        assert len(results) == 2

    def test_get_by_author_no_results(self):
        mp = VerifiedMarketplace()
        assert mp.get_by_author("ghost") == []

    def test_get_stats_total_listings(self):
        mp = VerifiedMarketplace()
        mp.submit_listing("A", "d", "a1")
        mp.submit_listing("B", "d", "a1")
        stats = mp.get_stats()
        assert stats["total_listings"] == 2

    def test_get_stats_status_distribution(self):
        mp = VerifiedMarketplace()
        l = mp.submit_listing("A", "d", "a1")
        mp.update_listing(l.id, status=ListingStatus.APPROVED)
        mp.publish(l.id)
        dist = mp.get_stats()["status_distribution"]
        assert dist.get("published", 0) == 1

    def test_status_lifecycle_full(self):
        mp = VerifiedMarketplace()
        listing = mp.submit_listing("A", "d", "a1")
        assert listing.status == ListingStatus.PENDING_REVIEW
        mp.update_listing(listing.id, status=ListingStatus.APPROVED)
        assert listing.status == ListingStatus.APPROVED
        mp.publish(listing.id)
        assert listing.status == ListingStatus.PUBLISHED
        mp.suspend(listing.id)
        assert listing.status == ListingStatus.SUSPENDED
        mp.archive(listing.id)
        assert listing.status == ListingStatus.ARCHIVED


# ------------------------------------------------------------------ #
#  SecurityAuditPipeline testleri
# ------------------------------------------------------------------ #


class TestSecurityAuditPipeline:
    """Guvenlik denetim hatti testleri."""

    def test_clean_code_passes(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "def hello(): return 42")
        assert report.passed is True
        assert report.result == AuditResult.PASS
        assert report.critical_count == 0

    def test_eval_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "result = eval('1+1')")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_exec_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "exec('print(1)')")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_os_system_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "os.system('rm -rf /')")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_subprocess_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "import subprocess.run")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_os_popen_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "os.popen('ls')")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_os_exec_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "os.execl('/bin/sh', 'sh')")
        assert report.passed is False

    def test_keylogger_pattern_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "keylogger = init_keylog()")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_reverse_shell_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "reverse_shell(ip, port)")
        assert report.passed is False

    def test_cryptominer_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "crypto_miner = CryptoMiner()")
        assert report.passed is False

    def test_backdoor_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "backdoor = open_connection()")
        assert report.passed is False

    def test_file_delete_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "os.remove('/etc/passwd')")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_rmtree_detected(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "shutil.rmtree('/')")
        assert report.passed is False
        assert report.critical_count >= 1

    def test_dynamic_import_is_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "mod = __import__('os')")
        assert report.warning_count >= 1

    def test_compile_usage_is_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "compile('code', 'f', 'exec')")
        # compile is warning, but also has 'exec' pattern
        assert report.warning_count >= 1

    def test_socket_is_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "s = socket.socket()")
        assert report.warning_count >= 1

    def test_requests_lib_is_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "requests.get('http://example.com')")
        assert report.warning_count >= 1

    def test_few_warnings_still_passes(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "import requests.get")
        # 1 warning only -> passes
        assert report.passed is True
        assert report.result == AuditResult.WARNING

    def test_many_warnings_fail(self):
        pipeline = SecurityAuditPipeline()
        code = (
            "socket.connect()\n"
            "requests.get(x)\n"
            "urllib.request.urlopen(x)\n"
            "httpx.get(x)\n"
            "open('file')\n"
        )
        report = pipeline.audit("l1", code)
        # >3 warnings -> fail
        assert report.warning_count > 3
        assert report.passed is False

    def test_base64_decode_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "base64.b64decode(data)")
        assert report.warning_count >= 1

    def test_env_access_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "key = os.environ['SECRET']")
        assert report.warning_count >= 1

    def test_os_getenv_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "os.getenv('TOKEN')")
        assert report.warning_count >= 1

    def test_hex_escape_warning(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", r"s = '\x41\x42'")
        assert report.warning_count >= 1

    def test_get_report_found(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "pass")
        result = pipeline.get_report(report.id)
        assert result is not None
        assert result.id == report.id

    def test_get_report_not_found(self):
        pipeline = SecurityAuditPipeline()
        assert pipeline.get_report("nope") is None

    def test_list_reports_for_listing(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "pass")
        pipeline.audit("l1", "x = eval('1')")
        pipeline.audit("l2", "pass")
        reports = pipeline.list_reports("l1")
        assert len(reports) == 2

    def test_list_reports_empty(self):
        pipeline = SecurityAuditPipeline()
        assert pipeline.list_reports("l999") == []

    def test_get_failed_audits(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "pass")
        pipeline.audit("l2", "eval('x')")
        pipeline.audit("l3", "exec('y')")
        failed = pipeline.get_failed_audits()
        assert len(failed) == 2

    def test_get_failed_audits_sorted_by_critical(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "eval('x')")
        pipeline.audit("l2", "eval('a') and exec('b') and os.system('c')")
        failed = pipeline.get_failed_audits()
        assert failed[0].critical_count >= failed[1].critical_count

    def test_get_failed_audits_limit(self):
        pipeline = SecurityAuditPipeline()
        for i in range(5):
            pipeline.audit(f"l{i}", "eval('x')")
        failed = pipeline.get_failed_audits(limit=3)
        assert len(failed) == 3

    def test_re_audit(self):
        pipeline = SecurityAuditPipeline()
        report1 = pipeline.audit("l1", "eval('x')")
        report2 = pipeline.re_audit("l1", "def f(): return 1")
        assert report1.passed is False
        assert report2.passed is True

    def test_re_audit_adds_to_listing_reports(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "eval('x')")
        pipeline.re_audit("l1", "pass")
        reports = pipeline.list_reports("l1")
        assert len(reports) == 2

    def test_stats_audits_run(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "pass")
        pipeline.audit("l2", "eval('x')")
        stats = pipeline.get_stats()
        assert stats["audits_run"] == 2

    def test_stats_passed_and_failed(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "pass")
        pipeline.audit("l2", "eval('x')")
        stats = pipeline.get_stats()
        assert stats["passed"] == 1
        assert stats["failed"] == 1

    def test_stats_pass_rate(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "pass")
        pipeline.audit("l2", "pass")
        pipeline.audit("l3", "eval('x')")
        stats = pipeline.get_stats()
        assert stats["pass_rate"] == pytest.approx(66.7, abs=0.1)

    def test_stats_critical_and_warnings_found(self):
        pipeline = SecurityAuditPipeline()
        pipeline.audit("l1", "eval('x') and socket.connect()")
        stats = pipeline.get_stats()
        assert stats["critical_found"] >= 1
        assert stats["warnings_found"] >= 1

    def test_audit_report_has_auditor_version(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "pass")
        assert report.auditor_version == "1.2.0"

    def test_audit_report_issues_contain_occurrences(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "eval('a') + eval('b')")
        eval_issues = [i for i in report.issues if i["id"] == "eval_usage"]
        assert len(eval_issues) == 1
        assert eval_issues[0]["occurrences"] == 2

    def test_dependency_vuln_check_pyyaml(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "import pyyaml")
        vuln_issues = [i for i in report.issues if "vuln_" in i["id"]]
        assert len(vuln_issues) >= 1

    def test_no_vuln_for_clean_deps(self):
        pipeline = SecurityAuditPipeline()
        report = pipeline.audit("l1", "import mylib")
        vuln_issues = [i for i in report.issues if "vuln_" in i["id"]]
        assert len(vuln_issues) == 0


# ------------------------------------------------------------------ #
#  RatingReviewSystem testleri
# ------------------------------------------------------------------ #


class TestRatingReviewSystem:
    """Degerlendirme ve yorum sistemi testleri."""

    def test_add_review_basic(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 4.0, "Good", "Nice agent")
        assert review.listing_id == "l1"
        assert review.user_id == "u1"
        assert review.rating == 4.0
        assert review.title == "Good"
        assert review.comment == "Nice agent"
        assert review.status == ReviewStatus.PENDING

    def test_add_review_rating_clamped_high(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 10.0)
        assert review.rating == 5.0

    def test_add_review_rating_clamped_low(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", -2.0)
        assert review.rating == 1.0

    def test_add_review_rating_exact_boundary(self):
        rrs = RatingReviewSystem()
        r1 = rrs.add_review("l1", "u1", 1.0)
        r2 = rrs.add_review("l1", "u2", 5.0)
        assert r1.rating == 1.0
        assert r2.rating == 5.0

    def test_add_review_increments_stat(self):
        rrs = RatingReviewSystem()
        rrs.add_review("l1", "u1", 4.0)
        assert rrs.get_stats()["reviews_added"] == 1

    def test_get_reviews_for_listing(self):
        rrs = RatingReviewSystem()
        rrs.add_review("l1", "u1", 4.0)
        rrs.add_review("l1", "u2", 3.0)
        rrs.add_review("l2", "u3", 5.0)
        reviews = rrs.get_reviews("l1")
        assert len(reviews) == 2

    def test_get_reviews_empty(self):
        rrs = RatingReviewSystem()
        assert rrs.get_reviews("l999") == []

    def test_get_reviews_filter_by_status(self):
        rrs = RatingReviewSystem()
        r1 = rrs.add_review("l1", "u1", 4.0)
        r2 = rrs.add_review("l1", "u2", 3.0)
        rrs.approve_review(r1.id)
        reviews = rrs.get_reviews("l1", status=ReviewStatus.APPROVED)
        assert len(reviews) == 1
        assert reviews[0].id == r1.id

    def test_get_reviews_filter_by_min_rating(self):
        rrs = RatingReviewSystem()
        rrs.add_review("l1", "u1", 5.0)
        rrs.add_review("l1", "u2", 2.0)
        reviews = rrs.get_reviews("l1", min_rating=4.0)
        assert len(reviews) == 1
        assert reviews[0].rating == 5.0

    def test_get_review_by_id(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 4.0)
        result = rrs.get_review(review.id)
        assert result is not None
        assert result.id == review.id

    def test_get_review_not_found(self):
        rrs = RatingReviewSystem()
        assert rrs.get_review("nope") is None

    def test_flag_review(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 1.0, comment="spam")
        assert rrs.flag_review(review.id, reason="spam") is True
        assert review.status == ReviewStatus.FLAGGED

    def test_flag_review_not_found(self):
        rrs = RatingReviewSystem()
        assert rrs.flag_review("nope") is False

    def test_flag_review_increments_stat(self):
        rrs = RatingReviewSystem()
        r = rrs.add_review("l1", "u1", 1.0)
        rrs.flag_review(r.id)
        assert rrs.get_stats()["reviews_flagged"] == 1

    def test_approve_review(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 5.0)
        assert rrs.approve_review(review.id) is True
        assert review.status == ReviewStatus.APPROVED

    def test_approve_review_not_found(self):
        rrs = RatingReviewSystem()
        assert rrs.approve_review("nope") is False

    def test_approve_review_increments_stat(self):
        rrs = RatingReviewSystem()
        r = rrs.add_review("l1", "u1", 5.0)
        rrs.approve_review(r.id)
        assert rrs.get_stats()["reviews_approved"] == 1

    def test_remove_review(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 2.0)
        assert rrs.remove_review(review.id) is True
        assert review.status == ReviewStatus.REMOVED

    def test_remove_review_not_found(self):
        rrs = RatingReviewSystem()
        assert rrs.remove_review("nope") is False

    def test_remove_review_increments_stat(self):
        rrs = RatingReviewSystem()
        r = rrs.add_review("l1", "u1", 2.0)
        rrs.remove_review(r.id)
        assert rrs.get_stats()["reviews_removed"] == 1

    def test_mark_helpful(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 5.0)
        assert rrs.mark_helpful(review.id) is True
        assert review.helpful_count == 1

    def test_mark_helpful_multiple(self):
        rrs = RatingReviewSystem()
        review = rrs.add_review("l1", "u1", 5.0)
        rrs.mark_helpful(review.id)
        rrs.mark_helpful(review.id)
        rrs.mark_helpful(review.id)
        assert review.helpful_count == 3

    def test_mark_helpful_not_found(self):
        rrs = RatingReviewSystem()
        assert rrs.mark_helpful("nope") is False

    def test_mark_helpful_increments_stat(self):
        rrs = RatingReviewSystem()
        r = rrs.add_review("l1", "u1", 5.0)
        rrs.mark_helpful(r.id)
        assert rrs.get_stats()["helpful_marks"] == 1

    def test_get_average_rating(self):
        rrs = RatingReviewSystem()
        rrs.add_review("l1", "u1", 4.0)
        rrs.add_review("l1", "u2", 2.0)
        avg = rrs.get_average_rating("l1")
        assert avg == 3.0

    def test_get_average_rating_empty(self):
        rrs = RatingReviewSystem()
        assert rrs.get_average_rating("l999") == 0.0

    def test_get_average_rating_excludes_removed(self):
        rrs = RatingReviewSystem()
        r1 = rrs.add_review("l1", "u1", 5.0)
        r2 = rrs.add_review("l1", "u2", 1.0)
        rrs.remove_review(r2.id)
        avg = rrs.get_average_rating("l1")
        assert avg == 5.0

    def test_get_average_rating_excludes_flagged(self):
        rrs = RatingReviewSystem()
        r1 = rrs.add_review("l1", "u1", 5.0)
        r2 = rrs.add_review("l1", "u2", 1.0)
        rrs.flag_review(r2.id)
        avg = rrs.get_average_rating("l1")
        assert avg == 5.0

    def test_get_average_rating_includes_pending_and_approved(self):
        rrs = RatingReviewSystem()
        r1 = rrs.add_review("l1", "u1", 4.0)  # pending
        r2 = rrs.add_review("l1", "u2", 2.0)
        rrs.approve_review(r2.id)  # approved
        avg = rrs.get_average_rating("l1")
        assert avg == 3.0

    def test_get_rating_distribution(self):
        rrs = RatingReviewSystem()
        rrs.add_review("l1", "u1", 5.0)
        rrs.add_review("l1", "u2", 5.0)
        rrs.add_review("l1", "u3", 3.0)
        rrs.add_review("l1", "u4", 1.0)
        dist = rrs.get_rating_distribution("l1")
        assert dist[5] == 2
        assert dist[3] == 1
        assert dist[1] == 1
        assert dist[2] == 0
        assert dist[4] == 0

    def test_get_rating_distribution_empty(self):
        rrs = RatingReviewSystem()
        dist = rrs.get_rating_distribution("l999")
        assert dist == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    def test_get_rating_distribution_excludes_removed(self):
        rrs = RatingReviewSystem()
        r1 = rrs.add_review("l1", "u1", 5.0)
        r2 = rrs.add_review("l1", "u2", 1.0)
        rrs.remove_review(r2.id)
        dist = rrs.get_rating_distribution("l1")
        assert dist[5] == 1
        assert dist[1] == 0

    def test_stats_total_reviews(self):
        rrs = RatingReviewSystem()
        rrs.add_review("l1", "u1", 4.0)
        rrs.add_review("l2", "u2", 3.0)
        stats = rrs.get_stats()
        assert stats["total_reviews"] == 2

    def test_stats_active_reviews(self):
        rrs = RatingReviewSystem()
        r1 = rrs.add_review("l1", "u1", 4.0)
        r2 = rrs.add_review("l1", "u2", 3.0)
        rrs.remove_review(r2.id)
        stats = rrs.get_stats()
        assert stats["active_reviews"] == 1

    def test_stats_listings_reviewed(self):
        rrs = RatingReviewSystem()
        rrs.add_review("l1", "u1", 4.0)
        rrs.add_review("l2", "u2", 3.0)
        stats = rrs.get_stats()
        assert stats["listings_reviewed"] == 2


# ------------------------------------------------------------------ #
#  RevenueSharing testleri
# ------------------------------------------------------------------ #


class TestRevenueSharing:
    """Gelir paylasim sistemi testleri."""

    def test_configure_with_defaults(self):
        rs = RevenueSharing()
        config = rs.configure("l1", "author1")
        assert config["listing_id"] == "l1"
        assert config["author_id"] == "author1"
        assert config["platform_fee_pct"] == 30.0

    def test_configure_custom_fee(self):
        rs = RevenueSharing()
        config = rs.configure("l1", "author1", platform_fee_pct=20.0)
        assert config["platform_fee_pct"] == 20.0

    def test_configure_custom_default_fee(self):
        rs = RevenueSharing(default_fee_pct=15.0)
        config = rs.configure("l1", "author1")
        assert config["platform_fee_pct"] == 15.0

    def test_record_transaction_fee_calculation(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        record = rs.record_transaction("l1", 100.0)
        # 30% fee
        assert record.gross_amount == 100.0
        assert record.platform_fee_pct == 30.0
        assert record.net_amount == 70.0

    def test_record_transaction_custom_fee(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1", platform_fee_pct=10.0)
        record = rs.record_transaction("l1", 50.0)
        assert record.net_amount == 45.0

    def test_record_transaction_no_config(self):
        rs = RevenueSharing()
        record = rs.record_transaction("l1", 100.0)
        assert record.author_id == "unknown"
        assert record.net_amount == 70.0  # default 30%

    def test_record_transaction_currency(self):
        rs = RevenueSharing()
        record = rs.record_transaction("l1", 10.0, currency="EUR")
        assert record.currency == "EUR"

    def test_record_transaction_accumulates_pending(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        rs.record_transaction("l1", 100.0)
        pending = rs._pending_payouts.get("author1", 0.0)
        assert pending == pytest.approx(140.0, abs=0.01)

    def test_get_author_earnings(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        earnings = rs.get_author_earnings("author1")
        assert earnings["total_gross"] == 100.0
        assert earnings["total_net"] == 70.0
        assert earnings["transactions"] == 1

    def test_get_author_earnings_no_records(self):
        rs = RevenueSharing()
        earnings = rs.get_author_earnings("ghost")
        assert earnings["total_gross"] == 0.0
        assert earnings["transactions"] == 0

    def test_get_author_earnings_pending_payout(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        earnings = rs.get_author_earnings("author1")
        assert earnings["pending_payout"] == 70.0

    def test_get_listing_revenue(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 50.0)
        rs.record_transaction("l1", 30.0)
        rev = rs.get_listing_revenue("l1")
        assert rev["total_gross"] == 80.0
        assert rev["records"] == 2

    def test_get_listing_revenue_no_records(self):
        rs = RevenueSharing()
        rev = rs.get_listing_revenue("l999")
        assert rev["total_gross"] == 0.0
        assert rev["transactions"] == 0

    def test_get_platform_revenue(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        platform = rs.get_platform_revenue()
        assert platform["total_gross"] == 100.0
        assert platform["platform_fees"] == 30.0
        assert platform["author_payouts"] == 70.0

    def test_get_platform_revenue_no_records(self):
        rs = RevenueSharing()
        platform = rs.get_platform_revenue()
        assert platform["total_gross"] == 0.0

    def test_process_payout_success(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        payout = rs.process_payout("author1")
        assert payout["status"] == "processed"
        assert payout["amount"] == 70.0

    def test_process_payout_clears_pending(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        rs.process_payout("author1")
        assert rs._pending_payouts["author1"] == 0.0

    def test_process_payout_below_minimum(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 5.0)
        payout = rs.process_payout("author1")
        assert payout["status"] == "below_minimum"
        assert payout["minimum"] == 10.0

    def test_process_payout_no_pending(self):
        rs = RevenueSharing()
        payout = rs.process_payout("ghost")
        assert payout["status"] == "below_minimum"

    def test_process_payout_increments_stat(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        rs.process_payout("author1")
        assert rs.get_stats()["payouts_processed"] == 1

    def test_get_pending_payouts(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.configure("l2", "author2")
        rs.record_transaction("l1", 100.0)
        rs.record_transaction("l2", 50.0)
        pending = rs.get_pending_payouts()
        assert len(pending) == 2
        ids = [p["author_id"] for p in pending]
        assert "author1" in ids
        assert "author2" in ids

    def test_get_pending_payouts_eligible_flag(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 5.0)  # net=3.5
        pending = rs.get_pending_payouts()
        assert len(pending) == 1
        assert pending[0]["eligible"] is False

    def test_get_pending_payouts_excludes_zero(self):
        rs = RevenueSharing()
        rs.configure("l1", "author1")
        rs.record_transaction("l1", 100.0)
        rs.process_payout("author1")
        pending = rs.get_pending_payouts()
        assert len(pending) == 0

    def test_stats_transactions(self):
        rs = RevenueSharing()
        rs.record_transaction("l1", 10.0)
        rs.record_transaction("l2", 20.0)
        stats = rs.get_stats()
        assert stats["transactions"] == 2

    def test_stats_total_gross(self):
        rs = RevenueSharing()
        rs.record_transaction("l1", 100.0)
        stats = rs.get_stats()
        assert stats["total_gross"] == 100.0

    def test_stats_configured_listings(self):
        rs = RevenueSharing()
        rs.configure("l1", "a1")
        rs.configure("l2", "a2")
        stats = rs.get_stats()
        assert stats["configured_listings"] == 2


# ------------------------------------------------------------------ #
#  DependencyResolver testleri
# ------------------------------------------------------------------ #


class TestDependencyResolver:
    """Bagimlilik cozumleyici testleri."""

    def test_analyze_basic(self):
        dr = DependencyResolver()
        nodes = dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
        ])
        assert len(nodes) == 1
        assert nodes[0].name == "requests"
        assert nodes[0].status == DependencyStatus.RESOLVED

    def test_analyze_missing_version(self):
        dr = DependencyResolver()
        nodes = dr.analyze("l1", [
            {"name": "mylib", "version": "", "required_version": "1.0"},
        ])
        assert nodes[0].status == DependencyStatus.MISSING

    def test_analyze_conflict_version(self):
        dr = DependencyResolver()
        nodes = dr.analyze("l1", [
            {"name": "requests", "version": "2.20.0", "required_version": "2.31.0"},
        ])
        assert nodes[0].status == DependencyStatus.CONFLICT

    def test_analyze_outdated_version(self):
        dr = DependencyResolver()
        nodes = dr.analyze("l1", [
            {"name": "requests", "version": "2.25.0", "required_version": ""},
        ])
        assert nodes[0].status == DependencyStatus.OUTDATED

    def test_analyze_increments_stat(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "a", "version": "1.0", "required_version": ""},
            {"name": "b", "version": "1.0", "required_version": ""},
        ])
        assert dr.get_stats()["analyzed"] == 2

    def test_analyze_sets_alternatives(self):
        dr = DependencyResolver()
        nodes = dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
        ])
        assert "httpx" in nodes[0].alternatives

    def test_analyze_unknown_no_alternatives(self):
        dr = DependencyResolver()
        nodes = dr.analyze("l1", [
            {"name": "customlib", "version": "1.0", "required_version": "1.0"},
        ])
        assert nodes[0].alternatives == []

    def test_check_conflicts_found(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.20.0", "required_version": "2.31.0"},
        ])
        conflicts = dr.check_conflicts("l1")
        assert len(conflicts) == 1
        assert conflicts[0]["status"] == "conflict"

    def test_check_conflicts_missing(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "mylib", "version": "", "required_version": "1.0"},
        ])
        conflicts = dr.check_conflicts("l1")
        assert len(conflicts) == 1
        assert conflicts[0]["status"] == "missing"

    def test_check_conflicts_none(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
        ])
        conflicts = dr.check_conflicts("l1")
        assert len(conflicts) == 0

    def test_check_conflicts_increments_stat(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "mylib", "version": "", "required_version": "1.0"},
        ])
        dr.check_conflicts("l1")
        assert dr.get_stats()["conflicts_found"] >= 1

    def test_check_conflicts_empty_listing(self):
        dr = DependencyResolver()
        assert dr.check_conflicts("l999") == []

    def test_resolve_all_resolved(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
        ])
        result = dr.resolve("l1")
        assert result["fully_resolved"] is True
        assert result["resolved_count"] == 1
        assert result["unresolved_count"] == 0

    def test_resolve_with_outdated_upgrades(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.25.0", "required_version": ""},
        ])
        result = dr.resolve("l1")
        assert result["fully_resolved"] is True
        assert any(r.get("update_to") for r in result["resolved"])

    def test_resolve_with_unresolved(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "mylib", "version": "", "required_version": "1.0"},
        ])
        result = dr.resolve("l1")
        assert result["fully_resolved"] is False
        assert result["unresolved_count"] == 1

    def test_resolve_empty_listing(self):
        dr = DependencyResolver()
        result = dr.resolve("l999")
        assert result["total"] == 0
        assert result["fully_resolved"] is True

    def test_resolve_increments_stat(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
        ])
        dr.resolve("l1")
        assert dr.get_stats()["resolved"] >= 1

    def test_get_dependency_tree(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
            {"name": "flask", "version": "3.0.0", "required_version": "3.0.0"},
        ])
        tree = dr.get_dependency_tree("l1")
        assert tree["total"] == 2
        names = [d["name"] for d in tree["dependencies"]]
        assert "requests" in names
        assert "flask" in names

    def test_get_dependency_tree_counts(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
            {"name": "mylib", "version": "", "required_version": "1.0"},
        ])
        tree = dr.get_dependency_tree("l1")
        assert tree["resolved"] == 1
        assert tree["issues"] == 1

    def test_get_dependency_tree_empty(self):
        dr = DependencyResolver()
        tree = dr.get_dependency_tree("l999")
        assert tree["total"] == 0

    def test_suggest_alternatives_known(self):
        dr = DependencyResolver()
        alts = dr.suggest_alternatives("requests")
        assert "httpx" in alts
        assert "aiohttp" in alts

    def test_suggest_alternatives_unknown(self):
        dr = DependencyResolver()
        alts = dr.suggest_alternatives("mylib")
        assert alts == []

    def test_suggest_alternatives_increments_stat(self):
        dr = DependencyResolver()
        dr.suggest_alternatives("pandas")
        assert dr.get_stats()["alternatives_suggested"] == 1

    def test_suggest_alternatives_no_increment_for_unknown(self):
        dr = DependencyResolver()
        dr.suggest_alternatives("unknownlib")
        assert dr.get_stats()["alternatives_suggested"] == 0

    def test_check_updates(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.25.0", "required_version": ""},
        ])
        updates = dr.check_updates("l1")
        assert len(updates) == 1
        assert updates[0]["latest_version"] == "2.31.0"

    def test_check_updates_none_needed(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
        ])
        updates = dr.check_updates("l1")
        assert len(updates) == 0

    def test_check_updates_empty(self):
        dr = DependencyResolver()
        assert dr.check_updates("l999") == []

    def test_stats_total_nodes(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "a", "version": "1.0", "required_version": "1.0"},
        ])
        assert dr.get_stats()["total_nodes"] == 1

    def test_stats_listings_tracked(self):
        dr = DependencyResolver()
        dr.analyze("l1", [{"name": "a", "version": "1.0", "required_version": ""}])
        dr.analyze("l2", [{"name": "b", "version": "1.0", "required_version": ""}])
        assert dr.get_stats()["listings_tracked"] == 2

    def test_stats_status_distribution(self):
        dr = DependencyResolver()
        dr.analyze("l1", [
            {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
            {"name": "mylib", "version": "", "required_version": "1.0"},
        ])
        dist = dr.get_stats()["status_distribution"]
        assert dist.get("resolved", 0) >= 1
        assert dist.get("missing", 0) >= 1


# ------------------------------------------------------------------ #
#  SkillAnalytics testleri
# ------------------------------------------------------------------ #


class TestSkillAnalytics:
    """Beceri analitik sistemi testleri."""

    def test_record_install(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        assert sa._install_counts["l1"] == 1

    def test_record_install_multiple(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        sa.record_install("l1")
        assert sa._install_counts["l1"] == 3

    def test_record_install_increments_stat(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        assert sa.get_stats()["installs_recorded"] == 1

    def test_record_uninstall(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_uninstall("l1")
        assert sa._uninstall_counts["l1"] == 1

    def test_record_uninstall_increments_stat(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_uninstall("l1")
        assert sa.get_stats()["uninstalls_recorded"] == 1

    def test_record_usage(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_usage("l1", api_calls=100, errors=5, response_ms=50.0)
        data = sa._usage_data["l1"]
        assert data["total_api_calls"] == 100
        assert data["total_errors"] == 5

    def test_record_usage_increments_stat(self):
        sa = SkillAnalytics()
        sa.record_usage("l1", api_calls=10)
        assert sa.get_stats()["usage_events"] == 1

    def test_record_usage_metric_api_calls(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_usage("l1", api_calls=50, errors=2, response_ms=30.0)
        metric = sa.get_metrics("l1")
        assert metric is not None
        assert metric.api_calls == 50

    def test_record_usage_error_rate(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_usage("l1", api_calls=100, errors=10, response_ms=0)
        metric = sa.get_metrics("l1")
        assert metric.error_rate == 10.0

    def test_get_metrics_found(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        metric = sa.get_metrics("l1")
        assert metric is not None
        assert metric.listing_id == "l1"

    def test_get_metrics_not_found(self):
        sa = SkillAnalytics()
        assert sa.get_metrics("l999") is None

    def test_get_metrics_increments_stat(self):
        sa = SkillAnalytics()
        sa.get_metrics("l1")
        assert sa.get_stats()["metrics_queried"] == 1

    def test_get_trending(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        sa.record_install("l2")
        trending = sa.get_trending()
        assert len(trending) == 2
        assert trending[0]["listing_id"] == "l1"

    def test_get_trending_empty(self):
        sa = SkillAnalytics()
        assert sa.get_trending() == []

    def test_get_trending_limit(self):
        sa = SkillAnalytics()
        for i in range(5):
            sa.record_install(f"l{i}")
        trending = sa.get_trending(limit=3)
        assert len(trending) == 3

    def test_get_trending_score_includes_api_calls(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_usage("l1", api_calls=1000)
        sa.record_install("l2")
        sa.record_install("l2")
        sa.record_install("l2")
        trending = sa.get_trending()
        # l1: 1*10 + 1000 = 1010, l2: 3*10 = 30
        assert trending[0]["listing_id"] == "l1"

    def test_get_top_rated(self):
        sa = SkillAnalytics()
        sa.set_rating("l1", 4.5)
        sa.set_rating("l2", 3.0)
        sa.set_rating("l3", 5.0)
        top = sa.get_top_rated()
        assert top[0]["listing_id"] == "l3"
        assert top[0]["rating"] == 5.0

    def test_get_top_rated_empty(self):
        sa = SkillAnalytics()
        assert sa.get_top_rated() == []

    def test_get_top_rated_limit(self):
        sa = SkillAnalytics()
        for i in range(5):
            sa.set_rating(f"l{i}", float(i))
        assert len(sa.get_top_rated(limit=3)) == 3

    def test_get_most_installed(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        sa.record_install("l2")
        installed = sa.get_most_installed()
        assert installed[0]["listing_id"] == "l1"
        assert installed[0]["installs"] == 2

    def test_get_most_installed_empty(self):
        sa = SkillAnalytics()
        assert sa.get_most_installed() == []

    def test_get_most_installed_limit(self):
        sa = SkillAnalytics()
        for i in range(5):
            sa.record_install(f"l{i}")
        assert len(sa.get_most_installed(limit=2)) == 2

    def test_get_most_installed_includes_uninstalls(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        sa.record_uninstall("l1")
        installed = sa.get_most_installed()
        assert installed[0]["uninstalls"] == 1

    def test_get_retention_rate_full(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        assert sa.get_retention_rate("l1") == 1.0

    def test_get_retention_rate_partial(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        sa.record_uninstall("l1")
        rate = sa.get_retention_rate("l1")
        assert rate == 0.5

    def test_get_retention_rate_zero_installs(self):
        sa = SkillAnalytics()
        assert sa.get_retention_rate("l999") == 0.0

    def test_get_retention_rate_all_uninstalled(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_uninstall("l1")
        assert sa.get_retention_rate("l1") == 0.0

    def test_stats_total_installs(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l2")
        stats = sa.get_stats()
        assert stats["total_installs"] == 2

    def test_stats_net_installs(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        sa.record_uninstall("l1")
        stats = sa.get_stats()
        assert stats["net_installs"] == 1

    def test_stats_tracked_listings(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l2")
        stats = sa.get_stats()
        assert stats["tracked_listings"] == 2

    def test_set_rating(self):
        sa = SkillAnalytics()
        sa.set_rating("l1", 4.5)
        assert sa._ratings["l1"] == 4.5

    def test_install_updates_active_users(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        metric = sa.get_metrics("l1")
        assert metric.active_users == 1

    def test_uninstall_decrements_active_users(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_install("l1")
        sa.record_uninstall("l1")
        metric = sa.get_metrics("l1")
        assert metric.active_users == 1

    def test_active_users_never_negative(self):
        sa = SkillAnalytics()
        sa.record_install("l1")
        sa.record_uninstall("l1")
        sa.record_uninstall("l1")
        metric = sa.get_metrics("l1")
        assert metric.active_users >= 0


# ------------------------------------------------------------------ #
#  AgentMarketOrchestrator testleri
# ------------------------------------------------------------------ #


class TestAgentMarketOrchestrator:
    """Agent Market orkestrator testleri."""

    def test_init_creates_all_components(self):
        orch = AgentMarketOrchestrator()
        assert orch.marketplace is not None
        assert orch.audit_pipeline is not None
        assert orch.reviews is not None
        assert orch.revenue is not None
        assert orch.deps is not None
        assert orch.analytics is not None

    def test_submit_and_audit_clean_code_approved(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="SafeAgent",
            description="A safe agent",
            author_id="author1",
            code="def run(): return True",
        )
        assert result["status"] == "approved"
        assert result["audit_passed"] is True
        assert result["critical_issues"] == 0

    def test_submit_and_audit_dangerous_code_rejected(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="BadAgent",
            description="Dangerous agent",
            author_id="author2",
            code="eval(input())",
        )
        assert result["status"] == "rejected"
        assert result["audit_passed"] is False
        assert result["critical_issues"] >= 1

    def test_submit_and_audit_listing_created(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="TestAgent",
            description="desc",
            author_id="a1",
            code="pass",
        )
        listing = orch.marketplace.get_listing(result["listing_id"])
        assert listing is not None
        assert listing.name == "TestAgent"

    def test_submit_and_audit_approved_status_set(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="Agent", description="d", author_id="a1",
            code="def f(): pass",
        )
        listing = orch.marketplace.get_listing(result["listing_id"])
        assert listing.status == ListingStatus.APPROVED

    def test_submit_and_audit_rejected_status_set(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="Agent", description="d", author_id="a1",
            code="exec('malicious')",
        )
        listing = orch.marketplace.get_listing(result["listing_id"])
        assert listing.status == ListingStatus.REJECTED

    def test_submit_and_audit_configures_revenue_for_paid(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="PaidAgent",
            description="Premium",
            author_id="a1",
            price=19.99,
            code="def run(): return 1",
            revenue_model=RevenueModel.ONE_TIME,
        )
        assert result["status"] == "approved"
        config = orch.revenue._configs.get(result["listing_id"])
        assert config is not None
        assert config["author_id"] == "a1"

    def test_submit_and_audit_no_revenue_for_free(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="FreeAgent", description="Free",
            author_id="a1", price=0.0, code="pass",
        )
        config = orch.revenue._configs.get(result["listing_id"])
        assert config is None

    def test_submit_and_audit_increments_stats(self):
        orch = AgentMarketOrchestrator()
        orch.submit_and_audit("A", "d", "a1", code="pass")
        orch.submit_and_audit("B", "d", "a2", code="eval('x')")
        stats = orch.get_stats()["orchestrator"]
        assert stats["submit_and_audit_count"] == 2
        assert stats["auto_approved"] == 1
        assert stats["auto_rejected"] == 1

    def test_submit_and_audit_report_id_returned(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit("A", "d", "a1", code="pass")
        assert "report_id" in result
        report = orch.audit_pipeline.get_report(result["report_id"])
        assert report is not None

    def test_submit_and_audit_with_tags_and_category(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="MLBot", description="ML agent",
            author_id="a1", category="ml",
            tags=["ai", "data"], code="import math",
        )
        listing = orch.marketplace.get_listing(result["listing_id"])
        assert listing.category == "ml"
        assert listing.tags == ["ai", "data"]

    def test_install_listing_success(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="Agent", description="d",
            author_id="a1", code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        install = orch.install_listing(listing_id, "user1")
        assert install["success"] is True
        assert install["listing_name"] == "Agent"

    def test_install_listing_not_found(self):
        orch = AgentMarketOrchestrator()
        result = orch.install_listing("nope", "user1")
        assert result["success"] is False
        assert result["error"] == "listing_not_found"

    def test_install_listing_not_published(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="A", description="d",
            author_id="a1", code="pass",
        )
        # status is APPROVED, not PUBLISHED
        install = orch.install_listing(result["listing_id"], "user1")
        assert install["success"] is False
        assert install["error"] == "listing_not_published"

    def test_install_listing_increments_download(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="A", description="d",
            author_id="a1", code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        orch.install_listing(listing_id, "u1")
        listing = orch.marketplace.get_listing(listing_id)
        assert listing.download_count == 1

    def test_install_listing_records_analytics(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="A", description="d",
            author_id="a1", code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        orch.install_listing(listing_id, "u1")
        assert orch.analytics._install_counts.get(listing_id, 0) == 1

    def test_install_listing_paid_records_revenue(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="PaidA", description="d",
            author_id="a1", price=25.0,
            code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        install = orch.install_listing(listing_id, "u1")
        assert install["success"] is True
        assert install["revenue_recorded"] is True

    def test_install_listing_free_no_revenue(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="FreeA", description="d",
            author_id="a1", price=0.0,
            code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        install = orch.install_listing(listing_id, "u1")
        assert install["revenue_recorded"] is False

    def test_install_listing_with_dependencies_resolved(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="A", description="d",
            author_id="a1", code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        install = orch.install_listing(
            listing_id, "u1",
            dependencies=[
                {"name": "requests", "version": "2.31.0", "required_version": "2.31.0"},
            ],
        )
        assert install["success"] is True
        assert install["dependencies_resolved"] is True

    def test_install_listing_with_unresolved_deps_fails(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="A", description="d",
            author_id="a1", code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        install = orch.install_listing(
            listing_id, "u1",
            dependencies=[
                {"name": "mylib", "version": "", "required_version": "1.0"},
            ],
        )
        assert install["success"] is False
        assert install["error"] == "dependency_resolution_failed"

    def test_install_listing_increments_stat(self):
        orch = AgentMarketOrchestrator()
        result = orch.submit_and_audit(
            name="A", description="d",
            author_id="a1", code="pass",
        )
        listing_id = result["listing_id"]
        orch.marketplace.publish(listing_id)
        orch.install_listing(listing_id, "u1")
        stats = orch.get_stats()["orchestrator"]
        assert stats["installs_processed"] == 1

    def test_get_marketplace_overview(self):
        orch = AgentMarketOrchestrator()
        orch.submit_and_audit("A", "d", "a1", code="pass")
        overview = orch.get_marketplace_overview()
        assert "listings" in overview
        assert "reviews" in overview
        assert "revenue" in overview
        assert "analytics" in overview
        assert "trending" in overview

    def test_get_marketplace_overview_listing_counts(self):
        orch = AgentMarketOrchestrator()
        r1 = orch.submit_and_audit("A", "d", "a1", code="pass")
        orch.marketplace.publish(r1["listing_id"])
        overview = orch.get_marketplace_overview()
        assert overview["listings"]["total"] >= 1

    def test_get_stats_all_sections(self):
        orch = AgentMarketOrchestrator()
        stats = orch.get_stats()
        assert "marketplace" in stats
        assert "audit" in stats
        assert "reviews" in stats
        assert "revenue" in stats
        assert "dependencies" in stats
        assert "analytics" in stats
        assert "orchestrator" in stats

    def test_full_lifecycle(self):
        """Tam yasam dongusu: submit -> audit -> publish -> install -> review."""
        orch = AgentMarketOrchestrator()

        # Submit and audit
        result = orch.submit_and_audit(
            name="SuperAgent",
            description="The best agent",
            author_id="topdev",
            price=15.0,
            code="def run(): return 42",
            category="automation",
            tags=["bot", "helper"],
        )
        assert result["status"] == "approved"
        listing_id = result["listing_id"]

        # Publish
        assert orch.marketplace.publish(listing_id) is True

        # Install
        install = orch.install_listing(listing_id, "user1")
        assert install["success"] is True

        # Review
        review = orch.reviews.add_review(listing_id, "user1", 5.0, "Great!", "Excellent!")
        orch.reviews.approve_review(review.id)
        avg = orch.reviews.get_average_rating(listing_id)
        assert avg == 5.0

        # Stats
        stats = orch.get_stats()
        assert stats["orchestrator"]["submit_and_audit_count"] == 1
        assert stats["orchestrator"]["installs_processed"] == 1
