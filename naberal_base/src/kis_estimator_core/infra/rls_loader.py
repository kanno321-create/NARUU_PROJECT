"""
RLS Policy Loader - Supabase Row Level Security Policy Management
==================================================================

Purpose: Load and apply RLS policies from core/ssot/rls/** to Supabase database
Compliance: SB-02 (RLS policies loaded from single source of truth)

Usage:
    # Command-line execution
    python -m src.kis_estimator_core.infra.rls_loader --apply

    # Programmatic usage
    from kis_estimator_core.infra.rls_loader import apply_rls_policies
    result = await apply_rls_policies()
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Import from SSOT (LAW-02: Single Source of Truth)
from kis_estimator_core.core.ssot.constants import (
    DEFAULT_POLICY_FILE,
    RLS_POLICIES_BASE_DIR,
)

logger = logging.getLogger(__name__)


# ==========================================================================
# CONSTANTS (Computed from SSOT base)
# ==========================================================================
RLS_POLICIES_DIR = Path(__file__).parent.parent / RLS_POLICIES_BASE_DIR


# ==========================================================================
# RLS POLICY LOADER
# ==========================================================================
class RLSPolicyLoader:
    """
    Load RLS policies from core/ssot/rls/** and apply to Supabase database.

    SB-02 Compliance: RLS policies must be loaded from SSOT, not hardcoded.
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize RLS policy loader.

        Args:
            database_url: Database connection URL (defaults to DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Cannot apply RLS policies without database connection."
            )

        self.engine: AsyncEngine | None = None

    async def _get_engine(self) -> AsyncEngine:
        """Get or create async engine for database operations."""
        if self.engine is None:
            self.engine = create_async_engine(
                self.database_url, echo=False, pool_pre_ping=True
            )
        return self.engine

    async def close(self):
        """Close database engine."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None

    def load_policy_file(self, filename: str = DEFAULT_POLICY_FILE) -> str:
        """
        Load RLS policy SQL from file.

        Args:
            filename: Policy file name (default: kpew_policies.sql)

        Returns:
            SQL content as string

        Raises:
            FileNotFoundError: If policy file not found
        """
        policy_path = RLS_POLICIES_DIR / filename

        if not policy_path.exists():
            raise FileNotFoundError(
                f"RLS policy file not found: {policy_path}\n"
                f"Expected location: {RLS_POLICIES_DIR}\n"
                "Ensure core/ssot/rls/kpew_policies.sql exists."
            )

        logger.info(f"Loading RLS policies from: {policy_path}")

        with open(policy_path, encoding="utf-8") as f:
            sql_content = f.read()

        if not sql_content.strip():
            raise ValueError(f"RLS policy file is empty: {policy_path}")

        return sql_content

    async def apply_policies(self, sql_content: str, dry_run: bool = False) -> dict:
        """
        Apply RLS policies to database.

        Args:
            sql_content: SQL statements to execute
            dry_run: If True, only validate SQL without executing

        Returns:
            Result dictionary with status, statements executed, and any errors
        """
        engine = await self._get_engine()

        # Split SQL into individual statements (naive split by semicolon)
        # More sophisticated parsing would be needed for production
        statements = [
            stmt.strip()
            for stmt in sql_content.split(";")
            if stmt.strip() and not stmt.strip().startswith("--")
        ]

        result = {
            "status": "pending",
            "dry_run": dry_run,
            "total_statements": len(statements),
            "executed": 0,
            "errors": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        if dry_run:
            logger.info(f"DRY RUN: Would execute {len(statements)} SQL statements")
            result["status"] = "dry_run_complete"
            return result

        logger.info(f"Applying {len(statements)} RLS policy statements...")

        async with engine.begin() as conn:
            for idx, stmt in enumerate(statements, 1):
                try:
                    logger.debug(
                        f"Executing statement {idx}/{len(statements)}: {stmt[:100]}..."
                    )
                    await conn.execute(text(stmt))
                    result["executed"] += 1

                except Exception as e:
                    error_info = {
                        "statement_index": idx,
                        "statement": stmt[:200],  # First 200 chars for debugging
                        "error": str(e),
                    }
                    result["errors"].append(error_info)
                    logger.error(f"Error executing statement {idx}: {e}")

                    # Continue with other statements (don't fail fast)
                    # Some errors may be acceptable (e.g., "policy already exists")

        if result["errors"]:
            result["status"] = "partial_success"
            logger.warning(
                f"Applied {result['executed']}/{result['total_statements']} statements "
                f"with {len(result['errors'])} errors"
            )
        else:
            result["status"] = "success"
            logger.info(
                f"Successfully applied all {result['executed']} RLS policy statements"
            )

        return result

    async def verify_policies(self) -> dict:
        """
        Verify RLS policies are correctly applied.

        Returns:
            Verification result with RLS status and policy counts
        """
        engine = await self._get_engine()

        verification_queries = {
            "rls_enabled": """
                SELECT schemaname, tablename, rowsecurity
                FROM pg_tables
                WHERE tablename IN ('epdl_plans', 'execution_history', 'evidence_packs')
                  AND schemaname = 'kis_beta'
            """,
            "policies_count": """
                SELECT tablename, COUNT(*) as policy_count
                FROM pg_policies
                WHERE tablename IN ('epdl_plans', 'execution_history', 'evidence_packs')
                  AND schemaname = 'kis_beta'
                GROUP BY tablename
            """,
        }

        result = {
            "status": "pending",
            "rls_enabled": [],
            "policy_counts": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        async with engine.connect() as conn:
            try:
                # Check RLS enabled
                rls_result = await conn.execute(
                    text(verification_queries["rls_enabled"])
                )
                result["rls_enabled"] = [
                    {"schema": row[0], "table": row[1], "rls_enabled": row[2]}
                    for row in rls_result
                ]

                # Check policy counts
                policy_result = await conn.execute(
                    text(verification_queries["policies_count"])
                )
                result["policy_counts"] = [
                    {"table": row[0], "count": row[1]} for row in policy_result
                ]

                # Determine overall status
                all_tables_have_rls = len(result["rls_enabled"]) == 3 and all(
                    row["rls_enabled"] for row in result["rls_enabled"]
                )
                all_tables_have_policies = len(result["policy_counts"]) == 3 and all(
                    row["count"] >= 2
                    for row in result["policy_counts"]  # At least 2 policies per table
                )

                if all_tables_have_rls and all_tables_have_policies:
                    result["status"] = "verified"
                else:
                    result["status"] = "incomplete"

            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
                logger.error(f"Error verifying RLS policies: {e}")

        return result


# ==========================================================================
# HIGH-LEVEL API
# ==========================================================================
async def apply_rls_policies(
    database_url: str | None = None,
    policy_file: str = DEFAULT_POLICY_FILE,
    dry_run: bool = False,
) -> dict:
    """
    Load and apply RLS policies from core/ssot/rls/** to database.

    Args:
        database_url: Database connection URL (defaults to DATABASE_URL env var)
        policy_file: RLS policy file name (default: kpew_policies.sql)
        dry_run: If True, only validate without executing

    Returns:
        Result dictionary with status and details

    Example:
        >>> result = await apply_rls_policies(dry_run=True)
        >>> print(result["status"])
        'dry_run_complete'

        >>> result = await apply_rls_policies()
        >>> print(result["status"])
        'success'
    """
    loader = RLSPolicyLoader(database_url)

    try:
        # Load policies from SSOT
        sql_content = loader.load_policy_file(policy_file)

        # Apply policies
        apply_result = await loader.apply_policies(sql_content, dry_run)

        # Verify if not dry run
        if not dry_run and apply_result["status"] in ("success", "partial_success"):
            verification = await loader.verify_policies()
            apply_result["verification"] = verification

        return apply_result

    finally:
        await loader.close()


async def verify_rls_policies(database_url: str | None = None) -> dict:
    """
    Verify RLS policies are correctly applied (health check).

    Args:
        database_url: Database connection URL (defaults to DATABASE_URL env var)

    Returns:
        Verification result dictionary

    Example:
        >>> result = await verify_rls_policies()
        >>> print(result["status"])
        'verified'
    """
    loader = RLSPolicyLoader(database_url)

    try:
        return await loader.verify_policies()
    finally:
        await loader.close()


# ==========================================================================
# CLI ENTRY POINT
# ==========================================================================
async def main():
    """Command-line entry point for RLS policy management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Supabase RLS Policy Loader (SB-02 Compliance)"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply RLS policies to database"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify RLS policies are correctly applied",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (validate without executing)",
    )
    parser.add_argument(
        "--policy-file",
        default=DEFAULT_POLICY_FILE,
        help=f"Policy file name (default: {DEFAULT_POLICY_FILE})",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if args.apply:
        logger.info("=" * 60)
        logger.info("RLS POLICY APPLICATION")
        logger.info("=" * 60)

        result = await apply_rls_policies(
            policy_file=args.policy_file, dry_run=args.dry_run
        )

        print("\n" + "=" * 60)
        print(f"Status: {result['status']}")
        print(f"Executed: {result['executed']}/{result['total_statements']} statements")

        if result["errors"]:
            print(f"\nErrors: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"  - Statement {error['statement_index']}: {error['error']}")

        if "verification" in result:
            print("\nVerification:")
            print(f"  Status: {result['verification']['status']}")
            print(f"  RLS Enabled: {len(result['verification']['rls_enabled'])} tables")
            print(f"  Policies: {result['verification']['policy_counts']}")

        print("=" * 60)

    elif args.verify:
        logger.info("=" * 60)
        logger.info("RLS POLICY VERIFICATION")
        logger.info("=" * 60)

        result = await verify_rls_policies()

        print("\n" + "=" * 60)
        print(f"Status: {result['status']}")
        print("\nRLS Enabled:")
        for row in result["rls_enabled"]:
            print(f"  {row['schema']}.{row['table']}: {row['rls_enabled']}")

        print("\nPolicy Counts:")
        for row in result["policy_counts"]:
            print(f"  {row['table']}: {row['count']} policies")

        print("=" * 60)

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
