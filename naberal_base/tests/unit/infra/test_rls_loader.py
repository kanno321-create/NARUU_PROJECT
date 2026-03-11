"""
P4-2.4: RLS Loader Tests
Target: rls_loader.py 0% → 50% coverage (~69/137 statements)

Tests RLS Policy Loader (SB-02 compliance):
- RLSPolicyLoader: load_policy_file, apply_policies, verify_policies
- High-level API: apply_rls_policies, verify_rls_policies
- File operations: FileNotFoundError, empty file, valid SQL
- Database operations: dry_run mode, policy application, verification queries

SB-02 Compliance: RLS policies from single source of truth (core/ssot/rls/*)
@requires_db: Some tests require real database connection (marked with fixture)
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch

from kis_estimator_core.infra.rls_loader import (
    RLSPolicyLoader,
    apply_rls_policies,
    verify_rls_policies,
    DEFAULT_POLICY_FILE,
)

# Import module explicitly for coverage measurement
from kis_estimator_core.infra import rls_loader as _  # noqa: F401


@pytest.fixture
def mock_database_url():
    """Mock DATABASE_URL environment variable."""
    test_url = "postgresql+asyncpg://user:pass@localhost/testdb"
    with patch.dict(os.environ, {"DATABASE_URL": test_url}):
        yield test_url


@pytest.fixture
def sample_rls_sql():
    """Sample RLS policy SQL content."""
    return """
-- Enable RLS on tables
ALTER TABLE kis_beta.epdl_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE kis_beta.execution_history ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own plans"
ON kis_beta.epdl_plans FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Service role full access"
ON kis_beta.epdl_plans FOR ALL
TO service_role
USING (true);
"""


class TestRLSPolicyLoaderInit:
    """RLSPolicyLoader initialization tests"""

    def test_init_with_env_var(self, mock_database_url):
        """Initialize with DATABASE_URL from env - PASS"""
        loader = RLSPolicyLoader()

        assert loader.database_url == mock_database_url
        assert loader.engine is None

    def test_init_with_explicit_url(self):
        """Initialize with explicit database_url parameter - PASS"""
        custom_url = "postgresql+asyncpg://custom:url@localhost/db"
        loader = RLSPolicyLoader(database_url=custom_url)

        assert loader.database_url == custom_url
        assert loader.engine is None

    def test_init_without_url_raises_error(self):
        """Initialize without DATABASE_URL raises ValueError - FAIL"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="DATABASE_URL environment variable not set"
            ):
                RLSPolicyLoader()


class TestLoadPolicyFile:
    """load_policy_file tests"""

    def test_load_policy_file_success(
        self, mock_database_url, sample_rls_sql, tmp_path
    ):
        """Load valid policy file - PASS"""
        # Create temporary policy file
        policy_file = tmp_path / "test_policies.sql"
        policy_file.write_text(sample_rls_sql, encoding="utf-8")

        loader = RLSPolicyLoader()

        with patch(
            "kis_estimator_core.infra.rls_loader.RLS_POLICIES_DIR", tmp_path
        ):
            sql_content = loader.load_policy_file("test_policies.sql")

        assert sql_content == sample_rls_sql
        assert "ENABLE ROW LEVEL SECURITY" in sql_content
        assert "CREATE POLICY" in sql_content

    def test_load_policy_file_not_found(self, mock_database_url, tmp_path):
        """Load nonexistent file raises FileNotFoundError - FAIL"""
        loader = RLSPolicyLoader()

        with patch(
            "kis_estimator_core.infra.rls_loader.RLS_POLICIES_DIR", tmp_path
        ):
            with pytest.raises(FileNotFoundError, match="RLS policy file not found"):
                loader.load_policy_file("nonexistent.sql")

    def test_load_policy_file_empty(self, mock_database_url, tmp_path):
        """Load empty file raises ValueError - FAIL"""
        # Create empty policy file
        policy_file = tmp_path / "empty.sql"
        policy_file.write_text("   \n  \n", encoding="utf-8")  # Only whitespace

        loader = RLSPolicyLoader()

        with patch(
            "kis_estimator_core.infra.rls_loader.RLS_POLICIES_DIR", tmp_path
        ):
            with pytest.raises(ValueError, match="RLS policy file is empty"):
                loader.load_policy_file("empty.sql")

    def test_load_policy_file_default(
        self, mock_database_url, sample_rls_sql, tmp_path
    ):
        """Load default policy file (kpew_policies.sql) - PASS"""
        # Create default policy file
        policy_file = tmp_path / DEFAULT_POLICY_FILE
        policy_file.write_text(sample_rls_sql, encoding="utf-8")

        loader = RLSPolicyLoader()

        with patch(
            "kis_estimator_core.infra.rls_loader.RLS_POLICIES_DIR", tmp_path
        ):
            sql_content = loader.load_policy_file()  # No filename = use default

        assert sql_content == sample_rls_sql


