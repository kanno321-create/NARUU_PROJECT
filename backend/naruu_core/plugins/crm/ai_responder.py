"""고객 AI 응답 생성기 — Claude API로 고객 문의에 응답."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# 토큰당 비용 (USD) — Claude Sonnet 4.5 기준
INPUT_COST_PER_TOKEN = 3.0 / 1_000_000
OUTPUT_COST_PER_TOKEN = 15.0 / 1_000_000

SYSTEM_PROMPTS: dict[str, str] = {
    "ja": (
        "あなたはNARUUプラットフォームのAIコンシェルジュです。\n"
        "大邱（テグ）の医療美容・整形・観光サービスを日本人のお客様にご案内します。\n"
        "丁寧で親切な日本語でお答えください。\n"
        "具体的なクリニック名や価格は「スタッフに確認後ご案内いたします」と伝えてください。\n"
        "回答は200文字以内で簡潔にお願いします。"
    ),
    "ko": (
        "당신은 NARUU 플랫폼의 AI 컨시어지입니다.\n"
        "대구의 의료미용·성형·관광 서비스를 고객님께 안내합니다.\n"
        "친절하고 정중한 한국어로 답변해주세요.\n"
        "구체적인 클리닉명이나 가격은 '스태프 확인 후 안내드리겠습니다'라고 전해주세요.\n"
        "답변은 200자 이내로 간결하게 해주세요."
    ),
    "en": (
        "You are the AI concierge for the NARUU platform.\n"
        "You help customers with medical beauty, cosmetic surgery, "
        "and tourism services in Daegu, South Korea.\n"
        "Be polite and helpful. For specific clinic names or prices, "
        "say 'Our staff will follow up with details.'\n"
        "Keep responses under 200 characters."
    ),
}


def build_responder_prompt(
    customer_message: str,
    language: str,
    customer_name: str,
) -> tuple[str, str]:
    """고객 응답용 시스템 프롬프트 + 유저 메시지 구성.

    Returns:
        (system_prompt, user_message)
    """
    lang = language if language in SYSTEM_PROMPTS else "ja"
    system_prompt = SYSTEM_PROMPTS[lang]

    if lang == "ja":
        user_msg = f"お客様「{customer_name}」からのメッセージ: {customer_message}"
    elif lang == "ko":
        user_msg = f"고객 '{customer_name}'님의 메시지: {customer_message}"
    else:
        user_msg = f"Message from customer '{customer_name}': {customer_message}"

    return system_prompt, user_msg


def calculate_response_cost(input_tokens: int, output_tokens: int) -> float:
    """API 호출 비용 계산 (USD)."""
    return round(
        input_tokens * INPUT_COST_PER_TOKEN + output_tokens * OUTPUT_COST_PER_TOKEN,
        6,
    )


class CustomerAIResponder:
    """Claude API로 고객 문의에 응답 생성.

    시스템 프롬프트: NARUU 플랫폼 컨시어지 역할.
    고객의 언어(ja/ko/en)에 맞춰 응답.
    의료관광/뷰티/관광 질문에 전문적 답변.
    """

    async def generate_response(
        self,
        customer_message: str,
        language: str,
        customer_name: str,
        config: dict[str, Any],
    ) -> tuple[str, float]:
        """고객 문의에 대한 AI 응답 생성.

        Args:
            customer_message: 고객이 보낸 메시지.
            language: 고객 언어 (ja/ko/en).
            customer_name: 고객 이름.
            config: API 설정 (anthropic_api_key, ai_model 등).

        Returns:
            (응답 텍스트, API 비용 USD).
            API 키 없거나 오류 시 (폴백 메시지, 0.0).
        """
        api_key = config.get("anthropic_api_key", "")
        if not api_key:
            return self._fallback_response(language), 0.0

        model = config.get("ai_model", "claude-sonnet-4-5-20250929")
        max_tokens = config.get("ai_max_tokens", 512)

        system_prompt, user_message = build_responder_prompt(
            customer_message, language, customer_name,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "temperature": 0.5,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_message},
                        ],
                    },
                )
                response.raise_for_status()

            data = response.json()
            reply_text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    reply_text += block["text"]

            usage = data.get("usage", {})
            cost = calculate_response_cost(
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
            )

            logger.info(
                "AI 고객 응답 생성: lang=%s, cost=$%.4f",
                language,
                cost,
            )
            return reply_text, cost

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("AI 응답 생성 실패: %s", e)
            return self._fallback_response(language), 0.0

    @staticmethod
    def _fallback_response(language: str) -> str:
        """AI 불가 시 폴백 응답."""
        fallbacks = {
            "ja": (
                "NARUUへようこそ！\n"
                "メッセージを受け取りました。\n"
                "スタッフが確認後、ご連絡いたします。"
            ),
            "ko": (
                "NARUU에 오신 것을 환영합니다!\n"
                "메시지를 받았습니다.\n"
                "스태프 확인 후 연락드리겠습니다."
            ),
            "en": (
                "Welcome to NARUU!\n"
                "We received your message.\n"
                "Our staff will get back to you shortly."
            ),
        }
        return fallbacks.get(language, fallbacks["ja"])
