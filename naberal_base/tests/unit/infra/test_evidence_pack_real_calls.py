"""
evidence.py 실제 호출 테스트 (P4-2 Real-Call 전환)

목적: coverage 측정을 위한 실제 함수 호출
원칙: Zero-Mock, 실제 파일 생성/검증
"""

from datetime import datetime, timezone

from kis_estimator_core.infra.evidence import (
    EvidenceCollector,
    Evidence,
    KnowledgeFileAccess,
    DatabaseQuery,
    QualityGateRecord,
    load_evidence,
)


# ============================================================
# Test: EvidenceCollector Initialization
# ============================================================
def test_evidence_collector_init():
    """EvidenceCollector 초기화"""
    # 실제 호출
    collector = EvidenceCollector(stage_name="test_stage")

    # 검증
    assert collector.stage_name == "test_stage"
    assert collector.execution_id is not None
    assert collector.started_at is not None
    assert len(collector.knowledge_files) == 0
    assert len(collector.database_queries) == 0
    assert len(collector.quality_gates) == 0


def test_evidence_collector_init_with_execution_id():
    """EvidenceCollector 초기화 (execution_id 제공)"""
    # 실제 호출
    collector = EvidenceCollector(
        stage_name="test_stage", execution_id="custom_exec_123"
    )

    # 검증
    assert collector.execution_id == "custom_exec_123"


# ============================================================
# Test: record_knowledge_file
# ============================================================
def test_record_knowledge_file():
    """지식 파일 접근 기록"""
    collector = EvidenceCollector("test_stage")

    # 실제 데이터
    test_data = {"meta": {"version": "1.0.0"}, "catalog": ["item1", "item2"]}

    # 실제 호출
    collector.record_knowledge_file(
        filename="test_knowledge.json",
        data=test_data,
        keys_accessed=["meta", "catalog"],
    )

    # 검증
    assert len(collector.knowledge_files) == 1
    access = collector.knowledge_files[0]
    assert access.filename == "test_knowledge.json"
    assert access.data_hash is not None
    assert access.keys_accessed == ["meta", "catalog"]


def test_record_knowledge_file_auto_keys():
    """지식 파일 접근 기록 (키 자동 추출)"""
    collector = EvidenceCollector("test_stage")

    test_data = {"key1": "value1", "key2": "value2"}

    # 실제 호출 (keys_accessed 없음)
    collector.record_knowledge_file(filename="test.json", data=test_data)

    # 검증: 키 자동 추출
    assert collector.knowledge_files[0].keys_accessed == ["key1", "key2"]


# ============================================================
# Test: record_db_query
# ============================================================
def test_record_db_query():
    """DB 쿼리 기록"""
    collector = EvidenceCollector("test_stage")

    # 실제 호출
    collector.record_db_query(
        table="catalog_items",
        query="SELECT * FROM catalog_items LIMIT 10",
        row_count=10,
        duration_ms=25.5,
    )

    # 검증
    assert len(collector.database_queries) == 1
    query = collector.database_queries[0]
    assert query.table == "catalog_items"
    assert query.row_count == 10
    assert query.duration_ms == 25.5


def test_record_db_query_without_duration():
    """DB 쿼리 기록 (duration 없음)"""
    collector = EvidenceCollector("test_stage")

    # 실제 호출
    collector.record_db_query(
        table="test_table", query="SELECT COUNT(*) FROM test_table", row_count=1
    )

    # 검증
    assert collector.database_queries[0].duration_ms is None


# ============================================================
# Test: record_quality_gate
# ============================================================
def test_record_quality_gate_pass():
    """품질 게이트 기록 (통과)"""
    collector = EvidenceCollector("test_stage")

    # 실제 호출
    collector.record_quality_gate(
        {
            "gate_name": "fit_score",
            "passed": True,
            "actual_value": 0.95,
            "threshold": 0.90,
            "operator": ">=",
        }
    )

    # 검증
    assert len(collector.quality_gates) == 1
    gate = collector.quality_gates[0]
    assert gate.gate_name == "fit_score"
    assert gate.passed is True
    assert gate.actual_value == 0.95
    assert gate.threshold == 0.90


