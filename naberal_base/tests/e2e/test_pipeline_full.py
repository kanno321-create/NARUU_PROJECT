"""
End-to-End Pipeline Tests - Full H→B→Critic→Format→Cover→Lint→Evidence
Contract-First + Evidence-Gated + Zero-Mock

Tests complete pipeline with real data:
- Phase 0: Input Validation
- Phase 1: Enclosure (H)
- Phase 2: Breaker Placement (B)
- Phase 2.1: Critic
- Phase 3: Format (XLSX Generation)
- Phase 4: Cover (표지 생성)
- Phase 5: Doc Lint (최종 검증)
- Evidence: Pack + SHA256SUMS
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime

from kis_estimator_core.engine.workflow_engine import WorkflowEngine

# Skip E2E tests in CI environment (requires real template files)
SKIP_CI = pytest.mark.skipif(
    os.getenv("CI") == "true" or not Path("절대코어파일/견적서양식.xlsx").exists(),
    reason="E2E tests require real template files - skipping in CI"
)


# Fixture paths
FIXTURES_DIR = Path("tests/fixtures/requests")
MINIMAL_REQUEST = FIXTURES_DIR / "minimal.json"
STANDARD_REQUEST = FIXTURES_DIR / "standard.json"

# Output paths (fixed)
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
TEST_ARTIFACTS_DIR = DIST_DIR / "test_artifacts" / "e2e"


@pytest.fixture(scope="module", autouse=True)
def setup_directories():
    """Create required directories"""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    TEST_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    yield


@pytest.fixture
def minimal_request():
    """Load minimal request fixture"""
    with open(MINIMAL_REQUEST, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def standard_request():
    """Load standard request fixture"""
    with open(STANDARD_REQUEST, "r", encoding="utf-8") as f:
        return json.load(f)


@SKIP_CI
class TestE2EPipelineMinimal:
    """E2E Pipeline: Minimal scenario (3 breakers, no accessories)"""

    @pytest.mark.asyncio
    async def test_minimal_pipeline_full(self, minimal_request):
        """
        Minimal 시나리오 전체 파이프라인 실행

        단계:
        - Phase 0: Validation
        - Phase 1: Enclosure (H) → fit_score ≥ 0.90
        - Phase 2: Breaker (B) → 상평형 ≤ 4%
        - Phase 2.1: Critic → 위반 = 0
        - Phase 3: Format → Excel 생성
        - Phase 4: Cover → TODO (표지 생성)
        - Phase 5: Doc Lint → TODO (최종 검증)
        """
        # Extract request data
        panel = minimal_request["panels"][0]

        # Main/branch breakers 분리
        main_breaker = None
        branch_breakers = []

        for breaker in panel["breakers"]:
            breaker_dict = {
                "id": breaker["id"],
                "model": breaker["model"],
                "poles": breaker["poles"],
                "current": breaker["current_a"],
                "frame": breaker["frame_af"],
                "type": "ELB" if breaker["is_elb"] else "MCCB",
            }

            if breaker["is_main"]:
                main_breaker = breaker_dict
            else:
                branch_breakers.append(breaker_dict)

        assert main_breaker is not None, "Main breaker must exist"

        # WorkflowEngine 실행
        workflow = WorkflowEngine(
            catalog_path=Path("절대코어파일/핵심파일풀/중요ai단가표의_2.0V.csv"),
            template_path=Path("절대코어파일/견적서양식.xlsx"),
        )

        output_path = BUILD_DIR / "minimal_estimate.xlsx"

        result = await workflow.execute(
            enclosure_material="STEEL 1.6T",
            enclosure_type=minimal_request["enclosure_type"],
            breaker_brand="상도차단기",
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            accessories=[],
            output_path=output_path,
            customer_name=minimal_request["customer"]["name"],
            project_name=minimal_request["customer"]["project_name"],
        )

        # Assertions: Workflow success
        assert result.success, f"Workflow failed: {result.blocking_errors}"

        # Phase 1: Enclosure
        phase1 = next((p for p in result.phases if "Enclosure" in p.phase), None)
        assert phase1 is not None, "Phase 1 (Enclosure) not found"
        assert phase1.success, "Phase 1 failed"
        assert phase1.output.get("fit_score", 0) >= 0.90, "Enclosure fit_score < 0.90"

        # Phase 2: Breaker
        phase2 = next((p for p in result.phases if "Breaker" in p.phase), None)
        assert phase2 is not None, "Phase 2 (Breaker) not found"
        assert phase2.success, "Phase 2 failed"
        phase_balance = phase2.output.get("phase_balance", 100)
        assert phase_balance <= 4.0, f"Phase imbalance {phase_balance}% > 4%"

        # Branch Bus Rules v1.0 validation (4P N-phase)
        placements = phase2.output.get("placements", [])
        four_pole_placements = [p for p in placements if p.get("poles") == 4]
        if four_pole_placements:
            # Check n_bus_metadata exists for all 4P breakers
            for fp in four_pole_placements:
                assert "n_bus_metadata" in fp.get(
                    "position", {}
                ), f"4P breaker {fp.get('breaker_id')} missing n_bus_metadata"
            # Check no N-phase violations
            n_violations = phase2.output.get("n_phase_violations", 0)
            assert n_violations == 0, f"N-phase violations: {n_violations}"

        # Phase 3: Format (Excel)
        phase3 = next((p for p in result.phases if "Excel" in p.phase), None)
        assert phase3 is not None, "Phase 3 (Excel Generation) not found"
        assert phase3.success, "Phase 3 failed"

        # Output file exists
        assert result.final_output is not None, "Final output path is None"
        assert Path(
            result.final_output
        ).exists(), f"Output file not found: {result.final_output}"

        # Write event log
        log_path = (
            TEST_ARTIFACTS_DIR
            / f"run_minimal_{datetime.now().strftime('%Y%m%d%H%M%S')}.jsonl"
        )
        with open(log_path, "w", encoding="utf-8") as f:
            for phase in result.phases:
                event = {
                    "phase": phase.phase,
                    "success": phase.success,
                    "errors": [
                        e.error_code.code
                        for e in phase.errors
                        if hasattr(e, "error_code")
                    ],
                    "warnings": phase.warnings,
                }
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        print("\n[E2E] Minimal pipeline: SUCCESS")
        print(f"[OUTPUT] {result.final_output}")
        print(f"[LOG] {log_path}")


@SKIP_CI
class TestE2EPipelineStandard:
    """E2E Pipeline: Standard scenario (5 breakers, 1 magnet)"""

    @pytest.mark.asyncio
    async def test_standard_pipeline_full(self, standard_request):
        """
        Standard 시나리오 전체 파이프라인 실행

        단계:
        - Phase 0: Validation
        - Phase 1: Enclosure (H) → fit_score ≥ 0.90
        - Phase 2: Breaker (B) → 상평형 ≤ 4%
        - Phase 2.1: Critic → 위반 = 0
        - Phase 3: Format → Excel 생성
        - Phase 4: Cover → TODO (표지 생성)
        - Phase 5: Doc Lint → TODO (최종 검증)
        """
        # Extract request data
        panel = standard_request["panels"][0]

        # Main/branch breakers 분리
        main_breaker = None
        branch_breakers = []

        for breaker in panel["breakers"]:
            breaker_dict = {
                "id": breaker["id"],
                "model": breaker["model"],
                "poles": breaker["poles"],
                "current": breaker["current_a"],
                "frame": breaker["frame_af"],
                "type": "ELB" if breaker["is_elb"] else "MCCB",
            }

            if breaker["is_main"]:
                main_breaker = breaker_dict
            else:
                branch_breakers.append(breaker_dict)

        assert main_breaker is not None, "Main breaker must exist"

        # Accessories 변환
        accessories = [
            {
                "name": acc["type"].upper(),
                "spec": acc["model"],
                "quantity": acc["quantity"],
            }
            for acc in panel["accessories"]
        ]

        # WorkflowEngine 실행
        workflow = WorkflowEngine(
            catalog_path=Path("절대코어파일/핵심파일풀/중요ai단가표의_2.0V.csv"),
            template_path=Path("절대코어파일/견적서양식.xlsx"),
        )

        output_path = BUILD_DIR / "standard_estimate.xlsx"

        result = await workflow.execute(
            enclosure_material="SUS201 1.2T",
            enclosure_type=standard_request["enclosure_type"],
            breaker_brand="상도차단기",
            main_breaker=main_breaker,
            branch_breakers=branch_breakers,
            accessories=accessories,
            output_path=output_path,
            customer_name=standard_request["customer"]["name"],
            project_name=standard_request["customer"]["project_name"],
        )

        # Assertions: Workflow success
        assert result.success, f"Workflow failed: {result.blocking_errors}"

        # Phase 1: Enclosure
        phase1 = next((p for p in result.phases if "Enclosure" in p.phase), None)
        assert phase1 is not None, "Phase 1 (Enclosure) not found"
        assert phase1.success, "Phase 1 failed"
        assert phase1.output.get("fit_score", 0) >= 0.90, "Enclosure fit_score < 0.90"

        # Phase 2: Breaker
        phase2 = next((p for p in result.phases if "Breaker" in p.phase), None)
        assert phase2 is not None, "Phase 2 (Breaker) not found"
        assert phase2.success, "Phase 2 failed"
        phase_balance = phase2.output.get("phase_balance", 100)
        assert phase_balance <= 4.0, f"Phase imbalance {phase_balance}% > 4%"

        # Branch Bus Rules v1.0 validation (4P N-phase)
        placements = phase2.output.get("placements", [])
        four_pole_placements = [p for p in placements if p.get("poles") == 4]
        if four_pole_placements:
            # Check n_bus_metadata exists for all 4P breakers
            for fp in four_pole_placements:
                assert "n_bus_metadata" in fp.get(
                    "position", {}
                ), f"4P breaker {fp.get('breaker_id')} missing n_bus_metadata"
            # Check no N-phase violations
            n_violations = phase2.output.get("n_phase_violations", 0)
            assert n_violations == 0, f"N-phase violations: {n_violations}"

        # Phase 3: Format (Excel)
        phase3 = next((p for p in result.phases if "Excel" in p.phase), None)
        assert phase3 is not None, "Phase 3 (Excel Generation) not found"
        assert phase3.success, "Phase 3 failed"

        # Output file exists
        assert result.final_output is not None, "Final output path is None"
        assert Path(
            result.final_output
        ).exists(), f"Output file not found: {result.final_output}"

        # Write event log
        log_path = (
            TEST_ARTIFACTS_DIR
            / f"run_standard_{datetime.now().strftime('%Y%m%d%H%M%S')}.jsonl"
        )
        with open(log_path, "w", encoding="utf-8") as f:
            for phase in result.phases:
                event = {
                    "phase": phase.phase,
                    "success": phase.success,
                    "errors": [
                        e.error_code.code
                        for e in phase.errors
                        if hasattr(e, "error_code")
                    ],
                    "warnings": phase.warnings,
                }
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        print("\n[E2E] Standard pipeline: SUCCESS")
        print(f"[OUTPUT] {result.final_output}")
        print(f"[LOG] {log_path}")


# Evidence artifact generation
@SKIP_CI
def test_e2e_pipeline_evidence():
    """E2E pipeline 증거 생성 - EvidencePack.zip + SHA256SUMS.txt"""
    from kis_estimator_core.evidence import EvidencePacker

    # Collect artifacts
    contract_files = []  # TODO: Add contract files when available

    pipeline_logs = list(TEST_ARTIFACTS_DIR.glob("run_*.jsonl"))

    artifacts = [
        BUILD_DIR / "minimal_estimate.xlsx",
        BUILD_DIR / "standard_estimate.xlsx",
    ]
    # Filter existing files only
    artifacts = [f for f in artifacts if f.exists()]

    # Create evidence pack
    packer = EvidencePacker(output_dir=DIST_DIR)
    result = packer.create_pack(
        contract_files=contract_files,
        pipeline_logs=pipeline_logs,
        artifacts=artifacts,
    )

    # Assertions
    pack_path = result["pack_path"]
    checksums_path = result["checksums_path"]

    assert pack_path.exists(), f"EvidencePack.zip not created: {pack_path}"
    assert checksums_path.exists(), f"SHA256SUMS.txt not created: {checksums_path}"
    assert result["file_count"] >= 2, "Not enough files in evidence pack"
    assert result["pack_size_bytes"] > 0, "EvidencePack is empty"

    # Verify integrity
    is_valid = packer.verify_pack(pack_path, checksums_path)
    assert is_valid, "EvidencePack integrity verification failed"

    print(f"\n[OK] EvidencePack created: {pack_path}")
    print(f"[OK] SHA256SUMS created: {checksums_path}")
    print(f"[OK] Files packed: {result['file_count']}")
    print(f"[OK] Pack size: {result['pack_size_bytes']:,} bytes")
    print("[OK] Integrity verified: ✅")
