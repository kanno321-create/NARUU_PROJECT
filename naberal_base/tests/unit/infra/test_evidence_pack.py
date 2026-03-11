"""
P2: infra/evidence.py Coverage Tests (0% → ≥60%)
ULTRATHINK | Zero-Mock | SSOT | LAW-01..06

Target:
- EvidenceCollector: record_knowledge_file, record_db_query, record_quality_gate
- Hash calculation: SHA256
- Save/Load round-trip
- Error paths: permission, invalid data

DoD: ≥60% coverage, 6+ test cases PASS
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from kis_estimator_core.infra.evidence import (
    EvidenceCollector,
    Evidence,
    load_evidence,
)


@pytest.mark.unit
def test_evidence_collector_basic_creation():
    """Test 1: Basic collector creation and ID generation"""
    collector = EvidenceCollector("test_stage")

    assert collector.stage_name == "test_stage"
    assert collector.execution_id.startswith("test_stage_")
    assert collector.started_at is not None
    assert isinstance(collector.started_at, datetime)
    assert len(collector.knowledge_files) == 0
    assert len(collector.database_queries) == 0
    assert len(collector.quality_gates) == 0


@pytest.mark.unit
def test_evidence_collector_custom_execution_id():
    """Test 2: Custom execution ID"""
    custom_id = "CUSTOM_EXEC_20250101_120000"
    collector = EvidenceCollector("test_stage", execution_id=custom_id)

    assert collector.execution_id == custom_id


@pytest.mark.unit
def test_evidence_collector_knowledge_file_recording():
    """Test 3: Record knowledge file access with SHA256 hash"""
    collector = EvidenceCollector("enclosure_solver")

    # Real data from SSOT catalog
    breakers_data = {
        "meta": {"version": "1.0.0", "source": "SSOT"},
        "catalog": ["SBE-102", "SBS-202", "SEE-104"],
        "selection_rules": {"경제형_우선": True, "frame_tolerance": 10},
    }

    collector.record_knowledge_file(
        "breakers.json", breakers_data, keys_accessed=["meta", "catalog"]
    )

    assert len(collector.knowledge_files) == 1
    kf = collector.knowledge_files[0]
    assert kf.filename == "breakers.json"
    assert kf.data_hash is not None
    assert len(kf.data_hash) == 64  # SHA256 = 64 hex chars
    assert kf.keys_accessed == ["meta", "catalog"]


@pytest.mark.unit
def test_evidence_collector_hash_consistency():
    """Test 4: Hash calculation consistency (same data → same hash)"""
    collector1 = EvidenceCollector("test_stage")
    collector2 = EvidenceCollector("test_stage")

    data = {"key": "value", "num": 42}

    collector1.record_knowledge_file("test.json", data)
    collector2.record_knowledge_file("test.json", data)

    hash1 = collector1.knowledge_files[0].data_hash
    hash2 = collector2.knowledge_files[0].data_hash

    assert hash1 == hash2


@pytest.mark.unit
def test_evidence_collector_db_query_recording():
    """Test 5: Record database query with duration"""
    collector = EvidenceCollector("catalog_loader")

    collector.record_db_query(
        table="catalog_items",
        query="SELECT * FROM catalog_items WHERE category = 'MCCB' LIMIT 100",
        row_count=122,
        duration_ms=45.2,
    )

    assert len(collector.database_queries) == 1
    query = collector.database_queries[0]
    assert query.table == "catalog_items"
    assert query.row_count == 122
    assert query.duration_ms == 45.2
    assert query.executed_at is not None


@pytest.mark.unit
def test_evidence_collector_quality_gate_recording():
    """Test 6: Record quality gate validations (PASS and FAIL)"""
    collector = EvidenceCollector("breaker_placer")

    # Gate 1: PASS
    collector.record_quality_gate(
        {
            "gate_name": "balance_tolerance",
            "passed": True,
            "actual_value": 3.2,
            "threshold": 4.0,
            "operator": "<=",
        }
    )

    # Gate 2: FAIL
    collector.record_quality_gate(
        {
            "gate_name": "interference_check",
            "passed": False,
            "actual_value": 2.0,
            "threshold": 0.0,
            "operator": "==",
        }
    )

    assert len(collector.quality_gates) == 2
    gate1, gate2 = collector.quality_gates

    assert gate1.passed is True
    assert gate1.actual_value == 3.2
    assert gate2.passed is False
    assert gate2.actual_value == 2.0


@pytest.mark.unit
def test_evidence_collector_input_output_hashes():
    """Test 7: Set input/output data hashes"""
    collector = EvidenceCollector("estimator")

    input_data = {
        "main_breaker": {"poles": 4, "current": 200, "frame": 200},
        "branch_count": 24,
    }
    output_data = {
        "enclosure": "HDS-700*600*200",
        "total_price": 850000,
    }

    collector.set_input_hash(input_data)
    collector.set_output_hash(output_data)

    assert collector.input_data_hash is not None
    assert collector.output_data_hash is not None
    assert len(collector.input_data_hash) == 64
    assert len(collector.output_data_hash) == 64
    assert collector.input_data_hash != collector.output_data_hash  # Different data


@pytest.mark.unit
def test_evidence_collector_metadata():
    """Test 8: Add metadata"""
    collector = EvidenceCollector("test_stage")

    collector.add_metadata("customer_id", "CUST-2025-001")
    collector.add_metadata("quote_id", "Q-20250101-123")
    collector.add_metadata("operator", "narberal_gamma")

    assert len(collector.metadata) == 3
    assert collector.metadata["customer_id"] == "CUST-2025-001"
    assert collector.metadata["operator"] == "narberal_gamma"


@pytest.mark.unit
def test_evidence_collector_summary():
    """Test 9: Get evidence summary"""
    collector = EvidenceCollector("test_stage")

    # Record some evidence
    collector.record_knowledge_file("test.json", {"key": "value"})
    collector.record_db_query("test_table", "SELECT *", 10)
    collector.record_quality_gate(
        {
            "gate_name": "test_gate",
            "passed": True,
            "actual_value": 0.95,
            "threshold": 0.90,
            "operator": ">=",
        }
    )
    collector.set_input_hash({"input": "data"})

    summary = collector.get_summary()

    assert summary["stage_name"] == "test_stage"
    assert summary["knowledge_files_accessed"] == 1
    assert summary["database_queries_executed"] == 1
    assert summary["quality_gates_validated"] == 1
    assert summary["quality_gates_passed"] == 1
    assert summary["quality_gates_failed"] == 0
    assert summary["has_input_hash"] is True
    assert summary["has_output_hash"] is False


@pytest.mark.unit
def test_evidence_collector_save_and_load_roundtrip():
    """Test 10: Save to JSON and load back (round-trip integrity)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Create collector with real data
        collector = EvidenceCollector("roundtrip_test")
        collector.record_knowledge_file(
            "catalog.json", {"items": ["A", "B", "C"]}, keys_accessed=["items"]
        )
        collector.record_db_query("catalog_items", "SELECT * FROM catalog_items", 150)
        collector.record_quality_gate(
            {
                "gate_name": "fit_score",
                "passed": True,
                "actual_value": 0.92,
                "threshold": 0.90,
                "operator": ">=",
            }
        )
        collector.set_input_hash({"input": "test"})
        collector.set_output_hash({"output": "result"})
        collector.add_metadata("test_key", "test_value")

        # Save to file
        saved_path = collector.save(output_dir)

        assert saved_path.exists()
        assert saved_path.suffix == ".json"

        # Load from file
        loaded_evidence = load_evidence(saved_path)

        # Verify data integrity
        assert loaded_evidence.stage_name == collector.stage_name
        assert loaded_evidence.execution_id == collector.execution_id
        assert len(loaded_evidence.knowledge_files) == 1
        assert len(loaded_evidence.database_queries) == 1
        assert len(loaded_evidence.quality_gates) == 1
        assert loaded_evidence.input_data_hash == collector.input_data_hash
        assert loaded_evidence.output_data_hash == collector.output_data_hash
        assert loaded_evidence.metadata["test_key"] == "test_value"

        # Verify timestamps
        assert loaded_evidence.started_at is not None
        assert loaded_evidence.completed_at is not None
        assert (
            loaded_evidence.completed_at >= loaded_evidence.started_at
        )  # >= to handle fast execution


