"""
OCR Service - 손글씨 및 문서 텍스트 인식 서비스

EasyOCR (로컬) + Claude Vision (클라우드) 하이브리드 방식
- 일반 텍스트/인쇄물: EasyOCR (빠름, 무료)
- 손글씨/복잡한 이미지: Claude Vision (정확도 높음)

Contract-First + Zero-Mock
NO MOCKS - Real OCR processing only
"""

import base64
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# EasyOCR 임포트
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR not available. Local OCR will be disabled.")

# Anthropic 임포트 (Claude Vision)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not available. Claude Vision will be disabled.")


class OCREngine(str, Enum):
    """OCR 엔진 선택"""
    EASYOCR = "easyocr"       # 로컬, 빠름, 인쇄물 최적
    CLAUDE_VISION = "claude"  # 클라우드, 정확함, 손글씨 최적
    AUTO = "auto"             # 자동 선택


class DocumentType(str, Enum):
    """문서 유형"""
    PRINTED = "printed"       # 인쇄물
    HANDWRITTEN = "handwritten"  # 손글씨
    MIXED = "mixed"           # 혼합
    DRAWING = "drawing"       # 도면
    UNKNOWN = "unknown"


@dataclass
class OCRResult:
    """OCR 결과"""
    text: str                      # 추출된 텍스트
    confidence: float              # 신뢰도 (0-1)
    engine_used: OCREngine         # 사용된 엔진
    document_type: DocumentType    # 감지된 문서 유형
    bounding_boxes: list[dict]     # 텍스트 영역 좌표
    processing_time_ms: float      # 처리 시간
    metadata: dict                 # 추가 메타데이터


