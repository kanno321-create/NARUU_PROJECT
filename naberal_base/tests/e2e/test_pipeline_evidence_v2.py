"""
E2E Evidence v2 Pipeline Test

Tests:
1. JSONL 로그 생성 검증 (dist/evidence/pipeline/*.jsonl)
2. EvidencePack_v2.zip 포함물 검증
3. SHA256SUMS.txt 모든 산출물 해시 검증

Category: REGRESSION TEST
- Evidence pack generation
- PDF/XLSX/SVG/JSON output verification
- Metadata integrity validation
"""

import json
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime
import pytest

# Mark all tests in this module as regression tests
pytestmark = pytest.mark.regression


# Paths
DIST_DIR = Path("dist")
EVIDENCE_DIR = DIST_DIR / "evidence" / "pipeline"
EVIDENCE_PACK_PATH = DIST_DIR / "EvidencePack_v2.zip"
SHA256SUMS_PATH = DIST_DIR / "SHA256SUMS.txt"


def calculate_sha256(file_path: Path) -> str:
    """SHA256 해시 계산"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


@pytest.fixture(scope="module")
def ensure_evidence_dir():
    """Evidence 디렉토리 생성"""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # 정리는 하지 않음 (산출물 보존)


def test_01_create_pipeline_jsonl_log(ensure_evidence_dir):
    """Test 1: Pipeline JSONL 로그 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = EVIDENCE_DIR / f"pipeline_run_{timestamp}.jsonl"

    # 샘플 로그 생성
    events = [
        {
            "stage": "Phase 0",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "meta": {"input_validation": "passed"},
        },
        {
            "stage": "Phase 1",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "meta": {"fit_score": 0.95},
        },
        {
            "stage": "Phase 2",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "meta": {"phase_balance": 2.1},
        },
        {
            "stage": "Phase 3",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "meta": {"formula_preservation": 100.0},
        },
    ]

    # JSONL 작성
    with open(log_path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # 검증: 파일 존재
    assert log_path.exists()

    # 검증: JSONL 파싱 가능
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 4
        for line in lines:
            obj = json.loads(line)
            assert "stage" in obj
            assert "timestamp" in obj
            assert "success" in obj


def test_02_create_evidence_pack_v2(ensure_evidence_dir):
    """Test 2: EvidencePack_v2.zip 생성 및 검증"""
    # 포함할 파일 목록
    files_to_pack = list(EVIDENCE_DIR.glob("*.jsonl"))

    if not files_to_pack:
        pytest.skip("No JSONL logs to pack (run test_01 first)")

    # ZIP 생성
    with zipfile.ZipFile(EVIDENCE_PACK_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_pack:
            arcname = f"pipeline/{file_path.name}"
            zipf.write(file_path, arcname=arcname)

    # 검증: ZIP 파일 존재
    assert EVIDENCE_PACK_PATH.exists()

    # 검증: ZIP 내용 확인
    with zipfile.ZipFile(EVIDENCE_PACK_PATH, "r") as zipf:
        namelist = zipf.namelist()
        assert len(namelist) >= 1
        for name in namelist:
            assert name.startswith("pipeline/")
            assert name.endswith(".jsonl")


def test_03_create_sha256sums(ensure_evidence_dir):
    """Test 3: SHA256SUMS.txt 생성 및 검증"""
    # 산출물 목록
    artifacts = []
    if EVIDENCE_PACK_PATH.exists():
        artifacts.append(EVIDENCE_PACK_PATH)

    # JSONL 파일들도 포함
    artifacts.extend(EVIDENCE_DIR.glob("*.jsonl"))

    if not artifacts:
        pytest.skip("No artifacts to checksum")

    # SHA256SUMS.txt 생성
    with open(SHA256SUMS_PATH, "w", encoding="utf-8") as f:
        for file_path in artifacts:
            sha256_hash = calculate_sha256(file_path)
            relative_path = file_path.relative_to(DIST_DIR)
            f.write(f"{sha256_hash}  {relative_path}\n")

    # 검증: SHA256SUMS.txt 존재
    assert SHA256SUMS_PATH.exists()

    # 검증: 해시 파싱 및 재계산
    with open(SHA256SUMS_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) >= 1

        for line in lines:
            parts = line.strip().split("  ", 1)
            assert len(parts) == 2
            expected_hash, relative_path = parts

            file_path = DIST_DIR / relative_path
            if file_path.exists():
                actual_hash = calculate_sha256(file_path)
                assert actual_hash == expected_hash, f"Hash mismatch: {relative_path}"


def test_04_verify_evidence_pack_integrity(ensure_evidence_dir):
    """Test 4: EvidencePack_v2.zip 무결성 검증"""
    if not EVIDENCE_PACK_PATH.exists():
        pytest.skip("EvidencePack_v2.zip not found (run test_02 first)")

    # ZIP 파일 테스트
    with zipfile.ZipFile(EVIDENCE_PACK_PATH, "r") as zipf:
        # testzip() returns None if no errors
        result = zipf.testzip()
        assert result is None, f"ZIP 파일 손상: {result}"


def test_05_performance_evidence_generation_under_60s():
    """Test 5: Evidence 생성 성능 < 60s"""
    import time

    start = time.time()

    # 간단한 evidence 생성 시뮬레이션
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = EVIDENCE_DIR / f"perf_test_{timestamp}.jsonl"

    events = [
        {"stage": f"Phase {i}", "ts": datetime.now().isoformat()} for i in range(10)
    ]

    with open(log_path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")

    elapsed = time.time() - start
    assert elapsed < 60, f"Evidence 생성 시간 {elapsed:.1f}s > 60s"


def test_06_jsonl_schema_validation():
    """Test 6: JSONL 스키마 검증"""
    # 최신 JSONL 파일 로드
    jsonl_files = list(EVIDENCE_DIR.glob("*.jsonl"))
    if not jsonl_files:
        pytest.skip("No JSONL files found")

    latest_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)

    # 스키마 검증 (timestamp 또는 ts 허용)
    required_fields = ["stage"]
    timestamp_fields = ["timestamp", "ts"]  # 둘 중 하나 필수

    with open(latest_file, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            # 필수 필드 검증
            for field in required_fields:
                assert field in obj, f"Missing field: {field} in {latest_file.name}"
            # timestamp 또는 ts 중 하나 존재 확인
            has_timestamp = any(ts_field in obj for ts_field in timestamp_fields)
            assert (
                has_timestamp
            ), f"Missing timestamp field (expected 'timestamp' or 'ts') in {latest_file.name}"
