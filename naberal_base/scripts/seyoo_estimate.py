"""
세유이앤씨 대량 견적 - Railway 백엔드 API 호출 스크립트
총 52면 (분전반1~9)

도면 + 세유이앤씨.txt 기반 패널 스펙 정의
"""

import json
import sys
import time
import requests
from datetime import datetime

# Windows cp949 인코딩 문제 방지
sys.stdout.reconfigure(encoding="utf-8")

API_URL = "https://naberalproject-production.up.railway.app/v1/public/estimates"
CUSTOMER = "세유이앤씨"
PROJECT = "삼부골든타워"


def make_branches(specs: list[tuple]) -> list[dict]:
    """(type, poles, current, frame, qty) → 개별 차단기 리스트"""
    result = []
    for typ, poles, current, frame, qty in specs:
        for _ in range(qty):
            result.append({
                "type": typ, "poles": poles,
                "current": current, "frame": frame
            })
    return result


def make_panel(name, location, material, main, branches, accessories=None):
    """패널 dict 생성"""
    return {
        "name": name,
        "install_location": location,
        "enclosure_material": material,
        "main_breaker": main,
        "branch_breakers": branches,
        "accessories": accessories or [],
    }


# ===== 패널 정의 (도면 + txt 기반) =====

panels = []

# ── 분전반1 (3면) ──

# L-B1: Main MCCB 4P 225/200AT, 노출형, 옥내
# 도면: 4P 분기 ~5개 (L-B1A/B1B 피더 + B1 + I4 + SP), 2P 분기 ~10개
panels.append(make_panel(
    "L-B1", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 30, 50, 5),   # 4P 분기 5개 (L-B1A피더, L-B1B피더, B1, I4, SP)
        ("ELB", 2, 20, 30, 10),  # 2P 분기 10개
    ])
))

# L-B1A: Main MCCB 4P 50/30AT, txt: 4P 2개 + 2P 18개
panels.append(make_panel(
    "L-B1A", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 30, "frame": 50},
    make_branches([
        ("MCCB", 4, 30, 50, 2),   # SP + P.B1-C
        ("ELB", 2, 20, 30, 18),  # 2P 18개 (9줄)
    ])
))

# L-B1B: Main MCCB 4P 100/100AT, txt: 4P 2개 + 2P 22개
panels.append(make_panel(
    "L-B1B", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 100, "frame": 100},
    make_branches([
        ("MCCB", 4, 30, 50, 2),   # SP + P.B1-C
        ("ELB", 2, 20, 30, 22),  # 2P 22개 (11줄)
    ])
))

# ── 분전반2 (4면) ──

# L-1: Main MCCB 4P 225/200AT, 4P분기 4개, 2P분기 16개
# WHM/SPD 없는걸로 → 4P 분기로 취급
panels.append(make_panel(
    "L-1", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 30, 50, 4),   # 4P 4개
        ("ELB", 2, 20, 30, 16),  # 2P 16개 (8줄)
    ])
))

# L-1-1: Main MCCB 4P 50AF, 4P분기 2개, 2P분기 8개
panels.append(make_panel(
    "L-1-1", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 30, "frame": 50},
    make_branches([
        ("MCCB", 4, 30, 50, 2),
        ("ELB", 2, 20, 30, 8),
    ])
))

# L-1-2: Same as L-1-1
panels.append(make_panel(
    "L-1-2", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 30, "frame": 50},
    make_branches([
        ("MCCB", 4, 30, 50, 2),
        ("ELB", 2, 20, 30, 8),
    ])
))

# L-외등: 2P분기 16개, MG 14개 + TIMER 14개
# txt: MG는 SP 2개 빼고 모두 달림 = 14개, 모든 MG에 TIMER
panels.append(make_panel(
    "L-외등", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 30, "frame": 50},
    make_branches([
        ("ELB", 2, 20, 30, 16),  # 2P 16개 (SP 포함)
    ]),
    accessories=[
        {"type": "magnet", "quantity": 14},
        {"type": "timer", "quantity": 14},
        {"type": "switch", "quantity": 14},
    ]
))

# ── 분전반3 (4면) ──

# L-1A-M: Main 200AF
# 도면: 4P분기 여러개 + 2P분기
panels.append(make_panel(
    "L-1A-M", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 30, 50, 4),
        ("ELB", 2, 20, 30, 8),
    ])
))

# L-1B-M: Main 200AF (same structure as L-1A-M)
panels.append(make_panel(
    "L-1B-M", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 30, 50, 4),
        ("ELB", 2, 20, 30, 8),
    ])
))

# L-1A-1: 복잡한 MG경유 패널, 2P 10개 + 2P 8개 (두 분전반 합체)
# txt: 외함 600*1200*200, MG 2개 + PBL
panels.append(make_panel(
    "L-1A-1", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 30, "frame": 50},
    make_branches([
        ("ELB", 2, 20, 30, 18),  # 10+8개
    ]),
    accessories=[
        {"type": "magnet", "quantity": 2},
        {"type": "switch", "quantity": 2},
    ]
))

