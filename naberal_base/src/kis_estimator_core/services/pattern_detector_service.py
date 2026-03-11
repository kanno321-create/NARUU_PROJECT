"""
패턴 감지 서비스 (Phase XIII)

CEO 견적 수정 이력에서 반복되는 패턴을 감지합니다.
Zero-Mock 원칙: 모든 패턴은 실제 데이터에서 추출됩니다.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

PatternCategory = Literal[
    "PRICE_ADJUSTMENT",   # 가격 조정 패턴
    "BRAND_PREFERENCE",   # 브랜드 선호도
    "LAYOUT_RULE",        # 레이아웃 규칙
    "MATERIAL_SWAP"       # 자재 교체 규칙
]


@dataclass
class LearningPattern:
    """감지된 패턴 데이터 모델"""
    pattern_id: str
    category: PatternCategory
    condition: dict  # 조건 (예: {"breaker_af": "100AF", "pole": "4P"})
    action: dict     # 액션 (예: {"use_brand": "LS산전", "discount": 0.05})
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    occurrences: int   # 발생 횟수
    last_seen: datetime
    evidence_hashes: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "pattern_id": self.pattern_id,
            "category": self.category,
            "condition": self.condition,
            "action": self.action,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "last_seen": self.last_seen.isoformat(),
            "evidence_hashes": self.evidence_hashes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# ============================================================================
# Pattern Detector Service
# ============================================================================

class PatternDetectorService:
    """
    패턴 감지 서비스

    Features:
    - 가격 조정 패턴 감지 (예: 100AF 4P → 항상 5% 할인)
    - 브랜드 선호도 패턴 (예: 4P 100AF → LS산전 선호)
    - 레이아웃 규칙 패턴 (예: 특정 조합 시 좌우 배치)
    - 자재 교체 패턴 (예: 상도 → LS산전 교체 빈도)
    """

    # 신뢰도 임계값
    MIN_CONFIDENCE_THRESHOLD = 0.6
    MIN_OCCURRENCES = 3

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 파일 저장 경로 (None이면 기본 경로 사용)
        """
        if storage_path is None:
            self.storage_path = Path(__file__).parent.parent.parent.parent / "data" / "ai_memory" / "patterns"
        else:
            self.storage_path = storage_path

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._patterns: dict[str, LearningPattern] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        """기존 패턴 로드"""
        try:
            index_file = self.storage_path / "patterns_index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("patterns", []):
                        pattern = LearningPattern(
                            pattern_id=item["pattern_id"],
                            category=item["category"],
                            condition=item["condition"],
                            action=item["action"],
                            confidence=item["confidence"],
                            occurrences=item["occurrences"],
                            last_seen=datetime.fromisoformat(item["last_seen"]),
                            evidence_hashes=item.get("evidence_hashes", []),
                            created_at=datetime.fromisoformat(item["created_at"]),
                            updated_at=datetime.fromisoformat(item["updated_at"])
                        )
                        self._patterns[pattern.pattern_id] = pattern
                logger.info(f"로드된 패턴: {len(self._patterns)}개")
        except Exception as e:
            logger.warning(f"패턴 로드 실패: {e}")

    def _save_index(self) -> None:
        """인덱스 파일 저장"""
        index_file = self.storage_path / "patterns_index.json"
        data = {
            "patterns": [p.to_dict() for p in self._patterns.values()],
            "total": len(self._patterns),
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_pattern_key(self, category: PatternCategory, condition: dict) -> str:
        """패턴 키 생성 (중복 방지용)"""
        key_data = {
            "category": category,
            "condition": condition
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:12]

    async def detect_patterns_from_modifications(
        self,
        modifications: list[dict]
    ) -> list[LearningPattern]:
        """
        수정 이력에서 패턴 감지

        Args:
            modifications: 수정 이력 목록

        Returns:
            감지된 패턴 목록
        """
        detected = []

        # 가격 조정 패턴 감지
        price_patterns = await self._detect_price_patterns(modifications)
        detected.extend(price_patterns)

        # 브랜드 선호도 패턴 감지
        brand_patterns = await self._detect_brand_patterns(modifications)
        detected.extend(brand_patterns)

        # 레이아웃 규칙 패턴 감지
        layout_patterns = await self._detect_layout_patterns(modifications)
        detected.extend(layout_patterns)

        # 자재 교체 패턴 감지
        material_patterns = await self._detect_material_swap_patterns(modifications)
        detected.extend(material_patterns)

        logger.info(f"감지된 패턴: {len(detected)}개")
        return detected

    async def _detect_price_patterns(
        self,
        modifications: list[dict]
    ) -> list[LearningPattern]:
        """가격 조정 패턴 감지"""
        patterns = []
        price_adjustments: dict[str, list[dict]] = {}

        for mod in modifications:
            diff = mod.get("diff", {})
            if "total_price" in diff or "price" in diff:
                # 가격 변경이 있는 경우
                before_price = diff.get("total_price", {}).get("before", 0)
                after_price = diff.get("total_price", {}).get("after", 0)

                if before_price and after_price:
                    change_rate = (after_price - before_price) / before_price

                    # 조건 추출 (메인 차단기 스펙 등)
                    before_data = mod.get("before_snapshot", {})
                    panels = before_data.get("panels", [])
                    if panels:
                        main_breaker = panels[0].get("main_breaker", {})
                        condition_key = f"{main_breaker.get('pole', '')}_{main_breaker.get('frame', '')}"

                        if condition_key not in price_adjustments:
                            price_adjustments[condition_key] = []

                        price_adjustments[condition_key].append({
                            "change_rate": change_rate,
                            "evidence_hash": mod.get("evidence_hash", "")
                        })

        # 패턴 생성
        for condition_key, adjustments in price_adjustments.items():
            if len(adjustments) >= self.MIN_OCCURRENCES:
                avg_change = sum(a["change_rate"] for a in adjustments) / len(adjustments)
                pole, frame = condition_key.split("_") if "_" in condition_key else ("", "")

                pattern = await self._create_or_update_pattern(
                    category="PRICE_ADJUSTMENT",
                    condition={"pole": pole, "frame": frame},
                    action={"adjustment_rate": round(avg_change, 4)},
                    evidence_hashes=[a["evidence_hash"] for a in adjustments]
                )
                patterns.append(pattern)

        return patterns

    async def _detect_brand_patterns(
        self,
        modifications: list[dict]
    ) -> list[LearningPattern]:
        """브랜드 선호도 패턴 감지"""
        patterns = []
        brand_changes: dict[str, dict[str, int]] = {}

        for mod in modifications:
            diff = mod.get("diff", {})
            before_data = mod.get("before_snapshot", {})
            after_data = mod.get("after_snapshot", {})

            # 메인 차단기 브랜드 변경 분석
            before_panels = before_data.get("panels", [])
            after_panels = after_data.get("panels", [])

            for bp, ap in zip(before_panels, after_panels):
                before_brand = bp.get("main_breaker", {}).get("brand")
                after_brand = ap.get("main_breaker", {}).get("brand")

                if before_brand != after_brand and after_brand:
                    # 조건 키 생성
                    pole = ap.get("main_breaker", {}).get("pole", "")
                    frame = ap.get("main_breaker", {}).get("frame", "")
                    condition_key = f"{pole}_{frame}"

                    if condition_key not in brand_changes:
                        brand_changes[condition_key] = {}

                    if after_brand not in brand_changes[condition_key]:
                        brand_changes[condition_key][after_brand] = 0

                    brand_changes[condition_key][after_brand] += 1

        # 패턴 생성 (가장 많이 선택된 브랜드)
        for condition_key, brands in brand_changes.items():
            total = sum(brands.values())
            if total >= self.MIN_OCCURRENCES:
                preferred_brand = max(brands, key=brands.get)
                preference_rate = brands[preferred_brand] / total
                pole, frame = condition_key.split("_") if "_" in condition_key else ("", "")

                pattern = await self._create_or_update_pattern(
                    category="BRAND_PREFERENCE",
                    condition={"pole": pole, "frame": frame},
                    action={"preferred_brand": preferred_brand, "preference_rate": round(preference_rate, 4)},
                    evidence_hashes=[]
                )
                patterns.append(pattern)

        return patterns

    async def _detect_layout_patterns(
        self,
        modifications: list[dict]
    ) -> list[LearningPattern]:
        """레이아웃 규칙 패턴 감지"""
        patterns = []
        layout_changes: dict[str, list[dict]] = {}

        for mod in modifications:
            if "layout" in mod.get("modified_fields", []):
                before_layout = mod.get("before_snapshot", {}).get("layout", {})
                after_layout = mod.get("after_snapshot", {}).get("layout", {})

                if before_layout != after_layout:
                    # 레이아웃 변경 조건 추출
                    panels = mod.get("after_snapshot", {}).get("panels", [])
                    branch_count = sum(len(p.get("branch_breakers", [])) for p in panels)

                    condition_key = f"branches_{branch_count // 5 * 5}"  # 5개 단위로 그룹화

                    if condition_key not in layout_changes:
                        layout_changes[condition_key] = []

                    layout_changes[condition_key].append({
                        "layout": after_layout,
                        "evidence_hash": mod.get("evidence_hash", "")
                    })

        # 패턴 생성
        for condition_key, changes in layout_changes.items():
            if len(changes) >= self.MIN_OCCURRENCES:
                # 가장 많이 사용된 레이아웃 찾기
                layout_counts: dict[str, int] = {}
                for c in changes:
                    layout_str = json.dumps(c["layout"], sort_keys=True)
                    layout_counts[layout_str] = layout_counts.get(layout_str, 0) + 1

                preferred_layout_str = max(layout_counts, key=layout_counts.get)
                preferred_layout = json.loads(preferred_layout_str)

                pattern = await self._create_or_update_pattern(
                    category="LAYOUT_RULE",
                    condition={"branch_range": condition_key},
                    action={"preferred_layout": preferred_layout},
                    evidence_hashes=[c["evidence_hash"] for c in changes]
                )
                patterns.append(pattern)

        return patterns

    async def _detect_material_swap_patterns(
        self,
        modifications: list[dict]
    ) -> list[LearningPattern]:
        """자재 교체 패턴 감지"""
        patterns = []
        swaps: dict[str, int] = {}

        for mod in modifications:
            before_panels = mod.get("before_snapshot", {}).get("panels", [])
            after_panels = mod.get("after_snapshot", {}).get("panels", [])

            for bp, ap in zip(before_panels, after_panels):
                # 분기 차단기 자재 교체 분석
                before_branches = bp.get("branch_breakers", [])
                after_branches = ap.get("branch_breakers", [])

                for bb, ab in zip(before_branches, after_branches):
                    if bb.get("brand") != ab.get("brand"):
                        swap_key = f"{bb.get('brand', 'unknown')}_to_{ab.get('brand', 'unknown')}"
                        swaps[swap_key] = swaps.get(swap_key, 0) + 1

        # 패턴 생성
        for swap_key, count in swaps.items():
            if count >= self.MIN_OCCURRENCES:
                from_brand, to_brand = swap_key.split("_to_")

                pattern = await self._create_or_update_pattern(
                    category="MATERIAL_SWAP",
                    condition={"from_brand": from_brand},
                    action={"to_brand": to_brand, "swap_count": count},
                    evidence_hashes=[]
                )
                patterns.append(pattern)

        return patterns

    async def _create_or_update_pattern(
        self,
        category: PatternCategory,
        condition: dict,
        action: dict,
        evidence_hashes: list[str]
    ) -> LearningPattern:
        """패턴 생성 또는 업데이트"""
        pattern_key = self._generate_pattern_key(category, condition)

        # 기존 패턴 검색
        existing = None
        for p in self._patterns.values():
            if self._generate_pattern_key(p.category, p.condition) == pattern_key:
                existing = p
                break

        if existing:
            # 업데이트
            existing.occurrences += 1
            existing.action = action
            existing.confidence = min(1.0, existing.occurrences / 10)  # 10회 → 100% 신뢰도
            existing.last_seen = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            existing.evidence_hashes.extend(evidence_hashes)
            existing.evidence_hashes = existing.evidence_hashes[-100:]  # 최근 100개만 유지

            self._save_index()
            logger.info(f"패턴 업데이트: {existing.pattern_id}, 발생 횟수: {existing.occurrences}")
            return existing
        else:
            # 새 패턴 생성
            pattern = LearningPattern(
                pattern_id=str(uuid.uuid4()),
                category=category,
                condition=condition,
                action=action,
                confidence=min(1.0, len(evidence_hashes) / 10),
                occurrences=1,
                last_seen=datetime.utcnow(),
                evidence_hashes=evidence_hashes
            )
            self._patterns[pattern.pattern_id] = pattern
            self._save_index()

            logger.info(f"새 패턴 생성: {pattern.pattern_id}, 카테고리: {category}")
            return pattern

    async def get_patterns(
        self,
        category: Optional[PatternCategory] = None,
        min_confidence: float = 0.0,
        limit: int = 50
    ) -> list[LearningPattern]:
        """
        패턴 조회

        Args:
            category: 카테고리 필터
            min_confidence: 최소 신뢰도
            limit: 최대 반환 개수

        Returns:
            패턴 목록 (신뢰도 내림차순)
        """
        result = list(self._patterns.values())

        if category:
            result = [p for p in result if p.category == category]

        result = [p for p in result if p.confidence >= min_confidence]

        # 신뢰도 내림차순 정렬
        result.sort(key=lambda x: x.confidence, reverse=True)

        return result[:limit]

    async def get_pattern_by_id(self, pattern_id: str) -> Optional[LearningPattern]:
        """ID로 패턴 조회"""
        return self._patterns.get(pattern_id)

    async def delete_pattern(self, pattern_id: str) -> bool:
        """패턴 삭제"""
        if pattern_id in self._patterns:
            del self._patterns[pattern_id]
            self._save_index()
            logger.info(f"패턴 삭제: {pattern_id}")
            return True
        return False

    def get_stats(self) -> dict:
        """패턴 통계"""
        if not self._patterns:
            return {
                "total": 0,
                "by_category": {},
                "avg_confidence": 0.0,
                "latest": None
            }

        by_category: dict[str, int] = {}
        total_confidence = 0.0

        for p in self._patterns.values():
            by_category[p.category] = by_category.get(p.category, 0) + 1
            total_confidence += p.confidence

        latest = max(self._patterns.values(), key=lambda x: x.last_seen)

        return {
            "total": len(self._patterns),
            "by_category": by_category,
            "avg_confidence": round(total_confidence / len(self._patterns), 4),
            "latest": latest.last_seen.isoformat()
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_pattern_detector: Optional[PatternDetectorService] = None


def get_pattern_detector() -> PatternDetectorService:
    """패턴 감지 서비스 싱글톤 인스턴스 반환"""
    global _pattern_detector
    if _pattern_detector is None:
        _pattern_detector = PatternDetectorService()
    return _pattern_detector