class TestApplyPolicies:
    """apply_policies tests"""

    @pytest.mark.asyncio
    async def test_apply_policies_dry_run(self, mock_database_url, sample_rls_sql):
        """Dry run mode doesn't execute SQL - PASS"""
        loader = RLSPolicyLoader()

        result = await loader.apply_policies(sample_rls_sql, dry_run=True)

        assert result["status"] == "dry_run_complete"
        assert result["dry_run"] is True
        # SQL split by semicolon creates 2 statements (multi-line are combined)
        assert result["total_statements"] == 2
        assert result["executed"] == 0  # No execution in dry run
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_apply_policies_success(self, mock_database_url, sample_rls_sql):
        """Apply policies successfully - PASS"""
        loader = RLSPolicyLoader()

        # Mock engine with proper async context manager
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        # Mock begin() context manager
        mock_begin_cm = AsyncMock()
        mock_begin_cm.__aenter__.return_value = mock_conn
        mock_begin_cm.__aexit__.return_value = None
        mock_engine.begin.return_value = mock_begin_cm

        loader.engine = mock_engine

        result = await loader.apply_policies(sample_rls_sql, dry_run=False)

        assert result["status"] == "success"
        assert result["executed"] == result["total_statements"]
        assert len(result["errors"]) == 0
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_apply_policies_partial_failure(
        self, mock_database_url, sample_rls_sql
    ):
        """Some statements fail but others succeed - PARTIAL"""
        loader = RLSPolicyLoader()

        # Mock engine with some failures
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        # First statement succeeds, second fails (2 statements total)
        mock_conn.execute.side_effect = [
            None,  # Success
            Exception("Policy already exists"),  # Failure
        ]

        # Mock begin() context manager
        mock_begin_cm = AsyncMock()
        mock_begin_cm.__aenter__.return_value = mock_conn
        mock_begin_cm.__aexit__.return_value = None
        mock_engine.begin.return_value = mock_begin_cm

        loader.engine = mock_engine

        result = await loader.apply_policies(sample_rls_sql, dry_run=False)

        assert result["status"] == "partial_success"
        assert result["executed"] == 1  # 1 out of 2 succeeded
        assert len(result["errors"]) == 1
        assert "Policy already exists" in result["errors"][0]["error"]


class TestVerifyPolicies:
    """verify_policies tests"""

    @pytest.mark.asyncio
    async def test_verify_policies_success(self, mock_database_url):
        """Verify policies successfully - VERIFIED"""
        loader = RLSPolicyLoader()

        # Mock engine and connection
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        # Mock RLS enabled results (3 tables, all with RLS)
        mock_rls_result = AsyncMock()
        mock_rls_result.__iter__ = MagicMock(
            return_value=iter(
                [
                    ("kis_beta", "epdl_plans", True),
                    ("kis_beta", "execution_history", True),
                    ("kis_beta", "evidence_packs", True),
                ]
            )
        )

        # Mock policy counts (3 tables, each with 2+ policies)
        mock_policy_result = AsyncMock()
        mock_policy_result.__iter__ = MagicMock(
            return_value=iter(
                [
                    ("epdl_plans", 3),
                    ("execution_history", 2),
                    ("evidence_packs", 2),
                ]
            )
        )

        mock_conn.execute.side_effect = [mock_rls_result, mock_policy_result]

        # Mock connect() context manager
        mock_connect_cm = AsyncMock()
        mock_connect_cm.__aenter__.return_value = mock_conn
        mock_connect_cm.__aexit__.return_value = None
        mock_engine.connect.return_value = mock_connect_cm

        loader.engine = mock_engine

        result = await loader.verify_policies()

        assert result["status"] == "verified"
        assert len(result["rls_enabled"]) == 3
        assert len(result["policy_counts"]) == 3
        assert all(row["rls_enabled"] for row in result["rls_enabled"])

    @pytest.mark.asyncio
    async def test_verify_policies_incomplete(self, mock_database_url):
        """Verify policies incomplete (missing RLS) - INCOMPLETE"""
        loader = RLSPolicyLoader()

        # Mock engine and connection
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        # Mock RLS enabled results (only 2 tables have RLS)
        mock_rls_result = AsyncMock()
        mock_rls_result.__iter__ = MagicMock(
            return_value=iter(
                [
                    ("kis_beta", "epdl_plans", True),
                    ("kis_beta", "execution_history", False),  # RLS not enabled!
                ]
            )
        )

        # Mock policy counts
        mock_policy_result = AsyncMock()
        mock_policy_result.__iter__ = MagicMock(
            return_value=iter(
                [
                    ("epdl_plans", 2),
                ]
            )
        )

        mock_conn.execute.side_effect = [mock_rls_result, mock_policy_result]

        # Mock connect() context manager
        mock_connect_cm = AsyncMock()
        mock_connect_cm.__aenter__.return_value = mock_conn
        mock_connect_cm.__aexit__.return_value = None
        mock_engine.connect.return_value = mock_connect_cm

        loader.engine = mock_engine

        result = await loader.verify_policies()

        assert result["status"] == "incomplete"

    @pytest.mark.asyncio
    async def test_verify_policies_error(self, mock_database_url):
        """Verify policies error handling (lines 240-243)"""
        loader = RLSPolicyLoader()

        # Mock engine and connection that raises exception
        mock_engine = MagicMock()
        mock_conn = AsyncMock()

        # Simulate database error
        mock_conn.execute.side_effect = Exception("Database connection failed")

        # Mock connect() context manager
        mock_connect_cm = AsyncMock()
        mock_connect_cm.__aenter__.return_value = mock_conn
        mock_connect_cm.__aexit__.return_value = None
        mock_engine.connect.return_value = mock_connect_cm

        loader.engine = mock_engine

        result = await loader.verify_policies()

        # Check error handling (lines 240-243)
        assert result["status"] == "error"
        assert "error" in result
        assert "Database connection failed" in result["error"]


