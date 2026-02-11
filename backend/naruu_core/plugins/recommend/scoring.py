"""추천 스코어링 엔진.

가중치:
- category_match:  0.30  (카테고리 일치)
- tag_match:       0.25  (태그 일치율)
- rating:          0.20  (평점)
- popularity:      0.15  (인기도)
- budget_fit:      0.10  (예산 적합도)
"""

from __future__ import annotations

import math

WEIGHTS = {
    "category_match": 0.30,
    "tag_match": 0.25,
    "rating": 0.20,
    "popularity": 0.15,
    "budget_fit": 0.10,
}


def score_spot(
    *,
    category: str,
    tags_csv: str,
    rating: float,
    popularity_score: float,
    avg_price_krw: int,
    req_categories: list[str],
    req_tags: list[str],
    req_budget_krw: int,
) -> tuple[float, list[str]]:
    """스팟 종합 점수 계산.

    Returns:
        (score, reasons) — score는 0.0~1.0, reasons는 점수 근거 목록.
    """
    reasons: list[str] = []

    # 1) 카테고리 매치
    if req_categories and category in req_categories:
        cat_score = 1.0
        reasons.append(f"카테고리 일치: {category}")
    elif not req_categories:
        cat_score = 0.5  # 필터 없으면 중간값
    else:
        cat_score = 0.0

    # 2) 태그 매치
    spot_tags = {t.strip().lower() for t in tags_csv.split(",") if t.strip()}
    req_tag_set = {t.lower() for t in req_tags}
    if req_tag_set and spot_tags:
        overlap = spot_tags & req_tag_set
        tag_score = len(overlap) / len(req_tag_set)
        if overlap:
            reasons.append(f"태그 일치: {', '.join(sorted(overlap))}")
    elif not req_tag_set:
        tag_score = 0.5
    else:
        tag_score = 0.0

    # 3) 평점 (0~5 → 0~1)
    rating_score = min(rating / 5.0, 1.0) if rating > 0 else 0.0
    if rating >= 4.0:
        reasons.append(f"높은 평점: {rating:.1f}")

    # 4) 인기도 (0~1 클리핑)
    pop_score = min(max(popularity_score, 0.0), 1.0)
    if pop_score >= 0.7:
        reasons.append(f"인기도 {pop_score:.0%}")

    # 5) 예산 적합도
    if req_budget_krw > 0 and avg_price_krw > 0:
        if avg_price_krw <= req_budget_krw:
            budget_score = 1.0
            reasons.append("예산 범위 내")
        else:
            ratio = req_budget_krw / avg_price_krw
            budget_score = max(ratio, 0.0)
    else:
        budget_score = 0.5  # 예산 미지정

    total = (
        WEIGHTS["category_match"] * cat_score
        + WEIGHTS["tag_match"] * tag_score
        + WEIGHTS["rating"] * rating_score
        + WEIGHTS["popularity"] * pop_score
        + WEIGHTS["budget_fit"] * budget_score
    )

    return round(total, 4), reasons


def haversine_km(
    lat1: float, lon1: float, lat2: float, lon2: float,
) -> float:
    """두 좌표 간 거리 (km). Haversine 공식."""
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
