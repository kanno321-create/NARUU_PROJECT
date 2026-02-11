"""스크립트 생성 단계 — Claude API로 콘텐츠 스크립트 생성."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from naruu_core.models.content import Content
from naruu_core.plugins.content.pipeline.base import StageHandler, StageResult

logger = logging.getLogger(__name__)

# 토큰당 비용 (USD) — Claude Sonnet 4.5 기준
INPUT_COST_PER_TOKEN = 3.0 / 1_000_000   # $3/MTok
OUTPUT_COST_PER_TOKEN = 15.0 / 1_000_000  # $15/MTok

SYSTEM_PROMPTS: dict[str, dict[str, str]] = {
    "video": {
        "ja": (
            "あなたはNARUUプラットフォームの動画ナレーション脚本家です。\n"
            "大邱の医療美容・観光情報を日本人向けに紹介する動画の台本を作成してください。\n"
            "自然な日本語で、視聴者の興味を引く構成にしてください。\n"
            "台本にはイントロ・本文・まとめを含めてください。"
        ),
        "ko": (
            "당신은 NARUU 플랫폼의 영상 나레이션 작가입니다.\n"
            "대구의 의료미용·관광 정보를 소개하는 영상 대본을 작성해주세요.\n"
            "자연스러운 한국어로, 시청자의 관심을 끄는 구성으로 만들어주세요.\n"
            "대본에는 인트로·본문·마무리를 포함해주세요."
        ),
        "en": (
            "You are a video narration scriptwriter for the NARUU platform.\n"
            "Create a script introducing Daegu's medical beauty and tourism to viewers.\n"
            "Use engaging language with a clear intro, body, and conclusion."
        ),
    },
    "blog": {
        "ja": (
            "あなたはNARUUプラットフォームのSEOブログライターです。\n"
            "大邱の医療美容・観光に関するSEO最適化されたブログ記事を日本語で作成してください。\n"
            "見出し(H2, H3)を使い、読みやすい構成にしてください。"
        ),
        "ko": (
            "당신은 NARUU 플랫폼의 SEO 블로그 작가입니다.\n"
            "대구의 의료미용·관광에 대한 SEO 최적화된 블로그 글을 한국어로 작성해주세요.\n"
            "소제목(H2, H3)을 사용하여 읽기 쉬운 구성으로 만들어주세요."
        ),
        "en": (
            "You are an SEO blog writer for the NARUU platform.\n"
            "Create an SEO-optimized blog post about Daegu's medical beauty and tourism.\n"
            "Use headings (H2, H3) for readability."
        ),
    },
    "sns": {
        "ja": (
            "あなたはNARUUプラットフォームのSNSコンテンツクリエーターです。\n"
            "大邱の医療美容・観光を紹介する短いSNS投稿を日本語で作成してください。\n"
            "ハッシュタグを含め、魅力的でシェアしたくなる内容にしてください。"
        ),
        "ko": (
            "당신은 NARUU 플랫폼의 SNS 콘텐츠 크리에이터입니다.\n"
            "대구의 의료미용·관광을 소개하는 짧은 SNS 포스트를 한국어로 작성해주세요.\n"
            "해시태그를 포함하고, 매력적이고 공유하고 싶은 내용으로 만들어주세요."
        ),
        "en": (
            "You are an SNS content creator for the NARUU platform.\n"
            "Create a short SNS post about Daegu's medical beauty and tourism.\n"
            "Include hashtags and make it engaging and shareable."
        ),
    },
}


def build_prompt(content: Content) -> tuple[str, str]:
    """content_type + language에 맞는 시스템 프롬프트 + 유저 메시지 구성.

    Returns:
        (system_prompt, user_message)
    """
    ct = content.content_type if content.content_type in SYSTEM_PROMPTS else "video"
    lang = content.language if content.language in SYSTEM_PROMPTS[ct] else "ja"
    system_prompt = SYSTEM_PROMPTS[ct][lang]

    topic = content.topic or content.title
    user_message = f"テーマ: {topic}" if lang == "ja" else (
        f"주제: {topic}" if lang == "ko" else f"Topic: {topic}"
    )
    return system_prompt, user_message


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """API 호출 비용 계산 (USD)."""
    return round(
        input_tokens * INPUT_COST_PER_TOKEN + output_tokens * OUTPUT_COST_PER_TOKEN,
        6,
    )


class ScriptGenerator(StageHandler):
    """Claude API로 콘텐츠 스크립트 생성.

    content_type별 프롬프트:
    - video: 나레이션 대본 (일본어/한국어/영어)
    - blog: SEO 최적화 블로그 글
    - sns: 짧은 SNS 포스트
    """

    @property
    def stage_name(self) -> str:
        return "script"

    async def execute(self, content: Content, config: dict[str, Any]) -> StageResult:
        """Claude API로 스크립트 생성.

        config 키:
        - anthropic_api_key: Anthropic API 키 (필수)
        - ai_model: 모델명 (기본: claude-sonnet-4-5-20250929)
        - ai_max_tokens: 최대 토큰 (기본: 2048)
        - ai_script_temperature: 온도 (기본: 0.7)
        """
        api_key = config.get("anthropic_api_key", "")
        if not api_key:
            return StageResult(
                success=False,
                next_stage="failed",
                error="anthropic_api_key가 설정되지 않았습니다.",
            )

        model = config.get("ai_model", "claude-sonnet-4-5-20250929")
        max_tokens = config.get("ai_max_tokens", 2048)
        temperature = config.get("ai_script_temperature", 0.7)

        system_prompt, user_message = build_prompt(content)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
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
                        "temperature": temperature,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_message},
                        ],
                    },
                )
                response.raise_for_status()

            data = response.json()
            script_text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    script_text += block["text"]

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cost = calculate_cost(input_tokens, output_tokens)

            logger.info(
                "스크립트 생성 완료: content=%s, tokens=%d+%d, cost=$%.4f",
                content.id,
                input_tokens,
                output_tokens,
                cost,
            )

            return StageResult(
                success=True,
                next_stage="image",
                data={
                    "script": script_text,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model": model,
                },
                cost_usd=cost,
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"Claude API 오류: {e.response.status_code}"
            logger.error("스크립트 생성 실패: %s", error_msg)
            return StageResult(
                success=False,
                next_stage="failed",
                error=error_msg,
            )
        except httpx.RequestError as e:
            error_msg = f"네트워크 오류: {e}"
            logger.error("스크립트 생성 실패: %s", error_msg)
            return StageResult(
                success=False,
                next_stage="failed",
                error=error_msg,
            )