# L-1B-1: Same as L-1A-1
panels.append(make_panel(
    "L-1B-1", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 30, "frame": 50},
    make_branches([
        ("ELB", 2, 20, 30, 18),
    ]),
    accessories=[
        {"type": "magnet", "quantity": 2},
        {"type": "switch", "quantity": 2},
    ]
))

# ── 분전반4 (4면) ──

# L-농산, L-축산, L-수산: 옥외STEEL, Main 200AF, 4P 6개, 2P 24개
for name in ["L-농산", "L-축산", "L-수산"]:
    panels.append(make_panel(
        name, "옥외노출", "STEEL 1.6T",
        {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
        make_branches([
            ("MCCB", 4, 30, 50, 6),   # 4P 6개 (3줄)
            ("ELB", 2, 20, 30, 24),  # 2P 24개 (12줄)
        ])
    ))

# L-2: Main 100AF이하, 4P 2개, 2P 16개
panels.append(make_panel(
    "L-2", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 75, "frame": 100},
    make_branches([
        ("MCCB", 4, 30, 50, 2),
        ("ELB", 2, 20, 30, 16),
    ])
))

# ── 분전반5 (16면) ──

# L-2A-M: Main 200AF, 4P 6개, 2P 4개
panels.append(make_panel(
    "L-2A-M", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 30, 50, 6),
        ("ELB", 2, 20, 30, 4),
    ])
))

# L-2B-M: Main 200AF, H=1090 → 700*1200*150
panels.append(make_panel(
    "L-2B-M", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 30, 50, 8),
        ("ELB", 2, 20, 30, 6),
    ])
))

# L-2A-1~4: 4면, Main 4P 100AF이하, 4P분기 + 2P분기
for i in range(1, 5):
    panels.append(make_panel(
        f"L-2A-{i}", "옥내노출", "STEEL 1.6T",
        {"type": "MCCB", "poles": 4, "current": 50, "frame": 50},
        make_branches([
            ("MCCB", 4, 30, 50, 2),
            ("ELB", 2, 20, 30, 8),
        ])
    ))

# L-2B-1~9: 9면, 4P 2개(1줄), 2P 8개(4줄)
for i in range(1, 10):
    panels.append(make_panel(
        f"L-2B-{i}", "옥내노출", "STEEL 1.6T",
        {"type": "MCCB", "poles": 4, "current": 50, "frame": 50},
        make_branches([
            ("MCCB", 4, 30, 50, 2),
            ("ELB", 2, 20, 30, 8),
        ])
    ))

# ── 분전반6 (3면) ──

# P-냉장냉동 1~3: Main 400AF, 4P 14개, 2P 10개
for i in range(1, 4):
    panels.append(make_panel(
        f"P-냉장냉동{i}", "옥내노출", "STEEL 1.6T",
        {"type": "MCCB", "poles": 4, "current": 400, "frame": 400},
        make_branches([
            ("MCCB", 4, 30, 50, 14),  # 4P 14개 (7줄)
            ("ELB", 2, 20, 30, 10),  # 2P 10개 (5줄)
        ])
    ))

# ── 분전반7 (3면) ──

# L-PK: Main 4P, 4P 2개, 2P 18개
panels.append(make_panel(
    "L-PK", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 50, "frame": 50},
    make_branches([
        ("MCCB", 4, 30, 50, 2),
        ("ELB", 2, 20, 30, 18),
    ])
))

# L-F: Main 4P 100AF이하, 4P 2개, 2P 12개
panels.append(make_panel(
    "L-F", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 50, "frame": 50},
    make_branches([
        ("MCCB", 4, 30, 50, 2),
        ("ELB", 2, 20, 30, 12),
    ])
))

# L-POS: Main 4P, 4P 2개, 2P 16개
panels.append(make_panel(
    "L-POS", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 75, "frame": 100},
    make_branches([
        ("MCCB", 4, 30, 50, 2),
        ("ELB", 2, 20, 30, 16),
    ])
))

# ── 분전반8 (7면) ──
# P-에어컨1~7: 주로 4P 분기만

# P-에어컨1: Main 200AF, 4P 5개
panels.append(make_panel(
    "P-에어컨1", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 50, 50, 5),  # 4P 5개 (3줄)
    ])
))

# P-에어컨2: Main 400AF, 4P 4개
panels.append(make_panel(
    "P-에어컨2", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 400, "frame": 400},
    make_branches([
        ("MCCB", 4, 75, 100, 4),  # 4P 4개 (2줄)
    ])
))

# P-에어컨3: Main 400AF, 4P 5개
panels.append(make_panel(
    "P-에어컨3", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 400, "frame": 400},
    make_branches([
        ("MCCB", 4, 75, 100, 5),
    ])
))

# P-에어컨4~5: Main 400AF, 4P 5개
for i in [4, 5]:
    panels.append(make_panel(
        f"P-에어컨{i}", "옥내노출", "STEEL 1.6T",
        {"type": "MCCB", "poles": 4, "current": 400, "frame": 400},
        make_branches([
            ("MCCB", 4, 75, 100, 5),
        ])
    ))

