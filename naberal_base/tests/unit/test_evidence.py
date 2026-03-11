"""
Evidence Collection System 유닛 테스트

Task: Phase I-3.5 Coverage 60% - Tier3 infra/evidence.py
- EvidenceCollector 기본 기능 검증
- Hash 계산 검증
- JSON save/load 검증
- 데이터 무결성 검증

목업 없음: 실제 Evidence 데이터만 사용
"""

import pytest
from datetime import datetime

from kis_estimator_core.infra.evidence import (
    EvidenceCollector,
    Evidence,
    load_evidence,
)


@pytest.fixture
def temp_evidence_dir(tmp_path):
    """임시 evidence 저장 디렉토리"""
    evidence_dir = tmp_path / "evidence_test"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir


@pytest.fixture
def sample_collector():
    """샘플 EvidenceCollector 인스턴스"""
    return EvidenceCollector("test_stage")


class TestEvidenceCollectorInit:
    """EvidenceCollector 초기화 테스트"""

    def test_init_with_stage_name(self):
        """Stage name으로 초기화"""
        collector = EvidenceCollector("enclosure_solver")
        assert collector.stage_name == "enclosure_solver"
        assert collector.execution_id.startswith("enclosure_solver_")
        assert collector.started_at is not None
        assert len(collector.knowledge_files) == 0
        assert len(collector.database_queries) == 0
        assert len(collector.quality_gates) == 0

    def test_init_with_custom_execution_id(self):
        """Custom execution ID로 초기화"""
        custom_id = "test_exec_001"
        collector = EvidenceCollector("test_stage", execution_id=custom_id)
        assert collector.execution_id == custom_id

    def test_generate_execution_id_format(self):
        """Execution ID 포맷 검증"""
        collector = EvidenceCollector("test_stage")
        # Format: {stage_name}_{YYYYMMDD_HHMMSS_ffffff}
        parts = collector.execution_id.split("_")
        assert len(parts) >= 4  # stage, date, time, microseconds
        assert parts[0] == "test"
        assert parts[1] == "stage"


class TestHashCalculation:
    """Hash 계산 검증"""

    def test_calculate_hash_deterministic(self, sample_collector):
        """동일 데이터 → 동일 해시"""
        data = {"key1": "value1", "key2": 123}
        hash1 = sample_collector._calculate_hash(data)
        hash2 = sample_collector._calculate_hash(data)
        assert hash1 == hash2

    def test_calculate_hash_different_order(self, sample_collector):
        """키 순서 다름 → 동일 해시 (sort_keys=True)"""
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}
        hash1 = sample_collector._calculate_hash(data1)
        hash2 = sample_collector._calculate_hash(data2)
        assert hash1 == hash2

    def test_calculate_hash_different_data(self, sample_collector):
        """다른 데이터 → 다른 해시"""
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        hash1 = sample_collector._calculate_hash(data1)
        hash2 = sample_collector._calculate_hash(data2)
        assert hash1 != hash2


class TestRecordKnowledgeFile:
    """Knowledge file 접근 기록 테스트"""

    def test_record_knowledge_file_basic(self, sample_collector):
        """기본 knowledge file 기록"""
        data = {"meta": {"version": "1.0"}, "catalog": ["A", "B"]}
        sample_collector.record_knowledge_file("test.json", data)

        assert len(sample_collector.knowledge_files) == 1
        record = sample_collector.knowledge_files[0]
        assert record.filename == "test.json"
        assert record.data_hash is not None
        assert len(record.data_hash) == 64  # SHA256 hex length
        assert "meta" in record.keys_accessed
        assert "catalog" in record.keys_accessed

    def test_record_knowledge_file_custom_keys(self, sample_collector):
        """Custom keys_accessed 지정"""
        data = {"a": 1, "b": 2, "c": 3}
        sample_collector.record_knowledge_file(
            "test.json", data, keys_accessed=["a", "b"]
        )

        record = sample_collector.knowledge_files[0]
        assert record.keys_accessed == ["a", "b"]

    def test_record_multiple_knowledge_files(self, sample_collector):
        """여러 knowledge file 기록"""
        sample_collector.record_knowledge_file("file1.json", {"data": 1})
        sample_collector.record_knowledge_file("file2.json", {"data": 2})
        sample_collector.record_knowledge_file("file3.json", {"data": 3})

        assert len(sample_collector.knowledge_files) == 3
        filenames = [kf.filename for kf in sample_collector.knowledge_files]
        assert filenames == ["file1.json", "file2.json", "file3.json"]


