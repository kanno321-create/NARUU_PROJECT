"""Claude AI service wrapper for chatbot, translation, and content generation."""

from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Module-level shared httpx client for connection pooling
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Return a shared httpx.AsyncClient, creating it on first use."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


async def close_ai_http_client() -> None:
    """Close the shared httpx client. Call on app shutdown."""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


class AIService:
    """Handles Claude API interactions."""

    def __init__(self):
        self.api_key = settings.CLAUDE_API_KEY
        self.model = settings.CLAUDE_MODEL

    @property
    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    async def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        max_tokens: int = 1024,
    ) -> Optional[str]:
        """Send a single message to Claude (no history)."""
        return await self.chat_multi(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

    async def chat_multi(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int = 1024,
    ) -> Optional[str]:
        """Send full conversation history to Claude for multi-turn continuity.

        messages: list of {"role": "user"|"assistant", "content": "..."}
        """
        if not self.api_key:
            return None

        # Claude API requires alternating user/assistant, strip extra fields
        api_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                api_messages.append({"role": role, "content": content})

        if not api_messages:
            return None

        # Ensure conversation starts with user (Claude requirement)
        if api_messages[0]["role"] != "user":
            api_messages = api_messages[1:]

        # Ensure alternating roles — merge consecutive same-role messages
        cleaned: list[dict] = []
        for msg in api_messages:
            if cleaned and cleaned[-1]["role"] == msg["role"]:
                cleaned[-1]["content"] += "\n" + msg["content"]
            else:
                cleaned.append(dict(msg))

        if not cleaned:
            return None

        body: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": cleaned,
        }
        if system_prompt:
            body["system"] = system_prompt

        client = _get_http_client()
        resp = await client.post(
            CLAUDE_API_URL,
            headers=self._headers,
            json=body,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"]
        return None

    async def translate(
        self,
        text: str,
        source_lang: str = "ja",
        target_lang: str = "ko",
    ) -> Optional[str]:
        """Translate text between languages."""
        system = (
            f"You are a professional translator specializing in medical tourism "
            f"and beauty industry terminology. Translate from {source_lang} to {target_lang}. "
            f"Output only the translation, no explanations."
        )
        return await self.chat(text, system_prompt=system)

    async def generate_line_reply(
        self,
        user_message: str,
        context: str = "",
        history: list[dict] | None = None,
    ) -> Optional[str]:
        """Generate a Japanese reply for LINE chatbot with conversation history."""
        system = (
            "あなたはNARUU（ナル）の日本語カスタマーサポートAIです。"
            "大邱の美容観光・医療観光・観光案内を担当しています。"
            "親切で丁寧な日本語で回答してください。"
            "医療効果の保証や誇大広告は絶対にしないでください。"
            "具体的な医療行為の推薦は避け、カウンセリング予約を案内してください。"
        )
        if context:
            system += f"\n\n参考情報:\n{context}"

        # Build messages with history for continuity
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        return await self.chat_multi(messages, system_prompt=system, max_tokens=512)


def get_ai_service() -> AIService:
    return AIService()
