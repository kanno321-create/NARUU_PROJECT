"""
Item Validators - Phase XVII-b: Zero-Mock / Contract-First

Validates quote line item fields (quantity, price, etc.)
"""

from kis_estimator_core.core.ssot.errors import ErrorCode, raise_error


def validate_qty(qty: int, item_idx: int = 0) -> None:
    """
    Validate quantity ≥1 (SSOT enforcement)

    Args:
        qty: Quantity value to validate
        item_idx: Item index for error messages (default: 0)

    Raises:
        EstimatorError E_VALIDATION: If qty is None, zero, or negative
    """
    if qty is None or qty < 1:
        raise_error(
            ErrorCode.E_VALIDATION,
            f"E_VALIDATION: Item {item_idx}: qty>=1 required (got {qty})",
            hint="Quantity must be a positive integer (≥1)",
        )


def validate_price(price: float, item_idx: int = 0) -> None:
    """
    Validate unit_price ≥0 (SSOT enforcement)

    Args:
        price: Unit price value to validate
        item_idx: Item index for error messages (default: 0)

    Raises:
        EstimatorError E_VALIDATION: If price is negative
    """
    if price < 0:
        raise_error(
            ErrorCode.E_VALIDATION,
            f"E_VALIDATION: Item {item_idx}: unit_price must be non-negative (got {price})",
            hint="Unit price cannot be negative",
        )