class OCRService:
    """
    하이브리드 OCR 서비스

    특징:
    - EasyOCR: 로컬 GPU 가속, 한글/영어 지원
    - Claude Vision: 손글씨 인식, 복잡한 레이아웃
    - 자동 엔진 선택 (문서 특성 기반)
    """

    _instance: Optional['OCRService'] = None
    _easyocr_reader: Any = None
    _anthropic_client: Any = None

    # Claude Vision 설정
    CLAUDE_MODEL = "claude-sonnet-4-20250514"
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB

    def __new__(cls) -> 'OCRService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """OCR 엔진 초기화"""
        # EasyOCR 초기화 (한글 + 영어)
        if EASYOCR_AVAILABLE:
            try:
                self._easyocr_reader = easyocr.Reader(
                    ['ko', 'en'],
                    gpu=True,  # GPU 사용 (RTX 4080 Super)
                    verbose=False,
                )
                logger.info("EasyOCR initialized with GPU support")
            except Exception as e:
                logger.warning(f"EasyOCR GPU init failed, trying CPU: {e}")
                try:
                    self._easyocr_reader = easyocr.Reader(
                        ['ko', 'en'],
                        gpu=False,
                        verbose=False,
                    )
                    logger.info("EasyOCR initialized with CPU")
                except Exception as e2:
                    logger.error(f"EasyOCR init failed: {e2}")

        # Anthropic 클라이언트 초기화
        if ANTHROPIC_AVAILABLE:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    self._anthropic_client = anthropic.Anthropic(api_key=api_key)
                    logger.info("Claude Vision initialized")
                except Exception as e:
                    logger.error(f"Anthropic init failed: {e}")
            else:
                logger.warning("ANTHROPIC_API_KEY not set")

    def _image_to_base64(self, image_path: str | Path) -> tuple[str, str]:
        """이미지를 base64로 변환"""
        path = Path(image_path)

        # MIME 타입 결정
        suffix = path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        mime_type = mime_types.get(suffix, 'image/jpeg')

        with open(path, 'rb') as f:
            image_data = f.read()

        return base64.standard_b64encode(image_data).decode('utf-8'), mime_type

    def _detect_document_type(self, image_path: str | Path) -> DocumentType:
        """
        문서 유형 자동 감지 (간단한 휴리스틱)

        실제로는 이미지 분석을 통해 더 정확하게 판별해야 함
        """
        # 파일 이름 기반 힌트
        path_str = str(image_path).lower()

        if 'handwritten' in path_str or '손글씨' in path_str or 'memo' in path_str:
            return DocumentType.HANDWRITTEN
        elif 'drawing' in path_str or '도면' in path_str or 'cad' in path_str:
            return DocumentType.DRAWING
        elif 'scan' in path_str or '스캔' in path_str:
            return DocumentType.PRINTED

        return DocumentType.UNKNOWN

    def _select_engine(
        self,
        document_type: DocumentType,
        preferred_engine: OCREngine,
    ) -> OCREngine:
        """최적 엔진 선택"""
        if preferred_engine != OCREngine.AUTO:
            return preferred_engine

        # 손글씨는 Claude Vision 권장
        if document_type == DocumentType.HANDWRITTEN:
            if self._anthropic_client:
                return OCREngine.CLAUDE_VISION
            elif self._easyocr_reader:
                return OCREngine.EASYOCR

        # 인쇄물/도면은 EasyOCR 권장 (빠름)
        if document_type in (DocumentType.PRINTED, DocumentType.DRAWING):
            if self._easyocr_reader:
                return OCREngine.EASYOCR
            elif self._anthropic_client:
                return OCREngine.CLAUDE_VISION

        # 기본: 사용 가능한 엔진
        if self._easyocr_reader:
            return OCREngine.EASYOCR
        elif self._anthropic_client:
            return OCREngine.CLAUDE_VISION

        raise RuntimeError("No OCR engine available")

    def _ocr_with_easyocr(self, image_path: str | Path) -> tuple[str, list[dict], float]:
        """EasyOCR로 OCR 수행"""
        if not self._easyocr_reader:
            raise RuntimeError("EasyOCR not initialized")

        results = self._easyocr_reader.readtext(str(image_path))

        text_parts = []
        bounding_boxes = []
        total_confidence = 0.0

        for bbox, text, confidence in results:
            text_parts.append(text)
            bounding_boxes.append({
                "text": text,
                "bbox": bbox,
                "confidence": confidence,
            })
            total_confidence += confidence

        full_text = ' '.join(text_parts)
        avg_confidence = total_confidence / len(results) if results else 0.0

        return full_text, bounding_boxes, avg_confidence

    def _ocr_with_claude(
        self,
        image_path: str | Path,
        document_type: DocumentType,
    ) -> tuple[str, list[dict], float]:
        """Claude Vision으로 OCR 수행"""
        if not self._anthropic_client:
            raise RuntimeError("Anthropic client not initialized")

        image_data, mime_type = self._image_to_base64(image_path)

        # 문서 유형에 따른 프롬프트 조정
        if document_type == DocumentType.HANDWRITTEN:
            prompt = """이 이미지에서 손글씨 텍스트를 추출해주세요.
            - 모든 텍스트를 정확히 읽어주세요
            - 줄바꿈과 단락을 유지해주세요
            - 읽기 어려운 부분은 [불명확: 추정값]으로 표시해주세요
            - 텍스트만 반환해주세요"""
        elif document_type == DocumentType.DRAWING:
            prompt = """이 도면/기술 문서에서 텍스트를 추출해주세요.
            - 치수, 라벨, 주석 모두 포함
            - 기술 용어와 숫자를 정확히
            - 레이아웃 구조를 유지해주세요
            - 텍스트만 반환해주세요"""
        else:
            prompt = """이 이미지에서 모든 텍스트를 추출해주세요.
            - 줄바꿈과 단락을 유지
            - 표가 있으면 구조를 유지
            - 텍스트만 반환해주세요"""

        try:
            response = self._anthropic_client.messages.create(
                model=self.CLAUDE_MODEL,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            extracted_text = response.content[0].text if response.content else ""

            # Claude는 bbox 정보 없음
            return extracted_text, [], 0.9  # 높은 신뢰도 가정

        except Exception as e:
            logger.error(f"Claude Vision OCR failed: {e}")
            raise

    def process_image(
        self,
        image_path: str | Path,
        engine: OCREngine = OCREngine.AUTO,
        document_type: Optional[DocumentType] = None,
    ) -> OCRResult:
        """
        이미지 OCR 처리

        Args:
            image_path: 이미지 파일 경로
            engine: OCR 엔진 선택
            document_type: 문서 유형 (None이면 자동 감지)

        Returns:
            OCR 결과
        """
        start_time = datetime.now(UTC)

        # 문서 유형 감지
        if document_type is None:
            document_type = self._detect_document_type(image_path)

        # 엔진 선택
        selected_engine = self._select_engine(document_type, engine)

        # OCR 실행
        try:
            if selected_engine == OCREngine.EASYOCR:
                text, bboxes, confidence = self._ocr_with_easyocr(image_path)
            else:
                text, bboxes, confidence = self._ocr_with_claude(image_path, document_type)

            processing_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

            return OCRResult(
                text=text,
                confidence=confidence,
                engine_used=selected_engine,
                document_type=document_type,
                bounding_boxes=bboxes,
                processing_time_ms=processing_time,
                metadata={
                    "image_path": str(image_path),
                    "processed_at": datetime.now(UTC).isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise

    def process_image_bytes(
        self,
        image_data: bytes,
        filename: str = "image.jpg",
        engine: OCREngine = OCREngine.AUTO,
        document_type: Optional[DocumentType] = None,
    ) -> OCRResult:
        """
        바이트 데이터로 OCR 처리

        Args:
            image_data: 이미지 바이트 데이터
            filename: 파일 이름 (확장자로 타입 판별)
            engine: OCR 엔진
            document_type: 문서 유형

        Returns:
            OCR 결과
        """
        # 임시 파일로 저장
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_path = temp_dir / f"ocr_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{filename}"

        try:
            with open(temp_path, 'wb') as f:
                f.write(image_data)

            result = self.process_image(temp_path, engine, document_type)
            return result

        finally:
            # 임시 파일 삭제
            if temp_path.exists():
                temp_path.unlink()

    def process_handwritten_feedback(
        self,
        image_path: str | Path,
    ) -> dict:
        """
        손글씨 피드백 처리 (대표님 메모용)

        Args:
            image_path: 손글씨 이미지 경로

        Returns:
            구조화된 피드백 데이터
        """
        result = self.process_image(
            image_path,
            engine=OCREngine.CLAUDE_VISION,  # 손글씨는 Claude 권장
            document_type=DocumentType.HANDWRITTEN,
        )

        return {
            "raw_text": result.text,
            "confidence": result.confidence,
            "engine": result.engine_used.value,
            "processed_at": result.metadata.get("processed_at"),
            "processing_time_ms": result.processing_time_ms,
        }

    def get_available_engines(self) -> list[str]:
        """사용 가능한 OCR 엔진 목록"""
        engines = []
        if self._easyocr_reader:
            engines.append(OCREngine.EASYOCR.value)
        if self._anthropic_client:
            engines.append(OCREngine.CLAUDE_VISION.value)
        return engines

    def get_status(self) -> dict:
        """OCR 서비스 상태"""
        return {
            "easyocr_available": self._easyocr_reader is not None,
            "claude_vision_available": self._anthropic_client is not None,
            "supported_languages": ["ko", "en"],
            "gpu_enabled": EASYOCR_AVAILABLE and self._easyocr_reader is not None,
        }


# 싱글톤 인스턴스 접근
_service: Optional[OCRService] = None


def get_ocr_service() -> OCRService:
    """OCRService 싱글톤"""
    global _service
    if _service is None:
        _service = OCRService()
    return _service