def test_record_quality_gate_fail():
    """품질 게이트 기록 (실패)"""
    collector = EvidenceCollector("test_stage")

    # 실제 호출
    collector.record_quality_gate(
        {
            "gate_name": "phase_balance",
            "passed": False,
            "actual_value": 0.08,
            "threshold": 0.04,
            "operator": "<=",
        }
    )

    # 검증
    assert collector.quality_gates[0].passed is False


# ============================================================
# Test: set_input_hash / set_output_hash
# ============================================================
def test_set_input_hash():
    """입력 데이터 해시 설정"""
    collector = EvidenceCollector("test_stage")

    input_data = {"main_breaker": "SBE-104", "branch_count": 10}

    # 실제 호출
    collector.set_input_hash(input_data)

    # 검증
    assert collector.input_data_hash is not None
    assert len(collector.input_data_hash) == 64  # SHA256 hex = 64 chars


def test_set_output_hash():
    """출력 데이터 해시 설정"""
    collector = EvidenceCollector("test_stage")

    output_data = {"enclosure": "HDS-600*800*200", "total_price": 500000}

    # 실제 호출
    collector.set_output_hash(output_data)

    # 검증
    assert collector.output_data_hash is not None
    assert len(collector.output_data_hash) == 64


def test_hash_consistency():
    """동일 데이터는 동일 해시 생성"""
    collector1 = EvidenceCollector("test_stage")
    collector2 = EvidenceCollector("test_stage")

    data = {"key": "value", "number": 123}

    collector1.set_input_hash(data)
    collector2.set_input_hash(data)

    # 검증: 동일 해시
    assert collector1.input_data_hash == collector2.input_data_hash


# ============================================================
# Test: add_metadata
# ============================================================
def test_add_metadata():
    """메타데이터 추가"""
    collector = EvidenceCollector("test_stage")

    # 실제 호출
    collector.add_metadata("customer_id", "CUST-001")
    collector.add_metadata("quote_id", "Q-123")
    collector.add_metadata("operator", "test_user")

    # 검증
    assert len(collector.metadata) == 3
    assert collector.metadata["customer_id"] == "CUST-001"
    assert collector.metadata["quote_id"] == "Q-123"


# ============================================================
# Test: finalize
# ============================================================
def test_finalize():
    """증거 완료"""
    collector = EvidenceCollector("test_stage")

    # 데이터 기록
    collector.record_knowledge_file("test.json", {"key": "value"})
    collector.record_db_query("test_table", "SELECT *", 10)
    collector.record_quality_gate(
        {
            "gate_name": "test_gate",
            "passed": True,
            "actual_value": 1.0,
            "threshold": 0.9,
            "operator": ">=",
        }
    )

    # 실제 호출
    evidence = collector.finalize()

    # 검증
    assert isinstance(evidence, Evidence)
    assert evidence.stage_name == "test_stage"
    assert evidence.completed_at is not None
    assert len(evidence.knowledge_files) == 1
    assert len(evidence.database_queries) == 1
    assert len(evidence.quality_gates) == 1


# ============================================================
# Test: save (파일 생성)
# ============================================================
def test_save_evidence(tmp_path):
    """증거 파일 저장"""
    collector = EvidenceCollector("test_stage", execution_id="test_exec_123")

    # 데이터 기록
    collector.record_knowledge_file("test.json", {"key": "value"})
    collector.set_input_hash({"input": "data"})
    collector.set_output_hash({"output": "result"})

    # 실제 호출
    saved_path = collector.save(tmp_path)

    # 검증: 파일 생성됨
    assert saved_path.exists()
    assert saved_path.suffix == ".json"
    assert saved_path.stat().st_size > 0


def test_save_evidence_with_custom_filename(tmp_path):
    """증거 파일 저장 (커스텀 파일명)"""
    collector = EvidenceCollector("test_stage")

    # 실제 호출
    saved_path = collector.save(tmp_path, filename="custom_evidence.json")

    # 검증
    assert saved_path.name == "custom_evidence.json"
    assert saved_path.exists()


def test_save_evidence_creates_directory(tmp_path):
    """증거 파일 저장 (디렉토리 자동 생성)"""
    collector = EvidenceCollector("test_stage")

    # 존재하지 않는 디렉토리
    nested_dir = tmp_path / "nested" / "evidence"

    # 실제 호출
    saved_path = collector.save(nested_dir)

    # 검증: 디렉토리 생성됨
    assert nested_dir.exists()
    assert saved_path.exists()


