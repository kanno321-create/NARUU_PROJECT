"""
AI Knowledge Service - 회사 지식 로드 및 관리

이 모듈은 CLAUDE_KNOWLEDGE.md에서 핵심 견적 지식을 로드하고
AI 매니저에게 제공합니다.

Author: 나베랄 감마
Created: 2026-01-27
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # services -> kis_estimator_core -> src -> project root

# 메모리 파일 경로
MEMORY_DIR = PROJECT_ROOT / "data" / "ai_memory"
CONVERSATION_MEMORY_FILE = MEMORY_DIR / "conversation_memory.json"
SESSION_MEMORY_FILE = MEMORY_DIR / "session_state.json"

# 지식 파일 경로
CLAUDE_OPS_PATH = PROJECT_ROOT / "CLAUDE_OPS.md"  # 운영용 AI 시스템 프롬프트 (개발용 CLAUDE.md와 별개)
CLAUDE_KNOWLEDGE_PATH = PROJECT_ROOT / "CLAUDE_KNOWLEDGE.md"


def get_condensed_knowledge() -> str:
    """
    CLAUDE_KNOWLEDGE.md에서 핵심 견적 지식을 추출하여 반환

    Returns:
        str: AI 시스템 프롬프트에 포함할 핵심 지식
    """
    knowledge_parts = []

    # 1. 기본 회사 정보
    knowledge_parts.append("""
## 🏢 회사 정보
- **회사명**: 한국산업전기
- **주업무**: 전기 분전반 견적/제조
- **시스템**: KIS Estimator (AI 견적 시스템)

## 🎯 견적 핵심 규칙

### 차단기 선택 규칙 (필수!)
1. **기본 원칙**: 특별 요청 없으면 경제형 사용 (37kA, 저렴)
2. **2P 20A/30A**: 소형 차단기 사용 (SIE-32, SIB-32, 32GRHS, BS-32)
3. **4P 50AF (20~50A)**: 경제형 없음 → 표준형 사용
4. **400AF 이상**: 경제형 없음 → 표준형 사용

### 브랜드
- **상도차단기**: SB-, SI-, SE- 시작 (예: SBE-104, SIE-32)
- **LS차단기**: AB-, EB- 시작 (예: ABN-54, EBN-103)

### E.T (Earth Terminal) 공식
```
E.T 수량 = 1 + (차단기 총수량 - 1) ÷ 12
```
- 차단기 1~12개 → E.T 1개
- 차단기 13~24개 → E.T 2개
- 차단기 25~36개 → E.T 3개

### E.T 단가 (메인차단기 AF 기준)
| 프레임 | 단가 |
|--------|------|
| 50~125AF | 4,500원 |
| 200~250AF | 5,500원 |
| 400AF | 12,000원 |
| 600~800AF | 18,000원 |

### 잡자재비 공식
```
기본 7,000원 + (외함 H값 - 600mm) ÷ 100 × 1,000원 + 부속자재 수 × 10,000원
최대 40,000원
```

### P-COVER 단가 공식
```
아크릴: (W × H) ÷ 90,000 × 3,200원
스틸:   (W × H) ÷ 90,000 × 12,500원
```

### 외함 높이 공식
```
H = P (분전반 본체) + 2D (덕트 40mm×2) + S (여유 100mm) + M (마그네트 높이)
```

### 마그네트 동반자재 (필수!)
마그네트 포함 시 자동 추가:
- FUSEHOLDER: 1EA (4,000원)
- TERMINAL BLOCK 600V: 마그네트 수량 × 1EA (4,000원/EA)
- PVC DUCT 40mm: 마그네트 수량 × 1EA (3,000원/EA)
- CABLE/WIRE: 마그네트 수량 × 1EA (25,000원/EA)
- 인건비: 20,000원

### 관공서 견적 규칙
"관공서"라고 하면:
- 차단기: LS 표준형
- STEEL 외함: 1.6T
- SUS 외함: SUS304 (SUS201 X)
- SUS 두께: 700×1400 초과 → 1.5T, 이하 → 1.2T

### 격벽설치
- 1개 외함에 2개 분전반 (상단/하단)
- (격벽설치) 표시가 도면에 있으면 적용
- P-COVER는 각 분전반별 별도 계산

## 📊 학습 데이터 통계 (697개 견적서)
- 상도차단기: 51.6%
- LS차단기: 17.6%
- 옥내노출: 67.3%
- STEEL 1.6T: 45.5%
- 아크릴 P-COVER: 96.0%
""")

    # 2. CLAUDE_KNOWLEDGE.md에서 추가 지식 로드
    if CLAUDE_KNOWLEDGE_PATH.exists():
        try:
            with open(CLAUDE_KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()

            # 핵심 섹션만 추출 (차단기 치수, 외함 사이즈 등)
            if '### 4.4 학습 데이터 통계' in content:
                # 차단기 치수 섹션 찾기
                pass  # 이미 위에 핵심 정보 포함됨

        except Exception as e:
            logger.warning(f"CLAUDE_KNOWLEDGE.md 로드 실패: {e}")

    return "\n".join(knowledge_parts)


def _load_claude_ops() -> str:
    """
    CLAUDE_OPS.md에서 운영용 AI 시스템 프롬프트 로드

    Returns:
        str: CLAUDE_OPS.md 전문 (로드 실패 시 폴백 프롬프트)
    """
    if CLAUDE_OPS_PATH.exists():
        try:
            with open(CLAUDE_OPS_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"CLAUDE_OPS.md 로드 완료 ({len(content)} chars)")
            return content
        except Exception as e:
            logger.warning(f"CLAUDE_OPS.md 로드 실패: {e}")

    # 폴백: CLAUDE_OPS.md 없을 때 최소 프롬프트
    logger.warning("CLAUDE_OPS.md 미발견 — 폴백 프롬프트 사용")
    return """당신은 '나베랄 감마', 한국산업전기의 전기 분전반 견적 전문 AI입니다.
