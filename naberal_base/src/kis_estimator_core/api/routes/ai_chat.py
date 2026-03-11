"""
AI Chat API Router
자연어 기반 견적/도면/이메일/ERP 통합 처리 + RAG 지식 검색

기능:
- 자연어 입력 파싱 (Claude Sonnet API 우선)
- 의도 분류 (견적, 도면, 이메일, ERP, 지식검색)
- 파라미터 추출
- RAG 기반 지식 검색 및 응답 생성
- 해당 서비스 호출 (도면 생성 포함)
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Literal

# .env 파일 로드 (프로젝트 루트에서)
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parents[4]  # api/routes -> api -> kis_estimator_core -> src -> project root
_env_path = _project_root / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

import anthropic

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 상대 import 사용 - 모듈 싱글톤 공유를 위해 필수
from ...services.drawing_service import DrawingService
from ...services.email_service import get_email_service
from ...services.erp_service import get_erp_service
from ...services.estimate_parser_service import (
    get_estimate_parser_service,
    ParsedEstimateRequest,
)
from ...core.ssot.constants import (
    AI_MODELS,
    BREAKER_MODEL_KEYWORDS,
    ACCESSORY_EXCLUDE_KEYWORDS,
)
from ...engine.fix4_pipeline import get_pipeline
from ..schemas.estimates import (
    EstimateRequest,
    BreakerInput,
    EnclosureInput,
    PanelInput,
    EstimateOptions,
)

# RAG 학습 서비스 import
from kis_estimator_core.rag.learner import get_learner, LearningCategory

# AI 지식 서비스 import
from kis_estimator_core.services.ai_knowledge_service import (
    get_estimate_system_prompt,
    get_cached_knowledge,
    load_conversation_memory,
    save_conversation_memory,
    get_session_state,
    save_session_state,
)

logger = logging.getLogger(__name__)

# 도면 서비스 싱글톤
_drawing_service: DrawingService | None = None

def get_drawing_service() -> DrawingService:
    """DrawingService 싱글톤"""
    global _drawing_service
    if _drawing_service is None:
        _drawing_service = DrawingService()
    return _drawing_service

router = APIRouter()

# RAG 시스템 연동 (선택적)
_rag_retriever = None

def get_rag_retriever():
    """RAG Retriever 싱글톤 (지연 초기화)"""
    global _rag_retriever
    if _rag_retriever is None:
        try:
            from kis_estimator_core.rag.config import RAGConfig
            from kis_estimator_core.rag.retriever import HybridRetriever
            config = RAGConfig()
            _rag_retriever = HybridRetriever(config)
            logger.info("RAG retriever initialized for AI chat")
        except ImportError as e:
            logger.warning(f"RAG system not available: {e}")
            _rag_retriever = None
        except Exception as e:
            logger.warning(f"RAG initialization failed: {e}")
            _rag_retriever = None
    return _rag_retriever


# Claude 클라이언트 싱글톤
_claude_client: anthropic.Anthropic | None = None

def get_claude_client() -> anthropic.Anthropic | None:
    """Claude API 클라이언트 싱글톤 (지연 초기화)"""
    global _claude_client
    if _claude_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                _claude_client = anthropic.Anthropic(api_key=api_key)
                logger.info("Claude API client initialized successfully")
            except Exception as e:
                logger.warning(f"Claude API initialization failed: {e}")
                _claude_client = None
        else:
            logger.warning("ANTHROPIC_API_KEY not found in environment")
    return _claude_client


# ===== AI 모델 타입 =====
# AI_MODELS는 core/ssot/constants.py에서 import됨


# ===== 스키마 정의 =====
class FileAttachment(BaseModel):
    """첨부파일 정보"""
    id: str = Field(..., description="첨부파일 ID")
    name: str = Field(..., description="파일명")
    type: str = Field(..., description="MIME 타입")
    url: str | None = Field(default=None, description="파일 URL (base64 또는 URL)")
    extractedData: dict | None = Field(default=None, description="추출된 데이터")


class ChatMessage(BaseModel):
    """채팅 메시지 (프론트엔드 호환)"""
    role: str = Field(..., description="메시지 역할 (user, assistant, system)")
    content: str = Field(..., description="메시지 내용")
    timestamp: str | None = Field(default=None, description="타임스탬프")


class ChatRequest(BaseModel):
    """AI 채팅 요청 (프론트엔드 messages[] 형식과 호환)"""
    # 프론트엔드 형식: messages 배열
    messages: list[ChatMessage] | None = Field(default=None, description="메시지 배열 (프론트엔드 호환)")
    # 백엔드 레거시 형식: 단일 message
    message: str | None = Field(default=None, max_length=2000, description="사용자 메시지 (레거시)")
    model: str = Field(default="claude-opus", description="사용할 AI 모델 (claude-opus, gemini-pro, gpt-thinking)")
    context: dict | None = Field(default=None, description="이전 대화 컨텍스트")
    attachments: list[FileAttachment] | None = Field(default=None, description="첨부파일 목록 (이미지 등)")
    options: dict | None = Field(default=None, description="추가 옵션 (프론트엔드 호환)")

    def get_user_message(self) -> str:
        """사용자 메시지 추출 (두 형식 모두 지원)"""
        # messages 배열에서 마지막 user 메시지 추출
        if self.messages:
            for msg in reversed(self.messages):
                if msg.role == "user":
                    return msg.content
            # user 메시지 없으면 마지막 메시지 사용
            if self.messages:
                return self.messages[-1].content
        # 레거시 message 필드 사용
        if self.message:
            return self.message
        return ""


class ParsedIntent(BaseModel):
    """파싱된 의도"""
    intent: Literal["estimate", "drawing", "email", "erp", "calendar", "help", "knowledge", "conversation", "image_analysis", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    params: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """AI 채팅 응답"""
    message: str = Field(..., description="응답 메시지")
    intent: ParsedIntent
    model: str = Field(default="claude-opus", description="사용된 AI 모델")
    model_info: dict | None = Field(default=None, description="모델 정보")
    action_result: dict | None = Field(default=None, description="액션 실행 결과")
    suggestions: list[str] = Field(default_factory=list, description="후속 제안")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== 자연어 파싱 =====
class NLPParser:
    """자연어 파싱 엔진"""

    # 키워드 매핑
    INTENT_KEYWORDS = {
        "estimate": ["견적", "분전반", "차단기", "외함", "브레이커", "quote"],
        "drawing": ["도면", "단선", "결선도", "배치도", "외형도", "drawing"],
        "email": ["이메일", "메일", "발송", "전송", "보내", "email"],
        "erp": ["erp", "발주", "재고", "주문", "order", "inventory", "stock", "cancel", "query", "취소", "조회"],
        "calendar": ["일정", "캘린더", "스케줄", "납품", "미팅", "회의", "약속", "schedule", "calendar", "event"],
        "help": ["도움", "help", "사용법", "명령어", "안내"],
        "knowledge": ["알려줘", "뭐야", "설명", "규칙", "공식", "치수", "가격", "단가",
                      "스펙", "사양", "어떻게", "무엇", "왜", "정보", "검색"],
    }

    # 도면 종류 매핑
    DRAWING_TYPES = {
        "wiring": ["단선", "결선도", "단선결선도", "wiring"],
        "enclosure": ["외함", "외형도", "외함외형도", "enclosure"],
        "placement": ["배치도", "배치", "placement"],
        "all": ["전체", "모두", "all"],
    }

    # 이메일 정규식
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    # 브랜드 매핑
    BRANDS = {
        "상도": "상도차단기",
        "ls": "LS차단기",
        "LS": "LS차단기",
        "한국산업": "한국산업",
    }

    # 외함 종류
    ENCLOSURE_TYPES = [
        "옥내노출", "옥외노출", "옥내자립", "옥외자립",
        "전주부착형", "FRP함", "하이박스", "매입함"
    ]

    # ERP 작업 유형
    ERP_OPERATIONS = {
        "order": ["발주", "등록", "주문", "order"],
        "inventory": ["재고", "확인", "stock", "inventory"],
        "query": ["조회", "내역", "리스트", "목록", "query"],
        "cancel": ["취소", "cancel"],
    }

    # 캘린더 작업 유형
    CALENDAR_OPERATIONS = {
        "create": ["추가", "등록", "생성", "만들", "잡아", "create", "add"],
        "list": ["목록", "조회", "확인", "보여줘", "list", "show"],
        "update": ["수정", "변경", "update", "modify"],
        "delete": ["삭제", "취소", "remove", "delete"],
        "upcoming": ["다가오는", "예정", "upcoming", "today", "오늘"],
    }

    # Claude API 파싱용 시스템 프롬프트
    CLAUDE_SYSTEM_PROMPT = """당신은 전기 분전반 견적 시스템의 자연어 파싱 엔진입니다.
사용자의 자연어 입력을 분석하여 의도(intent)와 파라미터를 JSON 형식으로 추출합니다.

★★★ 중요: 이전 대화 맥락을 반드시 고려하세요 ★★★
사용자가 이전에 파일(도면, 이미지 등)을 첨부했다면, 후속 질문은 그 파일에 대한 것입니다.
예: 이전에 "도면8.jpg 업로드" → 다음 "거래처명 찾아봐" = 도면에서 거래처명 찾기 (image_analysis)
예: 이전에 "이 견적서 파일" → 다음 "가격 확인해봐" = 파일에서 정보 추출 (image_analysis)

가능한 intent 종류:
- estimate: 견적서 생성 요청 (분전반, 차단기, 외함 관련) - 새로운 견적 생성만 해당
- drawing: 도면 생성 요청 (단선결선도, 배치도, 외형도)
- email: 이메일 발송 요청
- erp: ERP 관련 요청 (발주, 재고, 조회)
- calendar: 일정 관리 요청 (일정 추가, 조회, 수정, 삭제, 납품일정, 미팅, 회의)
  * "일정 추가해줘", "내일 일정 보여줘", "납품 일정 등록", "다가오는 일정"
- help: 도움말/사용법 요청
- knowledge: 지식/정보 질문 (차단기 치수, 가격, 공식 등 기술적 질문)
- image_analysis: 첨부파일(이미지/도면/문서)에서 정보 추출 요청
  * "거래처명 찾아줘", "업체명 뭐야?", "파일에서 XX 확인해줘"
  * 이전 대화에 파일 첨부가 있고 후속 질문이 정보 추출인 경우
- conversation: 일반 대화 및 업무 지원 (인사, 잡담, 안부, 호텔 검색, 비품 구매, 정보 검색, 일상 대화 전부)
- unknown: 분류 불가 (거의 사용하지 않음)

중요 규칙:
1. 이전 대화에 파일 첨부가 있고, 현재 요청이 "찾아봐", "확인해", "알려줘" 등이면 → image_analysis
2. 비즈니스 키워드(견적, 도면, 이메일, ERP, 지식검색)가 없는 일반적인 대화 → conversation
3. 분류가 애매하면 "conversation"으로 분류. unknown은 정말 해석 불가능한 경우에만 사용.
4. ★★★ 이미지 분석 결과에 차단기/외함/분전반 정보가 포함된 경우:
   - 사용자가 "견적" 키워드를 명시하지 않아도 → estimate 의도로 분류
   - 도면/스펙시트 이미지를 보냈다는 것 자체가 견적 요청 의도
   - 이미지 분석 결과에서 main_breaker, branch_breakers 등을 params로 추출

예: "안녕", "오늘 기분이 어때", "뭐해?", "고마워" → conversation
예: "출장 갈 때 호텔 추천해줘", "비품 구매 조언해줘" → conversation
예: "4P 100A 견적해줘", "SBE-104 치수 알려줘" → estimate, knowledge
예: [이전에 도면 첨부 후] "거래처명 찾아봐" → image_analysis
예: [이전에 파일 첨부 후] "이 파일에서 가격 확인해줘" → image_analysis
예: [이미지 분석 결과에 MCCB MAIN 4P 50AF 30AT, 분기 2P 30AF 20AT x8 포함] → estimate (도면=견적 의도)
예: "[이미지 분석 결과]...메인 차단기: MCCB 4P 50AF..." → estimate (견적 키워드 없어도 견적 의도)

━━━ ⚠️ 최우선 규칙: 차단기 전수검사 (CRITICAL — 이것을 틀리면 견적 대형사고) ━━━
도면/이미지에서 차단기를 추출할 때, 모든 차단기를 반드시 하나하나 개별적으로 확인하세요.
- 절대로 "같은 모델이니까 암페어도 같겠지"라고 추측하지 마세요
- 같은 2P ELB라도 20A가 10개, 30A가 8개일 수 있습니다 → 반드시 별도 항목으로 분리
- 같은 4P라도 MCCB 4P 100A 1개, ELB(CBR) 4P 30A 1개일 수 있습니다
- 각 차단기마다 MCCB/ELB 구분, 극수, 프레임, 암페어를 정확히 확인
- 암페어가 다른 차단기를 하나로 합치면 절대 안 됨
- ⚠️ 80A는 존재하지 않음! 80A로 읽히면 반드시 75A로 변환 (업계 표준: 80A → 75A)
- ⚠️ CBR = ELB = ELCB — 모두 동일한 누전차단기. 도면에 CBR/ELCB로 표기되어도 ELB로 통일
- ⚠️ 1분전반 1브랜드 원칙: 하나의 분전반에 2개 이상의 차단기 브랜드 혼용 금지 (상도면 상도만, LS면 LS만)
- ⚠️ SP(예비)도 반드시 차단기 수량에 포함! 예비도 실물 차단기임
- 취소된 항목(WHM 취소, SPD 취소 등)은 해당 차단기도 함께 제외