# P-에어컨6: Main 400AF, 4P 4개
panels.append(make_panel(
    "P-에어컨6", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 400, "frame": 400},
    make_branches([
        ("MCCB", 4, 75, 100, 4),
    ])
))

# P-에어컨7: Main 400AF, 4P 5개
panels.append(make_panel(
    "P-에어컨7", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 400, "frame": 400},
    make_branches([
        ("MCCB", 4, 75, 100, 5),
    ])
))

# ── 분전반9 (8면) ──

# P-ELEV-1~6: 4P 2개 + 2P 2개
# 200AF → W=700, 100AF이하 → W=600
elev_specs = [
    ("P-ELEV-1", 200, 225),
    ("P-ELEV-2", 100, 100),
    ("P-ELEV-3", 100, 100),
    ("P-ELEV-4", 100, 100),
    ("P-ELEV-5", 200, 225),
    ("P-ELEV-6", 100, 100),
]
for name, current, frame in elev_specs:
    panels.append(make_panel(
        name, "옥내노출", "STEEL 1.6T",
        {"type": "MCCB", "poles": 4, "current": current, "frame": frame},
        make_branches([
            ("MCCB", 4, 30, 50, 2),
            ("ELB", 2, 20, 30, 2),
        ])
    ))

# L-CAR1: Main 600AF, 4P 200AF 6개
panels.append(make_panel(
    "L-CAR1", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 600, "frame": 600},
    make_branches([
        ("MCCB", 4, 200, 225, 6),  # 4P 200AF 6개 (3줄)
    ])
))

# L-CAR2: Main 200AF
panels.append(make_panel(
    "L-CAR2", "옥내노출", "STEEL 1.6T",
    {"type": "MCCB", "poles": 4, "current": 200, "frame": 225},
    make_branches([
        ("MCCB", 4, 30, 50, 2),
        ("ELB", 2, 20, 30, 4),
    ])
))


# ===== API 호출 =====

def call_estimate_api(panel: dict) -> dict:
    """단일 패널 견적 API 호출"""
    payload = {
        "panel_usage": "일반",
        "install_location": panel["install_location"],
        "enclosure_material": panel["enclosure_material"],
        "breaker_brand": "상도",
        "breaker_grade": "경제형",
        "main_breaker": panel["main_breaker"],
        "branch_breakers": panel["branch_breakers"],
        "accessories": panel.get("accessories", []),
        "customer_name": CUSTOMER,
        "project_name": f"{PROJECT} {panel['name']}",
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        if resp.status_code == 201:
            return resp.json()
        elif resp.status_code == 429:
            # Rate limited — wait and retry
            data = resp.json()
            wait = data.get("detail", {}).get("retry_after_seconds", 10)
            print(f"  ⏳ Rate limited, waiting {wait}s...")
            time.sleep(wait + 1)
            resp = requests.post(API_URL, json=payload, timeout=30)
            return resp.json() if resp.status_code == 201 else {"error": resp.text}
        else:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(f"세유이앤씨 대량 견적 시작: {len(panels)}면")
    print(f"API: {API_URL}")
    print("=" * 70)

    results = []
    total_amount = 0
    success_count = 0
    fail_count = 0

    for i, panel in enumerate(panels, 1):
        name = panel["name"]
        branch_count = len(panel["branch_breakers"])
        print(f"[{i:02d}/{len(panels)}] {name} (분기 {branch_count}개)...", end=" ", flush=True)

        result = call_estimate_api(panel)

        if "error" in result:
            print(f"❌ {result['error'][:80]}")
            fail_count += 1
            results.append({"panel": name, "success": False, "error": result["error"]})
        else:
            amt = result.get("total_amount", 0) or 0
            success = result.get("success", False)
            est_id = result.get("estimate_id", "")
            items_count = len(result.get("line_items", []))

            if success:
                print(f"✅ {amt:>12,}원 ({items_count}항목) [{est_id}]")
                success_count += 1
                total_amount += amt
            else:
                msg = result.get("message", "unknown")[:60]
                print(f"⚠️  {msg}")
                fail_count += 1

            results.append({
                "panel": name,
                "success": success,
                "amount": amt,
                "items": items_count,
                "id": est_id,
                "message": result.get("message", ""),
            })

        # Rate limit 방지: 10/min → 7초 간격
        if i < len(panels):
            time.sleep(7)

    # 결과 요약
    print("\n" + "=" * 70)
    print(f"견적 완료: {success_count}/{len(panels)} 성공, {fail_count} 실패")
    print(f"총 견적 금액: {total_amount:,}원")
    print(f"부가세 포함: {int(total_amount * 1.1):,}원")

    # 결과 JSON 저장
    output_path = r"C:\Users\PC\바탕 화면\세유이앤씨 견적요청\estimate_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "customer": CUSTOMER,
            "project": PROJECT,
            "total_panels": len(panels),
            "success_count": success_count,
            "fail_count": fail_count,
            "total_amount": total_amount,
            "total_with_vat": int(total_amount * 1.1),
            "timestamp": datetime.now().isoformat(),
            "panels": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {output_path}")
