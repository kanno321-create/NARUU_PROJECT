"""
Report Repository
보고서 집계 SQL 쿼리 (일계표, 월별, 거래처별, 손익, 대차대조표 등)
Contract-First + Evidence-Gated + Zero-Mock

Dual-DSN 패턴:
- Alembic: psycopg2 (마이그레이션)
- App: asyncpg (런타임)
"""
from typing import Optional
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class ReportRepository:
    """보고서 집계 리포지토리"""

    # ========== 유틸 (상단 배치) ==========

    def _row_to_dict(self, row) -> dict:
        """Row를 dict로 변환, UUID 필드를 str로 변환"""
        data = dict(row)
        for key in ("id", "voucher_id", "customer_id"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        return data

    def _to_float_dict(self, row) -> dict:
        """Decimal/numeric 필드를 float로 변환"""
        if isinstance(row, dict):
            data = row
        else:
            data = dict(row)
        for key, value in data.items():
            if hasattr(value, "is_finite"):
                data[key] = float(value)
        return data

    # ========== 일계표 / 월별현황 ==========

    async def daily_summary(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """
        일별 매출/매입/수금/지급/경비 집계

        confirmed 전표만 대상. 날짜별로 voucher_type 기준 PIVOT.
        """
        query = text("""
            SELECT
                v.voucher_date AS summary_date,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales'    THEN v.total_amount ELSE 0 END), 0) AS sales_amount,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END), 0) AS purchase_amount,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'receipt'  THEN v.total_amount ELSE 0 END), 0) AS receipt_amount,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'payment'  THEN v.total_amount ELSE 0 END), 0) AS payment_amount,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'expense'  THEN v.total_amount ELSE 0 END), 0) AS expense_amount,
                COUNT(*) AS voucher_count
            FROM erp_vouchers v
            WHERE v.status = 'confirmed'
              AND v.voucher_date >= :start_date
              AND v.voucher_date <= :end_date
            GROUP BY v.voucher_date
            ORDER BY v.voucher_date ASC
        """)

        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date,
        })
        rows = result.mappings().all()
        return [self._to_float_dict(row) for row in rows]

    async def monthly_summary(
        self,
        session: AsyncSession,
        year: int,
    ) -> list[dict]:
        """
        월별 매출/매입/수금/지급/경비 + 매출총이익/순이익 집계

        confirmed 전표만 대상. 1~12월 전체 반환.
        """
        query = text("""
            WITH months AS (
                SELECT generate_series(1, 12) AS month
            ),
            aggregated AS (
                SELECT
                    EXTRACT(MONTH FROM v.voucher_date)::int AS month,
                    COALESCE(SUM(CASE WHEN v.voucher_type = 'sales'    THEN v.total_amount ELSE 0 END), 0) AS sales_amount,
                    COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END), 0) AS purchase_amount,
                    COALESCE(SUM(CASE WHEN v.voucher_type = 'receipt'  THEN v.total_amount ELSE 0 END), 0) AS receipt_amount,
                    COALESCE(SUM(CASE WHEN v.voucher_type = 'payment'  THEN v.total_amount ELSE 0 END), 0) AS payment_amount,
                    COALESCE(SUM(CASE WHEN v.voucher_type = 'expense'  THEN v.total_amount ELSE 0 END), 0) AS expense_amount
                FROM erp_vouchers v
                WHERE v.status = 'confirmed'
                  AND EXTRACT(YEAR FROM v.voucher_date) = :year
                GROUP BY EXTRACT(MONTH FROM v.voucher_date)
            )
            SELECT
                :year AS year,
                m.month,
                COALESCE(a.sales_amount, 0) AS sales_amount,
                COALESCE(a.purchase_amount, 0) AS purchase_amount,
                COALESCE(a.receipt_amount, 0) AS receipt_amount,
                COALESCE(a.payment_amount, 0) AS payment_amount,
                COALESCE(a.expense_amount, 0) AS expense_amount,
                COALESCE(a.sales_amount, 0) - COALESCE(a.purchase_amount, 0) AS gross_profit,
                COALESCE(a.sales_amount, 0) - COALESCE(a.purchase_amount, 0) - COALESCE(a.expense_amount, 0) AS net_profit
            FROM months m
            LEFT JOIN aggregated a ON a.month = m.month
            ORDER BY m.month ASC
        """)

        result = await session.execute(query, {"year": year})
        rows = result.mappings().all()
        return [self._to_float_dict(row) for row in rows]

    # ========== 거래처별 현황 ==========

    async def customer_balances(
        self,
        session: AsyncSession,
        as_of_date: date,
        include_zero: bool = False,
    ) -> list[dict]:
        """
        거래처별 매출/매입/수금/지급 합계 + 미수금/미지급금 잔액

        confirmed 전표만 대상. as_of_date 이전 전표 기준.
        """
        having_clause = "" if include_zero else """
            HAVING
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales' THEN v.total_amount ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN v.voucher_type = 'receipt' THEN v.total_amount ELSE 0 END), 0) != 0
                OR
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END), 0)
                - COALESCE(SUM(CASE WHEN v.voucher_type = 'payment' THEN v.total_amount ELSE 0 END), 0) != 0
        """

        query = text(f"""
            SELECT
                v.customer_id,
                c.name AS customer_name,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales'    THEN v.total_amount ELSE 0 END), 0) AS total_sales,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END), 0) AS total_purchase,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'receipt'  THEN v.total_amount ELSE 0 END), 0) AS total_receipt,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'payment'  THEN v.total_amount ELSE 0 END), 0) AS total_payment,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales' THEN v.total_amount ELSE 0 END), 0)
                    - COALESCE(SUM(CASE WHEN v.voucher_type = 'receipt' THEN v.total_amount ELSE 0 END), 0) AS receivable,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END), 0)
                    - COALESCE(SUM(CASE WHEN v.voucher_type = 'payment' THEN v.total_amount ELSE 0 END), 0) AS payable
            FROM erp_vouchers v
            JOIN erp_customers c ON c.id = v.customer_id
            WHERE v.status = 'confirmed'
              AND v.voucher_date <= :as_of_date
              AND v.customer_id IS NOT NULL
            GROUP BY v.customer_id, c.name
            {having_clause}
            ORDER BY c.name ASC
        """)

        result = await session.execute(query, {"as_of_date": as_of_date})
        rows = result.mappings().all()
        return [self._row_to_dict(self._to_float_dict(row)) for row in rows]

    async def customer_transactions(
        self,
        session: AsyncSession,
        customer_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        voucher_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """
        거래처별 거래 내역 + 요약 정보

        Returns:
            {customer_name, transactions: [...], summary: {...}}
        """
        where_clauses = [
            "v.customer_id = :customer_id",
            "v.status = 'confirmed'",
        ]
        params: dict = {
            "customer_id": customer_id,
            "skip": skip,
            "limit": limit,
        }

        if start_date is not None:
            where_clauses.append("v.voucher_date >= :start_date")
            params["start_date"] = start_date

        if end_date is not None:
            where_clauses.append("v.voucher_date <= :end_date")
            params["end_date"] = end_date

        if voucher_type is not None:
            where_clauses.append("v.voucher_type = :voucher_type")
            params["voucher_type"] = voucher_type

        where_sql = " AND ".join(where_clauses)

        # 거래처명 조회
        name_query = text("""
            SELECT name FROM erp_customers WHERE id = :customer_id
        """)
        name_result = await session.execute(name_query, {"customer_id": customer_id})
        name_row = name_result.mappings().first()
        customer_name = name_row["name"] if name_row else None

        # 거래 내역 조회
        tx_query = text(f"""
            SELECT
                v.id AS voucher_id,
                v.voucher_no,
                v.voucher_type,
                v.voucher_date,
                v.total_amount,
                v.paid_amount,
                v.unpaid_amount,
                v.memo
            FROM erp_vouchers v
            WHERE {where_sql}
            ORDER BY v.voucher_date DESC, v.voucher_no DESC
            OFFSET :skip
            LIMIT :limit
        """)

        tx_result = await session.execute(tx_query, params)
        tx_rows = tx_result.mappings().all()

        transactions = []
        for row in tx_rows:
            data = dict(row)
            data["voucher_id"] = str(data["voucher_id"])
            transactions.append(data)

        # 요약 집계 (skip/limit 제외)
        summary_query = text(f"""
            SELECT
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales'    THEN v.total_amount ELSE 0 END), 0) AS total_sales,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END), 0) AS total_purchase,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'receipt'  THEN v.total_amount ELSE 0 END), 0) AS total_receipt,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'payment'  THEN v.total_amount ELSE 0 END), 0) AS total_payment
            FROM erp_vouchers v
            WHERE {where_sql}
        """)

        summary_params = {k: v for k, v in params.items() if k not in ("skip", "limit")}
        summary_result = await session.execute(summary_query, summary_params)
        summary_row = summary_result.mappings().first()

        total_sales = float(summary_row["total_sales"])
        total_receipt = float(summary_row["total_receipt"])
        total_purchase = float(summary_row["total_purchase"])
        total_payment = float(summary_row["total_payment"])

        summary = {
            "total_sales": total_sales,
            "total_purchase": total_purchase,
            "total_receipt": total_receipt,
            "total_payment": total_payment,
            "net_receivable": (total_sales - total_receipt) - (total_purchase - total_payment),
        }

        return {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "transactions": transactions,
            "summary": summary,
        }

    # ========== 미수금 / 미지급금 (공통 메서드) ==========

    async def _unpaid_vouchers(
        self,
        session: AsyncSession,
        voucher_type: str,
        as_of_date: date,
        overdue_only: bool,
        total_key: str,
    ) -> dict:
        """
        미수금/미지급금 공통 집계 로직

        Args:
            voucher_type: 'sales' (미수금) or 'purchase' (미지급금)
            total_key: 'total_receivable' or 'total_payable'

        overdue_only=True 일 때 30일 초과 건만 필터.
        overdue_amount는 항상 30일 초과 기준.
        """
        overdue_clause = "AND (:as_of_date - v.voucher_date) > 30" if overdue_only else ""

        query = text(f"""
            SELECT
                v.id AS voucher_id,
                v.voucher_no,
                v.voucher_date,
                v.customer_id,
                c.name AS customer_name,
                v.total_amount,
                v.paid_amount,
                v.unpaid_amount,
                (:as_of_date - v.voucher_date) AS days_overdue
            FROM erp_vouchers v
            LEFT JOIN erp_customers c ON c.id = v.customer_id
            WHERE v.status = 'confirmed'
              AND v.voucher_type = :voucher_type
              AND v.unpaid_amount > 0
              AND v.voucher_date <= :as_of_date
              {overdue_clause}
            ORDER BY v.voucher_date ASC
        """)

        result = await session.execute(query, {
            "as_of_date": as_of_date,
            "voucher_type": voucher_type,
        })
        rows = result.mappings().all()

        details = []
        total_amount = 0.0
        overdue_amount = 0.0

        for row in rows:
            data = self._row_to_dict(self._to_float_dict(row))
            data["days_overdue"] = int(data.get("days_overdue", 0))
            total_amount += data["unpaid_amount"]
            if data["days_overdue"] > 30:
                overdue_amount += data["unpaid_amount"]
            details.append(data)

        return {
            total_key: total_amount,
            "overdue_amount": overdue_amount,
            "details": details,
        }

    async def receivables(
        self,
        session: AsyncSession,
        as_of_date: date,
        overdue_only: bool = False,
    ) -> dict:
        """미수금 현황 (매출전표 중 unpaid_amount > 0)"""
        return await self._unpaid_vouchers(
            session, "sales", as_of_date, overdue_only, "total_receivable",
        )

    async def payables(
        self,
        session: AsyncSession,
        as_of_date: date,
        overdue_only: bool = False,
    ) -> dict:
        """미지급금 현황 (매입전표 중 unpaid_amount > 0)"""
        return await self._unpaid_vouchers(
            session, "purchase", as_of_date, overdue_only, "total_payable",
        )

    # ========== 상품별 현황 (공통 메서드) ==========

    async def _product_aggregate(
        self,
        session: AsyncSession,
        voucher_type: str,
        start_date: date,
        end_date: date,
        top_n: int,
        total_key: str,
    ) -> dict:
        """
        상품별 매출/매입 공통 집계 로직

        Args:
            voucher_type: 'sales' or 'purchase'
            total_key: 'total_sales' or 'total_purchase'
        """
        query = text("""
            SELECT
                vi.product_name,
                COALESCE(SUM(vi.quantity), 0) AS total_quantity,
                COALESCE(SUM(vi.supply_price), 0) AS total_supply,
                COALESCE(SUM(vi.tax_amount), 0) AS total_tax,
                COALESCE(SUM(vi.total_amount), 0) AS total_amount
            FROM erp_voucher_items vi
            JOIN erp_vouchers v ON v.id = vi.voucher_id
            WHERE v.status = 'confirmed'
              AND v.voucher_type = :voucher_type
              AND v.voucher_date >= :start_date
              AND v.voucher_date <= :end_date
            GROUP BY vi.product_name
            ORDER BY total_amount DESC
            LIMIT :top_n
        """)

        result = await session.execute(query, {
            "voucher_type": voucher_type,
            "start_date": start_date,
            "end_date": end_date,
            "top_n": top_n,
        })
        rows = result.mappings().all()

        products = [self._to_float_dict(row) for row in rows]

        return {
            "products": products,
            total_key: sum(p["total_amount"] for p in products),
            "total_quantity": sum(p["total_quantity"] for p in products),
        }

    async def product_sales(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        top_n: int = 20,
    ) -> dict:
        """상품별 매출 집계 (매출전표 항목 기준)"""
        return await self._product_aggregate(
            session, "sales", start_date, end_date, top_n, "total_sales",
        )

    async def product_purchase(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        top_n: int = 20,
    ) -> dict:
        """상품별 매입 집계 (매입전표 항목 기준)"""
        return await self._product_aggregate(
            session, "purchase", start_date, end_date, top_n, "total_purchase",
        )

    # ========== 매출/매입 명세서 ==========

    async def statement(
        self,
        session: AsyncSession,
        voucher_type: str,
        start_date: date,
        end_date: date,
        customer_id: Optional[str] = None,
    ) -> dict:
        """
        매출/매입 명세서 (전표 목록 + 공급가액/세액/합계)

        Args:
            voucher_type: 'sales' or 'purchase'

        Returns:
            {vouchers: [...], total_supply, total_tax, total_amount}
        """
        where_clauses = [
            "v.status = 'confirmed'",
            "v.voucher_type = :voucher_type",
            "v.voucher_date >= :start_date",
            "v.voucher_date <= :end_date",
        ]
        params: dict = {
            "voucher_type": voucher_type,
            "start_date": start_date,
            "end_date": end_date,
        }

        if customer_id is not None:
            where_clauses.append("v.customer_id = :customer_id")
            params["customer_id"] = customer_id

        where_sql = " AND ".join(where_clauses)

        query = text(f"""
            SELECT
                v.id AS voucher_id,
                v.voucher_no,
                v.voucher_date,
                c.name AS customer_name,
                v.supply_amount,
                v.tax_amount,
                v.total_amount
            FROM erp_vouchers v
            LEFT JOIN erp_customers c ON c.id = v.customer_id
            WHERE {where_sql}
            ORDER BY v.voucher_date ASC, v.voucher_no ASC
        """)

        result = await session.execute(query, params)
        rows = result.mappings().all()

        vouchers = []
        total_supply = 0.0
        total_tax = 0.0
        total_amount = 0.0

        for row in rows:
            data = self._row_to_dict(self._to_float_dict(row))
            total_supply += data["supply_amount"]
            total_tax += data["tax_amount"]
            total_amount += data["total_amount"]
            vouchers.append(data)

        return {
            "vouchers": vouchers,
            "total_supply": total_supply,
            "total_tax": total_tax,
            "total_amount": total_amount,
        }

    # ========== 손익계산서 ==========

    async def profit_loss(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        손익계산서 (confirmed 전표 기반 집계)

        매출총이익 = 매출 - 매입
        순이익 = 매출총이익 - 경비
        이익률 = 순이익 / 매출 * 100

        Returns:
            {sales, cost_of_sales, gross_profit, expenses, net_profit, profit_margin}
        """
        query = text("""
            SELECT
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales'    THEN v.total_amount ELSE 0 END), 0) AS sales,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.total_amount ELSE 0 END), 0) AS cost_of_sales,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'expense'  THEN v.total_amount ELSE 0 END), 0) AS expenses
            FROM erp_vouchers v
            WHERE v.status = 'confirmed'
              AND v.voucher_date >= :start_date
              AND v.voucher_date <= :end_date
        """)

        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date,
        })
        row = result.mappings().first()

        sales = float(row["sales"])
        cost_of_sales = float(row["cost_of_sales"])
        expenses = float(row["expenses"])
        gross_profit = sales - cost_of_sales
        net_profit = gross_profit - expenses
        profit_margin = (net_profit / sales * 100) if sales > 0 else 0.0

        return {
            "sales": sales,
            "cost_of_sales": cost_of_sales,
            "gross_profit": gross_profit,
            "expenses": expenses,
            "net_profit": net_profit,
            "profit_margin": round(profit_margin, 2),
        }

    # ========== 대차대조표 ==========

    async def balance_sheet(
        self,
        session: AsyncSession,
        as_of_date: date,
    ) -> dict:
        """
        대차대조표 (posted 분개 기반)

        자산 = 부채 + 자본 검증 포함.
        결산 전표가 없으면 수익/비용이 자본에 반영되지 않아
        is_balanced=false가 될 수 있음 (정상 동작).

        Returns:
            {assets, liabilities, equity, total_assets, total_liabilities,
             total_equity, is_balanced}
        """
        query = text("""
            SELECT
                a.account_code,
                a.account_name,
                a.account_type,
                a.balance_direction,
                COALESCE(SUM(ji.debit), 0) - COALESCE(SUM(ji.credit), 0) AS net_balance
            FROM erp_accounts a
            JOIN (
                SELECT ji2.account_id, ji2.debit, ji2.credit
                FROM erp_journal_items ji2
                JOIN erp_journal_entries je ON je.id = ji2.journal_entry_id
                WHERE je.status = 'posted'
                  AND je.entry_date <= :as_of_date
            ) ji ON ji.account_id = a.id
            WHERE a.is_active = true
              AND a.account_type IN ('asset', 'liability', 'equity')
            GROUP BY a.id, a.account_code, a.account_name, a.account_type, a.balance_direction
            ORDER BY a.account_code ASC
        """)

        result = await session.execute(query, {"as_of_date": as_of_date})
        rows = result.mappings().all()

        assets = []
        liabilities = []
        equity = []
        total_assets = 0.0
        total_liabilities = 0.0
        total_equity = 0.0

        for row in rows:
            balance = float(row["net_balance"])
            # 부채/자본은 대변 잔액이므로 부호 반전
            if row["balance_direction"] == "credit":
                balance = -balance

            item = {
                "account_code": row["account_code"],
                "account_name": row["account_name"],
                "balance": balance,
            }

            if row["account_type"] == "asset":
                assets.append(item)
                total_assets += balance
            elif row["account_type"] == "liability":
                liabilities.append(item)
                total_liabilities += balance
            elif row["account_type"] == "equity":
                equity.append(item)
                total_equity += balance

        is_balanced = abs(total_assets - total_liabilities - total_equity) < 0.01

        return {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "is_balanced": is_balanced,
        }

    # ========== 세금 요약 ==========

    async def tax_summary(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        부가세 요약 (매출/매입 공급가액 + 세액 집계)

        tax_payable = 매출세액 - 매입세액

        Returns:
            {sales_supply, sales_tax, purchase_supply, purchase_tax,
             tax_payable, sales_count, purchase_count}
        """
        query = text("""
            SELECT
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales' THEN v.supply_amount ELSE 0 END), 0) AS sales_supply,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'sales' THEN v.tax_amount    ELSE 0 END), 0) AS sales_tax,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.supply_amount ELSE 0 END), 0) AS purchase_supply,
                COALESCE(SUM(CASE WHEN v.voucher_type = 'purchase' THEN v.tax_amount    ELSE 0 END), 0) AS purchase_tax,
                COUNT(CASE WHEN v.voucher_type = 'sales' THEN 1 END) AS sales_count,
                COUNT(CASE WHEN v.voucher_type = 'purchase' THEN 1 END) AS purchase_count
            FROM erp_vouchers v
            WHERE v.status = 'confirmed'
              AND v.voucher_type IN ('sales', 'purchase')
              AND v.voucher_date >= :start_date
              AND v.voucher_date <= :end_date
        """)

        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date,
        })
        row = result.mappings().first()

        sales_tax = float(row["sales_tax"])
        purchase_tax = float(row["purchase_tax"])

        return {
            "sales_supply": float(row["sales_supply"]),
            "sales_tax": sales_tax,
            "purchase_supply": float(row["purchase_supply"]),
            "purchase_tax": purchase_tax,
            "tax_payable": sales_tax - purchase_tax,
            "sales_count": int(row["sales_count"]),
            "purchase_count": int(row["purchase_count"]),
        }

    # ========== 경비 항목별 ==========

    async def expense_breakdown(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        경비 항목별 지출 집계 (경비전표 항목 기준)

        Returns:
            {categories: [...], total}
        """
        query = text("""
            SELECT
                vi.product_name,
                COALESCE(SUM(vi.total_amount), 0) AS total_amount,
                COUNT(*) AS count
            FROM erp_voucher_items vi
            JOIN erp_vouchers v ON v.id = vi.voucher_id
            WHERE v.status = 'confirmed'
              AND v.voucher_type = 'expense'
              AND v.voucher_date >= :start_date
              AND v.voucher_date <= :end_date
            GROUP BY vi.product_name
            ORDER BY total_amount DESC
        """)

        result = await session.execute(query, {
            "start_date": start_date,
            "end_date": end_date,
        })
        rows = result.mappings().all()

        categories = [self._to_float_dict(row) for row in rows]
        total = sum(c["total_amount"] for c in categories)

        return {
            "categories": categories,
            "total": total,
        }
