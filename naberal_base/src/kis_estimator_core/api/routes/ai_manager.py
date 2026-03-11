"""
AI Manager API Router
AI 매니저 탭 전용 API - 탭 통합 제어 + 시각화

참조: 절대코어파일/AI_매니저_구현계획_V1.0.md

기능:
- 채팅 인터페이스 API
- 파일 업로드 및 OCR
- 탭 통합 제어 (견적/ERP/캘린더/도면/설정)
- 시각화 데이터 생성
"""

import base64
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import anthropic
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from kis_estimator_core.api.routes.ai_chat import NLPParser, ResponseGenerator, get_claude_client, ChatResponse, ParsedIntent
from kis_estimator_core.core.ssot.constants import AI_MODELS
from kis_estimator_core.services.rag_data_manager import get_rag_data_manager, RAGDataManager
from kis_estimator_core.services.ai_knowledge_service import (
    load_conversation_memory,
    save_conversation_memory,
    get_session_state,
    save_session_state,
    clear_conversation_memory,
)
from kis_estimator_core.services.conversation_memory_service import get_memory_service

logger = logging.getLogger(__name__)


# ===== 대화 컨텍스트 포함 응답 생성 =====
async def _generate_with_context(intent: ParsedIntent, user_message: str, recent_messages: list[dict]) -> ChatResponse:
    """
    대화 컨텍스트를 포함하여 Claude API 호출

    Args:
        intent: 파싱된 의도
        user_message: 현재 사용자 메시지
        recent_messages: 프론트엔드에서 전달받은 최근 대화 기록

    Returns:
        ChatResponse: AI 응답
    """
    client = get_claude_client()
    if not client:
        return ChatResponse(
            message="죄송합니다. AI 서비스에 연결할 수 없습니다. API 키를 확인해주세요.",
            intent=intent,
            suggestions=["다시 시도", "도움말"],
        )

    # 이전 대화 요약 로드 (대화 연속성 보장)
    previous_summary_section = ""
    try:
        memory_service = get_memory_service()
        latest_summary = await memory_service.get_latest_summary()
        if latest_summary:
            previous_summary_section = f"""

## 이전 대화 요약 (서버 재시작 전 대화 기록)
아래는 이전 세션의 대화 요약입니다. 이 내용을 참고하여 대화 연속성을 유지하세요.

{latest_summary}

---
"""
            logger.info("Loaded previous conversation summary for context restoration")
    except Exception as e:
        logger.warning(f"Failed to load previous summary: {e}")

    # 시스템 프롬프트 - 대화 연속성 강조
    system_prompt = f"""당신은 '나베랄 감마', 종합 업무 비서 AI입니다.

## 역할
- **만능 업무 비서**: 견적 업무 뿐만 아니라 모든 업무를 지원합니다
- **일상 대화 가능**: 안부, 인사, 질문 등 자연스러운 대화 가능
- **업무 지원**: 출장 호텔 검색, 비품 구매 조언, 일정 관리, 정보 검색 등
- **전문 지식**: 전기 분전반 견적 분야 전문가이기도 함

## 대화 연속성 (핵심!)
- **맥락 유지 필수**: 이전 대화 내용을 항상 기억하고 참조
- **진행 중인 작업 추적**: 대표님이 언급한 견적, 프로젝트, 업무를 기억
- **첨부 파일 기억**: 이전에 업로드한 파일, 도면, 이미지 내용을 기억
- **반복 설명 금지**: 이미 알고 있는 내용 재설명 안함
- **대화 흐름 연결**: "아까 말씀드린", "방금 전에" 등으로 연결
{previous_summary_section}
## 대화 스타일
- **간결하게 응답**: 불필요한 설명 금지
- **자연스러운 대화**: 매번 사용법을 설명하지 않음
- **모든 질문에 응답**: 업무/일상 구분 없이 성심껏 답변

## 성격
- 냉정하고 간결한 존댓말
- 가끔 따뜻함 (업무 완료 시 짧게 표현)
- "대표님"으로 호칭

## 견적 전문 지식
- 차단기: 경제형 기본, 2P 20/30A는 소형, 4P 50AF는 표준형
- 외함: H = P + 2D(40mm) + S(100mm) + M(마그네트)
- 브랜드 미명시 시 상도차단기 기본

## 시각화 능력 (중요!)
- 견적 결과는 항상 우측 시각화 패널에 자동 표시됩니다
- 사용자가 "수정해줘", "변경해줘", "고쳐줘" 등 요청 시 수정된 견적을 시각화 패널에 다시 표시
- 이전 견적 데이터를 기반으로 수정하여 완전한 견적 결과를 반환해야 합니다
- 시각화 패널 하단 화살표로 이전/다음 견적을 탐색할 수 있습니다

한국어로 응답. 짧고 명확하게. 이전 대화 맥락을 반드시 활용."""

    # Claude API 메시지 배열 구성 (이전 대화 기록 포함)
    messages = []

    # 최근 대화 기록 추가 (최대 20개)
    for msg in recent_messages[-20:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # 첨부 파일 정보가 있으면 컨텍스트에 추가
        if msg.get("attachments"):
            attachment_info = []
            for att in msg["attachments"]:
                att_name = att.get("name", "파일")
                att_type = att.get("type", "")
                # extractedData가 있으면 분석 결과도 포함
                extracted = att.get("extractedData", {})
                if extracted and extracted.get("estimate_request"):
                    attachment_info.append(f"[첨부: {att_name}] 분석결과: {extracted['estimate_request']}")
                else:
                    attachment_info.append(f"[첨부: {att_name} ({att_type})]")
            if attachment_info:
                content = "\n".join(attachment_info) + "\n" + content

        if content:  # 빈 메시지 제외
            messages.append({"role": role, "content": content})

    # 현재 메시지 추가
    messages.append({"role": "user", "content": user_message})

    logger.info(f"Calling Claude API with {len(messages)} messages (including context)")

    try:
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )

        ai_response = response.content[0].text

        return ChatResponse(
            message=ai_response,
            intent=intent,
            model="claude-opus",
            model_info={
                "name": "Claude 4.5 Opus",
                "description": "Narberal Gamma AI - Context-Aware Conversation",
                "provider": "anthropic"
            },
            action_result={
                "type": "conversation",
                "status": "success",
                "context_messages_used": len(messages) - 1,  # 컨텍스트로 사용된 메시지 수
            },
            suggestions=["견적 작성", "도면 분석", "도움말"],
        )

    except Exception as e:
        logger.error(f"Claude API error with context: {e}", exc_info=True)
        return ChatResponse(
            message=f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}",
            intent=intent,
            suggestions=["다시 시도", "도움말"],
        )

