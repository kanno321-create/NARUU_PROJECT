"""
Vision AI 분석 서비스 (Phase XIV)

도면/사진을 분석하여 전기 패널 구성요소를 자동 추출하고
견적을 생성하는 서비스입니다.

Zero-Mock 원칙: 실제 Claude Vision API를 사용합니다.
Evidence-Gated: 모든 분석 결과는 해시와 함께 저장됩니다.
"""

import base64
import hashlib
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

ImageType = Literal["DRAWING", "PANEL_PHOTO", "SPEC_SHEET", "HANDWRITTEN", "OTHER"]
ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW", "MANUAL"]


@dataclass
class ExtractedComponent:
    """추출된 컴포넌트 기본 클래스"""
    confidence: ConfidenceLevel = "MEDIUM"
    source_image_id: str = ""
    bounding_box: Optional[dict] = None


@dataclass
class ExtractedBreaker(ExtractedComponent):
    """추출된 차단기"""
    breaker_type: str = "MCCB"  # MCCB or ELB
    brand: Optional[str] = None
    pole: str = "4P"
    frame: str = "100AF"
    ampere: int = 100
    quantity: int = 1
    is_main: bool = False


@dataclass
class ExtractedEnclosure(ExtractedComponent):
    """추출된 외함"""
    enclosure_type: str = "옥내노출"
    material: str = "STEEL"
    thickness: str = "1.6T"
    width: Optional[int] = None
    height: Optional[int] = None
    depth: Optional[int] = None


@dataclass
class ExtractedPanel:
    """추출된 분전반"""
    panel_name: str
    enclosure: Optional[ExtractedEnclosure] = None
    main_breaker: Optional[ExtractedBreaker] = None
    branch_breakers: list[ExtractedBreaker] = field(default_factory=list)
    accessories: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    confidence: ConfidenceLevel = "MEDIUM"


@dataclass
class AnalysisResult:
    """분석 결과"""
    analysis_id: str
    image_id: str
    image_type: ImageType
    panels: list[ExtractedPanel]
    customer_name: Optional[str] = None
    project_name: Optional[str] = None
    raw_text: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    processing_time_ms: int = 0
    evidence_hash: str = ""
    analyzed_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Vision Analysis Service
# ============================================================================