class TestHighLevelAPI:
    """High-level API tests"""

    @pytest.mark.asyncio
    async def test_apply_rls_policies_dry_run(
        self, mock_database_url, sample_rls_sql, tmp_path
    ):
        """apply_rls_policies dry run - PASS"""
        # Create policy file
        policy_file = tmp_path / DEFAULT_POLICY_FILE
        policy_file.write_text(sample_rls_sql, encoding="utf-8")

        with patch(
            "kis_estimator_core.infra.rls_loader.RLS_POLICIES_DIR", tmp_path
        ):
            result = await apply_rls_policies(dry_run=True)

        assert result["status"] == "dry_run_complete"
        assert result["dry_run"] is True
        assert (
            result["total_statements"] == 2
        )  # Multi-line SQL combined into 2 statements

    @pytest.mark.asyncio
    async def test_verify_rls_policies_api(self, mock_database_url):
        """verify_rls_policies high-level API - PASS"""
        with patch.object(
            RLSPolicyLoader, "verify_policies", new_callable=AsyncMock
        ) as mock_verify:
            mock_verify.return_value = {
                "status": "verified",
                "rls_enabled": [],
                "policy_counts": [],
            }

            result = await verify_rls_policies()

        assert result["status"] == "verified"
        mock_verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_rls_policies_success_with_verification(
        self, mock_database_url, sample_rls_sql, tmp_path
    ):
        """apply_rls_policies success with verification (lines 287-288)"""
        # Create policy file
        policy_file = tmp_path / DEFAULT_POLICY_FILE
        policy_file.write_text(sample_rls_sql, encoding="utf-8")

        with patch(
            "kis_estimator_core.infra.rls_loader.RLS_POLICIES_DIR", tmp_path
        ):
            # Setup engine mock
            mock_engine = MagicMock()
            mock_engine.dispose = AsyncMock()  # close() needs async dispose
            mock_conn = AsyncMock()

            # Mock begin() for apply_policies
            mock_begin_cm = AsyncMock()
            mock_begin_cm.__aenter__.return_value = mock_conn
            mock_begin_cm.__aexit__.return_value = None
            mock_engine.begin.return_value = mock_begin_cm

            # Mock connect() for verify_policies
            mock_verify_conn = AsyncMock()
            mock_rls_result = AsyncMock()
            mock_rls_result.__iter__ = MagicMock(
                return_value=iter(
                    [
                        ("kis_beta", "epdl_plans", True),
                    ]
                )
            )
            mock_policy_result = AsyncMock()
            mock_policy_result.__iter__ = MagicMock(
                return_value=iter(
                    [
                        ("epdl_plans", 3),
                    ]
                )
            )
            mock_verify_conn.execute.side_effect = [mock_rls_result, mock_policy_result]

            mock_connect_cm = AsyncMock()
            mock_connect_cm.__aenter__.return_value = mock_verify_conn
            mock_connect_cm.__aexit__.return_value = None
            mock_engine.connect.return_value = mock_connect_cm

            # Patch engine creation
            with patch(
                "kis_estimator_core.infra.rls_loader.create_async_engine",
                return_value=mock_engine,
            ):
                result = await apply_rls_policies(dry_run=False)

        # Verify that verification was executed (lines 287-288)
        assert "verification" in result
        assert (
            result["verification"]["status"] == "incomplete"
        )  # Only 1 table instead of 3


class TestEngineManagement:
    """Engine lifecycle management tests"""

    @pytest.mark.asyncio
    async def test_get_engine_creates_once(self, mock_database_url):
        """_get_engine creates engine only once - PASS"""
        loader = RLSPolicyLoader()

        with patch(
            "kis_estimator_core.infra.rls_loader.create_async_engine"
        ) as mock_create:
            mock_engine = AsyncMock()
            mock_create.return_value = mock_engine

            # First call creates engine
            engine1 = await loader._get_engine()
            assert engine1 == mock_engine
            assert mock_create.call_count == 1

            # Second call returns same engine
            engine2 = await loader._get_engine()
            assert engine2 == mock_engine
            assert mock_create.call_count == 1  # Not called again

    @pytest.mark.asyncio
    async def test_close_disposes_engine(self, mock_database_url):
        """close() disposes engine - PASS"""
        loader = RLSPolicyLoader()

        # Create mock engine
        mock_engine = AsyncMock()
        loader.engine = mock_engine

        await loader.close()

        mock_engine.dispose.assert_called_once()
        assert loader.engine is None