━━━ 도면 스펙 읽는 법 ━━━
"CBR 2P 30/20AT 2.5KA" → ELB 2P, 30AF 프레임, 20A 정격전류, 2.5KA 차단용량
"MCCB 4P 225/200AT 25KA" → MCCB 4P, 225AF 프레임, 200A 정격전류, 25KA 차단용량
"MCCB 4P 100/80AT" → 80A는 없으므로 75A로 변환!
읽는 순서: MAIN → 좌측열 위→아래 → 우측열 위→아래 (각 행 = 차단기 1개)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

견적 요청(estimate)의 파라미터 추출 규칙:
- main_breaker: 메인 차단기 정보 (poles: 극수 2/3/4, current: 암페어, breaker_type: MCCB/ELB)
- branch_breakers: 분기 차단기 배열 [{poles, current, breaker_type, quantity}]
  ★★★ 핵심: 암페어가 다른 차단기는 반드시 별도 항목으로 분리! ★★★
  ★ 중요: quantity(수량)는 "N개", "N대", "NEA" 형식에서 정확히 추출해야 합니다.
  예: "8개" → quantity: 8, "5개" → quantity: 5, "10개" → quantity: 10
  예: 2P 20A 10개 + 2P 30A 8개 → 반드시 2개의 별도 항목으로 분리
- enclosure_type: 외함 종류 (옥내노출, 옥외노출, 옥내자립, 옥외자립, 매입함 등)
  ★ 자립형(옥내자립/옥외자립): 베이스 높이(기본 200mm)를 외함H에 더해 총 높이로 평수계산
  예: 외함 600×700×150 + 베이스 200 → 600×900×150으로 주문제작함 단가 산출
- enclosure_material: 외함 재질 (STEEL 1.6T, SUS201 1.2T 등)
- brand: 차단기 브랜드 (상도차단기, LS차단기 등)
- customer_name: 고객명
- project_name: 프로젝트명

=== 예시 1: 기본 견적 ===
입력: "상도 4P 100A 메인, 분기 ELB 3P 30A 5개로 견적해줘"
출력:
{
  "intent": "estimate",
  "confidence": 0.95,
  "params": {
    "brand": "상도차단기",
    "main_breaker": {"poles": 4, "current": 100, "breaker_type": "MCCB"},
    "branch_breakers": [{"poles": 3, "current": 30, "breaker_type": "ELB", "quantity": 5}],
    "enclosure_type": "옥내노출",
    "enclosure_material": "STEEL 1.6T"
  }
}

=== 예시 2: 소형 차단기(2P 20A/30A) ===
입력: "상도 4P 100A 메인, 분기 ELB 2P 20A 8개로 견적해줘"
출력:
{
  "intent": "estimate",
  "confidence": 0.95,
  "params": {
    "brand": "상도차단기",
    "main_breaker": {"poles": 4, "current": 100, "breaker_type": "MCCB"},
    "branch_breakers": [{"poles": 2, "current": 20, "breaker_type": "ELB", "quantity": 8}],
    "enclosure_type": "옥내노출",
    "enclosure_material": "STEEL 1.6T"
  }
}

=== 예시 3: 복수 분기 타입 ===
입력: "LS 3P 200A 메인, 분기 ELB 3P 30A 10개, MCCB 3P 50A 3개"
출력:
{
  "intent": "estimate",
  "confidence": 0.95,
  "params": {
    "brand": "LS차단기",
    "main_breaker": {"poles": 3, "current": 200, "breaker_type": "MCCB"},
    "branch_breakers": [
      {"poles": 3, "current": 30, "breaker_type": "ELB", "quantity": 10},
      {"poles": 3, "current": 50, "breaker_type": "MCCB", "quantity": 3}
    ],
    "enclosure_type": "옥내노출",
    "enclosure_material": "STEEL 1.6T"
  }
}

