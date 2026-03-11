"""
PlanRepo - VerbSpec Plan Repository (I-3.4)

Zero-Mock: 실제 Supabase PostgreSQL 저장/로드
Supabase Canon (SB-01): AsyncSession, search_path, TIMESTAMPTZ
"""

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PlanRepo:
    """VerbSpec Plan Repository"""

    def __init__(self, session: AsyncSession):
        """
        Initialize PlanRepo

        Args:
            session: AsyncSession (Supabase Pooler or direct connection)
        """
        self.session = session

    async def save_plan(self, plan_id: str, specs: list[dict[str, Any]]) -> str:
        """
        Save VerbSpec list to database

        Args:
            plan_id: Estimate ID (EST-YYYYMMDDHHMMSS)
            specs: VerbSpec list

        Returns:
            plan_id (same as input)

        Raises:
            Exception: Database insert error
        """
        try:
            specs_json = json.dumps(specs, ensure_ascii=False)
            specs_count = len(specs)

            # SB-01: TIMESTAMPTZ with UTC
            await self.session.execute(
                text(
                    """
                    INSERT INTO verb_plans
                    (plan_id, specs_json, specs_count, is_valid, created_at, updated_at)
                    VALUES (:plan_id, :specs_json, :specs_count, :is_valid,
                            timezone('utc', now()), timezone('utc', now()))
                """
                ),
                {
                    "plan_id": plan_id,
                    "specs_json": specs_json,
                    "specs_count": specs_count,
                    "is_valid": True,
                },
            )
            await self.session.commit()

            logger.info(f"Plan saved: {plan_id}, specs_count={specs_count}")
            return plan_id

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to save plan {plan_id}: {e}")
            raise

    async def load_plan(self, plan_id: str) -> list[dict[str, Any]] | None:
        """
        Load VerbSpec list from database

        Args:
            plan_id: Estimate ID

        Returns:
            VerbSpec list or None if not found

        Raises:
            Exception: Database query error
        """
        try:
            result = await self.session.execute(
                text(
                    "SELECT specs_json, is_valid FROM verb_plans WHERE plan_id = :plan_id"
                ),
                {"plan_id": plan_id},
            )
            row = result.fetchone()

            if not row:
                logger.warning(f"Plan not found: {plan_id}")
                return None

            specs_json, is_valid = row

            if not is_valid:
                logger.warning(f"Plan {plan_id} is marked as invalid")
                return None

            # SB-01: asyncpg automatically parses JSONB to Python objects
            # specs_json is already a list, not a JSON string
            if isinstance(specs_json, str):
                specs = json.loads(specs_json)
            else:
                specs = specs_json  # Already parsed by asyncpg

            logger.info(f"Plan loaded: {plan_id}, specs_count={len(specs)}")
            return specs

        except Exception as e:
            logger.error(f"Failed to load plan {plan_id}: {e}")
            raise

    async def exists(self, plan_id: str) -> bool:
        """
        Check if plan exists

        Args:
            plan_id: Estimate ID

        Returns:
            True if exists, False otherwise
        """
        try:
            result = await self.session.execute(
                text("SELECT 1 FROM verb_plans WHERE plan_id = :plan_id LIMIT 1"),
                {"plan_id": plan_id},
            )
            row = result.fetchone()
            return row is not None

        except Exception as e:
            logger.error(f"Failed to check existence for {plan_id}: {e}")
            return False

    async def delete_plan(self, plan_id: str) -> bool:
        """
        Delete plan (for cleanup/testing)

        Args:
            plan_id: Estimate ID

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.session.execute(
                text(
                    "DELETE FROM verb_plans WHERE plan_id = :plan_id RETURNING plan_id"
                ),
                {"plan_id": plan_id},
            )
            await self.session.commit()

            deleted_row = result.fetchone()
            if deleted_row:
                logger.info(f"Plan deleted: {plan_id}")
                return True
            else:
                logger.warning(f"Plan not found for deletion: {plan_id}")
                return False

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete plan {plan_id}: {e}")
            raise
