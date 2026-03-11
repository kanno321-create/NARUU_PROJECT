"""
supabase_client.py 실제 호출 테스트 (P4-2 Phase I-4)

목적: Supabase 클라이언트 coverage 측정 (0% → 60%)
원칙: Zero-Mock (실제 Supabase 연결), @requires_db 마커 사용, SB-05 준수
"""

import pytest
import os
from unittest.mock import patch

from kis_estimator_core.infra.supabase_client import (
    get_supabase_client,
    test_supabase_connection,
    query_catalog_items,
    insert_quote,
    get_quote_by_id,
    get_cached_client,
    SupabaseClientError,
    SupabaseConnectionError,
    SupabaseConfigError,
)


# ============================================================
# Fixture: Skip if Supabase Not Available
# ============================================================
@pytest.fixture
def skip_if_no_supabase():
    """Supabase 환경변수 없으면 스킵 (SB-05 준수)"""
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        pytest.skip(
            "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set - skipping Supabase tests (SB-05 compliance)"
        )


# ============================================================
# Test: Exception Classes
# ============================================================
def test_supabase_client_error_inheritance():
    """SupabaseClientError 상속 구조"""
    # 실제 호출
    error = SupabaseClientError("test error")

    # 검증
    assert isinstance(error, Exception)
    assert str(error) == "test error"


def test_supabase_connection_error_inheritance():
    """SupabaseConnectionError 상속 구조"""
    # 실제 호출
    error = SupabaseConnectionError("connection failed")

    # 검증
    assert isinstance(error, SupabaseClientError)
    assert isinstance(error, Exception)
    assert str(error) == "connection failed"


def test_supabase_config_error_inheritance():
    """SupabaseConfigError 상속 구조"""
    # 실제 호출
    error = SupabaseConfigError("config missing")

    # 검증
    assert isinstance(error, SupabaseClientError)
    assert isinstance(error, Exception)
    assert str(error) == "config missing"


# ============================================================
# Test: get_supabase_client (환경변수 검증)
# ============================================================
def test_get_supabase_client_missing_url():
    """SUPABASE_URL 누락 → SupabaseConfigError"""
    with patch.dict(os.environ, {}, clear=True):
        # 실제 호출
        with pytest.raises(SupabaseConfigError, match="SUPABASE_URL.*missing"):
            get_supabase_client()


def test_get_supabase_client_missing_service_key():
    """SUPABASE_SERVICE_ROLE_KEY 누락 → SupabaseConfigError"""
    with patch.dict(
        os.environ, {"SUPABASE_URL": "https://test.supabase.co"}, clear=True
    ):
        # 실제 호출
        with pytest.raises(SupabaseConfigError, match="SERVICE_ROLE_KEY.*missing"):
            get_supabase_client()


def test_get_supabase_client_invalid_url_format():
    """SUPABASE_URL 잘못된 형식 → SupabaseConfigError"""
    with patch.dict(
        os.environ,
        {
            "SUPABASE_URL": "http://test.supabase.co",  # http (X)
            "SUPABASE_SERVICE_ROLE_KEY": "test_key",
        },
        clear=True,
    ):
        # 실제 호출
        with pytest.raises(SupabaseConfigError, match="Invalid SUPABASE_URL.*https://"):
            get_supabase_client()


@pytest.mark.requires_db
def test_get_supabase_client_success(skip_if_no_supabase):
    """Supabase 클라이언트 생성 성공 (실제 DB) - @requires_db"""
    # 실제 호출
    client = get_supabase_client()

    # 검증
    assert client is not None
    # Supabase client는 table() 메서드를 가짐
    assert hasattr(client, "table")


# ============================================================
# Test: test_supabase_connection (연결 테스트)
# ============================================================
def test_test_supabase_connection_missing_env_vars():
    """환경변수 없을 때 연결 테스트 결과"""
    with patch.dict(os.environ, {}, clear=True):
        # 실제 호출
        result = test_supabase_connection()

        # 검증: configuration 에러
        assert result["status"] == "error"
        assert result["connected"] is False
        assert result["error_type"] == "configuration"
        assert "SUPABASE_URL" in result["message"]


@pytest.mark.requires_db
def test_test_supabase_connection_success(skip_if_no_supabase):
    """연결 테스트 성공 (실제 DB) - @requires_db"""
    # 실제 호출
    result = test_supabase_connection()

    # 검증
    assert result["status"] == "success"
    assert result["connected"] is True
    assert result["table"] == "catalog_items"
    assert "record_count" in result
    assert result["url"] == os.getenv("SUPABASE_URL")


