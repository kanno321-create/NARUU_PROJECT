"""
Estimate Parser Service - 자연어 견적 요청 파싱

AI 매니저 탭에서 자연어로 견적 요청을 받아 자동으로 파싱:
- 고객명 추출 → ERP 검색
- 외함 정보 추출 (종류, 재질)
- 메인 차단기 추출 (브랜드, 등급, 극수, 용량)
- 분기 차단기 추출 (종류, 극수, 용량, 수량)
- 외함 사이즈 자동 계산
- 카탈로그 매칭하여 모델명/단가 반환

예시 입력:
"중앙전기, 옥내노출 스틸1.6T, 상도 경제형 메인4P 50A, 분기 ELB 4P30A 2개, ELB 2P 20A 8개 견적줘"

╔══════════════════════════════════════════════════════════════════╗
║  ⚠️ 최우선 규칙: 차단기 전수검사 (BREAKER FULL INSPECTION)      ║
║                                                                  ║
║  도면에서 차단기를 추출할 때 모든 차단기를 하나하나 확인해야 함  ║
║  - 같은 모델이라도 암페어가 다르면 반드시 별도 항목으로 분리     ║
║  - MCCB/ELB(CBR) 혼동 절대 금지                                 ║
║  - 예: 2P 20A 10개 + 2P 30A 8개 → 별도 2개 항목                ║
║  - 예: 4P MCCB 100A 1개 + 4P ELB 30A 1개 → 별도 2개 항목       ║
║  ⚠️ 80A는 존재하지 않음 → 반드시 75A로 변환!                      ║
║  ⚠️ CBR = ELB = ELCB → 모두 누전차단기, ELB로 통일!              ║
║  ⚠️ 자립형: 총높이 = 외함H + 베이스H(기본200) → 평수계산 적용   ║
║  ⚠️ 1분전반 1브랜드: 상도면 상도만, LS면 LS만 사용!             ║
║  이것을 틀리면 견적 대형사고 발생!                               ║
╚══════════════════════════════════════════════════════════════════╝
"""

import logging
import re
from dataclasses import dataclass, field

from kis_estimator_core.services.ai_catalog_service import AICatalogService
from kis_estimator_core.services.erp_service import get_erp_service

logger = logging.getLogger(__name__)


@dataclass
class ParsedBreaker:
    """파싱된 차단기 정보"""
    category: str  # MCCB or ELB
    brand: str  # 상도, LS 등
    series: str  # 경제형, 표준형
    poles: int  # 2, 3, 4
    current_a: int  # 정격전류
    quantity: int = 1  # 수량
    is_main: bool = False  # 메인 차단기 여부


@dataclass
class ParsedEnclosure:
    """파싱된 외함 정보"""
    enclosure_type: str  # 옥내노출, 옥외노출 등
    material: str  # STEEL 1.6T, SUS201 등
    remarks: str | None = None  # 양문형 등 특이사항


@dataclass
class ParsedEstimateRequest:
    """파싱된 견적 요청"""
    customer_name: str | None = None
    customer_data: dict | None = None  # ERP에서 찾은 고객 정보
    enclosure: ParsedEnclosure | None = None
    main_breaker: ParsedBreaker | None = None
    branch_breakers: list[ParsedBreaker] = field(default_factory=list)
    calculated_enclosure_size: dict | None = None  # {width, height, depth}
    enclosure_classification: str | None = None  # 기성함/주문제작함
    parse_success: bool = False
    parse_messages: list[str] = field(default_factory=list)


