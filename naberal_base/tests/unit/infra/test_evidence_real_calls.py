"""
Test evidence.py - Real evidence collection (NO MOCKS)
Phase I-5 Wave 9 (1/4)

Zero-Mock 준수: 실제 파일 I/O, 실제 데이터만 사용
"""

import pytest
from datetime import datetime, timezone
from kis_estimator_core.infra.evidence import (
    EvidenceCollector,
    Evidence,
    load_evidence,
)


@pytest.mark.unit
class TestEvidenceCollector:
    """EvidenceCollector 실제 호출 테스트"""

    def test_init_default(self):
        """기본 초기화 (execution_id 자동 생성)."""
        collector = EvidenceCollector("enclosure_solver_test")

        assert collector.stage_name == "enclosure_solver_test"
        assert collector.execution_id.startswith("enclosure_solver_test_")
        assert collector.started_at is not None
        assert len(collector.knowledge_files) == 0
        assert len(collector.database_queries) == 0
        assert len(collector.quality_gates) == 0

    def test_init_custom_execution_id(self):
        """커스텀 execution_id 사용."""
        collector = EvidenceCollector("test_stage", execution_id="CUSTOM-001")

        assert collector.execution_id == "CUSTOM-001"
        assert collector.stage_name == "test_stage"

    def test_record_knowledge_file(self):
        """실제 지식파일 데이터 기록."""
        collector = EvidenceCollector("test_stage")

        real_data = {
            "meta": {"version": "1.0.0"},
            "catalog": ["SBE-102", "SBS-202"],
            "selection_rules": {"경제형_우선": True},
        }

        collector.record_knowledge_file(
            "breakers.json", real_data, keys_accessed=["meta", "catalog"]
        )

        assert len(collector.knowledge_files) == 1
        kf = collector.knowledge_files[0]
        assert kf.filename == "breakers.json"
        assert kf.data_hash is not None
        assert len(kf.data_hash) == 64  # SHA256 hex
        assert kf.keys_accessed == ["meta", "catalog"]

    def test_record_knowledge_file_auto_keys(self):
        """keys_accessed 자동 추출."""
        collector = EvidenceCollector("test_stage")

        data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        collector.record_knowledge_file("test.json", data)

        assert len(collector.knowledge_files) == 1
        kf = collector.knowledge_files[0]
        assert set(kf.keys_accessed) == {"key1", "key2", "key3"}

    def test_record_db_query(self):
        """실제 DB 쿼리 기록."""
        collector = EvidenceCollector("test_stage")

        collector.record_db_query(
            table="catalog_items",
            query="SELECT * FROM catalog_items WHERE category = 'MCCB' LIMIT 100",
            row_count=122,
            duration_ms=45.2,
        )

        assert len(collector.database_queries) == 1
        dbq = collector.database_queries[0]
        assert dbq.table == "catalog_items"
        assert dbq.query.startswith("SELECT *")
        assert dbq.row_count == 122
        assert dbq.duration_ms == 45.2
        assert dbq.executed_at is not None

    def test_record_quality_gate(self):
        """실제 품질 게이트 검증 기록."""
        collector = EvidenceCollector("test_stage")

        gate_result = {
            "gate_name": "fit_score",
            "passed": True,
            "actual_value": 0.93,
            "threshold": 0.90,
            "operator": ">=",
        }
        collector.record_quality_gate(gate_result)

        assert len(collector.quality_gates) == 1
        qg = collector.quality_gates[0]
        assert qg.gate_name == "fit_score"
        assert qg.passed
        assert qg.actual_value == 0.93
        assert qg.threshold == 0.90
        assert qg.operator == ">="

    def test_set_input_output_hash(self):
        """입출력 데이터 해시 설정."""
        collector = EvidenceCollector("test_stage")

        input_data = {
            "main_breaker": "SBS-203",
            "branch_count": 24,
            "enclosure_type": "옥내자립",
        }
        output_data = {
            "selected_enclosure": "HDS-700*600*200",
            "fit_score": 0.93,
            "total_price": 850000,
        }

        collector.set_input_hash(input_data)
        collector.set_output_hash(output_data)

        assert collector.input_data_hash is not None
        assert len(collector.input_data_hash) == 64
        assert collector.output_data_hash is not None
        assert len(collector.output_data_hash) == 64
        assert collector.input_data_hash != collector.output_data_hash

    def test_add_metadata(self):
        """메타데이터 추가."""
        collector = EvidenceCollector("test_stage")

        collector.add_metadata("customer_id", "CUST-2025-001")
        collector.add_metadata("quote_id", "Q-20250101-123")
        collector.add_metadata("operator", "narberal_gamma")

        assert len(collector.metadata) == 3
        assert collector.metadata["customer_id"] == "CUST-2025-001"
        assert collector.metadata["quote_id"] == "Q-20250101-123"
        assert collector.metadata["operator"] == "narberal_gamma"

    def test_get_summary(self):
        """증거 요약 정보 생성."""
        collector = EvidenceCollector("test_stage")

        # 데이터 추가
        collector.record_knowledge_file("test.json", {"key": "value"})
        collector.record_db_query("test_table", "SELECT *", 10)
        collector.record_quality_gate(
            {
                "gate_name": "test",
                "passed": True,
                "actual_value": 1.0,
                "threshold": 0.9,
                "operator": ">=",
            }
        )
        collector.record_quality_gate(
            {
                "gate_name": "test2",
                "passed": False,
                "actual_value": 0.5,
                "threshold": 0.8,
                "operator": ">=",
            }
        )
        collector.set_input_hash({"test": "input"})
        collector.set_output_hash({"test": "output"})

        summary = collector.get_summary()

        assert summary["stage_name"] == "test_stage"
        assert summary["knowledge_files_accessed"] == 1
        assert summary["database_queries_executed"] == 1
        assert summary["quality_gates_validated"] == 2
        assert summary["quality_gates_passed"] == 1
        assert summary["quality_gates_failed"] == 1
        assert summary["has_input_hash"]
        assert summary["has_output_hash"]

    def test_finalize(self):
        """증거 패키지 완성."""
        collector = EvidenceCollector("test_stage", execution_id="TEST-001")

        collector.record_knowledge_file("test.json", {"key": "value"})
        collector.record_db_query("test_table", "SELECT *", 10)
        collector.record_quality_gate(
            {
                "gate_name": "test",
                "passed": True,
                "actual_value": 1.0,
                "threshold": 0.9,
                "operator": ">=",
            }
        )

        evidence = collector.finalize()

        assert isinstance(evidence, Evidence)
        assert evidence.stage_name == "test_stage"
        assert evidence.execution_id == "TEST-001"
        assert evidence.started_at is not None
        assert evidence.completed_at is not None
        assert (
            evidence.completed_at >= evidence.started_at
        )  # 빠른 실행 시 동일 시간 가능
        assert len(evidence.knowledge_files) == 1
        assert len(evidence.database_queries) == 1
        assert len(evidence.quality_gates) == 1

    def test_save_and_load(self, tmp_path):
        """실제 파일 저장 및 로드 (Zero-Mock)."""
        collector = EvidenceCollector("test_stage", execution_id="TEST-SAVE-001")

        # 실제 데이터 기록
        real_breakers_data = {
            "meta": {"version": "1.0.0"},
            "catalog": ["SBE-102", "SBS-202"],
        }
        collector.record_knowledge_file(
            "breakers.json", real_breakers_data, keys_accessed=["meta", "catalog"]
        )

        collector.record_db_query(
            table="catalog_items",
            query="SELECT * FROM catalog_items",
            row_count=122,
            duration_ms=45.2,
        )

        collector.record_quality_gate(
            {
                "gate_name": "fit_score",
                "passed": True,
                "actual_value": 0.93,
                "threshold": 0.90,
                "operator": ">=",
            }
        )

        input_data = {"main_breaker": "SBS-203", "branch_count": 24}
        output_data = {"selected_enclosure": "HDS-700*600*200", "fit_score": 0.93}

        collector.set_input_hash(input_data)
        collector.set_output_hash(output_data)
        collector.add_metadata("customer_id", "CUST-2025-001")

        # 파일 저장
        evidence_dir = tmp_path / "evidence"
        saved_path = collector.save(evidence_dir)

        # 파일 존재 확인
        assert saved_path.exists()
        assert saved_path.stat().st_size > 0

        # 파일 로드
        loaded_evidence = load_evidence(saved_path)

        # 데이터 무결성 검증
        assert loaded_evidence.stage_name == "test_stage"
        assert loaded_evidence.execution_id == "TEST-SAVE-001"
        assert len(loaded_evidence.knowledge_files) == 1
        assert len(loaded_evidence.database_queries) == 1
        assert len(loaded_evidence.quality_gates) == 1
        assert loaded_evidence.input_data_hash == collector.input_data_hash
        assert loaded_evidence.output_data_hash == collector.output_data_hash
        assert loaded_evidence.metadata["customer_id"] == "CUST-2025-001"

    def test_save_custom_filename(self, tmp_path):
        """커스텀 파일명으로 저장."""
        collector = EvidenceCollector("test_stage")
        collector.record_knowledge_file("test.json", {"key": "value"})

        evidence_dir = tmp_path / "evidence"
        saved_path = collector.save(evidence_dir, filename="custom_evidence.json")

        assert saved_path.name == "custom_evidence.json"
        assert saved_path.exists()

    def test_save_creates_directory(self, tmp_path):
        """존재하지 않는 디렉토리 자동 생성."""
        collector = EvidenceCollector("test_stage")
        collector.record_knowledge_file("test.json", {"key": "value"})

        evidence_dir = tmp_path / "nonexistent" / "nested" / "evidence"
        saved_path = collector.save(evidence_dir)

        assert evidence_dir.exists()
        assert saved_path.exists()

    def test_hash_consistency(self):
        """동일 데이터는 동일 해시 생성."""
        collector1 = EvidenceCollector("test1")
        collector2 = EvidenceCollector("test2")

        data = {"key1": "value1", "key2": "value2"}

        collector1.set_input_hash(data)
        collector2.set_input_hash(data)

        assert collector1.input_data_hash == collector2.input_data_hash

    def test_hash_different_for_different_data(self):
        """다른 데이터는 다른 해시 생성."""
        collector1 = EvidenceCollector("test1")
        collector2 = EvidenceCollector("test2")

        collector1.set_input_hash({"key": "value1"})
        collector2.set_input_hash({"key": "value2"})

        assert collector1.input_data_hash != collector2.input_data_hash

    def test_multiple_knowledge_files(self):
        """여러 지식파일 기록."""
        collector = EvidenceCollector("test_stage")

        for i in range(5):
            collector.record_knowledge_file(f"file_{i}.json", {"index": i})

        assert len(collector.knowledge_files) == 5
        for i, kf in enumerate(collector.knowledge_files):
            assert kf.filename == f"file_{i}.json"

    def test_multiple_db_queries(self):
        """여러 DB 쿼리 기록."""
        collector = EvidenceCollector("test_stage")

        tables = ["catalog_items", "prices", "inventory", "customers"]
        for table in tables:
            collector.record_db_query(table, f"SELECT * FROM {table}", 100)

        assert len(collector.database_queries) == 4
        for i, dbq in enumerate(collector.database_queries):
            assert dbq.table == tables[i]

    def test_multiple_quality_gates(self):
        """여러 품질 게이트 기록."""
        collector = EvidenceCollector("test_stage")

        gates = [
            ("fit_score", True, 0.93, 0.90),
            ("ip_rating", True, 54.0, 44.0),
            ("clearance", False, 5.0, 10.0),
        ]

        for name, passed, actual, threshold in gates:
            collector.record_quality_gate(
                {
                    "gate_name": name,
                    "passed": passed,
                    "actual_value": actual,
                    "threshold": threshold,
                    "operator": ">=",
                }
            )

        assert len(collector.quality_gates) == 3
        summary = collector.get_summary()
        assert summary["quality_gates_passed"] == 2
        assert summary["quality_gates_failed"] == 1

    def test_timestamp_ordering(self):
        """타임스탬프 순서 검증."""
        collector = EvidenceCollector("test_stage")
        _ = collector.started_at

        collector.record_knowledge_file("test.json", {"key": "value"})

        evidence = collector.finalize()

        assert evidence.started_at <= evidence.knowledge_files[0].accessed_at
        assert evidence.knowledge_files[0].accessed_at <= evidence.completed_at


