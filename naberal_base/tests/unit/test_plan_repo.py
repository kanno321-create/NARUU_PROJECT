"""
Unit Tests for repos/plan_repo.py
Coverage target: >80% for PlanRepo async methods
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession"""
    session = AsyncMock()
    return session


class TestPlanRepo:
    """Tests for PlanRepo class"""

    def test_init(self, mock_session):
        """Test PlanRepo initialization"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        repo = PlanRepo(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_save_plan_success(self, mock_session):
        """Test successful plan save"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        repo = PlanRepo(mock_session)
        specs = [{"verb": "CREATE", "item": "BREAKER", "params": {"type": "MCCB"}}]

        result = await repo.save_plan("EST-20250101120000", specs)

        assert result == "EST-20250101120000"
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_plan_failure(self, mock_session):
        """Test plan save with database error"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_session.execute.side_effect = Exception("DB insert error")

        repo = PlanRepo(mock_session)
        specs = [{"verb": "CREATE"}]

        with pytest.raises(Exception) as exc:
            await repo.save_plan("EST-20250101120000", specs)

        assert "DB insert error" in str(exc.value)
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_plan_success_json_string(self, mock_session):
        """Test successful plan load with JSON string"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        specs = [{"verb": "CREATE", "item": "BREAKER"}]
        mock_row = (json.dumps(specs), True)

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.load_plan("EST-20250101120000")

        assert result == specs
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_plan_success_parsed_json(self, mock_session):
        """Test successful plan load with already parsed JSON"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        specs = [{"verb": "CREATE", "item": "ENCLOSURE"}]
        mock_row = (specs, True)  # Already parsed by asyncpg

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.load_plan("EST-20250101120000")

        assert result == specs

    @pytest.mark.asyncio
    async def test_load_plan_not_found(self, mock_session):
        """Test plan load when plan not found"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.load_plan("EST-NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_plan_invalid(self, mock_session):
        """Test plan load when plan is marked invalid"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_row = ([{"verb": "CREATE"}], False)  # is_valid = False

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.load_plan("EST-20250101120000")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_plan_failure(self, mock_session):
        """Test plan load with database error"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_session.execute.side_effect = Exception("DB query error")

        repo = PlanRepo(mock_session)

        with pytest.raises(Exception) as exc:
            await repo.load_plan("EST-20250101120000")

        assert "DB query error" in str(exc.value)

    @pytest.mark.asyncio
    async def test_exists_true(self, mock_session):
        """Test exists returns True when plan exists"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.exists("EST-20250101120000")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, mock_session):
        """Test exists returns False when plan not found"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.exists("EST-NONEXISTENT")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_error(self, mock_session):
        """Test exists returns False on database error"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_session.execute.side_effect = Exception("DB error")

        repo = PlanRepo(mock_session)
        result = await repo.exists("EST-20250101120000")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_plan_success(self, mock_session):
        """Test successful plan deletion"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_result = MagicMock()
        mock_result.fetchone.return_value = ("EST-20250101120000",)
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.delete_plan("EST-20250101120000")

        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_plan_not_found(self, mock_session):
        """Test delete when plan not found"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        repo = PlanRepo(mock_session)
        result = await repo.delete_plan("EST-NONEXISTENT")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_plan_failure(self, mock_session):
        """Test delete with database error"""
        from kis_estimator_core.repos.plan_repo import PlanRepo

        mock_session.execute.side_effect = Exception("DB delete error")

        repo = PlanRepo(mock_session)

        with pytest.raises(Exception) as exc:
            await repo.delete_plan("EST-20250101120000")

        assert "DB delete error" in str(exc.value)
        mock_session.rollback.assert_called_once()
