"""
ERP Test Configuration

Automatically applies 'erp' marker to all tests in this directory.
ERP tests are excluded from the main estimator CI pipeline per CLAUDE.md:
- ERP 관련 기능은 제외 (발주/재고/회계/인사)
- ERP는 별도 AI 시스템이 담당

To run ERP tests locally (requires ERP schema migrations):
  pytest tests/erp/ -m erp -v

Note: ERP schema migrations (erp_001_schema ~ erp_012_*) are in
cleanbackend/alembic/versions/ and must be applied first.
"""

import pytest


def pytest_collection_modifyitems(config, items):
    """Automatically mark all tests in tests/erp/ with @pytest.mark.erp."""
    for item in items:
        # Check if test is in tests/erp/ directory
        if "/erp/" in str(item.fspath) or "\\erp\\" in str(item.fspath):
            item.add_marker(pytest.mark.erp)
