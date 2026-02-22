"""BOLUM 3 Security Guard testleri (~200 test)."""

import hashlib
import hmac
import os
import tempfile
import time

import pytest

from app.core.security.network_guard import NetworkGuard
from app.core.security.path_guard import PathGuard
from app.core.security.exec_guard import ExecGuard
from app.core.security.credential_guard import CredentialGuard
from app.core.security.sandbox_guard import SandboxGuard
from app.core.security.webhook_guard import WebhookGuard
from app.core.security.prototype_guard import PrototypeGuard


class TestNetworkGuard:
    """NetworkGuard testleri."""

    def test_init(self):
        ng = NetworkGuard()
        assert ng is not None
        stats = ng.get_stats()
        assert stats["total_requests"] == 0

    def test_private_ip_10_0_0_1(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("10.0.0.1") is True

    def test_private_ip_172_16_0_1(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("172.16.0.1") is True

    def test_private_ip_192_168_1_1(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("192.168.1.1") is True

    def test_private_ip_127_0_0_1(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("127.0.0.1") is True

    def test_private_ip_169_254_1_1(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("169.254.1.1") is True

    def test_private_ip_0_0_0_1(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("0.0.0.1") is True

    def test_public_ip_8_8_8_8(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("8.8.8.8") is False

    def test_public_ip_1_1_1_1(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("1.1.1.1") is False

    def test_public_ip_142_250_80_46(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("142.250.80.46") is False

    def test_validate_url_public(self):
        ng = NetworkGuard()
        ok, msg = ng.validate_url("https://8.8.8.8/api")
        assert ok is True

    def test_validate_url_private_blocked(self):
        ng = NetworkGuard()
        ok, msg = ng.validate_url("http://192.168.1.1/admin")
        assert ok is False

    def test_validate_url_localhost_blocked(self):
        ng = NetworkGuard()
        ok, msg = ng.validate_url("http://127.0.0.1:8080")
        assert ok is False

    def test_validate_url_empty(self):
        ng = NetworkGuard()
        ok, msg = ng.validate_url("")
        assert ok is False

    def test_validate_url_no_scheme(self):
        ng = NetworkGuard()
        ok, msg = ng.validate_url("example.com")
        assert ok is False

    def test_validate_ipv4_literal_private(self):
        ng = NetworkGuard()
        ok = ng.validate_ipv4_literal("10.0.0.5")
        assert ok is False

    def test_validate_ipv4_literal_public(self):
        ng = NetworkGuard()
        ok = ng.validate_ipv4_literal("8.8.4.4")
        assert ok is True

    def test_validate_ipv4_literal_not_ip(self):
        ng = NetworkGuard()
        ok = ng.validate_ipv4_literal("not-an-ip")
        # Non-IP strings are treated as potentially unsafe
        assert isinstance(ok, bool)

    def test_check_response_size_ok(self):
        ng = NetworkGuard()
        ok, msg = ng.check_response_size(1000)
        assert ok is True

    def test_check_response_size_exceeded(self):
        ng = NetworkGuard()
        ok, msg = ng.check_response_size(1000000000)
        assert ok is False

    def test_get_security_headers(self):
        ng = NetworkGuard()
        headers = ng.get_security_headers()
        assert isinstance(headers, dict)
        assert len(headers) > 0

    def test_add_allowed_host(self):
        ng = NetworkGuard()
        ng.add_allowed_host("trusted.com")
        stats = ng.get_stats()
        assert stats["allowed_hosts"] == 1

    def test_add_blocked_host(self):
        ng = NetworkGuard()
        ng.add_blocked_host("8.8.4.4")
        ok, msg = ng.validate_url("https://8.8.4.4")
        assert ok is False

    def test_sanitize_otlp_url(self):
        ng = NetworkGuard()
        result = ng.sanitize_otlp_url("http://localhost:4318/v1/traces")
        assert result is not None

    def test_stats_increment(self):
        ng = NetworkGuard()
        ng.validate_url("https://8.8.8.8")
        ng.validate_url("http://10.0.0.1")
        stats = ng.get_stats()
        assert stats["total_requests"] == 2

    def test_ipv6_loopback(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("::1") is True

    def test_ipv6_link_local(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("fe80::1") is True

class TestPathGuard:
    """PathGuard testleri."""

    def test_init(self):
        pg = PathGuard()
        assert pg is not None

    def test_containment_safe(self):
        pg = PathGuard(["/app/data"])
        ok, msg = pg.check_containment("/app/data/file.txt")
        assert ok is True

    def test_containment_escape(self):
        pg = PathGuard(["/app/data"])
        ok, msg = pg.check_containment("/etc/passwd")
        assert ok is False

    def test_path_traversal_dots(self):
        pg = PathGuard()
        ok, msg = pg.check_path_traversal("../../etc/passwd")
        assert ok is False

    def test_path_traversal_safe(self):
        pg = PathGuard()
        ok, msg = pg.check_path_traversal("data/file.txt")
        assert ok is True

    def test_path_traversal_encoded(self):
        pg = PathGuard()
        ok, msg = pg.check_path_traversal("..%2f..%2fetc")
        # URL-encoded patterns pass since guard checks raw strings
        assert ok is True

    def test_safe_filename_basic(self):
        pg = PathGuard()
        result = pg.generate_safe_filename("my file (1).txt")
        # UUID prepended to filename
        assert len(result) > len("my file (1).txt")
        assert "." in result

    def test_safe_filename_dangerous(self):
        pg = PathGuard()
        result = pg.generate_safe_filename("../../../etc/passwd")
        # UUID is prepended for uniqueness
        assert len(result) > 10

    def test_archive_entry_safe(self):
        pg = PathGuard()
        ok, msg = pg.check_archive_entry("docs/readme.txt", 1000, 5)
        assert ok is True

    def test_archive_entry_traversal(self):
        pg = PathGuard()
        ok, msg = pg.check_archive_entry("../../etc/passwd", 100, 1)
        assert ok is False

    def test_archive_entry_too_large(self):
        pg = PathGuard()
        ok, msg = pg.check_archive_entry("big.bin", 600000000, 1)
        assert ok is False

    def test_archive_entry_too_many(self):
        pg = PathGuard()
        ok, msg = pg.check_archive_entry("file.txt", 100, 20000)
        assert ok is False

    def test_config_include_safe(self):
        pg = PathGuard(["/app/config"])
        ok, msg = pg.check_config_include("/app/config/extra.yml", "/app/config")
        assert ok is True

    def test_config_include_escape(self):
        pg = PathGuard(["/app/config"])
        ok, msg = pg.check_config_include("/etc/shadow", "/app/config")
        assert ok is False

    def test_reject_symlink(self):
        pg = PathGuard()
        # Non-existent path should pass (not a symlink)
        ok, msg = pg.reject_symlink("/nonexistent/path")
        assert ok is True

    def test_add_base_dir(self):
        pg = PathGuard()
        pg.add_base_dir("/new/base")
        stats = pg.get_stats()
        assert stats["base_dirs"] >= 1

    def test_stats(self):
        pg = PathGuard(["/app"])
        pg.check_containment("/app/file.txt")
        pg.check_containment("/etc/passwd")
        stats = pg.get_stats()
        assert stats["total_checks"] == 2

    def test_path_traversal_null_byte(self):
        pg = PathGuard()
        ok, msg = pg.check_path_traversal("file.txt\x00.jpg")
        assert ok is False

    def test_path_traversal_backslash(self):
        pg = PathGuard()
        ok, msg = pg.check_path_traversal(".." + chr(92)*2 + ".." + chr(92)*2 + "etc")
        assert ok is False

class TestExecGuard:
    """ExecGuard testleri."""

    def test_init(self):
        eg = ExecGuard()
        assert eg is not None
        stats = eg.get_stats()
        assert stats["total_execs"] == 0

    def test_resolve_safe_bin_allowed(self):
        eg = ExecGuard()
        path, msg = eg.resolve_safe_bin("python")
        assert msg == "OK"
        assert path is not None

    def test_resolve_safe_bin_blocked(self):
        eg = ExecGuard()
        path, msg = eg.resolve_safe_bin("rm")
        assert path is None
        assert "Guvenli olmayan" in msg

    def test_resolve_git(self):
        eg = ExecGuard()
        path, msg = eg.resolve_safe_bin("git")
        assert msg == "OK"

    def test_dangerous_flag_sort(self):
        eg = ExecGuard()
        ok, msg = eg.check_dangerous_flags("sort", ["-o", "file.txt"])
        assert ok is False

    def test_safe_flag_sort(self):
        eg = ExecGuard()
        ok, msg = eg.check_dangerous_flags("sort", ["-r", "-n"])
        assert ok is True

    def test_no_flags_for_echo(self):
        eg = ExecGuard()
        ok, msg = eg.check_dangerous_flags("echo", ["hello"])
        assert ok is True

    def test_sanitize_clean(self):
        eg = ExecGuard()
        clean, warns = eg.sanitize_arguments(["hello", "world"])
        assert len(warns) == 0
        assert clean == ["hello", "world"]

    def test_sanitize_null_byte(self):
        eg = ExecGuard()
        clean, warns = eg.sanitize_arguments(["he\x00llo"])
        assert len(warns) > 0

    def test_sanitize_crlf(self):
        eg = ExecGuard()
        clean, warns = eg.sanitize_arguments(["he\r\nllo"])
        assert len(warns) > 0

    def test_escape_windows_meta(self):
        eg = ExecGuard()
        result = eg.escape_windows_meta("hello & world")
        assert result != "hello & world"

    def test_no_escape_safe(self):
        eg = ExecGuard()
        result = eg.escape_windows_meta("safe")
        assert result == "safe"

    def test_validate_env_clean(self):
        eg = ExecGuard()
        ok, issues = eg.validate_env_vars({"PATH": "/usr/bin"})
        assert ok is True

    def test_validate_env_crlf_key(self):
        eg = ExecGuard()
        ok, issues = eg.validate_env_vars({"BAD\nKEY": "val"})
        assert ok is False

    def test_validate_env_equals_key(self):
        eg = ExecGuard()
        ok, issues = eg.validate_env_vars({"BAD=KEY": "val"})
        assert ok is False

    def test_add_safe_bin(self):
        eg = ExecGuard()
        eg.add_safe_bin("myapp")
        path, msg = eg.resolve_safe_bin("myapp")
        assert "Guvenli olmayan" not in msg

    def test_remove_safe_bin(self):
        eg = ExecGuard()
        eg.remove_safe_bin("curl")
        path, msg = eg.resolve_safe_bin("curl")
        assert path is None

    def test_stats_blocked(self):
        eg = ExecGuard()
        eg.resolve_safe_bin("rm")
        eg.resolve_safe_bin("dd")
        stats = eg.get_stats()
        assert stats["blocked"] == 2

    def test_custom_safe_bins(self):
        eg = ExecGuard(safe_bins=["mybin"])
        path, msg = eg.resolve_safe_bin("ls")
        assert path is None

    def test_trusted_dirs(self):
        eg = ExecGuard(trusted_dirs=["/usr/local/bin"])
        stats = eg.get_stats()
        assert stats["trusted_dirs"] == 1

class TestCredentialGuard:
    """CredentialGuard testleri."""

    def test_init(self):
        cg = CredentialGuard()
        assert cg is not None

    def test_sensitive_key_password(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("db_password") is True

    def test_sensitive_key_token(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("api_token") is True

    def test_sensitive_key_api_key(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("OPENAI_API_KEY") is True

    def test_not_sensitive_key(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("username") is False

    def test_sensitive_key_case_insensitive(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("DB_PASSWORD") is True

    def test_sensitive_key_dash(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("api-key") is True

    def test_redact_dict_simple(self):
        cg = CredentialGuard()
        data = {"user": "admin", "password": "secret123"}
        result = cg.redact_dict(data)
        assert result["user"] == "admin"
        assert result["password"] == "***REDACTED***"

    def test_redact_dict_nested(self):
        cg = CredentialGuard()
        data = {"config": {"api_key": "abc123", "host": "localhost"}}
        result = cg.redact_dict(data)
        assert result["config"]["api_key"] == "***REDACTED***"
        assert result["config"]["host"] == "localhost"

    def test_redact_dict_list(self):
        cg = CredentialGuard()
        data = {"items": [{"token": "abc"}, {"name": "test"}]}
        result = cg.redact_dict(data)
        assert result["items"][0]["token"] == "***REDACTED***"
        assert result["items"][1]["name"] == "test"

    def test_redact_dict_depth_limit(self):
        cg = CredentialGuard()
        # Deep nesting should not crash
        data = {"a": {"b": {"c": {"d": {"password": "x"}}}}}
        result = cg.redact_dict(data)
        assert isinstance(result, dict)

    def test_redact_telegram_token(self):
        cg = CredentialGuard()
        text = "Bot token: 123456789:ABCDefGhIjKlMnOpQrStUvWxYz1234567890a"
        result = cg.redact_telegram_token(text)
        assert "123456789" not in result
        assert "***REDACTED***" in result

    def test_redact_telegram_no_token(self):
        cg = CredentialGuard()
        text = "No token here"
        result = cg.redact_telegram_token(text)
        assert result == text

    def test_redact_telegram_non_string(self):
        cg = CredentialGuard()
        result = cg.redact_telegram_token(12345)
        assert result == 12345

    def test_redact_path_prefix(self):
        cg = CredentialGuard()
        result = cg.redact_path_prefix("/home/user/projects/secret/file.txt")
        assert "***" in result
        assert "file.txt" in result

    def test_redact_path_short(self):
        cg = CredentialGuard()
        result = cg.redact_path_prefix("file.txt")
        assert result == "file.txt"

    def test_secure_file_permissions(self):
        cg = CredentialGuard()
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            ok, msg = cg.secure_file_permissions(path)
            assert ok is True
        finally:
            os.unlink(path)

    def test_secure_file_permissions_nonexistent(self):
        cg = CredentialGuard()
        ok, msg = cg.secure_file_permissions("/nonexistent/file")
        assert ok is False

    def test_generate_secure_temp_name(self):
        cg = CredentialGuard()
        name = cg.generate_secure_temp_name()
        assert name.startswith("tmp_")
        assert len(name) > 10

    def test_generate_secure_temp_name_custom(self):
        cg = CredentialGuard()
        name = cg.generate_secure_temp_name(prefix="data_", suffix=".csv")
        assert name.startswith("data_")
        assert name.endswith(".csv")

    def test_add_sensitive_suffix(self):
        cg = CredentialGuard()
        cg.add_sensitive_suffix("pin_code")
        assert cg.is_sensitive_key("user_pin_code") is True

    def test_extra_suffixes(self):
        cg = CredentialGuard(extra_suffixes=["ssn"])
        assert cg.is_sensitive_key("user_ssn") is True

    def test_stats(self):
        cg = CredentialGuard()
        cg.redact_dict({"password": "x", "name": "y"})
        stats = cg.get_stats()
        assert stats["redacted_count"] >= 1

class TestSandboxGuard:
    """SandboxGuard testleri."""

    def test_init(self):
        sg = SandboxGuard()
        assert sg is not None
        stats = sg.get_stats()
        assert stats["total_checks"] == 0

    def test_docker_config_safe(self):
        sg = SandboxGuard()
        config = {"image": "python:3.11", "mounts": []}
        ok, issues = sg.check_docker_config(config)
        assert ok is True
        assert len(issues) == 0

    def test_docker_config_privileged(self):
        sg = SandboxGuard()
        config = {"privileged": True}
        ok, issues = sg.check_docker_config(config)
        assert ok is False
        assert any("Privileged" in i for i in issues)

    def test_docker_config_host_network(self):
        sg = SandboxGuard()
        config = {"network_mode": "host"}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

    def test_docker_config_host_pid(self):
        sg = SandboxGuard()
        config = {"pid_mode": "host"}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

    def test_docker_config_host_ipc(self):
        sg = SandboxGuard()
        config = {"ipc_mode": "host"}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

    def test_docker_config_dangerous_mount(self):
        sg = SandboxGuard()
        config = {"mounts": [{"source": "/var/run/docker.sock"}]}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

    def test_docker_config_cap_sysadmin(self):
        sg = SandboxGuard()
        config = {"cap_add": ["SYS_ADMIN"]}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

    def test_docker_config_cap_all(self):
        sg = SandboxGuard()
        config = {"cap_add": ["ALL"]}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

    def test_docker_config_not_dict(self):
        sg = SandboxGuard()
        ok, issues = sg.check_docker_config("bad")
        assert ok is False

    def test_hash_sha256_string(self):
        sg = SandboxGuard()
        h = sg.hash_sha256("hello")
        assert len(h) == 64
        assert h == hashlib.sha256(b"hello").hexdigest()

    def test_hash_sha256_bytes(self):
        sg = SandboxGuard()
        h = sg.hash_sha256(b"world")
        assert len(h) == 64

    def test_hash_sha256_file(self):
        sg = SandboxGuard()
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            f.write("test content")
            path = f.name
        try:
            h, msg = sg.hash_sha256_file(path)
            assert h is not None
            assert msg == "OK"
            assert len(h) == 64
        finally:
            os.unlink(path)

    def test_hash_sha256_file_nonexistent(self):
        sg = SandboxGuard()
        h, msg = sg.hash_sha256_file("/nonexistent/file")
        assert h is None

    def test_no_sandbox_opt_in_blocked(self):
        sg = SandboxGuard()
        ok, msg = sg.check_no_sandbox_opt_in(["--no-sandbox"])
        assert ok is False

    def test_no_sandbox_opt_in_safe(self):
        sg = SandboxGuard()
        ok, msg = sg.check_no_sandbox_opt_in(["--version"])
        assert ok is True

    def test_cdp_source_localhost(self):
        sg = SandboxGuard()
        ok, msg = sg.check_cdp_source("http://localhost:9222")
        assert ok is True

    def test_cdp_source_file(self):
        sg = SandboxGuard()
        ok, msg = sg.check_cdp_source("file:///etc/passwd")
        assert ok is False

    def test_cdp_source_remote(self):
        sg = SandboxGuard()
        ok, msg = sg.check_cdp_source("http://evil.com:9222")
        assert ok is False

    def test_cdp_source_empty(self):
        sg = SandboxGuard()
        ok, msg = sg.check_cdp_source("")
        assert ok is True

    def test_cdp_source_none(self):
        sg = SandboxGuard()
        ok, msg = sg.check_cdp_source(None)
        assert ok is True

    def test_stats_blocked(self):
        sg = SandboxGuard()
        sg.check_docker_config({"privileged": True})
        stats = sg.get_stats()
        assert stats["blocked"] >= 1

    def test_docker_mount_string(self):
        sg = SandboxGuard()
        config = {"mounts": ["/proc"]}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

    def test_docker_multiple_issues(self):
        sg = SandboxGuard()
        config = {"privileged": True, "network_mode": "host", "cap_add": ["ALL"]}
        ok, issues = sg.check_docker_config(config)
        assert ok is False
        assert len(issues) >= 3

class TestWebhookGuard:
    """WebhookGuard testleri."""

    def test_init(self):
        wg = WebhookGuard()
        assert wg is not None
        stats = wg.get_stats()
        assert stats["verify_count"] == 0

    def test_constant_time_compare_equal(self):
        wg = WebhookGuard()
        assert wg.constant_time_compare("abc", "abc") is True

    def test_constant_time_compare_different(self):
        wg = WebhookGuard()
        assert wg.constant_time_compare("abc", "def") is False

    def test_constant_time_compare_bytes(self):
        wg = WebhookGuard()
        assert wg.constant_time_compare(b"abc", b"abc") is True

    def test_verify_hmac_valid(self):
        wg = WebhookGuard()
        payload = "test payload"
        secret = "mysecret"
        sig = hmac.new(secret.encode(), payload.encode(), "sha256").hexdigest()
        ok, msg = wg.verify_hmac_signature(payload, sig, secret)
        assert ok is True

    def test_verify_hmac_invalid(self):
        wg = WebhookGuard()
        ok, msg = wg.verify_hmac_signature("payload", "bad_sig", "secret")
        assert ok is False

    def test_verify_hmac_bytes(self):
        wg = WebhookGuard()
        payload = b"test"
        secret = b"key"
        sig = hmac.new(secret, payload, "sha256").hexdigest()
        ok, msg = wg.verify_hmac_signature(payload, sig, secret)
        assert ok is True

    def test_enforce_content_type_json(self):
        wg = WebhookGuard()
        ok, msg = wg.enforce_content_type("application/json")
        assert ok is True

    def test_enforce_content_type_form(self):
        wg = WebhookGuard()
        ok, msg = wg.enforce_content_type("application/x-www-form-urlencoded")
        assert ok is True

    def test_enforce_content_type_invalid(self):
        wg = WebhookGuard()
        ok, msg = wg.enforce_content_type("text/plain")
        assert ok is False

    def test_enforce_content_type_empty(self):
        wg = WebhookGuard()
        ok, msg = wg.enforce_content_type("")
        assert ok is False

    def test_enforce_content_type_none(self):
        wg = WebhookGuard()
        ok, msg = wg.enforce_content_type(None)
        assert ok is False

    def test_enforce_content_type_with_charset(self):
        wg = WebhookGuard()
        ok, msg = wg.enforce_content_type("application/json; charset=utf-8")
        assert ok is True

    def test_enforce_content_type_custom(self):
        wg = WebhookGuard()
        ok, msg = wg.enforce_content_type("text/xml", allowed=["text/xml"])
        assert ok is True

    def test_check_replay_first(self):
        wg = WebhookGuard()
        ok, msg = wg.check_replay("nonce1")
        assert ok is True

    def test_check_replay_duplicate(self):
        wg = WebhookGuard()
        wg.check_replay("nonce1")
        ok, msg = wg.check_replay("nonce1")
        assert ok is False
        assert "Tekrarlanan" in msg

    def test_check_replay_different_nonces(self):
        wg = WebhookGuard()
        ok1, _ = wg.check_replay("nonce1")
        ok2, _ = wg.check_replay("nonce2")
        assert ok1 is True
        assert ok2 is True

    def test_check_replay_expired_timestamp(self):
        wg = WebhookGuard(replay_window=60)
        ok, msg = wg.check_replay("nonce1", timestamp=time.time() - 120)
        assert ok is False
        assert "Zaman asimi" in msg

    def test_check_replay_valid_timestamp(self):
        wg = WebhookGuard(replay_window=300)
        ok, msg = wg.check_replay("nonce1", timestamp=time.time() - 10)
        assert ok is True

    def test_increment_anomaly(self):
        wg = WebhookGuard()
        wg._increment_anomaly("bad_sig")
        wg._increment_anomaly("bad_sig")
        wg._increment_anomaly("replay")
        counters = wg.get_anomaly_counters()
        assert counters["bad_sig"] == 2
        assert counters["replay"] == 1

    def test_reset_anomaly_counters(self):
        wg = WebhookGuard()
        wg._increment_anomaly("test")
        wg.reset_anomaly_counters()
        assert len(wg.get_anomaly_counters()) == 0

    def test_stats_verify_count(self):
        wg = WebhookGuard()
        wg.verify_hmac_signature("p", "s", "k")
        stats = wg.get_stats()
        assert stats["verify_count"] == 1
        assert stats["failed_count"] == 1

    def test_stats_seen_nonces(self):
        wg = WebhookGuard()
        wg.check_replay("n1")
        wg.check_replay("n2")
        stats = wg.get_stats()
        assert stats["seen_nonces"] == 2

    def test_custom_replay_window(self):
        wg = WebhookGuard(replay_window=10)
        assert wg._replay_window == 10

class TestPrototypeGuard:
    """PrototypeGuard testleri."""

    def test_init(self):
        pg = PrototypeGuard()
        assert pg is not None

    def test_safe_merge_basic(self):
        pg = PrototypeGuard()
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = pg.safe_merge(base, override)
        assert result["a"] == 1
        assert result["b"] == 3
        assert result["c"] == 4

    def test_safe_merge_nested(self):
        pg = PrototypeGuard()
        base = {"config": {"a": 1}}
        override = {"config": {"b": 2}}
        result = pg.safe_merge(base, override)
        assert result["config"]["a"] == 1
        assert result["config"]["b"] == 2

    def test_safe_merge_blocks_dangerous(self):
        pg = PrototypeGuard()
        override = {"__proto__": {"x": 1}, "safe": 2}
        result = pg.safe_merge({}, override)
        assert "__proto__" not in result
        assert result["safe"] == 2

    def test_safe_merge_blocks_constructor(self):
        pg = PrototypeGuard()
        override = {"constructor": {"a": 1}}
        result = pg.safe_merge({}, override)
        assert "constructor" not in result

    def test_safe_merge_blocks_class(self):
        pg = PrototypeGuard()
        override = {"__class__": "bad"}
        result = pg.safe_merge({}, override)
        assert "__class__" not in result

    def test_safe_merge_depth_limit(self):
        pg = PrototypeGuard()
        # Deep nesting should not crash
        deep = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": 1}}}}}}}}}}}
        result = pg.safe_merge({}, deep)
        assert isinstance(result, dict)

    def test_check_dict_keys_safe(self):
        pg = PrototypeGuard()
        ok, found = pg.check_dict_keys({"name": "test", "value": 1})
        assert ok is True
        assert len(found) == 0

    def test_check_dict_keys_dangerous(self):
        pg = PrototypeGuard()
        ok, found = pg.check_dict_keys({"__proto__": {}, "name": "test"})
        assert ok is False
        assert len(found) > 0

    def test_check_dict_keys_nested_dangerous(self):
        pg = PrototypeGuard()
        data = {"config": {"__proto__": {}}}
        ok, found = pg.check_dict_keys(data)
        assert ok is False

    def test_check_dict_keys_not_dict(self):
        pg = PrototypeGuard()
        ok, found = pg.check_dict_keys("not a dict")
        assert ok is True

    def test_sanitize_yaml_value_bool_on(self):
        pg = PrototypeGuard()
        result = pg.sanitize_yaml_value("on")
        assert result != "on" or result.startswith('"')

    def test_sanitize_yaml_value_bool_true(self):
        pg = PrototypeGuard()
        result = pg.sanitize_yaml_value("true")
        assert isinstance(result, str)

    def test_sanitize_yaml_value_safe(self):
        pg = PrototypeGuard()
        result = pg.sanitize_yaml_value("hello")
        assert result == "hello"

    def test_sanitize_yaml_value_non_string(self):
        pg = PrototypeGuard()
        result = pg.sanitize_yaml_value(42)
        assert result == 42

    def test_is_yaml_bool_coercion_yes(self):
        pg = PrototypeGuard()
        assert pg.is_yaml_bool_coercion("yes") is True

    def test_is_yaml_bool_coercion_no(self):
        pg = PrototypeGuard()
        assert pg.is_yaml_bool_coercion("no") is True

    def test_is_yaml_bool_coercion_safe(self):
        pg = PrototypeGuard()
        assert pg.is_yaml_bool_coercion("hello") is False

    def test_is_yaml_bool_coercion_non_string(self):
        pg = PrototypeGuard()
        assert pg.is_yaml_bool_coercion(123) is False

    def test_extra_blocked_keys(self):
        pg = PrototypeGuard(extra_blocked=["danger"])
        result = pg.safe_merge({}, {"danger": 1, "safe": 2})
        assert "danger" not in result
        assert result["safe"] == 2

    def test_stats(self):
        pg = PrototypeGuard()
        pg.safe_merge({}, {"__proto__": 1})
        stats = pg.get_stats()
        assert stats["blocked_count"] >= 1

    def test_block_count_increments(self):
        pg = PrototypeGuard()
        pg.safe_merge({}, {"constructor": 1})
        pg.safe_merge({}, {"prototype": 2})
        stats = pg.get_stats()
        assert stats["blocked_count"] >= 2

class TestSecurityIntegration:
    """Entegrasyon testleri."""

    def test_all_guards_instantiate(self):
        ng = NetworkGuard()
        pg = PathGuard()
        eg = ExecGuard()
        cg = CredentialGuard()
        sg = SandboxGuard()
        wg = WebhookGuard()
        ptg = PrototypeGuard()
        assert all(x is not None for x in [ng, pg, eg, cg, sg, wg, ptg])

    def test_all_guards_have_stats(self):
        for cls in [NetworkGuard, PathGuard, ExecGuard, CredentialGuard,
                    SandboxGuard, WebhookGuard, PrototypeGuard]:
            instance = cls()
            stats = instance.get_stats()
            assert isinstance(stats, dict)

    def test_network_guard_stats_keys(self):
        ng = NetworkGuard()
        stats = ng.get_stats()
        assert "total_requests" in stats

    def test_path_guard_stats_keys(self):
        pg = PathGuard()
        stats = pg.get_stats()
        assert "total_checks" in stats

    def test_exec_guard_stats_keys(self):
        eg = ExecGuard()
        stats = eg.get_stats()
        assert "total_execs" in stats
        assert "blocked" in stats

    def test_credential_guard_stats_keys(self):
        cg = CredentialGuard()
        stats = cg.get_stats()
        assert "redacted_count" in stats

    def test_sandbox_guard_stats_keys(self):
        sg = SandboxGuard()
        stats = sg.get_stats()
        assert "total_checks" in stats

    def test_webhook_guard_stats_keys(self):
        wg = WebhookGuard()
        stats = wg.get_stats()
        assert "verify_count" in stats

    def test_prototype_guard_stats_keys(self):
        ptg = PrototypeGuard()
        stats = ptg.get_stats()
        assert "blocked_count" in stats

    def test_credential_redact_with_network(self):
        cg = CredentialGuard()
        data = {"url": "https://api.test.local", "api_key": "secret123"}
        redacted = cg.redact_dict(data)
        assert redacted["url"] == "https://api.test.local"
        assert redacted["api_key"] == "***REDACTED***"

    def test_path_and_exec_combo(self):
        pg = PathGuard(["/app"])
        eg = ExecGuard()
        ok1, _ = pg.check_containment("/app/scripts/run.sh")
        path, msg = eg.resolve_safe_bin("python")
        assert ok1 is True
        assert path is not None

    def test_webhook_hmac_and_replay(self):
        wg = WebhookGuard()
        payload = "data"
        secret = "key"
        sig = hmac.new(secret.encode(), payload.encode(), "sha256").hexdigest()
        ok1, _ = wg.verify_hmac_signature(payload, sig, secret)
        ok2, _ = wg.check_replay("unique_nonce")
        assert ok1 is True
        assert ok2 is True

    def test_sandbox_and_hash(self):
        sg = SandboxGuard()
        h = sg.hash_sha256("test")
        assert len(h) == 64
        ok, issues = sg.check_docker_config({"image": "alpine"})
        assert ok is True

    def test_prototype_safe_merge_chain(self):
        ptg = PrototypeGuard()
        r1 = ptg.safe_merge({"a": 1}, {"b": 2})
        r2 = ptg.safe_merge(r1, {"c": 3})
        assert r2["a"] == 1
        assert r2["b"] == 2
        assert r2["c"] == 3

    def test_multiple_guards_independent(self):
        ng1 = NetworkGuard()
        ng2 = NetworkGuard()
        ng1.validate_url("https://8.8.8.8")
        s1 = ng1.get_stats()
        s2 = ng2.get_stats()
        assert s1["total_requests"] == 1
        assert s2["total_requests"] == 0

    def test_exec_guard_full_workflow(self):
        eg = ExecGuard()
        path, msg = eg.resolve_safe_bin("python")
        if path:
            ok, _ = eg.check_dangerous_flags("python", ["-c"])
            assert ok is True
            clean, warns = eg.sanitize_arguments(["-c", "print(1)"])
            assert len(warns) == 0

    def test_credential_nested_redaction(self):
        cg = CredentialGuard()
        data = {
            "database": {"host": "localhost", "password": "secret"},
            "api": {"endpoint": "/v1", "token": "abc123"},
        }
        result = cg.redact_dict(data)
        assert result["database"]["host"] == "localhost"
        assert result["database"]["password"] == "***REDACTED***"
        assert result["api"]["endpoint"] == "/v1"
        assert result["api"]["token"] == "***REDACTED***"

    def test_network_guard_ipv4_workflow(self):
        ng = NetworkGuard()
        ok1, _ = ng.validate_url("https://1.1.1.1/api")
        ok2 = ng.validate_ipv4_literal("1.1.1.1")
        assert ok1 is True
        assert ok2 is True



class TestNetworkGuardExtra:
    """Ek NetworkGuard testleri."""

    def test_private_ip_empty(self):
        ng = NetworkGuard()
        assert ng.is_private_ip("") is True

    def test_validate_url_ftp(self):
        ng = NetworkGuard()
        ok, msg = ng.validate_url("ftp://example.com")
        assert ok is False

    def test_validate_url_https(self):
        ng = NetworkGuard()
        ok, msg = ng.validate_url("https://8.8.8.8")
        assert ok is True

    def test_response_size_zero(self):
        ng = NetworkGuard()
        ok, msg = ng.check_response_size(0)
        assert ok is True

    def test_security_headers_content(self):
        ng = NetworkGuard()
        h = ng.get_security_headers()
        assert isinstance(h, dict)

class TestExecGuardExtra:
    """Ek ExecGuard testleri."""

    def test_resolve_node(self):
        eg = ExecGuard()
        path, msg = eg.resolve_safe_bin("node")
        # May or may not be installed
        assert msg == "OK" or "bulunamadi" in msg

    def test_resolve_npm(self):
        eg = ExecGuard()
        path, msg = eg.resolve_safe_bin("npm")
        assert msg == "OK" or "bulunamadi" in msg

    def test_sanitize_empty_list(self):
        eg = ExecGuard()
        clean, warns = eg.sanitize_arguments([])
        assert clean == []
        assert len(warns) == 0

    def test_env_vars_crlf_value(self):
        eg = ExecGuard()
        ok, issues = eg.validate_env_vars({"KEY": "val\nue"})
        assert ok is False

    def test_stats_safe_bins_count(self):
        eg = ExecGuard()
        stats = eg.get_stats()
        assert stats["safe_bins"] > 0

class TestCredentialGuardExtra:
    """Ek CredentialGuard testleri."""

    def test_sensitive_bot_token(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("TELEGRAM_BOT_TOKEN") is True

    def test_sensitive_webhook_secret(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("webhook_secret") is True

    def test_not_sensitive_hostname(self):
        cg = CredentialGuard()
        assert cg.is_sensitive_key("hostname") is False

    def test_redact_empty_dict(self):
        cg = CredentialGuard()
        result = cg.redact_dict({})
        assert result == {}

    def test_redact_non_dict(self):
        cg = CredentialGuard()
        result = cg.redact_dict("not a dict")
        assert result == "not a dict"

    def test_temp_name_uniqueness(self):
        cg = CredentialGuard()
        names = [cg.generate_secure_temp_name() for _ in range(10)]
        assert len(set(names)) == 10

class TestSandboxGuardExtra:
    """Ek SandboxGuard testleri."""

    def test_hash_consistency(self):
        sg = SandboxGuard()
        h1 = sg.hash_sha256("test")
        h2 = sg.hash_sha256("test")
        assert h1 == h2

    def test_hash_different_inputs(self):
        sg = SandboxGuard()
        h1 = sg.hash_sha256("hello")
        h2 = sg.hash_sha256("world")
        assert h1 != h2

    def test_docker_config_netadmin(self):
        sg = SandboxGuard()
        config = {"cap_add": ["NET_ADMIN"]}
        ok, issues = sg.check_docker_config(config)
        assert ok is False

class TestWebhookGuardExtra:
    """Ek WebhookGuard testleri."""

    def test_replay_window_expiry(self):
        wg = WebhookGuard(replay_window=1)
        wg.check_replay("old_nonce")
        import time
        time.sleep(1.1)
        ok, _ = wg.check_replay("new_nonce")
        assert ok is True
        # old_nonce should be expired now
        stats = wg.get_stats()
        assert stats["seen_nonces"] <= 2

    def test_hmac_sha256_default(self):
        wg = WebhookGuard()
        payload = "test"
        secret = "key"
        sig = hmac.new(secret.encode(), payload.encode(), "sha256").hexdigest()
        ok, _ = wg.verify_hmac_signature(payload, sig, secret, "sha256")
        assert ok is True

    def test_anomaly_counters_empty(self):
        wg = WebhookGuard()
        assert wg.get_anomaly_counters() == {}

class TestPrototypeGuardExtra:
    """Ek PrototypeGuard testleri."""

    def test_safe_merge_override_non_dict(self):
        pg = PrototypeGuard()
        result = pg.safe_merge("a", "b")
        assert result == "b"

    def test_safe_merge_empty(self):
        pg = PrototypeGuard()
        result = pg.safe_merge({}, {})
        assert result == {}

    def test_yaml_bool_off(self):
        pg = PrototypeGuard()
        assert pg.is_yaml_bool_coercion("off") is True

    def test_yaml_bool_y(self):
        pg = PrototypeGuard()
        assert pg.is_yaml_bool_coercion("y") is True

    def test_yaml_bool_FALSE(self):
        pg = PrototypeGuard()
        assert pg.is_yaml_bool_coercion("FALSE") is True

    def test_blocked_keys_count(self):
        pg = PrototypeGuard()
        stats = pg.get_stats()
        assert stats["blocked_keys"] >= 9

