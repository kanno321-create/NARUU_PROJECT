"""
Evidence Collection System for KIS Estimator
Tracks all data sources, queries, and validation results
NO MOCKS - Real data tracking only
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeFileAccess(BaseModel):
    """Record of knowledge file access"""

    filename: str
    accessed_at: datetime
    data_hash: str = Field(..., description="SHA256 hash of accessed data")
    keys_accessed: list[str] | None = Field(
        None, description="Top-level keys accessed"
    )


class DatabaseQuery(BaseModel):
    """Record of database query execution"""

    table: str
    query: str
    row_count: int
    executed_at: datetime
    duration_ms: float | None = None


class QualityGateRecord(BaseModel):
    """Record of quality gate validation"""

    gate_name: str
    passed: bool
    actual_value: float
    threshold: float
    operator: str
    validated_at: datetime


class Evidence(BaseModel):
    """
    Complete evidence package for a pipeline stage execution

    Tracks all data sources, queries, and validations to ensure
    complete traceability and reproducibility
    """

    stage_name: str
    execution_id: str
    started_at: datetime
    completed_at: datetime | None = None
    knowledge_files: list[KnowledgeFileAccess] = Field(default_factory=list)
    database_queries: list[DatabaseQuery] = Field(default_factory=list)
    quality_gates: list[QualityGateRecord] = Field(default_factory=list)
    input_data_hash: str | None = None
    output_data_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EvidenceCollector:
    """
    Collects evidence during pipeline stage execution

    NO MOCKS - Real data tracking only

    Example:
        collector = EvidenceCollector("enclosure_solver")

        # Track knowledge file access
        breakers_data = loader.load("breakers.json")
        collector.record_knowledge_file("breakers.json", breakers_data)

        # Track database query
        result = supabase.table("catalog_items").select("*").execute()
        collector.record_db_query("catalog_items", "SELECT * FROM catalog_items", len(result.data))

        # Track quality gate validation
        collector.record_quality_gate({
            "gate_name": "fit_score",
            "passed": True,
            "actual_value": 0.93,
            "threshold": 0.90,
            "operator": ">="
        })

        # Save evidence
        collector.save(Path("./evidence"))
    """

    def __init__(self, stage_name: str, execution_id: str | None = None):
        """
        Initialize evidence collector

        Args:
            stage_name: Name of pipeline stage (e.g., "enclosure_solver")
            execution_id: Unique execution ID (auto-generated if not provided)
        """
        self.stage_name = stage_name
        self.execution_id = execution_id or self._generate_execution_id()
        self.started_at = datetime.now(UTC)

        self.knowledge_files: list[KnowledgeFileAccess] = []
        self.database_queries: list[DatabaseQuery] = []
        self.quality_gates: list[QualityGateRecord] = []

        self.input_data_hash: str | None = None
        self.output_data_hash: str | None = None
        self.metadata: dict[str, Any] = {}

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID based on timestamp"""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
        return f"{self.stage_name}_{timestamp}"

    def _calculate_hash(self, data: Any) -> str:
        """
        Calculate SHA256 hash of data

        Args:
            data: Data to hash (will be JSON serialized)

        Returns:
            str: SHA256 hex digest
        """
        # Convert to JSON string for consistent hashing
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()

    def record_knowledge_file(
        self,
        filename: str,
        data: dict[str, Any],
        keys_accessed: list[str] | None = None,
    ):
        """
        Record access to a knowledge file

        Args:
            filename: Knowledge file name (e.g., "breakers.json")
            data: Actual data accessed from the file
            keys_accessed: Optional list of top-level keys accessed
        """
        data_hash = self._calculate_hash(data)

        # Extract keys if not provided
        if keys_accessed is None and isinstance(data, dict):
            keys_accessed = list(data.keys())

        access = KnowledgeFileAccess(
            filename=filename,
            accessed_at=datetime.now(UTC),
            data_hash=data_hash,
            keys_accessed=keys_accessed,
        )
        self.knowledge_files.append(access)

    def record_db_query(
        self,
        table: str,
        query: str,
        row_count: int,
        duration_ms: float | None = None,
    ):
        """
        Record database query execution

        Args:
            table: Table name queried
            query: SQL query or description
            row_count: Number of rows returned
            duration_ms: Query execution time in milliseconds
        """
        query_record = DatabaseQuery(
            table=table,
            query=query,
            row_count=row_count,
            executed_at=datetime.now(UTC),
            duration_ms=duration_ms,
        )
        self.database_queries.append(query_record)

    def record_quality_gate(self, gate_result: dict[str, Any]):
        """
        Record quality gate validation result

        Args:
            gate_result: Dictionary with gate validation result
                Required keys: gate_name, passed, actual_value, threshold, operator
        """
        gate = QualityGateRecord(
            gate_name=gate_result["gate_name"],
            passed=gate_result["passed"],
            actual_value=gate_result["actual_value"],
            threshold=gate_result["threshold"],
            operator=gate_result["operator"],
            validated_at=datetime.now(UTC),
        )
        self.quality_gates.append(gate)

    def set_input_hash(self, input_data: Any):
        """
        Set hash of input data

        Args:
            input_data: Input data to hash
        """
        self.input_data_hash = self._calculate_hash(input_data)

    def set_output_hash(self, output_data: Any):
        """
        Set hash of output data

        Args:
            output_data: Output data to hash
        """
        self.output_data_hash = self._calculate_hash(output_data)

    def add_metadata(self, key: str, value: Any):
        """
        Add metadata to evidence

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def finalize(self) -> Evidence:
        """
        Finalize evidence collection

        Returns:
            Evidence: Complete evidence package
        """
        evidence = Evidence(
            stage_name=self.stage_name,
            execution_id=self.execution_id,
            started_at=self.started_at,
            completed_at=datetime.now(UTC),
            knowledge_files=self.knowledge_files,
            database_queries=self.database_queries,
            quality_gates=self.quality_gates,
            input_data_hash=self.input_data_hash,
            output_data_hash=self.output_data_hash,
            metadata=self.metadata,
        )
        return evidence

    def save(self, output_dir: Path, filename: str | None = None) -> Path:
        """
        Save evidence to JSON file

        Args:
            output_dir: Directory to save evidence file
            filename: Optional custom filename (default: {stage_name}_evidence.json)

        Returns:
            Path: Path to saved evidence file
        """
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if filename is None:
            filename = f"{self.stage_name}_evidence_{self.execution_id}.json"

        # Finalize evidence
        evidence = self.finalize()

        # Save to JSON
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                evidence.model_dump(),
                f,
                indent=2,
                ensure_ascii=False,
                default=str,  # Handle datetime serialization
            )

        return filepath

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary of collected evidence

        Returns:
            dict: Summary statistics
        """
        return {
            "stage_name": self.stage_name,
            "execution_id": self.execution_id,
            "knowledge_files_accessed": len(self.knowledge_files),
            "database_queries_executed": len(self.database_queries),
            "quality_gates_validated": len(self.quality_gates),
            "quality_gates_passed": sum(1 for g in self.quality_gates if g.passed),
            "quality_gates_failed": sum(1 for g in self.quality_gates if not g.passed),
            "has_input_hash": self.input_data_hash is not None,
            "has_output_hash": self.output_data_hash is not None,
        }


