"""
CSV 카탈로그 → AI 최적화 JSON 변환 스크립트

입력: 절대코어파일/핵심파일풀/중요ai단가표의_2.0V_csv.csv (622 lines, 인간용)
출력: 절대코어파일/ai_catalog_v1.json (AI 최적화)

실행: python scripts/convert_catalog_to_ai.py
"""

import csv
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kis_estimator_core.models.catalog import (
    AICatalog,
    CatalogBreakerItem,
    CatalogEnclosureItem,
    BreakerDimensions,
    BreakerCategory,
    BreakerSeries,
    Brand,
    EnclosureType,
    EnclosureMaterial,
)


def parse_price(price_str: str) -> int:
    """가격 파싱 (쉼표 제거)"""
    try:
        return int(price_str.replace(",", "").replace(" ", ""))
    except:
        return 0


def parse_dimensions_from_note(note: str) -> Optional[BreakerDimensions]:
    """
    주석에서 치수 파싱
    예: "4P  100*130*60" → (100, 130, 60)
    예: "2P  50*130*60" → (50, 130, 60)
    """
    if not note:
        return None

    # 패턴: 숫자*숫자*숫자
    match = re.search(r'(\d+)\s*[*×]\s*(\d+)\s*[*×]\s*(\d+)', note)
    if match:
        return BreakerDimensions(
            width_mm=int(match.group(1)),
            height_mm=int(match.group(2)),
            depth_mm=int(match.group(3)),
        )
    return None


def get_default_dimensions(poles: int, frame_af: int) -> BreakerDimensions:
    """
    프레임과 극수 기반 기본 치수 반환
    원본: breaker_dimensions.json 참조
    """
    if frame_af <= 32:  # 소형
        return BreakerDimensions(width_mm=33, height_mm=70, depth_mm=42)
    elif frame_af <= 50:
        width = 50 if poles == 2 else (75 if poles == 3 else 100)
        return BreakerDimensions(width_mm=width, height_mm=130, depth_mm=60)
    elif frame_af <= 125:
        width = 50 if poles == 2 else (75 if poles == 3 else 100)
        return BreakerDimensions(width_mm=width, height_mm=130, depth_mm=60)
    elif frame_af <= 250:
        width = 70 if poles == 2 else (105 if poles == 3 else 140)
        return BreakerDimensions(width_mm=width, height_mm=165, depth_mm=60)
    elif frame_af <= 400:
        width = 140 if poles == 3 else 187
        return BreakerDimensions(width_mm=width, height_mm=257, depth_mm=109)
    else:  # 600~800AF
        width = 210 if poles == 3 else 280
        return BreakerDimensions(width_mm=width, height_mm=280, depth_mm=109)


def parse_breaker_row(row: list, line_no: int) -> Optional[CatalogBreakerItem]:
    """
    차단기 행 파싱

    row[0]: category (MCCB/ELB)
    row[1]: brand
    row[2]: series (경제형/표준형)
    row[3]: model
    row[4]: poles
    row[5]: current (예: "20A")
    row[6]: breaking_capacity (예: "14kA")
    row[7]: price
    row[8]: frame_af
    row[11]: notes (치수 정보)
    """
    try:
        # 카테고리 파싱
        if "MCCB" in row[0]:
            category = BreakerCategory.MCCB
        elif "ELB" in row[0]:
            category = BreakerCategory.ELB
        else:
            return None

        # 브랜드 파싱
        brand_str = row[1]
        if "상도" in brand_str:
            brand = Brand.SADOELE
        elif "LS" in brand_str or "산전" in brand_str:
            brand = Brand.LSIS
        elif "현대" in brand_str:
            brand = Brand.HDELECTRIC
        else:
            brand = Brand.SADOELE  # 기본값

        # 시리즈 파싱
        series_str = row[2]
        if "경제" in series_str:
            series = BreakerSeries.ECONOMY
        elif "표준" in series_str:
            series = BreakerSeries.STANDARD
        else:
            series = BreakerSeries.ECONOMY  # 기본값

        # 모델명
        model = row[3].strip()

        # 극수
        poles = int(row[4])
        if poles not in [2, 3, 4]:
            return None

        # 전류 (20A → 20)
        current_str = row[5].replace("A", "").strip()
        current_a = int(current_str)

        # 차단용량 (14kA → 14.0, 37Ka → 37.0 오타 처리)
        breaking_cap_str = row[6].replace("kA", "").replace("Ka", "").strip()
        breaking_capacity_ka = float(breaking_cap_str)

        # 가격
        price = parse_price(row[7])

        # 프레임
        frame_af = int(row[8]) if row[8].strip() else 50

        # 치수 (주석에서 파싱 or 기본값)
        note = row[11] if len(row) > 11 else ""
        dimensions = parse_dimensions_from_note(note)
        if not dimensions:
            dimensions = get_default_dimensions(poles, frame_af)

        return CatalogBreakerItem(
            category=category,
            brand=brand,
            series=series,
            model=model,
            poles=poles,
            current_a=current_a,
            frame_af=frame_af,
            breaking_capacity_ka=breaking_capacity_ka,
            price=price,
            dimensions=dimensions,
            source_line=line_no,
            notes=note if note else None,
        )

    except Exception as e:
        print(f"[WARNING] Line {line_no} 파싱 실패 (breaker): {e}")
        return None