# ============================================================
# Test: get_summary
# ============================================================
def test_get_summary():
    """증거 요약 정보"""
    collector = EvidenceCollector("test_stage")

    # 데이터 기록
    collector.record_knowledge_file("file1.json", {"key": "value"})
    collector.record_knowledge_file("file2.json", {"key2": "value2"})
    collector.record_db_query("table1", "SELECT *", 10)
    collector.record_quality_gate(
        {
            "gate_name": "gate1",
            "passed": True,
            "actual_value": 1.0,
            "threshold": 0.9,
            "operator": ">=",
        }
    )
    collector.record_quality_gate(
        {
            "gate_name": "gate2",
            "passed": False,
            "actual_value": 0.8,
            "threshold": 0.9,
            "operator": ">=",
        }
    )
    collector.set_input_hash({"input": "data"})

    # 실제 호출
    summary = collector.get_summary()

    # 검증
    assert summary["stage_name"] == "test_stage"
    assert summary["knowledge_files_accessed"] == 2
    assert summary["database_queries_executed"] == 1
    assert summary["quality_gates_validated"] == 2
    assert summary["quality_gates_passed"] == 1
    assert summary["quality_gates_failed"] == 1
    assert summary["has_input_hash"] is True
    assert summary["has_output_hash"] is False


# ============================================================
# Test: load_evidence (파일 로딩)
# ============================================================
def test_load_evidence(tmp_path):
    """증거 파일 로딩"""
    # 1. 저장
    collector = EvidenceCollector("test_stage", execution_id="test_exec_456")
    collector.record_knowledge_file("test.json", {"key": "value"})
    collector.record_db_query("test_table", "SELECT *", 5)
    collector.record_quality_gate(
        {
            "gate_name": "test_gate",
            "passed": True,
            "actual_value": 1.0,
            "threshold": 0.9,
            "operator": ">=",
        }
    )
    collector.add_metadata("test_key", "test_value")

    saved_path = collector.save(tmp_path)

    # 2. 로딩 (실제 호출)
    loaded_evidence = load_evidence(saved_path)

    # 검증
    assert loaded_evidence.stage_name == "test_stage"
    assert loaded_evidence.execution_id == "test_exec_456"
    assert len(loaded_evidence.knowledge_files) == 1
    assert len(loaded_evidence.database_queries) == 1
    assert len(loaded_evidence.quality_gates) == 1
    assert loaded_evidence.metadata["test_key"] == "test_value"


def test_load_evidence_datetime_parsing(tmp_path):
    """증거 파일 로딩 (datetime 파싱)"""
    # 저장
    collector = EvidenceCollector("test_stage")
    collector.record_knowledge_file("test.json", {"key": "value"})
    saved_path = collector.save(tmp_path)

    # 로딩 (실제 호출)
    loaded_evidence = load_evidence(saved_path)

    # 검증: datetime 객체로 파싱됨
    assert isinstance(loaded_evidence.started_at, datetime)
    assert isinstance(loaded_evidence.completed_at, datetime)
    assert isinstance(loaded_evidence.knowledge_files[0].accessed_at, datetime)


# ============================================================
# Test: Pydantic Models
# ============================================================
def test_knowledge_file_access_model():
    """KnowledgeFileAccess 모델"""
    # 실제 호출
    access = KnowledgeFileAccess(
        filename="test.json",
        accessed_at=datetime.now(timezone.utc),
        data_hash="abc123",
        keys_accessed=["key1", "key2"],
    )

    # 검증
    assert access.filename == "test.json"
    assert access.data_hash == "abc123"


def test_database_query_model():
    """DatabaseQuery 모델"""
    # 실제 호출
    query = DatabaseQuery(
        table="test_table",
        query="SELECT *",
        row_count=10,
        executed_at=datetime.now(timezone.utc),
        duration_ms=25.5,
    )

    # 검증
    assert query.table == "test_table"
    assert query.row_count == 10


def test_quality_gate_record_model():
    """QualityGateRecord 모델"""
    # 실제 호출
    gate = QualityGateRecord(
        gate_name="test_gate",
        passed=True,
        actual_value=1.0,
        threshold=0.9,
        operator=">=",
        validated_at=datetime.now(timezone.utc),
    )

    # 검증
    assert gate.gate_name == "test_gate"
    assert gate.passed is True
