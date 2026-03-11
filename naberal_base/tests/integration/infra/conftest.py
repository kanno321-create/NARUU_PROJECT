"""
Integration Infra Tests Configuration

Auto-initializes catalog for infra integration tests
"""

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def auto_catalog_init(catalog_initialized):
    """
    Auto-initialize catalog for integration infra tests

    - Supabase client tests need catalog data
    - Uses catalog_initialized fixture with autouse=True
    - Zero-Mock compliant: real catalog from DB
    """
    return catalog_initialized
