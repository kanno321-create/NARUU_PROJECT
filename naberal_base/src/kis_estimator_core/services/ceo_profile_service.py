"""
CEO 프로파일 서비스 (Phase XIII)

CEO의 견적 수정 패턴에서 선호도를 학습하고 프로파일을 구축합니다.
Zero-Mock 원칙: 모든 선호도는 실제 수정 이력에서 추출됩니다.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

PreferenceCategory = Literal["BRAND", "PRICE", "LAYOUT", "MATERIAL"]


@dataclass
class CEOPreference:
    """CEO 선호도 항목"""
    preference_id: str
    user_id: str
    category: PreferenceCategory
    key: str  # 예: "preferred_brand_4P_100AF"
    value: str | float | dict
    confidence: float  # 0.0 ~ 1.0
    sample_size: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "preference_id": self.preference_id,
            "user_id": self.user_id,
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "sample_size": self.sample_size,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class CEOProfile:
    """CEO 프로파일"""
    user_id: str
    brand_preferences: dict[str, str] = field(default_factory=dict)  # {"4P_100AF": "LS산전"}
    price_thresholds: dict[str, float] = field(default_factory=dict)  # {"discount_max": 0.15}
    layout_style: dict = field(default_factory=dict)  # {"prefer_compact": True}
    preferences: list[CEOPreference] = field(default_factory=list)
    sample_size: int = 0
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "user_id": self.user_id,
            "brand_preferences": self.brand_preferences,
            "price_thresholds": self.price_thresholds,
            "layout_style": self.layout_style,
            "preferences": [p.to_dict() for p in self.preferences],
            "sample_size": self.sample_size,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


# ============================================================================
# CEO Profile Service
# ============================================================================

class CEOProfileService:
    """
    CEO 프로파일 서비스

    Features:
    - 브랜드 선호도 학습
    - 가격 조정 임계값 학습
    - 레이아웃 스타일 학습
    - 프로파일 기반 견적 추천
    """

    # 신뢰도 계산을 위한 최소 샘플 수
    MIN_SAMPLES_FOR_CONFIDENCE = 5

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 파일 저장 경로 (None이면 기본 경로 사용)
        """
        if storage_path is None:
            self.storage_path = Path(__file__).parent.parent.parent.parent / "data" / "ai_memory" / "profiles"
        else:
            self.storage_path = storage_path

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._profiles: dict[str, CEOProfile] = {}
        self._load_existing()

    def _load_existing(self) -> None:
        """기존 프로파일 로드"""
        try:
            index_file = self.storage_path / "profiles_index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("profiles", []):
                        preferences = []
                        for pref_data in item.get("preferences", []):
                            pref = CEOPreference(
                                preference_id=pref_data["preference_id"],
                                user_id=pref_data["user_id"],
                                category=pref_data["category"],
                                key=pref_data["key"],
                                value=pref_data["value"],
                                confidence=pref_data["confidence"],
                                sample_size=pref_data["sample_size"],
                                created_at=datetime.fromisoformat(pref_data["created_at"]),
                                updated_at=datetime.fromisoformat(pref_data["updated_at"])
                            )
                            preferences.append(pref)

                        profile = CEOProfile(
                            user_id=item["user_id"],
                            brand_preferences=item.get("brand_preferences", {}),
                            price_thresholds=item.get("price_thresholds", {}),
                            layout_style=item.get("layout_style", {}),
                            preferences=preferences,
                            sample_size=item.get("sample_size", 0),
                            last_updated=datetime.fromisoformat(item["last_updated"]) if item.get("last_updated") else None
                        )
                        self._profiles[profile.user_id] = profile
                logger.info(f"로드된 프로파일: {len(self._profiles)}개")
        except Exception as e:
            logger.warning(f"프로파일 로드 실패: {e}")

    def _save_index(self) -> None:
        """인덱스 파일 저장"""
        index_file = self.storage_path / "profiles_index.json"
        data = {
            "profiles": [p.to_dict() for p in self._profiles.values()],
            "total": len(self._profiles),
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def learn_from_modifications(
        self,
        user_id: str,
        modifications: list[dict]
    ) -> CEOProfile:
        """
        수정 이력에서 CEO 선호도 학습

        Args:
            user_id: CEO 사용자 ID
            modifications: 수정 이력 목록

        Returns:
            업데이트된 CEO 프로파일
        """
        profile = await self._get_or_create_profile(user_id)

        # 브랜드 선호도 학습
        await self._learn_brand_preferences(profile, modifications)

        # 가격 임계값 학습
        await self._learn_price_thresholds(profile, modifications)

        # 레이아웃 스타일 학습
        await self._learn_layout_style(profile, modifications)

        # 메타데이터 업데이트
        profile.sample_size += len(modifications)
        profile.last_updated = datetime.utcnow()

        self._save_index()
        logger.info(f"프로파일 학습 완료: {user_id}, 샘플 수: {profile.sample_size}")

        return profile

    async def _get_or_create_profile(self, user_id: str) -> CEOProfile:
        """프로파일 조회 또는 생성"""
        if user_id not in self._profiles:
            self._profiles[user_id] = CEOProfile(user_id=user_id)
        return self._profiles[user_id]

    async def _learn_brand_preferences(
        self,
        profile: CEOProfile,
        modifications: list[dict]
    ) -> None:
        """브랜드 선호도 학습"""
        brand_selections: dict[str, dict[str, int]] = {}

        for mod in modifications:
            after_data = mod.get("after_snapshot", {})
            panels = after_data.get("panels", [])

            for panel in panels:
                # 메인 차단기 브랜드
                main = panel.get("main_breaker", {})
                brand = main.get("brand")
                pole = main.get("pole", "")
                frame = main.get("frame", "")

                if brand and pole and frame:
                    key = f"{pole}_{frame}"
                    if key not in brand_selections:
                        brand_selections[key] = {}
                    brand_selections[key][brand] = brand_selections[key].get(brand, 0) + 1

        # 선호도 추출
        for spec_key, brands in brand_selections.items():
            if sum(brands.values()) >= self.MIN_SAMPLES_FOR_CONFIDENCE:
                preferred_brand = max(brands, key=brands.get)
                total = sum(brands.values())
                confidence = brands[preferred_brand] / total

                profile.brand_preferences[spec_key] = preferred_brand

                # 상세 선호도 저장
                await self._update_preference(
                    profile=profile,
                    category="BRAND",
                    key=f"preferred_brand_{spec_key}",
                    value=preferred_brand,
                    confidence=confidence,
                    sample_size=total
                )

    async def _learn_price_thresholds(
        self,
        profile: CEOProfile,
        modifications: list[dict]
    ) -> None:
        """가격 임계값 학습"""
        price_changes: list[float] = []

        for mod in modifications:
            diff = mod.get("diff", {})
            if "total_price" in diff:
                before = diff["total_price"].get("before", 0)
                after = diff["total_price"].get("after", 0)

                if before and before > 0:
                    change_rate = (after - before) / before
                    price_changes.append(change_rate)

        if len(price_changes) >= self.MIN_SAMPLES_FOR_CONFIDENCE:
            # 할인 최대값 (음수 변화율의 최소값)
            discounts = [c for c in price_changes if c < 0]
            if discounts:
                max_discount = abs(min(discounts))
                avg_discount = abs(sum(discounts) / len(discounts))

                profile.price_thresholds["discount_max"] = round(max_discount, 4)
                profile.price_thresholds["discount_avg"] = round(avg_discount, 4)

                await self._update_preference(
                    profile=profile,
                    category="PRICE",
                    key="discount_max",
                    value=max_discount,
                    confidence=min(1.0, len(discounts) / 10),
                    sample_size=len(discounts)
                )

            # 인상 최대값 (양수 변화율의 최대값)
            increases = [c for c in price_changes if c > 0]
            if increases:
                max_increase = max(increases)
                avg_increase = sum(increases) / len(increases)

                profile.price_thresholds["increase_max"] = round(max_increase, 4)
                profile.price_thresholds["increase_avg"] = round(avg_increase, 4)

                await self._update_preference(
                    profile=profile,
                    category="PRICE",
                    key="increase_max",
                    value=max_increase,
                    confidence=min(1.0, len(increases) / 10),
                    sample_size=len(increases)
                )

    async def _learn_layout_style(
        self,
        profile: CEOProfile,
        modifications: list[dict]
    ) -> None:
        """레이아웃 스타일 학습"""
        layout_choices: dict[str, int] = {}

        for mod in modifications:
            if "layout" in mod.get("modified_fields", []):
                after_layout = mod.get("after_snapshot", {}).get("layout", {})
                layout_str = json.dumps(after_layout, sort_keys=True)
                layout_choices[layout_str] = layout_choices.get(layout_str, 0) + 1

        if layout_choices and sum(layout_choices.values()) >= self.MIN_SAMPLES_FOR_CONFIDENCE:
            # 가장 많이 선택된 레이아웃
            preferred_layout_str = max(layout_choices, key=layout_choices.get)
            preferred_layout = json.loads(preferred_layout_str)
            total = sum(layout_choices.values())
            confidence = layout_choices[preferred_layout_str] / total

            profile.layout_style = preferred_layout

            await self._update_preference(
                profile=profile,
                category="LAYOUT",
                key="preferred_style",
                value=preferred_layout,
                confidence=confidence,
                sample_size=total
            )

    async def _update_preference(
        self,
        profile: CEOProfile,
        category: PreferenceCategory,
        key: str,
        value: str | float | dict,
        confidence: float,
        sample_size: int
    ) -> None:
        """선호도 업데이트 또는 추가"""
        import uuid

        # 기존 선호도 찾기
        existing = None
        for pref in profile.preferences:
            if pref.category == category and pref.key == key:
                existing = pref
                break

        if existing:
            # 업데이트
            existing.value = value
            existing.confidence = confidence
            existing.sample_size = sample_size
            existing.updated_at = datetime.utcnow()
        else:
            # 새로 추가
            pref = CEOPreference(
                preference_id=str(uuid.uuid4()),
                user_id=profile.user_id,
                category=category,
                key=key,
                value=value,
                confidence=confidence,
                sample_size=sample_size
            )
            profile.preferences.append(pref)

    async def get_profile(self, user_id: str) -> Optional[CEOProfile]:
        """CEO 프로파일 조회"""
        return self._profiles.get(user_id)

    async def get_all_profiles(self) -> list[CEOProfile]:
        """모든 프로파일 조회"""
        return list(self._profiles.values())

    async def get_recommendation(
        self,
        user_id: str,
        breaker_spec: dict
    ) -> dict:
        """
        CEO 선호도 기반 추천

        Args:
            user_id: CEO 사용자 ID
            breaker_spec: 차단기 사양 {"pole": "4P", "frame": "100AF", ...}

        Returns:
            추천 결과
        """
        profile = self._profiles.get(user_id)

        if not profile:
            return {
                "has_profile": False,
                "recommendations": [],
                "message": "학습된 프로파일이 없습니다."
            }

        recommendations = []

        # 브랜드 추천
        spec_key = f"{breaker_spec.get('pole', '')}_{breaker_spec.get('frame', '')}"
        if spec_key in profile.brand_preferences:
            recommendations.append({
                "type": "BRAND",
                "recommendation": profile.brand_preferences[spec_key],
                "reason": f"CEO가 {spec_key} 사양에서 선호하는 브랜드입니다.",
                "confidence": self._get_preference_confidence(profile, "BRAND", f"preferred_brand_{spec_key}")
            })

        # 가격 조정 추천
        if profile.price_thresholds:
            avg_discount = profile.price_thresholds.get("discount_avg", 0)
            if avg_discount > 0:
                recommendations.append({
                    "type": "PRICE",
                    "recommendation": f"{round(avg_discount * 100, 1)}% 할인",
                    "reason": "CEO의 평균 할인율입니다.",
                    "confidence": self._get_preference_confidence(profile, "PRICE", "discount_max")
                })

        # 레이아웃 추천
        if profile.layout_style:
            recommendations.append({
                "type": "LAYOUT",
                "recommendation": profile.layout_style,
                "reason": "CEO가 선호하는 레이아웃 스타일입니다.",
                "confidence": self._get_preference_confidence(profile, "LAYOUT", "preferred_style")
            })

        return {
            "has_profile": True,
            "user_id": user_id,
            "recommendations": recommendations,
            "sample_size": profile.sample_size,
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else None
        }

    def _get_preference_confidence(
        self,
        profile: CEOProfile,
        category: PreferenceCategory,
        key: str
    ) -> float:
        """선호도 신뢰도 조회"""
        for pref in profile.preferences:
            if pref.category == category and pref.key == key:
                return pref.confidence
        return 0.0

    async def delete_profile(self, user_id: str) -> bool:
        """프로파일 삭제"""
        if user_id in self._profiles:
            del self._profiles[user_id]
            self._save_index()
            logger.info(f"프로파일 삭제: {user_id}")
            return True
        return False

    def get_stats(self) -> dict:
        """프로파일 통계"""
        if not self._profiles:
            return {
                "total_profiles": 0,
                "total_preferences": 0,
                "avg_sample_size": 0,
                "latest_update": None
            }

        total_preferences = sum(len(p.preferences) for p in self._profiles.values())
        total_samples = sum(p.sample_size for p in self._profiles.values())

        latest = max(
            [p for p in self._profiles.values() if p.last_updated],
            key=lambda x: x.last_updated,
            default=None
        )

        return {
            "total_profiles": len(self._profiles),
            "total_preferences": total_preferences,
            "avg_sample_size": round(total_samples / len(self._profiles), 1) if self._profiles else 0,
            "latest_update": latest.last_updated.isoformat() if latest and latest.last_updated else None
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_ceo_profile_service: Optional[CEOProfileService] = None


def get_ceo_profile_service() -> CEOProfileService:
    """CEO 프로파일 서비스 싱글톤 인스턴스 반환"""
    global _ceo_profile_service
    if _ceo_profile_service is None:
        _ceo_profile_service = CEOProfileService()
    return _ceo_profile_service
