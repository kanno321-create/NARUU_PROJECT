"""
evidence/packer.py 실제 호출 테스트 (P4-2 Phase I-4)

목적: Evidence Pack 생성 시스템 coverage 측정 (0% → 70%)
원칙: Zero-Mock (실제 파일 I/O, ZIP 생성), SSOT 정책 사용
"""

import pytest
from pathlib import Path
import hashlib
import zipfile
import json

from kis_estimator_core.evidence.packer import EvidencePacker


# ============================================================
# Fixture: Temporary Evidence Files
# ============================================================
@pytest.fixture
def temp_evidence_files(tmp_path):
    """임시 증거 파일 생성"""
    # Contract files
    contract_dir = tmp_path / "contract"
    contract_dir.mkdir()
    contract_file = contract_dir / "openapi_v1.0.0.json"
    contract_file.write_text(json.dumps({"openapi": "3.1.0"}), encoding='utf-8')

    # Pipeline logs
    pipeline_dir = tmp_path / "pipeline"
    pipeline_dir.mkdir()
    pipeline_log = pipeline_dir / "pipeline_events.jsonl"
    pipeline_log.write_text('{"event": "stage1_start"}\n{"event": "stage1_end"}\n', encoding='utf-8')

    # Artifacts
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    artifact_xlsx = artifacts_dir / "estimate.xlsx"
    artifact_xlsx.write_text("fake xlsx content", encoding='utf-8')
    artifact_pdf = artifacts_dir / "estimate.pd"
    artifact_pdf.write_text("fake pdf content", encoding='utf-8')

    return {
        "contract_files": [contract_file],
        "pipeline_logs": [pipeline_log],
        "artifacts": [artifact_xlsx, artifact_pdf],
    }


@pytest.fixture
def packer(tmp_path):
    """EvidencePacker 인스턴스"""
    output_dir = tmp_path / "dist"
    return EvidencePacker(output_dir)


# ============================================================
# Test: EvidencePacker Initialization
# ============================================================
def test_evidence_packer_init_success(tmp_path):
    """EvidencePacker 초기화 성공"""
    output_dir = tmp_path / "dist"

    # 실제 호출
    packer = EvidencePacker(output_dir)

    # 검증
    assert packer.output_dir == output_dir
    assert output_dir.exists()  # mkdir with parents=True


def test_evidence_packer_init_default_dir():
    """EvidencePacker 기본 디렉토리 (dist)"""
    # 실제 호출
    packer = EvidencePacker()

    # 검증
    assert packer.output_dir == Path("dist")


# ============================================================
# Test: create_pack (Evidence Pack 생성)
# ============================================================
def test_create_pack_success(packer, temp_evidence_files):
    """Evidence Pack 생성 성공"""
    # 실제 호출
    result = packer.create_pack(
        contract_files=temp_evidence_files["contract_files"],
        pipeline_logs=temp_evidence_files["pipeline_logs"],
        artifacts=temp_evidence_files["artifacts"],
    )

    # 검증: 결과 딕셔너리
    assert "pack_path" in result
    assert "checksums_path" in result
    assert "file_count" in result
    assert "pack_size_bytes" in result

    # 검증: 파일 생성됨
    assert Path(result["pack_path"]).exists()
    assert Path(result["checksums_path"]).exists()
    assert Path(result["pack_path"]).name == "EvidencePack.zip"
    assert Path(result["checksums_path"]).name == "SHA256SUMS.txt"

    # 검증: 파일 개수
    assert result["file_count"] == 4  # 1 contract + 1 pipeline + 2 artifacts

    # 검증: Pack 크기 > 0
    assert result["pack_size_bytes"] > 0


def test_create_pack_zip_structure(packer, temp_evidence_files):
    """Evidence Pack ZIP 구조 검증"""
    # 실제 호출
    result = packer.create_pack(
        contract_files=temp_evidence_files["contract_files"],
        pipeline_logs=temp_evidence_files["pipeline_logs"],
        artifacts=temp_evidence_files["artifacts"],
    )

    pack_path = Path(result["pack_path"])

    # ZIP 내용 검증
    with zipfile.ZipFile(pack_path, 'r') as zf:
        namelist = zf.namelist()

        # 검증: contract/ 디렉토리
        assert any("contract/" in name for name in namelist)
        assert "contract/openapi_v1.0.0.json" in namelist

        # 검증: pipeline/ 디렉토리
        assert any("pipeline/" in name for name in namelist)
        assert "pipeline/pipeline_events.jsonl" in namelist

        # 검증: artifacts/ 디렉토리
        assert any("artifacts/" in name for name in namelist)
        assert "artifacts/estimate.xlsx" in namelist
        assert "artifacts/estimate.pd" in namelist


