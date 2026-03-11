"""
Stage 3 Format - Data Models
Excel/PDF 견적서 생성용 데이터 모델

SPEC KIT 기준:
- 실물 템플릿 기반 (목업 금지)
- 수식 보존 100% (data_only=False)
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from kis_estimator_core.core.ssot.constants_format import (
    UNIT_ASSEMBLY,
    UNIT_BUSBAR,
)

# Import from SSOT (LAW-02: Single Source of Truth)


@dataclass
class LineItem:
    """
    견적서 품목 (베이스 클래스)

    Excel 매핑:
    - A: 번호 (순번)
    - B: item_name (품명)
    - C: spec (규격)
    - D: unit (단위)
    - E: quantity (수량)
    - F: unit_price (단가)
    - G: **수식** (=F*E, 절대 입력 금지)
    """

    item_name: str  # 품명 (예: "옥외자립함", "MCCB", "ELB")
    spec: str  # 규격 (예: "DEFAULT_ENCLOSURE_SIZE", "4P 300AT 35kA")
    unit: str  # 단위 (예: UNIT_ACCESSORY, UNIT_ASSEMBLY, UNIT_BUSBAR)
    quantity: float  # 수량 (예: 1, 2, 10, 15.4)
    unit_price: float  # 단가 (예: 450000, 118000)
    priority: int = 99  # 정렬 우선순위 (낮을수록 먼저)

    @property
    def amount(self) -> float:
        """금액 (수량 × 단가) - 참조용, Excel에는 수식 사용"""
        return self.quantity * self.unit_price


@dataclass
class EnclosureItem(LineItem):
    """외함 품목"""

    enclosure_type: str = ""  # "옥내노출", "옥외자립" 등
    material: str = ""  # "STEEL 1.6T", "SUS201 1.2T"
    dimensions_whd: str = ""  # "DEFAULT_ENCLOSURE_SIZE*200"

    def __post_init__(self):
        if not self.item_name:
            self.item_name = f"{self.enclosure_type} {self.material}"
        if not self.spec:
            self.spec = self.dimensions_whd
        self.priority = 1  # 외함은 가장 먼저


@dataclass
class BreakerItem(LineItem):
    """차단기 품목"""

    breaker_type: str = ""  # "MCCB", "ELB"
    model: str = ""  # "SBS-54", "SEE-104"
    is_main: bool = False  # 메인 차단기 여부
    poles: int = 0
    current_a: float = 0.0
    breaking_capacity_ka: float = 0.0
    frame_af: int = 0  # 프레임 크기 (AF)

    def __post_init__(self):
        if not self.item_name:
            self.item_name = self.breaker_type
        # spec은 이미 설정되어 있음 (예: "4P 300AT 35kA")
        if self.is_main:
            self.priority = 3  # 메인 차단기
        else:
            self.priority = 4  # 분기 차단기


@dataclass
class AccessoryItem(LineItem):
    """부속자재 품목"""

    accessory_type: str = ""  # "E.T", "N.T", "N.P", "INSULATOR" 등

    def __post_init__(self):
        # 우선순위 매핑 (실물 견적서 순서 기준)
        # 외함(1) → 메인차단기(3) → 분기차단기(4) → 부속자재(5~17) → 인건비(18)
        priority_map = {
            "SUSCOVER": 2,  # SUS 커버 (외함 직후)
            "E.T": 5,  # 접지 (Earth Terminal)
            "N.T": 6,  # 중성선 접지
            "N.P": 7,  # 명판 (Name Plate)
            "MAIN BUS-BAR": 8,  # 메인 부스바
            "BUS-BAR": 9,  # 분기 부스바
            "COATING": 10,  # 부스바 절연코팅
            "P-COVER": 11,  # 부스바 보호커버
            "ELB보호커버": 12,  # ELB 지지대 (작은 차단기용)
            "ELB지지대": 12,  # ELB 지지대 (동일)
            "INSULATOR": 13,  # 메인 부스바 하단 지지대
            "인출단자대": 14,  # 인출단자대
            "단자대": 15,  # 단자대
            "잡자재비": 16,  # 잡자재비 (제작 자재 일체)
            "ASSEMBLY CHARGE": 18,  # 인건비 (마지막)
        }
        self.priority = priority_map.get(self.accessory_type, 99)


@dataclass
class BusbarItem(LineItem):
    """부스바 품목"""

    busbar_type: str = ""  # "MAIN BUS-BAR", "BUS-BAR"
    thickness_width: str = ""  # "6T*30", "3T*15"
    weight_kg: float = 0.0

    def __post_init__(self):
        if not self.item_name:
            self.item_name = self.busbar_type
        if not self.spec:
            self.spec = self.thickness_width
        if not self.quantity:
            self.quantity = self.weight_kg
        if not self.unit:
            self.unit = UNIT_BUSBAR

        # 우선순위 (실물 견적서 순서 기준)
        if "MAIN" in self.busbar_type:
            self.priority = 8  # MAIN BUS-BAR
        else:
            self.priority = 9  # BUS-BAR


@dataclass
class AssemblyItem(LineItem):
    """가공비 품목"""

    assembly_type: str = ""  # "ASSEMBLY CHARGE", "조립비" 등

    def __post_init__(self):
        if not self.item_name:
            self.item_name = "ASSEMBLY CHARGE"
        if not self.unit:
            self.unit = UNIT_ASSEMBLY
        if not self.quantity:
            self.quantity = 1
        self.priority = 17  # 인건비 (부속자재 다음)


@dataclass
class MiscItem(LineItem):
    """기타 품목"""

    misc_type: str = ""

    def __post_init__(self):
        self.priority = 18  # 기타는 가장 마지막


@dataclass
class PanelEstimate:
    """
    분전반별 견적 정보

    실물 견적서 구조:
    - 품목들 (정렬된 순서)
    - 소계 (해당 분전반 합계)
    - 합계 (누적 합계)
    """

    panel_id: str  # 분전반 ID (예: "LP-M", "L-1", "L-2")
    quantity: int = 1  # 동일 분전반 수량 (기본 1, L-2~3인 경우 2)
    enclosure: EnclosureItem | None = None
    main_breaker: BreakerItem | None = None
    branch_breakers: list[BreakerItem] = field(default_factory=list)
    accessories: list[AccessoryItem] = field(default_factory=list)
    busbar: BusbarItem | None = None
    assembly_charge: AssemblyItem | None = None
    misc_items: list[MiscItem] = field(default_factory=list)

    @property
    def all_items_sorted(self) -> list[LineItem]:
        """
        모든 품목을 정렬된 순서로 반환

        정렬 기준: priority (낮을수록 먼저)
        실제 견적서 순서:
        1. 외함 (priority=1)
        2. SUSCOVER (priority=2)
        3. 메인 차단기 (priority=3)
        4. 분기 차단기들 (priority=4)
        5. E.T, N.T, N.P (priority=6,7,8)
        6. MAIN BUS-BAR (priority=9)
        7. BUS-BAR (priority=10)
        8. COATING, P-COVER (priority=11,12)
        9. 인출단자대, ELB보호커버, INSULATOR (priority=13,14,15)
        10. 단자대 (priority=16)
        11. ASSEMBLY CHARGE (priority=17)
        12. 기타 (priority=18)
        """
        items: list[LineItem] = []

        if self.enclosure:
            items.append(self.enclosure)
        if self.main_breaker:
            items.append(self.main_breaker)
        items.extend(self.branch_breakers)
        items.extend(self.accessories)
        if self.busbar:
            items.append(self.busbar)
        if self.assembly_charge:
            items.append(self.assembly_charge)
        items.extend(self.misc_items)

        # priority 기준 정렬
        return sorted(items, key=lambda x: x.priority)

    @property
    def subtotal(self) -> float:
        """분전반 소계 (참조용, Excel에는 수식 사용)"""
        return sum(item.amount for item in self.all_items_sorted)


@dataclass
class EstimateData:
    """
    견적서 생성용 전체 데이터

    Excel 매핑:
    - 표지 시트: customer_name (A5), project_name (A7), created_date (C3)
    - 견적서 시트: panels별 품목들
    - 요약 테이블: panels별 소계
    """

    customer_name: str  # 고객명 (예: "유광기전")
    project_name: str = ""  # 프로젝트명 (예: "공장 증설")
    created_date: str = ""  # 작성일 (빈 문자열이면 TODAY() 수식 사용)
    panels: list[PanelEstimate] = field(default_factory=list)

    @property
    def total_amount(self) -> float:
        """전체 합계 (VAT 별도)"""
        return sum(panel.subtotal * panel.quantity for panel in self.panels)

    @property
    def vat_included(self) -> float:
        """VAT 포함 금액"""
        return self.total_amount * 1.1


@dataclass
class ValidationReport:
    """
    검증 보고서

    품질 게이트:
    - 수식 보존 100%
    - 병합 셀 손상 0
    - 크로스 시트 참조 100% 정확
    """

    formula_preservation: bool  # 수식 보존 100%
    merged_cells_intact: bool  # 병합 셀 손상 0
    cross_references_valid: bool  # 크로스 참조 정확성
    violations: list[str] = field(default_factory=list)  # 위반 사항
    warnings: list[str] = field(default_factory=list)  # 경고 사항
    metadata: dict[str, Any] = field(default_factory=dict)  # 추가 정보

    @property
    def passed(self) -> bool:
        """전체 검증 통과 여부"""
        return (
            self.formula_preservation
            and self.merged_cells_intact
            and self.cross_references_valid
            and len(self.violations) == 0
        )


@dataclass
class EstimateOutput:
    """
    Stage 3 출력

    Evidence:
    - estimate_{timestamp}.xlsx
    - estimate_{timestamp}.pdf (선택적)
    - validation_report.json
    - metadata.json
    """

    excel_path: Path
    pdf_path: Path | None = None
    validation_report: ValidationReport = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.metadata:
            self.metadata = {
                "timestamp": datetime.now().isoformat(),
                "excel_size_bytes": (
                    self.excel_path.stat().st_size if self.excel_path.exists() else 0
                ),
                "pdf_generated": self.pdf_path is not None,
            }