반드시 유효한 JSON만 출력하세요. 설명이나 추가 텍스트 없이 JSON만 출력합니다."""

    @classmethod
    def parse_with_claude(cls, text: str, context: dict | None = None, attachments: list | None = None) -> ParsedIntent | None:
        """Claude Sonnet API를 사용하여 자연어 파싱 (우선 사용)

        Args:
            text: 현재 사용자 메시지
            context: 이전 대화 컨텍스트 (recentMessages, currentVisualization 등)
            attachments: 현재 요청의 첨부파일 목록
        """
        client = get_claude_client()
        if client is None:
            logger.warning("Claude client not available, falling back to rule-based parsing")
            return None

        try:
            # 대화 맥락 구성
            messages = []

            # 이전 대화 히스토리 추가 (context에서 recentMessages 추출)
            if context and context.get("recentMessages"):
                recent_msgs = context.get("recentMessages", [])
                for msg in recent_msgs[-30:]:  # 최근 30개까지 (긴 대화 연속성 지원)
                    role = "user" if msg.get("role") == "user" else "assistant"
                    content = msg.get("content", "")
                    # 첨부파일 정보 포함
                    if msg.get("attachments"):
                        attachments_info = ", ".join([f"{att.get('name', 'file')}" for att in msg.get("attachments", [])])
                        content = f"[첨부파일: {attachments_info}]\n{content}"
                    if content:
                        messages.append({"role": role, "content": content})

            # 현재 메시지 구성 (첨부파일 정보 포함)
            current_content = text
            if attachments:
                attachments_info = ", ".join([att.name if hasattr(att, 'name') else str(att.get('name', 'file')) for att in attachments])
                current_content = f"[현재 첨부파일: {attachments_info}]\n{text}"

            messages.append({"role": "user", "content": current_content})

            logger.debug(f"Claude parsing with {len(messages)} messages, context: {bool(context)}, attachments: {bool(attachments)}")

            response = client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                system=cls.CLAUDE_SYSTEM_PROMPT,
                messages=messages
            )

            # 응답 텍스트 추출
            response_text = response.content[0].text.strip()
            logger.debug(f"Claude response: {response_text}")

            # JSON 파싱
            # JSON 블록이 있으면 추출
            if "```json" in response_text:
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            elif "```" in response_text:
                json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

            parsed = json.loads(response_text)

            # ParsedIntent 객체 생성
            intent = parsed.get("intent", "conversation")
            confidence = parsed.get("confidence", 0.9)
            params = parsed.get("params", {})

            # intent 유효성 검사
            valid_intents = ["estimate", "drawing", "email", "erp", "calendar", "help", "knowledge", "conversation", "image_analysis", "unknown"]
            if intent not in valid_intents:
                intent = "conversation"

            logger.info(f"Claude parsed intent: {intent} with confidence {confidence}")
            return ParsedIntent(
                intent=intent,
                confidence=confidence,
                params=params
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Claude response as JSON: {e}")
            return None
        except anthropic.APIError as e:
            logger.warning(f"Claude API error: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error in Claude parsing: {e}")
            return None

    @classmethod
    def parse(cls, text: str, context: dict | None = None, attachments: list | None = None) -> ParsedIntent:
        """자연어 텍스트를 의도와 파라미터로 파싱 (Claude 우선, 폴백으로 키워드 기반)

        Args:
            text: 현재 사용자 메시지
            context: 이전 대화 컨텍스트 (recentMessages, currentVisualization 등)
            attachments: 현재 요청의 첨부파일 목록
        """
        # Claude API 우선 시도 (context와 attachments 전달)
        claude_result = cls.parse_with_claude(text, context, attachments)
        if claude_result is not None:
            logger.info(f"Using Claude parsing result: {claude_result.intent}")
            return claude_result

        # Claude 실패 시 키워드 기반 폴백
        logger.info("Falling back to keyword-based parsing")
        lower_text = text.lower()
        params = {}

        # 의도 분류 (우선순위 기반)
        intent = "unknown"
        confidence = 0.0

        # 이메일 주소 패턴이 있으면 email 의도 우선 처리
        has_email_address = bool(re.search(cls.EMAIL_PATTERN, text))
        has_email_keywords = any(kw in lower_text for kw in ["발송", "전송", "보내", "메일"])

        if has_email_address and has_email_keywords:
            intent = "email"
            confidence = 0.85
        else:
            # 일반 키워드 기반 의도 분류
            for intent_name, keywords in cls.INTENT_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in lower_text:
                        intent = intent_name
                        confidence = 0.8
                        break
                if intent != "unknown":
                    break

        # 파라미터 추출 (의도별)
        if intent == "estimate":
            params = cls._extract_estimate_params(text)
            if params:
                confidence = min(0.95, confidence + len(params) * 0.05)
        elif intent == "drawing":
            params = cls._extract_drawing_params(text)
            if params:
                confidence = min(0.95, confidence + len(params) * 0.05)
        elif intent == "email":
            params = cls._extract_email_params(text)
            if params:
                confidence = min(0.95, confidence + len(params) * 0.05)
        elif intent == "erp":
            params = cls._extract_erp_params(text)
            if params:
                confidence = min(0.95, confidence + len(params) * 0.05)
        elif intent == "calendar":
            params = cls._extract_calendar_params(text)
            if params:
                confidence = min(0.95, confidence + len(params) * 0.05)

        return ParsedIntent(
            intent=intent,
            confidence=confidence,
            params=params
        )

    @classmethod
    def _extract_drawing_params(cls, text: str) -> dict:
        """도면 파라미터 추출"""
        params = {}

        # 견적 ID 추출 (EST-YYYYMMDDHHMMSS 형식)
        estimate_match = re.search(r'EST-(\d{14}|\d{8})', text, re.IGNORECASE)
        if estimate_match:
            params["estimate_id"] = estimate_match.group(0).upper()

        # 도면 종류 추출
        lower_text = text.lower()
        for drawing_type, keywords in cls.DRAWING_TYPES.items():
            for keyword in keywords:
                if keyword in lower_text:
                    params["drawing_type"] = drawing_type
                    break
            if "drawing_type" in params:
                break

        # 기본값: 전체 도면
        if "drawing_type" not in params:
            params["drawing_type"] = "all"

        return params

    @classmethod
    def _extract_email_params(cls, text: str) -> dict:
        """이메일 파라미터 추출"""
        params = {}

        # 이메일 주소 추출
        email_match = re.search(cls.EMAIL_PATTERN, text)
        if email_match:
            params["to"] = email_match.group(0)

        # 견적 ID 추출 (EST-YYYYMMDDHHMMSS 형식)
        estimate_match = re.search(r'EST-(\d{14}|\d{8})', text, re.IGNORECASE)
        if estimate_match:
            params["estimate_id"] = estimate_match.group(0).upper()

        # 고객명 추출 (XX님, XX고객)
        customer_match = re.search(r'([가-힣]+)\s*(님|고객|업체)', text)
        if customer_match:
            params["customer_name"] = customer_match.group(1)

        return params

    @classmethod
    def _extract_calendar_params(cls, text: str) -> dict:
        """캘린더 파라미터 추출"""
        params = {}
        lower_text = text.lower()

        # 작업 유형 추출 (우선순위: delete > update > create > upcoming > list)
        priority_order = ["delete", "update", "create", "upcoming", "list"]
        for op_type in priority_order:
            keywords = cls.CALENDAR_OPERATIONS.get(op_type, [])
            for keyword in keywords:
                if keyword in lower_text:
                    params["operation"] = op_type
                    break
            if "operation" in params:
                break

        # 기본값: 조회
        if "operation" not in params:
            params["operation"] = "list"

        # 날짜 추출 (YYYY-MM-DD, YYYY/MM/DD, MM월 DD일 등)
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2025-01-15, 2025/1/15
            r'(\d{1,2})월\s*(\d{1,2})일',        # 1월 15일
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                if '월' in pattern:
                    from datetime import datetime
                    month = int(date_match.group(1))
                    day = int(date_match.group(2))
                    year = datetime.now().year
                    params["date"] = f"{year}-{month:02d}-{day:02d}"
                else:
                    params["date"] = date_match.group(1).replace('/', '-')
                break

        # 시간 추출 (HH:MM, 오전/오후 X시)
        time_patterns = [
            r'(\d{1,2})[:\s시](\d{0,2})분?',  # 14:30, 14시 30분
            r'(오전|오후)\s*(\d{1,2})시',      # 오후 2시
        ]
        for pattern in time_patterns:
            time_match = re.search(pattern, text)
            if time_match:
                if '오전' in pattern or '오후' in pattern:
                    period = time_match.group(1)
                    hour = int(time_match.group(2))
                    if period == '오후' and hour < 12:
                        hour += 12
                    params["time"] = f"{hour:02d}:00"
                else:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    params["time"] = f"{hour:02d}:{minute:02d}"
                break

        # 일정 유형 추출
        if any(kw in lower_text for kw in ['납품', '배송', 'delivery']):
            params["event_type"] = "delivery"
        elif any(kw in lower_text for kw in ['미팅', '회의', '면담', 'meeting']):
            params["event_type"] = "meeting"
        elif any(kw in lower_text for kw in ['알림', '리마인더', 'reminder']):
            params["event_type"] = "reminder"
        else:
            params["event_type"] = "task"

        # 제목 추출 시도 (일정 뒤에 오는 내용)
        title_match = re.search(r'(일정|미팅|회의|납품|약속)[:\s]*([가-힣a-zA-Z0-9\s]+?)(?:에|을|를|$)', text)
        if title_match:
            params["title"] = title_match.group(2).strip()

        # 고객/거래처명 추출
        customer_match = re.search(r'([가-힣]+)\s*(님|고객|업체|회사)', text)
        if customer_match:
            params["customer"] = customer_match.group(1)

        return params

    @classmethod
    def _extract_erp_params(cls, text: str) -> dict:
        """ERP 파라미터 추출"""
        params = {}
        lower_text = text.lower()

        # ERP 작업 유형 추출 (우선순위: cancel > query > inventory > order)
        priority_order = ["cancel", "query", "inventory", "order"]
        for op_type in priority_order:
            keywords = cls.ERP_OPERATIONS.get(op_type, [])
            for keyword in keywords:
                if keyword in lower_text:
                    params["operation"] = op_type
                    break
            if "operation" in params:
                break

        # 기본값: 주문 조회
        if "operation" not in params:
            params["operation"] = "query"

        # 견적/주문 ID 추출
        estimate_match = re.search(r'EST-(\d{14}|\d{8})', text, re.IGNORECASE)
        if estimate_match:
            params["estimate_id"] = estimate_match.group(0).upper()

        order_match = re.search(r'ORD-(\d+)', text, re.IGNORECASE)
        if order_match:
            params["order_id"] = order_match.group(0).upper()

        # 품목 코드 추출 (SKU)
        sku_match = re.search(r'(SBE|SEE|ENC|ET|NT)-\w+', text, re.IGNORECASE)
        if sku_match:
            params["sku"] = sku_match.group(0).upper()

        # 카테고리 추출
        if "차단기" in text:
            params["category"] = "차단기"
        elif "외함" in text:
            params["category"] = "외함"
        elif "부속" in text or "자재" in text:
            params["category"] = "부속"

        # 고객명 추출
        customer_match = re.search(r'([가-힣]+)\s*(님|고객|업체)', text)
        if customer_match:
            params["customer_name"] = customer_match.group(1)

        return params

    @classmethod
    def _extract_estimate_params(cls, text: str) -> dict:
        """견적 파라미터 추출"""
        params = {}

        # 극수 추출 (2P, 3P, 4P, 2극, 3극, 4극)
        poles_match = re.search(r'(\d)\s*[Pp극]', text)
        if poles_match:
            params["poles"] = int(poles_match.group(1))

        # 암페어 추출 (100A, 100암페어, 100암)
        amp_match = re.search(r'(\d+)\s*[Aa암]', text)
        if amp_match:
            params["current"] = int(amp_match.group(1))

        # 프레임 추출 (100AF)
        frame_match = re.search(r'(\d+)\s*[Aa][Ff]', text)
        if frame_match:
            params["frame"] = int(frame_match.group(1))

        # 브랜드 추출
        for keyword, brand in cls.BRANDS.items():
            if keyword in text:
                params["brand"] = brand
                break

        # 외함 종류 추출
        for enc_type in cls.ENCLOSURE_TYPES:
            if enc_type in text:
                params["enclosure_type"] = enc_type
                break

        # 차단기 종류 추출
        if "누전" in text or "ELB" in text.upper():
            params["breaker_type"] = "ELB"
        elif "배선용" in text or "MCCB" in text.upper():
            params["breaker_type"] = "MCCB"

        # 수량 추출
        qty_match = re.search(r'(\d+)\s*(?:개|대|EA)', text, re.IGNORECASE)
        if qty_match:
            params["quantity"] = int(qty_match.group(1))

        # 메인/분기 구분
        if "메인" in text:
            params["is_main"] = True
        if "분기" in text:
            params["has_branch"] = True

        return params


# ===== Claude 파싱 결과 → EstimateRequest 변환 =====
def _convert_intent_params_to_estimate_request(params: dict) -> EstimateRequest | None:
    """
    Claude API로 파싱한 intent.params → EstimateRequest 변환

    Claude 파싱 결과 구조:
    {
        "brand": "상도차단기",
        "main_breaker": {"poles": 4, "current": 100, "breaker_type": "MCCB"},
        "branch_breakers": [{"poles": 3, "current": 30, "breaker_type": "ELB", "quantity": 5}],
        "enclosure_type": "옥내노출",
        "enclosure_material": "STEEL 1.6T"
    }
    """
    if not params:
        return None

    # 메인 차단기 변환
    main_breaker = None
    if params.get("main_breaker"):
        mb = params["main_breaker"]
        main_breaker = BreakerInput(
            breaker_type=mb.get("breaker_type", "MCCB"),
            ampere=mb.get("current", 100),
            poles=mb.get("poles", 4),
            quantity=1,
            model=None,
        )

    # 메인 차단기가 없으면 변환 불가
    if not main_breaker:
        return None

    # 분기 차단기 변환
    branch_breakers = []
    for br in params.get("branch_breakers", []):
        branch_breakers.append(BreakerInput(
            breaker_type=br.get("breaker_type", "ELB"),
            ampere=br.get("current", 30),
            poles=br.get("poles", 3),
            quantity=br.get("quantity", 1),
            model=None,
        ))

    # 외함 변환
    enc_type = params.get("enclosure_type", "옥내노출")
    enc_material = params.get("enclosure_material", "STEEL 1.6T")

    # 재질 포맷 보정
    if enc_material and "SUS201" in enc_material and "1.2T" not in enc_material:
        enc_material = "SUS201 1.2T"
    elif enc_material and "STEEL" in enc_material and "1.6" in enc_material and "1.6T" not in enc_material:
        enc_material = "STEEL 1.6T"
    elif enc_material and "STEEL" in enc_material and "1.0" in enc_material and "1.0T" not in enc_material:
        enc_material = "STEEL 1.0T"

    # enclosure_type → type 변환
    if enc_type == "전주부착":
        enc_type = "전주부착형"

    enclosure = EnclosureInput(
        type=enc_type,
        material=enc_material or "STEEL 1.6T",
        custom_size=None,
    )

    # 고객명
    customer_name = params.get("customer_name") or "AI매니저 견적"

    # PanelInput 생성 (비전 추출 panel_name 우선 사용)
    panel_name = params.get("panel_name") or "분전반"
    panel = PanelInput(
        panel_name=panel_name,
        main_breaker=main_breaker,
        branch_breakers=branch_breakers if branch_breakers else None,
        accessories=None,
        enclosure=enclosure,
    )

    # 브랜드 결정
    brand_pref = None
    brand = params.get("brand", "")
    if brand:
        br_brand = brand.upper()
        if "LS" in br_brand:
            brand_pref = "LS"
        else:
            brand_pref = "SANGDO"

    return EstimateRequest(
        customer_name=customer_name,
        project_name=params.get("project_name") or "AI매니저 프로젝트",
        panels=[panel],
        options=EstimateOptions(
            include_evidence_pack=False,
            breaker_brand_preference=brand_pref,
        ),
    )


# ===== 파싱 데이터 → EstimateRequest 변환 =====
def _convert_parsed_to_estimate_request(parsed: ParsedEstimateRequest) -> EstimateRequest:
    """
    ParsedEstimateRequest → EstimateRequest 변환

    AI 매니저에서 파싱한 자연어 견적 요청을 FIX-4 파이프라인용 스키마로 변환
    """
    # 메인 차단기 변환
    main_breaker = None
    if parsed.main_breaker:
        mb = parsed.main_breaker
        main_breaker = BreakerInput(
            breaker_type=mb.category,  # MCCB or ELB
            ampere=mb.current_a,
            poles=mb.poles,
            quantity=1,  # 메인은 항상 1개
            model=None,  # Backend에서 카탈로그 조회
        )
    else:
        # 메인차단기 미지정 시: 분기차단기 최대 암페어 기준으로 기본값 생성
        max_ampere = 100  # 기본값
        max_poles = 4
        if parsed.branch_breakers:
            max_ampere = max(br.current_a for br in parsed.branch_breakers)
            max_poles = max(br.poles for br in parsed.branch_breakers)
        # 메인은 분기 최대값보다 한 단계 이상 커야 함
        if max_ampere <= 50:
            main_ampere = 100
        elif max_ampere <= 100:
            main_ampere = 200
        elif max_ampere <= 200:
            main_ampere = 400
        else:
            main_ampere = 600
        main_breaker = BreakerInput(
            breaker_type="MCCB",
            ampere=main_ampere,
            poles=max_poles if max_poles >= 3 else 4,
            quantity=1,
            model=None,
        )

    # 분기 차단기 변환
    branch_breakers = []
    for br in parsed.branch_breakers:
        branch_breakers.append(BreakerInput(
            breaker_type=br.category,
            ampere=br.current_a,
            poles=br.poles,
            quantity=br.quantity,
            model=None,
        ))

    # 외함 변환
    enclosure = None
    if parsed.enclosure:
        enc = parsed.enclosure
        # 재질 포맷 보정 (STEEL 1.6T, SUS201 1.2T 등)
        material = enc.material
        if material and "SUS201" in material and "1.2T" not in material:
            material = "SUS201 1.2T"
        elif material and "STEEL" in material and "1.6" in material and "1.6T" not in material:
            material = "STEEL 1.6T"
        elif material and "STEEL" in material and "1.0" in material and "1.0T" not in material:
            material = "STEEL 1.0T"

        # enclosure_type → type 변환
        enc_type = enc.enclosure_type
        if enc_type == "전주부착":
            enc_type = "전주부착형"

        enclosure = EnclosureInput(
            type=enc_type,
            material=material or "STEEL 1.6T",
            custom_size=None,
        )
    else:
        # 외함 정보 없으면 기본값
        enclosure = EnclosureInput(
            type="옥내노출",
            material="STEEL 1.6T",
            custom_size=None,
        )

    # 고객명 결정
    customer_name = parsed.customer_name or "AI매니저 견적"

    # PanelInput 생성
    panel = PanelInput(
        panel_name="분전반",
        main_breaker=main_breaker,
        branch_breakers=branch_breakers if branch_breakers else None,
        accessories=None,
        enclosure=enclosure,
    )

    # 브랜드 결정 (메인 차단기에서 추출)
    brand_pref = None
    if parsed.main_breaker:
        br_brand = parsed.main_breaker.brand.upper() if parsed.main_breaker.brand else ""
        if "LS" in br_brand:
            brand_pref = "LS"
        else:
            brand_pref = "SANGDO"

    # EstimateRequest 생성
    return EstimateRequest(
        customer_name=customer_name,
        project_name=None,
        panels=[panel],
        options=EstimateOptions(
            breaker_brand_preference=brand_pref,
            use_economy_series=True,
            include_evidence_pack=True,
        ),
    )


# ===== 응답 생성기 =====
class ResponseGenerator:
    """AI 응답 생성기"""

    @classmethod
    async def generate(cls, intent: ParsedIntent, user_message: str, recent_messages: list = None) -> ChatResponse:
        """의도에 따른 응답 생성

        Args:
            intent: 파싱된 의도
            user_message: 사용자 메시지
            recent_messages: 프론트엔드에서 전달받은 최근 대화 히스토리 (선택적)
        """
        handlers = {
            "estimate": cls._handle_estimate,
            "drawing": cls._handle_drawing,  # async handler
            "email": cls._handle_email,
            "erp": cls._handle_erp,
            "calendar": cls._handle_calendar,  # async handler
            "help": cls._handle_help,
            "knowledge": cls._handle_knowledge,
            "conversation": cls._handle_conversation,
            "image_analysis": cls._handle_image_analysis,  # 이미지/첨부파일 정보 추출
            "unknown": cls._handle_unknown,
        }

        handler = handlers.get(intent.intent, cls._handle_unknown)

        # estimate, drawing, email, erp, conversation, image_analysis는 async 핸들러
        if intent.intent in ("estimate", "drawing", "email", "erp", "conversation", "image_analysis"):
            # conversation 핸들러에는 recent_messages 전달
            if intent.intent == "conversation":
                return await handler(intent, user_message, recent_messages)
            return await handler(intent, user_message)
        return handler(intent, user_message)

    @classmethod
    async def _handle_estimate(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """
        견적 처리 - FIX-4 파이프라인 연동

        자연어 입력을 파싱하여 FIX-4 파이프라인으로 완전한 견적 생성
        (외함, 부스바, E.T, N.T, N.P, COATING, P-COVER, 잡자재비, ASSEMBLY CHARGE 포함)
        """
        try:
            # Claude API가 파싱한 intent.params가 있으면 우선 사용
            estimate_request = None
            customer_name = None
            parse_messages = []  # Claude/regex 공통 변수

            # DEBUG: 파라미터 상세 로깅
            logger.info(f"[DEBUG] intent.params type: {type(intent.params)}")
            logger.info(f"[DEBUG] intent.params value: {intent.params}")
            logger.info(f"[DEBUG] intent.params truthy: {bool(intent.params)}")
            if intent.params:
                logger.info(f"[DEBUG] main_breaker in params: {'main_breaker' in intent.params}")
                logger.info(f"[DEBUG] params.get('main_breaker'): {intent.params.get('main_breaker')}")

            if intent.params and intent.params.get("main_breaker"):
                logger.info(f"[DEBUG] Entering Claude params conversion branch")
                estimate_request = _convert_intent_params_to_estimate_request(intent.params)
                logger.info(f"[DEBUG] _convert_intent_params_to_estimate_request returned: {estimate_request}")
                customer_name = intent.params.get("customer_name")
                parse_messages = ["Claude API 파싱 성공", f"브랜드: {intent.params.get('brand', '상도차단기')}", f"메인: {intent.params.get('main_breaker')}", f"분기: {intent.params.get('branch_breakers')}"]
                logger.info(f"Claude 파싱 결과 사용: main_breaker={intent.params.get('main_breaker')}")

            # Claude 파싱 실패 시 regex 기반 EstimateParserService로 폴백
            if not estimate_request:
                logger.info("Claude 파싱 없음, regex 파싱으로 폴백")
                parser_service = get_estimate_parser_service()
                parsed = await parser_service.parse_estimate_request(user_message)

                # 파싱 실패 시 안내
                if not parsed.parse_success:
                    return ChatResponse(
                        message=f"""견적을 생성하려면 추가 정보가 필요합니다.

