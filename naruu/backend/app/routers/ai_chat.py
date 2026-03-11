"""AI Chat router — admin chat + natural language DB queries."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.ai_conversation import AIConversation, ConversationContext
from app.models.user import User
from app.services.ai_service import get_ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


# ── Schemas ──────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    context: str = "chat"  # chat | query | translation
    conversation_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    tokens_used: int


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "ja"
    target_lang: str = "ko"


class TranslateResponse(BaseModel):
    translated: str
    source_lang: str
    target_lang: str


class ConversationListItem(BaseModel):
    id: int
    context: str
    preview: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to Claude AI and get a response."""
    ai_service = get_ai_service()

    # Determine system prompt based on context
    system_prompts = {
        "chat": (
            "あなたはNARUU（ナル）のAIアシスタントです。"
            "管理者からの質問に日本語または韓国語で回答してください。"
            "医療観光、大邱観光、顧客管理に関する質問に対応します。"
            "相手の言語に合わせて回答してください。"
        ),
        "query": (
            "You are a NARUU business intelligence assistant. "
            "Answer questions about customers, reservations, orders, and revenue. "
            "Respond in the same language as the question. "
            "Be precise with numbers and data."
        ),
        "content": (
            "あなたはNARUUのコンテンツクリエーターです。"
            "日本人観光客向けの大邱観光・美容コンテンツのアイデアや"
            "スクリプトを生成します。フォーマット: ショート動画25-35秒。"
        ),
    }

    system = system_prompts.get(body.context, system_prompts["chat"])

    # Load conversation history if continuing
    messages_history: list[dict] = []
    if body.conversation_id:
        from sqlalchemy import select
        result = await db.execute(
            select(AIConversation).where(AIConversation.id == body.conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv and isinstance(conv.messages, list):
            messages_history = conv.messages

    # Add new user message
    messages_history.append({
        "role": "user",
        "content": body.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Call Claude with FULL conversation history for continuity
    # Build messages list from history (exclude timestamps for API)
    api_messages = []
    for msg in messages_history:
        if isinstance(msg, dict) and msg.get("role") in ("user", "assistant"):
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })

    reply = await ai_service.chat_multi(api_messages, system_prompt=system)

    if not reply:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 응답을 받지 못했습니다. API 키를 확인하세요.",
        )

    # Add assistant response
    messages_history.append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    # Rough token estimation (4 chars ≈ 1 token)
    tokens_est = (len(body.message) + len(reply)) // 4

    # Context enum mapping
    ctx_map = {
        "chat": ConversationContext.CHAT,
        "query": ConversationContext.QUERY,
        "content": ConversationContext.CONTENT,
        "translation": ConversationContext.TRANSLATION,
    }

    # Save or update conversation
    if body.conversation_id:
        from sqlalchemy import select
        result = await db.execute(
            select(AIConversation).where(AIConversation.id == body.conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            conv.messages = messages_history
            conv.tokens_used = (conv.tokens_used or 0) + tokens_est
            conversation_id = conv.id
        else:
            conv = AIConversation(
                user_id=current_user.id,
                context=ctx_map.get(body.context, ConversationContext.CHAT),
                messages=messages_history,
                model_used=ai_service.model,
                tokens_used=tokens_est,
            )
            db.add(conv)
            await db.flush()
            conversation_id = conv.id
    else:
        conv = AIConversation(
            user_id=current_user.id,
            context=ctx_map.get(body.context, ConversationContext.CHAT),
            messages=messages_history,
            model_used=ai_service.model,
            tokens_used=tokens_est,
        )
        db.add(conv)
        await db.flush()
        conversation_id = conv.id

    return ChatResponse(
        reply=reply,
        conversation_id=conversation_id,
        tokens_used=tokens_est,
    )


@router.post("/translate", response_model=TranslateResponse)
async def translate(
    body: TranslateRequest,
    _: User = Depends(get_current_user),
):
    """Translate text between ja/ko/en."""
    ai_service = get_ai_service()
    result = await ai_service.translate(body.text, body.source_lang, body.target_lang)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="번역에 실패했습니다",
        )

    return TranslateResponse(
        translated=result,
        source_lang=body.source_lang,
        target_lang=body.target_lang,
    )


class ConversationDetailResponse(BaseModel):
    id: int
    context: str
    messages: list[dict]
    tokens_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Load a specific conversation with full message history."""
    from sqlalchemy import select

    result = await db.execute(
        select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다",
        )

    return ConversationDetailResponse(
        id=conv.id,
        context=conv.context.value,
        messages=conv.messages if isinstance(conv.messages, list) else [],
        tokens_used=conv.tokens_used,
        created_at=conv.created_at,
    )


@router.get("/conversations", response_model=list[ConversationListItem])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent AI conversations for current user."""
    from sqlalchemy import select

    result = await db.execute(
        select(AIConversation)
        .where(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.created_at.desc())
        .limit(50)
    )
    conversations = result.scalars().all()

    items = []
    for c in conversations:
        # Extract preview from first user message
        preview = ""
        if isinstance(c.messages, list) and c.messages:
            for msg in c.messages:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    preview = msg.get("content", "")[:80]
                    break

        items.append(ConversationListItem(
            id=c.id,
            context=c.context.value,
            preview=preview,
            created_at=c.created_at,
        ))

    return items
