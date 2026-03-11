"""
Report Service
보고서 비즈니스 로직 (일계표, 월별현황, 거래처별, 손익, 대차대조표 등)
Contract-First + Evidence-Gated + Zero-Mock
"""
from typing import Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from kis_erp_core.repositories.report_repository import ReportRepository


class ReportService:
    """보고서 서비스"""

    def __init__(self):
        self.repo = ReportRepository()

    async def get_daily_summary(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> list:
        """일계표 조회"""
        return await self.repo.daily_summary(session, start_date, end_date)

    async def get_monthly_summary(
        self,
        session: AsyncSession,
        year: int,
    ) -> list:
        """월별 현황 조회 (1~12월)"""
        return await self.repo.monthly_summary(session, year)

    async def get_customer_balances(
        self,
        session: AsyncSession,
        as_of_date: date,
        include_zero: bool = False,
    ) -> list:
        """거래처별 잔액 현황"""
        return await self.repo.customer_balances(session, as_of_date, include_zero)

    async def get_customer_transactions(
        self,
        session: AsyncSession,
        customer_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        voucher_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """거래처별 거래 내역"""
        return await self.repo.customer_transactions(
            session, customer_id, start_date, end_date, voucher_type, skip, limit,
        )

    async def get_receivables(
        self,
        session: AsyncSession,
        as_of_date: date,
        overdue_only: bool = False,
    ) -> dict:
        """미수금 현황"""
        return await self.repo.receivables(session, as_of_date, overdue_only)

    async def get_payables(
        self,
        session: AsyncSession,
        as_of_date: date,
        overdue_only: bool = False,
    ) -> dict:
        """미지급금 현황"""
        return await self.repo.payables(session, as_of_date, overdue_only)

    async def get_product_sales(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        top_n: int = 20,
    ) -> dict:
        """상품별 매출 현황"""
        return await self.repo.product_sales(session, start_date, end_date, top_n)

    async def get_product_purchase(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        top_n: int = 20,
    ) -> dict:
        """상품별 매입 현황"""
        return await self.repo.product_purchase(session, start_date, end_date, top_n)

    async def get_sales_statement(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        customer_id: Optional[str] = None,
    ) -> dict:
        """매출명세서"""
        return await self.repo.statement(
            session, "sales", start_date, end_date, customer_id,
        )

    async def get_purchase_statement(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        customer_id: Optional[str] = None,
    ) -> dict:
        """매입명세서"""
        return await self.repo.statement(
            session, "purchase", start_date, end_date, customer_id,
        )

    async def get_profit_loss(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> dict:
        """손익계산서"""
        return await self.repo.profit_loss(session, start_date, end_date)

    async def get_balance_sheet(
        self,
        session: AsyncSession,
        as_of_date: date,
    ) -> dict:
        """대차대조표"""
        return await self.repo.balance_sheet(session, as_of_date)

    async def get_tax_summary(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> dict:
        """부가세 요약"""
        return await self.repo.tax_summary(session, start_date, end_date)

    async def get_expense_breakdown(
        self,
        session: AsyncSession,
        start_date: date,
        end_date: date,
    ) -> dict:
        """경비 항목별 현황"""
        return await self.repo.expense_breakdown(session, start_date, end_date)
