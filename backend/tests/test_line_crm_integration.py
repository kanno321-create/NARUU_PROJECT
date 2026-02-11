"""LINE → CRM 통합 + AI 응답 테스트."""

from __future__ import annotations

import pytest
import respx
from httpx import Response
from sqlalchemy.ext.asyncio import AsyncSession

from naruu_core.plugins.crm.ai_responder import (
    CustomerAIResponder,
    build_responder_prompt,
    calculate_response_cost,
)
from naruu_core.plugins.crm.plugin import Plugin as CrmPlugin
from naruu_core.plugins.crm.schemas import CustomerCreate, InteractionCreate
from naruu_core.plugins.crm.service import CrmCRUD

# ── Mock 응답 ──

MOCK_AI_RESPONSE = {
    "content": [
        {
            "type": "text",
            "text": "NARUUへようこそ！大邱の美容クリニックについてご案内いたします。",
        }
    ],
    "usage": {"input_tokens": 80, "output_tokens": 50},
}


# ── Unit 테스트: AI 프롬프트 빌더 ──


@pytest.mark.unit
class TestResponderPrompt:
    """AI 응답 프롬프트 빌더 테스트."""

    def test_ja_prompt(self) -> None:
        """일본어 프롬프트."""
        system, user = build_responder_prompt(
            "整形の料金は？", "ja", "田中様",
        )
        assert "コンシェルジュ" in system
        assert "大邱" in system
        assert "田中様" in user
        assert "整形の料金は？" in user

    def test_ko_prompt(self) -> None:
        """한국어 프롬프트."""
        system, user = build_responder_prompt(
            "성형 비용 문의", "ko", "홍길동",
        )
        assert "컨시어지" in system
        assert "홍길동" in user

    def test_en_prompt(self) -> None:
        """영어 프롬프트."""
        system, user = build_responder_prompt(
            "How much?", "en", "John",
        )
        assert "concierge" in system
        assert "John" in user

    def test_unknown_lang_fallback(self) -> None:
        """알 수 없는 언어 → ja 폴백."""
        system, _ = build_responder_prompt("test", "zh", "Test")
        assert "コンシェルジュ" in system  # ja 기본값


# ── Unit 테스트: 비용 계산 ──


@pytest.mark.unit
class TestResponseCost:
    """응답 비용 계산 테스트."""

    def test_zero_cost(self) -> None:
        assert calculate_response_cost(0, 0) == 0.0

    def test_known_cost(self) -> None:
        # 80 * 3/1M + 50 * 15/1M = 0.00024 + 0.00075 = 0.00099
        cost = calculate_response_cost(80, 50)
        assert abs(cost - 0.00099) < 0.00001


# ── Unit 테스트: AI Responder ──


@pytest.mark.unit
class TestCustomerAIResponder:
    """CustomerAIResponder 테스트."""

    async def test_no_api_key_fallback(self) -> None:
        """API 키 없음 → 폴백 응답."""
        responder = CustomerAIResponder()
        reply, cost = await responder.generate_response(
            customer_message="テスト",
            language="ja",
            customer_name="テスト様",
            config={},
        )
        assert "NARUU" in reply
        assert "メッセージ" in reply
        assert cost == 0.0

    async def test_fallback_ko(self) -> None:
        """한국어 폴백 응답."""
        responder = CustomerAIResponder()
        reply, cost = await responder.generate_response(
            customer_message="테스트",
            language="ko",
            customer_name="테스트",
            config={},
        )
        assert "NARUU" in reply
        assert "환영" in reply
        assert cost == 0.0

    @respx.mock
    async def test_successful_ai_response(self) -> None:
        """Claude API 성공 → AI 응답."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=MOCK_AI_RESPONSE),
        )
        responder = CustomerAIResponder()
        reply, cost = await responder.generate_response(
            customer_message="整形の料金は？",
            language="ja",
            customer_name="田中様",
            config={"anthropic_api_key": "sk-test"},
        )
        assert "NARUU" in reply
        assert cost > 0

    @respx.mock
    async def test_api_error_fallback(self) -> None:
        """API 오류 시 폴백."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(500, json={"error": "server error"}),
        )
        responder = CustomerAIResponder()
        reply, cost = await responder.generate_response(
            customer_message="test",
            language="en",
            customer_name="Test",
            config={"anthropic_api_key": "sk-test"},
        )
        assert "Welcome to NARUU" in reply
        assert cost == 0.0


# ── Unit 테스트: CRM Plugin ──


