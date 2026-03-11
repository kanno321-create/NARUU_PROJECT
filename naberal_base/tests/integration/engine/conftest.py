"""
Integration Engine Tests Configuration

Auto-initializes catalog for all tests in this directory
"""

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def auto_catalog_init(catalog_initialized):
    """
    Auto-initialize catalog for all integration engine tests

    - All tests in tests/integration/engine/ need catalog data
    - Uses catalog_initialized fixture with autouse=True
    - Zero-Mock compliant: real catalog from DB
    """
    return catalog_initialized
