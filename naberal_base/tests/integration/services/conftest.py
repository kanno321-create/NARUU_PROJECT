"""
Integration Services Tests Configuration

Auto-initializes catalog for service integration tests
"""

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def auto_catalog_init(catalog_initialized):
    """
    Auto-initialize catalog for service integration tests

    - Catalog service tests need real catalog data
    - Uses catalog_initialized fixture with autouse=True
    - Zero-Mock compliant: real catalog from DB
    """
    return catalog_initialized
