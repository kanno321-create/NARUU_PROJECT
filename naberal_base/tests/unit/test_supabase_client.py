"""
Unit Tests for infra/supabase_client.py
Coverage target: >70% for Supabase client functions

Zero-Mock exception: Unit tests may use unittest.mock for external Supabase calls
to avoid requiring real Supabase connection in CI environment.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestSupabaseClientExceptions:
    """Tests for Supabase client exceptions"""

    def test_supabase_client_error_inheritance(self):
        """Test SupabaseClientError is proper Exception"""
        from kis_estimator_core.infra.supabase_client import SupabaseClientError

        error = SupabaseClientError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_supabase_connection_error_inheritance(self):
        """Test SupabaseConnectionError inherits from SupabaseClientError"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseClientError,
            SupabaseConnectionError,
        )

        error = SupabaseConnectionError("connection failed")
        assert isinstance(error, SupabaseClientError)
        assert isinstance(error, Exception)
        assert str(error) == "connection failed"

    def test_supabase_config_error_inheritance(self):
        """Test SupabaseConfigError inherits from SupabaseClientError"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseClientError,
            SupabaseConfigError,
        )

        error = SupabaseConfigError("config missing")
        assert isinstance(error, SupabaseClientError)
        assert isinstance(error, Exception)
        assert str(error) == "config missing"


class TestGetSupabaseClient:
    """Tests for get_supabase_client function"""

    def test_missing_supabase_url_raises_config_error(self):
        """Test that missing SUPABASE_URL raises SupabaseConfigError"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseConfigError,
            get_supabase_client,
        )

        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing env vars
            if "SUPABASE_URL" in os.environ:
                del os.environ["SUPABASE_URL"]
            if "SUPABASE_SERVICE_ROLE_KEY" in os.environ:
                del os.environ["SUPABASE_SERVICE_ROLE_KEY"]

            with pytest.raises(SupabaseConfigError) as exc_info:
                get_supabase_client()

            assert "SUPABASE_URL" in str(exc_info.value)

    def test_missing_service_role_key_raises_config_error(self):
        """Test that missing SUPABASE_SERVICE_ROLE_KEY raises SupabaseConfigError"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseConfigError,
            get_supabase_client,
        )

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co"}, clear=True
        ):
            with pytest.raises(SupabaseConfigError) as exc_info:
                get_supabase_client()

            assert "SUPABASE_SERVICE_ROLE_KEY" in str(exc_info.value)

    def test_invalid_url_format_raises_config_error(self):
        """Test that invalid URL format raises SupabaseConfigError"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseConfigError,
            get_supabase_client,
        )

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "http://test.supabase.co",  # http instead of https
                "SUPABASE_SERVICE_ROLE_KEY": "test-key",
            },
            clear=True,
        ):
            with pytest.raises(SupabaseConfigError) as exc_info:
                get_supabase_client()

            assert "https://" in str(exc_info.value)

    @patch("kis_estimator_core.infra.supabase_client.create_client")
    def test_successful_client_creation(self, mock_create_client):
        """Test successful Supabase client creation"""
        from kis_estimator_core.infra.supabase_client import get_supabase_client

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
            },
            clear=True,
        ):
            client = get_supabase_client()

            mock_create_client.assert_called_once_with(
                "https://test.supabase.co", "test-service-role-key"
            )
            assert client == mock_client

    @patch("kis_estimator_core.infra.supabase_client.create_client")
    def test_connection_error_on_create_failure(self, mock_create_client):
        """Test SupabaseConnectionError when create_client fails"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseConnectionError,
            get_supabase_client,
        )

        mock_create_client.side_effect = Exception("Network error")

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_SERVICE_ROLE_KEY": "test-key",
            },
            clear=True,
        ):
            with pytest.raises(SupabaseConnectionError) as exc_info:
                get_supabase_client()

            assert "Network error" in str(exc_info.value)


class TestTestSupabaseConnection:
    """Tests for test_supabase_connection function"""

    @patch("kis_estimator_core.infra.supabase_client.get_supabase_client")
    def test_successful_connection(self, mock_get_client):
        """Test successful connection test"""
        from kis_estimator_core.infra.supabase_client import test_supabase_connection

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.count = 100
        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            mock_response
        )
        mock_get_client.return_value = mock_client

        with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co"}):
            result = test_supabase_connection()

        assert result["status"] == "success"
        assert result["connected"] is True
        assert result["table"] == "catalog_items"
        assert result["record_count"] == 100

    @patch("kis_estimator_core.infra.supabase_client.get_supabase_client")
    def test_config_error_returns_error_dict(self, mock_get_client):
        """Test configuration error returns proper error dict"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseConfigError,
            test_supabase_connection,
        )

        mock_get_client.side_effect = SupabaseConfigError("Missing URL")

        result = test_supabase_connection()

        assert result["status"] == "error"
        assert result["connected"] is False
        assert result["error_type"] == "configuration"
        assert "Missing URL" in result["message"]

    @patch("kis_estimator_core.infra.supabase_client.get_supabase_client")
    def test_connection_error_returns_error_dict(self, mock_get_client):
        """Test connection error returns proper error dict"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseConnectionError,
            test_supabase_connection,
        )

        mock_get_client.side_effect = SupabaseConnectionError("Connection refused")

        result = test_supabase_connection()

        assert result["status"] == "error"
        assert result["connected"] is False
        assert result["error_type"] == "connection"
        assert "Connection refused" in result["message"]

    @patch("kis_estimator_core.infra.supabase_client.get_supabase_client")
    def test_unknown_error_returns_error_dict(self, mock_get_client):
        """Test unknown error returns proper error dict"""
        from kis_estimator_core.infra.supabase_client import test_supabase_connection

        mock_get_client.side_effect = RuntimeError("Unknown error")

        result = test_supabase_connection()

        assert result["status"] == "error"
        assert result["connected"] is False
        assert result["error_type"] == "unknown"


class TestQueryCatalogItems:
    """Tests for query_catalog_items function"""

    def test_query_without_category(self):
        """Test query without category filter"""
        from kis_estimator_core.infra.supabase_client import query_catalog_items

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]

        mock_query = MagicMock()
        mock_query.limit.return_value.execute.return_value = mock_response
        mock_client.table.return_value.select.return_value = mock_query

        result = query_catalog_items(mock_client)

        assert len(result) == 2
        mock_client.table.assert_called_with("catalog_items")

    def test_query_with_category(self):
        """Test query with category filter"""
        from kis_estimator_core.infra.supabase_client import query_catalog_items

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": 1, "category": "breaker"}]

        mock_query = MagicMock()
        mock_query.eq.return_value.limit.return_value.execute.return_value = mock_response
        mock_client.table.return_value.select.return_value = mock_query

        result = query_catalog_items(mock_client, category="breaker")

        assert len(result) == 1
        mock_query.eq.assert_called_with("category", "breaker")

    def test_query_with_limit(self):
        """Test query with custom limit"""
        from kis_estimator_core.infra.supabase_client import query_catalog_items

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []

        mock_query = MagicMock()
        mock_query.limit.return_value.execute.return_value = mock_response
        mock_client.table.return_value.select.return_value = mock_query

        query_catalog_items(mock_client, limit=50)

        mock_query.limit.assert_called_with(50)

    def test_query_raises_client_error_on_failure(self):
        """Test query raises SupabaseClientError on failure"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseClientError,
            query_catalog_items,
        )

        mock_client = MagicMock()
        mock_client.table.return_value.select.side_effect = Exception("Query failed")

        with pytest.raises(SupabaseClientError) as exc_info:
            query_catalog_items(mock_client)

        assert "Query failed" in str(exc_info.value)


