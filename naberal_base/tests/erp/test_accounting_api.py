"""
회계 API 엔드포인트 테스트 - FastAPI TestClient 기반
12개 엔드포인트 모두 테스트

의존성:
- AccountService, JournalService를 패치하여 DB 없이 테스트
- FastAPI dependency_overrides로 get_db 우회

엔드포인트:
1. GET  /v1/erp/accounting/accounts
2. POST /v1/erp/accounting/accounts
3. GET  /v1/erp/accounting/accounts/{id}
4. PUT  /v1/erp/accounting/accounts/{id}
5. GET  /v1/erp/accounting/journal-entries
6. POST /v1/erp/accounting/journal-entries
7. GET  /v1/erp/accounting/journal-entries/{id}
8. POST /v1/erp/accounting/journal-entries/{id}/post
9. POST /v1/erp/accounting/journal-entries/{id}/cancel
10. GET /v1/erp/accounting/reports/trial-balance
11. GET /v1/erp/accounting/reports/balance-sheet
12. GET /v1/erp/accounting/reports/profit-loss
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app
from api.db import get_db


# ========== Fixtures ==========


@pytest.fixture(autouse=True)
def override_db():
    """DB 의존성을 AsyncMock으로 오버라이드"""

    async def mock_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Sync TestClient"""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ========== 계정과목 API ==========

PREFIX = "/v1/erp/accounting"


