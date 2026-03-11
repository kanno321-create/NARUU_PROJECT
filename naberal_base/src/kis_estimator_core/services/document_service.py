"""
Document Service for KIS Estimator
Handles document upload to Supabase Storage and signed URL generation

Contract-First + Evidence-Gated + Zero-Mock

NO MOCKS - Real Supabase Storage operations only
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path

from kis_estimator_core.core.ssot.constants import (
    DOCUMENT_BUCKET,
    DOCUMENT_SIGNED_URL_EXPIRY,
)

logger = logging.getLogger(__name__)

# Alias for backward compatibility
SIGNED_URL_EXPIRY_SECONDS = DOCUMENT_SIGNED_URL_EXPIRY


class DocumentServiceError(Exception):
    """Document service error base class"""

    def __init__(self, message: str, code: str = "DOC_ERR"):
        self.message = message
        self.code = code
        super().__init__(message)


class DocumentService:
    """
    Document upload and URL generation service

    Responsibilities:
    - Upload Excel/PDF files to Supabase Storage
    - Generate time-limited signed URLs for download
    - Track document metadata with SHA256 hashes

    Contract: Operations.md#Security Policy
    - Signed URLs: Time-limited (300s prod / 600s staging)
    - RLS Enforcement: Writer = Service role ONLY
    """

    def __init__(self, supabase_client=None):
        """
        Initialize document service

        Args:
            supabase_client: Optional Supabase client instance
                If not provided, will attempt to get from infra
        """
        self._client = supabase_client
        logger.info("DocumentService initialized")

    @property
    def client(self):
        """Lazy-loaded Supabase client"""
        if self._client is None:
            try:
                from kis_estimator_core.infra.supabase_client import get_cached_client
                self._client = get_cached_client()
            except Exception as e:
                logger.warning(f"Supabase client not available: {e}")
                raise DocumentServiceError(
                    "Supabase client not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.",
                    code="DOC_NO_CLIENT"
                ) from e
        return self._client

    def upload_document(
        self,
        file_path: Path,
        estimate_id: str,
        document_type: str = "excel",
    ) -> tuple[str, str]:
        """
        Upload document to Supabase Storage

        Args:
            file_path: Local file path to upload
            estimate_id: Estimate ID for organizing files
            document_type: Type of document ("excel" or "pdf")

        Returns:
            Tuple[str, str]: (storage_path, sha256_hash)

        Raises:
            DocumentServiceError: If upload fails
        """
        if not file_path.exists():
            raise DocumentServiceError(
                f"File not found: {file_path}",
                code="DOC_FILE_NOT_FOUND"
            )

        # Generate storage path
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        extension = file_path.suffix.lower()
        storage_path = f"{estimate_id}/{timestamp}/{document_type}{extension}"

        # Calculate SHA256 hash
        sha256_hash = self._calculate_file_hash(file_path)

        try:
            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Upload to Supabase Storage
            self.client.storage.from_(DOCUMENT_BUCKET).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": self._get_content_type(extension),
                    "x-upsert": "true",  # Overwrite if exists
                }
            )

            logger.info(
                f"Document uploaded: bucket={DOCUMENT_BUCKET}, "
                f"path={storage_path}, hash={sha256_hash[:16]}..."
            )

            return storage_path, sha256_hash

        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            raise DocumentServiceError(
                f"Failed to upload document: {e}",
                code="DOC_UPLOAD_FAILED"
            ) from e

    def generate_signed_url(
        self,
        storage_path: str,
        expiry_seconds: int = SIGNED_URL_EXPIRY_SECONDS,
    ) -> str:
        """
        Generate time-limited signed URL for document download

        Args:
            storage_path: Path in Supabase Storage
            expiry_seconds: URL expiration time in seconds

        Returns:
            str: Signed download URL

        Raises:
            DocumentServiceError: If URL generation fails

        Contract: Operations.md#Security Policy
        - Time-limited: 300s prod / 600s staging
        """
        try:
            response = self.client.storage.from_(DOCUMENT_BUCKET).create_signed_url(
                path=storage_path,
                expires_in=expiry_seconds,
            )

            signed_url = response.get("signedURL") or response.get("signedUrl")

            if not signed_url:
                raise DocumentServiceError(
                    "No signed URL in response",
                    code="DOC_NO_SIGNED_URL"
                )

            logger.info(
                f"Signed URL generated: path={storage_path}, "
                f"expires_in={expiry_seconds}s"
            )

            return signed_url

        except DocumentServiceError:
            raise
        except Exception as e:
            logger.error(f"Signed URL generation failed: {e}")
            raise DocumentServiceError(
                f"Failed to generate signed URL: {e}",
                code="DOC_SIGNED_URL_FAILED"
            ) from e

    def upload_and_get_url(
        self,
        file_path: Path,
        estimate_id: str,
        document_type: str = "excel",
        expiry_seconds: int = SIGNED_URL_EXPIRY_SECONDS,
    ) -> tuple[str, str]:
        """
        Upload document and generate signed URL in one operation

        Args:
            file_path: Local file path to upload
            estimate_id: Estimate ID for organizing files
            document_type: Type of document ("excel" or "pdf")
            expiry_seconds: URL expiration time in seconds

        Returns:
            Tuple[str, str]: (signed_url, sha256_hash)
        """
        storage_path, sha256_hash = self.upload_document(
            file_path=file_path,
            estimate_id=estimate_id,
            document_type=document_type,
        )

        signed_url = self.generate_signed_url(
            storage_path=storage_path,
            expiry_seconds=expiry_seconds,
        )

        return signed_url, sha256_hash

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
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".pdf": "application/pdf",
            ".json": "application/json",
        }
        return content_types.get(extension, "application/octet-stream")


# Module-level functions for convenience

def generate_document_urls(
    excel_path: Path | None,
    pdf_path: Path | None,
    estimate_id: str,
) -> tuple[str | None, str | None, str | None]:
    """
    Generate document URLs for estimate response

    Args:
        excel_path: Path to Excel file (optional)
        pdf_path: Path to PDF file (optional)
        estimate_id: Estimate ID

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]:
            (excel_url, pdf_url, sha256_hash)

    Note:
        Returns (None, None, None) if Supabase is not configured.
        This allows local development without storage.
    """
    try:
        service = DocumentService()
        excel_url = None
        pdf_url = None
        sha256_hash = None

        if excel_path and excel_path.exists():
            excel_url, sha256_hash = service.upload_and_get_url(
                file_path=excel_path,
                estimate_id=estimate_id,
                document_type="excel",
            )

        if pdf_path and pdf_path.exists():
            pdf_url, _ = service.upload_and_get_url(
                file_path=pdf_path,
                estimate_id=estimate_id,
                document_type="pdf",
            )

        return excel_url, pdf_url, sha256_hash

    except DocumentServiceError as e:
        # Log but don't fail - allow local development
        logger.warning(f"Document URL generation skipped: {e.message}")
        return None, None, None


def generate_local_document_urls(
    excel_path: Path | None,
    pdf_path: Path | None,
    base_url: str = "/v1/documents",
) -> tuple[str | None, str | None]:
    """
    Generate local document URLs (for development without Supabase)

    Args:
        excel_path: Path to Excel file
        pdf_path: Path to PDF file
        base_url: API base URL for document endpoints

    Returns:
        Tuple[Optional[str], Optional[str]]: (excel_url, pdf_url)
    """
    excel_url = None
    pdf_url = None

    if excel_path and excel_path.exists():
        excel_url = f"{base_url}/{excel_path.name}"

    if pdf_path and pdf_path.exists():
        pdf_url = f"{base_url}/{pdf_path.name}"

    return excel_url, pdf_url
