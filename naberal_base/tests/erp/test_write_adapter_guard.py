"""
ERP Write Adapter Guard Tests - Phase 4 가드 검증 (4 cases)

절대 원칙:
- ERP_WRITE_DISABLED 에러만 검증
- 실제 DB/API 쓰기 없음 (더미/목업 금지)
- FeatureFlag 차단 동작만 확인
"""

import pytest
from kis_erp_core.adapters import ERPWriteAdapter
from kis_erp_core.adapters.write_adapter import ERPWriteDisabledError


def test_01_write_adapter_init_default_disabled():
    """Test 1: Write adapter 초기화 시 기본값 disabled"""
    adapter = ERPWriteAdapter()
    assert adapter.write_enabled is False


def test_02_journal_entry_guard_blocks():
    """Test 2: journal_entry() → ERP_WRITE_DISABLED"""
    adapter = ERPWriteAdapter()

    with pytest.raises(ERPWriteDisabledError) as exc_info:
        adapter.journal_entry({"account": "1000", "debit": 10000})

    assert exc_info.value.code == "ERP_WRITE_DISABLED"
    assert "비활성화" in exc_info.value.message
    assert exc_info.value.meta["feature_flag"] == "ERP_WRITE_ENABLED"
    assert exc_info.value.meta["current_value"] == "false"


def test_03_inventory_adjust_guard_blocks():
    """Test 3: inventory_adjust() → ERP_WRITE_DISABLED"""
    adapter = ERPWriteAdapter()

    with pytest.raises(ERPWriteDisabledError) as exc_info:
        adapter.inventory_adjust({"item_code": "PANEL-001", "qty": 5})

    assert exc_info.value.code == "ERP_WRITE_DISABLED"
    assert "비활성화" in exc_info.value.message


def test_04_invoice_issue_guard_blocks():
    """Test 4: invoice_issue() → ERP_WRITE_DISABLED"""
    adapter = ERPWriteAdapter()

    with pytest.raises(ERPWriteDisabledError) as exc_info:
        adapter.invoice_issue({"customer": "ABC Corp", "amount": 1000000})

    assert exc_info.value.code == "ERP_WRITE_DISABLED"
    assert "비활성화" in exc_info.value.message
    assert exc_info.value.meta["phase"] == "4-scaffold"