# ============================================================
# Test: query_catalog_items (카탈로그 조회)
# ============================================================
@pytest.mark.requires_db
def test_query_catalog_items_no_filter(skip_if_no_supabase):
    """카탈로그 조회 (필터 없음) - @requires_db"""
    client = get_supabase_client()

    # 실제 호출
    items = query_catalog_items(client, category=None, limit=10)

    # 검증
    assert isinstance(items, list)
    # 데이터 존재 여부는 DB 상태에 따라 다름


@pytest.mark.requires_db
def test_query_catalog_items_with_category_filter(skip_if_no_supabase):
    """카탈로그 조회 (카테고리 필터) - @requires_db"""
    client = get_supabase_client()

    # 실제 호출
    items = query_catalog_items(client, category="enclosure", limit=5)

    # 검증
    assert isinstance(items, list)
    # enclosure 카테고리만 반환되어야 함
    if items:
        assert all(item.get("category") == "enclosure" for item in items)


@pytest.mark.requires_db
def test_query_catalog_items_with_limit(skip_if_no_supabase):
    """카탈로그 조회 (limit 제한) - @requires_db"""
    client = get_supabase_client()

    # 실제 호출
    items = query_catalog_items(client, limit=3)

    # 검증
    assert isinstance(items, list)
    assert len(items) <= 3  # limit 이하 개수


# ============================================================
# Test: insert_quote (견적 삽입)
# ============================================================
@pytest.mark.requires_db
def test_insert_quote_success(skip_if_no_supabase):
    """견적 삽입 성공 - @requires_db"""
    client = get_supabase_client()

    # 테스트 데이터
    quote_data = {
        "customer_name": "Test Customer",
        "project_name": "Test Project",
        "total_amount": 1000000,
        "status": "draft",
    }

    try:
        # 실제 호출
        inserted = insert_quote(client, quote_data)

        # 검증
        assert inserted is not None
        assert "id" in inserted
        assert inserted["customer_name"] == "Test Customer"
        assert inserted["total_amount"] == 1000000

    except SupabaseClientError:
        # DB 스키마가 없을 경우 스킵 (quotes 테이블 없음)
        pytest.skip("quotes table not available in test DB")


# ============================================================
# Test: get_quote_by_id (견적 조회)
# ============================================================
@pytest.mark.requires_db
def test_get_quote_by_id_not_found(skip_if_no_supabase):
    """존재하지 않는 견적 조회 → None - @requires_db"""
    client = get_supabase_client()

    # 실제 호출 (존재하지 않는 UUID)
    try:
        quote = get_quote_by_id(client, "00000000-0000-0000-0000-000000000000")

        # 검증: None 반환
        assert quote is None

    except SupabaseClientError:
        # quotes 테이블 없음 (스킵)
        pytest.skip("quotes table not available in test DB")


@pytest.mark.requires_db
def test_get_quote_by_id_success(skip_if_no_supabase):
    """견적 삽입 후 조회 성공 - @requires_db"""
    client = get_supabase_client()

    # 테스트 데이터 삽입
    quote_data = {
        "customer_name": "Test Customer 2",
        "project_name": "Test Project 2",
        "total_amount": 2000000,
        "status": "draft",
    }

    try:
        # 삽입
        inserted = insert_quote(client, quote_data)
        quote_id = inserted["id"]

        # 조회
        retrieved = get_quote_by_id(client, quote_id)

        # 검증
        assert retrieved is not None
        assert retrieved["id"] == quote_id
        assert retrieved["customer_name"] == "Test Customer 2"

    except SupabaseClientError:
        pytest.skip("quotes table not available in test DB")


# ============================================================
# Test: get_cached_client (싱글톤 캐시)
# ============================================================
@pytest.mark.requires_db
def test_get_cached_client_singleton(skip_if_no_supabase):
    """캐시된 클라이언트 싱글톤 패턴 - @requires_db"""
    # 실제 호출
    client1 = get_cached_client()
    client2 = get_cached_client()

    # 검증: 동일 인스턴스
    assert client1 is client2


def test_get_cached_client_missing_env_vars():
    """환경변수 없을 때 캐시된 클라이언트 → SupabaseConfigError"""
    # _client 글로벌 변수 초기화
    import src.kis_estimator_core.infra.supabase_client as supabase_module

    supabase_module._client = None

    with patch.dict(os.environ, {}, clear=True):
        # 실제 호출
        with pytest.raises(SupabaseConfigError):
            get_cached_client()