class TestRecordDatabaseQuery:
    """Database query 기록 테스트"""

    def test_record_db_query_basic(self, sample_collector):
        """기본 DB query 기록"""
        sample_collector.record_db_query(
            table="catalog_items",
            query="SELECT * FROM catalog_items",
            row_count=100,
        )

        assert len(sample_collector.database_queries) == 1
        query = sample_collector.database_queries[0]
        assert query.table == "catalog_items"
        assert query.query == "SELECT * FROM catalog_items"
        assert query.row_count == 100
        assert query.duration_ms is None

    def test_record_db_query_with_duration(self, sample_collector):
        """Duration 포함 DB query 기록"""
        sample_collector.record_db_query(
            table="breakers",
            query="SELECT * FROM breakers WHERE af = 100",
            row_count=50,
            duration_ms=25.5,
        )

        query = sample_collector.database_queries[0]
        assert query.duration_ms == 25.5

    def test_record_multiple_db_queries(self, sample_collector):
        """여러 DB query 기록"""
        sample_collector.record_db_query("table1", "query1", 10)
        sample_collector.record_db_query("table2", "query2", 20)
        sample_collector.record_db_query("table3", "query3", 30)

        assert len(sample_collector.database_queries) == 3
        row_counts = [q.row_count for q in sample_collector.database_queries]
        assert row_counts == [10, 20, 30]


class TestRecordQualityGate:
    """Quality gate 검증 기록 테스트"""

    def test_record_quality_gate_passed(self, sample_collector):
        """PASS된 quality gate 기록"""
        gate_result = {
            "gate_name": "fit_score",
            "passed": True,
            "actual_value": 0.93,
            "threshold": 0.90,
            "operator": ">=",
        }
        sample_collector.record_quality_gate(gate_result)

        assert len(sample_collector.quality_gates) == 1
        gate = sample_collector.quality_gates[0]
        assert gate.gate_name == "fit_score"
        assert gate.passed is True
        assert gate.actual_value == 0.93
        assert gate.threshold == 0.90
        assert gate.operator == ">="

    def test_record_quality_gate_failed(self, sample_collector):
        """FAIL된 quality gate 기록"""
        gate_result = {
            "gate_name": "phase_balance",
            "passed": False,
            "actual_value": 0.08,
            "threshold": 0.04,
            "operator": "<=",
        }
        sample_collector.record_quality_gate(gate_result)

        gate = sample_collector.quality_gates[0]
        assert gate.passed is False

    def test_record_multiple_quality_gates(self, sample_collector):
        """여러 quality gate 기록"""
        sample_collector.record_quality_gate(
            {
                "gate_name": "gate1",
                "passed": True,
                "actual_value": 1.0,
                "threshold": 0.9,
                "operator": ">=",
            }
        )
        sample_collector.record_quality_gate(
            {
                "gate_name": "gate2",
                "passed": False,
                "actual_value": 0.5,
                "threshold": 0.8,
                "operator": ">=",
            }
        )

        assert len(sample_collector.quality_gates) == 2
        assert sample_collector.quality_gates[0].passed is True
        assert sample_collector.quality_gates[1].passed is False


class TestInputOutputHash:
    """Input/Output hash 설정 테스트"""

    def test_set_input_hash(self, sample_collector):
        """Input data hash 설정"""
        input_data = {"main_breaker": "SBS-203", "branch_count": 24}
        sample_collector.set_input_hash(input_data)

        assert sample_collector.input_data_hash is not None
        assert len(sample_collector.input_data_hash) == 64

    def test_set_output_hash(self, sample_collector):
        """Output data hash 설정"""
        output_data = {"enclosure": "HDS-700*600*200", "fit_score": 0.93}
        sample_collector.set_output_hash(output_data)

        assert sample_collector.output_data_hash is not None
        assert len(sample_collector.output_data_hash) == 64

    def test_input_output_hashes_different(self, sample_collector):
        """Input ≠ Output 해시"""
        input_data = {"data": "input"}
        output_data = {"data": "output"}
        sample_collector.set_input_hash(input_data)
        sample_collector.set_output_hash(output_data)

        assert sample_collector.input_data_hash != sample_collector.output_data_hash