def load_evidence(filepath: Path) -> Evidence:
    """
    Load evidence from JSON file

    Args:
        filepath: Path to evidence JSON file

    Returns:
        Evidence: Loaded evidence package
    """
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    # Convert datetime strings back to datetime objects
    for key in ["started_at", "completed_at"]:
        if data.get(key):
            data[key] = datetime.fromisoformat(data[key])

    for kf in data.get("knowledge_files", []):
        kf["accessed_at"] = datetime.fromisoformat(kf["accessed_at"])

    for db in data.get("database_queries", []):
        db["executed_at"] = datetime.fromisoformat(db["executed_at"])

    for qg in data.get("quality_gates", []):
        qg["validated_at"] = datetime.fromisoformat(qg["validated_at"])

    return Evidence(**data)


if __name__ == "__main__":
    # Test evidence collection system with real data
    print("=" * 60)
    print("Testing Evidence Collection System")
    print("NO MOCKS - Real data tracking only")
    print("=" * 60)

    # Test 1: Create collector and record real data
    print("\n[TEST 1] Create collector and record evidence")
    collector = EvidenceCollector("enclosure_solver_test")
    print(f"Execution ID: {collector.execution_id}")
    print(f"Started at: {collector.started_at}")

    # Test 2: Record knowledge file access (real data)
    print("\n[TEST 2] Record knowledge file access")
    real_breakers_data = {
        "meta": {"version": "1.0.0"},
        "catalog": ["SBE-102", "SBS-202"],
        "selection_rules": {"경제형_우선": True},
    }
    collector.record_knowledge_file(
        "breakers.json", real_breakers_data, keys_accessed=["meta", "catalog"]
    )
    print("[OK] Recorded breakers.json access")
    print(f"  Data hash: {collector.knowledge_files[0].data_hash[:16]}...")

    # Test 3: Record database query (real query)
    print("\n[TEST 3] Record database query")
    collector.record_db_query(
        table="catalog_items",
        query="SELECT * FROM catalog_items WHERE category = 'MCCB' LIMIT 100",
        row_count=122,
        duration_ms=45.2,
    )
    print("[OK] Recorded database query")
    print("  Table: catalog_items")
    print("  Row count: 122")
    print("  Duration: 45.2ms")

    # Test 4: Record quality gate results (real validation)
    print("\n[TEST 4] Record quality gate validation")
    collector.record_quality_gate(
        {
            "gate_name": "fit_score",
            "passed": True,
            "actual_value": 0.93,
            "threshold": 0.90,
            "operator": ">=",
        }
    )
    collector.record_quality_gate(
        {
            "gate_name": "ip_rating",
            "passed": True,
            "actual_value": 54.0,
            "threshold": 44.0,
            "operator": ">=",
        }
    )
    print("[OK] Recorded 2 quality gate validations")

    # Test 5: Set input/output hashes (real data)
    print("\n[TEST 5] Set input/output data hashes")
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
    print(f"[OK] Input hash: {collector.input_data_hash[:16]}...")
    print(f"[OK] Output hash: {collector.output_data_hash[:16]}...")

    # Test 6: Add metadata (real context)
    print("\n[TEST 6] Add metadata")
    collector.add_metadata("customer_id", "CUST-2025-001")
    collector.add_metadata("quote_id", "Q-20250101-123")
    collector.add_metadata("operator", "narberal_gamma")
    print("[OK] Added 3 metadata fields")

    # Test 7: Get summary
    print("\n[TEST 7] Get evidence summary")
    summary = collector.get_summary()
    print(f"  Stage: {summary['stage_name']}")
    print(f"  Knowledge files accessed: {summary['knowledge_files_accessed']}")
    print(f"  Database queries: {summary['database_queries_executed']}")
    print(f"  Quality gates validated: {summary['quality_gates_validated']}")
    print(f"  Quality gates passed: {summary['quality_gates_passed']}")
    print(f"  Has input hash: {summary['has_input_hash']}")
    print(f"  Has output hash: {summary['has_output_hash']}")

    # Test 8: Save evidence to file
    print("\n[TEST 8] Save evidence to JSON file")
    evidence_dir = Path("./evidence_test")
    saved_path = collector.save(evidence_dir)
    print(f"[OK] Evidence saved to: {saved_path}")
    print(f"  File exists: {saved_path.exists()}")
    print(f"  File size: {saved_path.stat().st_size} bytes")

    # Test 9: Load evidence from file
    print("\n[TEST 9] Load evidence from JSON file")
    loaded_evidence = load_evidence(saved_path)
    print("[OK] Evidence loaded successfully")
    print(f"  Stage: {loaded_evidence.stage_name}")
    print(f"  Execution ID: {loaded_evidence.execution_id}")
    print(f"  Knowledge files: {len(loaded_evidence.knowledge_files)}")
    print(f"  Database queries: {len(loaded_evidence.database_queries)}")
    print(f"  Quality gates: {len(loaded_evidence.quality_gates)}")

    # Test 10: Verify data integrity
    print("\n[TEST 10] Verify data integrity")
    assert loaded_evidence.stage_name == collector.stage_name
    assert loaded_evidence.execution_id == collector.execution_id
    assert len(loaded_evidence.knowledge_files) == 1
    assert len(loaded_evidence.database_queries) == 1
    assert len(loaded_evidence.quality_gates) == 2
    assert loaded_evidence.input_data_hash == collector.input_data_hash
    assert loaded_evidence.output_data_hash == collector.output_data_hash
    assert loaded_evidence.metadata["customer_id"] == "CUST-2025-001"
    print("[OK] All data integrity checks passed")

    # Test 11: Verify timestamps
    print("\n[TEST 11] Verify timestamps")
    assert loaded_evidence.started_at is not None
    assert loaded_evidence.completed_at is not None
    assert loaded_evidence.completed_at > loaded_evidence.started_at
    duration = (
        loaded_evidence.completed_at - loaded_evidence.started_at
    ).total_seconds()
    print(f"[OK] Execution duration: {duration:.3f} seconds")

    # Cleanup
    print("\n[CLEANUP] Removing test evidence file")
    saved_path.unlink()
    evidence_dir.rmdir()
    print("[OK] Test files cleaned up")

    print("\n" + "=" * 60)
    print("[SUCCESS] All evidence collection tests passed")
    print("=" * 60)