@pytest.mark.unit
class TestCrmPlugin:
    """CRM Plugin execute() 테스트."""

    def test_plugin_version_updated(self) -> None:
        plugin = CrmPlugin()
        assert plugin.version == "0.2.0"

    def test_has_ai_respond_capability(self) -> None:
        plugin = CrmPlugin()
        caps = plugin.capabilities()
        assert "line.ai_respond" in caps
        assert len(caps) == 12

    async def test_ai_respond_no_key(self) -> None:
        """line.ai_respond 키 없음 → 폴백."""
        plugin = CrmPlugin()
        await plugin.initialize({})
        result = await plugin.execute(
            "line.ai_respond",
            {"message": "テスト", "language": "ja"},
        )
        assert result["status"] == "ok"
        assert "reply" in result
        assert result["cost_usd"] == 0.0

    @respx.mock
    async def test_ai_respond_with_key(self) -> None:
        """line.ai_respond API 키 있음 → AI 응답."""
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=Response(200, json=MOCK_AI_RESPONSE),
        )
        plugin = CrmPlugin()
        await plugin.initialize({"anthropic_api_key": "sk-test"})
        result = await plugin.execute(
            "line.ai_respond",
            {"message": "整形の料金は？"},
        )
        assert result["status"] == "ok"
        assert result["cost_usd"] > 0

    async def test_other_command(self) -> None:
        """일반 명령 → 기존 응답."""
        plugin = CrmPlugin()
        await plugin.initialize({})
        result = await plugin.execute("customer.create", {})
        assert result["status"] == "ok"
        assert "reply" not in result


# ── Integration 테스트: LINE → CRM ──


@pytest.mark.integration
class TestLineCrmIntegration:
    """LINE → CRM 통합 테스트 (DB 연동)."""

    async def test_customer_create_from_line(
        self, db_session: AsyncSession,
    ) -> None:
        """LINE user_id로 고객 생성."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(
                line_user_id="U1234567890abcdef",
                display_name="LINE:U1234567",
            )
        )
        assert customer.line_user_id == "U1234567890abcdef"
        assert customer.display_name == "LINE:U1234567"

    async def test_customer_lookup_by_line_id(
        self, db_session: AsyncSession,
    ) -> None:
        """LINE user_id로 고객 조회."""
        crud = CrmCRUD(db_session)
        await crud.create_customer(
            CustomerCreate(
                line_user_id="Ufind_test",
                display_name="FindMe",
            )
        )
        found = await crud.get_customer_by_line_id("Ufind_test")
        assert found is not None
        assert found.display_name == "FindMe"

    async def test_customer_reuse_existing(
        self, db_session: AsyncSession,
    ) -> None:
        """기존 고객 재사용 (중복 생성 방지)."""
        crud = CrmCRUD(db_session)
        c1 = await crud.create_customer(
            CustomerCreate(
                line_user_id="Ureuse",
                display_name="First",
            )
        )
        existing = await crud.get_customer_by_line_id("Ureuse")
        assert existing is not None
        assert existing.id == c1.id

    async def test_interaction_record_inbound(
        self, db_session: AsyncSession,
    ) -> None:
        """Inbound Interaction 기록."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(
                line_user_id="Uinbound",
                display_name="InboundTest",
            )
        )
        interaction = await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="line",
                direction="inbound",
                content="整形の料金は？",
            )
        )
        assert interaction.channel == "line"
        assert interaction.direction == "inbound"
        assert interaction.content == "整形の料金は？"

    async def test_interaction_record_outbound(
        self, db_session: AsyncSession,
    ) -> None:
        """Outbound Interaction 기록."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(
                line_user_id="Uoutbound",
                display_name="OutboundTest",
            )
        )
        interaction = await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="line",
                direction="outbound",
                content="NARUUへようこそ！",
            )
        )
        assert interaction.direction == "outbound"

    async def test_interaction_pair(
        self, db_session: AsyncSession,
    ) -> None:
        """Inbound + Outbound 쌍 기록."""
        crud = CrmCRUD(db_session)
        customer = await crud.create_customer(
            CustomerCreate(
                line_user_id="Upair",
                display_name="PairTest",
            )
        )
        # Inbound
        await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="line",
                direction="inbound",
                content="質問です",
            )
        )
        # Outbound
        await crud.create_interaction(
            InteractionCreate(
                customer_id=customer.id,
                channel="line",
                direction="outbound",
                content="回答です",
            )
        )
        interactions = await crud.list_interactions(customer.id)
        assert len(interactions) == 2
        directions = {i.direction for i in interactions}
        assert directions == {"inbound", "outbound"}