class TestMetadata:
    """Metadata 관리 테스트"""

    def test_add_metadata_single(self, sample_collector):
        """단일 metadata 추가"""
        sample_collector.add_metadata("customer_id", "CUST-001")
        assert sample_collector.metadata["customer_id"] == "CUST-001"

    def test_add_metadata_multiple(self, sample_collector):
        """여러 metadata 추가"""
        sample_collector.add_metadata("customer_id", "CUST-001")
        sample_collector.add_metadata("quote_id", "Q-001")
        sample_collector.add_metadata("operator", "narberal_gamma")

        assert len(sample_collector.metadata) == 3
        assert sample_collector.metadata["operator"] == "narberal_gamma"


class TestFinalize:
    """Evidence 최종화 테스트"""

    def test_finalize_basic(self, sample_collector):
        """기본 finalize"""
        sample_collector.record_knowledge_file("test.json", {"data": 1})
        sample_collector.add_metadata("test", "value")

        evidence = sample_collector.finalize()

        assert isinstance(evidence, Evidence)
        assert evidence.stage_name == "test_stage"
        assert evidence.execution_id == sample_collector.execution_id
        assert evidence.completed_at is not None
        assert (
            evidence.completed_at >= evidence.started_at
        )  # >= (microsecond precision)
        assert len(evidence.knowledge_files) == 1
        assert evidence.metadata["test"] == "value"

    def test_finalize_sets_completed_at(self, sample_collector):
        """completed_at 자동 설정"""
        started = sample_collector.started_at
        evidence = sample_collector.finalize()

        assert evidence.started_at == started
        assert evidence.completed_at >= started


class TestGetSummary:
    """Summary 생성 테스트"""

    def test_get_summary_empty(self, sample_collector):
        """빈 collector summary"""
        summary = sample_collector.get_summary()

        assert summary["stage_name"] == "test_stage"
        assert summary["knowledge_files_accessed"] == 0
        assert summary["database_queries_executed"] == 0
        assert summary["quality_gates_validated"] == 0
        assert summary["quality_gates_passed"] == 0
        assert summary["quality_gates_failed"] == 0
        assert summary["has_input_hash"] is False
        assert summary["has_output_hash"] is False

    def test_get_summary_with_data(self, sample_collector):
        """데이터 포함 summary"""
        sample_collector.record_knowledge_file("test.json", {"data": 1})
        sample_collector.record_db_query("table", "query", 100)
        sample_collector.record_quality_gate(
            {
                "gate_name": "gate1",
                "passed": True,
                "actual_value": 1.0,
                "threshold": 0.9,
                "operator": ">=",
            }
        )
        sample_collector.record_quality_gate(
            {
                "gate_name": "gate2",
                "passed": False,
                "actual_value": 0.5,
                "threshold": 0.8,
                "operator": ">=",
            }
        )
        sample_collector.set_input_hash({"in": 1})
        sample_collector.set_output_hash({"out": 2})

        summary = sample_collector.get_summary()

        assert summary["knowledge_files_accessed"] == 1
        assert summary["database_queries_executed"] == 1
        assert summary["quality_gates_validated"] == 2
        assert summary["quality_gates_passed"] == 1
        assert summary["quality_gates_failed"] == 1
        assert summary["has_input_hash"] is True
        assert summary["has_output_hash"] is True