@pytest.mark.unit
class TestLoadEvidence:
    """load_evidence 함수 테스트"""

    def test_load_valid_evidence(self, tmp_path):
        """유효한 증거 파일 로드."""
        collector = EvidenceCollector("load_test", execution_id="LOAD-001")
        collector.record_knowledge_file("test.json", {"key": "value"})
        collector.record_db_query("test_table", "SELECT *", 10)
        collector.record_quality_gate(
            {
                "gate_name": "test",
                "passed": True,
                "actual_value": 1.0,
                "threshold": 0.9,
                "operator": ">=",
            }
        )

        evidence_dir = tmp_path / "evidence"
        saved_path = collector.save(evidence_dir)

        loaded = load_evidence(saved_path)

        assert loaded.stage_name == "load_test"
        assert loaded.execution_id == "LOAD-001"
        assert isinstance(loaded.started_at, datetime)
        assert isinstance(loaded.completed_at, datetime)

    def test_load_preserves_timestamps(self, tmp_path):
        """로드 시 타임스탬프 보존."""
        collector = EvidenceCollector("timestamp_test")
        collector.record_knowledge_file("test.json", {"key": "value"})

        evidence_dir = tmp_path / "evidence"
        saved_path = collector.save(evidence_dir)

        loaded = load_evidence(saved_path)

        assert loaded.started_at.tzinfo == timezone.utc
        assert loaded.completed_at.tzinfo == timezone.utc
        assert loaded.knowledge_files[0].accessed_at.tzinfo == timezone.utc
