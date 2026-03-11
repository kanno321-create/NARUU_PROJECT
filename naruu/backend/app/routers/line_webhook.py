"""LINE Messaging API webhook handler.

Receives messages from LINE → logs → AI auto-reply → stores response.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.line_message import LineMessage, MessageDirection, MessageType
from app.services.ai_service import get_ai_service
from app.services.line_service import get_line_service

router = APIRouter(prefix="/line", tags=["line"])


# ── Schemas (LINE webhook payload) ───────────────


class LineSource(BaseModel):
    type: str
    userId: str | None = None
    groupId: str | None = None


class LineMessagePayload(BaseModel):
    id: str
    type: str
    text: str | None = None


class LineEvent(BaseModel):
    type: str
    replyToken: str | None = None
    source: LineSource | None = None
    message: LineMessagePayload | None = None


class LineWebhookBody(BaseModel):
    events: list[LineEvent]


# ── Webhook Endpoint ─────────────────────────────


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(..., alias="X-Line-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """LINE webhook receiver — validates signature, processes events."""
    body = await request.body()
    line_service = get_line_service()

    # Verify signature
    if not line_service.verify_signature(body, x_line_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature",
        )

    payload = LineWebhookBody.model_validate_json(body)

    for event in payload.events:
        if event.type == "message" and event.message and event.source:
            await _handle_message(db, event, line_service)
        elif event.type == "follow" and event.source:
            await _handle_follow(db, event, line_service)

    return {"status": "ok"}


# ── Event Handlers ───────────────────────────────


async def _handle_message(
    db: AsyncSession, event: LineEvent, line_service
):
    """Process incoming text message → AI reply."""
    user_id = event.source.userId if event.source else None
    if not user_id or not event.message:
        return

    text = event.message.text or ""

    # Find or link customer
    customer = await _get_or_create_customer(db, user_id, line_service)

    # Log incoming message
    incoming = LineMessage(
        line_user_id=user_id,
        customer_id=customer.id if customer else None,
        direction=MessageDirection.IN,
        message_type=MessageType.TEXT,
        content=text,
        ai_generated=False,
    )
    db.add(incoming)

    # Load recent conversation history for this LINE user (last 10 messages)
    recent_msgs = await db.execute(
        select(LineMessage)
        .where(LineMessage.line_user_id == user_id)
        .order_by(LineMessage.created_at.desc())
        .limit(10)
    )
    history_rows = list(reversed(recent_msgs.scalars().all()))
    history = []
    for msg in history_rows:
        role = "user" if msg.direction == MessageDirection.IN else "assistant"
        history.append({"role": role, "content": msg.content})

    # Generate AI reply with conversation history
    ai_service = get_ai_service()
    reply_text = await ai_service.generate_line_reply(text, history=history)

    if not reply_text:
        reply_text = (
            "申し訳ございません。ただいま対応できません。"
            "スタッフが確認次第、ご連絡いたします。"
        )

    # Send reply
    if event.replyToken:
        await line_service.reply_message(event.replyToken, reply_text)

    # Log outgoing message
    outgoing = LineMessage(
        line_user_id=user_id,
        customer_id=customer.id if customer else None,
        direction=MessageDirection.OUT,
        message_type=MessageType.TEXT,
        content=reply_text,
        ai_generated=True,
    )
    db.add(outgoing)


async def _handle_follow(
    db: AsyncSession, event: LineEvent, line_service
):
    """New friend added — create customer record + welcome message."""
    user_id = event.source.userId if event.source else None
    if not user_id:
        return

    customer = await _get_or_create_customer(db, user_id, line_service)

    welcome = (
        "NARUUへようこそ！🎉\n\n"
        "大邱の美容・医療観光についてお気軽にご質問ください。\n"
        "・美容施術のご相談\n"
        "・観光プランのご案内\n"
        "・レストラン・グルメ情報\n\n"
        "何でもお聞きくださいね😊"
    )

    if event.replyToken:
        await line_service.reply_message(event.replyToken, welcome)

    # Log welcome message
    outgoing = LineMessage(
        line_user_id=user_id,
        customer_id=customer.id if customer else None,
        direction=MessageDirection.OUT,
        message_type=MessageType.TEXT,
        content=welcome,
        ai_generated=False,
    )
    db.add(outgoing)


# ── Helper ───────────────────────────────────────


async def _get_or_create_customer(
    db: AsyncSession, line_user_id: str, line_service
) -> Customer | None:
    """Find existing customer by LINE ID, or create a new one."""
    result = await db.execute(
        select(Customer).where(Customer.line_user_id == line_user_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        # Fetch LINE profile for display name
        profile = await line_service.get_profile(line_user_id)
        display_name = profile.get("displayName", "LINE User") if profile else "LINE User"

        customer = Customer(
            name_ja=display_name,
            line_user_id=line_user_id,
            nationality="JP",
            preferred_language="ja",
            tags=["LINE"],
        )
        db.add(customer)
        await db.flush()
        await db.refresh(customer)

    return customer
