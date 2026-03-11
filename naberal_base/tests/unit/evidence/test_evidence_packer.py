"""
Unit tests for evidence/packer.py - Evidence Pack Generator

Target: 85% coverage for packer.py (56 lines)
Principles:
- Zero-Mock: Real file I/O with tempfile
- Real ZIP creation and SHA256 hashing
- Complete round-trip integrity testing

Test Count: 8 tests
"""

import pytest
import tempfile
import zipfile
from pathlib import Path

from kis_estimator_core.evidence.packer import EvidencePacker


# ============================================================================
# Test 1-3: create_pack with Real Files
# ============================================================================


@pytest.mark.unit
def test_evidence_packer_create_pack_basic():
    """Test 1: create_pack with basic files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files
        contract_file = tmppath / "openapi.json"
        contract_file.write_text('{"version": "1.0"}')

        pipeline_log = tmppath / "pipeline.jsonl"
        pipeline_log.write_text('{"stage": "1", "status": "ok"}\n')

        artifact_file = tmppath / "estimate.xlsx"
        artifact_file.write_bytes(b"FAKE_XLSX_CONTENT")

        # Create packer
        output_dir = tmppath / "output"
        packer = EvidencePacker(output_dir=output_dir)

        # Create pack
        result = packer.create_pack(
            contract_files=[contract_file],
            pipeline_logs=[pipeline_log],
            artifacts=[artifact_file],
        )

        # Verify result
        assert "pack_path" in result
        assert "checksums_path" in result
        assert "file_count" in result
        assert "pack_size_bytes" in result

        assert result["pack_path"].exists()
        assert result["checksums_path"].exists()
        assert result["file_count"] == 3
        assert result["pack_size_bytes"] > 0


@pytest.mark.unit
def test_evidence_packer_zip_structure():
    """Test 2: Verify ZIP internal structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files
        contract_file = tmppath / "contract.json"
        contract_file.write_text('{"test": "data"}')

        pipeline_log = tmppath / "log.jsonl"
        pipeline_log.write_text('{"event": "start"}\n')

        artifact_file = tmppath / "result.pd"
        artifact_file.write_bytes(b"PDF_CONTENT")

        # Create pack
        output_dir = tmppath / "output"
        packer = EvidencePacker(output_dir=output_dir)
        result = packer.create_pack(
            contract_files=[contract_file],
            pipeline_logs=[pipeline_log],
            artifacts=[artifact_file],
        )

        # Verify ZIP contents
        pack_path = result["pack_path"]
        with zipfile.ZipFile(pack_path, "r") as zf:
            namelist = zf.namelist()

            # Verify directory structure
            assert "contract/contract.json" in namelist
            assert "pipeline/log.jsonl" in namelist
            assert "artifacts/result.pd" in namelist

            # Verify file contents
            contract_content = zf.read("contract/contract.json")
            assert contract_content == b'{"test": "data"}'


@pytest.mark.unit
def test_evidence_packer_checksums_file():
    """Test 3: Verify SHA256SUMS.txt format"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test file
        test_file = tmppath / "test.txt"
        test_file.write_text("Hello Evidence Pack")

        # Create pack
        output_dir = tmppath / "output"
        packer = EvidencePacker(output_dir=output_dir)
        result = packer.create_pack(
            contract_files=[test_file],
            pipeline_logs=[],
            artifacts=[],
        )

        # Read checksums file
        checksums_path = result["checksums_path"]
        checksums_content = checksums_path.read_text()

        # Verify format: <checksum>  <filename>
        lines = checksums_content.strip().split("\n")
        assert len(lines) >= 1

        for line in lines:
            parts = line.split("  ", 1)
            assert len(parts) == 2
            checksum, filename = parts
            # SHA256 checksum is 64 hex characters
            assert len(checksum) == 64
            assert all(c in "0123456789abcdef" for c in checksum)


# ============================================================================
# Test 4-5: SHA256 Checksum Generation
# ============================================================================


@pytest.mark.unit
def test_sha256_calculation():
    """Test 4: _sha256() calculates correct SHA256 hash"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test file with known content
        test_file = tmppath / "test.txt"
        test_file.write_text("test content")

        # Calculate SHA256
        packer = EvidencePacker()
        checksum = packer._sha256(test_file)

        # Verify checksum format
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

        # Verify deterministic (same input → same output)
        checksum2 = packer._sha256(test_file)
        assert checksum == checksum2


@pytest.mark.unit
def test_sha256_different_files():
    """Test 5: Different files produce different checksums"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create two different files
        file1 = tmppath / "file1.txt"
        file1.write_text("content 1")

        file2 = tmppath / "file2.txt"
        file2.write_text("content 2")

        # Calculate checksums
        packer = EvidencePacker()
        checksum1 = packer._sha256(file1)
        checksum2 = packer._sha256(file2)

        # Different files → different checksums
        assert checksum1 != checksum2


# ============================================================================
# Test 6-7: verify_pack Integrity Check
# ============================================================================


@pytest.mark.unit
def test_verify_pack_success():
    """Test 6: verify_pack() validates pack integrity"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test file
        test_file = tmppath / "data.json"
        test_file.write_text('{"key": "value"}')

        # Create pack
        output_dir = tmppath / "output"
        packer = EvidencePacker(output_dir=output_dir)
        result = packer.create_pack(
            contract_files=[test_file],
            pipeline_logs=[],
            artifacts=[],
        )

        # Verify pack
        pack_path = result["pack_path"]
        checksums_path = result["checksums_path"]

        is_valid = packer.verify_pack(pack_path, checksums_path)
        assert is_valid is True


@pytest.mark.unit
def test_verify_pack_missing_files():
    """Test 7: verify_pack() fails if files missing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        packer = EvidencePacker()

        # Non-existent files
        fake_pack = tmppath / "nonexistent.zip"
        fake_checksums = tmppath / "nonexistent_checksums.txt"

        is_valid = packer.verify_pack(fake_pack, fake_checksums)
        assert is_valid is False


# ============================================================================
# Test 8: Error Handling - Missing Files
# ============================================================================


@pytest.mark.unit
def test_create_pack_skips_missing_files():
    """Test 8: create_pack() skips non-existent files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create one real file
        real_file = tmppath / "real.txt"
        real_file.write_text("real content")

        # Reference non-existent files
        fake_file1 = tmppath / "nonexistent1.txt"
        fake_file2 = tmppath / "nonexistent2.txt"

        # Create pack (should skip missing files)
        output_dir = tmppath / "output"
        packer = EvidencePacker(output_dir=output_dir)
        result = packer.create_pack(
            contract_files=[real_file, fake_file1],
            pipeline_logs=[fake_file2],
            artifacts=[],
        )

        # Should only include real file
        pack_path = result["pack_path"]
        with zipfile.ZipFile(pack_path, "r") as zf:
            namelist = zf.namelist()
            assert len(namelist) == 1  # Only real_file
            assert "contract/real.txt" in namelist
