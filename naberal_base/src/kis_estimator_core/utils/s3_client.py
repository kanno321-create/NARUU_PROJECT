"""
S3 Client - Phase XI

Minimal boto3 wrapper for Quote PDF archiving:
- Upload PDF to S3 bucket
- Generate public/signed URL
- Graceful degradation on failure (local storage only)

Zero-Mock / Evidence-Gated / Fail-Safe
"""

import logging
import os
from datetime import datetime
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception

logger = logging.getLogger(__name__)


class S3ArchiveResult:
    """S3 Archive Result"""

    def __init__(
        self,
        success: bool,
        s3_url: str | None = None,
        error: str | None = None,
        degraded: bool = False,
    ):
        self.success = success
        self.s3_url = s3_url
        self.error = error
        self.degraded = degraded  # True if fallback to local storage only


class S3Client:
    """
    S3 Archive Client (Phase XI)

    Environment variables required:
    - S3_BUCKET: S3 bucket name
    - S3_REGION: AWS region (default: us-east-1)
    - S3_ACCESS_KEY_ID: AWS access key
    - S3_SECRET_ACCESS_KEY: AWS secret key
    - S3_ENDPOINT_URL: (Optional) Custom S3 endpoint for testing

    Graceful degradation:
    - If boto3 not available → degraded mode (local only)
    - If credentials missing → degraded mode
    - If upload fails → degraded mode + warning header
    """

    def __init__(self):
        self.enabled = BOTO3_AVAILABLE and self._check_credentials()

        if not BOTO3_AVAILABLE:
            logger.warning(
                "boto3 not available. S3 archiving disabled (graceful degradation)"
            )
            return

        if not self.enabled:
            logger.warning(
                "S3 credentials not configured. Archiving disabled (graceful degradation)"
            )
            return

        # Initialize S3 client
        self.bucket = os.getenv("S3_BUCKET")
        self.region = os.getenv("S3_REGION", "us-east-1")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL")  # For testing/MinIO

        try:
            self.client = boto3.client(
                "s3",
                aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            )
            logger.info(
                f"S3 client initialized: bucket={self.bucket}, region={self.region}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.enabled = False

    def _check_credentials(self) -> bool:
        """Check if S3 credentials are configured"""
        required_env = ["S3_BUCKET", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"]
        return all(os.getenv(var) for var in required_env)

    def upload_pdf(
        self, pdf_path: Path, quote_id: str, timestamp: str | None = None
    ) -> S3ArchiveResult:
        """
        Upload PDF to S3

        Args:
            pdf_path: Local PDF file path
            quote_id: Quote ID
            timestamp: Optional timestamp (ISO8601 format)

        Returns:
            S3ArchiveResult with success status and URL
        """
        if not self.enabled:
            return S3ArchiveResult(
                success=False,
                error="S3 client not enabled (credentials missing or boto3 unavailable)",
                degraded=True,
            )

        if not pdf_path.exists():
            return S3ArchiveResult(
                success=False,
                error=f"PDF file not found: {pdf_path}",
                degraded=False,
            )

        try:
            # Generate S3 key
            ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            s3_key = f"quotes/{quote_id}/quote-{quote_id}-{ts}.pdf"

            # Upload to S3
            self.client.upload_file(
                str(pdf_path),
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": "application/pdf"},
            )

            # Generate URL
            if self.endpoint_url:
                # Custom endpoint (MinIO, etc.)
                s3_url = f"{self.endpoint_url}/{self.bucket}/{s3_key}"
            else:
                # AWS S3
                s3_url = (
                    f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"
                )

            logger.info(f"PDF uploaded to S3: {s3_url}")

            return S3ArchiveResult(success=True, s3_url=s3_url)

        except NoCredentialsError:
            logger.error("S3 credentials not found")
            return S3ArchiveResult(
                success=False,
                error="S3 credentials not found",
                degraded=True,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"S3 upload failed: {error_code} - {str(e)}")
            return S3ArchiveResult(
                success=False,
                error=f"S3 upload failed: {error_code}",
                degraded=True,
            )

        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            return S3ArchiveResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                degraded=True,
            )

    def get_url(self, quote_id: str, timestamp: str) -> str | None:
        """
        Get S3 URL for uploaded PDF

        Args:
            quote_id: Quote ID
            timestamp: Upload timestamp (ISO8601 format)

        Returns:
            S3 URL or None if not enabled
        """
        if not self.enabled:
            return None

        s3_key = f"quotes/{quote_id}/quote-{quote_id}-{timestamp}.pdf"

        if self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket}/{s3_key}"
        else:
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{s3_key}"

    def presign_get_pdf(
        self,
        quote_id: str,
        evidence_hash: str,
        ttl: int,
        timestamp: str | None = None,
    ) -> tuple[str, str, str]:
        """
        Generate pre-signed GET URL for PDF (Phase XII)

        Args:
            quote_id: Quote ID
            evidence_hash: Evidence hash for PDF
            ttl: URL expiration time in seconds
            timestamp: Optional timestamp (ISO8601 format)

        Returns:
            Tuple of (url, expires_at ISO8601, storage_mode)
            - If S3 enabled: (presigned_url, expires_at, "s3")
            - If S3 disabled: (local://path, "never", "local")
        """
        from datetime import datetime, timedelta

        ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat() + "Z"

        # Graceful degradation: local mode if S3 disabled
        if not self.enabled:
            local_url = f"local://out/pdf/quote-{quote_id}.pdf"
            return (local_url, "never", "local")

        try:
            s3_key = f"quotes/{quote_id}/quote-{quote_id}-{ts}.pdf"

            # Generate pre-signed URL
            presigned_url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=ttl,
            )

            logger.info(f"Pre-signed URL generated for {quote_id}: expires in {ttl}s")
            return (presigned_url, expires_at, "s3")

        except Exception as e:
            logger.error(f"Failed to generate pre-signed URL: {e}")
            # Fallback to local mode
            local_url = f"local://out/pdf/quote-{quote_id}.pdf"
            return (local_url, "never", "local")


# Global S3 client instance (lazy initialization)
_s3_client: S3Client | None = None


def get_s3_client() -> S3Client:
    """Get global S3 client instance"""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client
