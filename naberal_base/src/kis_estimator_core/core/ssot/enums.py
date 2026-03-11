"""
SSOT Enums - 모든 Enum 타입 중앙 정의

절대 원칙:
- 모든 Enum/TypedDict는 여기서만 정의
- 코드에서 직접 Enum 정의 금지
- 변경 시 이 파일만 수정

LAW-02: SSOT 위반 금지 - 단일 출처만 참조
"""

from enum import Enum

# ============================================================
# Catalog Enums (models/catalog.py에서 이관)
# ============================================================


class BreakerCategory(str, Enum):
    """차단기 카테고리"""

    MCCB = "MCCB"  # 배선용차단기
    ELB = "ELB"  # 누전차단기


class BreakerSeries(str, Enum):
    """차단기 시리즈"""

    ECONOMY = "경제형"
    STANDARD = "표준형"
    SMALL = "소형"  # SIB-32, SIE-32, BS-32, 32GRHS
    COMPACT = "컴팩트"  # SBC-52, ABS52FB (FB타입)


class Brand(str, Enum):
    """브랜드"""

    SADOELE = "상도차단기"
    LSIS = "LS산전"
    LSIS_ALT = "LS차단기"  # ai_catalog_v1.json 호환
    HDELECTRIC = "현대일렉트릭"
    KISCO = "한국산업"


class EnclosureType(str, Enum):
    """외함 종류 (ai_estimation_core.json 기준)"""

    INDOOR_EXPOSED = "옥내노출"
    OUTDOOR_EXPOSED = "옥외노출"
    INDOOR_STANDALONE = "옥내자립"
    OUTDOOR_STANDALONE = "옥외자립"
    EMBEDDED = "매입함"
    # 2026-02-06 추가 (지식파일 일관성 검사)
    POLE_MOUNTED = "전주부착형"
    FRP = "FRP함"
    HIBOX = "하이박스"


class EnclosureMaterial(str, Enum):
    """외함 재질"""

    STEEL_16T = "STEEL 1.6T"
    STEEL_10T = "STEEL 1.0T"
    SUS201_12T = "SUS201 1.2T"


# ============================================================
# Error Enums (errors/error_codes.py에서 이관)
# ============================================================


class ErrorSeverity(Enum):
    """에러 심각도"""

    BLOCKING = "BLOCKING"  # 다음 단계 진행 불가
    WARNING = "WARNING"  # 경고만 표시
    INFO = "INFO"  # 정보성 메시지


class ErrorCategory(Enum):
    """에러 카테고리"""

    INPUT = "INPUT"  # 입력 데이터 오류
    CATALOG = "CATALOG"  # 카탈로그 검증 오류
    BREAKER = "BREAKER"  # 차단기 관련 오류
    ENCLOSURE = "ENCLOSURE"  # 외함 관련 오류
    ACCESSORY = "ACCESSORY"  # 부속자재 오류
    LAYOUT = "LAYOUT"  # 배치 오류
    CALCULATION = "CALCULATION"  # 계산 오류


# ============================================================
# Quality Gate Enums (infra/quality_gate.py에서 이관)
# ============================================================


class QualityGateOperator(str, Enum):
    """Supported comparison operators for quality gates"""

    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


# ============================================================
# RAG Enums (rag/ 모듈에서 SSOT 통합)
# ============================================================


class RAGCategory(str, Enum):
    """RAG 문서 카테고리"""

    BREAKER = "BREAKER"  # 차단기 지식
    ENCLOSURE = "ENCLOSURE"  # 외함 지식
    ACCESSORY = "ACCESSORY"  # 부속자재 지식
    FORMULA = "FORMULA"  # 계산 공식
    STANDARD = "STANDARD"  # IEC/KS 표준
    PRICE = "PRICE"  # 가격 정보
    RULE = "RULE"  # 비즈니스 규칙


class RAGSearchType(str, Enum):
    """RAG 검색 유형"""

    SEMANTIC = "semantic"  # 의미 기반 검색 (벡터)
    KEYWORD = "keyword"  # 키워드 기반 검색 (BM25)
    HYBRID = "hybrid"  # 하이브리드 검색 (RRF)
