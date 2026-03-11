"""
Evidence Service for KIS Estimator
Handles evidence pack generation, upload, and URL generation

Contract-First + Evidence-Gated + Zero-Mock

NO MOCKS - Real evidence collection and storage only
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kis_estimator_core.core.ssot.constants import (
    EVIDENCE_BUCKET,
    EVIDENCE_PACK_PREFIX,
    EVIDENCE_SIGNED_URL_EXPIRY,
)
from kis_estimator_core.infra.evidence import EvidenceCollector

logger = logging.getLogger(__name__)

# Backward compatibility alias
SIGNED_URL_EXPIRY_SECONDS = EVIDENCE_SIGNED_URL_EXPIRY


class EvidenceServiceError(Exception):
    """Evidence service error base class"""

    def __init__(self, message: str, code: str = "EVD_ERR"):
        self.message = message
        self.code = code
        super().__init__(message)


class EvidenceService:
    """
    Evidence pack generation and upload service

    Responsibilities:
    - Collect evidence from all pipeline stages
    - Generate SHA256SUMS.txt for integrity verification
    - Upload evidence pack to Supabase Storage
    - Generate time-limited signed URLs

    Contract: Operations.md#Evidence Ledger Operations
    - Zero-Mock: All file I/O and hash calculations are real
    - SHA256 verification: All files have checksums
    """

    def __init__(self, supabase_client=None):
        """
        Initialize evidence service

        Args:
            supabase_client: Optional Supabase client instance
        """
        self._client = supabase_client
        self._collectors: dict[str, EvidenceCollector] = {}
        logger.info("EvidenceService initialized")

    @property
    def client(self):
        """Lazy-loaded Supabase client"""
        if self._client is None:
            try:
                from kis_estimator_core.infra.supabase_client import get_cached_client
                self._client = get_cached_client()
            except Exception as e:
                logger.warning(f"Supabase client not available: {e}")
                raise EvidenceServiceError(
                    "Supabase client not configured for evidence storage.",
                    code="EVD_NO_CLIENT"
                ) from e
        return self._client

    def create_collector(self, stage_name: str, execution_id: str | None = None) -> EvidenceCollector:
        """
        Create evidence collector for a pipeline stage

        Args:
            stage_name: Pipeline stage name
            execution_id: Optional execution ID

        Returns:
            EvidenceCollector: New collector instance
        """
        collector = EvidenceCollector(stage_name=stage_name, execution_id=execution_id)
        self._collectors[stage_name] = collector
        return collector

    def get_collector(self, stage_name: str) -> EvidenceCollector | None:
        """Get existing collector for stage"""
        return self._collectors.get(stage_name)

    def generate_evidence_pack(
        self,
        estimate_id: str,
        workflow_phases: list[Any],
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        output_dir: Path | None = None,
    ) -> tuple[Path, str]:
        """
        Generate evidence pack from workflow execution

        Args:
            estimate_id: Estimate ID for organizing evidence
            workflow_phases: List of PhaseResult from WorkflowEngine
            input_data: Original input data
            output_data: Final output data
            output_dir: Output directory (default: out/evidence/{estimate_id})

        Returns:
            Tuple[Path, str]: (evidence_pack_path, sha256_hash)
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        if output_dir is None:
            output_dir = Path(f"out/evidence/{estimate_id}_{timestamp}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate evidence files for each phase
        evidence_files = []

        for phase in workflow_phases:
            phase_evidence = self._generate_phase_evidence(phase)
            phase_file = output_dir / f"{phase.phase.replace(' ', '_').replace(':', '_')}_evidence.json"

            with open(phase_file, "w", encoding="utf-8") as f:
                json.dump(phase_evidence, f, indent=2, ensure_ascii=False, default=str)

            evidence_files.append(phase_file)

        # 2. Generate input/output evidence
        input_file = output_dir / "input.json"
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(input_data, f, indent=2, ensure_ascii=False, default=str)
        evidence_files.append(input_file)

        output_file = output_dir / "output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        evidence_files.append(output_file)

        # 3. Generate metrics summary
        metrics = self._generate_metrics(workflow_phases, estimate_id, timestamp)
        metrics_file = output_dir / "metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)
        evidence_files.append(metrics_file)

        # 4. Generate SHA256SUMS.txt
        sha256sums = self._generate_sha256sums(evidence_files)
        sha256sums_file = output_dir / "SHA256SUMS.txt"
        with open(sha256sums_file, "w", encoding="utf-8") as f:
            f.write(sha256sums)

        # 5. Calculate pack hash (hash of SHA256SUMS.txt)
        pack_hash = self._calculate_file_hash(sha256sums_file)

        logger.info(
            f"Evidence pack generated: {output_dir}, "
            f"files={len(evidence_files)}, hash={pack_hash[:16]}..."
        )

        return output_dir, pack_hash

    def upload_evidence_pack(
        self,
        pack_dir: Path,
        estimate_id: str,
    ) -> tuple[str, str]:
        """
        Upload evidence pack to Supabase Storage

        Args:
            pack_dir: Local directory containing evidence files
            estimate_id: Estimate ID

        Returns:
            Tuple[str, str]: (signed_url, sha256_hash)
        """
        try:
            # Get all files in pack directory
            files = list(pack_dir.glob("*"))

            if not files:
                raise EvidenceServiceError(
                    f"No files in evidence pack: {pack_dir}",
                    code="EVD_EMPTY_PACK"
                )

            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            storage_prefix = f"{EVIDENCE_PACK_PREFIX}/{estimate_id}_{timestamp}"

            # Upload each file
            for file_path in files:
                if file_path.is_file():
                    storage_path = f"{storage_prefix}/{file_path.name}"

                    with open(file_path, "rb") as f:
                        file_content = f.read()

                    self.client.storage.from_(EVIDENCE_BUCKET).upload(
                        path=storage_path,
                        file=file_content,
                        file_options={
                            "content-type": self._get_content_type(file_path.suffix),
                            "x-upsert": "true",
                        }
                    )

            # Generate signed URL for SHA256SUMS.txt
            sha256sums_path = f"{storage_prefix}/SHA256SUMS.txt"
            response = self.client.storage.from_(EVIDENCE_BUCKET).create_signed_url(
                path=sha256sums_path,
                expires_in=SIGNED_URL_EXPIRY_SECONDS,
            )

            signed_url = response.get("signedURL") or response.get("signedUrl")

            if not signed_url:
                raise EvidenceServiceError(
                    "No signed URL in response",
                    code="EVD_NO_SIGNED_URL"
                )

            # Get pack hash
            sha256sums_file = pack_dir / "SHA256SUMS.txt"
            pack_hash = self._calculate_file_hash(sha256sums_file) if sha256sums_file.exists() else ""

            logger.info(
                f"Evidence pack uploaded: prefix={storage_prefix}, "
                f"files={len(files)}"
            )

            return signed_url, pack_hash

        except EvidenceServiceError:
            raise
        except Exception as e:
            logger.error(f"Evidence pack upload failed: {e}")
            raise EvidenceServiceError(
                f"Failed to upload evidence pack: {e}",
                code="EVD_UPLOAD_FAILED"
            ) from e

    def _generate_phase_evidence(self, phase) -> dict[str, Any]:
        """Generate evidence dict from PhaseResult"""
        return {
            "phase": phase.phase,
            "success": phase.success,
            "errors": [
                {
                    "code": str(getattr(e, "error_code", "UNKNOWN")),
                    "message": str(e),
                }
                for e in (phase.errors or [])
            ],
            "warnings": phase.warnings or [],
            "output_summary": self._summarize_output(phase.output),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _summarize_output(self, output: Any) -> dict[str, Any]:
        """Summarize output for evidence (avoid storing full data)"""
        if output is None:
            return {"type": "null"}
        if isinstance(output, dict):
            return {
                "type": "dict",
                "keys": list(output.keys()),
                "size": len(output),
            }
        if isinstance(output, Path):
            return {
                "type": "path",
                "path": str(output),
                "exists": output.exists() if hasattr(output, "exists") else None,
            }
        return {
            "type": type(output).__name__,
            "str": str(output)[:200],
        }

    def _generate_metrics(
        self,
        workflow_phases: list[Any],
        estimate_id: str,
        timestamp: str,
    ) -> dict[str, Any]:
        """Generate metrics summary"""
        total_phases = len(workflow_phases)
        passed_phases = sum(1 for p in workflow_phases if p.success)
        total_errors = sum(len(p.errors or []) for p in workflow_phases)
        total_warnings = sum(len(p.warnings or []) for p in workflow_phases)

        return {
            "estimate_id": estimate_id,
            "timestamp": timestamp,
            "phases": {
                "total": total_phases,
                "passed": passed_phases,
                "failed": total_phases - passed_phases,
            },
            "errors": total_errors,
            "warnings": total_warnings,
            "success": passed_phases == total_phases,
        }

    def _generate_sha256sums(self, files: list[Path]) -> str:
        """Generate SHA256SUMS.txt content"""
        lines = []
        for file_path in sorted(files):
            if file_path.is_file():
                file_hash = self._calculate_file_hash(file_path)
                lines.append(f"{file_hash}  {file_path.name}")
        return "\n".join(lines)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_content_type(self, extension: str) -> str:
        """Get MIME content type for file extension"""
        content_types = {
            ".json": "application/json",
            ".txt": "text/plain",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pdf": "application/pdf",
        }
        return content_types.get(extension, "application/octet-stream")


# Module-level functions for convenience

def generate_evidence_pack(
    estimate_id: str,
    workflow_phases: list[Any],
    input_data: dict[str, Any],
    output_data: dict[str, Any],
) -> tuple[str | None, str | None]:
    """
    Generate and optionally upload evidence pack

    Args:
        estimate_id: Estimate ID
        workflow_phases: List of PhaseResult from WorkflowEngine
        input_data: Original input data
        output_data: Final output data

    Returns:
        Tuple[Optional[str], Optional[str]]: (evidence_pack_url, sha256_hash)
        Returns (None, None) if generation fails or Supabase not configured.
    """
    try:
        service = EvidenceService()

        # Generate local evidence pack
        pack_dir, pack_hash = service.generate_evidence_pack(
            estimate_id=estimate_id,
            workflow_phases=workflow_phases,
            input_data=input_data,
            output_data=output_data,
        )

        # 로컬 경로 반환 (Supabase 미사용)
        return f"file://{pack_dir}/SHA256SUMS.txt", pack_hash

    except Exception as e:
        logger.error(f"Evidence pack generation failed: {e}")
        return None, None