class EstimateParserService:
    """자연어 견적 요청 파싱 서비스"""

    def __init__(self):
        self.erp_service = get_erp_service()
        self.catalog_service = AICatalogService()

    async def parse_estimate_request(self, text: str) -> ParsedEstimateRequest:
        """
        자연어 견적 요청 파싱

        Args:
            text: 자연어 견적 요청
                예: "중앙전기, 옥내노출 스틸1.6T, 상도 경제형 메인4P 50A,
                    분기 ELB 4P30A 2개, ELB 2P 20A 8개 견적줘"

        Returns:
            ParsedEstimateRequest: 파싱된 견적 요청 데이터
        """
        result = ParsedEstimateRequest()
        text = text.strip()

        # 1. 고객명 추출 및 ERP 검색
        customer_name = self._extract_customer_name(text)
        if customer_name:
            result.customer_name = customer_name
            customer_result = await self.erp_service.search_customers(customer_name, limit=1)
            if customer_result["success"] and customer_result["data"]["customers"]:
                result.customer_data = customer_result["data"]["customers"][0]
                result.parse_messages.append(f"고객 '{customer_name}' 검색 완료")
            else:
                result.parse_messages.append(f"고객 '{customer_name}' ERP에서 찾지 못함")

        # 2. 외함 정보 추출
        enclosure = self._extract_enclosure(text)
        if enclosure:
            result.enclosure = enclosure
            result.parse_messages.append(f"외함: {enclosure.enclosure_type} {enclosure.material}")

        # 3. 메인 차단기 추출
        main_breaker = self._extract_main_breaker(text)
        if main_breaker:
            result.main_breaker = main_breaker
            result.parse_messages.append(
                f"메인: {main_breaker.brand} {main_breaker.series} "
                f"{main_breaker.category} {main_breaker.poles}P {main_breaker.current_a}A"
            )

        # 4. 분기 차단기 추출
        branch_breakers = self._extract_branch_breakers(text)
        if branch_breakers:
            result.branch_breakers = branch_breakers
            for br in branch_breakers:
                result.parse_messages.append(
                    f"분기: {br.category} {br.poles}P {br.current_a}A x{br.quantity}"
                )

        # 5. 외함 사이즈 자동 계산
        if main_breaker or branch_breakers:
            enclosure_size = self._calculate_enclosure_size(main_breaker, branch_breakers)
            result.calculated_enclosure_size = enclosure_size
            result.parse_messages.append(
                f"외함 계산 크기: {enclosure_size['width']}x{enclosure_size['height']}x{enclosure_size['depth']}mm"
            )

            # 6. 기성함/주문제작함 분류
            if enclosure:
                enc_result = self.catalog_service.get_enclosure_with_classification(
                    enclosure_type=enclosure.enclosure_type,
                    material=enclosure.material,
                    width_mm=enclosure_size["width"],
                    height_mm=enclosure_size["height"],
                    depth_mm=enclosure_size["depth"],
                    remarks=enclosure.remarks
                )
                result.enclosure_classification = enc_result.get("classification", "주문제작함")
                result.parse_messages.append(f"외함 분류: {result.enclosure_classification}")

        result.parse_success = bool(main_breaker or branch_breakers)
        return result

    def _extract_customer_name(self, text: str) -> str | None:
        """고객명 추출 (첫 번째 쉼표 앞 또는 특정 패턴)"""
        # 패턴 1: "OOO, " 형태 (첫 번째 쉼표 앞)
        if "," in text:
            first_part = text.split(",")[0].strip()
            # 외함/차단기 키워드가 아니면 고객명으로 간주
            if not any(kw in first_part for kw in ["옥내", "옥외", "상도", "LS", "메인", "분기", "MCCB", "ELB"]):
                return first_part

        # 패턴 2: "OOO 견적" 형태
        match = re.search(r"^([가-힣a-zA-Z0-9\(\)]+)\s+견적", text)
        if match:
            return match.group(1)

        return None

    def _extract_enclosure(self, text: str) -> ParsedEnclosure | None:
        """외함 정보 추출"""
        enclosure_type = None
        material = None
        remarks = None

        # 외함 종류 추출 (모든 타입 지원)
        type_patterns = [
            (r"옥내노출", "옥내노출"),
            (r"옥외노출", "옥외노출"),
            (r"옥내자립", "옥내자립"),
            (r"옥외자립", "옥외자립"),
            (r"전주부착형?", "전주부착"),
            (r"매입함?", "매입함"),
            (r"FRP함?|FRP", "FRP함"),
            (r"하이박스", "하이박스"),
            (r"속판제작|속판", "속판제작"),
        ]
        for pattern, type_name in type_patterns:
            if re.search(pattern, text):
                enclosure_type = type_name
                break

        # 재질 추출 - 순서 중요! 구체적인 패턴을 먼저 검사
        material_patterns = [
            # 1. 구체적 두께 지정 (1.0T 먼저 - 1.6T보다 앞에 와야 함)
            (r"스틸\s*1\.?0T|STEEL\s*1\.?0T", "STEEL 1.0T"),
            # 2. 1.6T 명시적 지정
            (r"스틸\s*1\.?6T|STEEL\s*1\.?6T", "STEEL 1.6T"),
            # 3. SUS 계열
            (r"SUS\s*304|스테인레스\s*304", "SUS304 1.5T"),
            (r"SUS\s*201|스테인레스|SUS201", "SUS201 1.2T"),
            # 4. STEEL/스틸 단독 입력 → 기본 1.6T (마지막에 검사)
            (r"\bSTEEL\b|\b스틸\b", "STEEL 1.6T"),
        ]
        for pattern, mat_name in material_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                material = mat_name
                break

        # 특이사항 추출
        if "양문" in text:
            remarks = "양문형"
        elif "도어없음" in text or "노도어" in text:
            remarks = "도어없음"

        # 외함 종류와 재질이 모두 있어야 정확한 매칭 가능
        if enclosure_type and material:
            return ParsedEnclosure(
                enclosure_type=enclosure_type,
                material=material,
                remarks=remarks
            )
        elif enclosure_type:
            # 재질만 누락 - 경고 로그 후 기본값 사용
            logger.warning(f"[PARSE] 외함 재질 누락, 기본값 'STEEL 1.6T' 사용 (입력: {text[:50]}...)")
            return ParsedEnclosure(
                enclosure_type=enclosure_type,
                material="STEEL 1.6T",
                remarks=f"{remarks or ''} [재질 자동설정]".strip()
            )
        elif material:
            # 외함 종류만 누락 - 경고 로그 후 기본값 사용
            logger.warning(f"[PARSE] 외함 종류 누락, 기본값 '옥내노출' 사용 (입력: {text[:50]}...)")
            return ParsedEnclosure(
                enclosure_type="옥내노출",
                material=material,
                remarks=f"{remarks or ''} [종류 자동설정]".strip()
            )
        return None

    def _extract_main_breaker(self, text: str) -> ParsedBreaker | None:
        """메인 차단기 추출"""
        # 패턴: "상도 경제형 메인4P 50A" 또는 "메인 4P 50A 상도 경제형" 또는 "상도 4P 100A 메인"
        # "메인차단기"도 "메인"으로 인식
        main_patterns = [
            # 패턴 1: 브랜드 등급 메인(차단기) 극수 용량
            (r"(상도|LS|ls)\s*(경제형|표준형)?\s*메인(?:차단기)?\s*(\d)P\s*(\d+)A?", "brand_grade_main"),
            # 패턴 2: 메인(차단기) 브랜드 등급 극수 용량
            (r"메인(?:차단기)?\s*(상도|LS|ls)?\s*(경제형|표준형)?\s*(\d)P\s*(\d+)A?", "main_brand"),
            # 패턴 3: 메인(차단기) 종류 극수 용량
            (r"메인(?:차단기)?\s*(MCCB|mccb|ELB|elb|배선용|누전)?\s*(\d)P\s*(\d+)A?", "main_type"),
            # 패턴 3-1: 메인(차단기) 극수 용량 (종류 없이)
            (r"메인(?:차단기)?\s*(\d)P\s*(\d+)A?", "main_simple"),
            # 패턴 3-2: 메인(차단기) 용량만 (극수 생략 → 기본 4P)
            (r"메인(?:차단기)?\s*(\d+)A", "main_ampere_only"),
            # 패턴 4: 브랜드 등급 극수 용량 메인(차단기) (메인이 뒤에 오는 경우)
            (r"(상도|LS|ls)\s*(경제형|표준형)?\s*(\d)P\s*(\d+)A?\s*메인(?:차단기)?", "brand_poles_main"),
            # 패턴 5: 극수 용량 메인(차단기) (간단한 형태)
            (r"(\d)P\s*(\d+)A?\s*메인(?:차단기)?", "poles_main"),
            # 패턴 6: MCCB/ELB 극수 용량 (메인 키워드 없음 — 첫 번째 차단기를 메인으로 추정)
            (r"(MCCB|mccb)\s*(\d)P\s*(\d+)A?", "type_poles_ampere"),
        ]

        for pattern, pattern_type in main_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                logger.info(f"[PARSE] 메인 차단기 매칭: 패턴={pattern_type}, 그룹={groups}")

                # 패턴 타입별 파싱
                if pattern_type == "brand_grade_main":
                    # 패턴 1: (브랜드)(등급)(극수)(용량)
                    brand = groups[0]
                    series = groups[1] or "경제형"
                    poles = int(groups[2])
                    current_a = int(groups[3])
                    category = "MCCB"

                elif pattern_type == "brand_poles_main":
                    # 패턴 4: (브랜드)(등급)(극수)(용량) - 메인이 뒤에 옴
                    brand = groups[0]
                    series = groups[1] or "경제형"
                    poles = int(groups[2])
                    current_a = int(groups[3])
                    category = "MCCB"

                elif pattern_type == "main_brand":
                    # 패턴 2: (브랜드)(등급)(극수)(용량)
                    brand = groups[0] if groups[0] else "상도"
                    series = groups[1] if groups[1] else "경제형"
                    poles = int(groups[2])
                    current_a = int(groups[3])
                    category = "MCCB"

                elif pattern_type == "main_type":
                    # 패턴 3: (종류)(극수)(용량)
                    breaker_type = groups[0].upper() if groups[0] else "MCCB"
                    if breaker_type in ["누전"]:
                        category = "ELB"
                    elif breaker_type in ["배선용"]:
                        category = "MCCB"
                    else:
                        category = breaker_type if breaker_type in ["MCCB", "ELB"] else "MCCB"
                    brand = "상도"
                    series = "경제형"
                    poles = int(groups[1])
                    current_a = int(groups[2])

                elif pattern_type == "poles_main":
                    # 패턴 5: (극수)(용량)
                    brand = "상도"
                    series = "경제형"
                    poles = int(groups[0])
                    current_a = int(groups[1])
                    category = "MCCB"

                elif pattern_type == "main_simple":
                    # 패턴 3-1: (극수)(용량) — 메인(차단기) 뒤에 바로 극수/용량
                    brand = "상도"
                    series = "경제형"
                    poles = int(groups[0])
                    current_a = int(groups[1])
                    category = "MCCB"

                elif pattern_type == "main_ampere_only":
                    # 패턴 3-2: (용량)만 — 극수 생략, 기본 4P
                    brand = "상도"
                    series = "경제형"
                    poles = 4
                    current_a = int(groups[0])
                    category = "MCCB"

                elif pattern_type == "type_poles_ampere":
                    # 패턴 6: (MCCB/ELB)(극수)(용량) — 메인 키워드 없음
                    breaker_type = groups[0].upper()
                    category = breaker_type if breaker_type in ["MCCB", "ELB"] else "MCCB"
                    brand = "상도"
                    series = "경제형"
                    poles = int(groups[1])
                    current_a = int(groups[2])

                else:
                    brand = "상도"
                    series = "경제형"
                    poles = 4
                    current_a = 50
                    category = "MCCB"

                logger.info(f"[PARSE] 메인 차단기 파싱 결과: {brand} {series} {category} {poles}P {current_a}A")

                return ParsedBreaker(
                    category=category,
                    brand=brand if brand else "상도",
                    series=series if series else "경제형",
                    poles=poles,
                    current_a=current_a,
                    quantity=1,
                    is_main=True
                )

        return None

    def _extract_branch_breakers(self, text: str) -> list[ParsedBreaker]:
        """분기 차단기 추출"""
        breakers = []

        # 패턴: "분기 ELB 4P30A 2개" 또는 "ELB 4P 30A 2개" 또는 "ELB 4P30A 2" 또는 "분기 3P 30A 10개로"
        branch_patterns = [
            # 패턴 1: 분기 종류 극수 용량 수량 (종류 생략 가능, "개로" 지원)
            r"분기\s*(MCCB|mccb|ELB|elb|배선용|누전)?\s*(\d)P\s*(\d+)A?\s*(\d+)개?(?:로)?",
            # 패턴 2: 종류 극수 용량 수량 (메인 이후)
            r"(MCCB|mccb|ELB|elb|배선용|누전)\s*(\d)P\s*(\d+)A?\s*(\d+)개?(?:로)?",
            # 패턴 3: 종류 극수용량 수량개
            r"(MCCB|mccb|ELB|elb)\s*(\d)P(\d+)A?\s*(\d+)개",
        ]

        # 메인 차단기 부분 제거하고 분기 부분만 추출
        text_lower = text.lower()
        branch_section = text
        if "분기" in text:
            branch_idx = text.find("분기")
            branch_section = text[branch_idx:]
        elif "메인" in text_lower:
            # 메인 부분 이후의 ELB/MCCB 패턴 추출
            parts = re.split(r"메인[^,]*,?\s*", text, flags=re.IGNORECASE)
            if len(parts) > 1:
                branch_section = parts[1]

        # 여러 차단기 패턴 찾기
        for pattern in branch_patterns:
            matches = re.finditer(pattern, branch_section, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                category = groups[0].upper() if groups[0] else "MCCB"
                if category in ["배선용"]:
                    category = "MCCB"
                elif category in ["누전"]:
                    category = "ELB"

                poles = int(groups[1])
                current_a = int(groups[2])
                quantity = int(groups[3]) if groups[3] else 1

                # 중복 체크
                is_duplicate = False
                for existing in breakers:
                    if (existing.category == category and
                        existing.poles == poles and
                        existing.current_a == current_a):
                        is_duplicate = True
                        break

                if not is_duplicate and not (poles == 4 and current_a == 50 and "메인" in text_lower):
                    breakers.append(ParsedBreaker(
                        category=category,
                        brand="상도",  # 분기는 기본 상도
                        series="경제형",  # 분기는 기본 경제형
                        poles=poles,
                        current_a=current_a,
                        quantity=quantity,
                        is_main=False
                    ))

        return breakers

    def _calculate_enclosure_size(
        self,
        main_breaker: ParsedBreaker | None,
        branch_breakers: list[ParsedBreaker]
    ) -> dict:
        """
        차단기 기반 외함 크기 계산

        CLAUDE.md 공식 참조:
        H = A + B + C + D + E
        A: 상단 여유 (메인 프레임별)
        B: 메인-분기 간격 30mm
        C: 분기 차단기 총 높이
        D: 하단 여유 (150~250mm)
        E: 부속자재 여유
        """
        # 기본값
        width = 600
        height = 400
        depth = 200

        # 메인 차단기 프레임 결정
        main_af = 50
        if main_breaker:
            if main_breaker.current_a <= 50:
                main_af = 50
            elif main_breaker.current_a <= 100:
                main_af = 100
            elif main_breaker.current_a <= 125:
                main_af = 125
            elif main_breaker.current_a <= 250:
                main_af = 250
            elif main_breaker.current_a <= 400:
                main_af = 400
            else:
                main_af = 600

        # 차단기 치수 (CLAUDE.md 참조)
        # 30AF (소형 SIE-32/SIB-32): W33×H70×D42mm
        breaker_heights = {
            30: 70,   # 소형 2P 15~30A (SIE-32, SIB-32)
            50: 130,
            100: 130,
            125: 155,
            200: 165,
            250: 165,
            400: 257,
            600: 280,
            800: 280,
        }

        # 소형 차단기 폭 (W) - 눕혔을 때 높이로 사용
        breaker_widths = {
            30: 33,   # 소형 2P
            50: {2: 50, 3: 75, 4: 100},
            100: {2: 50, 3: 75, 4: 100},
            125: {2: 60, 3: 90, 4: 120},
            200: {2: 70, 3: 105, 4: 140},
            250: {2: 70, 3: 105, 4: 140},
            400: {3: 140, 4: 187},
            600: {3: 210, 4: 280},
            800: {3: 210, 4: 280},
        }

        # A: 상단 여유
        if main_af <= 100:
            top_margin = 130
        elif main_af <= 250:
            top_margin = 170
        else:
            top_margin = 200

        # B: 메인-분기 간격
        main_branch_gap = 30

        # C: 분기 차단기 총 높이 계산
        total_branch_height = 0
        total_branch_width = 0
        for br in branch_breakers:
            # 분기 프레임 결정 (2P 15~30A는 소형 30AF)
            if br.poles == 2 and br.current_a <= 30:
                br_af = 30  # 소형 SIE-32/SIB-32
            elif br.current_a <= 50:
                br_af = 50
            elif br.current_a <= 100:
                br_af = 100
            elif br.current_a <= 125:
                br_af = 125
            elif br.current_a <= 250:
                br_af = 250
            else:
                br_af = 400

            br_height = breaker_heights.get(br_af, 130)

            # 분기 차단기는 마주보기 배치이므로 rows = ceil(count/2)
            rows = (br.quantity + 1) // 2
            # 각 행의 높이는 차단기 폭(W)값 사용 (눕혀서 배치)
            if br_af == 30:
                row_height = breaker_widths[30]  # 33mm
            else:
                width_dict = breaker_widths.get(br_af, {2: 50, 3: 75, 4: 100})
                row_height = width_dict.get(br.poles, 75) if isinstance(width_dict, dict) else 75

            total_branch_height += row_height * rows

            # 폭 계산 (극수별)
            br_width = 33 if br_af == 30 else (50 if br.poles == 2 else (75 if br.poles == 3 else 100))
            total_branch_width = max(total_branch_width, br_width * 2)  # 좌우 배치

        # D: 하단 여유
        if main_af <= 250:
            bottom_margin = 150
        elif main_af <= 400:
            bottom_margin = 200
        else:
            bottom_margin = 250

        # E: 부속자재 여유 (20%)
        accessory_margin = int(total_branch_height * 0.2)

        # 최종 높이 계산
        main_height = breaker_heights.get(main_af, 130) if main_breaker else 0
        height = top_margin + main_height + main_branch_gap + total_branch_height + bottom_margin + accessory_margin

        # 폭 결정 (CLAUDE.md width_rules 참조)
        total_breakers = sum(br.quantity for br in branch_breakers)
        if main_af <= 100:
            width = 600 if total_breakers < 28 else 700
        elif main_af <= 250:
            width = 700
        elif main_af <= 400:
            width = 800
        else:
            width = 900

        # 깊이
        depth = 200

        # 50mm 단위로 올림
        height = ((height + 49) // 50) * 50
        width = ((width + 49) // 50) * 50

        return {
            "width": width,
            "height": height,
            "depth": depth
        }

    async def generate_estimate_form_data(self, parsed: ParsedEstimateRequest) -> dict:
        """
        파싱된 데이터를 견적 폼 데이터로 변환

        Returns:
            프론트엔드 견적 폼에 바로 적용 가능한 데이터
        """
        form_data = {
            "customer": None,
            "enclosure": None,
            "main_breaker": None,
            "branch_breakers": [],
            "messages": parsed.parse_messages,
            "success": parsed.parse_success
        }

        # 고객 정보
        if parsed.customer_data:
            form_data["customer"] = {
                "customer_id": parsed.customer_data.get("customer_id"),
                "company_name": parsed.customer_data.get("company_name"),
                "contact_name": parsed.customer_data.get("contact_name"),
                "phone": parsed.customer_data.get("phone"),
                "email": parsed.customer_data.get("email"),
                "address": parsed.customer_data.get("address"),
            }

        # 외함 정보
        if parsed.enclosure and parsed.calculated_enclosure_size:
            form_data["enclosure"] = {
                "type": parsed.enclosure.enclosure_type,
                "material": parsed.enclosure.material,
                "width": parsed.calculated_enclosure_size["width"],
                "height": parsed.calculated_enclosure_size["height"],
                "depth": parsed.calculated_enclosure_size["depth"],
                "classification": parsed.enclosure_classification,
                "remarks": parsed.enclosure.remarks,
            }

        # 메인 차단기
        if parsed.main_breaker:
            br = parsed.main_breaker
            # 카탈로그에서 모델명/단가 조회
            catalog_result = self.catalog_service.get_breaker_model_and_price(
                brand=br.brand,
                series=br.series,
                category=br.category,
                poles=br.poles,
                current_a=br.current_a
            )
            form_data["main_breaker"] = {
                "brand": br.brand,
                "series": br.series,
                "category": br.category,
                "poles": br.poles,
                "current_a": br.current_a,
                "quantity": br.quantity,
                "model": catalog_result.get("model") if catalog_result else None,
                "price": catalog_result.get("price") if catalog_result else None,
                "auto_substituted": catalog_result.get("auto_substituted", False) if catalog_result else False,
            }

        # 분기 차단기
        for br in parsed.branch_breakers:
            catalog_result = self.catalog_service.get_breaker_model_and_price(
                brand=br.brand,
                series=br.series,
                category=br.category,
                poles=br.poles,
                current_a=br.current_a
            )
            form_data["branch_breakers"].append({
                "brand": br.brand,
                "series": br.series,
                "category": br.category,
                "poles": br.poles,
                "current_a": br.current_a,
                "quantity": br.quantity,
                "model": catalog_result.get("model") if catalog_result else None,
                "price": catalog_result.get("price") if catalog_result else None,
            })

        return form_data


# 싱글톤 인스턴스
_parser_service: EstimateParserService | None = None


def get_estimate_parser_service() -> EstimateParserService:
    """EstimateParserService 싱글톤"""
    global _parser_service
    if _parser_service is None:
        _parser_service = EstimateParserService()
    return _parser_service
