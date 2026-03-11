"""
AI 대화 세션 및 메모리 API
- 세션 관리 (생성, 조회, 삭제)
- 메모리 관리 (기억, 회상, 삭제)
- 대화 이력 조회
- 요약 생성 및 조회 (MD 파일)
- 활성 세션 조회
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from kis_estimator_core.services.conversation_memory_service import (
    get_memory_service,
    ConversationMessage,
    MemoryEntry
)

router = APIRouter(prefix="/v1/ai/sessions", tags=["AI Sessions"])


# ===== 요청/응답 스키마 =====
class CreateSessionRequest(BaseModel):
    user_id: str = Field(default="default", description="사용자 ID")
    title: Optional[str] = Field(default=None, description="세션 제목")


class CreateSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    message: str = "세션이 생성되었습니다."


class SessionListResponse(BaseModel):
    sessions: list[dict]
    total: int


class SessionDetailResponse(BaseModel):
    session_id: str
    title: Optional[str]
    user_id: str
    message_count: int
    messages: list[dict]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    summary: Optional[str] = None


class AddMessageRequest(BaseModel):
    role: str = Field(..., description="user 또는 assistant")
    content: str = Field(..., description="메시지 내용")
    intent: Optional[str] = Field(default=None)
    metadata: Optional[dict] = Field(default=None)


class MemoryRequest(BaseModel):
    key: str = Field(..., description="메모리 키")
    value: str = Field(..., description="메모리 값")
    category: str = Field(default="knowledge", description="customer|project|preference|knowledge")
    importance: int = Field(default=5, ge=1, le=10)
    expires_in_days: Optional[int] = Field(default=None)
    user_id: str = Field(default="default")


class MemoryResponse(BaseModel):
    memory_id: str
    key: str
    value: str
    category: str
    importance: int
    message: str = "메모리가 저장되었습니다."


class MemoryListResponse(BaseModel):
    memories: list[dict]
    total: int


class SystemPromptRequest(BaseModel):
    content: str = Field(..., description="시스템 프롬프트 내용")


class SummaryResponse(BaseModel):
    session_id: str
    summary: Optional[str]
    generated: bool
    message: str


# ===== 세션 API =====
@router.post("/create", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """새 대화 세션 생성 (이전 요약 자동 참조)"""
    service = get_memory_service()
    session = await service.create_session(
        user_id=request.user_id,
        title=request.title
    )
    return CreateSessionResponse(
        session_id=session.session_id,
        title=session.title or "",
        created_at=session.created_at
    )


@router.get("/list", response_model=SessionListResponse)
async def list_sessions(
    user_id: str = Query(default="default"),
    limit: int = Query(default=20, le=100)
):
    """세션 목록 조회 (summary 필드 포함)"""
    service = get_memory_service()
    sessions = await service.list_sessions(user_id, limit)
    return SessionListResponse(
        sessions=sessions,
        total=len(sessions)
    )


@router.get("/active")
async def get_active_session(user_id: str = Query(default="default")):
    """현재 활성 세션 조회 (Mission 4: 새 엔드포인트)

    24시간 이내에 활성화된 세션이 있으면 반환.
    없으면 404.
    """
    service = get_memory_service()
    session = await service.get_active_session(user_id=user_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="활성 세션이 없습니다. 새 세션을 생성해주세요."
        )

    # 이전 요약 존재 여부 확인
    latest_summary = await service.get_latest_summary()

    return {
        "session_id": session.session_id,
        "title": session.title,
        "user_id": session.user_id,
        "message_count": len(session.messages),
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "is_active": session.is_active,
        "has_summary": session.summary is not None,
        "has_previous_summary": latest_summary is not None,
    }


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str):
    """세션 상세 조회 (summary 포함)"""
    service = get_memory_service()
    session = await service.storage.load_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return SessionDetailResponse(
        session_id=session.session_id,
        title=session.title,
        user_id=session.user_id,
        message_count=len(session.messages),
        messages=[
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp.isoformat(),
                "intent": m.intent
            }
            for m in session.messages
        ],
        created_at=session.created_at,
        updated_at=session.updated_at,
        is_active=session.is_active,
        summary=session.summary
    )


@router.post("/{session_id}/messages")
async def add_message(session_id: str, request: AddMessageRequest):
    """세션에 메시지 추가"""
    service = get_memory_service()

    # 세션 존재 확인
    session = await service.storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    message = await service.add_message(
        role=request.role,
        content=request.content,
        session_id=session_id,
        intent=request.intent,
        metadata=request.metadata
    )

    return {
        "success": True,
        "message": "메시지가 추가되었습니다.",
        "timestamp": message.timestamp.isoformat()
    }


@router.get("/{session_id}/context")
async def get_conversation_context(
    session_id: str,
    max_tokens: int = Query(default=4000)
):
    """대화 컨텍스트 조회 (AI 프롬프트용)"""
    service = get_memory_service()

    # 세션 로드
    session = await service.storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    service._current_session = session
    context = await service.get_conversation_context(session_id, max_tokens)

    return {
        "session_id": session_id,
        "context": context,
        "message_count": len(session.messages)
    }


@router.post("/{session_id}/close")
async def close_session(session_id: str):
    """세션 종료 (자동 요약 생성)"""
    service = get_memory_service()
    success = await service.close_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return {"success": True, "message": "세션이 종료되었습니다. 요약이 자동 생성되었습니다."}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    service = get_memory_service()
    success = await service.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    return {"success": True, "message": "세션이 삭제되었습니다."}


# ===== 요약 API (Mission 4) =====
@router.post("/{session_id}/summarize", response_model=SummaryResponse)
async def summarize_session(session_id: str):
    """수동 요약 트리거 (Mission 4: 새 엔드포인트)

    세션의 대화 내용을 규칙 기반으로 요약하고
    MD 파일로 저장합니다.
    """
    service = get_memory_service()

    # 세션 존재 확인
    session = await service.storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    if not session.messages:
        return SummaryResponse(
            session_id=session_id,
            summary=None,
            generated=False,
            message="대화 내용이 없어 요약을 생성할 수 없습니다."
        )

    md_content = await service.generate_summary(session_id)

    if md_content is None:
        raise HTTPException(status_code=500, detail="요약 생성에 실패했습니다.")

    return SummaryResponse(
        session_id=session_id,
        summary=md_content,
        generated=True,
        message=f"요약이 생성되었습니다. ({len(session.messages)}개 메시지 분석)"
    )


@router.get("/{session_id}/summary")
async def get_session_summary(session_id: str, format: str = Query(default="json")):
    """세션 요약 조회 (Mission 4: 새 엔드포인트)

    Args:
        session_id: 세션 ID
        format: 응답 형식 ("json" 또는 "md")
    """
    service = get_memory_service()

    # 세션 존재 확인
    session = await service.storage.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    summary = await service.get_summary(session_id)

    # 요약이 없으면 생성 시도
    if summary is None and session.messages:
        summary = await service.generate_summary(session_id)

    if format == "md" and summary:
        return PlainTextResponse(content=summary, media_type="text/markdown; charset=utf-8")

    return {
        "session_id": session_id,
        "summary": summary,
        "has_summary": summary is not None,
        "message_count": len(session.messages),
    }


# ===== 메모리 API =====
@router.post("/memory/remember", response_model=MemoryResponse)
async def remember(request: MemoryRequest):
    """정보 기억하기"""
    service = get_memory_service()
    memory = await service.remember(
        key=request.key,
        value=request.value,
        category=request.category,
        importance=request.importance,
        expires_in_days=request.expires_in_days,
        user_id=request.user_id
    )

    return MemoryResponse(
        memory_id=memory.memory_id,
        key=memory.key,
        value=memory.value,
        category=memory.category,
        importance=memory.importance
    )


@router.get("/memory/recall", response_model=MemoryListResponse)
async def recall(
    user_id: str = Query(default="default"),
    category: Optional[str] = Query(default=None)
):
    """기억 회상하기"""
    service = get_memory_service()
    memories = await service.recall(category=category, user_id=user_id)

    return MemoryListResponse(
        memories=[
            {
                "memory_id": m.memory_id,
                "key": m.key,
                "value": m.value,
                "category": m.category,
                "importance": m.importance,
                "created_at": m.created_at.isoformat()
            }
            for m in memories
        ],
        total=len(memories)
    )


@router.delete("/memory/{memory_id}")
async def forget(memory_id: str, user_id: str = Query(default="default")):
    """기억 삭제"""
    service = get_memory_service()
    success = await service.forget(memory_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="메모리를 찾을 수 없습니다.")

    return {"success": True, "message": "메모리가 삭제되었습니다."}


# ===== 시스템 프롬프트 API =====
@router.get("/system-prompt")
async def get_system_prompt():
    """시스템 프롬프트 조회"""
    service = get_memory_service()
    content = await service.get_system_prompt()

    return {
        "content": content,
        "has_prompt": content is not None
    }


@router.post("/system-prompt")
async def set_system_prompt(request: SystemPromptRequest):
    """시스템 프롬프트 설정"""
    service = get_memory_service()
    success = await service.set_system_prompt(request.content)

    if not success:
        raise HTTPException(status_code=500, detail="시스템 프롬프트 저장에 실패했습니다.")

    return {"success": True, "message": "시스템 프롬프트가 저장되었습니다."}


# ===== 전체 컨텍스트 API =====
@router.get("/full-context")
async def get_full_context(
    user_id: str = Query(default="default"),
    session_id: Optional[str] = Query(default=None)
):
    """AI에 전달할 전체 컨텍스트 조회 (이전 요약 포함)"""
    service = get_memory_service()

    # 세션이 지정된 경우 로드
    if session_id:
        session = await service.storage.load_session(session_id)
        if session:
            service._current_session = session

    context = await service.get_full_context_for_ai(user_id, session_id)

    return {
        "system_prompt": context["system_prompt"],
        "memories": context["memories"],
        "conversation": context["conversation"],
        "previous_summary": context.get("previous_summary"),
        "session_id": context["session_id"]
    }


# ===== 현재/마지막 세션 =====
@router.get("/current")
async def get_current_session(user_id: str = Query(default="default")):
    """현재 또는 마지막 활성 세션 조회 (없으면 자동 생성)"""
    service = get_memory_service()
    session = await service.get_or_create_session(user_id=user_id)

    # 이전 요약 존재 여부 확인
    latest_summary = await service.get_latest_summary()

    return {
        "session_id": session.session_id,
        "title": session.title,
        "message_count": len(session.messages),
        "updated_at": session.updated_at.isoformat(),
        "is_new": len(session.messages) == 0,
        "has_previous_summary": latest_summary is not None,
    }
