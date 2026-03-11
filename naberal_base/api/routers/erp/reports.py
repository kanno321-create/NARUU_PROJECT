"""
KIS ERP - 보고서 API
일계표, 월별현황, 거래처별잔액, 미수금/미지급금, 상품별, 명세서,
손익계산서, 대차대조표, 세금요약, 경비항목별
Contract-First + Evidence-Gated + Zero-Mock
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from api.db import get_db

from kis_erp_core.services.report_service import ReportService
from kis_erp_core.models.voucher_models import VoucherType
from kis_erp_core.models.report_models import (
    DailySummary,
    MonthlySummary,
    CustomerBalance,
    CustomerTransactionReport,
    ReceivableReport,
    PayableReport,
    ProductSalesReport,
    ProductPurchaseReport,
    StatementReport,
    ProfitLossReport,
    BalanceSheetReport,
    TaxSummaryReport,
    ExpenseBreakdownReport,
)

router = APIRouter(prefix="/reports", tags=["ERP - 보고서"])


# ==================== 일별/월별 현황 ====================


@router.get("/daily-summary", response_model=List[DailySummary], summary="일계표")
async def get_daily_summary(
    start_date: Optional[date] = Query(None, description="시작일 (기본: 오늘)"),
    end_date: Optional[date] = Query(None, description="종료일 (기본: 오늘)"),
    target_date: Optional[date] = Query(None, description="특정일 (start/end 대신 사용)"),
    db: AsyncSession = Depends(get_db),
) -> List[DailySummary]:
    """
    일별 매출/매입/수금/지급/경비 현황을 조회합니다.

    - target_date 지정 시: 해당 일자만 조회
    - start_date/end_date 지정 시: 기간 조회
    - 아무것도 없으면: 오늘 조회
    """
    if target_date is not None:
        start_date = target_date
        end_date = target_date
    else:
        today = date.today()
        start_date = start_date or today
        end_date = end_date or today

    service = ReportService()
    results = await service.get_daily_summary(db, start_date, end_date)
    return [DailySummary(**r) for r in results]


@router.get("/monthly-summary", response_model=List[MonthlySummary], summary="월별 현황")
async def get_monthly_summary(
    year: int = Query(..., description="연도"),
    db: AsyncSession = Depends(get_db),
) -> List[MonthlySummary]:
    """
    월별 매출/매입/손익 현황을 조회합니다. (1~12월 전체)
    """
    service = ReportService()
    results = await service.get_monthly_summary(db, year)
    return [MonthlySummary(**r) for r in results]


# ==================== 거래처별 현황 ====================


@router.get(
    "/customer-balances",
    response_model=List[CustomerBalance],
    summary="거래처별 잔액 현황",
)
async def get_customer_balances(
    as_of_date: Optional[date] = Query(None, description="기준일 (기본: 오늘)"),
    include_zero: bool = Query(False, description="잔액 0인 거래처 포함"),
    db: AsyncSession = Depends(get_db),
) -> List[CustomerBalance]:
    """
    거래처별 미수금/미지급금 잔액 현황을 조회합니다.
    """
    as_of_date = as_of_date or date.today()
    service = ReportService()
    results = await service.get_customer_balances(db, as_of_date, include_zero)
    return [CustomerBalance(**r) for r in results]


@router.get(
    "/customer/{customer_id}/transactions",
    response_model=CustomerTransactionReport,
    summary="거래처별 거래 내역",
)
async def get_customer_transactions(
    customer_id: str,
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    voucher_type: Optional[VoucherType] = Query(None, description="전표 유형"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CustomerTransactionReport:
    """
    특정 거래처의 거래 내역을 조회합니다.
    """
    vtype = voucher_type.value if voucher_type else None
    service = ReportService()
    result = await service.get_customer_transactions(
        db, customer_id, start_date, end_date, vtype, skip, limit,
    )
    return CustomerTransactionReport(**result)


@router.get(
    "/receivables",
    response_model=ReceivableReport,
    summary="미수금 현황",
)
async def get_receivables(
    as_of_date: Optional[date] = Query(None, description="기준일"),
    overdue_only: bool = Query(False, description="연체건만"),
    db: AsyncSession = Depends(get_db),
) -> ReceivableReport:
    """
    미수금 현황을 조회합니다. (매출전표 중 미결제 건)
    """
    as_of_date = as_of_date or date.today()
    service = ReportService()
    result = await service.get_receivables(db, as_of_date, overdue_only)
    return ReceivableReport(**result)


@router.get(
    "/payables",
    response_model=PayableReport,
    summary="미지급금 현황",
)
async def get_payables(
    as_of_date: Optional[date] = Query(None, description="기준일"),
    overdue_only: bool = Query(False, description="연체건만"),
    db: AsyncSession = Depends(get_db),
) -> PayableReport:
    """
    미지급금 현황을 조회합니다. (매입전표 중 미결제 건)
    """
    as_of_date = as_of_date or date.today()
    service = ReportService()
    result = await service.get_payables(db, as_of_date, overdue_only)
    return PayableReport(**result)


# ==================== 상품별 현황 ====================


@router.get(
    "/product-sales",
    response_model=ProductSalesReport,
    summary="상품별 매출 현황",
)
async def get_product_sales(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    top_n: int = Query(20, ge=1, le=100, description="상위 N개"),
    db: AsyncSession = Depends(get_db),
) -> ProductSalesReport:
    """
    상품별 매출 현황을 조회합니다.
    """
    service = ReportService()
    result = await service.get_product_sales(db, start_date, end_date, top_n)
    return ProductSalesReport(
        period_start=start_date,
        period_end=end_date,
        **result,
    )


@router.get(
    "/product-purchase",
    response_model=ProductPurchaseReport,
    summary="상품별 매입 현황",
)
async def get_product_purchase(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    top_n: int = Query(20, ge=1, le=100, description="상위 N개"),
    db: AsyncSession = Depends(get_db),
) -> ProductPurchaseReport:
    """
    상품별 매입 현황을 조회합니다.
    """
    service = ReportService()
    result = await service.get_product_purchase(db, start_date, end_date, top_n)
    return ProductPurchaseReport(
        period_start=start_date,
        period_end=end_date,
        **result,
    )


# ==================== 매출/매입 명세서 ====================


@router.get(
    "/sales-statement",
    response_model=StatementReport,
    summary="매출명세서",
)
async def get_sales_statement(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    db: AsyncSession = Depends(get_db),
) -> StatementReport:
    """
    매출명세서를 생성합니다. (기간별 매출전표 목록 + 공급가/세액/합계)
    """
    service = ReportService()
    result = await service.get_sales_statement(db, start_date, end_date, customer_id)
    return StatementReport(
        period_start=start_date,
        period_end=end_date,
        **result,
    )


@router.get(
    "/purchase-statement",
    response_model=StatementReport,
    summary="매입명세서",
)
async def get_purchase_statement(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    customer_id: Optional[str] = Query(None, description="거래처 ID"),
    db: AsyncSession = Depends(get_db),
) -> StatementReport:
    """
    매입명세서를 생성합니다. (기간별 매입전표 목록 + 공급가/세액/합계)
    """
    service = ReportService()
    result = await service.get_purchase_statement(db, start_date, end_date, customer_id)
    return StatementReport(
        period_start=start_date,
        period_end=end_date,
        **result,
    )


# ==================== 손익 분석 ====================


@router.get(
    "/profit-loss",
    response_model=ProfitLossReport,
    summary="손익계산서",
)
async def get_profit_loss(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    db: AsyncSession = Depends(get_db),
) -> ProfitLossReport:
    """
    기간별 손익계산서를 조회합니다.

    - 매출총이익 = 매출 - 매입
    - 순이익 = 매출총이익 - 경비
    - 이익률 = 순이익 / 매출 * 100
    """
    service = ReportService()
    result = await service.get_profit_loss(db, start_date, end_date)
    return ProfitLossReport(
        period_start=start_date,
        period_end=end_date,
        **result,
    )


@router.get(
    "/expense-breakdown",
    response_model=ExpenseBreakdownReport,
    summary="경비 항목별 현황",
)
async def get_expense_breakdown(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    db: AsyncSession = Depends(get_db),
) -> ExpenseBreakdownReport:
    """
    경비 항목별 지출 현황을 조회합니다.
    """
    service = ReportService()
    result = await service.get_expense_breakdown(db, start_date, end_date)
    return ExpenseBreakdownReport(
        period_start=start_date,
        period_end=end_date,
        **result,
    )


# ==================== 대차대조표 / 세금요약 (신규) ====================


@router.get(
    "/balance-sheet",
    response_model=BalanceSheetReport,
    summary="대차대조표",
)
async def get_balance_sheet(
    as_of_date: Optional[date] = Query(None, description="기준일 (기본: 오늘)"),
    db: AsyncSession = Depends(get_db),
) -> BalanceSheetReport:
    """
    대차대조표를 조회합니다. (자산 = 부채 + 자본)

    - posted 상태의 분개 기반
    - is_balanced: 차변/대변 균형 여부
    """
    as_of_date = as_of_date or date.today()
    service = ReportService()
    result = await service.get_balance_sheet(db, as_of_date)
    return BalanceSheetReport(as_of_date=as_of_date, **result)


@router.get(
    "/tax-summary",
    response_model=TaxSummaryReport,
    summary="부가세 요약",
)
async def get_tax_summary(
    start_date: date = Query(..., description="시작일"),
    end_date: date = Query(..., description="종료일"),
    db: AsyncSession = Depends(get_db),
) -> TaxSummaryReport:
    """
    부가세 매출/매입 집계를 조회합니다. (분기별 신고용)

    - tax_payable = 매출세액 - 매입세액
    """
    service = ReportService()
    result = await service.get_tax_summary(db, start_date, end_date)
    return TaxSummaryReport(
        period_start=start_date,
        period_end=end_date,
        **result,
    )
