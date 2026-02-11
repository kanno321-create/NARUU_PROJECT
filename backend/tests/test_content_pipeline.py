"""콘텐츠 파이프라인 AI 테스트 — Claude API mock."""

from __future__ import annotations

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_core.models.content import Content
from naruu_core.plugins.content.pipeline.base import StageHandler, StageResult
from naruu_core.plugins.content.pipeline.script_generator import (
    ScriptGenerator,
    build_prompt,
    calculate_cost,
)
from naruu_core.plugins.content.schemas import ContentCreate
from naruu_core.plugins.content.service import (
    STAGE_HANDLERS,
    ContentCRUD,
)

# ── Claude API Mock 응답 헬퍼 ──

MOCK_CLAUDE_RESPONSE = {
    "id": "msg_mock_001",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": "大邱美容クリニック紹介動画の台本です。\n\nイントロ: 皆さん、こんにちは。",
        }
    ],
    "model": "claude-sonnet-4-5-20250929",
    "stop_reason": "end_turn",
    "usage": {
        "input_tokens": 150,
        "output_tokens": 500,
    },
}

MOCK_CLAUDE_ERROR = {
    "type": "error",
    "error": {
        "type": "authentication_error",
        "message": "invalid x-api-key",
    },
}


# ── Unit 테스트: StageResult ──


@pytest.mark.unit
class TestStageResult:
    """StageResult 데이터클래스 테스트."""

    def test_success_result(self) -> None:
        """성공 결과 생성."""
        result = StageResult(
            success=True,
            next_stage="image",
            data={"script": "test script"},
            cost_usd=0.0081,
        )
        assert result.success is True
        assert result.next_stage == "image"
        assert result.data["script"] == "test script"
        assert result.cost_usd == 0.0081
        assert result.error == ""

    def test_failure_result(self) -> None:
        """실패 결과 생성."""
        result = StageResult(
            success=False,
            next_stage="failed",
            error="API key missing",
        )
        assert result.success is False
        assert result.next_stage == "failed"
        assert result.error == "API key missing"
        assert result.data == {}
        assert result.cost_usd == 0.0

    def test_default_values(self) -> None:
        """기본값 확인."""
        result = StageResult(success=True, next_stage="image")
        assert result.data == {}
        assert result.error == ""
        assert result.cost_usd == 0.0


# ── Unit 테스트: 프롬프트 빌더 ──


@pytest.mark.unit
class TestPromptBuilder:
    """프롬프트 생성 테스트."""

    def _make_content(self, **kwargs: object) -> Content:
        defaults = {
            "title": "テスト",
            "content_type": "video",
            "language": "ja",
            "topic": "大邱美容",
        }
        defaults.update(kwargs)
        return Content(**defaults)

    def test_video_ja_prompt(self) -> None:
        """video + ja 프롬프트."""
        content = self._make_content(content_type="video", language="ja")
        system, user = build_prompt(content)
        assert "動画" in system
        assert "台本" in system
        assert "テーマ:" in user
        assert "大邱美容" in user

    def test_blog_ko_prompt(self) -> None:
        """blog + ko 프롬프트."""
        content = self._make_content(
            content_type="blog", language="ko", topic="대구 관광"
        )
        system, user = build_prompt(content)
        assert "SEO" in system
        assert "블로그" in system
        assert "주제:" in user
        assert "대구 관광" in user

    def test_sns_en_prompt(self) -> None:
        """sns + en 프롬프트."""
        content = self._make_content(
            content_type="sns", language="en", topic="Daegu Beauty"
        )
        system, user = build_prompt(content)
        assert "SNS" in system
        assert "hashtags" in system
        assert "Topic:" in user

    def test_fallback_to_default(self) -> None:
        """알 수 없는 content_type → video 폴백."""
        content = self._make_content(content_type="unknown", language="xx")
        system, user = build_prompt(content)
        assert "動画" in system  # video ja 기본값

    def test_empty_topic_uses_title(self) -> None:
        """topic이 비어있으면 title 사용."""
        content = self._make_content(topic="", title="大邱旅行ガイド")
        _, user = build_prompt(content)
        assert "大邱旅行ガイド" in user


# ── Unit 테스트: 비용 계산 ──