class TestSaveAndLoad:
    """JSON save/load 테스트"""

    def test_save_creates_file(self, sample_collector, temp_evidence_dir):
        """save() 파일 생성 확인"""
        saved_path = sample_collector.save(temp_evidence_dir)

        assert saved_path.exists()
        assert saved_path.suffix == ".json"
        assert saved_path.stat().st_size > 0

    def test_save_custom_filename(self, sample_collector, temp_evidence_dir):
        """Custom filename 지정"""
        custom_name = "custom_evidence.json"
        saved_path = sample_collector.save(temp_evidence_dir, filename=custom_name)

        assert saved_path.name == custom_name

    def test_save_creates_directory(self, sample_collector, tmp_path):
        """존재하지 않는 디렉토리 자동 생성"""
        nonexistent_dir = tmp_path / "deep" / "nested" / "path"
        saved_path = sample_collector.save(nonexistent_dir)

        assert saved_path.exists()
        assert nonexistent_dir.exists()

    def test_load_evidence_basic(self, sample_collector, temp_evidence_dir):
        """저장 후 로드"""
        sample_collector.add_metadata("test", "value")
        saved_path = sample_collector.save(temp_evidence_dir)

        loaded_evidence = load_evidence(saved_path)

        assert loaded_evidence.stage_name == sample_collector.stage_name
        assert loaded_evidence.execution_id == sample_collector.execution_id
        assert loaded_evidence.metadata["test"] == "value"

    def test_save_load_round_trip_integrity(self, temp_evidence_dir):
        """저장 → 로드 → 데이터 무결성 검증"""
        # 모든 필드 채운 collector 생성
        collector = EvidenceCollector("integrity_test")
        collector.record_knowledge_file("test.json", {"data": 123})
        collector.record_db_query("table", "SELECT *", 50, duration_ms=25.5)
        collector.record_quality_gate(
            {
                "gate_name": "fit_score",
                "passed": True,
                "actual_value": 0.95,
                "threshold": 0.90,
                "operator": ">=",
            }
        )
        collector.set_input_hash({"input": "data"})
        collector.set_output_hash({"output": "result"})
        collector.add_metadata("customer", "CUST-001")

        # 저장
        saved_path = collector.save(temp_evidence_dir)

        # 로드
        loaded = load_evidence(saved_path)

        # 검증
        assert loaded.stage_name == "integrity_test"
        assert loaded.execution_id == collector.execution_id
        assert len(loaded.knowledge_files) == 1
        assert loaded.knowledge_files[0].filename == "test.json"
        assert len(loaded.database_queries) == 1
        assert loaded.database_queries[0].row_count == 50
        assert loaded.database_queries[0].duration_ms == 25.5
        assert len(loaded.quality_gates) == 1
        assert loaded.quality_gates[0].passed is True
        assert loaded.input_data_hash == collector.input_data_hash
        assert loaded.output_data_hash == collector.output_data_hash
        assert loaded.metadata["customer"] == "CUST-001"

    def test_load_preserves_timestamps(self, sample_collector, temp_evidence_dir):
        """Timestamp 보존 확인"""
        saved_path = sample_collector.save(temp_evidence_dir)
        loaded = load_evidence(saved_path)

        assert isinstance(loaded.started_at, datetime)
        assert isinstance(loaded.completed_at, datetime)
        assert loaded.completed_at > loaded.started_at


class TestIntegration:
    """통합 시나리오 테스트"""

    def test_full_pipeline_evidence_collection(self, temp_evidence_dir):
        """전체 파이프라인 evidence 수집 시뮬레이션"""
        # Stage 1: Enclosure Solver
        collector = EvidenceCollector("enclosure_solver")

        # Knowledge file 접근
        collector.record_knowledge_file(
            "core_rules.json",
            {"breaker_dimensions_mm": {}, "frame_clearances": {}},
            keys_accessed=["breaker_dimensions_mm", "frame_clearances"],
        )

        # DB 쿼리
        collector.record_db_query(
            table="catalog_items",
            query="SELECT * FROM catalog_items WHERE category = 'enclosure'",
            row_count=122,
            duration_ms=45.2,
        )

        # Quality gate 검증
        collector.record_quality_gate(
            {
                "gate_name": "fit_score",
                "passed": True,
                "actual_value": 0.93,
                "threshold": 0.90,
                "operator": ">=",
            }
        )

        # Input/Output
        collector.set_input_hash({"main_a": 100, "branch_count": 24})
        collector.set_output_hash({"enclosure": "HDS-700*600*200"})

        # Metadata
        collector.add_metadata("customer_id", "CUST-2025-001")
        collector.add_metadata("operator", "narberal_gamma")

        # 저장
        saved_path = collector.save(temp_evidence_dir)

        # 로드 및 검증
        loaded = load_evidence(saved_path)
        assert loaded.stage_name == "enclosure_solver"
        assert len(loaded.knowledge_files) == 1
        assert len(loaded.database_queries) == 1
        assert len(loaded.quality_gates) == 1
        assert loaded.quality_gates[0].passed is True
        assert loaded.metadata["operator"] == "narberal_gamma"