**필요한 정보:** 메인 차단기 (극수, 용량)

**예시:**
- "상도 4P 100A 메인, 분기 ELB 3P 30A 10개로 견적해줘"
- "중앙전기, 옥내노출 스틸1.6T, 메인4P 50A, 분기 ELB 2P 20A 8개"
- "옥외자립, LS 표준형 메인 4P 200A"

**파싱 시도 결과:**
{chr(10).join(f"- {msg}" for msg in parsed.parse_messages) if parsed.parse_messages else "정보 없음"}""",
                        intent=intent,
                        suggestions=["상도 4P 100A 메인, 3P 30A 분기 5개 견적", "도움말"],
                    )

                # ParsedEstimateRequest → EstimateRequest 변환
                estimate_request = _convert_parsed_to_estimate_request(parsed)
                customer_name = parsed.customer_name
                parse_messages = parsed.parse_messages or []

            # FIX-4 파이프라인 실행 (완전한 견적 생성)
            # estimate_id는 None으로 전달 → 파이프라인에서 EST-YYYYMMDD-NNNN 형식으로 자동 생성
            pipeline = get_pipeline()
            estimate_response = await pipeline.execute(estimate_request, estimate_id=None)

            # estimate_id 추출 (파이프라인에서 자동 생성)
            estimate_id = estimate_response.estimate_id

            # 첫 번째 패널 결과
            panel = estimate_response.panels[0] if estimate_response.panels else None

            if not panel:
                return ChatResponse(
                    message="❌ **견적 생성 실패**: 패널 정보가 없습니다.",
                    intent=intent,
                    suggestions=["다시 시도", "도움말"],
                )

            # 차단기 정보 포맷팅
            main_info = ""
            branch_items = []
            accessory_items = []
            enclosure_item = None
            total_branch_qty = 0
            main_breaker_found = False  # 첫 번째 차단기를 메인으로 취급하기 위한 플래그

            # SSOT: constants.py에서 가져온 키워드 사용
            # BREAKER_MODEL_KEYWORDS: 차단기 모델명 키워드 (MCCB, ELB 계열)
            # ACCESSORY_EXCLUDE_KEYWORDS: 부속자재 키워드 (차단기로 오인되지 않도록 제외)

            for item in panel.items:
                # LineItemResponse: name, spec, quantity, unit, unit_price, supply_price
                # 카테고리 속성이 없으므로 name 기반으로 분류
                item_name_upper = item.name.upper() if item.name else ""

                # 부속자재 제외 체크 (ELB지지대 등이 차단기로 오인되지 않도록)
                is_accessory_type = any(exc_kw in item.name or exc_kw in item_name_upper for exc_kw in ACCESSORY_EXCLUDE_KEYWORDS)

                # 차단기 타입인지 확인 (부속자재가 아닌 경우에만)
                is_breaker = not is_accessory_type and any(kw in item_name_upper for kw in BREAKER_MODEL_KEYWORDS)

                # 메인 차단기 감지: 이름에 '메인' 포함 또는 첫 번째 차단기
                if "메인" in item.name or (is_breaker and not main_breaker_found):
                    main_info = f"- **메인:** {item.name} ({item.quantity}EA) - **{item.unit_price:,}원**"
                    main_breaker_found = True
                # 분기 차단기 감지 (메인 이후의 차단기들)
                elif is_breaker:
                    branch_items.append(f"- {item.name} x{int(item.quantity)} - **{item.supply_price:,}원**")
                    total_branch_qty += int(item.quantity)
                # 외함 감지
                elif "외함" in item.name or "HDS" in item_name_upper or "함체" in item.name:
                    enclosure_item = item
                else:
                    # 부속자재 (E.T, N.T, N.P, BUS-BAR, COATING, P-COVER, 잡자재비, ASSEMBLY CHARGE 등)
                    accessory_items.append(f"- {item.name}: {item.quantity}{item.unit or 'EA'} - **{item.supply_price:,}원**")

            # 외함 정보 포맷팅
            enc_info = ""
            if enclosure_item:
                enc_info = f"""
**외함:**
- 품목: {enclosure_item.name}
- 규격: {enclosure_item.spec or '-'}
- 단가: **{enclosure_item.unit_price:,}원**"""

            # 고객 정보
            customer_info = ""
            if customer_name:
                customer_info = f"\n**거래처:** {customer_name}"

            # 합계 금액 - LineItemResponse에는 supply_price 속성만 있음
            subtotal = panel.subtotal if hasattr(panel, 'subtotal') else sum(item.supply_price for item in panel.items)
            total = panel.total if hasattr(panel, 'total') else subtotal

            # 간소화된 요약 메시지 (상세 내용은 시각화 패널에서 확인)
            summary_message = f"""✅ **견적 생성 완료!**

**견적 ID:** `{estimate_id}`
**합계:** **{total:,}원** (VAT 별도)
**분기 차단기:** {total_branch_qty}개

👉 우측 시각화 패널에서 상세 내용을 확인하세요."""

            return ChatResponse(
                message=summary_message,
                intent=intent,
                action_result={
                    "type": "estimate",
                    "status": "success",
                    "estimate_id": estimate_id,
                    "estimate_response": estimate_response.model_dump() if hasattr(estimate_response, 'model_dump') else {},
                    "parsed_messages": parse_messages,
                },
                suggestions=["Excel 다운로드", "도면 생성해줘", "이메일 보내줘"],
            )

        except Exception as e:
            logger.error(f"Estimate generation failed: {e}", exc_info=True)
            return ChatResponse(
                message=f"""❌ **견적 생성 오류**

**오류:** {str(e)}

자연어 견적 요청 형식을 확인해주세요.

**올바른 형식 예시:**
- "상도 4P 100A 메인, 분기 ELB 3P 30A 10개"
- "중앙전기, 옥내노출 스틸1.6T, 메인4P 50A, 분기 2P 20A 8개"
- "옥외자립 SUS201, LS 표준형 메인 4P 200A, 분기 MCCB 3P 50A 5개"

**필수 정보:**
- 메인 차단기: 극수(2P/3P/4P), 용량(A)
- 분기 차단기: 종류(ELB/MCCB), 극수, 용량, 수량""",
                intent=intent,
                action_result={
                    "type": "estimate",
                    "status": "error",
                    "error": str(e),
                },
                suggestions=["도움말", "예시 보기"],
            )

    @classmethod
    async def _handle_drawing(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """도면 처리 - DrawingService 연동"""
        params = intent.params
        estimate_id = params.get("estimate_id")
        drawing_type = params.get("drawing_type", "all")

        # 견적 ID가 없으면 안내
        if not estimate_id:
            return ChatResponse(
                message="""📐 **도면 생성 기능**

**견적 ID가 필요합니다.**

도면을 생성하려면 견적 ID를 포함해서 말씀해주세요.

**예시:**
- "EST-20250101120000 도면 전체 생성"
- "EST-20250101120000 단선결선도 생성"
- "EST-20250101120000 배치도 만들어줘"

**지원 도면 종류:**
1. **단선결선도** (wiring) - 전기 회로 단선 표현
2. **외함외형도** (enclosure) - 외함 치수 및 구조
3. **차단기 배치도** (placement) - 차단기 물리적 배치
4. **전체 도면** (all) - 위 3종 모두 생성

*먼저 견적을 생성하시면 견적 ID가 부여됩니다.*""",
                intent=intent,
                suggestions=["견적 생성해줘", "도움말"],
            )

        # DrawingService로 도면 생성
        try:
            service = get_drawing_service()

            # 샘플 패널 데이터 (실제로는 DB에서 조회)
            panel_data = {
                "name": estimate_id,
                "enclosure": {
                    "width": 600,
                    "height": 800,
                    "depth": 200,
                    "material": "STEEL 1.6T",
                    "type": "옥내노출",
                    "ip_rating": "IP44",
                },
                "main_breaker": {
                    "model": "SBE-104",
                    "poles": 4,
                    "rating": "100A",
                    "frame": 100,
                    "width": 100,
                    "height": 130,
                },
            }

            # 샘플 배치 결과 (실제로는 BreakerPlacer에서 계산)
            placement_result = {
                "breakers": [
                    {"model": "SBE-53", "poles": 3, "rating": "30A", "side": "left", "width": 75, "height": 130},
                    {"model": "SBE-53", "poles": 3, "rating": "30A", "side": "left", "width": 75, "height": 130},
                    {"model": "SBE-53", "poles": 3, "rating": "30A", "side": "right", "width": 75, "height": 130},
                    {"model": "SBE-53", "poles": 3, "rating": "30A", "side": "right", "width": 75, "height": 130},
                ]
            }

            # 도면 생성
            result = await service.generate_drawings(
                estimate_id=estimate_id,
                panel_data=panel_data,
                placement_result=placement_result
            )

            drawings = result.get("drawings", {})
            generated_count = len(drawings)

            # 생성된 도면 정보 포맷팅
            drawing_list = []
            if "wiring_diagram" in drawings:
                drawing_list.append(f"- **단선결선도**: {drawings['wiring_diagram']['path']}")
            if "enclosure_diagram" in drawings:
                drawing_list.append(f"- **외함외형도**: {drawings['enclosure_diagram']['path']}")
            if "placement_diagram" in drawings:
                drawing_list.append(f"- **배치도**: {drawings['placement_diagram']['path']}")

            drawing_info = "\n".join(drawing_list) if drawing_list else "도면 없음"

            return ChatResponse(
                message=f"""📐 **도면 생성 완료!**

**견적 ID:** {estimate_id}
**생성 시각:** {result.get('generated_at', '-')}

**생성된 도면 ({generated_count}개):**
{drawing_info}

**다음 작업:**
- "이메일 발송" - 도면과 함께 견적서 전송
- "ERP 등록" - 발주 시스템 연동
- "다른 도면 생성" - 추가 도면 요청""",
                intent=intent,
                action_result={
                    "type": "drawing",
                    "status": "success",
                    "estimate_id": estimate_id,
                    "drawing_type": drawing_type,
                    "generated_count": generated_count,
                    "drawings": drawings,
                },
                suggestions=["이메일 발송해줘", "ERP 등록해줘", "다른 견적 생성"],
            )

        except Exception as e:
            logger.error(f"Drawing generation failed: {e}")
            return ChatResponse(
                message=f"""📐 **도면 생성 실패**

**오류:** {str(e)}

다시 시도하시거나 관리자에게 문의해주세요.

**확인 사항:**
- 견적 ID가 올바른지 확인
- 견적 데이터가 존재하는지 확인""",
                intent=intent,
                action_result={
                    "type": "drawing",
                    "status": "error",
                    "error": str(e),
                },
                suggestions=["다시 시도", "견적 생성", "도움말"],
            )

    @classmethod
    async def _handle_email(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """이메일 처리 - EmailService 연동"""
        params = intent.params
        to_email = params.get("to")
        estimate_id = params.get("estimate_id")
        customer_name = params.get("customer_name", "")

        # 이메일 주소 없으면 안내
        if not to_email:
            return ChatResponse(
                message="""📧 **이메일 발송 기능**

**수신자 이메일이 필요합니다.**

이메일을 발송하려면 수신자 이메일 주소를 포함해서 말씀해주세요.

**예시:**
- "EST-20250101120000 견적서를 abc@company.com으로 보내줘"
- "김철수님에게 EST-20250101120000 견적 이메일 발송"
- "abc@company.com으로 견적서 전송해줘"