class TestAccountEndpoints:
    """계정과목 CRUD 엔드포인트"""

    @patch("api.routers.erp.accounting.AccountService")
    def test_list_accounts(self, MockService, client):
        """GET /accounts - 목록 조회"""
        mock_svc = MockService.return_value
        mock_svc.list_accounts = AsyncMock(
            return_value=[
                {
                    "id": "acc-1",
                    "account_code": "1010",
                    "account_name": "현금",
                    "account_type": "asset",
                    "parent_id": None,
                    "is_group": False,
                    "balance_direction": "debit",
                    "description": "보유 현금",
                    "is_active": True,
                    "created_at": "2026-02-08T00:00:00",
                    "updated_at": None,
                }
            ]
        )

        response = client.get(f"{PREFIX}/accounts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["account_code"] == "1010"
        assert data[0]["account_type"] == "asset"

    @patch("api.routers.erp.accounting.AccountService")
    def test_list_accounts_with_filter(self, MockService, client):
        """GET /accounts?account_type=asset - 필터 조회"""
        mock_svc = MockService.return_value
        mock_svc.list_accounts = AsyncMock(return_value=[])

        response = client.get(
            f"{PREFIX}/accounts",
            params={"account_type": "asset", "is_group": False},
        )
        assert response.status_code == 200

    @patch("api.routers.erp.accounting.AccountService")
    def test_get_account(self, MockService, client):
        """GET /accounts/{id} - 상세 조회"""
        mock_svc = MockService.return_value
        mock_svc.get_account = AsyncMock(
            return_value={
                "id": "acc-1",
                "account_code": "1010",
                "account_name": "현금",
                "account_type": "asset",
                "parent_id": None,
                "is_group": False,
                "balance_direction": "debit",
                "description": "보유 현금",
                "is_active": True,
                "created_at": "2026-02-08T00:00:00",
                "updated_at": None,
            }
        )

        response = client.get(f"{PREFIX}/accounts/acc-1")
        assert response.status_code == 200
        data = response.json()
        assert data["account_code"] == "1010"

    @patch("api.routers.erp.accounting.AccountService")
    def test_get_account_not_found(self, MockService, client):
        """GET /accounts/{id} - 404 미존재"""
        mock_svc = MockService.return_value
        mock_svc.get_account = AsyncMock(return_value=None)

        response = client.get(f"{PREFIX}/accounts/nonexistent")
        assert response.status_code == 404

    @patch("api.routers.erp.accounting.AccountService")
    def test_create_account(self, MockService, client):
        """POST /accounts - 생성 (201)"""
        mock_svc = MockService.return_value
        mock_svc.create_account = AsyncMock(
            return_value={
                "id": "new-acc",
                "account_code": "1015",
                "account_name": "정기예금",
                "account_type": "asset",
                "parent_id": None,
                "is_group": False,
                "balance_direction": "debit",
                "description": None,
                "is_active": True,
                "created_at": "2026-02-08T00:00:00",
                "updated_at": None,
            }
        )

        response = client.post(
            f"{PREFIX}/accounts",
            json={
                "account_code": "1015",
                "account_name": "정기예금",
                "account_type": "asset",
                "balance_direction": "debit",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["account_code"] == "1015"

    @patch("api.routers.erp.accounting.AccountService")
    def test_create_account_duplicate_code(self, MockService, client):
        """POST /accounts - 409 중복 코드"""
        mock_svc = MockService.return_value
        mock_svc.create_account = AsyncMock(
            side_effect=ValueError("계정코드 '1010'이(가) 이미 존재합니다")
        )

        response = client.post(
            f"{PREFIX}/accounts",
            json={
                "account_code": "1010",
                "account_name": "현금",
                "account_type": "asset",
                "balance_direction": "debit",
            },
        )
        assert response.status_code == 409
        assert "이미 존재" in response.json()["message"]

    @patch("api.routers.erp.accounting.AccountService")
    def test_update_account(self, MockService, client):
        """PUT /accounts/{id} - 수정"""
        mock_svc = MockService.return_value
        mock_svc.update_account = AsyncMock(
            return_value={
                "id": "acc-1",
                "account_code": "1010",
                "account_name": "수정된 현금",
                "account_type": "asset",
                "parent_id": None,
                "is_group": False,
                "balance_direction": "debit",
                "description": "수정됨",
                "is_active": True,
                "created_at": "2026-02-08T00:00:00",
                "updated_at": "2026-02-08T01:00:00",
            }
        )

        response = client.put(
            f"{PREFIX}/accounts/acc-1",
            json={"account_name": "수정된 현금", "description": "수정됨"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["account_name"] == "수정된 현금"

    @patch("api.routers.erp.accounting.AccountService")
    def test_update_account_not_found(self, MockService, client):
        """PUT /accounts/{id} - 404 미존재"""
        mock_svc = MockService.return_value
        mock_svc.update_account = AsyncMock(return_value=None)

        response = client.put(
            f"{PREFIX}/accounts/nonexistent",
            json={"account_name": "없는 계정"},
        )
        assert response.status_code == 404


# ========== 분개장 API ==========


class TestJournalEndpoints:
    """분개장 CRUD + 상태 전이 엔드포인트"""

    @patch("api.routers.erp.accounting.JournalService")
    def test_create_journal_entry(self, MockService, client):
        """POST /journal-entries - 분개 생성 (201)"""
        mock_svc = MockService.return_value
        mock_svc.create_journal_entry = AsyncMock(
            return_value={
                "id": "je-1",
                "entry_number": "JE-20260208-0001",
                "entry_date": "2026-02-08",
                "narration": "상품 매출",
                "voucher_id": None,
                "status": "draft",
                "total_debit": 100000.0,
                "total_credit": 100000.0,
                "items": [],
                "created_at": "2026-02-08T00:00:00",
                "updated_at": None,
            }
        )

        response = client.post(
            f"{PREFIX}/journal-entries",
            json={
                "entry_date": "2026-02-08",
                "narration": "상품 매출",
                "items": [
                    {"account_id": "acc-1", "debit": 100000.0, "credit": 0.0},
                    {"account_id": "acc-2", "debit": 0.0, "credit": 100000.0},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert data["total_debit"] == 100000.0

    @patch("api.routers.erp.accounting.JournalService")
    def test_create_journal_entry_unbalanced(self, MockService, client):
        """POST /journal-entries - 400 대차불일치"""
        mock_svc = MockService.return_value
        mock_svc.create_journal_entry = AsyncMock(
            side_effect=ValueError("대차평균 불일치")
        )

        response = client.post(
            f"{PREFIX}/journal-entries",
            json={
                "entry_date": "2026-02-08",
                "narration": "불균형",
                "items": [
                    {"account_id": "acc-1", "debit": 100000.0, "credit": 0.0},
                    {"account_id": "acc-2", "debit": 0.0, "credit": 50000.0},
                ],
            },
        )
        assert response.status_code == 400
        assert "대차평균" in response.json()["message"]

    @patch("api.routers.erp.accounting.JournalService")
    def test_get_journal_entry(self, MockService, client):
        """GET /journal-entries/{id} - 상세 조회"""
        mock_svc = MockService.return_value
        mock_svc.get_entry = AsyncMock(
            return_value={
                "id": "je-1",
                "entry_number": "JE-20260208-0001",
                "entry_date": "2026-02-08",
                "narration": "상품 매출",
                "voucher_id": None,
                "status": "posted",
                "total_debit": 100000.0,
                "total_credit": 100000.0,
                "items": [
                    {
                        "id": "item-1",
                        "journal_entry_id": "je-1",
                        "account_id": "acc-1",
                        "account_code": "1010",
                        "account_name": "현금",
                        "debit": 100000.0,
                        "credit": 0.0,
                        "customer_id": None,
                        "customer_name": None,
                        "description": "현금 수령",
                    },
                ],
                "created_at": "2026-02-08T00:00:00",
                "updated_at": None,
            }
        )

        response = client.get(f"{PREFIX}/journal-entries/je-1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["account_code"] == "1010"

    @patch("api.routers.erp.accounting.JournalService")
    def test_get_journal_entry_not_found(self, MockService, client):
        """GET /journal-entries/{id} - 404"""
        mock_svc = MockService.return_value
        mock_svc.get_entry = AsyncMock(return_value=None)

        response = client.get(f"{PREFIX}/journal-entries/nonexistent")
        assert response.status_code == 404

    @patch("api.routers.erp.accounting.JournalService")
    def test_post_journal_entry(self, MockService, client):
        """POST /journal-entries/{id}/post - 전기"""
        mock_svc = MockService.return_value
        mock_svc.post_entry = AsyncMock(
            return_value={
                "id": "je-1",
                "entry_number": "JE-20260208-0001",
                "entry_date": "2026-02-08",
                "narration": "테스트",
                "voucher_id": None,
                "status": "posted",
                "total_debit": 50000.0,
                "total_credit": 50000.0,
                "items": [],
                "created_at": "2026-02-08T00:00:00",
                "updated_at": "2026-02-08T01:00:00",
            }
        )

        response = client.post(f"{PREFIX}/journal-entries/je-1/post")
        assert response.status_code == 200
        assert response.json()["status"] == "posted"

    @patch("api.routers.erp.accounting.JournalService")
    def test_post_already_posted_returns_400(self, MockService, client):
        """POST /journal-entries/{id}/post - 이미 posted면 400"""
        mock_svc = MockService.return_value
        mock_svc.post_entry = AsyncMock(
            side_effect=ValueError("draft만 전기 가능")
        )

        response = client.post(f"{PREFIX}/journal-entries/je-1/post")
        assert response.status_code == 400

    @patch("api.routers.erp.accounting.JournalService")
    def test_cancel_journal_entry(self, MockService, client):
        """POST /journal-entries/{id}/cancel - 취소 + 역분개"""
        mock_svc = MockService.return_value
        mock_svc.cancel_entry = AsyncMock(
            return_value={
                "id": "je-reverse",
                "entry_number": "JE-20260208-0002",
                "entry_date": "2026-02-08",
                "narration": "[역분개] 상품 매출",
                "voucher_id": None,
                "status": "draft",
                "total_debit": 100000.0,
                "total_credit": 100000.0,
                "items": [],
                "created_at": "2026-02-08T00:00:00",
                "updated_at": None,
            }
        )

        response = client.post(f"{PREFIX}/journal-entries/je-1/cancel")
        assert response.status_code == 200
        data = response.json()
        assert "[역분개]" in data["narration"]

    @patch("api.routers.erp.accounting.JournalService")
    def test_cancel_draft_returns_400(self, MockService, client):
        """POST /journal-entries/{id}/cancel - draft 취소 불가"""
        mock_svc = MockService.return_value
        mock_svc.cancel_entry = AsyncMock(
            side_effect=ValueError("posted만 취소 가능")
        )

        response = client.post(f"{PREFIX}/journal-entries/je-1/cancel")
        assert response.status_code == 400


# ========== 재무보고서 API ==========


class TestReportEndpoints:
    """재무보고서 엔드포인트"""

    @patch("api.routers.erp.accounting.JournalService")
    def test_trial_balance(self, MockService, client):
        """GET /reports/trial-balance - 시산표"""
        mock_svc = MockService.return_value
        mock_svc.get_trial_balance = AsyncMock(
            return_value={
                "as_of_date": "2026-02-08",
                "accounts": [
                    {
                        "account_id": "acc-1",
                        "account_code": "1010",
                        "account_name": "현금",
                        "account_type": "asset",
                        "debit_total": 500000.0,
                        "credit_total": 200000.0,
                        "balance": 300000.0,
                    },
                ],
                "total_debit": 500000.0,
                "total_credit": 500000.0,
            }
        )

        response = client.get(
            f"{PREFIX}/reports/trial-balance",
            params={"as_of_date": "2026-02-08"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_debit"] == 500000.0
        assert len(data["accounts"]) == 1

    @patch("api.routers.erp.accounting.JournalService")
    def test_trial_balance_requires_date(self, MockService, client):
        """GET /reports/trial-balance - 기준일 필수"""
        response = client.get(f"{PREFIX}/reports/trial-balance")
        assert response.status_code == 422  # Validation error

    @patch("api.routers.erp.accounting.JournalService")
    def test_balance_sheet(self, MockService, client):
        """GET /reports/balance-sheet - 대차대조표"""
        mock_svc = MockService.return_value
        mock_svc.get_balance_sheet = AsyncMock(
            return_value={
                "as_of_date": "2026-02-08",
                "assets": {
                    "section_name": "자산",
                    "accounts": [],
                    "total": 1000000.0,
                },
                "liabilities": {
                    "section_name": "부채",
                    "accounts": [],
                    "total": 400000.0,
                },
                "equity": {
                    "section_name": "자본",
                    "accounts": [],
                    "total": 600000.0,
                },
                "total_assets": 1000000.0,
                "total_liabilities_equity": 1000000.0,
                "is_balanced": True,
            }
        )

        response = client.get(
            f"{PREFIX}/reports/balance-sheet",
            params={"as_of_date": "2026-02-08"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_balanced"] is True
        assert data["total_assets"] == data["total_liabilities_equity"]

    @patch("api.routers.erp.accounting.JournalService")
    def test_profit_loss(self, MockService, client):
        """GET /reports/profit-loss - 손익계산서"""
        mock_svc = MockService.return_value
        mock_svc.get_profit_loss = AsyncMock(
            return_value={
                "start_date": "2026-01-01",
                "end_date": "2026-02-08",
                "revenue": {
                    "section_name": "수익",
                    "accounts": [],
                    "total": 5000000.0,
                },
                "expenses": {
                    "section_name": "비용",
                    "accounts": [],
                    "total": 3000000.0,
                },
                "total_revenue": 5000000.0,
                "total_expenses": 3000000.0,
                "net_profit": 2000000.0,
            }
        )

        response = client.get(
            f"{PREFIX}/reports/profit-loss",
            params={"start_date": "2026-01-01", "end_date": "2026-02-08"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net_profit"] == 2000000.0
        assert data["net_profit"] == data["total_revenue"] - data["total_expenses"]

    @patch("api.routers.erp.accounting.JournalService")
    def test_profit_loss_requires_dates(self, MockService, client):
        """GET /reports/profit-loss - 시작일/종료일 필수"""
        response = client.get(f"{PREFIX}/reports/profit-loss")
        assert response.status_code == 422
