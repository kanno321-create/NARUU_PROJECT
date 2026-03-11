"""
Transformer Tests Configuration

Provides catalog fixture for transformer tests that need real catalog data.
For unit tests that mock get_catalog_service, this fixture is NOT auto-used.
"""

import pytest_asyncio


@pytest_asyncio.fixture
async def catalog_for_transformer(catalog_initialized):
    """
    Initialize catalog for transformer tests that need real DB data

    - NOT autouse: unit tests mock get_catalog_service directly
    - Only use this fixture for integration tests requiring real catalog
    - Zero-Mock compliant: real catalog from DB when explicitly requested
    """
    return catalog_initialized