**필요 정보:**
1. **이메일 주소** (필수) - 수신자 이메일
2. **견적 ID** (선택) - 특정 견적서 첨부
3. **고객명** (선택) - 이메일 인사말에 사용""",
                intent=intent,
                suggestions=["abc@example.com으로 견적 보내줘", "도움말"],
            )

        # 이메일 발송 실행
        try:
            service = get_email_service()

            # 견적 데이터 (실제로는 DB에서 조회)
            estimate_data = {}
            if estimate_id:
                estimate_data = {
                    "enclosure_type": "옥내노출",
                    "brand": "상도차단기",
                    "main_breaker": "SBE-104 4P 100A",
                    "branch_count": 10,
                    "total_price": 850000,
                }

            # 첨부파일 (실제로는 생성된 PDF/Excel 경로)
            attachments = []

            # 이메일 발송
            result = await service.send_estimate_email(
                to=to_email,
                estimate_id=estimate_id or f"EST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                customer_name=customer_name,
                estimate_data=estimate_data,
                attachments=attachments if attachments else None
            )

            if result.success:
                return ChatResponse(
                    message=f"""📧 **이메일 발송 완료!**

**발송 결과:** ✅ 성공

**수신자:** {to_email}
**제목:** {result.subject}
**발송 시각:** {result.sent_at or '-'}

{f"**견적 ID:** {estimate_id}" if estimate_id else ""}
{f"**고객명:** {customer_name}님" if customer_name else ""}

**다음 작업:**
- "다른 이메일 발송" - 추가 이메일 전송
- "ERP 등록" - 발주 시스템 연동""",
                    intent=intent,
                    action_result={
                        "type": "email",
                        "status": "success",
                        "to": to_email,
                        "estimate_id": estimate_id,
                        "sent_at": result.sent_at,
                    },
                    suggestions=["다른 이메일 보내줘", "ERP 등록해줘"],
                )
            else:
                return ChatResponse(
                    message=f"""📧 **이메일 발송 실패**

**오류:** {result.message}
{f"**상세:** {result.error}" if result.error else ""}

**확인 사항:**
- SMTP 설정이 올바른지 확인
- 이메일 주소가 유효한지 확인
- 네트워크 연결 상태 확인

*SMTP 환경변수: SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD*""",
                    intent=intent,
                    action_result={
                        "type": "email",
                        "status": "error",
                        "error": result.error,
                    },
                    suggestions=["다시 시도", "도움말"],
                )

        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return ChatResponse(
                message=f"""📧 **이메일 발송 오류**

**오류:** {str(e)}

이메일 서비스가 설정되지 않았거나 오류가 발생했습니다.
관리자에게 문의하거나 SMTP 설정을 확인해주세요.""",
                intent=intent,
                action_result={
                    "type": "email",
                    "status": "error",
                    "error": str(e),
                },
                suggestions=["도움말"],
            )

    @classmethod
    async def _handle_calendar(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """캘린더 처리 - Calendar API 연동"""
        import httpx
        from datetime import datetime, timedelta

        params = intent.params
        operation = params.get("operation", "list")
        event_date = params.get("date")
        event_time = params.get("time")
        event_type = params.get("event_type", "task")
        title = params.get("title")
        customer = params.get("customer")

        base_url = "http://localhost:8000/v1/calendar"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 작업별 처리
                if operation == "create":
                    # 일정 생성
                    if not title:
                        return ChatResponse(
                            message="""📅 **일정 생성 기능**

**일정 제목이 필요합니다.**

일정을 생성하려면 제목을 포함해서 말씀해주세요.

**예시:**
- "12월 15일 납품 일정 등록해줘"
- "내일 오후 2시 김철수님 미팅 추가"
- "1월 10일 견적 마감일 설정"

**필요 정보:**
1. **제목** (필수) - 일정 제목
2. **날짜** (선택) - YYYY-MM-DD 또는 MM월 DD일
3. **시간** (선택) - HH:MM 또는 오전/오후 X시
4. **유형** (선택) - 납품/미팅/리마인더/작업""",
                            intent=intent,
                            suggestions=["내일 납품 일정 등록", "도움말"],
                        )

                    # 날짜/시간 조합
                    if not event_date:
                        event_date = datetime.now().strftime("%Y-%m-%d")
                    start_time = f"{event_date}T{event_time or '09:00'}:00"

                    # 일정 생성 API 호출
                    response = await client.post(
                        f"{base_url}/events",
                        json={
                            "title": title,
                            "start": start_time,
                            "type": event_type,
                            "customer": customer,
                            "description": f"AI 매니저로 생성: {user_message}",
                        }
                    )

                    if response.status_code == 201:
                        event = response.json()
                        return ChatResponse(
                            message=f"""📅 **일정 생성 완료!**

**일정 ID:** {event.get('id', '-')}
**제목:** {event.get('title', '-')}
**날짜:** {event.get('start', '-')[:10]}
**시간:** {event.get('start', '-')[11:16] if 'T' in event.get('start', '') else '-'}
**유형:** {event.get('type', '-')}
{f"**거래처:** {event.get('customer')}" if event.get('customer') else ""}

**다음 작업:**
- "일정 목록 보여줘" - 전체 일정 확인
- "이번 주 일정" - 다가오는 일정 확인""",
                            intent=intent,
                            visualizations=[{
                                "id": f"cal-{event.get('id', 'new')}",
                                "type": "calendar_event",
                                "title": "생성된 일정",
                                "data": event,
                                "actions": [
                                    {"id": "edit", "label": "수정", "icon": "✏️"},
                                    {"id": "delete", "label": "삭제", "icon": "🗑️"},
                                ]
                            }],
                            action_result={
                                "type": "calendar",
                                "operation": "create",
                                "status": "success",
                                "event_id": event.get('id'),
                            },
                            suggestions=["일정 목록 보여줘", "이번 주 일정"],
                        )
                    else:
                        return ChatResponse(
                            message=f"""📅 **일정 생성 실패**

**오류:** {response.text}

다시 시도하거나 형식을 확인해주세요.""",
                            intent=intent,
                            suggestions=["다시 시도", "도움말"],
                        )

                elif operation == "upcoming":
                    # 다가오는 일정 조회
                    days = 7  # 기본 7일
                    response = await client.get(f"{base_url}/events/upcoming", params={"days": days})

                    if response.status_code == 200:
                        events = response.json()
                        if not events:
                            return ChatResponse(
                                message="""📅 **다가오는 일정 없음**

앞으로 7일 내 등록된 일정이 없습니다.

**일정을 추가해보세요:**
- "내일 납품 일정 등록"
- "다음 주 월요일 미팅 추가" """,
                                intent=intent,
                                suggestions=["일정 추가", "전체 일정 보기"],
                            )

                        events_text = "\n".join([
                            f"- **{e.get('title', '제목없음')}** ({e.get('start', '')[:10]}) - {e.get('type', 'task')}"
                            for e in events[:10]
                        ])

                        return ChatResponse(
                            message=f"""📅 **다가오는 일정** (7일 이내)

{events_text}

총 {len(events)}건의 일정이 있습니다.""",
                            intent=intent,
                            visualizations=[{
                                "id": "upcoming-events",
                                "type": "calendar_event",
                                "title": "다가오는 일정",
                                "data": {"events": events, "count": len(events)},
                            }],
                            suggestions=["일정 추가", "오늘 일정"],
                        )

                elif operation == "list":
                    # 일정 목록 조회
                    query_params = {}
                    if event_date:
                        query_params["start_date"] = event_date
                        query_params["end_date"] = event_date
                    if event_type and event_type != "task":
                        query_params["type"] = event_type

                    response = await client.get(f"{base_url}/events", params=query_params)

                    if response.status_code == 200:
                        events = response.json()
                        if not events:
                            date_str = f" ({event_date})" if event_date else ""
                            return ChatResponse(
                                message=f"""📅 **일정 없음**{date_str}

조회 조건에 맞는 일정이 없습니다.

**일정을 추가해보세요:**
- "내일 납품 일정 등록"
- "12월 20일 미팅 추가" """,
                                intent=intent,
                                suggestions=["일정 추가", "다가오는 일정"],
                            )

                        events_text = "\n".join([
                            f"- **{e.get('title', '제목없음')}** ({e.get('start', '')[:10]}) - {e.get('type', 'task')}"
                            for e in events[:15]
                        ])

                        return ChatResponse(
                            message=f"""📅 **일정 목록**

{events_text}

총 {len(events)}건의 일정이 조회되었습니다.""",
                            intent=intent,
                            visualizations=[{
                                "id": "event-list",
                                "type": "calendar_event",
                                "title": "일정 목록",
                                "data": {"events": events, "count": len(events)},
                            }],
                            suggestions=["일정 추가", "이번 주 일정"],
                        )

                elif operation == "delete":
                    # 일정 삭제 (제목으로 검색 후 삭제)
                    if not title:
                        return ChatResponse(
                            message="""📅 **일정 삭제 기능**

**삭제할 일정을 지정해주세요.**

**예시:**
- "납품 일정 삭제해줘"
- "12월 15일 미팅 취소" """,
                            intent=intent,
                            suggestions=["일정 목록 보기", "도움말"],
                        )

                    # 먼저 일정 검색
                    response = await client.get(f"{base_url}/events")
                    if response.status_code == 200:
                        events = response.json()
                        # 제목으로 매칭
                        matching = [e for e in events if title.lower() in e.get('title', '').lower()]

                        if matching:
                            # 첫 번째 매칭 삭제
                            event_to_delete = matching[0]
                            del_response = await client.delete(f"{base_url}/events/{event_to_delete['id']}")

                            if del_response.status_code == 200:
                                return ChatResponse(
                                    message=f"""📅 **일정 삭제 완료!**

**삭제된 일정:** {event_to_delete.get('title')}
**날짜:** {event_to_delete.get('start', '')[:10]}""",
                                    intent=intent,
                                    action_result={
                                        "type": "calendar",
                                        "operation": "delete",
                                        "status": "success",
                                        "deleted_id": event_to_delete['id'],
                                    },
                                    suggestions=["일정 목록 보기", "새 일정 추가"],
                                )

                        return ChatResponse(
                            message=f"""📅 **일정을 찾을 수 없음**

'{title}' 제목의 일정을 찾을 수 없습니다.

일정 목록을 확인해보세요.""",
                            intent=intent,
                            suggestions=["일정 목록 보기"],
                        )

                elif operation == "update":
                    return ChatResponse(
                        message="""📅 **일정 수정 기능**

일정 수정은 현재 웹 UI에서 지원됩니다.
캘린더 탭에서 수정할 일정을 클릭하여 수정하세요.

**또는 삭제 후 재생성:**
- "기존 일정 삭제해줘"
- "새 일정 등록해줘" """,
                        intent=intent,
                        suggestions=["일정 목록 보기", "새 일정 추가"],
                    )

                else:
                    # 기본: 오늘 일정 조회
                    today = datetime.now().strftime("%Y-%m-%d")
                    response = await client.get(f"{base_url}/events/today")

                    if response.status_code == 200:
                        events = response.json()
                        if not events:
                            return ChatResponse(
                                message="""📅 **오늘 일정 없음**

오늘 등록된 일정이 없습니다.

**다른 일정 확인:**
- "이번 주 일정 보여줘"
- "다가오는 일정 확인" """,
                                intent=intent,
                                suggestions=["이번 주 일정", "일정 추가"],
                            )

                        events_text = "\n".join([
                            f"- **{e.get('title', '제목없음')}** ({e.get('start', '')[11:16]}) - {e.get('type', 'task')}"
                            for e in events
                        ])

                        return ChatResponse(
                            message=f"""📅 **오늘 일정** ({today})

{events_text}

총 {len(events)}건의 일정이 있습니다.""",
                            intent=intent,
                            visualizations=[{
                                "id": "today-events",
                                "type": "calendar_event",
                                "title": "오늘 일정",
                                "data": {"events": events, "date": today},
                            }],
                            suggestions=["이번 주 일정", "일정 추가"],
                        )

        except httpx.ConnectError:
            return ChatResponse(
                message="""📅 **캘린더 서비스 연결 실패**

백엔드 서버에 연결할 수 없습니다.
서버가 실행 중인지 확인해주세요.""",
                intent=intent,
                suggestions=["다시 시도", "도움말"],
            )
        except Exception as e:
            logger.error(f"Calendar operation failed: {e}")
            return ChatResponse(
                message=f"""📅 **캘린더 오류**

**오류:** {str(e)}

다시 시도하거나 관리자에게 문의하세요.""",
                intent=intent,
                action_result={
                    "type": "calendar",
                    "status": "error",
                    "error": str(e),
                },
                suggestions=["다시 시도", "도움말"],
            )

    @classmethod
    async def _handle_erp(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """ERP 처리 - ERPService 연동"""
        params = intent.params
        operation = params.get("operation", "query")

        try:
            service = get_erp_service()

            # 작업별 처리
            if operation == "order":
                # 발주 등록
                estimate_id = params.get("estimate_id")
                customer_name = params.get("customer_name", "")

                if not estimate_id:
                    return ChatResponse(
                        message="""📦 **발주 등록 기능**

**견적 ID가 필요합니다.**

발주를 등록하려면 견적 ID를 포함해서 말씀해주세요.

**예시:**
- "EST-20250101120000 발주 등록해줘"
- "김철수고객 EST-20250101120000 발주"