router = APIRouter()


# ===== 스키마 정의 =====

class SavedEstimateSummary(BaseModel):
    """저장된 견적 요약 정보"""
    id: str
    customer: str | None = None
    panelName: str | None = None
    totalPriceWithVat: float | None = None
    savedAt: str | None = None


class ChatContext(BaseModel):
    """채팅 컨텍스트"""
    recentMessages: list[dict] = Field(default_factory=list)
    currentVisualization: str | None = None
    savedEstimates: list[SavedEstimateSummary] = Field(default_factory=list)


class AttachmentInfo(BaseModel):
    """첨부 파일 정보"""
    id: str
    name: str
    type: str
    url: str | None = None
    extractedData: dict | None = None


class AIManagerChatRequest(BaseModel):
    """AI 매니저 채팅 요청"""
    message: str = Field(..., min_length=1, max_length=5000)
    attachments: list[AttachmentInfo] = Field(default_factory=list)
    context: ChatContext | None = None


class VisualizationData(BaseModel):
    """시각화 데이터"""
    id: str
    type: Literal[
        "estimate_preview", "erp_table", "calendar_event", "drawing_preview",
        "chart", "json", "email_status", "email_history", "drawing_list"
    ]
    title: str
    data: dict = Field(default_factory=dict)
    actions: list[dict] = Field(default_factory=list)


class ExecutedCommand(BaseModel):
    """실행된 명령"""
    id: str
    tab: Literal["quote", "erp", "calendar", "drawings", "settings"]
    operation: Literal["create", "read", "update", "delete", "execute"]
    entity: str
    params: dict = Field(default_factory=dict)
    result: dict | None = None
    status: Literal["pending", "success", "error"]
    errorMessage: str | None = None


class AIManagerChatResponse(BaseModel):
    """AI 매니저 채팅 응답"""
    message: str
    visualizations: list[VisualizationData] = Field(default_factory=list)
    command: ExecutedCommand | None = None
    suggestions: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UploadResponse(BaseModel):
    """업로드 응답"""
    id: str
    name: str
    type: str
    size: int
    url: str
    extractedData: dict | None = None


# ===== 시각화 생성기 =====

