"""
PDF Generator with Evidence Footer
reportlab 기반 PDF 생성 (표지, 조건표, 상세 견적, Evidence Footer)

PDF_STANDARD.md v1 준수:
- 맑은 고딕 폰트
- A4 (210 x 297 mm)
- 여백: 20mm
- Evidence Footer: Build:[tag]  Hash:[hash]  Content:[content_hash]  TS:[timestamp]
"""

import hashlib
import json
import logging
import subprocess
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from kis_estimator_core.core.ssot.constants_format import UNIT_ENCLOSURE
from kis_estimator_core.core.ssot.ssot_loader import load_rounding

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    PDF 생성기 (PDF_STANDARD.md v1 준수)

    Features:
    - Evidence Footer 자동 추가
    - SSOT (VAT, 할인, 라운딩) 반영
    - 맑은 고딕 폰트, A4, 20mm 여백
    """

    def __init__(self):
        """PDF 생성기 초기화"""
        # 맑은 고딕 폰트 등록 시도 (Windows 기준)
        try:
            font_path = r"C:\Windows\Fonts\malgun.ttf"
            if Path(font_path).exists():
                pdfmetrics.registerFont(TTFont("MalgunGothic", font_path))
                self.font_name = "MalgunGothic"
            else:
                logger.warning("맑은 고딕 폰트를 찾을 수 없습니다. Helvetica 사용")
                self.font_name = "Helvetica"
        except Exception as e:
            logger.warning(f"폰트 등록 실패: {e}. Helvetica 사용")
            self.font_name = "Helvetica"

        # A4 크기 및 여백 설정
        self.page_width, self.page_height = A4
        self.margin = 20 * mm
        self.content_width = self.page_width - 2 * self.margin
        self.content_height = self.page_height - 2 * self.margin

    def generate(
        self,
        estimate_data,
        output_path: Path,
        build_tag: str | None = None,
        git_hash: str | None = None,
    ) -> Path:
        """
        PDF 생성 메인 메서드

        Args:
            estimate_data: EstimateData 객체
            output_path: PDF 출력 경로
            build_tag: 빌드 태그 (예: prod-20251030T1252-lockin)
            git_hash: Git commit hash (8자리)

        Returns:
            Path: 생성된 PDF 파일 경로
        """
        logger.info(f"Starting PDF generation: {output_path}")

        # Git 정보 자동 추출 (없으면 기본값)
        if not build_tag:
            build_tag = self._get_build_tag()
        if not git_hash:
            git_hash = self._get_git_hash()

        timestamp = datetime.now(UTC).isoformat()

        # Content Hash 계산 (estimate_data + build_tag + git_hash)
        content_hash = self._calculate_content_hash(estimate_data, build_tag, git_hash)

        # Canvas 생성
        c = canvas.Canvas(str(output_path), pagesize=A4)

        # 메타데이터 설정
        c.setAuthor("KIS Estimator System")
        c.setCreator("NABERAL KIS Estimator v1.0")
        c.setTitle(f"{estimate_data.project_name} 견적서")
        c.setSubject("Electrical Panel Estimate")

        # 1. 표지 생성
        self._draw_cover_page(c, estimate_data, build_tag, git_hash, content_hash, timestamp)

        # 2. 조건표 생성
        c.showPage()
        self._draw_terms_page(c, build_tag, git_hash, content_hash, timestamp)

        # 3. 상세 견적 생성
        c.showPage()
        self._draw_estimate_details(c, estimate_data, build_tag, git_hash, content_hash, timestamp)

        # PDF 저장
        c.save()

        logger.info(f"PDF generation completed: {output_path}")
        return output_path

    def _draw_cover_page(self, c, estimate_data, build_tag, git_hash, content_hash, timestamp):
        """
        표지 생성 (견적서표지작성법.txt 준수)

        표지 구성:
        1. 제목 "견적서"
        2. 날짜 (YYYY년 MM월 DD일)
        3. 거래처명
        4. 건명
        5. 분전반 정보 테이블 (분전반명/사이즈/단위/수량/견적가/특이사항)
        6. 합계 (소계/부가세/총액)
        7. NOTE 섹션 (차단기 브랜드, 외함 종류/스펙)
        """
        y = self.page_height - self.margin - 25 * mm

        # === 1. 제목 ===
        c.setFont(self.font_name, 28)
        c.drawCentredString(self.page_width / 2, y, "견 적 서")
        y -= 20 * mm

        # === 2. 날짜 (C3) ===
        c.setFont(self.font_name, 11)
        date_str = datetime.now().strftime("%Y년 %m월 %d일")
        c.drawRightString(self.page_width - self.margin, y, date_str)
        y -= 15 * mm

        # === 3. 거래처명 (C5) ===
        c.setFont(self.font_name, 12)
        c.drawString(self.margin, y, f"거래처: {estimate_data.customer_name}")
        y -= 8 * mm

        # === 4. 건명 (C7) ===
        project_name = estimate_data.project_name or ""
        if project_name:
            c.drawString(self.margin, y, f"건  명: {project_name}")
            y -= 12 * mm
        else:
            y -= 4 * mm

        # === 5. 분전반 정보 테이블 (B17~J17) ===
        y -= 5 * mm
        c.setFont(self.font_name, 10)

        # 테이블 헤더
        col_widths = [60*mm, 50*mm, 20*mm, 20*mm, 40*mm, 40*mm]  # 분전반명, 사이즈, 단위, 수량, 견적가, 특이사항
        headers = ["분전반명", "사이즈", "단위", "수량", "견적가", "특이사항"]

        x = self.margin
        c.setFont(self.font_name, 9)
        for i, header in enumerate(headers):
            c.drawString(x + 2*mm, y, header)
            x += col_widths[i]

        # 헤더 밑줄
        y -= 3 * mm
        c.line(self.margin, y, self.page_width - self.margin, y)
        y -= 5 * mm

        # 테이블 데이터 (분전반별)
        grand_subtotal = Decimal("0")
        panel_count = 0

        # 차단기 브랜드 및 외함 정보 수집 (NOTE용)
        breaker_brands = set()
        enclosure_specs = []

        if estimate_data.panels:
            for panel in estimate_data.panels:
                panel_count += 1
                x = self.margin

                # 분전반명
                panel_name = getattr(panel, 'panel_name', None) or f"분전반{panel_count}"
                c.drawString(x + 2*mm, y, panel_name[:12])  # 최대 12자
                x += col_widths[0]

                # 사이즈 (W×H×D)
                enclosure = getattr(panel, 'enclosure', None)
                if enclosure:
                    w = getattr(enclosure, 'width', 0)
                    h = getattr(enclosure, 'height', 0)
                    d = getattr(enclosure, 'depth', 0)
                    size_str = f"{w}×{h}×{d}"
                    enc_type = getattr(enclosure, 'type', '')
                    enc_material = getattr(enclosure, 'material', '')
                    if enc_type or enc_material:
                        enclosure_specs.append(f"{enc_type} {enc_material}".strip())
                else:
                    size_str = "-"
                c.drawString(x + 2*mm, y, size_str[:12])
                x += col_widths[1]

                # 단위
                c.drawString(x + 2*mm, y, UNIT_ENCLOSURE)
                x += col_widths[2]

                # 수량
                qty = getattr(panel, 'quantity', 1) or 1
                c.drawString(x + 2*mm, y, str(qty))
                x += col_widths[3]

                # 견적가 (소계)
                if hasattr(panel, "total_price"):
                    panel_subtotal = Decimal(str(panel.total_price))
                elif hasattr(panel, "all_items_sorted"):
                    panel_subtotal = Decimal(sum(item.amount for item in panel.all_items_sorted))
                else:
                    panel_subtotal = Decimal("0")
                grand_subtotal += panel_subtotal * qty
                c.drawString(x + 2*mm, y, f"{panel_subtotal:,.0f}")
                x += col_widths[4]

                # 특이사항
                remarks = getattr(panel, 'remarks', '') or ""
                c.drawString(x + 2*mm, y, remarks[:10])  # 최대 10자

                # 차단기 브랜드 수집
                main_breaker = getattr(panel, 'main_breaker', None)
                if main_breaker:
                    brand = getattr(main_breaker, 'brand', None)
                    if brand:
                        breaker_brands.add(brand)

                y -= 6 * mm

                if y < self.margin + 80 * mm:  # 페이지 하단 근처면 중단
                    break

        # 테이블 하단 줄
        y -= 2 * mm
        c.line(self.margin, y, self.page_width - self.margin, y)
        y -= 10 * mm

        # === 6. 합계 섹션 ===
        c.setFont(self.font_name, 11)

        # 소계
        c.drawString(self.margin, y, "합    계:")
        c.drawRightString(self.page_width - self.margin - 50*mm, y, f"{grand_subtotal:,.0f}원")
        y -= 7 * mm

        # 부가세 (SSOT에서 동적 로드)
        rounding_rules = load_rounding()
        vat_pct = Decimal(str(rounding_rules.get("vat_pct", 0.10)))
        vat_amount = grand_subtotal * vat_pct
        vat_display_pct = int(vat_pct * 100)
        c.drawString(self.margin, y, f"부가세 ({vat_display_pct}%):")
        c.drawRightString(self.page_width - self.margin - 50*mm, y, f"{vat_amount:,.0f}원")
        y -= 7 * mm

        # 총액
        grand_total = grand_subtotal + vat_amount
        c.setFont(self.font_name, 14)
        c.drawString(self.margin, y, "총    액:")
        c.drawRightString(self.page_width - self.margin - 50*mm, y, f"{grand_total:,.0f}원")
        y -= 15 * mm

        # === 7. NOTE 섹션 ===
        c.setFont(self.font_name, 9)
        breaker_brand_str = ", ".join(breaker_brands) if breaker_brands else "상도차단기"
        enclosure_spec_str = enclosure_specs[0] if enclosure_specs else "옥내노출 STEEL 1.6T"

        note_text = f"< NOTE > 1. 차단기: {breaker_brand_str}, 외함: {enclosure_spec_str}"
        c.drawString(self.margin, y, note_text)

        # Evidence Footer
        self._draw_footer(c, build_tag, git_hash, content_hash, timestamp)

    def _draw_terms_page(self, c, build_tag, git_hash, content_hash, timestamp):
        """조건표 생성"""
        y = self.page_height - self.margin - 20 * mm

        c.setFont(self.font_name, 16)
        c.drawString(self.margin, y, "거래 조건")
        y -= 15 * mm

        c.setFont(self.font_name, 12)
        terms = [
            "결제 조건: 계약금 30% / 중도금 40% / 잔금 30%",
            "배송 조건: EXW (공장 인도)",
            "보증 기간: 제품 1년, 설치 6개월",
            "견적 유효 기간: 30일",
            "납기: 주문 후 4-6주",
        ]

        for term in terms:
            c.drawString(self.margin, y, f"• {term}")
            y -= 7 * mm

        # Evidence Footer
        self._draw_footer(c, build_tag, git_hash, content_hash, timestamp)

    def _draw_estimate_details(self, c, estimate_data, build_tag, git_hash, content_hash, timestamp):
        """상세 견적 생성"""
        y = self.page_height - self.margin - 20 * mm

        c.setFont(self.font_name, 16)
        c.drawString(self.margin, y, "상세 견적")
        y -= 15 * mm

        c.setFont(self.font_name, 10)

        # 품목별 상세 내역 (간소화)
        if estimate_data.panels:
            panel = estimate_data.panels[0]
            items = panel.all_items_sorted if hasattr(panel, 'all_items_sorted') else []
            for i, item in enumerate(items[:10]):  # 최대 10개만 표시
                line = f"{i+1}. {item.item_name} x {item.quantity} = {item.amount:,.0f}원"
                c.drawString(self.margin, y, line)
                y -= 5 * mm

                if y < self.margin + 30 * mm:  # 페이지 하단 근처
                    break

        # Evidence Footer
        self._draw_footer(c, build_tag, git_hash, content_hash, timestamp)

    def _draw_footer(self, c, build_tag, git_hash, content_hash, timestamp):
        """
        Evidence Footer 생성 (모든 페이지)
        Format: Build:[tag]  Hash:[git_hash]  Content:[content_hash]  TS:[timestamp]
        """
        footer_y = 10 * mm  # 페이지 하단에서 10mm 위치

        c.setFont("Helvetica", 8)
        footer_text = f"Build:{build_tag}  Hash:{git_hash}  Content:{content_hash}  TS:{timestamp}"
        c.drawCentredString(self.page_width / 2, footer_y, footer_text)

    def _get_build_tag(self) -> str:
        """빌드 태그 자동 추출 (git describe 사용)"""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Git tag 추출 실패: {e}")

        return "unknown"

    def _get_git_hash(self) -> str:
        """Git commit hash 자동 추출 (8자리)"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short=8", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Git hash 추출 실패: {e}")

        return "00000000"

    def _calculate_content_hash(self, estimate_data, build_tag: str = "", git_hash: str = "") -> str:
        """
        PDF 내용의 SHA256 해시 계산 (8자리)

        Args:
            estimate_data: EstimateData 객체
            build_tag: 빌드 태그 (해시에 포함)
            git_hash: Git 해시 (해시에 포함)

        Returns:
            str: SHA256 해시의 처음 8자리

        Note:
            Content Hash는 견적 데이터의 무결성을 보장합니다.
            동일한 입력 데이터는 항상 동일한 해시를 생성합니다.
        """
        try:
            # 핵심 내용을 딕셔너리로 추출
            content_dict = {
                "customer_name": estimate_data.customer_name,
                "project_name": estimate_data.project_name,
                "build_tag": build_tag,
                "git_hash": git_hash,
                "panels": [],
            }

            # 패널 정보 추출
            if estimate_data.panels:
                for panel in estimate_data.panels:
                    panel_dict = {
                        "total_price": float(panel.total_price) if hasattr(panel, "total_price") else 0,
                        "items": [],
                    }

                    # 품목 정보 추출 (최대 10개)
                    items = panel.all_items_sorted if hasattr(panel, "all_items_sorted") else []
                    for item in items[:10]:
                        item_dict = {
                            "description": item.item_name if hasattr(item, "item_name") else "",
                            "quantity": item.quantity if hasattr(item, "quantity") else 0,
                            "line_total": float(item.amount) if hasattr(item, "amount") else 0,
                        }
                        panel_dict["items"].append(item_dict)

                    content_dict["panels"].append(panel_dict)

            # JSON으로 직렬화 (정렬 및 일관성 보장)
            content_json = json.dumps(content_dict, sort_keys=True, ensure_ascii=False)

            # SHA256 해시 계산
            content_bytes = content_json.encode("utf-8")
            hash_object = hashlib.sha256(content_bytes)
            hash_hex = hash_object.hexdigest()

            # 처음 8자리 반환
            return hash_hex[:8]

        except Exception as e:
            logger.warning(f"Content hash 계산 실패: {e}")
            return "00000000"