@pytest.mark.unit
class TestCostCalculation:
    """API 비용 계산 테스트."""

    def test_zero_tokens(self) -> None:
        """토큰 0 → 비용 0."""
        assert calculate_cost(0, 0) == 0.0

    def test_known_cost(self) -> None:
        """알려진 토큰 수 → 정확한 비용."""
        # 150 input + 500 output
        # 150 * 3/1M + 500 * 15/1M = 0.00045 + 0.0075 = 0.00795
        cost = calculate_cost(150, 500)
        assert abs(cost - 0.00795) < 0.00001

    def test_large_tokens(self) -> None:
        """대량 토큰 비용."""
        cost = calculate_cost(10000, 4096)
        assert cost > 0
        # 10000 * 3/1M + 4096 * 15/1M = 0.03 + 0.06144 = 0.09144
        assert abs(cost - 0.09144) < 0.00001


# ── Unit 테스트: STAGE_HANDLERS 맵 ──


@pytest.mark.unit
class TestStageHandlersMap:
    """STAGE_HANDLERS 맵 검증."""

    def test_script_has_handler(self) -> None:
        """script 단계에 ScriptGenerator 등록."""
        assert STAGE_HANDLERS["script"] is ScriptGenerator

    def test_other_stages_none(self) -> None:
        """image/voice/video/publish는 아직 None."""
        for stage in ("image", "voice", "video", "publish"):
            assert STAGE_HANDLERS[stage] is None

    def test_pending_not_in_handlers(self) -> None:
        """pending 단계는 핸들러 없음 (단순 진행)."""
        assert "pending" not in STAGE_HANDLERS

    def test_script_generator_is_stage_handler(self) -> None:
        """ScriptGenerator가 StageHandler ABC 구현."""
        assert issubclass(ScriptGenerator, StageHandler)

    def test_script_generator_stage_name(self) -> None:
        """ScriptGenerator stage_name = 'script'."""
        gen = ScriptGenerator()
        assert gen.stage_name == "script"


# ── Integration 테스트: ScriptGenerator + Claude API Mock ──


@pytest.mark.integration
class TestScriptGeneratorWithMock:
    """ScriptGenerator Claude API mock 테스트."""

    def _make_content(self, **kwargs: object) -> Content:
        defaults = {
            "title": "テスト動画",
            "content_type": "video",
            "language": "ja",
            "topic": "大邱美容クリニック紹介",
            "pipeline_stage": "script",
        }
        defaults.update(kwargs)
        return Content(**defaults)

    @respx.mock
    async def test_successful_generation(self) -> None:
        """성공적인 스크립트 생성."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=MOCK_CLAUDE_RESPONSE)
        )

        gen = ScriptGenerator()
        content = self._make_content()
        result = await gen.execute(content, {"anthropic_api_key": "sk-test-key"})

        assert result.success is True
        assert result.next_stage == "image"
        assert "大邱美容クリニック" in result.data["script"]
        assert result.data["input_tokens"] == 150
        assert result.data["output_tokens"] == 500
        assert result.cost_usd > 0

    @respx.mock
    async def test_api_error_401(self) -> None:
        """API 인증 오류 → failed."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(401, json=MOCK_CLAUDE_ERROR)
        )

        gen = ScriptGenerator()
        content = self._make_content()
        result = await gen.execute(content, {"anthropic_api_key": "bad-key"})

        assert result.success is False
        assert result.next_stage == "failed"
        assert "401" in result.error

    async def test_missing_api_key(self) -> None:
        """API 키 없음 → failed."""
        gen = ScriptGenerator()
        content = self._make_content()
        result = await gen.execute(content, {})

        assert result.success is False
        assert result.next_stage == "failed"
        assert "anthropic_api_key" in result.error

    @respx.mock
    async def test_network_error(self) -> None:
        """네트워크 오류 → failed."""
        import httpx as _httpx

        respx.post("https://api.anthropic.com/v1/messages").mock(
            side_effect=_httpx.ConnectError("connection refused")
        )

        gen = ScriptGenerator()
        content = self._make_content()
        result = await gen.execute(content, {"anthropic_api_key": "sk-test-key"})

        assert result.success is False
        assert result.next_stage == "failed"
        assert "오류" in result.error

    @respx.mock
    async def test_custom_model_config(self) -> None:
        """커스텀 모델 설정 전달."""
        route = respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=MOCK_CLAUDE_RESPONSE)
        )

        gen = ScriptGenerator()
        content = self._make_content()
        config = {
            "anthropic_api_key": "sk-test-key",
            "ai_model": "claude-opus-4-6",
            "ai_max_tokens": 4096,
            "ai_script_temperature": 0.5,
        }
        await gen.execute(content, config)

        request = route.calls[0].request
        import json

        body = json.loads(request.content)
        assert body["model"] == "claude-opus-4-6"
        assert body["max_tokens"] == 4096
        assert body["temperature"] == 0.5

    @respx.mock
    async def test_blog_ko_generation(self) -> None:
        """블로그 한국어 스크립트 생성."""
        ko_response = {
            **MOCK_CLAUDE_RESPONSE,
            "content": [
                {"type": "text", "text": "대구 관광 블로그 글입니다."},
            ],
        }
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=ko_response)
        )

        gen = ScriptGenerator()
        content = self._make_content(content_type="blog", language="ko")
        result = await gen.execute(content, {"anthropic_api_key": "sk-test-key"})

        assert result.success is True
        assert "대구 관광" in result.data["script"]