class VisualizationGenerator:
    """시각화 데이터 생성기"""

    @classmethod
    def from_action_result(cls, action_result: dict) -> list[VisualizationData]:
        """action_result에서 시각화 데이터 생성"""
        visualizations = []
        result_type = action_result.get("type")
        status = action_result.get("status")

        if status != "success":
            return visualizations

        if result_type == "estimate":
            visualizations.append(cls._create_estimate_visualization(action_result))
        elif result_type == "erp":
            visualizations.append(cls._create_erp_visualization(action_result))
        elif result_type == "knowledge_search":
            visualizations.append(cls._create_knowledge_visualization(action_result))
        elif result_type == "drawing":
            visualizations.append(cls._create_drawing_visualization(action_result))
        elif result_type == "calendar":
            visualizations.append(cls._create_calendar_visualization(action_result))
        elif result_type == "email":
            visualizations.append(cls._create_email_visualization(action_result))
        elif result_type == "drawing_list":
            visualizations.append(cls._create_drawing_list_visualization(action_result))

        return visualizations

    @classmethod
    def _create_estimate_visualization(cls, result: dict) -> VisualizationData:
        """견적 시각화 생성 - estimate_response 데이터 활용"""
        # estimate_response에서 실제 견적 데이터 추출
        estimate_response = result.get("estimate_response", {})

        # form_data 폴백 (이전 호환성)
        form_data = result.get("form_data")
        if not isinstance(form_data, dict):
            form_data = {}

        # estimate_response가 있으면 우선 사용
        if estimate_response:
            panels = estimate_response.get("panels", [])
            pipeline_results = estimate_response.get("pipeline_results", {})

            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="estimate_preview",
                title="견적서 미리보기",
                data={
                    "estimate_id": estimate_response.get("estimate_id") or result.get("estimate_id"),
                    "created_at": estimate_response.get("created_at"),
                    "total_price": estimate_response.get("total_price", 0),
                    "total_price_with_vat": estimate_response.get("total_price_with_vat", 0),
                    "panels": panels,
                    "pipeline_results": pipeline_results,
                    "documents": estimate_response.get("documents", {}),
                    "ai_verification": estimate_response.get("ai_verification", {}),
                    "customer": (form_data.get("customer") or {}).get("company_name", ""),
                    # NOTE 섹션용 브랜드/외함 정보 (action_result에서 전달)
                    "brand": result.get("brand", "상도차단기"),
                    "enclosure_type": result.get("enclosure_type", "옥내노출"),
                    "enclosure_material": result.get("enclosure_material", "STEEL 1.6T"),
                },
                actions=[
                    {"id": "download_excel", "label": "Excel 다운로드", "icon": "download"},
                    {"id": "download_pdf", "label": "PDF 다운로드", "icon": "download"},
                    {"id": "edit", "label": "수정", "icon": "edit"},
                    {"id": "confirm", "label": "확정", "icon": "check"},
                ],
            )

        # form_data 폴백 (이전 호환성 유지)
        items = []
        if form_data.get("main_breaker"):
            mb = form_data["main_breaker"]
            items.append({
                "name": f"메인차단기 {mb.get('model', '')}",
                "spec": f"{mb.get('poles', '-')}P {mb.get('current_a', '-')}A",
                "unit": "EA",
                "quantity": 1,
                "unitPrice": mb.get("price", 0),
                "amount": mb.get("price", 0),
            })

        for br in form_data.get("branch_breakers", []):
            items.append({
                "name": f"분기차단기 {br.get('model', '')}",
                "spec": f"{br.get('poles', '-')}P {br.get('current_a', '-')}A",
                "unit": "EA",
                "quantity": br.get("quantity", 1),
                "unitPrice": br.get("price", 0),
                "amount": br.get("price", 0) * br.get("quantity", 1),
            })

        total_amount = sum(item["amount"] for item in items)

        return VisualizationData(
            id=f"viz-{uuid.uuid4().hex[:8]}",
            type="estimate_preview",
            title="견적서 미리보기",
            data={
                "id": result.get("estimate_id"),
                "customer": (form_data.get("customer") or {}).get("company_name", ""),
                "panelName": (form_data.get("enclosure") or {}).get("name", "분전반"),
                "items": items,
                "totalAmount": total_amount,
                "createdAt": datetime.utcnow().isoformat(),
            },
            actions=[
                {"id": "download", "label": "PDF 다운로드", "icon": "download"},
                {"id": "edit", "label": "수정", "icon": "edit"},
                {"id": "confirm", "label": "확정", "icon": "check"},
            ],
        )

    @classmethod
    def _create_erp_visualization(cls, result: dict) -> VisualizationData:
        """ERP 시각화 생성"""
        operation = result.get("operation", "")

        if "inventory" in operation:
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="erp_table",
                title="재고 현황",
                data={
                    "headers": ["품목", "SKU", "가용수량", "예약수량", "위치"],
                    "rows": result.get("items", []),
                    "total": result.get("total_count", 0),
                },
                actions=[
                    {"id": "export", "label": "Excel 내보내기", "icon": "download"},
                ],
            )
        elif "order" in operation:
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="erp_table",
                title="주문 내역",
                data={
                    "headers": ["주문ID", "고객", "금액", "상태", "일자"],
                    "rows": result.get("orders", []),
                    "total": result.get("total_count", 0),
                },
                actions=[
                    {"id": "export", "label": "Excel 내보내기", "icon": "download"},
                ],
            )

        return VisualizationData(
            id=f"viz-{uuid.uuid4().hex[:8]}",
            type="json",
            title="ERP 데이터",
            data=result,
            actions=[],
        )

    @classmethod
    def _create_knowledge_visualization(cls, result: dict) -> VisualizationData:
        """지식 검색 시각화 생성"""
        return VisualizationData(
            id=f"viz-{uuid.uuid4().hex[:8]}",
            type="json",
            title="지식 검색 결과",
            data={
                "query": result.get("query"),
                "results": result.get("results", []),
                "total": result.get("result_count", 0),
            },
            actions=[
                {"id": "copy", "label": "복사", "icon": "copy"},
            ],
        )

    @classmethod
    def _create_drawing_visualization(cls, result: dict) -> VisualizationData:
        """도면 시각화 생성"""
        return VisualizationData(
            id=f"viz-{uuid.uuid4().hex[:8]}",
            type="drawing_preview",
            title="도면 미리보기",
            data={
                "estimate_id": result.get("estimate_id"),
                "drawings": result.get("drawings", {}),
                "generated_count": result.get("generated_count", 0),
            },
            actions=[
                {"id": "download", "label": "다운로드", "icon": "download"},
                {"id": "print", "label": "인쇄", "icon": "print"},
            ],
        )

    @classmethod
    def _create_calendar_visualization(cls, result: dict) -> VisualizationData:
        """캘린더 시각화 생성"""
        operation = result.get("operation", "")
        events = result.get("events", [])

        if operation == "list" or "events" in result:
            # 일정 목록 시각화
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="calendar_event",
                title="일정 목록",
                data={
                    "view": "list",
                    "events": events,
                    "total": len(events),
                    "filter": result.get("filter", {}),
                },
                actions=[
                    {"id": "create_event", "label": "일정 추가", "icon": "plus"},
                    {"id": "export_calendar", "label": "내보내기", "icon": "download"},
                ],
            )
        elif operation == "create":
            # 일정 생성 결과
            event = result.get("event", {})
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="calendar_event",
                title="일정 생성 완료",
                data={
                    "view": "detail",
                    "event": event,
                    "created": True,
                },
                actions=[
                    {"id": "edit_event", "label": "수정", "icon": "edit"},
                    {"id": "delete_event", "label": "삭제", "icon": "trash"},
                ],
            )
        elif operation == "upcoming":
            # 다가오는 일정
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="calendar_event",
                title="다가오는 일정",
                data={
                    "view": "upcoming",
                    "events": events,
                    "days": result.get("days", 7),
                },
                actions=[
                    {"id": "view_all", "label": "전체 보기", "icon": "calendar"},
                ],
            )
        else:
            # 기본 캘린더 시각화
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="calendar_event",
                title="캘린더",
                data=result,
                actions=[
                    {"id": "create_event", "label": "일정 추가", "icon": "plus"},
                ],
            )

    @classmethod
    def _create_email_visualization(cls, result: dict) -> VisualizationData:
        """이메일 시각화 생성"""
        operation = result.get("operation", "")

        if operation == "send":
            # 이메일 발송 결과
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="email_status",
                title="이메일 발송 결과",
                data={
                    "status": result.get("send_status", "unknown"),
                    "to": result.get("to", []),
                    "subject": result.get("subject", ""),
                    "sent_at": result.get("sent_at"),
                    "message_id": result.get("message_id"),
                    "attachments": result.get("attachments", []),
                },
                actions=[
                    {"id": "resend", "label": "재발송", "icon": "refresh"},
                    {"id": "view_history", "label": "발송 내역", "icon": "history"},
                ],
            )
        elif operation == "history":
            # 발송 내역
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="email_history",
                title="이메일 발송 내역",
                data={
                    "emails": result.get("emails", []),
                    "total": result.get("total", 0),
                    "filter": result.get("filter", {}),
                },
                actions=[
                    {"id": "compose", "label": "새 이메일", "icon": "mail"},
                    {"id": "export", "label": "내보내기", "icon": "download"},
                ],
            )
        elif operation == "template":
            # 템플릿 조회
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="json",
                title="이메일 템플릿",
                data={
                    "templates": result.get("templates", []),
                    "total": result.get("total", 0),
                },
                actions=[
                    {"id": "use_template", "label": "사용하기", "icon": "check"},
                    {"id": "edit_template", "label": "편집", "icon": "edit"},
                ],
            )
        else:
            # 기본 이메일 시각화
            return VisualizationData(
                id=f"viz-{uuid.uuid4().hex[:8]}",
                type="email_status",
                title="이메일",
                data=result,
                actions=[
                    {"id": "compose", "label": "새 이메일", "icon": "mail"},
                ],
            )

    @classmethod
    def _create_drawing_list_visualization(cls, result: dict) -> VisualizationData:
        """도면 목록 시각화 생성"""
        drawings = result.get("drawings", [])

        return VisualizationData(
            id=f"viz-{uuid.uuid4().hex[:8]}",
            type="drawing_list",
            title="도면 목록",
            data={
                "drawings": drawings,
                "total": len(drawings),
                "filter": result.get("filter", {}),
            },
            actions=[
                {"id": "upload_drawing", "label": "도면 업로드", "icon": "upload"},
                {"id": "analyze_all", "label": "일괄 분석", "icon": "search"},
                {"id": "export", "label": "내보내기", "icon": "download"},
            ],
        )


