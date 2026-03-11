"""
Journal Repository
분개장 CRUD + 잔액/시산표 조회
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional, List
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.models.accounting_models import JournalEntryFilter


class JournalRepository:
    """
    Journal 리포지토리

    Dual-DSN 패턴:
    - Alembic: psycopg2 (마이그레이션)
    - App: asyncpg (런타임)
    """

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in ("id", "journal_entry_id", "account_id", "voucher_id", "customer_id"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    async def list(
        self,
        session: AsyncSession,
        filters: JournalEntryFilter,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        """
        분개 목록 조회

        Args:
            session: AsyncSession
            filters: JournalEntryFilter
            skip: offset
            limit: limit

        Returns:
            List of JournalEntry dicts (items 미포함)
        """
        where_clauses = []
        params = {"skip": skip, "limit": limit}

        if filters.start_date is not None:
            where_clauses.append("je.entry_date >= :start_date")
            params["start_date"] = filters.start_date

        if filters.end_date is not None:
            where_clauses.append("je.entry_date <= :end_date")
            params["end_date"] = filters.end_date

        if filters.status is not None:
            where_clauses.append("je.status = :status")
            params["status"] = filters.status.value

        if filters.voucher_id is not None:
            where_clauses.append("je.voucher_id = :voucher_id")
            params["voucher_id"] = filters.voucher_id

        if filters.account_id is not None:
            where_clauses.append("""
                EXISTS (
                    SELECT 1 FROM erp.erp_journal_items ji
                    WHERE ji.journal_entry_id = je.id
                    AND ji.account_id = :account_id
                )
            """)
            params["account_id"] = filters.account_id

        if filters.search:
            where_clauses.append(
                "(je.narration ILIKE :search OR je.entry_number ILIKE :search)"
            )
            params["search"] = f"%{filters.search}%"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(f"""
            SELECT
                je.id, je.entry_number, je.entry_date, je.narration,
                je.voucher_id, je.total_debit, je.total_credit,
                je.status, je.created_at, je.updated_at
            FROM erp.erp_journal_entries je
            WHERE {where_sql}
            ORDER BY je.entry_date DESC, je.entry_number DESC
            OFFSET :skip
            LIMIT :limit
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()

        return [self._row_to_dict(row) for row in rows]

    async def get(self, session: AsyncSession, id: str) -> Optional[dict]:
        """
        분개 단일 조회 (items JOIN 포함)

        Args:
            session: AsyncSession
            id: JournalEntry ID

        Returns:
            JournalEntry dict with items or None
        """
        # 분개 헤더 조회
        header_query = text("""
            SELECT
                je.id, je.entry_number, je.entry_date, je.narration,
                je.voucher_id, je.total_debit, je.total_credit,
                je.status, je.created_at, je.updated_at
            FROM erp.erp_journal_entries je
            WHERE je.id = :id
        """)

        result = await session.execute(header_query, {"id": id})
        header_row = result.mappings().first()

        if not header_row:
            return None

        entry = self._row_to_dict(header_row)

        # 분개 항목 조회 (계정정보 JOIN)
        items_query = text("""
            SELECT
                ji.id, ji.journal_entry_id, ji.account_id,
                a.account_code, a.account_name,
                ji.debit, ji.credit,
                ji.customer_id,
                c.name AS customer_name,
                ji.description
            FROM erp.erp_journal_items ji
            JOIN erp.erp_accounts a ON a.id = ji.account_id
            LEFT JOIN erp.customers c ON c.id = ji.customer_id
            WHERE ji.journal_entry_id = :id
            ORDER BY ji.debit DESC, ji.credit DESC
        """)

        items_result = await session.execute(items_query, {"id": id})
        items_rows = items_result.mappings().all()

        entry["items"] = [self._row_to_dict(row) for row in items_rows]

        return entry

    async def create_entry(
        self, session: AsyncSession, entry_data: dict, items_data: List[dict]
    ) -> dict:
        """
        분개 생성 (entry + items)

        Args:
            session: AsyncSession
            entry_data: 분개 헤더 정보
            items_data: 분개 항목 목록

        Returns:
            Created JournalEntry dict with items
        """
        # 1. 분개번호 자동 생성
        no_query = text("SELECT kis_beta.next_journal_no() AS entry_number")
        no_result = await session.execute(no_query)
        entry_number = no_result.mappings().first()["entry_number"]

        # 2. 합계 계산
        total_debit = sum(item["debit"] for item in items_data)
        total_credit = sum(item["credit"] for item in items_data)

        # 3. 분개 헤더 생성
        header_query = text("""
            INSERT INTO erp.erp_journal_entries (
                id, entry_number, entry_date, narration,
                voucher_id, total_debit, total_credit,
                status, created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :entry_number, :entry_date, :narration,
                :voucher_id, :total_debit, :total_credit,
                'draft', timezone('utc', now()), timezone('utc', now())
            )
            RETURNING
                id, entry_number, entry_date, narration,
                voucher_id, total_debit, total_credit,
                status, created_at, updated_at
        """)

        header_result = await session.execute(header_query, {
            "entry_number": entry_number,
            "entry_date": entry_data["entry_date"],
            "narration": entry_data["narration"],
            "voucher_id": entry_data.get("voucher_id"),
            "total_debit": total_debit,
            "total_credit": total_credit,
        })

        header_row = header_result.mappings().first()
        if not header_row:
            raise RuntimeError("Failed to create journal entry")

        entry = self._row_to_dict(header_row)
        entry_id = entry["id"]

        # 4. 분개 항목 생성
        items = []
        for item in items_data:
            item_query = text("""
                INSERT INTO erp.erp_journal_items (
                    id, journal_entry_id, account_id,
                    debit, credit, customer_id, description
                ) VALUES (
                    gen_random_uuid(), :journal_entry_id, :account_id,
                    :debit, :credit, :customer_id, :description
                )
                RETURNING
                    id, journal_entry_id, account_id,
                    debit, credit, customer_id, description
            """)

            item_result = await session.execute(item_query, {
                "journal_entry_id": entry_id,
                "account_id": item["account_id"],
                "debit": item["debit"],
                "credit": item["credit"],
                "customer_id": item.get("customer_id"),
                "description": item.get("description"),
            })

            item_row = item_result.mappings().first()
            if not item_row:
                raise RuntimeError("Failed to create journal item")

            items.append(self._row_to_dict(item_row))

        entry["items"] = items
        return entry

    async def update_status(
        self, session: AsyncSession, id: str, status: str
    ) -> Optional[dict]:
        """
        분개 상태 변경

        Args:
            session: AsyncSession
            id: JournalEntry ID
            status: 새 상태 (draft/posted/cancelled)

        Returns:
            Updated JournalEntry dict or None
        """
        query = text("""
            UPDATE erp.erp_journal_entries
            SET status = :status, updated_at = timezone('utc', now())
            WHERE id = :id
            RETURNING
                id, entry_number, entry_date, narration,
                voucher_id, total_debit, total_credit,
                status, created_at, updated_at
        """)

        result = await session.execute(query, {"id": id, "status": status})
        row = result.mappings().first()

        if not row:
            return None

        return self._row_to_dict(row)

    async def get_account_balance(
        self,
        session: AsyncSession,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        계정별 잔액 조회

        Args:
            session: AsyncSession
            account_id: Account ID
            start_date: 시작일 (선택)
            end_date: 종료일 (선택)

        Returns:
            {account_id, debit_total, credit_total, balance}
        """
        where_clauses = [
            "ji.account_id = :account_id",
            "je.status = 'posted'",
        ]
        params = {"account_id": account_id}

        if start_date is not None:
            where_clauses.append("je.entry_date >= :start_date")
            params["start_date"] = start_date

        if end_date is not None:
            where_clauses.append("je.entry_date <= :end_date")
            params["end_date"] = end_date

        where_sql = " AND ".join(where_clauses)

        query = text(f"""
            SELECT
                COALESCE(SUM(ji.debit), 0) AS debit_total,
                COALESCE(SUM(ji.credit), 0) AS credit_total
            FROM erp.erp_journal_items ji
            JOIN erp.erp_journal_entries je ON je.id = ji.journal_entry_id
            WHERE {where_sql}
        """)

        result = await session.execute(query, params)
        row = result.mappings().first()

        debit_total = float(row["debit_total"])
        credit_total = float(row["credit_total"])

        return {
            "account_id": account_id,
            "debit_total": debit_total,
            "credit_total": credit_total,
            "balance": debit_total - credit_total,
        }

    async def get_trial_balance(
        self, session: AsyncSession, as_of_date: date
    ) -> List[dict]:
        """
        시산표 조회 (posted 분개만)

        Args:
            session: AsyncSession
            as_of_date: 기준일

        Returns:
            List of {account_id, account_code, account_name, account_type,
                      debit_total, credit_total, balance}
        """
        query = text("""
            SELECT
                a.id AS account_id,
                a.account_code,
                a.account_name,
                a.account_type,
                COALESCE(SUM(ji.debit), 0) AS debit_total,
                COALESCE(SUM(ji.credit), 0) AS credit_total,
                COALESCE(SUM(ji.debit), 0) - COALESCE(SUM(ji.credit), 0) AS balance
            FROM erp.erp_accounts a
            LEFT JOIN erp.erp_journal_items ji ON ji.account_id = a.id
            LEFT JOIN erp.erp_journal_entries je ON je.id = ji.journal_entry_id
                AND je.status = 'posted'
                AND je.entry_date <= :as_of_date
            WHERE a.is_active = true
            GROUP BY a.id, a.account_code, a.account_name, a.account_type
            HAVING COALESCE(SUM(ji.debit), 0) != 0 OR COALESCE(SUM(ji.credit), 0) != 0
            ORDER BY a.account_code ASC
        """)

        result = await session.execute(query, {"as_of_date": as_of_date})
        rows = result.mappings().all()

        results = []
        for row in rows:
            data = dict(row)
            data["account_id"] = str(data["account_id"])
            data["debit_total"] = float(data["debit_total"])
            data["credit_total"] = float(data["credit_total"])
            data["balance"] = float(data["balance"])
            results.append(data)

        return results
