"""
Carryover Repository
기초이월 CRUD (erp_stock_carryovers + erp_balance_carryovers + erp_cash_carryovers)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional, List
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CarryoverRepository:
    """기초이월 리포지토리"""

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, 모든 UUID 필드를 str로 변환"""
        data = dict(row)
        for key in ("id", "product_id", "customer_id", "account_id"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    # ==================== 상품재고 이월 ====================

    async def list_stock(
        self,
        session: AsyncSession,
        fiscal_year: int,
        product_id: Optional[str] = None,
    ) -> List[dict]:
        """재고이월 목록 조회 (JOIN erp_products for product_name/code)"""
        where_clauses = ["sc.fiscal_year = :fiscal_year"]
        params: dict = {"fiscal_year": fiscal_year}

        if product_id is not None:
            where_clauses.append("sc.product_id = :product_id")
            params["product_id"] = product_id

        where_sql = " AND ".join(where_clauses)

        query = text(f"""
            SELECT
                sc.id, sc.fiscal_year, sc.product_id,
                p.name AS product_name, p.code AS product_code,
                sc.quantity, sc.unit_cost, sc.total_value,
                sc.carryover_date, sc.created_at
            FROM erp_stock_carryovers sc
            LEFT JOIN erp_products p ON p.id = sc.product_id
            WHERE {where_sql}
            ORDER BY sc.created_at DESC
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def create_stock(self, session: AsyncSession, data: dict) -> dict:
        """재고이월 단건 생성"""
        carryover_date = data.get("carryover_date") or date(data["fiscal_year"], 1, 1)
        quantity = float(data["quantity"])
        unit_cost = float(data["unit_cost"])
        total_value = round(quantity * unit_cost, 2)

        query = text("""
            INSERT INTO erp_stock_carryovers (
                id, fiscal_year, product_id, quantity, unit_cost,
                total_value, carryover_date, created_at
            ) VALUES (
                gen_random_uuid(), :fiscal_year, :product_id, :quantity,
                :unit_cost, :total_value, :carryover_date,
                timezone('utc', now())
            )
            RETURNING
                id, fiscal_year, product_id, quantity, unit_cost,
                total_value, carryover_date, created_at
        """)

        result = await session.execute(query, {
            "fiscal_year": data["fiscal_year"],
            "product_id": data["product_id"],
            "quantity": quantity,
            "unit_cost": unit_cost,
            "total_value": total_value,
            "carryover_date": carryover_date,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create stock carryover")

        return self._row_to_dict(row)

    async def create_stock_bulk(
        self, session: AsyncSession, items: List[dict]
    ) -> List[dict]:
        """재고이월 일괄 생성"""
        created = []
        for item in items:
            row = await self.create_stock(session, item)
            created.append(row)
        return created

    async def delete_stock(self, session: AsyncSession, carryover_id: str) -> bool:
        """재고이월 삭제"""
        query = text("""
            DELETE FROM erp_stock_carryovers
            WHERE id = :id
            RETURNING id
        """)
        result = await session.execute(query, {"id": carryover_id})
        return result.mappings().first() is not None

    # ==================== 미수/미지급금 이월 ====================

    async def list_balance(
        self,
        session: AsyncSession,
        fiscal_year: int,
        balance_type: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> List[dict]:
        """잔액이월 목록 조회 (JOIN erp_customers for customer_name)"""
        where_clauses = ["bc.fiscal_year = :fiscal_year"]
        params: dict = {"fiscal_year": fiscal_year}

        if balance_type is not None:
            where_clauses.append("bc.balance_type = :balance_type")
            params["balance_type"] = balance_type

        if customer_id is not None:
            where_clauses.append("bc.customer_id = :customer_id")
            params["customer_id"] = customer_id

        where_sql = " AND ".join(where_clauses)

        query = text(f"""
            SELECT
                bc.id, bc.fiscal_year, bc.customer_id,
                c.name AS customer_name,
                bc.balance_type, bc.amount,
                bc.carryover_date, bc.created_at
            FROM erp_balance_carryovers bc
            LEFT JOIN erp_customers c ON c.id = bc.customer_id
            WHERE {where_sql}
            ORDER BY bc.created_at DESC
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def create_balance(self, session: AsyncSession, data: dict) -> dict:
        """잔액이월 단건 생성"""
        carryover_date = data.get("carryover_date") or date(data["fiscal_year"], 1, 1)

        query = text("""
            INSERT INTO erp_balance_carryovers (
                id, fiscal_year, customer_id, balance_type,
                amount, carryover_date, created_at
            ) VALUES (
                gen_random_uuid(), :fiscal_year, :customer_id, :balance_type,
                :amount, :carryover_date, timezone('utc', now())
            )
            RETURNING
                id, fiscal_year, customer_id, balance_type,
                amount, carryover_date, created_at
        """)

        result = await session.execute(query, {
            "fiscal_year": data["fiscal_year"],
            "customer_id": data["customer_id"],
            "balance_type": data["balance_type"],
            "amount": float(data["amount"]),
            "carryover_date": carryover_date,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create balance carryover")

        return self._row_to_dict(row)

    async def create_balance_bulk(
        self, session: AsyncSession, items: List[dict]
    ) -> List[dict]:
        """잔액이월 일괄 생성"""
        created = []
        for item in items:
            row = await self.create_balance(session, item)
            created.append(row)
        return created

    async def delete_balance(self, session: AsyncSession, carryover_id: str) -> bool:
        """잔액이월 삭제"""
        query = text("""
            DELETE FROM erp_balance_carryovers
            WHERE id = :id
            RETURNING id
        """)
        result = await session.execute(query, {"id": carryover_id})
        return result.mappings().first() is not None

    # ==================== 현금잔고 이월 ====================

    async def list_cash(
        self,
        session: AsyncSession,
        fiscal_year: int,
        account_id: Optional[str] = None,
    ) -> List[dict]:
        """현금이월 목록 조회 (JOIN erp_bank_accounts for account_name)"""
        where_clauses = ["cc.fiscal_year = :fiscal_year"]
        params: dict = {"fiscal_year": fiscal_year}

        if account_id is not None:
            where_clauses.append("cc.account_id = :account_id")
            params["account_id"] = account_id

        where_sql = " AND ".join(where_clauses)

        query = text(f"""
            SELECT
                cc.id, cc.fiscal_year, cc.account_id,
                ba.account_name AS account_name,
                cc.amount, cc.carryover_date, cc.created_at
            FROM erp_cash_carryovers cc
            LEFT JOIN erp_bank_accounts ba ON ba.id = cc.account_id
            WHERE {where_sql}
            ORDER BY cc.created_at DESC
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()
        return [self._row_to_dict(row) for row in rows]

    async def create_cash(self, session: AsyncSession, data: dict) -> dict:
        """현금이월 단건 생성"""
        carryover_date = data.get("carryover_date") or date(data["fiscal_year"], 1, 1)

        query = text("""
            INSERT INTO erp_cash_carryovers (
                id, fiscal_year, account_id,
                amount, carryover_date, created_at
            ) VALUES (
                gen_random_uuid(), :fiscal_year, :account_id,
                :amount, :carryover_date, timezone('utc', now())
            )
            RETURNING
                id, fiscal_year, account_id,
                amount, carryover_date, created_at
        """)

        result = await session.execute(query, {
            "fiscal_year": data["fiscal_year"],
            "account_id": data.get("account_id"),
            "amount": float(data["amount"]),
            "carryover_date": carryover_date,
        })

        row = result.mappings().first()
        if not row:
            raise RuntimeError("Failed to create cash carryover")

        return self._row_to_dict(row)

    async def create_cash_bulk(
        self, session: AsyncSession, items: List[dict]
    ) -> List[dict]:
        """현금이월 일괄 생성"""
        created = []
        for item in items:
            row = await self.create_cash(session, item)
            created.append(row)
        return created

    async def delete_cash(self, session: AsyncSession, carryover_id: str) -> bool:
        """현금이월 삭제"""
        query = text("""
            DELETE FROM erp_cash_carryovers
            WHERE id = :id
            RETURNING id
        """)
        result = await session.execute(query, {"id": carryover_id})
        return result.mappings().first() is not None

    # ==================== 자동 이월 생성 ====================

    async def auto_generate(
        self,
        session: AsyncSession,
        fiscal_year: int,
        carryover_date: date,
    ) -> dict:
        """
        전년도 데이터 기반으로 기초이월 자동 생성

        1. 해당 회계연도의 기존 이월 데이터 삭제
        2. 재고이월: stock_qty > 0 인 상품
        3. 잔액이월: 미수금(sales-receipt) / 미지급금(purchase-payment) 잔액
        4. 현금이월: 은행계좌 잔액 + 현금
        """
        # 1. 기존 이월 데이터 삭제
        await session.execute(
            text("DELETE FROM erp_stock_carryovers WHERE fiscal_year = :fy"),
            {"fy": fiscal_year},
        )
        await session.execute(
            text("DELETE FROM erp_balance_carryovers WHERE fiscal_year = :fy"),
            {"fy": fiscal_year},
        )
        await session.execute(
            text("DELETE FROM erp_cash_carryovers WHERE fiscal_year = :fy"),
            {"fy": fiscal_year},
        )

        stock_count = 0
        balance_count = 0
        cash_count = 0

        # 2. 재고이월: stock_qty > 0 인 상품
        stock_query = text("""
            SELECT id, name, stock_qty, unit_cost
            FROM erp_products
            WHERE stock_qty > 0 AND is_active = true
        """)
        stock_result = await session.execute(stock_query)
        stock_rows = stock_result.mappings().all()

        for prod in stock_rows:
            qty = float(prod["stock_qty"])
            cost = float(prod["unit_cost"])
            total_value = round(qty * cost, 2)

            await session.execute(
                text("""
                    INSERT INTO erp_stock_carryovers (
                        id, fiscal_year, product_id, quantity, unit_cost,
                        total_value, carryover_date, created_at
                    ) VALUES (
                        gen_random_uuid(), :fiscal_year, :product_id,
                        :quantity, :unit_cost, :total_value,
                        :carryover_date, timezone('utc', now())
                    )
                """),
                {
                    "fiscal_year": fiscal_year,
                    "product_id": str(prod["id"]),
                    "quantity": qty,
                    "unit_cost": cost,
                    "total_value": total_value,
                    "carryover_date": carryover_date,
                },
            )
            stock_count += 1

        # 3. 잔액이월: 미수금/미지급금 잔액 (거래처별 집계)
        # 미수금: sales 전표 총액 - receipt 전표 총액 (거래처별)
        receivable_query = text("""
            SELECT
                v.customer_id,
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'sales' THEN v.total_amount ELSE 0 END
                ), 0) -
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'receipt' THEN v.total_amount ELSE 0 END
                ), 0) AS balance
            FROM erp_vouchers v
            WHERE v.customer_id IS NOT NULL
              AND v.status IN ('confirmed', 'posted')
              AND v.voucher_type IN ('sales', 'receipt')
            GROUP BY v.customer_id
            HAVING
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'sales' THEN v.total_amount ELSE 0 END
                ), 0) -
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'receipt' THEN v.total_amount ELSE 0 END
                ), 0) > 0
        """)
        recv_result = await session.execute(receivable_query)
        recv_rows = recv_result.mappings().all()

        for row in recv_rows:
            await session.execute(
                text("""
                    INSERT INTO erp_balance_carryovers (
                        id, fiscal_year, customer_id, balance_type,
                        amount, carryover_date, created_at
                    ) VALUES (
                        gen_random_uuid(), :fiscal_year, :customer_id,
                        'receivable', :amount, :carryover_date,
                        timezone('utc', now())
                    )
                """),
                {
                    "fiscal_year": fiscal_year,
                    "customer_id": str(row["customer_id"]),
                    "amount": float(row["balance"]),
                    "carryover_date": carryover_date,
                },
            )
            balance_count += 1

        # 미지급금: purchase 전표 총액 - payment 전표 총액 (거래처별)
        payable_query = text("""
            SELECT
                v.customer_id,
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END
                ), 0) -
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'payment' THEN v.total_amount ELSE 0 END
                ), 0) AS balance
            FROM erp_vouchers v
            WHERE v.customer_id IS NOT NULL
              AND v.status IN ('confirmed', 'posted')
              AND v.voucher_type IN ('purchase', 'payment')
            GROUP BY v.customer_id
            HAVING
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END
                ), 0) -
                COALESCE(SUM(
                    CASE WHEN v.voucher_type = 'payment' THEN v.total_amount ELSE 0 END
                ), 0) > 0
        """)
        pay_result = await session.execute(payable_query)
        pay_rows = pay_result.mappings().all()

        for row in pay_rows:
            await session.execute(
                text("""
                    INSERT INTO erp_balance_carryovers (
                        id, fiscal_year, customer_id, balance_type,
                        amount, carryover_date, created_at
                    ) VALUES (
                        gen_random_uuid(), :fiscal_year, :customer_id,
                        'payable', :amount, :carryover_date,
                        timezone('utc', now())
                    )
                """),
                {
                    "fiscal_year": fiscal_year,
                    "customer_id": str(row["customer_id"]),
                    "amount": float(row["balance"]),
                    "carryover_date": carryover_date,
                },
            )
            balance_count += 1

        # 4. 현금이월: 은행계좌 잔액
        bank_query = text("""
            SELECT id, account_name, balance
            FROM erp_bank_accounts
            WHERE is_active = true
        """)
        bank_result = await session.execute(bank_query)
        bank_rows = bank_result.mappings().all()

        for bank in bank_rows:
            balance_val = float(bank["balance"])
            if balance_val != 0:
                await session.execute(
                    text("""
                        INSERT INTO erp_cash_carryovers (
                            id, fiscal_year, account_id,
                            amount, carryover_date, created_at
                        ) VALUES (
                            gen_random_uuid(), :fiscal_year, :account_id,
                            :amount, :carryover_date, timezone('utc', now())
                        )
                    """),
                    {
                        "fiscal_year": fiscal_year,
                        "account_id": str(bank["id"]),
                        "amount": balance_val,
                        "carryover_date": carryover_date,
                    },
                )
                cash_count += 1

        return {
            "stock": stock_count,
            "balance": balance_count,
            "cash": cash_count,
        }

    # ==================== 이월 현황 요약 ====================

    async def summary(self, session: AsyncSession, fiscal_year: int) -> dict:
        """해당 회계연도의 기초이월 현황 요약"""
        # 재고이월 집계
        stock_query = text("""
            SELECT
                COUNT(*) AS count,
                COALESCE(SUM(total_value), 0) AS total_value
            FROM erp_stock_carryovers
            WHERE fiscal_year = :fiscal_year
        """)
        stock_result = await session.execute(stock_query, {"fiscal_year": fiscal_year})
        stock_row = stock_result.mappings().first()

        # 미수금 집계
        recv_query = text("""
            SELECT
                COUNT(*) AS count,
                COALESCE(SUM(amount), 0) AS total_amount
            FROM erp_balance_carryovers
            WHERE fiscal_year = :fiscal_year AND balance_type = 'receivable'
        """)
        recv_result = await session.execute(recv_query, {"fiscal_year": fiscal_year})
        recv_row = recv_result.mappings().first()

        # 미지급금 집계
        pay_query = text("""
            SELECT
                COUNT(*) AS count,
                COALESCE(SUM(amount), 0) AS total_amount
            FROM erp_balance_carryovers
            WHERE fiscal_year = :fiscal_year AND balance_type = 'payable'
        """)
        pay_result = await session.execute(pay_query, {"fiscal_year": fiscal_year})
        pay_row = pay_result.mappings().first()

        # 현금이월 집계
        cash_query = text("""
            SELECT
                COUNT(*) AS count,
                COALESCE(SUM(amount), 0) AS total_amount
            FROM erp_cash_carryovers
            WHERE fiscal_year = :fiscal_year
        """)
        cash_result = await session.execute(cash_query, {"fiscal_year": fiscal_year})
        cash_row = cash_result.mappings().first()

        return {
            "fiscal_year": fiscal_year,
            "stock": {
                "count": int(stock_row["count"]),
                "total_value": str(stock_row["total_value"]),
            },
            "receivable": {
                "count": int(recv_row["count"]),
                "total_amount": str(recv_row["total_amount"]),
            },
            "payable": {
                "count": int(pay_row["count"]),
                "total_amount": str(pay_row["total_amount"]),
            },
            "cash": {
                "count": int(cash_row["count"]),
                "total_amount": str(cash_row["total_amount"]),
            },
        }
