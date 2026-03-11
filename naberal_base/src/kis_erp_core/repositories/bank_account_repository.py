"""
BankAccount Repository
은행계좌 CRUD (erp_bank_accounts)
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class BankAccountRepository:
    """은행계좌 리포지토리"""

    async def create(self, session: AsyncSession, data: dict) -> dict:
        """은행계좌 생성"""
        query = text("""
            INSERT INTO erp_bank_accounts (
                id, account_no, bank_name, account_name, holder_name,
                balance, is_active, memo,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :account_no, :bank_name, :account_name, :holder_name,
                :balance, :is_active, :memo,
                timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, account_no, bank_name, account_name, holder_name,
                balance, is_active, memo, created_at, updated_at
        """)

        result = await session.execute(query, {
            "account_no": data.get("account_no", ""),
            "bank_name": data.get("bank_name", ""),
            "account_name": data.get("account_name"),
            "holder_name": data.get("holder_name"),
            "balance": data.get("balance", 0),
            "is_active": data.get("is_active", True),
            "memo": data.get("memo"),
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create bank account")

        row_dict = dict(row)
        row_dict["id"] = str(row_dict["id"])
        row_dict["balance"] = float(row_dict["balance"]) if row_dict["balance"] else 0
        return row_dict

    async def get(self, session: AsyncSession, account_id: str) -> Optional[dict]:
        """은행계좌 조회"""
        query = text("""
            SELECT
                id, account_no, bank_name, account_name, holder_name,
                balance, is_active, memo, created_at, updated_at
            FROM erp_bank_accounts
            WHERE id = :id
        """)

        result = await session.execute(query, {"id": account_id})
        row = result.mappings().first()

        if not row:
            return None

        row_dict = dict(row)
        row_dict["id"] = str(row_dict["id"])
        row_dict["balance"] = float(row_dict["balance"]) if row_dict["balance"] else 0
        return row_dict

    async def list(
        self,
        session: AsyncSession,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """은행계좌 목록 조회"""
        where_clauses = []
        params: dict = {"skip": skip, "limit": limit}

        if is_active is not None:
            where_clauses.append("is_active = :is_active")
            params["is_active"] = is_active

        if search:
            where_clauses.append(
                "(bank_name ILIKE :search OR account_no ILIKE :search OR account_name ILIKE :search)"
            )
            params["search"] = f"%{search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                id, account_no, bank_name, account_name, holder_name,
                balance, is_active, memo, created_at, updated_at
            FROM erp_bank_accounts
            WHERE {where_sql}
            ORDER BY created_at DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()

        return [
            {
                **dict(row),
                "id": str(row["id"]),
                "balance": float(row["balance"]) if row["balance"] else 0,
            }
            for row in rows
        ]

    async def update(
        self, session: AsyncSession, account_id: str, data: dict
    ) -> Optional[dict]:
        """은행계좌 수정"""
        updates = []
        params: dict = {"id": account_id}

        for field in ("account_no", "bank_name", "account_name", "holder_name", "balance", "is_active", "memo"):
            if field in data and data[field] is not None:
                updates.append(f"{field} = :{field}")
                params[field] = data[field]

        if not updates:
            return await self.get(session, account_id)

        updates.append("updated_at = timezone('utc', now())")
        update_sql = ", ".join(updates)

        query = text(f"""
            UPDATE erp_bank_accounts
            SET {update_sql}
            WHERE id = :id
            RETURNING
                id, account_no, bank_name, account_name, holder_name,
                balance, is_active, memo, created_at, updated_at
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        if not row:
            return None

        row_dict = dict(row)
        row_dict["id"] = str(row_dict["id"])
        row_dict["balance"] = float(row_dict["balance"]) if row_dict["balance"] else 0
        return row_dict

    async def delete(self, session: AsyncSession, account_id: str) -> bool:
        """은행계좌 삭제 (soft delete - is_active=false)"""
        query = text("""
            UPDATE erp_bank_accounts
            SET is_active = false, updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING id
        """)

        result = await session.execute(query, {"id": account_id})
        row = result.mappings().first()
        return row is not None