*먼저 견적을 생성하시면 견적 ID가 부여됩니다.*""",
                        intent=intent,
                        suggestions=["견적 생성해줘", "도움말"],
                    )

                # 발주 등록 실행
                result = await service.create_order(
                    estimate_id=estimate_id,
                    customer_name=customer_name
                )

                if result.success:
                    data = result.data or {}
                    return ChatResponse(
                        message=f"""📦 **발주 등록 완료!**

**발주 ID:** {data.get('order_id', '-')}
**견적 ID:** {data.get('estimate_id', '-')}
**고객명:** {data.get('customer_name', '-') or '미지정'}
**상태:** {data.get('status', '-')}

**다음 작업:**
- "주문 조회" - 주문 내역 확인
- "재고 확인" - 재고 상태 확인""",
                        intent=intent,
                        action_result={
                            "type": "erp",
                            "operation": "order_create",
                            "status": "success",
                            **data
                        },
                        suggestions=["주문 조회해줘", "재고 확인해줘"],
                    )
                else:
                    return ChatResponse(
                        message=f"""📦 **발주 등록 실패**

**오류:** {result.message}
{f"**상세:** {result.error}" if result.error else ""}

다시 시도하거나 관리자에게 문의해주세요.""",
                        intent=intent,
                        action_result={
                            "type": "erp",
                            "operation": "order_create",
                            "status": "error",
                            "error": result.error
                        },
                        suggestions=["다시 시도", "도움말"],
                    )

            elif operation == "inventory":
                # 재고 확인
                sku = params.get("sku")
                category = params.get("category")

                result = await service.check_inventory(sku=sku, category=category)

                if result.success:
                    data = result.data or {}

                    if sku:
                        # 단일 품목
                        return ChatResponse(
                            message=f"""📊 **재고 조회 결과**

**품목:** {data.get('name', sku)}
**SKU:** {data.get('sku', sku)}
**가용 재고:** {data.get('available_qty', 0)}개
**예약 재고:** {data.get('reserved_qty', 0)}개
**위치:** {data.get('location', '-')}

**다음 작업:**
- "발주 등록" - 자재 발주
- "다른 품목 확인" - 추가 재고 조회""",
                            intent=intent,
                            action_result={
                                "type": "erp",
                                "operation": "inventory_check",
                                "status": "success",
                                **data
                            },
                            suggestions=["발주 등록해줘", "차단기 재고 확인"],
                        )
                    else:
                        # 목록 조회
                        items = data.get("items", [])
                        total = data.get("total_count", 0)

                        items_text = "\n".join([
                            f"- **{item['name']}** ({item['sku']}): {item['available_qty']}개"
                            for item in items[:10]
                        ])

                        return ChatResponse(
                            message=f"""📊 **재고 현황** ({total}개 품목)

{items_text}
{f"... 외 {total - 10}개 품목" if total > 10 else ""}

**필터 옵션:**
- "차단기 재고" - 차단기 카테고리
- "외함 재고" - 외함 카테고리
- "SBE-104 재고" - 특정 품목""",
                            intent=intent,
                            action_result={
                                "type": "erp",
                                "operation": "inventory_check",
                                "status": "success",
                                "total_count": total
                            },
                            suggestions=["차단기 재고", "외함 재고", "발주 등록"],
                        )
                else:
                    return ChatResponse(
                        message=f"""📊 **재고 조회 실패**

**오류:** {result.message}

다시 시도해주세요.""",
                        intent=intent,
                        action_result={
                            "type": "erp",
                            "operation": "inventory_check",
                            "status": "error",
                            "error": result.error
                        },
                        suggestions=["재고 확인", "도움말"],
                    )

            elif operation == "query":
                # 주문 조회
                order_id = params.get("order_id")
                estimate_id = params.get("estimate_id")

                result = await service.get_orders(
                    order_id=order_id,
                    estimate_id=estimate_id
                )

                if result.success:
                    data = result.data or {}

                    if order_id:
                        # 단일 주문
                        return ChatResponse(
                            message=f"""📋 **주문 상세**

**주문 ID:** {data.get('order_id', '-')}
**견적 ID:** {data.get('estimate_id', '-') or '미지정'}
**고객명:** {data.get('customer_name', '-') or '미지정'}
**총 금액:** {data.get('total_amount', 0):,}원
**상태:** {data.get('status', '-')}
**등록일:** {data.get('created_at', '-')[:10] if data.get('created_at') else '-'}

**작업:**
- "주문 취소" - 해당 주문 취소""",
                            intent=intent,
                            action_result={
                                "type": "erp",
                                "operation": "order_query",
                                "status": "success",
                                **data
                            },
                            suggestions=["주문 취소", "다른 주문 조회"],
                        )
                    else:
                        # 목록 조회
                        orders = data.get("orders", [])
                        total = data.get("total_count", 0)

                        if not orders:
                            return ChatResponse(
                                message="""📋 **주문 내역**

등록된 주문이 없습니다.

**새 발주를 등록하시겠습니까?**
- "EST-XXXXX 발주 등록" - 견적 기반 발주""",
                                intent=intent,
                                action_result={
                                    "type": "erp",
                                    "operation": "order_query",
                                    "status": "success",
                                    "total_count": 0
                                },
                                suggestions=["발주 등록해줘", "견적 생성해줘"],
                            )

                        orders_text = "\n".join([
                            f"- **{o['order_id']}** | {o.get('customer_name', '-') or '-'} | {o['total_amount']:,}원 | {o['status']}"
                            for o in orders[:5]
                        ])

                        return ChatResponse(
                            message=f"""📋 **주문 목록** ({total}건)

{orders_text}

**상세 조회:**
- "ORD-XXXXX 조회" - 특정 주문 상세""",
                            intent=intent,
                            action_result={
                                "type": "erp",
                                "operation": "order_query",
                                "status": "success",
                                "total_count": total
                            },
                            suggestions=["발주 등록", "재고 확인"],
                        )
                else:
                    return ChatResponse(
                        message=f"""📋 **주문 조회 실패**

**오류:** {result.message}

다시 시도해주세요.""",
                        intent=intent,
                        action_result={
                            "type": "erp",
                            "operation": "order_query",
                            "status": "error",
                            "error": result.error
                        },
                        suggestions=["주문 조회", "도움말"],
                    )

            elif operation == "cancel":
                # 주문 취소
                order_id = params.get("order_id")

                if not order_id:
                    return ChatResponse(
                        message="""📦 **주문 취소 기능**

**주문 ID가 필요합니다.**

주문을 취소하려면 주문 ID를 포함해서 말씀해주세요.

**예시:**
- "ORD-20250101120000 취소해줘"
- "주문 ORD-20250101120000 취소"

*먼저 주문 조회로 주문 ID를 확인하세요.*""",
                        intent=intent,
                        suggestions=["주문 조회해줘", "도움말"],
                    )

                result = await service.cancel_order(order_id=order_id)

                if result.success:
                    data = result.data or {}
                    return ChatResponse(
                        message=f"""📦 **주문 취소 완료**

**주문 ID:** {data.get('order_id', '-')}
**취소 시각:** {data.get('cancelled_at', '-')[:19] if data.get('cancelled_at') else '-'}

**다음 작업:**
- "주문 조회" - 다른 주문 확인
- "발주 등록" - 새 발주 등록""",
                        intent=intent,
                        action_result={
                            "type": "erp",
                            "operation": "order_cancel",
                            "status": "success",
                            **data
                        },
                        suggestions=["주문 조회해줘", "발주 등록해줘"],
                    )
                else:
                    return ChatResponse(
                        message=f"""📦 **주문 취소 실패**

**오류:** {result.message}

취소 불가능한 상태이거나 주문 ID가 올바르지 않습니다.""",
                        intent=intent,
                        action_result={
                            "type": "erp",
                            "operation": "order_cancel",
                            "status": "error",
                            "error": result.error
                        },
                        suggestions=["주문 조회", "도움말"],
                    )

            else:
                # 기본 안내
                return ChatResponse(
                    message="""📦 **ERP 연동 기능**

사용 가능한 ERP 작업:
1. **발주 등록** - "EST-XXXXX 발주 등록해줘"
2. **재고 확인** - "재고 확인해줘" / "차단기 재고"
3. **주문 조회** - "주문 내역 보여줘"
4. **주문 취소** - "ORD-XXXXX 취소해줘"

**예시:**
- "EST-20250101120000 발주 등록해줘"
- "SBE-104 재고 확인"
- "주문 목록 조회"
- "ORD-20250101120000 취소"

견적 ID 또는 주문 ID와 함께 요청하세요.""",
                    intent=intent,
                    suggestions=["발주 등록", "재고 확인", "주문 조회"],
                )

        except Exception as e:
            logger.error(f"ERP operation failed: {e}")
            return ChatResponse(
                message=f"""📦 **ERP 작업 오류**

**오류:** {str(e)}

ERP 서비스에 문제가 발생했습니다.
관리자에게 문의하거나 잠시 후 다시 시도해주세요.""",
                intent=intent,
                action_result={
                    "type": "erp",
                    "status": "error",
                    "error": str(e)
                },
                suggestions=["도움말"],
            )

    @classmethod
    def _handle_help(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """도움말"""
        return ChatResponse(
            message="""🤖 **AI 매니저 사용 가이드**

## 견적 생성
자연어로 분전반 사양을 말씀해주세요:
- "상도 4P 100A 메인, 3P 30A 분기 10개로 견적해줘"
- "옥내노출 분전반, 메인 200A, 분기 20A 8개"
- "LS 누전차단기 2P 30A 5개 견적"

## 도면 생성
- "도면 생성해줘"
- "단선결선도 만들어줘"
- "EST-123456 배치도 생성"

## 이메일 발송
- "견적서 이메일 보내줘"
- "abc@company.com으로 견적 전송"

## ERP 연동
- "발주 등록해줘"
- "재고 확인해줘"

## 지원 사양
- **브랜드**: 상도, LS, 한국산업
- **차단기**: MCCB(배선용), ELB(누전)
- **극수**: 2P, 3P, 4P
- **프레임**: 30AF ~ 800AF
- **외함**: 옥내노출, 옥외노출, 옥내자립, 옥외자립, 매입함 등""",
            intent=intent,
            suggestions=["견적 생성 예시", "도면 생성", "이메일 발송"],
        )

    @classmethod
    def _handle_knowledge(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """지식 검색 (RAG 연동)"""
        retriever = get_rag_retriever()

        if retriever is None:
            return ChatResponse(
                message="""📚 **지식 검색 시스템**

RAG 시스템이 아직 초기화되지 않았습니다.
기본 지식으로 응답해 드리겠습니다.

**검색 가능한 정보:**
- 차단기 사양, 치수, 가격
- 외함 종류, 크기 계산 공식
- 부속자재 규격
- 견적 작성 규칙

구체적인 질문을 해주시면 도움이 됩니다.
예: "SBE-104 차단기 치수 알려줘"
예: "4P 100A 차단기 가격은?"
예: "외함 높이 계산 공식은?"
""",
                intent=intent,
                suggestions=["차단기 치수 검색", "외함 규격 검색", "가격 검색"],
            )

        # RAG 검색 실행
        try:
            # 🔴 학습된 데이터 우선 검색 (가격 정보 등)
            from kis_estimator_core.rag.learner import get_learner
            learner = get_learner()
            learned_results = learner.search(user_message, limit=5)

            # 학습된 데이터에서 결과가 있으면 우선 반환
            if learned_results:
                # 학습된 데이터에서 검색 결과 있음
                result_lines = []
                for item in learned_results[:3]:
                    if "item_name" in item:  # 가격 정보
                        result_lines.append(
                            f"**[가격]** {item.get('item_name', 'N/A')}: "
                            f"{item.get('new_price', 0):,}원"
                        )
                    else:  # 지식/노하우
                        result_lines.append(
                            f"**[{item.get('category', 'KNOWLEDGE')}]** {item.get('title', 'N/A')}\n"
                            f"{item.get('content', '')[:200]}..."
                        )

                result_text = "\n\n".join(result_lines)

                return ChatResponse(
                    message=f"""📚 **학습된 지식 검색 결과**

**질문:** "{user_message}"

---

{result_text}

---

*학습된 데이터에서 {len(learned_results)}개 결과 검색됨*""",
                    intent=intent,
                    action_result={
                        "type": "learned_search",
                        "status": "success",
                        "query": user_message,
                        "result_count": len(learned_results),
                        "results": learned_results[:5],
                    },
                    suggestions=["더 자세히 알려줘", "다른 검색"],
                )

            # 학습된 데이터에도 없으면 ChromaDB에서 검색
            results = retriever.search(user_message, top_k=5)

            if not results:
                return ChatResponse(
                    message=f"""📚 **검색 결과**

**질문:** "{user_message}"

관련 정보를 찾지 못했습니다.
다른 키워드로 검색해 보세요.

**검색 팁:**
- 차단기: "SBE-104", "4P 100A", "상도 배선용"
- 외함: "옥내노출", "600×800", "HDS"
- 부속자재: "마그네트 MC-22", "터미널블록"
- 공식: "외함 높이", "E.T 수량", "잡자재비"
""",
                    intent=intent,
                    suggestions=["차단기 검색", "외함 검색", "공식 검색"],
                )

            # 검색 결과 포맷팅
            result_text = "\n\n".join([
                f"**[{r.metadata.get('category', 'UNKNOWN')}]** (관련도: {r.score:.0%})\n{r.content[:500]}{'...' if len(r.content) > 500 else ''}"
                for r in results[:3]
            ])

            return ChatResponse(
                message=f"""📚 **지식 검색 결과**