@pytest.mark.unit
def test_evidence_collector_finalize():
    """Test 11: Finalize evidence collection"""
    collector = EvidenceCollector("finalize_test")
    collector.record_knowledge_file("test.json", {"data": 123})

    evidence = collector.finalize()

    assert isinstance(evidence, Evidence)
    assert evidence.stage_name == "finalize_test"
    assert evidence.completed_at is not None
    assert len(evidence.knowledge_files) == 1


@pytest.mark.unit
def test_evidence_collector_empty_save():
    """Test 12: Save evidence with no records (empty case)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        collector = EvidenceCollector("empty_test")
        saved_path = collector.save(output_dir)

        assert saved_path.exists()

        # Load and verify empty evidence
        loaded = load_evidence(saved_path)
        assert len(loaded.knowledge_files) == 0
        assert len(loaded.database_queries) == 0
        assert len(loaded.quality_gates) == 0


@pytest.mark.unit
def test_evidence_load_nonexistent_file():
    """Test 13: Error path - Load nonexistent file"""
    with pytest.raises(FileNotFoundError):
        load_evidence(Path("/nonexistent/path/evidence.json"))


@pytest.mark.unit
def test_evidence_collector_auto_keys_extraction():
    """Test 14: Auto extract keys from dict data"""
    collector = EvidenceCollector("auto_keys_test")

    data = {
        "meta": {"version": "1.0"},
        "catalog": ["A", "B"],
        "rules": {"key": "value"},
    }

    # Don't specify keys_accessed - should auto-extract
    collector.record_knowledge_file("auto.json", data)

    assert len(collector.knowledge_files) == 1
    kf = collector.knowledge_files[0]
    assert set(kf.keys_accessed) == {"meta", "catalog", "rules"}


@pytest.mark.unit
def test_evidence_collector_hash_different_data():
    """Test 15: Different data → different hashes"""
    collector = EvidenceCollector("hash_test")

    data1 = {"key": "value1"}
    data2 = {"key": "value2"}

    collector.record_knowledge_file("file1.json", data1)
    collector.record_knowledge_file("file2.json", data2)

    hash1 = collector.knowledge_files[0].data_hash
    hash2 = collector.knowledge_files[1].data_hash

    assert hash1 != hash2