# ── Integration 테스트: advance_pipeline with AI ──


@pytest.mark.integration
class TestAdvancePipelineAI:
    """advance_pipeline AI 핸들러 연동 테스트."""

    @respx.mock
    async def test_pending_to_script_ai(
        self, db_session: AsyncSession,
    ) -> None:
        """pending → script 단계에서 AI 핸들러 트리거.

        pending에는 핸들러가 없으므로 단순 진행 → script.
        script에는 ScriptGenerator 핸들러가 있으므로 Claude API 호출.
        """
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=MOCK_CLAUDE_RESPONSE)
        )

        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(
                title="AI Test Video",
                content_type="video",
                language="ja",
                topic="大邱美容",
            )
        )
        assert content.pipeline_stage == "pending"

        # pending → script (단순 진행)
        content = await crud.advance_pipeline(content.id)
        assert content is not None
        assert content.pipeline_stage == "script"

        # script → image (AI 핸들러 실행)
        config = {"anthropic_api_key": "sk-test-key"}
        content = await crud.advance_pipeline(content.id, config=config)
        assert content is not None
        assert content.pipeline_stage == "image"
        assert content.script != ""
        assert content.cost_usd > 0

    @respx.mock
    async def test_ai_failure_sets_failed(
        self, db_session: AsyncSession,
    ) -> None:
        """AI 호출 실패 → pipeline_stage = 'failed'."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(500, json={"error": "server error"})
        )

        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(title="Fail Test", topic="test")
        )
        # pending → script
        await crud.advance_pipeline(content.id)

        # script → AI 실패 → failed
        config = {"anthropic_api_key": "sk-test-key"}
        content = await crud.advance_pipeline(content.id, config=config)
        assert content is not None
        assert content.pipeline_stage == "failed"
        assert content.error_message != ""

    async def test_no_api_key_sets_failed(
        self, db_session: AsyncSession,
    ) -> None:
        """API 키 없이 script 단계 → failed."""
        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(title="No Key Test", topic="test")
        )
        await crud.advance_pipeline(content.id)  # pending → script

        content = await crud.advance_pipeline(content.id, config={})
        assert content is not None
        assert content.pipeline_stage == "failed"
        assert "anthropic_api_key" in content.error_message

    @respx.mock
    async def test_cost_accumulates(
        self, db_session: AsyncSession,
    ) -> None:
        """AI 호출 비용이 content.cost_usd에 누적."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=MOCK_CLAUDE_RESPONSE)
        )

        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(title="Cost Test", topic="test")
        )
        assert content.cost_usd == 0.0

        await crud.advance_pipeline(content.id)  # pending → script
        config = {"anthropic_api_key": "sk-test-key"}
        content = await crud.advance_pipeline(content.id, config=config)
        assert content is not None
        assert content.cost_usd > 0

    async def test_non_ai_stages_simple_advance(
        self, db_session: AsyncSession,
    ) -> None:
        """AI 핸들러 없는 단계는 단순 진행 (기존 동작 유지)."""
        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(title="Simple Test", topic="test")
        )
        # pending → script (pending에 핸들러 없음)
        content = await crud.advance_pipeline(content.id)
        assert content is not None
        assert content.pipeline_stage == "script"

    async def test_done_no_advance(
        self, db_session: AsyncSession,
    ) -> None:
        """done 단계에서는 더 이상 진행 안 함."""
        crud = ContentCRUD(db_session)
        content = await crud.create_content(
            ContentCreate(title="Done Test", topic="test")
        )
        # 수동으로 done 설정
        content.pipeline_stage = "done"
        await db_session.commit()
        await db_session.refresh(content)

        result = await crud.advance_pipeline(content.id)
        assert result is not None
        assert result.pipeline_stage == "done"