**질문:** "{user_message}"

---

{result_text}

---

*RAG 시스템에서 {len(results)}개 결과 검색됨*

추가 질문이 있으시면 말씀해주세요.""",
                intent=intent,
                action_result={
                    "type": "knowledge_search",
                    "status": "success",
                    "query": user_message,
                    "result_count": len(results),
                    "results": [
                        {
                            "id": r.id,
                            "category": r.metadata.get("category"),
                            "score": r.score,
                            "source": r.source,
                        }
                        for r in results
                    ],
                },
                suggestions=["더 자세히 알려줘", "관련 견적 생성", "도움말"],
            )

        except Exception as e:
            logger.error(f"RAG search error: {e}")

            # RAG 검색 실패해도 지식 저장 시도 (중요!)
            try:
                saved_info = cls._detect_and_save_knowledge(user_message, "")
                if saved_info and saved_info.get("items"):
                    saved_count = saved_info.get('saved_count', 0)
                    saved_items_desc = ", ".join([
                        f"{item.get('type', 'UNKNOWN')}: {item.get('item', item.get('content', ''))[:30]}..."
                        for item in saved_info.get('items', [])[:3]
                    ])
                    return ChatResponse(
                        message=f"""📚 **지식 검색**

검색 중 오류가 발생했습니다: {str(e)}

✅ **지식 저장 완료**: 입력하신 정보가 저장되었습니다.
- 저장된 항목: {saved_count}개
- 내용: {saved_items_desc}

다음에 관련 질문 시 활용하겠습니다.""",
                        intent=intent,
                        action_result=saved_info,
                        suggestions=["저장된 지식 확인", "도움말"],
                    )
            except Exception as save_error:
                logger.error(f"지식 저장도 실패: {save_error}")

            return ChatResponse(
                message=f"""📚 **지식 검색**

검색 중 오류가 발생했습니다: {str(e)}

기본 검색 기능을 이용해주세요.""",
                intent=intent,
                suggestions=["도움말", "견적 생성"],
            )


    @classmethod
    def _detect_and_save_knowledge(cls, user_message: str, ai_response: str) -> dict | None:
        """
        대화 중 학습 가능한 지식/노하우/단가를 자동 감지하고 저장

        감지 패턴:
        - 가격 정보: "XX는 YY원이야", "단가가 ZZ원으로 변경"
        - 노하우: "~할 때는 ~해야해", "~하는 게 좋아"
        - 규칙: "~하면 안 돼", "반드시 ~해야 해"
        - 지식: "~는 ~이야", "~의 치수는 ~"

        Returns:
            저장된 지식 정보 또는 None
        """
        import re

        combined_text = f"{user_message} {ai_response}"
        learner = get_learner()
        saved_items = []

        # 1. 가격 정보 감지 (예: "SBE-104는 15000원이야", "단가 20000원")
        price_patterns = [
            r'([A-Z0-9\-]+)(?:는|은|의|가)\s*(\d{1,3}(?:,?\d{3})*)\s*원',  # SBE-104는 15000원
            r'단가(?:가|는|를)?\s*(\d{1,3}(?:,?\d{3})*)\s*원(?:으로|에서)?\s*(?:변경|수정)?',  # 단가가 20000원으로 변경
            r'([가-힣A-Za-z0-9\-\s]+)\s*가격(?:이|은|는)?\s*(\d{1,3}(?:,?\d{3})*)\s*원',  # XX 가격이 YY원
            # 추가 패턴: "XX의 단가는 YY원", "XX 단가 YY원"
            r'([A-Z0-9\-\s]+[A-Za-z0-9]+)(?:의|에)?\s*단가(?:는|가|이)?\s*(\d{1,3}(?:,?\d{3})*)\s*원',  # SBE-104 3P 75A의 단가는 12500원
            r'([가-힣A-Za-z0-9\-\s]{2,30})(?:은|는|이|가)?\s*(\d{1,3}(?:,?\d{3})*)\s*원(?:이야|야|임|입니다)',  # XX는 YY원이야
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                if len(match) >= 2:
                    item_name = match[0].strip() if isinstance(match[0], str) else ""
                    price_str = match[1].replace(",", "") if isinstance(match[1], str) else match[0].replace(",", "")
                    try:
                        price = int(price_str)
                        if price > 100 and price < 100000000:  # 합리적인 가격 범위
                            item = learner.save_price(
                                item_name=item_name or "미상 품목",
                                new_price=price,
                                source="대화 자동 감지",
                                reason="대화 중 언급된 가격"
                            )
                            saved_items.append({"type": "price", "item": item_name, "price": price})
                            logger.info(f"RAG 학습: 가격 저장 - {item_name}: {price}원")
                    except (ValueError, TypeError):
                        pass

        # 2. 노하우 감지 (예: "~할 때는 ~해야 해", "~하는 게 좋아")
        knowhow_patterns = [
            r'([가-힣A-Za-z0-9\s]+(?:할|하는|선택|사용|적용))\s*(?:때는?|경우에?는?)\s*([가-힣A-Za-z0-9\s]+(?:해야|하면|해|사용|적용))',
            r'([가-힣A-Za-z0-9\s]{5,50})(?:하는\s*게|하면)\s*(?:좋|낫)',
            r'(?:팁|노하우|요령)[:\s]+([가-힣A-Za-z0-9\s,\.]{10,100})',
        ]

        for pattern in knowhow_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                content = match if isinstance(match, str) else " ".join(match)
                if len(content) > 10 and len(content) < 500:
                    item = learner.save_knowhow(
                        title=content[:50] + "..." if len(content) > 50 else content,
                        content=content,
                        source="대화 자동 감지"
                    )
                    saved_items.append({"type": "knowhow", "content": content[:100]})
                    logger.info(f"RAG 학습: 노하우 저장 - {content[:50]}")

        # 3. 규칙 감지 (예: "~하면 안 돼", "반드시 ~해야 해")
        rule_patterns = [
            r'([가-힣A-Za-z0-9\s]+)(?:하면|은|는)\s*(?:안\s*돼|금지|불가)',
            r'(?:반드시|꼭|필수로?)\s*([가-힣A-Za-z0-9\s]+)(?:해야|해)',
            r'(?:규칙|원칙|정책)[:\s]+([가-힣A-Za-z0-9\s,\.]{10,100})',
        ]

        for pattern in rule_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                content = match if isinstance(match, str) else match[0]
                if len(content) > 5 and len(content) < 300:
                    item = learner.save_rule(
                        title=content[:50] + "..." if len(content) > 50 else content,
                        content=content,
                        source="대화 자동 감지"
                    )
                    saved_items.append({"type": "rule", "content": content[:100]})
                    logger.info(f"RAG 학습: 규칙 저장 - {content[:50]}")

        # 4. 기술 지식 감지 (예: "~는 ~이야", "~의 치수/규격/스펙은 ~")
        knowledge_patterns = [
            r'([A-Z0-9\-]+)(?:의|는|은)\s*(?:치수|규격|스펙|사양)(?:는|은|이)?\s*([0-9×xX\-\s\.,]+(?:mm|cm|m)?)',
            r'([가-힣A-Za-z0-9\-]+)(?:는|은|이)\s*([가-힣A-Za-z0-9\s]+)(?:이야|야|입니다|임)',
        ]

        for pattern in knowledge_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                if len(match) >= 2:
                    title = match[0].strip()
                    content = f"{match[0]}: {match[1]}"
                    if len(title) > 2 and len(content) > 5:
                        item = learner.save_knowledge(
                            title=title,
                            content=content,
                            category="KNOWLEDGE",
                            source="대화 자동 감지"
                        )
                        saved_items.append({"type": "knowledge", "title": title, "content": content[:100]})
                        logger.info(f"RAG 학습: 지식 저장 - {title}")

        if saved_items:
            return {"saved_count": len(saved_items), "items": saved_items}
        return None

    @classmethod
    async def _handle_conversation(cls, intent: ParsedIntent, user_message: str, recent_messages: list = None) -> ChatResponse:
        """General conversation handler - Claude API with enhanced knowledge

        Args:
            intent: 파싱된 의도
            user_message: 사용자 메시지
            recent_messages: 프론트엔드에서 전달받은 최근 대화 히스토리 (우선 사용)
        """
        import anthropic

        # Memory context - 프론트엔드 히스토리 우선, 없으면 지식 서비스 사용
        messages = []
        has_history = False

        # 1순위: 프론트엔드에서 전달받은 recent_messages
        if recent_messages and len(recent_messages) > 0:
            for msg in recent_messages[-30:]:  # 최근 30개 메시지
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})
            has_history = len(messages) > 0
            logger.info(f"[HISTORY] 프론트엔드 히스토리 사용: {len(messages)}개 메시지")

        # 2순위: 지식 서비스 기반 메모리
        if not has_history:
            messages = await load_conversation_memory()
            has_history = len(messages) > 0
            if has_history:
                logger.info(f"[HISTORY] 지식 서비스 메모리 사용: {len(messages)}개 메시지")

        # 강화된 시스템 프롬프트 (CLAUDE_KNOWLEDGE.md 포함)
        system_prompt = get_estimate_system_prompt(has_history=has_history)

        messages.append({"role": "user", "content": user_message})

        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=2048,
                system=system_prompt,
                messages=messages
            )

            ai_response = response.content[0].text

            # RAG 학습: 대화 중 지식/노하우/단가 자동 감지 및 저장
            learning_result = None
            try:
                learning_result = cls._detect_and_save_knowledge(user_message, ai_response)
            except Exception as learn_err:
                # 학습 실패해도 대화는 계속 진행
                pass

            # Save to memory - 지식 서비스 사용
            await save_conversation_memory(user_message, ai_response)

            # Build action_result with learning info if any
            action_result = {
                "type": "conversation",
                "status": "success"
            }
            if learning_result:
                action_result["learning"] = learning_result

            return ChatResponse(
                message=ai_response,
                intent=intent,
                model="claude-opus",
                model_info={
                    "name": "Claude 4.5 Opus",
                    "description": "Narberal Gamma AI - Conversation Mode",
                    "provider": "anthropic"
                },
                action_result=action_result,
                suggestions=["estimate", "drawing", "help"]
            )

        except Exception as e:
            return ChatResponse(
                message=f"Sorry, an error occurred: {str(e)[:100]}",
                intent=intent,
                model="claude-opus",
                action_result={"type": "conversation", "status": "error", "error": str(e)},
                suggestions=["retry", "help"]
            )

    @classmethod
    async def _handle_image_analysis(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """이미지/첨부파일에서 정보 추출 처리

        사용자가 이전에 업로드한 파일에서 특정 정보를 찾는 요청 처리
        예: "거래처명 찾아줘", "업체명 뭐야?"
        """
        try:
            # user_message에 이미 이미지 분석 결과가 포함되어 있음
            # (chat() 엔드포인트에서 analyze_image_with_claude 호출됨)
            client = get_claude_client()
            if client is None:
                return ChatResponse(
                    message="❌ Claude API 연결 실패. API 키를 확인해주세요.",
                    intent=intent,
                    suggestions=["다시 시도", "도움말"],
                )

            # 사용자가 요청한 정보 추출을 위한 프롬프트
            extraction_prompt = f"""당신은 전기 분전반 도면/견적서 분석 전문가입니다.
사용자가 첨부한 파일에서 정보를 추출하여 질문에 답변해주세요.

**사용자 요청:**
{user_message}

**추출할 정보:**
- 요청한 정보를 명확하게 추출
- 찾을 수 없으면 "해당 정보를 찾을 수 없습니다" 응답
- 관련 추가 정보도 함께 제공

