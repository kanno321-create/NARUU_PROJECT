"""
KIS ERP API Routers Package
ERP 관련 API 엔드포인트 모음
"""

from api.routers.erp.customers import router as customers_router
from api.routers.erp.products import router as products_router
from api.routers.erp.vouchers import router as vouchers_router
from api.routers.erp.reports import router as reports_router
from api.routers.erp.carryover import router as carryover_router

# 추가 ERP 라우터
from api.routers.erp.company import router as company_router
from api.routers.erp.employees import router as employees_router
from api.routers.erp.payroll import router as payroll_router
from api.routers.erp.orders import router as orders_router
from api.routers.erp.statements import router as statements_router
from api.routers.erp.inventory import router as inventory_router
from api.routers.erp.settings import router as settings_router
from api.routers.erp.accounting import router as accounting_router
from api.routers.erp.audit import router as audit_router
from api.routers.erp.bank_accounts import router as bank_accounts_router
from api.routers.erp.estimate_files import router as estimate_files_router
from api.routers.erp.drawing_files import router as drawing_files_router

# FE-BE 경로 어댑터 라우터
from api.routers.erp.sales_adapter import router as sales_adapter_router
from api.routers.erp.purchases_adapter import router as purchases_adapter_router
from api.routers.erp.payments_adapter import router as payments_adapter_router
from api.routers.erp.dashboard_adapter import router as dashboard_adapter_router
from api.routers.erp.tax_invoices import router as tax_invoices_router

__all__ = [
    # 기본 ERP 라우터
    "customers_router",
    "products_router",
    "vouchers_router",
    "reports_router",
    "carryover_router",
    # 추가 ERP 라우터
    "company_router",
    "employees_router",
    "payroll_router",
    "orders_router",
    "statements_router",
    "inventory_router",
    "settings_router",
    "accounting_router",
    "audit_router",
    "bank_accounts_router",
    # 파일 저장 라우터
    "estimate_files_router",
    "drawing_files_router",
    # FE-BE 경로 어댑터 라우터
    "sales_adapter_router",
    "purchases_adapter_router",
    "payments_adapter_router",
    "dashboard_adapter_router",
    "tax_invoices_router",
]