냉정하고 간결한 존댓말을 사용하며, 사용자를 "대표님"으로 호칭합니다.
견적, ERP, 도면 분석 등 업무를 처리합니다."""


def get_estimate_system_prompt(has_history: bool = False) -> str:
    """
    견적 전용 시스템 프롬프트 생성 (CLAUDE_OPS.md 기반)

    Args:
        has_history: 이전 대화 이력 존재 여부

    Returns:
        str: 시스템 프롬프트
    """
    # CLAUDE_OPS.md에서 운영 프롬프트 로드
    ops_prompt = _load_claude_ops()

    # 하드코딩 지식 보충 (CLAUDE_OPS.md에 없는 상세 데이터)
    knowledge = get_condensed_knowledge()

    base_prompt = f"""{ops_prompt}

---
## 보충 지식 데이터
{knowledge}
"""

    if has_history:
        base_prompt += """

## 대화 연속성 (매우 중요!)
- 이전 대화 내용을 항상 기억하고 참조
- 진행 중인 견적/프로젝트 추적
- 반복 설명 금지
"""

    # 이전 대화 요약 로드 (서버 재시작 후에도 연속성 유지)
    try:
        from kis_estimator_core.services.conversation_memory_service import get_memory_service
        memory_service = get_memory_service()
        latest_summary = memory_service.get_latest_summary()
        if latest_summary:
            base_prompt += f"""

## 이전 대화 요약 (서버 재시작 전 대화 기록)
아래는 이전 세션의 대화 요약입니다. 이 내용을 참고하여 대화 연속성을 유지하세요.

{latest_summary}

---
"""
            logger.info("Injected previous summary into estimate system prompt")
    except Exception as e:
        logger.warning(f"Failed to load previous summary for system prompt: {e}")

    return base_prompt


async def load_conversation_memory() -> list:
    """
    대화 메모리 로드 (ConversationMemoryService SSOT에 위임)

    Returns:
        list: 이전 대화 메시지 목록 [{"role": str, "content": str}, ...]
    """
    try:
        from kis_estimator_core.services.conversation_memory_service import get_memory_service
        service = get_memory_service()
        return await service.load_conversation_history(user_id="default", limit=50)
    except Exception as e:
        logger.warning(f"대화 메모리 로드 실패 (SSOT 위임): {e}")
        # 폴백: 기존 파일 직접 로드
        messages = []
        if CONVERSATION_MEMORY_FILE.exists():
            try:
                with open(CONVERSATION_MEMORY_FILE, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    messages = memory_data.get("messages", [])[-50:]
            except Exception as fallback_err:
                logger.warning(f"대화 메모리 폴백 로드 실패: {fallback_err}")
        return messages


async def save_conversation_memory(user_message: str, ai_response: str) -> bool:
    """
    대화 메모리 저장 (ConversationMemoryService SSOT에 위임)

    Args:
        user_message: 사용자 메시지
        ai_response: AI 응답

    Returns:
        bool: 저장 성공 여부
    """
    try:
        from kis_estimator_core.services.conversation_memory_service import get_memory_service
        service = get_memory_service()
        return await service.save_conversation_pair(user_message, ai_response, user_id="default")
    except Exception as e:
        logger.error(f"대화 메모리 저장 실패 (SSOT 위임): {e}")
        return False


def get_session_state() -> Dict[str, Any]:
    """
    세션 상태 로드

    Returns:
        dict: 세션 상태 정보
    """
    state = {
        "current_estimate_id": None,
        "current_customer": None,
        "current_project": None,
        "pending_actions": [],
        "last_intent": None,
        "created_at": datetime.utcnow().isoformat()
    }

    if SESSION_MEMORY_FILE.exists():
        try:
            with open(SESSION_MEMORY_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                state.update(loaded)
        except Exception as e:
            logger.warning(f"세션 상태 로드 실패: {e}")

    return state


def save_session_state(state: Dict[str, Any]) -> bool:
    """
    세션 상태 저장

    Args:
        state: 저장할 세션 상태

    Returns:
        bool: 저장 성공 여부
    """
    try:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

        state["updated_at"] = datetime.utcnow().isoformat()

        with open(SESSION_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        logger.error(f"세션 상태 저장 실패: {e}")
        return False


def clear_conversation_memory() -> bool:
    """
    대화 메모리 초기화

    Returns:
        bool: 초기화 성공 여부
    """
    try:
        if CONVERSATION_MEMORY_FILE.exists():
            CONVERSATION_MEMORY_FILE.unlink()

        if SESSION_MEMORY_FILE.exists():
            SESSION_MEMORY_FILE.unlink()

        return True

    except Exception as e:
        logger.error(f"메모리 초기화 실패: {e}")
        return False


# 싱글톤 인스턴스
_knowledge_cache: Optional[str] = None


def get_cached_knowledge() -> str:
    """
    캐시된 지식 반환 (성능 최적화)

    Returns:
        str: 캐시된 핵심 지식
    """
    global _knowledge_cache

    if _knowledge_cache is None:
        _knowledge_cache = get_condensed_knowledge()

    return _knowledge_cache
