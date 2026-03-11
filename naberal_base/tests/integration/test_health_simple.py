"""
Phase I-6 Restored: /health endpoint DB integration (simplified)

SB-05 Compliance:
- @requires_db: Real PostgreSQL health check allowed
- No mocks: Actual DB ping
- search_path="kis_beta,public" enforced (SB-01)

Coverage Target: api/main.py health_check() DB check logic
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.requires_db
class TestHealthSimple:
    """Integration tests for /health endpoint with real DB"""

    async def test_health_check(self, async_client: AsyncClient):
        """
        /health with DB connection

        Covers:
        - api/main.py: health_check() method
        - api/db.py: check_db_health() function
        """
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
