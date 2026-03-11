"""
Account Repository
계정과목 CRUD
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.accounting_models import (
    AccountCreate,
    AccountUpdate,
    AccountFilter,
)


class AccountRepository:
    """
    Account 리포지토리

    Dual-DSN 패턴:
    - Alembic: psycopg2 (마이그레이션)
    - App: asyncpg (런타임)
    """

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in ("id", "parent_id"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    async def list(
        self,
        session: AsyncSession,
        filters: AccountFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """
        계정과목 목록 조회

        Args:
            session: AsyncSession
            filters: AccountFilter
            skip: offset
            limit: limit

        Returns:
            List of Account dicts
        """
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if filters.account_type is not None:
            where_clauses.append("account_type = :account_type")
            params["account_type"] = filters.account_type.value

        if filters.is_group is not None:
            where_clauses.append("is_group = :is_group")
            params["is_group"] = filters.is_group

        if filters.is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = filters.is_active

        if filters.parent_id is not None:
            where_clauses.append("parent_id = :parent_id")
            params["parent_id"] = filters.parent_id

        if filters.search:
            where_clauses.append(
                "(account_name ILIKE :search OR account_code ILIKE :search)"
            )
            params["search"] = f"%{filters.search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                id, account_code, account_name, account_type,
                parent_id, is_group, balance_direction,
                description, is_active, created_at, updated_at
            FROM erp.erp_accounts
            WHERE {where_sql}
            ORDER BY account_code ASC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()

        return [self._row_to_dict(row) for row in rows]

    async def get(self, session: AsyncSession, id: str) -> Optional[dict]:
        """
        계정과목 단일 조회

        Args:
            session: AsyncSession
            id: Account ID

        Returns:
            Account dict or None
        """
        query = text("""
            SELECT
                id, account_code, account_name, account_type,
                parent_id, is_group, balance_direction,
                description, is_active, created_at, updated_at
            FROM erp.erp_accounts
            WHERE id = :id
        """)

        result = await session.execute(query, {"id": id})
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_dict(row)

    async def get_by_code(self, session: AsyncSession, code: str) -> Optional[dict]:
        """
        계정코드로 조회

        Args:
            session: AsyncSession
            code: 계정코드

        Returns:
            Account dict or None
        """
        query = text("""
            SELECT
                id, account_code, account_name, account_type,
                parent_id, is_group, balance_direction,
                description, is_active, created_at, updated_at
            FROM erp.erp_accounts
            WHERE account_code = :code
        """)

        result = await session.execute(query, {"code": code})
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_dict(row)

    async def create(self, session: AsyncSession, data: AccountCreate) -> dict:
        """
        계정과목 생성

        Args:
            session: AsyncSession
            data: AccountCreate

        Returns:
            Created Account dict
        """
        query = text("""
            INSERT INTO erp.erp_accounts (
                id, account_code, account_name, account_type,
                parent_id, is_group, balance_direction,
                description, is_active,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :account_code, :account_name, :account_type,
                :parent_id, :is_group, :balance_direction,
                :description, :is_active,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, account_code, account_name, account_type,
                parent_id, is_group, balance_direction,
                description, is_active, created_at, updated_at
        """)

        result = await session.execute(query, {
            "account_code": data.account_code,
            "account_name": data.account_name,
            "account_type": data.account_type.value,
            "parent_id": data.parent_id,
            "is_group": data.is_group,
            "balance_direction": data.balance_direction.value,
            "description": data.description,
            "is_active": data.is_active,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create account")

        return self._row_to_dict(row)

    async def update(
        self, session: AsyncSession, id: str, data: AccountUpdate
    ) -> Optional[dict]:
        """
        계정과목 수정

        Args:
            session: AsyncSession
            id: Account ID
            data: AccountUpdate

        Returns:
            Updated Account dict or None
        """
        updates = []
        params = {"id": id}

        if data.account_name is not None:
            updates.append("account_name = :account_name")
            params["account_name"] = data.account_name

        if data.parent_id is not None:
            updates.append("parent_id = :parent_id")
            params["parent_id"] = data.parent_id

        if data.is_group is not None:
            updates.append("is_group = :is_group")
            params["is_group"] = data.is_group

        if data.description is not None:
            updates.append("description = :description")
            params["description"] = data.description

        if data.is_active is not None:
            updates.append("is_active = :is_active")
            params["is_active"] = data.is_active

        if not updates:
            return await self.get(session, id)

        updates.append("updated_at = timezone('utc', now())")
        update_sql = ", ".join(updates)

        query = text(f"""
            UPDATE erp.erp_accounts
            SET {update_sql}
            WHERE id = :id
            RETURNING
                id, account_code, account_name, account_type,
                parent_id, is_group, balance_direction,
                description, is_active, created_at, updated_at
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_dict(row)