class TestInsertQuote:
    """Tests for insert_quote function"""

    def test_successful_insert(self):
        """Test successful quote insertion"""
        from kis_estimator_core.infra.supabase_client import insert_quote

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "uuid-123", "customer": "Test"}]
        mock_client.table.return_value.insert.return_value.execute.return_value = (
            mock_response
        )

        result = insert_quote(mock_client, {"customer": "Test"})

        assert result["id"] == "uuid-123"
        mock_client.table.assert_called_with("quotes")

    def test_insert_raises_error_on_empty_response(self):
        """Test insert raises error when no data returned"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseClientError,
            insert_quote,
        )

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []  # Empty response
        mock_client.table.return_value.insert.return_value.execute.return_value = (
            mock_response
        )

        with pytest.raises(SupabaseClientError) as exc_info:
            insert_quote(mock_client, {"customer": "Test"})

        assert "No data returned" in str(exc_info.value)

    def test_insert_raises_error_on_failure(self):
        """Test insert raises error on exception"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseClientError,
            insert_quote,
        )

        mock_client = MagicMock()
        mock_client.table.return_value.insert.side_effect = Exception("Insert failed")

        with pytest.raises(SupabaseClientError) as exc_info:
            insert_quote(mock_client, {"customer": "Test"})

        assert "Insert failed" in str(exc_info.value)


class TestGetQuoteById:
    """Tests for get_quote_by_id function"""

    def test_get_existing_quote(self):
        """Test getting existing quote"""
        from kis_estimator_core.infra.supabase_client import get_quote_by_id

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "uuid-123", "customer": "Test"}]
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        result = get_quote_by_id(mock_client, "uuid-123")

        assert result["id"] == "uuid-123"
        mock_client.table.return_value.select.return_value.eq.assert_called_with(
            "id", "uuid-123"
        )

    def test_get_nonexistent_quote_returns_none(self):
        """Test getting non-existent quote returns None"""
        from kis_estimator_core.infra.supabase_client import get_quote_by_id

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        result = get_quote_by_id(mock_client, "nonexistent-id")

        assert result is None

    def test_get_raises_error_on_failure(self):
        """Test get raises error on exception"""
        from kis_estimator_core.infra.supabase_client import (
            SupabaseClientError,
            get_quote_by_id,
        )

        mock_client = MagicMock()
        mock_client.table.return_value.select.side_effect = Exception("Query failed")

        with pytest.raises(SupabaseClientError) as exc_info:
            get_quote_by_id(mock_client, "uuid-123")

        assert "Query failed" in str(exc_info.value)


class TestGetCachedClient:
    """Tests for get_cached_client function"""

    @patch("kis_estimator_core.infra.supabase_client.get_supabase_client")
    def test_cached_client_singleton(self, mock_get_client):
        """Test cached client returns singleton"""
        import kis_estimator_core.infra.supabase_client as module

        # Reset singleton
        module._client = None

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # First call creates client
        client1 = module.get_cached_client()
        # Second call returns same client
        client2 = module.get_cached_client()

        assert client1 is client2
        # get_supabase_client called only once
        mock_get_client.assert_called_once()

        # Cleanup
        module._client = None
