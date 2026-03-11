"""
견적 수정 감사 서비스 (Phase XIII)

CEO가 견적을 수정할 때마다 before/after diff를 저장하고 분석합니다.
Zero-Mock 원칙: 모든 데이터는 실제로 저장됩니다.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class EstimateModification:
    """견적 수정 레코드"""
    modification_id: str
    estimate_id: str
    user_id: str  # CEO ID
    before_snapshot: dict  # 수정 전 전체 데이터
    after_snapshot: dict   # 수정 후 전체 데이터
    diff: dict            # JSON Patch 형식 diff
    modified_fields: list[str]  # ["price", "brand", "layout"]
    reason: Optional[str]    # 수정 사유 (선택)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence_hash: str = ""  # SHA256

    def __post_init__(self):
        if not self.evidence_hash:
            self.evidence_hash = self._generate_hash()

    def _generate_hash(self) -> str:
        """무결성 해시 생성"""
        data = {
            "estimate_id": self.estimate_id,
            "before": self.before_snapshot,
            "after": self.after_snapshot,
            "timestamp": self.timestamp.isoformat()
        }
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()


# ============================================================================
# Modification Audit Service
# ============================================================================

class ModificationAuditService:
    """
    견적 수정 감사 서비스

    Features:
    - Before/After 스냅샷 저장
    - JSON Patch diff 생성
    - SHA256 무결성 해시
    - 수정 필드 자동 감지
    - 패턴 분석용 데이터 제공
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: 파일 저장 경로 (None이면 기본 경로 사용)
        """
        if storage_path is None:
            self.storage_path = Path(__file__).parent.parent.parent.parent / "data" / "ai_memory" / "modifications"
        else:
            self.storage_path = storage_path

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._modifications: list[EstimateModification] = []
        self._load_existing()

    def _load_existing(self) -> None:
        """기존 수정 이력 로드"""
        try:
            index_file = self.storage_path / "index.json"
            if index_file.exists():
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("modifications", []):
                        self._modifications.append(EstimateModification(
                            modification_id=item["modification_id"],
                            estimate_id=item["estimate_id"],
                            user_id=item["user_id"],
                            before_snapshot=item["before_snapshot"],
                            after_snapshot=item["after_snapshot"],
                            diff=item["diff"],
                            modified_fields=item["modified_fields"],
                            reason=item.get("reason"),
                            timestamp=datetime.fromisoformat(item["timestamp"]),
                            evidence_hash=item["evidence_hash"]
                        ))
                logger.info(f"로드된 수정 이력: {len(self._modifications)}개")
        except Exception as e:
            logger.warning(f"수정 이력 로드 실패: {e}")

    def _save_index(self) -> None:
        """인덱스 파일 저장"""
        index_file = self.storage_path / "index.json"
        data = {
            "modifications": [
                {
                    "modification_id": m.modification_id,
                    "estimate_id": m.estimate_id,
                    "user_id": m.user_id,
                    "before_snapshot": m.before_snapshot,
                    "after_snapshot": m.after_snapshot,
                    "diff": m.diff,
                    "modified_fields": m.modified_fields,
                    "reason": m.reason,
                    "timestamp": m.timestamp.isoformat(),
                    "evidence_hash": m.evidence_hash
                }
                for m in self._modifications
            ],
            "total": len(self._modifications),
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def capture_modification(
        self,
        estimate_id: str,
        before: dict,
        after: dict,
        user_id: str,
        reason: Optional[str] = None
    ) -> EstimateModification:
        """
        견적 수정 캡처

        Args:
            estimate_id: 견적 ID
            before: 수정 전 데이터
            after: 수정 후 데이터
            user_id: 수정자 ID (CEO)
            reason: 수정 사유 (선택)

        Returns:
            저장된 EstimateModification
        """
        # Diff 분석
        diff_result = await self.analyze_diff(before, after)

        modification = EstimateModification(
            modification_id=str(uuid.uuid4()),
            estimate_id=estimate_id,
            user_id=user_id,
            before_snapshot=before,
            after_snapshot=after,
            diff=diff_result["diff"],
            modified_fields=diff_result["modified_fields"],
            reason=reason,
            timestamp=datetime.utcnow()
        )

        self._modifications.append(modification)
        self._save_index()

        # Evidence 파일 저장
        await self._save_evidence(modification)

        logger.info(
            f"견적 수정 캡처 완료: {estimate_id} by {user_id}, "
            f"변경 필드: {modification.modified_fields}"
        )

        return modification

    async def _save_evidence(self, modification: EstimateModification) -> None:
        """Evidence 파일 저장"""
        evidence_dir = self.storage_path / "evidence" / modification.modification_id[:8]
        evidence_dir.mkdir(parents=True, exist_ok=True)

        # 전체 데이터 저장
        evidence_file = evidence_dir / f"{modification.modification_id}.json"
        with open(evidence_file, "w", encoding="utf-8") as f:
            json.dump({
                "modification_id": modification.modification_id,
                "estimate_id": modification.estimate_id,
                "user_id": modification.user_id,
                "before_snapshot": modification.before_snapshot,
                "after_snapshot": modification.after_snapshot,
                "diff": modification.diff,
                "modified_fields": modification.modified_fields,
                "reason": modification.reason,
                "timestamp": modification.timestamp.isoformat(),
                "evidence_hash": modification.evidence_hash
            }, f, ensure_ascii=False, indent=2)

    async def analyze_diff(
        self,
        before: dict,
        after: dict
    ) -> dict:
        """
        Before/After diff 분석

        Returns:
            {
                "diff": {...},  # JSON Patch 형식
                "modified_fields": [...],  # 변경된 필드 목록
                "price_changes": [...],  # 가격 변경 상세
                "brand_changes": [...],  # 브랜드 변경 상세
                "layout_changes": [...]  # 레이아웃 변경 상세
            }
        """
        modified_fields = []
        price_changes = []
        brand_changes = []
        layout_changes = []
        diff = {}

        # 최상위 필드 비교
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)

            if before_val != after_val:
                modified_fields.append(key)
                diff[key] = {
                    "before": before_val,
                    "after": after_val
                }

        # 패널별 상세 분석
        before_panels = before.get("panels", [])
        after_panels = after.get("panels", [])

        # 가격 변경 분석
        before_price = before.get("total_price", 0)
        after_price = after.get("total_price", 0)
        if before_price != after_price:
            price_changes.append({
                "field": "total_price",
                "before": before_price,
                "after": after_price,
                "change_rate": (after_price - before_price) / before_price if before_price else 0
            })

        # 브랜드 변경 분석
        for i, (bp, ap) in enumerate(zip(before_panels, after_panels)):
            # 메인 차단기 브랜드
            before_brand = bp.get("main_breaker", {}).get("brand")
            after_brand = ap.get("main_breaker", {}).get("brand")
            if before_brand != after_brand:
                brand_changes.append({
                    "panel_index": i,
                    "component": "main_breaker",
                    "before": before_brand,
                    "after": after_brand
                })

            # 분기 차단기 브랜드
            before_branches = bp.get("branch_breakers", [])
            after_branches = ap.get("branch_breakers", [])
            for j, (bb, ab) in enumerate(zip(before_branches, after_branches)):
                if bb.get("brand") != ab.get("brand"):
                    brand_changes.append({
                        "panel_index": i,
                        "component": f"branch_breaker_{j}",
                        "before": bb.get("brand"),
                        "after": ab.get("brand")
                    })

        # 레이아웃 변경 분석
        before_layout = before.get("layout", {})
        after_layout = after.get("layout", {})
        if before_layout != after_layout:
            layout_changes.append({
                "before": before_layout,
                "after": after_layout
            })

        return {
            "diff": diff,
            "modified_fields": modified_fields,
            "price_changes": price_changes,
            "brand_changes": brand_changes,
            "layout_changes": layout_changes
        }

    async def get_modifications(
        self,
        estimate_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> list[EstimateModification]:
        """
        수정 이력 조회

        Args:
            estimate_id: 특정 견적 ID로 필터링
            user_id: 특정 사용자 ID로 필터링
            limit: 최대 반환 개수

        Returns:
            수정 이력 목록 (최신순)
        """
        result = self._modifications.copy()

        if estimate_id:
            result = [m for m in result if m.estimate_id == estimate_id]

        if user_id:
            result = [m for m in result if m.user_id == user_id]

        # 최신순 정렬
        result.sort(key=lambda x: x.timestamp, reverse=True)

        return result[:limit]

    async def get_modification_by_id(
        self,
        modification_id: str
    ) -> Optional[EstimateModification]:
        """ID로 수정 이력 조회"""
        for m in self._modifications:
            if m.modification_id == modification_id:
                return m
        return None

    def get_stats(self) -> dict:
        """수정 이력 통계"""
        if not self._modifications:
            return {
                "total": 0,
                "by_user": {},
                "by_field": {},
                "latest": None
            }

        by_user: dict[str, int] = {}
        by_field: dict[str, int] = {}

        for m in self._modifications:
            by_user[m.user_id] = by_user.get(m.user_id, 0) + 1
            for field in m.modified_fields:
                by_field[field] = by_field.get(field, 0) + 1

        latest = max(self._modifications, key=lambda x: x.timestamp)

        return {
            "total": len(self._modifications),
            "by_user": by_user,
            "by_field": by_field,
            "latest": latest.timestamp.isoformat()
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_audit_service: Optional[ModificationAuditService] = None


def get_audit_service() -> ModificationAuditService:
    """감사 서비스 싱글톤 인스턴스 반환"""
    global _audit_service
    if _audit_service is None:
        _audit_service = ModificationAuditService()
    return _audit_service