def test_create_pack_checksums_file(packer, temp_evidence_files):
    """SHA256SUMS.txt 파일 내용 검증"""
    # 실제 호출
    result = packer.create_pack(
        contract_files=temp_evidence_files["contract_files"],
        pipeline_logs=temp_evidence_files["pipeline_logs"],
        artifacts=temp_evidence_files["artifacts"],
    )

    checksums_path = Path(result["checksums_path"])

    # 파일 읽기
    with open(checksums_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 검증: SHA256 해시 포맷 (64자 hex + 공백 + 파일명)
    lines = content.strip().split('\n')
    assert len(lines) >= 1

    for line in lines:
        parts = line.split("  ", 1)
        assert len(parts) == 2
        checksum, filename = parts
        assert len(checksum) == 64  # SHA256 = 64 hex chars
        assert all(c in '0123456789abcdef' for c in checksum.lower())


def test_create_pack_with_nonexistent_files(packer, tmp_path):
    """존재하지 않는 파일 포함 시 (스킵됨)"""
    # 존재하지 않는 파일 경로
    nonexistent_file = tmp_path / "nonexistent.json"

    # 실제 호출
    result = packer.create_pack(
        contract_files=[nonexistent_file],
        pipeline_logs=[],
        artifacts=[],
    )

    # 검증: Pack은 생성되지만 파일은 ZIP에 추가되지 않음
    # Note: file_count는 입력 리스트 길이를 반환 (실제 추가된 파일 수 아님)
    assert Path(result["pack_path"]).exists()
    assert result["file_count"] == 1  # Input list length, not actual files in ZIP


# ============================================================
# Test: _generate_checksums (SHA256 생성)
# ============================================================
def test_generate_checksums_success(packer, temp_evidence_files):
    """SHA256 체크섬 생성"""
    files = temp_evidence_files["contract_files"] + temp_evidence_files["pipeline_logs"]

    # 실제 호출
    checksums = packer._generate_checksums(files)

    # 검증: 딕셔너리 반환
    assert isinstance(checksums, dict)
    assert len(checksums) == 2  # 2 files

    # 검증: 모든 해시가 64자 hex
    for filename, checksum in checksums.items():
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum.lower())


def test_generate_checksums_empty_list(packer):
    """빈 파일 리스트 (빈 딕셔너리 반환)"""
    # 실제 호출
    checksums = packer._generate_checksums([])

    # 검증: 빈 딕셔너리
    assert checksums == {}


# ============================================================
# Test: _sha256 (SHA256 해시 계산)
# ============================================================
def test_sha256_calculation(packer, tmp_path):
    """SHA256 해시 계산 정확성"""
    # 테스트 파일 생성
    test_file = tmp_path / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)

    # 예상 SHA256 계산
    expected_hash = hashlib.sha256(test_content).hexdigest()

    # 실제 호출
    actual_hash = packer._sha256(test_file)

    # 검증: 일치
    assert actual_hash == expected_hash


def test_sha256_large_file(packer, tmp_path):
    """큰 파일 SHA256 계산 (청크 단위 처리)"""
    # 큰 파일 생성 (8KB)
    test_file = tmp_path / "large.bin"
    test_content = b"A" * 8192
    test_file.write_bytes(test_content)

    # 예상 SHA256
    expected_hash = hashlib.sha256(test_content).hexdigest()

    # 실제 호출
    actual_hash = packer._sha256(test_file)

    # 검증: 일치 (청크 읽기가 정상 동작)
    assert actual_hash == expected_hash


# ============================================================
# Test: verify_pack (Evidence Pack 검증)
# ============================================================
def test_verify_pack_success(packer, temp_evidence_files):
    """Evidence Pack 검증 성공"""
    # Pack 생성
    result = packer.create_pack(
        contract_files=temp_evidence_files["contract_files"],
        pipeline_logs=temp_evidence_files["pipeline_logs"],
        artifacts=temp_evidence_files["artifacts"],
    )

    pack_path = result["pack_path"]
    checksums_path = result["checksums_path"]

    # 실제 호출: 검증
    is_valid = packer.verify_pack(Path(pack_path), Path(checksums_path))

    # 검증: True (무결성 확인)
    assert is_valid is True


def test_verify_pack_missing_pack_file(packer, tmp_path):
    """Pack 파일 없음 → False"""
    missing_pack = tmp_path / "missing.zip"
    checksums_path = tmp_path / "SHA256SUMS.txt"
    checksums_path.write_text("abc123  missing.zip\n")

    # 실제 호출
    is_valid = packer.verify_pack(missing_pack, checksums_path)

    # 검증: False
    assert is_valid is False


def test_verify_pack_missing_checksums_file(packer, tmp_path):
    """Checksums 파일 없음 → False"""
    pack_path = tmp_path / "EvidencePack.zip"
    pack_path.write_bytes(b"fake zip")
    missing_checksums = tmp_path / "missing.txt"

    # 실제 호출
    is_valid = packer.verify_pack(pack_path, missing_checksums)

    # 검증: False
    assert is_valid is False


def test_verify_pack_corrupted_pack(packer, temp_evidence_files):
    """Pack 파일 손상 (해시 불일치) → False"""
    # Pack 생성
    result = packer.create_pack(
        contract_files=temp_evidence_files["contract_files"],
        pipeline_logs=temp_evidence_files["pipeline_logs"],
        artifacts=temp_evidence_files["artifacts"],
    )

    pack_path = result["pack_path"]
    checksums_path = result["checksums_path"]

    # Pack 파일 변조 (1바이트 추가)
    with open(pack_path, 'ab') as f:
        f.write(b"X")

    # 실제 호출
    is_valid = packer.verify_pack(Path(pack_path), Path(checksums_path))

    # 검증: False (해시 불일치)
    assert is_valid is False