# ── Unit 테스트: Content Plugin execute() ──


@pytest.mark.unit
class TestContentPluginExecute:
    """Content Plugin execute() 실구현 테스트."""

    async def test_advance_pipeline_returns_config(self) -> None:
        """advance_pipeline 명령 → config 포함 응답."""
        from naruu_core.plugins.content.plugin import Plugin

        plugin = Plugin()
        await plugin.initialize({
            "anthropic_api_key": "sk-test",
            "ai_model": "claude-opus-4-6",
        })

        result = await plugin.execute("content.advance_pipeline", {})
        assert result["status"] == "ok"
        assert "config" in result
        assert result["config"]["anthropic_api_key"] == "sk-test"
        assert result["config"]["ai_model"] == "claude-opus-4-6"

    async def test_other_command_generic(self) -> None:
        """다른 명령 → 기존 응답."""
        from naruu_core.plugins.content.plugin import Plugin

        plugin = Plugin()
        await plugin.initialize({})
        result = await plugin.execute("content.create", {"title": "test"})
        assert result["status"] == "ok"
        assert "config" not in result

    async def test_plugin_version_updated(self) -> None:
        """플러그인 버전 0.2.0."""
        from naruu_core.plugins.content.plugin import Plugin

        plugin = Plugin()
        assert plugin.version == "0.2.0"


# ── E2E 테스트: 전체 파이프라인 ──


@pytest.mark.integration
class TestPipelineE2E:
    """전체 파이프라인 E2E 테스트."""

    @respx.mock
    async def test_full_pipeline_script_stage(
        self, db_session: AsyncSession,
    ) -> None:
        """create → pending → script(AI) → image → ... 전체 흐름."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=MOCK_CLAUDE_RESPONSE)
        )

        crud = ContentCRUD(db_session)
        config = {"anthropic_api_key": "sk-test-key"}

        # 1. 콘텐츠 생성
        content = await crud.create_content(
            ContentCreate(
                title="E2E Test: 大邱美容",
                content_type="video",
                language="ja",
                topic="大邱の美容クリニック完全ガイド",
            )
        )
        assert content.pipeline_stage == "pending"
        assert content.script == ""
        assert content.cost_usd == 0.0

        # 2. pending → script (단순 진행)
        content = await crud.advance_pipeline(content.id)
        assert content is not None
        assert content.pipeline_stage == "script"

        # 3. script → image (AI 핸들러: Claude API 호출)
        content = await crud.advance_pipeline(content.id, config=config)
        assert content is not None
        assert content.pipeline_stage == "image"
        assert content.script != ""
        assert "大邱美容クリニック" in content.script
        assert content.cost_usd > 0

        # 4. image → voice (핸들러 없음: 단순 진행)
        content = await crud.advance_pipeline(content.id)
        assert content is not None
        assert content.pipeline_stage == "voice"

        # 5. 나머지 단계도 단순 진행
        for expected_stage in ("video", "publish", "done"):
            content = await crud.advance_pipeline(content.id)
            assert content is not None
            assert content.pipeline_stage == expected_stage

        # 6. done 이후 → 변화 없음
        content = await crud.advance_pipeline(content.id)
        assert content is not None
        assert content.pipeline_stage == "done"

        # 7. 비용 유지
        assert content.cost_usd > 0