def parse_enclosure_row(row: list, line_no: int) -> Optional[CatalogEnclosureItem]:
    """
    외함 행 파싱

    row[0]: type (옥내노출스틸1.6T)
    row[1]: brand
    row[2]: series (기성함)
    row[3]: model (HB304015)
    row[4]: material (STEEL 1.6T)
    row[5]: size (300*400*150)
    row[7]: price
    """
    try:
        # 타입 파싱
        type_str = row[0]
        if "옥내노출" in type_str:
            enc_type = EnclosureType.INDOOR_EXPOSED
        elif "옥외노출" in type_str:
            enc_type = EnclosureType.OUTDOOR_EXPOSED
        elif "옥내자립" in type_str:
            enc_type = EnclosureType.INDOOR_STANDALONE
        elif "옥외자립" in type_str:
            enc_type = EnclosureType.OUTDOOR_STANDALONE
        elif "매입" in type_str:
            enc_type = EnclosureType.EMBEDDED
        else:
            return None

        # 브랜드
        brand_str = row[1]
        if "한국" in brand_str:
            brand = Brand.KISCO
        elif "상도" in brand_str:
            brand = Brand.SADOELE
        else:
            brand = Brand.KISCO  # 기본값

        # 재질
        material_str = row[4]
        if "STEEL 1.6T" in material_str or "스틸1.6T" in type_str:
            material = EnclosureMaterial.STEEL_16T
        elif "STEEL 1.0T" in material_str or "스틸1.0T" in type_str:
            material = EnclosureMaterial.STEEL_10T
        elif "SUS201 1.2T" in material_str or "SUS" in type_str:
            material = EnclosureMaterial.SUS201_12T
        else:
            material = EnclosureMaterial.STEEL_16T  # 기본값

        # 모델명
        model = row[3].strip()

        # 사이즈 (300*400*150 → (300, 400, 150))
        size_str = row[5]
        size_match = re.search(r'(\d+)\s*[*×]\s*(\d+)\s*[*×]\s*(\d+)', size_str)
        if not size_match:
            return None

        width_mm = int(size_match.group(1))
        height_mm = int(size_match.group(2))
        depth_mm = int(size_match.group(3))

        # 가격
        price = parse_price(row[7])

        # 주석
        note = row[11] if len(row) > 11 else ""

        return CatalogEnclosureItem(
            type=enc_type,
            material=material,
            brand=brand,
            model=model,
            width_mm=width_mm,
            height_mm=height_mm,
            depth_mm=depth_mm,
            price=price,
            source_line=line_no,
            notes=note if note else None,
        )

    except Exception as e:
        print(f"[WARNING] Line {line_no} 파싱 실패 (enclosure): {e}")
        return None


def convert_csv_to_ai_catalog(
    csv_path: Path,
    output_path: Path,
) -> AICatalog:
    """CSV → AI 카탈로그 변환"""

    print(f"[INFO] 변환 시작: {csv_path}")

    breakers = []
    enclosures = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for line_no, row in enumerate(reader, start=1):
            if not row or not row[0].strip():
                continue

            category = row[0]

            # 차단기 행
            if "MCCB" in category or "ELB" in category:
                breaker = parse_breaker_row(row, line_no)
                if breaker:
                    breakers.append(breaker)

            # 외함 행
            elif "옥" in category or "매입" in category:
                enclosure = parse_enclosure_row(row, line_no)
                if enclosure:
                    enclosures.append(enclosure)

    # AICatalog 생성
    catalog = AICatalog(
        version="v1.0.0",
        created_at=datetime.now().isoformat(),
        source_file=csv_path.name,
        breakers=breakers,
        enclosures=enclosures,
    )

    # JSON 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(
            catalog.model_dump(),
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"[SUCCESS] 변환 완료: {output_path}")
    print(f"   차단기: {catalog.breaker_count}개")
    print(f"   외함: {catalog.enclosure_count}개")
    print(f"   총: {catalog.total_items}개")

    return catalog


if __name__ == "__main__":
    # 경로 설정
    csv_path = Path("절대코어파일/핵심파일풀/중요ai단가표의_2.0V_csv.csv")
    output_path = Path("절대코어파일/ai_catalog_v1.json")

    # 변환 실행
    catalog = convert_csv_to_ai_catalog(csv_path, output_path)

    print("\n[SUCCESS] AI 카탈로그 생성 완료!")
    print(f"   파일: {output_path}")
    print(f"   크기: {output_path.stat().st_size / 1024:.1f} KB")
