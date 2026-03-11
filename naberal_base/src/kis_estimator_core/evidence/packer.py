"""
Evidence Pack Generator - EvidencePack.zip + SHA256SUMS.txt
Contract-First + Evidence-Gated + Zero-Mock

Generates:
- dist/EvidencePack.zip: Complete evidence artifacts
- dist/SHA256SUMS.txt: SHA256 checksums for all files
"""

import hashlib
import zipfile
from pathlib import Path
from typing import List, Dict
import json


class EvidencePacker:
    """Evidence artifact packer with SHA256 integrity verification"""

    def __init__(self, output_dir: Path = Path("dist")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_pack(
        self,
        contract_files: List[Path],
        pipeline_logs: List[Path],
        artifacts: List[Path],
    ) -> Dict[str, Path]:
        """
        Create EvidencePack.zip + SHA256SUMS.txt

        Args:
            contract_files: OpenAPI specs, contract snapshots
            pipeline_logs: Pipeline event logs (JSONL)
            artifacts: Excel, PDF outputs

        Returns:
            {
                "pack_path": Path("dist/EvidencePack.zip"),
                "checksums_path": Path("dist/SHA256SUMS.txt")
            }
        """
        pack_path = self.output_dir / "EvidencePack.zip"
        checksums_path = self.output_dir / "SHA256SUMS.txt"

        # Create zip file
        with zipfile.ZipFile(pack_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add contract files
            for file_path in contract_files:
                if file_path.exists():
                    arcname = f"contract/{file_path.name}"
                    zf.write(file_path, arcname=arcname)

            # Add pipeline logs
            for file_path in pipeline_logs:
                if file_path.exists():
                    arcname = f"pipeline/{file_path.name}"
                    zf.write(file_path, arcname=arcname)

            # Add artifacts
            for file_path in artifacts:
                if file_path.exists():
                    arcname = f"artifacts/{file_path.name}"
                    zf.write(file_path, arcname=arcname)

        # Generate SHA256 checksums
        checksums = self._generate_checksums([pack_path] + contract_files + pipeline_logs + artifacts)

        # Write checksums file
        with open(checksums_path, "w", encoding="utf-8") as f:
            for file_path, checksum in checksums.items():
                f.write(f"{checksum}  {file_path}\n")

        return {
            "pack_path": pack_path,
            "checksums_path": checksums_path,
            "file_count": len(contract_files) + len(pipeline_logs) + len(artifacts),
            "pack_size_bytes": pack_path.stat().st_size,
        }

    def _generate_checksums(self, files: List[Path]) -> Dict[str, str]:
        """Generate SHA256 checksums for files"""
        checksums = {}
        for file_path in files:
            if file_path.exists():
                checksum = self._sha256(file_path)
                checksums[str(file_path.name)] = checksum
        return checksums

    def _sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def verify_pack(self, pack_path: Path, checksums_path: Path) -> bool:
        """Verify EvidencePack integrity using SHA256SUMS.txt"""
        if not pack_path.exists() or not checksums_path.exists():
            return False

        # Read expected checksums
        expected = {}
        with open(checksums_path, "r", encoding="utf-8") as f:
            for line in f:
                checksum, filename = line.strip().split("  ", 1)
                expected[filename] = checksum

        # Verify pack checksum
        actual_checksum = self._sha256(pack_path)
        expected_checksum = expected.get(pack_path.name)

        if actual_checksum != expected_checksum:
            return False

        return True