**응답 형식:**
- 간결하고 명확하게
- 찾은 정보를 강조 표시 (**굵게**)"""

            response = client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=1024,
                messages=[{"role": "user", "content": extraction_prompt}]
            )

            if response.content and len(response.content) > 0:
                analysis_result = response.content[0].text
                return ChatResponse(
                    message=f"📋 **파일 분석 결과**\n\n{analysis_result}",
                    intent=intent,
                    action_result={
                        "type": "image_analysis",
                        "status": "success",
                    },
                    suggestions=["견적 생성해줘", "다른 정보 찾기", "도면 분석"],
                )

            return ChatResponse(
                message="❌ 파일에서 요청한 정보를 찾을 수 없습니다.\n파일을 다시 업로드하거나 질문을 더 구체적으로 해주세요.",
                intent=intent,
                suggestions=["파일 다시 업로드", "도움말"],
            )

        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return ChatResponse(
                message=f"❌ 파일 분석 중 오류 발생: {str(e)[:100]}",
                intent=intent,
                suggestions=["다시 시도", "도움말"],
            )

    @classmethod
    def _handle_unknown(cls, intent: ParsedIntent, user_message: str) -> ChatResponse:
        """알 수 없는 의도 - RAG 검색 후 일반 대화로 처리"""
        # unknown인 경우에도 RAG 검색 시도
        retriever = get_rag_retriever()

        if retriever is not None:
            try:
                results = retriever.search(user_message, top_k=3)
                if results and results[0].score > 0.5:
                    # 관련 지식이 있으면 knowledge로 처리
                    return cls._handle_knowledge(intent, user_message)
            except Exception:
                pass

        # RAG에 관련 지식 없으면 일반 대화로 처리 (Claude 활용)
        # 일반 업무 비서로서 모든 질문에 응답
        return cls._handle_conversation(intent, user_message)


# ===== API 엔드포인트 =====
async def analyze_image_with_claude(attachments: list[FileAttachment], user_message: str) -> str:
    """
    Claude Vision API를 사용하여 이미지 분석

    Args:
        attachments: 첨부파일 목록
        user_message: 사용자 메시지

    Returns:
        분석된 이미지 내용 + 사용자 메시지
    """
    import anthropic
    import base64
    import httpx
    from pathlib import Path

    client = anthropic.Anthropic()

    # 이미지 첨부파일 필터링
    image_attachments = [
        att for att in attachments
        if att.type.startswith("image/") or att.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
    ]

    if not image_attachments:
        return user_message

    # Claude Vision API 메시지 구성
    content = []

    for att in image_attachments:
        if att.url:
            # base64 데이터인 경우
            if att.url.startswith("data:"):
                # data:image/jpeg;base64,... 형식
                parts = att.url.split(",", 1)
                if len(parts) == 2:
                    media_type_part = parts[0].split(";")[0].replace("data:", "")
                    base64_data = parts[1]
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type_part or "image/jpeg",
                            "data": base64_data
                        }
                    })
            # URL인 경우
            elif att.url.startswith("http"):
                # URL에서 이미지 다운로드 후 base64 인코딩
                try:
                    async with httpx.AsyncClient() as http_client:
                        resp = await http_client.get(att.url)
                        if resp.status_code == 200:
                            image_data = base64.standard_b64encode(resp.content).decode("utf-8")
                            media_type = resp.headers.get("content-type", "image/jpeg")
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            })
                except Exception as e:
                    logger.warning(f"Failed to download image from URL: {e}")
            # 로컬 파일 경로인 경우
            else:
                try:
                    file_path = Path(att.url)
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
                        # 확장자로 미디어 타입 추정
                        ext = file_path.suffix.lower()
                        media_type_map = {
                            ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg",
                            ".png": "image/png",
                            ".gif": "image/gif",
                            ".webp": "image/webp"
                        }
                        media_type = media_type_map.get(ext, "image/jpeg")
                        content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        })
                except Exception as e:
                    logger.warning(f"Failed to read local image: {e}")

    if not content:
        return user_message

    # 이미지 분석 요청 추가 — 구조화된 견적 파라미터 추출 포함
    content.append({
        "type": "text",
        "text": f"""이 이미지를 분석해주세요.

★★★ 핵심 규칙 ★★★
전기 분전반 도면, 견적서, 스펙시트, 단선결선도 등 전기 패널 관련 이미지인 경우:
사용자가 "견적" 키워드를 말하지 않더라도, 도면 이미지를 보냈다는 것 자체가 견적 의도입니다.
반드시 아래 JSON 블록을 응답에 포함해주세요.

이미지에서 다음 정보를 추출하세요:
1. 분전반명 (있으면)
2. 메인 차단기: 종류(MCCB/ELB), 극수(P), 프레임(AF), 트립(AT)
3. 분기 차단기: 종류별, 극수, 프레임(AF), 트립(AT), 수량, 용도(라벨)
4. 외함: 종류(옥내노출/매입함/옥외 등), 재질(STEEL/SUS 등)
5. 고객/업체명 (있으면)
6. 전압 (있으면)
7. 부속자재 (마그네트, 타이머, 계량기 등)

추출 후 반드시 아래 형식의 JSON 블록을 포함하세요:

```estimate_json
{{
  "is_panel_diagram": true,
  "panel_name": "분전반명 또는 null",
  "main_breaker": {{"breaker_type": "MCCB", "poles": 4, "ampere_frame": 50, "ampere_trip": 30}},
  "branch_breakers": [
    {{"breaker_type": "MCCB", "poles": 2, "ampere_frame": 30, "ampere_trip": 20, "quantity": 8, "label": "전등"}}
  ],
  "enclosure": {{"type": "매입함", "material": "SUS"}},
  "customer_name": "고객명 또는 null",
  "voltage": "전압 또는 null",
  "accessories": []
}}
```

규칙:
- AF(프레임)와 AT(트립)를 구분하세요. 예: 50AF 30AT → ampere_frame=50, ampere_trip=30
- 극수는 숫자만: 4P → poles=4, 2P → poles=2
- MCCB = 배선용차단기, ELB = 누전차단기, CBR = MCCB로 처리
- 분기 차단기는 같은 스펙이면 수량으로 합치세요
- SPARE는 제외하세요
- 전기 도면이 아닌 경우 is_panel_diagram: false로 설정

사용자 요청: {user_message}"""
    })

    try:
        # Claude Vision API 호출
        response = client.messages.create(
            model="claude-opus-4-5-20251101",  # Vision 지원 모델
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )

        # 분석 결과 추출
        if response.content and len(response.content) > 0:
            extracted_text = response.content[0].text
            logger.info(f"Image analysis completed: {len(extracted_text)} chars")
            return f"[이미지 분석 결과]\n{extracted_text}\n\n[사용자 요청]\n{user_message}"

    except Exception as e:
        logger.error(f"Claude Vision API error: {e}")
        return f"[이미지 첨부됨: {', '.join(att.name for att in image_attachments)}]\n{user_message}"

    return user_message


def _extract_panel_json_from_vision(vision_text: str) -> dict | None:
    """
    비전 분석 결과에서 구조화된 견적 파라미터 JSON 추출

    analyze_image_with_claude()가 반환한 텍스트에서
    ```estimate_json ... ``` 블록을 찾아 파싱합니다.
    """
    # estimate_json 블록 추출
    json_match = re.search(r'```estimate_json\s*(.*?)\s*```', vision_text, re.DOTALL)
    if not json_match:
        # 일반 json 블록에서도 시도
        json_match = re.search(r'```json\s*(.*?)\s*```', vision_text, re.DOTALL)

    if not json_match:
        return None

    try:
        panel_data = json.loads(json_match.group(1))
        if panel_data.get("is_panel_diagram"):
            logger.info(f"[VISION→ESTIMATE] 도면에서 견적 파라미터 추출 성공: "
                        f"메인={panel_data.get('main_breaker')}, "
                        f"분기={len(panel_data.get('branch_breakers', []))}종")
            return panel_data
    except json.JSONDecodeError as e:
        logger.warning(f"[VISION→ESTIMATE] JSON 파싱 실패: {e}")

    return None


def _convert_vision_panel_to_intent_params(panel_data: dict) -> dict:
    """
    비전 분석에서 추출된 도면 JSON → NLP 파서 호환 intent params 변환

    AI가 이미지에서 추론한 구조화된 데이터를 견적 파이프라인 입력으로 변환합니다.
    """
    params = {}

    # 메인 차단기
    mb = panel_data.get("main_breaker")
    if mb:
        params["main_breaker"] = {
            "breaker_type": mb.get("breaker_type", "MCCB"),
            "poles": mb.get("poles", 4),
            "current": mb.get("ampere_trip") or mb.get("ampere_frame", 100),
        }

    # 분기 차단기
    branch_list = panel_data.get("branch_breakers", [])
    if branch_list:
        params["branch_breakers"] = []
        for br in branch_list:
            params["branch_breakers"].append({
                "breaker_type": br.get("breaker_type", "MCCB"),
                "poles": br.get("poles", 2),
                "current": br.get("ampere_trip") or br.get("ampere_frame", 20),
                "quantity": br.get("quantity", 1),
            })

    # 외함
    enc = panel_data.get("enclosure")
    if enc:
        enc_type = enc.get("type", "옥내노출")
        material = enc.get("material", "STEEL 1.6T")
        # 외함 종류 보정 (AI 비전이 약칭 반환할 수 있음)
        enc_type_map = {
            "매입": "매입함", "옥내": "옥내노출", "옥외": "옥외노출",
            "전주": "전주부착형", "FRP": "FRP함",
        }
        enc_type = enc_type_map.get(enc_type, enc_type)
        # SUS → SUS201 1.2T 기본 매핑
        if material and "SUS" in material.upper() and "1.2T" not in material:
            material = "SUS201 1.2T"
        elif material and "STEEL" in material.upper() and "T" not in material:
            material = "STEEL 1.6T"
        params["enclosure_type"] = enc_type
        params["enclosure_material"] = material

    # 고객명
    customer = panel_data.get("customer_name")
    if customer and customer != "null":
        params["customer_name"] = customer

    # 분전반명
    panel_name = panel_data.get("panel_name")
    if panel_name and panel_name != "null":
        params["panel_name"] = panel_name

    # 브랜드 (기본값)
    params["brand"] = "상도차단기"

    return params


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    AI 채팅 엔드포인트

    자연어 입력을 받아 견적/도면/이메일/ERP 작업을 처리합니다.

    **예시 입력:**
    - "상도 4P 100A 메인, 3P 30A 분기 10개로 견적해줘"
    - "도면 생성해줘"
    - "견적서 이메일 보내줘"
    """
    try:
        # 모델 유효성 검증
        model = request.model
        if model not in AI_MODELS:
            model = "claude-opus"  # 기본 모델로 폴백

        model_info = AI_MODELS.get(model)
        logger.info(f"Using AI model: {model} ({model_info['name']})")

        # 사용자 메시지 추출 (messages[] 또는 message 필드에서)
        user_message = request.get_user_message()
        if not user_message:
            raise HTTPException(status_code=400, detail="메시지가 비어있습니다")

        # 첨부파일이 있으면 이미지 분석 먼저 수행
        message_to_parse = user_message
        vision_panel_data = None  # AI 비전에서 추출한 구조화된 도면 데이터
        if request.attachments:
            logger.info(f"Processing {len(request.attachments)} attachments")
            message_to_parse = await analyze_image_with_claude(request.attachments, user_message)
            logger.info(f"Message after image analysis: {message_to_parse[:200]}...")

            # ★ AI 추론: 이미지에서 구조화된 도면 데이터가 추출되었는지 확인
            vision_panel_data = _extract_panel_json_from_vision(message_to_parse)

        # ★ AI 의도 추론: 도면 이미지에서 견적 파라미터가 추출된 경우 → 자동 견적 의도
        if vision_panel_data:
            logger.info("[AI 의도 추론] 도면 이미지 감지 → 견적 의도로 자동 라우팅")
            intent_params = _convert_vision_panel_to_intent_params(vision_panel_data)
            intent = ParsedIntent(
                intent="estimate",
                confidence=0.95,
                params=intent_params
            )
        else:
            # 자연어 파싱 (이전 대화 컨텍스트 및 첨부파일 정보 전달)
            # request.context에는 recentMessages, currentVisualization 등이 포함됨
            # request.attachments에는 현재 요청의 첨부파일 목록이 포함됨
            attachments_dict = None
            if request.attachments:
                attachments_dict = [att.model_dump() if hasattr(att, 'model_dump') else dict(att) for att in request.attachments]

            intent = NLPParser.parse(message_to_parse, request.context, attachments_dict)
            logger.info(f"Parsed intent: {intent.intent} with confidence {intent.confidence}, context: {bool(request.context)}, attachments: {bool(request.attachments)}")

        # 응답 생성 (async 핸들러 포함)
        response = await ResponseGenerator.generate(intent, message_to_parse)

        # 모델 정보 추가
        response.model = model
        response.model_info = model_info

        return response

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/models")
async def get_available_models():
    """
    사용 가능한 AI 모델 목록

    Returns:
        dict: AI 모델 목록 및 정보
    """
    return {
        "models": [
            {
                "id": model_id,
                "name": info["name"],
                "description": info["description"],
                "provider": info["provider"],
            }
            for model_id, info in AI_MODELS.items()
        ],
        "default": "claude-opus",
    }


@router.get("/intents")
async def get_supported_intents():
    """지원되는 의도 목록"""
    return {
        "intents": [
            {
                "name": "estimate",
                "description": "견적 생성",
                "keywords": NLPParser.INTENT_KEYWORDS["estimate"],
                "example": "상도 4P 100A 메인, 3P 30A 분기 10개",
            },
            {
                "name": "drawing",
                "description": "도면 생성",
                "keywords": NLPParser.INTENT_KEYWORDS["drawing"],
                "example": "단선결선도 생성해줘",
            },
            {
                "name": "email",
                "description": "이메일 발송",
                "keywords": NLPParser.INTENT_KEYWORDS["email"],
                "example": "견적서 이메일 보내줘",
            },
            {
                "name": "erp",
                "description": "ERP 연동",
                "keywords": NLPParser.INTENT_KEYWORDS["erp"],
                "example": "발주 등록해줘",
            },
        ],
        "brands": list(NLPParser.BRANDS.values()),
        "enclosure_types": NLPParser.ENCLOSURE_TYPES,
    }