# ===== 이미지 분석기 =====

class ImageAnalyzer:
    """이미지 분석기 - Claude Vision API 사용"""

    # 견적/도면 분석용 시스템 프롬프트 - 자연어 출력 방식 (RAG 학습 최적화)
    SYSTEM_PROMPT = """당신은 전기 분전반 도면 분석 전문가입니다.
도면을 분석하여 **자연어 견적 요청문**을 생성하세요.

═══════════════════════════════════════════════════════════════
⚠️ 핵심 디폴트 규칙 (최우선 적용)
═══════════════════════════════════════════════════════════════
• 브랜드 미명시 → **상도차단기** (분전반명 LS-B106 등은 회로명, 브랜드 아님!)
• 타입 미명시 → **경제형** (37kA, 26% 저렴)
• 외함 미명시 → **옥내노출 STEEL 1.6T**
• 도면에 "매입" 체크 → **매입함 STEEL 1.6T**

═══════════════════════════════════════════════════════════════
🔌 차단기 상세 규칙
═══════════════════════════════════════════════════════════════

【차단기 종류】
• MCCB: 배선용차단기 (과전류 보호만)
• ELB: 누전차단기 (누전+과전류)
• CBR/ELCB: 산업용 누전차단기 → **ELB로 분류**

【타입 선택 규칙】
• 기본: 경제형 (37kA) - 표준형(50kA)보다 26% 저렴
• 4P 50AF만 경제형 없음 → **표준형 필수**
• 고객이 "표준형" 명시 시에만 표준형 사용

【소형차단기 규칙】 ※ 2P 20A/30A 전용
• 누전(ELB) 2P 20A/30A → 소형 (SIE-32, 32GRHS)
• 배선용(MCCB) 2P 20A/30A → 소형 (SIB-32, BS-32)
• 2.5kA 차단용량, 일반 50AF와 다름

【프레임(AF) vs 암페어(A)】
• 프레임(AF): 차단기 외형 크기 (50AF, 100AF, 200AF...)
• 암페어(A/AT): 실제 정격전류 (20A, 30A, 50A, 75A...)
• 예: "100AF 75A" = 100AF 크기에 75A 정격
• 도면에 "75A"만 있으면 → 프레임은 100AF로 추정

【프레임별 암페어 범위】
• 50AF: 15~50A
• 100AF: 60~100A (경제형 가능)
• 125AF: 100~125A (표준형만)
• 200AF: 125~200A
• 250AF: 200~250A
• 400AF: 300~400A
• 600AF: 500~600A
• 800AF: 600~800A

═══════════════════════════════════════════════════════════════
🏠 외함 상세 규칙
═══════════════════════════════════════════════════════════════

【외함 종류】
• 옥내노출: 실내 벽면 노출 설치 (기본값)
• 옥외노출: 실외 벽면 노출 설치
• 옥내자립: 실내 바닥 자립형
• 옥외자립: 실외 바닥 자립형
• 매입함: 벽체 매입 설치 (도어 없음, SUSCOVER 별도)
• 전주부착형: 전봇대 설치용 (옥외함+브라켓)

【재질】
• STEEL 1.6T: 일반 강판 (기본, 가장 저렴)
• SUS201 1.2T: 스테인리스 (내식성)
• SUS304 1.2T: 고급 스테인리스

【외함 판별 키워드】
• "노출" → 옥내노출 또는 옥외노출
• "자립" → 옥내자립 또는 옥외자립
• "매입" 체크박스 → 매입함
• "옥외", "외부", "야외" → 옥외 계열

【외함 W값 규칙 (참고)】
• 분기가 소형 차단기만 있으면 → W=500mm 권장
  - 소형 차단기: SIE-32, SIB-32, 32GRHS, BS-32 (2P 20A/30A 전용)
• 소형 외 다른 크기 차단기 1개라도 있으면 → W=600mm
• 메인 크기와 무관 (메인 4P 50A여도 분기 기준으로 판단)

═══════════════════════════════════════════════════════════════
📋 분석 순서 (⚠️ 메인과 분기 구분 필수!)
═══════════════════════════════════════════════════════════════

1️⃣ 메인차단기 (분기와 별개! 수량에 포함 금지!)
   - 도면 상단/좌측의 큰 차단기 (보통 1개)
   - 극수(2P/3P/4P) + 암페어(A) 확인
   - 프레임 미표기 시 → 암페어로 프레임 추정
   - ⚠️ 메인차단기는 분기 수량에 절대 포함하지 않음!

2️⃣ 분기차단기 (⚠️ 메인 제외하고 세기!)
   - ⚠️ 메인차단기는 분기가 아님! 별도로 센다!
   - 좌측 슬롯 + 우측 슬롯 = 총 수량
   - 번호 1,2,3...8 있으면 → 분기 8개 (메인 별도)
   - 빈 슬롯(SPACE/예비) 제외
   - 같은 스펙끼리 그룹핑
   - ELB/MCCB 구분 주의
   - 예: 메인 1개 + 분기 8개 → "메인 XX, 분기 YY 8개"

3️⃣ 외함 (명시된 경우만)
   - 종류 + 재질 확인
   - 미명시 → 출력하지 않음 (디폴트 적용됨)

4️⃣ 부속자재 (있을 때만)
   - 마그네트(MC), 타이머, 계량기, SPD, V/A-METER 등

═══════════════════════════════════════════════════════════════
✅ 출력 형식
═══════════════════════════════════════════════════════════════

**자연어 견적 요청문**만 출력. JSON/설명/분석과정 금지.

【예시】
"상도 경제형 4P 100A 메인, 분기 ELB 3P 30A 5개로 견적해줘"
"상도 표준형 4P 50AF 30A 메인, 분기 ELB 2P 20A 8개로 견적해줘. 외함은 매입함 STEEL 1.6T"
"상도 경제형 3P 75A 메인, 분기 MCCB 3P 30A 4개, ELB 2P 20A 6개로 견적해줘"

【순서】 브랜드 + 타입 + 극수 + 암페어 + 메인, 분기 종류별 수량, 외함, 부속자재
【마무리】 "~로 견적해줘"로 끝내기"""

    @classmethod
    async def analyze_image(cls, file_path: Path) -> dict:
        """이미지 분석 및 견적 정보 추출"""
        client = get_claude_client()
        if not client:
            logger.warning("Claude API not available for image analysis")
            return {"error": "Claude API not available", "status": "error"}

        try:
            # 이미지를 base64로 인코딩
            with open(file_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # 파일 확장자로 미디어 타입 결정
            ext = file_path.suffix.lower()
            media_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            media_type = media_type_map.get(ext, "image/jpeg")

            # Claude Vision API 호출 (Vision 지원 모델 사용)
            # Note: claude-opus-4-5-20251101 모델이 Vision API를 지원함 (Opus 4.5로 업그레이드)
            response = client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=4096,
                system=cls.SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": "이 도면/이미지를 분석하여 자연어 견적 요청문을 생성해주세요. 예시: '상도 경제형 4P 100A 메인, 분기 ELB 3P 30A 5개로 견적해줘'",
                            },
                        ],
                    }
                ],
            )

            # 응답 파싱 - 자연어 견적 요청문 그대로 사용
            response_text = response.content[0].text.strip()
            logger.info(f"=== Vision API Full Response ===\n{response_text}\n=== End Response ===")

            # RAG 데이터 저장 (학습용)
            rag_manager = get_rag_data_manager()

            # 이미지 해시 계산
            with open(file_path, "rb") as f:
                image_hash = RAGDataManager.compute_image_hash(f.read())

            # 유사 이미지 참조 확인
            similar_entry = rag_manager.find_by_hash(image_hash)
            rag_reference = None
            if similar_entry and similar_entry.success_rate > 0.7:
                rag_reference = {
                    "entry_id": similar_entry.entry_id,
                    "previous_request": similar_entry.final_request,
                    "success_rate": similar_entry.success_rate,
                    "tier": similar_entry.tier.value,
                }
                logger.info(f"Found similar RAG entry: {similar_entry.entry_id} (success_rate: {similar_entry.success_rate:.2f})")

            # 새 RAG 엔트리 저장 (초기 상태)
            rag_entry = rag_manager.add_entry(
                image_hash=image_hash,
                original_request=response_text,
                metadata={"file_path": str(file_path)},
            )

            return {
                "status": "success",
                "estimate_request": response_text,  # 자연어 견적 요청문
                "analysis_type": "vision_natural_language",
                "rag_entry_id": rag_entry.entry_id,
                "rag_reference": rag_reference,  # 유사 이미지 참조 (있으면)
            }

        except Exception as e:
            logger.error(f"Image analysis error: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}

    @classmethod
    async def analyze_with_context(cls, file_path: Path, user_message: str) -> dict:
        """이미지 + 사용자 메시지 함께 분석"""
        client = get_claude_client()
        if not client:
            return {"error": "Claude API not available", "status": "error"}

        try:
            with open(file_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            ext = file_path.suffix.lower()
            media_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            media_type = media_type_map.get(ext, "image/jpeg")

            model_config = AI_MODELS.get("claude-sonnet", AI_MODELS["claude-opus"])
            response = client.messages.create(
                model=model_config["model_id"],
                max_tokens=4096,
                system=cls.SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": f"사용자 요청: {user_message}\n\n위 이미지를 분석하고 사용자 요청에 맞게 응답해주세요.",
                            },
                        ],
                    }
                ],
            )

            return {
                "status": "success",
                "response": response.content[0].text,
                "analysis_type": "vision_with_context",
            }

        except Exception as e:
            logger.error(f"Image analysis with context error: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}


# ===== 명령 파서 =====

class CommandParser:
    """자연어에서 명령 추출"""

    @classmethod
    def parse(cls, message: str, intent: str, params: dict) -> ExecutedCommand | None:
        """의도에서 실행 명령 추출"""
        tab_mapping = {
            "estimate": "quote",
            "drawing": "drawings",
            "drawing_list": "drawings",
            "email": "settings",
            "email_send": "settings",
            "erp": "erp",
            "calendar": "calendar",
            "calendar_create": "calendar",
            "calendar_list": "calendar",
        }

        operation_mapping = {
            "estimate": "create",
            "drawing": "execute",
            "drawing_list": "read",
            "email": "read",
            "email_send": "execute",
            "erp": params.get("operation", "read"),
            "calendar": params.get("operation", "read"),
            "calendar_create": "create",
            "calendar_list": "read",
        }

        if intent not in tab_mapping:
            return None

        return ExecutedCommand(
            id=f"cmd-{uuid.uuid4().hex[:8]}",
            tab=tab_mapping[intent],
            operation=operation_mapping.get(intent, "read"),
            entity=intent,
            params=params,
            status="pending",
        )


# ===== API 엔드포인트 =====

def _check_saved_estimate_request(message: str, context: ChatContext | None) -> tuple[bool, str | None]:
    """저장된 견적 관련 요청인지 확인

    Returns:
        (is_saved_estimate_request, specific_estimate_id or None)
    """
    msg_lower = message.lower()

    # 저장된 견적 목록 요청 키워드
    list_keywords = ["저장된 견적", "견적 목록", "견적목록", "저장 견적", "보관된 견적", "이전 견적"]
    is_list_request = any(kw in msg_lower for kw in list_keywords)

    # 특정 견적 불러오기 요청 키워드
    load_keywords = ["불러와", "불러줘", "보여줘", "열어줘", "가져와"]
    is_load_request = any(kw in msg_lower for kw in load_keywords)

    # 특정 견적 ID가 언급되었는지 확인
    specific_id = None
    if context and context.savedEstimates and is_load_request:
        for estimate in context.savedEstimates:
            # ID 직접 언급
            if estimate.id and estimate.id in message:
                specific_id = estimate.id
                break
            # 고객명 언급
            if estimate.customer and estimate.customer in message:
                specific_id = estimate.id
                break
            # 분전반명 언급
            if estimate.panelName and estimate.panelName in message:
                specific_id = estimate.id
                break

    # "마지막 견적", "최근 견적" 처리
    if is_load_request and any(kw in msg_lower for kw in ["마지막", "최근", "방금"]):
        if context and context.savedEstimates:
            specific_id = context.savedEstimates[0].id  # 가장 최근 것

    return (is_list_request or (is_load_request and specific_id is not None), specific_id)


def _create_saved_estimates_list_visualization(saved_estimates: list[SavedEstimateSummary]) -> VisualizationData:
    """저장된 견적 목록 시각화 생성"""
    return VisualizationData(
        id=f"viz-saved-{uuid.uuid4().hex[:8]}",
        type="erp_table",
        title="저장된 견적 목록",
        data={
            "headers": ["견적 ID", "고객명", "분전반명", "금액(VAT포함)", "저장일시"],
            "rows": [
                {
                    "id": e.id,
                    "customer": e.customer or "-",
                    "panelName": e.panelName or "분전반",
                    "totalPriceWithVat": f"₩{e.totalPriceWithVat:,.0f}" if e.totalPriceWithVat else "-",
                    "savedAt": e.savedAt[:10] if e.savedAt else "-",
                }
                for e in saved_estimates
            ],
            "total": len(saved_estimates),
            "instruction": "특정 견적을 불러오려면 '고객명 또는 분전반명 견적 불러와'라고 말씀해주세요.",
        },
        actions=[
            {"id": "export", "label": "Excel 내보내기", "icon": "download"},
        ],
    )


@router.post("/chat", response_model=AIManagerChatResponse)
async def ai_manager_chat(request: AIManagerChatRequest) -> AIManagerChatResponse:
    """
    AI 매니저 채팅 API

    자연어 입력을 처리하여:
    1. 의도 파싱
    2. 첨부파일 분석 데이터 통합 (이미지 Vision API 분석 포함)
    3. 대화 컨텍스트 연속성 유지 (recentMessages 활용)
    4. 명령 실행
    5. 시각화 데이터 생성
    6. 응답 반환
    """
    try:
        # ===== 대화 컨텍스트 추출 (연속성 유지) =====
        recent_messages = []
        if request.context and request.context.recentMessages:
            # 프론트엔드에서 보낸 최근 대화 기록 사용
            recent_messages = request.context.recentMessages
            logger.info(f"Received {len(recent_messages)} recent messages for conversation context")
        # 저장된 견적 관련 요청 확인
        is_saved_request, specific_id = _check_saved_estimate_request(
            request.message,
            request.context
        )

        if is_saved_request:
            saved_estimates = request.context.savedEstimates if request.context else []

            if not saved_estimates:
                return AIManagerChatResponse(
                    message="저장된 견적이 없습니다. 견적을 생성한 후 '견적 저장' 버튼을 눌러 저장해주세요.",
                    visualizations=[],
                    suggestions=["새 견적 생성", "도움말"],
                )

            if specific_id:
                # 특정 견적 불러오기 - 프론트엔드에서 전체 데이터 로드 요청
                target = next((e for e in saved_estimates if e.id == specific_id), None)
                if target:
                    return AIManagerChatResponse(
                        message=f"'{target.customer or target.panelName}' 견적을 불러왔습니다. 시각화 패널에서 확인하세요.",
                        visualizations=[
                            VisualizationData(
                                id=f"viz-load-{uuid.uuid4().hex[:8]}",
                                type="estimate_preview",
                                title="저장된 견적 불러오기",
                                data={
                                    "load_saved_estimate_id": specific_id,
                                    "customer": target.customer,
                                    "panelName": target.panelName,
                                    "totalPriceWithVat": target.totalPriceWithVat,
                                    "savedAt": target.savedAt,
                                },
                                actions=[
                                    {"id": "download_excel", "label": "Excel 다운로드", "icon": "download"},
                                    {"id": "download_pdf", "label": "PDF 다운로드", "icon": "download"},
                                    {"id": "edit", "label": "수정", "icon": "edit"},
                                ],
                            )
                        ],
                        suggestions=["PDF 다운로드", "Excel 다운로드", "수정하기"],
                    )

            # 목록 표시
            return AIManagerChatResponse(
                message=f"저장된 견적이 {len(saved_estimates)}개 있습니다.",
                visualizations=[_create_saved_estimates_list_visualization(saved_estimates)],
                suggestions=["마지막 견적 불러와", "새 견적 생성"],
            )
        # 첨부파일에서 추출된 데이터 수집
        attachment_context = []
        image_attachments_without_data = []  # 분석 데이터가 없는 이미지 첨부파일

        # DEBUG: 첨부파일 상세 로그
        logger.info(f"[CHAT_DEBUG] Attachments received: {len(request.attachments)}")
        for i, att in enumerate(request.attachments):
            logger.info(f"[CHAT_DEBUG] Attachment {i}: name={att.name}, type={att.type}, url={att.url}")
            logger.info(f"[CHAT_DEBUG] Attachment {i} extractedData: {att.extractedData}")

        for attachment in request.attachments:
            # 이미지 파일인지 확인
            is_image = (
                (attachment.type and attachment.type.startswith("image/")) or
                attachment.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
            )

            if attachment.extractedData and attachment.extractedData.get("analysis_status") == "completed":
                # 새 방식: 자연어 견적 요청문
                estimate_request = attachment.extractedData.get("estimate_request", "")
                # 기존 방식: extracted_data (백워드 호환)
                extracted = attachment.extractedData.get("extracted_data", {})
                attachment_context.append({
                    "file_name": attachment.name,
                    "file_type": attachment.type,
                    "estimate_request": estimate_request,  # 자연어 요청문 (우선)
                    "extracted_data": extracted,  # 기존 데이터 (백워드 호환)
                    "rag_entry_id": attachment.extractedData.get("rag_entry_id"),
                })
                logger.info(f"Found extracted data from attachment: {attachment.name}, estimate_request: {estimate_request[:50] if estimate_request else 'N/A'}...")
            elif is_image and attachment.url:
                # 분석 데이터가 없는 이미지 - 직접 분석 필요
                image_attachments_without_data.append(attachment)
                logger.info(f"Image without extracted data, will analyze directly: {attachment.name}")

        # 분석 데이터 없는 이미지가 있으면 직접 분석 시도
        if image_attachments_without_data:
            for attachment in image_attachments_without_data:
                try:
                    # URL에서 파일 경로 추출 시도 (프로젝트 루트 기준)
                    file_path = None
                    project_root = Path(__file__).parent.parent.parent.parent.parent
                    if attachment.url and attachment.url.startswith("/uploads/"):
                        file_path = project_root / attachment.url.lstrip("/")
                        logger.info(f"[CHAT_DEBUG] Resolved file path: {file_path}, exists: {file_path.exists()}")
                    elif attachment.url and attachment.url.startswith("data:"):
                        # base64 데이터인 경우 - 임시 파일로 저장 후 분석
                        import tempfile
                        parts = attachment.url.split(",", 1)
                        if len(parts) == 2:
                            image_bytes = base64.b64decode(parts[1])
                            ext = ".jpg"
                            if "png" in parts[0]:
                                ext = ".png"
                            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                                tmp.write(image_bytes)
                                file_path = Path(tmp.name)

                    if file_path and file_path.exists():
                        logger.info(f"Directly analyzing image: {file_path}")
                        analysis_result = await ImageAnalyzer.analyze_image(file_path)
                        if analysis_result.get("status") == "success":
                            # 자연어 견적 요청문 사용
                            estimate_request = analysis_result.get("estimate_request", "")
                            attachment_context.append({
                                "file_name": attachment.name,
                                "file_type": attachment.type,
                                "estimate_request": estimate_request,  # 자연어 요청문
                                "rag_entry_id": analysis_result.get("rag_entry_id"),
                            })
                            logger.info(f"Direct image analysis successful: {attachment.name} -> {estimate_request[:100]}...")
                        else:
                            logger.warning(f"Direct image analysis failed: {analysis_result.get('error')}")
                except Exception as e:
                    logger.warning(f"Failed to analyze image directly: {e}")

        # 메시지에 첨부파일 컨텍스트 추가
        enhanced_message = request.message
        if attachment_context:
            # 자연어 견적 요청문이 있으면 직접 메시지로 사용
            estimate_requests = [ctx.get('estimate_request', '') for ctx in attachment_context if ctx.get('estimate_request')]
            if estimate_requests:
                # 이미지 분석 결과를 직접 견적 요청으로 사용
                combined_request = " ".join(estimate_requests)
                if request.message.strip() in ["견적해줘", "견적 해줘", "견적", "이 도면으로 견적해줘", ""]:
                    # 사용자 메시지가 단순 요청이면 분석 결과를 직접 사용
                    enhanced_message = combined_request
                else:
                    # 사용자가 추가 요청사항을 적었으면 함께 포함
                    enhanced_message = f"{combined_request} {request.message}"
                logger.info(f"Using natural language estimate request: {enhanced_message[:100]}...")
            else:
                # 기존 방식 (백워드 호환)
                context_str = "\n\n[첨부파일 분석 결과]\n"
                for ctx in attachment_context:
                    context_str += f"- 파일: {ctx['file_name']}\n"
                    if ctx.get('estimate_request'):
                        context_str += f"  견적 요청: {ctx['estimate_request']}\n"
                enhanced_message = f"{request.message}\n{context_str}"
            logger.info(f"Enhanced message with {len(attachment_context)} attachment(s) context")
        elif image_attachments_without_data:
            # 이미지는 있지만 분석 실패 - 메시지에 표시
            context_str = "\n\n[첨부파일 정보]\n"
            for att in image_attachments_without_data:
                context_str += f"- 이미지 파일: {att.name} (분석 대기중)\n"
            enhanced_message = f"{request.message}\n{context_str}"
            logger.info(f"Added {len(image_attachments_without_data)} unanalyzed image(s) to message")

        # 자연어 파싱
        intent = NLPParser.parse(enhanced_message)
        logger.info(f"AI Manager - Parsed intent: {intent.intent} (confidence: {intent.confidence})")

        # 이미지 첨부 + 견적 관련 키워드가 있으면 estimate 의도로 강제
        estimate_keywords = ["견적", "분전반", "차단기", "브레이커", "외함", "메인", "분기", "quote", "estimate"]
        has_image = bool(attachment_context) or bool(image_attachments_without_data)
        has_estimate_keyword = any(kw in request.message.lower() for kw in estimate_keywords)

        if has_image and has_estimate_keyword and intent.intent not in ["estimate", "drawing"]:
            logger.info(f"Forcing intent to 'estimate' due to image attachment + keyword match")
            from kis_estimator_core.api.routes.ai_chat import ParsedIntent
            intent = ParsedIntent(
                intent="estimate",
                confidence=0.9,
                params=intent.params
            )

        # 수정/변경 키워드 + 최근 견적 컨텍스트 → estimate 인텐트 강제
        modify_keywords = ["수정", "변경", "고쳐", "바꿔", "다시", "틀렸", "잘못"]
        has_modify_keyword = any(kw in request.message.lower() for kw in modify_keywords)
        has_recent_estimate = any(
            msg.get("role") == "assistant" and (
                "견적" in msg.get("content", "") or
                "분전반" in msg.get("content", "") or
                "소계" in msg.get("content", "")
            )
            for msg in recent_messages[-5:]
        ) if recent_messages else False

        if has_modify_keyword and has_recent_estimate and intent.intent in ("conversation", "unknown"):
            logger.info(f"Forcing intent to 'estimate' due to modify keyword + recent estimate context")
            from kis_estimator_core.api.routes.ai_chat import ParsedIntent
            intent = ParsedIntent(
                intent="estimate",
                confidence=0.85,
                params=intent.params
            )

        # 응답 생성 (대화 컨텍스트 포함)
        # conversation/unknown 의도인 경우 대화 컨텍스트를 Claude API에 직접 전달
        if intent.intent in ("conversation", "unknown") and recent_messages:
            chat_response = await _generate_with_context(intent, enhanced_message, recent_messages)
        else:
            # 기존 ai_chat 로직 재사용 (견적, 도면, ERP 등) - recent_messages 전달
            chat_response = await ResponseGenerator.generate(intent, enhanced_message, recent_messages)

        # 시각화 데이터 생성
        visualizations = []
        if chat_response.action_result:
            visualizations = VisualizationGenerator.from_action_result(chat_response.action_result)

        # 명령 추출
        command = None
        if chat_response.action_result:
            parsed_command = CommandParser.parse(
                request.message,
                intent.intent,
                intent.params
            )
            if parsed_command:
                parsed_command.status = "success" if chat_response.action_result.get("status") == "success" else "error"
                parsed_command.result = chat_response.action_result
                if parsed_command.status == "error":
                    parsed_command.errorMessage = chat_response.action_result.get("error")
                command = parsed_command

        # 대화 쌍 SSOT에 저장 (ConversationMemoryService)
        try:
            memory_svc = get_memory_service()
            await memory_svc.save_conversation_pair(request.message, chat_response.message)
        except Exception as save_err:
            logger.warning(f"Failed to save conversation pair to SSOT: {save_err}")

        return AIManagerChatResponse(
            message=chat_response.message,
            visualizations=visualizations,
            command=command,
            suggestions=chat_response.suggestions,
            timestamp=chat_response.timestamp,
        )

    except Exception as e:
        logger.error(f"AI Manager chat error: {e}", exc_info=True)
        return AIManagerChatResponse(
            message=f"죄송합니다. 요청 처리 중 오류가 발생했습니다: {str(e)}",
            visualizations=[],
            command=None,
            suggestions=["도움말", "다시 시도"],
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
) -> UploadResponse:
    """
    파일 업로드 API

    지원 형식:
    - 이미지: PNG, JPG, JPEG, GIF
    - 문서: PDF, XLSX, XLS, CSV, DOC, DOCX, TXT
    - 도면: DWG, DXF
    """
    try:
        # 파일 크기 제한 (10MB)
        max_size = 10 * 1024 * 1024
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail="파일 크기가 10MB를 초과합니다."
            )

        # 파일 저장 경로 (프로젝트 루트 기준 절대 경로)
        # Railway에서 cd src && uvicorn으로 실행되므로 __file__ 기준으로 루트 찾기
        project_root = Path(__file__).parent.parent.parent.parent.parent
        upload_dir = project_root / "uploads" / datetime.now().strftime("%Y%m%d")
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[UPLOAD] Saving to: {upload_dir}")

        file_id = uuid.uuid4().hex[:12]
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        file_name = f"{file_id}{file_ext}"
        file_path = upload_dir / file_name

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File uploaded: {file_name} ({len(content)} bytes)")

        # OCR/데이터 추출 (이미지인 경우 Vision API 사용)
        extracted_data = None
        if file.content_type and file.content_type.startswith("image/"):
            # 이미지 분석 - Claude Vision API 사용 (자연어 출력)
            logger.info(f"Analyzing image with Vision API: {file_path}")
            analysis_result = await ImageAnalyzer.analyze_image(file_path)
            if analysis_result.get("status") == "success":
                # 자연어 견적 요청문 반환 (RAG 학습 지원)
                extracted_data = {
                    "analysis_status": "completed",
                    "estimate_request": analysis_result.get("estimate_request", ""),  # 자연어 견적 요청문
                    "analysis_type": analysis_result.get("analysis_type", "vision_natural_language"),
                    "rag_entry_id": analysis_result.get("rag_entry_id"),  # RAG 학습 엔트리 ID
                    "rag_reference": analysis_result.get("rag_reference"),  # 유사 이미지 참조
                }
                logger.info(f"Vision analysis completed: {analysis_result.get('estimate_request', '')[:100]}...")
            else:
                extracted_data = {
                    "analysis_status": "error",
                    "error": analysis_result.get("error", "Unknown error"),
                }
        elif file_ext in [".xlsx", ".xls", ".csv"]:
            # Excel/CSV 파싱 (향후 구현)
            extracted_data = {"parse_status": "pending"}

        return UploadResponse(
            id=file_id,
            name=file.filename or file_name,
            type=file.content_type or "application/octet-stream",
            size=len(content),
            url=f"/uploads/{datetime.now().strftime('%Y%m%d')}/{file_name}",
            extractedData=extracted_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions(limit: int = 20):
    """
    채팅 세션 목록 조회 - 현재 대화 메모리 기반

    Returns:
        세션 정보 및 최근 대화 요약
    """
    try:
        messages = await load_conversation_memory()
        session_state = get_session_state()

        # 현재 세션 정보 구성
        current_session = {
            "id": "current",
            "title": session_state.get("current_project") or "현재 대화",
            "message_count": len(messages),
            "last_message": messages[-1]["content"][:100] if messages else None,
            "created_at": session_state.get("created_at"),
            "updated_at": session_state.get("updated_at"),
        }

        return {
            "sessions": [current_session] if messages else [],
            "total": 1 if messages else 0,
            "limit": limit,
            "current_session": current_session if messages else None,
        }

    except Exception as e:
        logger.error(f"Session list error: {e}")
        return {
            "sessions": [],
            "total": 0,
            "limit": limit,
            "error": str(e),
        }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    특정 세션 조회 - 대화 메모리에서 메시지 로드

    Args:
        session_id: 세션 ID (현재는 "current"만 지원)

    Returns:
        세션 메시지 목록 및 상태
    """
    try:
        messages = await load_conversation_memory()
        session_state = get_session_state()

        return {
            "session_id": session_id,
            "messages": messages,
            "message_count": len(messages),
            "state": session_state,
        }

    except Exception as e:
        logger.error(f"Session get error: {e}")
        return {
            "session_id": session_id,
            "messages": [],
            "error": str(e),
        }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    세션 삭제 - 대화 메모리 초기화

    Args:
        session_id: 세션 ID (현재는 "current"만 지원)

    Returns:
        삭제 결과
    """
    try:
        success = clear_conversation_memory()

        return {
            "session_id": session_id,
            "deleted": success,
            "message": "대화 기록이 초기화되었습니다." if success else "초기화 실패",
        }

    except Exception as e:
        logger.error(f"Session delete error: {e}")
        return {
            "session_id": session_id,
            "deleted": False,
            "error": str(e),
        }


@router.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """
    세션 대화 초기화 (새 대화 시작)

    Args:
        session_id: 세션 ID

    Returns:
        초기화 결과
    """
    try:
        success = clear_conversation_memory()

        return {
            "session_id": session_id,
            "cleared": success,
            "message": "새 대화가 시작되었습니다. 대표님, 무엇을 도와드릴까요?" if success else "초기화 실패",
        }

    except Exception as e:
        logger.error(f"Session clear error: {e}")
        return {
            "session_id": session_id,
            "cleared": False,
            "error": str(e),
        }
