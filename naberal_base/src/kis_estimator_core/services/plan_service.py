"""
PlanService - VerbSpec Generation Service (I-3.4)

책임: PlanRequest → VerbSpec 리스트 변환
LLM 제거: Deterministic VerbSpec 생성
SSOT 준수: params.json, generated_verbs.py
"""

import logging
from typing import Any

from pydantic import ValidationError

from ..core.ssot.generated_verbs import PickenclosureParams, PlaceParams, VerbSpecModel

logger = logging.getLogger(__name__)


class PlanService:
    """VerbSpec Plan Generation Service"""

    @staticmethod
    def _parse_enclosure_material(enclosure_material: str) -> tuple[str, str]:
        """
        'STEEL 1.6T' → ('STEEL', '1.6T')
        'SUS304 1.2T' → ('SUS304', '1.2T')
        """
        parts = enclosure_material.strip().rsplit(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return "STEEL", "1.6T"

    @staticmethod
    def create_verb_specs(
        customer_name: str,
        project_name: str,
        enclosure_type: str,
        breaker_brand: str,
        main_breaker: dict[str, Any],
        branch_breakers: list[dict[str, Any]],
        accessories: list[dict[str, Any]],
        enclosure_material: str = "STEEL 1.6T",
        breaker_grade: str = "경제형",
    ) -> list[dict[str, Any]]:
        """
        Generate VerbSpec list from user requirements

        Deterministic transformation (no LLM):
        1. PICK_ENCLOSURE Verb (외함 선택)
        2. PLACE Verb (브레이커 배치)

        Args:
            customer_name: 고객사명
            project_name: 프로젝트명
            enclosure_type: 외함 종류
            breaker_brand: 차단기 브랜드
            main_breaker: 메인 차단기 스펙
            branch_breakers: 분기 차단기 목록
            accessories: 부속자재 목록
            enclosure_material: 외함 재질+두께 (예: 'STEEL 1.6T', 'SUS304 1.2T')
            breaker_grade: 차단기 등급 (경제형/표준형)

        Returns:
            VerbSpec list (validated)

        Raises:
            ValidationError: VerbSpec validation failed
        """
        specs = []

        # 재질/두께 파싱
        material, thickness = PlanService._parse_enclosure_material(enclosure_material)

        # 1. PICK_ENCLOSURE VerbSpec
        pick_spec = {
            "verb_name": "PICK_ENCLOSURE",
            "params": {
                "main_breaker": main_breaker,
                "branch_breakers": branch_breakers,
                "enclosure_type": enclosure_type,
                "material": material,
                "thickness": thickness,
                "accessories": accessories,
                "panel": "default",
                "strategy": "auto",
            },
            "version": "1.0.0",
        }

        # Validate PICK_ENCLOSURE
        try:
            VerbSpecModel(**pick_spec)
            PickenclosureParams(**pick_spec["params"])
        except ValidationError as e:
            logger.error(f"PICK_ENCLOSURE validation failed: {e}")
            raise

        specs.append(pick_spec)

        # 2. PLACE VerbSpec
        # Generate breaker IDs: MAIN + BR1, BR2, ...
        breaker_ids = ["MAIN"]
        for i in range(len(branch_breakers)):
            breaker_ids.append(f"BR{i+1}")

        place_spec = {
            "verb_name": "PLACE",
            "params": {
                "breakers": breaker_ids,
                "panel": "default",
                "strategy": "compact",
                "algo": "heuristic",
                "seed": 42,
            },
            "version": "1.0.0",
        }

        # Validate PLACE
        try:
            VerbSpecModel(**place_spec)
            PlaceParams(**place_spec["params"])
        except ValidationError as e:
            logger.error(f"PLACE validation failed: {e}")
            raise

        specs.append(place_spec)

        logger.info(
            f"VerbSpecs created: {len(specs)} specs "
            f"(customer={customer_name}, project={project_name})"
        )

        return specs

    @staticmethod
    def validate_verb_specs(specs: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        """
        Validate VerbSpec list

        Args:
            specs: VerbSpec list

        Returns:
            (is_valid, errors)
        """
        errors = []

        if not specs:
            errors.append("Empty VerbSpec list")
            return False, errors

        for i, spec in enumerate(specs):
            try:
                # VerbSpecModel validation
                VerbSpecModel(**spec)
            except ValidationError as e:
                errors.append(f"Spec[{i}] validation failed: {e}")

        is_valid = len(errors) == 0
        return is_valid, errors