class VisionAnalysisService:
    """
    Vision AI 분석 서비스

    Features:
    - Claude Vision API를 사용한 도면/사진 분석
    - 차단기, 외함, 부속자재 자동 추출
    - 신뢰도 점수 산출
    - 분석 결과 캐싱 및 이력 관리
    """

    # 차단기 패턴 정규표현식
    BREAKER_PATTERNS = {
        "sangdo": r"(S[BE][ES])-(\d)(\d)",  # SBE-104, SBS-54 등
        "ls": r"([AE]B[NS])-(\d)(\d)",       # ABN-54, EBS-203 등
        "generic": r"(MCCB|ELB)\s*(\d+)P\s*(\d+)(?:AF|A)",
        "ampere": r"(\d+)\s*(?:A|AT|AMP)",
        "pole": r"([234])\s*P(?:OLE)?",
        "frame": r"(\d+)\s*AF",
    }

    # 외함 패턴
    ENCLOSURE_PATTERNS = {
        "type": r"(옥내노출|옥외노출|옥내자립|옥외자립|매입함|전주부착|FRP함|하이박스)",
        "material": r"(STEEL|SUS201|SUS304|스틸|스텐)",
        "thickness": r"(\d+\.?\d*)\s*[Tt]",
        "dimension": r"(\d+)\s*[×xX*]\s*(\d+)\s*[×xX*]\s*(\d+)",
    }

    # Claude Vision 분석 프롬프트
    # ╔══════════════════════════════════════════════════════════════════╗
    # ║  ⚠️ 최우선 규칙: 차단기 전수검사 (BREAKER FULL INSPECTION)      ║
    # ║  도면 내 모든 차단기를 하나하나 개별 확인해야 한다.              ║
    # ║  절대로 "같은 모델이니까 암페어도 같겠지" 추측 금지!            ║
    # ║  MCCB/ELB 구분, 극수, 프레임, 암페어를 각각 정확히 읽어야 함   ║
    # ║  예시: 같은 2P라도 20A 10개 + 30A 8개일 수 있음                ║
    # ║  예시: 4P도 MCCB 100A 1개 + ELB 30A 1개일 수 있음             ║
    # ║  이것을 틀리면 견적 대형사고 발생 → 반드시 전수검사!           ║
    # ╚══════════════════════════════════════════════════════════════════╝
    ANALYSIS_PROMPT = """당신은 전기 분전반 도면/사진 분석 전문가입니다.
이미지를 분석하여 다음 정보를 JSON 형식으로 추출하세요:

━━━ ⚠️ 최우선 규칙: 차단기 전수검사 (CRITICAL) ━━━
도면 안의 모든 차단기를 반드시 하나하나 개별적으로 확인하세요.
- 메인 차단기와 모든 분기 차단기를 빠짐없이 전수조사
- 각 차단기마다 반드시 확인할 항목: MCCB인지 ELB(CBR)인지, 극수(2P/3P/4P), 프레임(AF), 정격전류(A)
- 절대로 "같은 모델이니 암페어도 동일하겠지"라고 추측하지 마세요
- 같은 2P ELB라도 20A가 10개, 30A가 8개일 수 있습니다
- 같은 4P라도 MCCB 4P 100A 1개, ELB 4P 30A 1개일 수 있습니다
- ⚠️ 80A는 존재하지 않음! 80A로 읽히면 반드시 75A로 변환 (업계 표준: 80A → 75A)
- ⚠️ CBR = ELB = ELCB — 모두 동일한 누전차단기. 도면에 CBR/ELCB로 표기되어도 ELB로 통일
- ⚠️ 1분전반 1브랜드 원칙: 하나의 분전반에 2개 이상의 차단기 브랜드를 혼용하지 않음 (상도면 상도만, LS면 LS만)
- ⚠️ SP(예비)도 반드시 차단기 수량에 포함! 예비도 실물 차단기임
- 취소된 항목(WHM 취소, SPD 취소 등)은 해당 차단기도 함께 제외
- 차단기 스펙이 조금이라도 불확실하면 warnings에 반드시 기재하세요

━━━ 도면 차단기 스펙 읽는 법 ━━━
도면 표기 예: "CBR 2P 30/20AT 2.5KA"
  → CBR = ELB(누전차단기), 2P = 2극, 30 = 프레임(30AF), 20 = 정격전류(20A), 2.5KA = 차단용량
도면 표기 예: "MCCB 4P 225/200AT 25KA"
  → MCCB = 배선용차단기, 4P = 4극, 225 = 프레임(225AF), 200 = 정격전류(200A), 25KA = 차단용량
도면 표기 예: "MCCB 4P 100/80AT 25KA"
  → 80A는 없으므로 75A로 변환! → MCCB 4P 100AF 75A

읽는 순서: MAIN 먼저 → 좌측 열 위→아래 → 우측 열 위→아래 → 각 행이 차단기 1개

━━━ 자립형 외함 규칙 ━━━
- 자립형(옥내자립/옥외자립)은 베이스 높이(기본 200mm)를 외함 H에 더한 총 높이로 평수 계산
- 예: 외함 600×700×150 + 베이스 200 → 평수계산은 600×900×150으로 적용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 이미지 유형 (image_type): DRAWING, PANEL_PHOTO, SPEC_SHEET, HANDWRITTEN, OTHER
2. 분전반 목록 (panels): 각 분전반에 대해
   - panel_name: 분전반명
   - enclosure: 외함 정보 (type, material, thickness, width, height, depth)
   - main_breaker: 메인 차단기 (type, brand, pole, frame, ampere) — 반드시 정확한 스펙 확인
   - branch_breakers: 분기 차단기 목록 [{type, brand, pole, frame, ampere, quantity}]
     ※ 같은 모델이라도 암페어가 다르면 반드시 별도 항목으로 분리!
     ※ MCCB와 ELB(CBR)을 절대로 혼동하지 말 것!
   - accessories: 부속자재 목록 (마그네트, 타이머, SPD 등)
3. 고객 정보 (customer): name, project_name
4. 추출된 텍스트 (raw_text): 이미지에서 읽은 주요 텍스트들
5. 경고사항 (warnings): 불확실하거나 확인이 필요한 사항 (차단기 스펙 불명확 시 반드시 기재)

차단기 브랜드:
- 상도: SBE, SBS, SIE, SIB 시리즈
- LS: ABN, ABS, EBN, EBS 시리즈

JSON 형식으로만 응답하세요. 설명 없이 JSON만 출력합니다."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 분석 결과 저장 경로
        """
        if storage_path is None:
            self.storage_path = Path(__file__).parent.parent.parent.parent / "data" / "ai_memory" / "vision"
        else:
            self.storage_path = storage_path

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._results_cache: dict[str, AnalysisResult] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        """기존 분석 결과 로드"""
        try:
            index_file = self.storage_path / "vision_index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"로드된 Vision 분석 결과: {data.get('total', 0)}개")
        except Exception as e:
            logger.warning(f"Vision 분석 결과 로드 실패: {e}")

    def _save_result(self, result: AnalysisResult) -> None:
        """분석 결과 저장"""
        # 개별 결과 저장
        result_file = self.storage_path / f"{result.analysis_id}.json"
        result_data = {
            "analysis_id": result.analysis_id,
            "image_id": result.image_id,
            "image_type": result.image_type,
            "panels": self._serialize_panels(result.panels),
            "customer_name": result.customer_name,
            "project_name": result.project_name,
            "raw_text": result.raw_text,
            "warnings": result.warnings,
            "processing_time_ms": result.processing_time_ms,
            "evidence_hash": result.evidence_hash,
            "analyzed_at": result.analyzed_at.isoformat()
        }

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        # 인덱스 업데이트
        self._update_index(result)

    def _serialize_panels(self, panels: list[ExtractedPanel]) -> list[dict]:
        """분전반 목록 직렬화"""
        serialized = []
        for panel in panels:
            panel_dict = {
                "panel_name": panel.panel_name,
                "confidence": panel.confidence,
                "notes": panel.notes,
                "accessories": panel.accessories
            }

            if panel.enclosure:
                panel_dict["enclosure"] = {
                    "type": panel.enclosure.enclosure_type,
                    "material": panel.enclosure.material,
                    "thickness": panel.enclosure.thickness,
                    "width": panel.enclosure.width,
                    "height": panel.enclosure.height,
                    "depth": panel.enclosure.depth,
                    "confidence": panel.enclosure.confidence
                }

            if panel.main_breaker:
                panel_dict["main_breaker"] = {
                    "type": panel.main_breaker.breaker_type,
                    "brand": panel.main_breaker.brand,
                    "pole": panel.main_breaker.pole,
                    "frame": panel.main_breaker.frame,
                    "ampere": panel.main_breaker.ampere,
                    "is_main": True,
                    "confidence": panel.main_breaker.confidence
                }

            panel_dict["branch_breakers"] = [
                {
                    "type": b.breaker_type,
                    "brand": b.brand,
                    "pole": b.pole,
                    "frame": b.frame,
                    "ampere": b.ampere,
                    "quantity": b.quantity,
                    "confidence": b.confidence
                }
                for b in panel.branch_breakers
            ]

            serialized.append(panel_dict)

        return serialized

    def _update_index(self, result: AnalysisResult) -> None:
        """인덱스 파일 업데이트"""
        index_file = self.storage_path / "vision_index.json"

        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
        else:
            index = {"analyses": [], "total": 0}

        # 새 항목 추가
        index["analyses"].append({
            "analysis_id": result.analysis_id,
            "image_type": result.image_type,
            "panel_count": len(result.panels),
            "analyzed_at": result.analyzed_at.isoformat()
        })
        index["total"] = len(index["analyses"])
        index["updated_at"] = datetime.utcnow().isoformat()

        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _compute_evidence_hash(self, data: dict) -> str:
        """Evidence 해시 계산"""
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    async def analyze_image(
        self,
        image_data: str,
        image_id: str,
        image_name: str,
        mime_type: str = "image/png",
        user_hint: Optional[str] = None
    ) -> AnalysisResult:
        """
        단일 이미지 분석

        Args:
            image_data: base64 인코딩된 이미지 데이터 또는 URL
            image_id: 이미지 ID
            image_name: 이미지 파일명
            mime_type: MIME 타입
            user_hint: 사용자 힌트

        Returns:
            분석 결과
        """
        import time
        start_time = time.time()

        analysis_id = str(uuid.uuid4())
        logger.info(f"Vision 분석 시작: {analysis_id}, 이미지: {image_name}")

        try:
            # Claude Vision API 호출
            import anthropic
            client = anthropic.Anthropic()

            # 이미지 데이터 준비
            if image_data.startswith("data:"):
                # data:image/png;base64,... 형식
                parts = image_data.split(",", 1)
                if len(parts) == 2:
                    base64_data = parts[1]
                    media_type = parts[0].split(";")[0].replace("data:", "")
                else:
                    base64_data = image_data
                    media_type = mime_type
            elif image_data.startswith("http"):
                # URL에서 다운로드
                async with httpx.AsyncClient() as http_client:
                    resp = await http_client.get(image_data)
                    if resp.status_code == 200:
                        base64_data = base64.standard_b64encode(resp.content).decode("utf-8")
                        media_type = resp.headers.get("content-type", mime_type)
                    else:
                        raise ValueError(f"이미지 다운로드 실패: {resp.status_code}")
            else:
                base64_data = image_data
                media_type = mime_type

            # 프롬프트 구성
            prompt = self.ANALYSIS_PROMPT
            if user_hint:
                prompt += f"\n\n사용자 힌트: {user_hint}"

            # Vision API 호출
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            # 응답 파싱
            response_text = response.content[0].text
            extracted = self._parse_claude_response(response_text)

            # 결과 구성
            processing_time = int((time.time() - start_time) * 1000)

            panels = self._build_panels(extracted.get("panels", []))
            image_type = extracted.get("image_type", "OTHER")

            result = AnalysisResult(
                analysis_id=analysis_id,
                image_id=image_id,
                image_type=image_type,
                panels=panels,
                customer_name=extracted.get("customer", {}).get("name"),
                project_name=extracted.get("customer", {}).get("project_name"),
                raw_text=extracted.get("raw_text", []),
                warnings=extracted.get("warnings", []),
                processing_time_ms=processing_time
            )

            # Evidence 해시 생성
            result.evidence_hash = self._compute_evidence_hash({
                "analysis_id": analysis_id,
                "image_id": image_id,
                "panels": self._serialize_panels(panels),
                "analyzed_at": result.analyzed_at.isoformat()
            })

            # 캐시 및 저장
            self._results_cache[analysis_id] = result
            self._save_result(result)

            logger.info(f"Vision 분석 완료: {analysis_id}, 분전반 {len(panels)}개, {processing_time}ms")
            return result

        except Exception as e:
            logger.error(f"Vision 분석 실패: {e}")
            # 실패 시에도 기본 결과 반환
            return AnalysisResult(
                analysis_id=analysis_id,
                image_id=image_id,
                image_type="OTHER",
                panels=[],
                warnings=[f"분석 실패: {str(e)}"],
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

    def _parse_claude_response(self, response_text: str) -> dict:
        """Claude 응답 파싱"""
        try:
            # JSON 블록 추출
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패: {e}")
            # 텍스트에서 정보 추출 시도
            return self._extract_from_text(response_text)

    def _extract_from_text(self, text: str) -> dict:
        """텍스트에서 정보 추출 (폴백)"""
        result = {"panels": [], "raw_text": [text], "warnings": ["JSON 파싱 실패, 텍스트 추출 사용"]}

        # 차단기 정보 추출
        breakers = []
        for pattern_name, pattern in self.BREAKER_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if pattern_name in ["sangdo", "ls"]:
                    breakers.append({
                        "brand": "상도" if pattern_name == "sangdo" else "LS",
                        "model": match[0] if isinstance(match, tuple) else match
                    })

        if breakers:
            result["panels"].append({
                "panel_name": "분전반1",
                "branch_breakers": breakers
            })

        return result

    def _build_panels(self, panels_data: list[dict]) -> list[ExtractedPanel]:
        """분전반 객체 목록 생성"""
        panels = []

        for idx, panel_data in enumerate(panels_data):
            panel_name = panel_data.get("panel_name", f"분전반{idx + 1}")

            # 외함 정보
            enclosure = None
            if panel_data.get("enclosure"):
                enc_data = panel_data["enclosure"]
                enclosure = ExtractedEnclosure(
                    enclosure_type=enc_data.get("type", "옥내노출"),
                    material=enc_data.get("material", "STEEL"),
                    thickness=enc_data.get("thickness", "1.6T"),
                    width=enc_data.get("width"),
                    height=enc_data.get("height"),
                    depth=enc_data.get("depth"),
                    confidence=self._determine_confidence(enc_data)
                )

            # 메인 차단기
            main_breaker = None
            if panel_data.get("main_breaker"):
                mb_data = panel_data["main_breaker"]
                main_breaker = ExtractedBreaker(
                    breaker_type=mb_data.get("type", "MCCB"),
                    brand=mb_data.get("brand"),
                    pole=mb_data.get("pole", "4P"),
                    frame=mb_data.get("frame", "100AF"),
                    ampere=mb_data.get("ampere", 100),
                    is_main=True,
                    confidence=self._determine_confidence(mb_data)
                )

            # 분기 차단기
            branch_breakers = []
            for br_data in panel_data.get("branch_breakers", []):
                breaker = ExtractedBreaker(
                    breaker_type=br_data.get("type", "ELB"),
                    brand=br_data.get("brand"),
                    pole=br_data.get("pole", "2P"),
                    frame=br_data.get("frame", "30AF"),
                    ampere=br_data.get("ampere", 20),
                    quantity=br_data.get("quantity", 1),
                    is_main=False,
                    confidence=self._determine_confidence(br_data)
                )
                branch_breakers.append(breaker)

            panel = ExtractedPanel(
                panel_name=panel_name,
                enclosure=enclosure,
                main_breaker=main_breaker,
                branch_breakers=branch_breakers,
                accessories=panel_data.get("accessories", []),
                notes=panel_data.get("notes", []),
                confidence=self._determine_panel_confidence(enclosure, main_breaker, branch_breakers)
            )
            panels.append(panel)

        return panels

    def _determine_confidence(self, data: dict) -> ConfidenceLevel:
        """개별 데이터의 신뢰도 결정"""
        # 필수 필드가 모두 있으면 HIGH
        required_fields = {"type", "pole", "frame", "ampere"} if "type" in data else {"type", "material"}
        present_fields = set(k for k, v in data.items() if v is not None)

        if required_fields.issubset(present_fields):
            return "HIGH"
        elif len(present_fields) >= len(required_fields) * 0.7:
            return "MEDIUM"
        else:
            return "LOW"

    def _determine_panel_confidence(
        self,
        enclosure: Optional[ExtractedEnclosure],
        main_breaker: Optional[ExtractedBreaker],
        branch_breakers: list[ExtractedBreaker]
    ) -> ConfidenceLevel:
        """분전반 전체 신뢰도 결정"""
        confidences = []

        if enclosure:
            confidences.append(enclosure.confidence)
        if main_breaker:
            confidences.append(main_breaker.confidence)
        for b in branch_breakers:
            confidences.append(b.confidence)

        if not confidences:
            return "MANUAL"

        # 신뢰도 점수 계산
        score_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "MANUAL": 0}
        avg_score = sum(score_map.get(c, 0) for c in confidences) / len(confidences)

        if avg_score >= 2.5:
            return "HIGH"
        elif avg_score >= 1.5:
            return "MEDIUM"
        elif avg_score >= 0.5:
            return "LOW"
        else:
            return "MANUAL"

    async def analyze_multiple_images(
        self,
        images: list[dict],
        user_hint: Optional[str] = None
    ) -> dict:
        """
        여러 이미지 분석 및 병합

        Args:
            images: 이미지 목록 [{id, name, type, url}, ...]
            user_hint: 사용자 힌트

        Returns:
            병합된 분석 결과
        """
        request_id = str(uuid.uuid4())
        results = []
        all_panels = []

        for img in images:
            result = await self.analyze_image(
                image_data=img.get("url", ""),
                image_id=img.get("id", str(uuid.uuid4())),
                image_name=img.get("name", "unknown"),
                mime_type=img.get("type", "image/png"),
                user_hint=user_hint
            )
            results.append(result)
            all_panels.extend(result.panels)

        # 분전반 병합 (중복 제거)
        merged_panels = self._merge_panels(all_panels)

        # 전체 신뢰도 계산
        if merged_panels:
            confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "MANUAL": 0}
            for panel in merged_panels:
                confidence_counts[panel.confidence] += 1

            if confidence_counts["HIGH"] >= len(merged_panels) * 0.7:
                overall_confidence = "HIGH"
            elif confidence_counts["HIGH"] + confidence_counts["MEDIUM"] >= len(merged_panels) * 0.5:
                overall_confidence = "MEDIUM"
            else:
                overall_confidence = "LOW"
        else:
            overall_confidence = "MANUAL"

        # 총 차단기 수 계산
        total_breakers = sum(
            (1 if p.main_breaker else 0) + sum(b.quantity for b in p.branch_breakers)
            for p in merged_panels
        )

        return {
            "request_id": request_id,
            "status": "SUCCESS" if merged_panels else "FAILED",
            "results": results,
            "merged_panels": merged_panels,
            "total_breakers": total_breakers,
            "total_panels": len(merged_panels),
            "overall_confidence": overall_confidence,
            "message": f"분석 완료: {len(merged_panels)}개 분전반, {total_breakers}개 차단기 추출"
        }

    def _merge_panels(self, panels: list[ExtractedPanel]) -> list[ExtractedPanel]:
        """분전반 목록 병합 (중복 제거)"""
        merged: dict[str, ExtractedPanel] = {}

        for panel in panels:
            name = panel.panel_name

            if name in merged:
                # 기존 패널과 병합
                existing = merged[name]

                # 더 높은 신뢰도의 정보 사용
                if not existing.enclosure or (panel.enclosure and
                    self._confidence_score(panel.enclosure.confidence) > self._confidence_score(existing.enclosure.confidence)):
                    existing.enclosure = panel.enclosure

                if not existing.main_breaker or (panel.main_breaker and
                    self._confidence_score(panel.main_breaker.confidence) > self._confidence_score(existing.main_breaker.confidence)):
                    existing.main_breaker = panel.main_breaker

                # 분기 차단기 병합
                existing.branch_breakers.extend(panel.branch_breakers)
                existing.accessories.extend(panel.accessories)
                existing.notes.extend(panel.notes)
            else:
                merged[name] = panel

        return list(merged.values())

    def _confidence_score(self, confidence: ConfidenceLevel) -> int:
        """신뢰도를 숫자로 변환"""
        return {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "MANUAL": 0}.get(confidence, 0)

    async def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """분석 결과 조회"""
        if analysis_id in self._results_cache:
            return self._results_cache[analysis_id]

        # 파일에서 로드
        result_file = self.storage_path / f"{analysis_id}.json"
        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # AnalysisResult 재구성
                # (간단화를 위해 캐시에서 반환)
                return None

        return None

    def get_stats(self) -> dict:
        """Vision 분석 통계"""
        index_file = self.storage_path / "vision_index.json"

        if index_file.exists():
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)
                return {
                    "total_analyses": index.get("total", 0),
                    "updated_at": index.get("updated_at")
                }

        return {"total_analyses": 0, "updated_at": None}


# ============================================================================
# Singleton Instance
# ============================================================================

_vision_service: Optional[VisionAnalysisService] = None


def get_vision_service() -> VisionAnalysisService:
    """Vision 분석 서비스 싱글톤 인스턴스 반환"""
    global _vision_service
    if _vision_service is None:
        _vision_service = VisionAnalysisService()
    return _vision_service
