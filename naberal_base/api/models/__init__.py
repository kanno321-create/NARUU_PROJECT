"""
ERP Models Package
"""
from api.models.erp import (
    # Company
    CompanyInfo,

    # Customer
    Customer,
    CustomerType,

    # Product
    Product,
    ProductCategory,

    # Employee
    Employee,
    EmployeeStatus,

    # Voucher
    Voucher,
    VoucherType,
    VoucherStatus,

    # Order
    Order,
    OrderStatus,

    # Statement
    Statement,
    StatementStatus,
)

__all__ = [
    # Company
    "CompanyInfo",

    # Customer
    "Customer",
    "CustomerType",

    # Product
    "Product",
    "ProductCategory",

    # Employee
    "Employee",
    "EmployeeStatus",

    # Voucher
    "Voucher",
    "VoucherType",
    "VoucherStatus",

    # Order
    "Order",
    "OrderStatus",

    # Statement
    "Statement",
    "StatementStatus",
]
