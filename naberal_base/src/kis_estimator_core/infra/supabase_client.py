"""
Supabase Client for KIS Estimator
Real Supabase connection - NO MOCKS
"""

import os

from dotenv import load_dotenv

from supabase import Client, create_client

# Load environment variables
load_dotenv()


class SupabaseClientError(Exception):
    """Supabase client error"""

    pass


class SupabaseConnectionError(SupabaseClientError):
    """Supabase connection error"""

    pass


class SupabaseConfigError(SupabaseClientError):
    """Supabase configuration error"""

    pass


def get_supabase_client() -> Client:
    """
    Get Supabase client instance with real connection

    Returns:
        Client: Supabase client instance

    Raises:
        SupabaseConfigError: If required environment variables are missing
        SupabaseConnectionError: If connection fails

    Environment Variables Required:
        SUPABASE_URL: Supabase project URL
        SUPABASE_SERVICE_ROLE_KEY: Service role key for full access
    """
    # Validate environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        raise SupabaseConfigError(
            "SUPABASE_URL environment variable is missing. "
            "Please set it in .env file."
        )

    if not service_role_key:
        raise SupabaseConfigError(
            "SUPABASE_SERVICE_ROLE_KEY environment variable is missing. "
            "Please set it in .env file."
        )

    # Validate URL format
    if not supabase_url.startswith("https://"):
        raise SupabaseConfigError(
            f"Invalid SUPABASE_URL format: {supabase_url}. "
            "Must start with 'https://'"
        )

    try:
        # Create real Supabase client
        client = create_client(supabase_url, service_role_key)
        return client

    except Exception as e:
        raise SupabaseConnectionError(f"Failed to connect to Supabase: {str(e)}") from e


def test_supabase_connection() -> dict:
    """
    Test Supabase connection by querying catalog_items table

    Returns:
        dict: Connection test result with status and details

    Raises:
        SupabaseClientError: If connection test fails
    """
    try:
        client = get_supabase_client()

        # Test query: Get count of catalog_items
        response = (
            client.table("catalog_items").select("*", count="exact").limit(1).execute()
        )

        return {
            "status": "success",
            "connected": True,
            "table": "catalog_items",
            "record_count": response.count,
            "url": os.getenv("SUPABASE_URL"),
            "message": "Supabase connection successful",
        }

    except SupabaseConfigError as e:
        return {
            "status": "error",
            "connected": False,
            "error_type": "configuration",
            "message": str(e),
        }

    except SupabaseConnectionError as e:
        return {
            "status": "error",
            "connected": False,
            "error_type": "connection",
            "message": str(e),
        }

    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error_type": "unknown",
            "message": str(e),
        }


def query_catalog_items(
    client: Client, category: str | None = None, limit: int = 100
) -> list:
    """
    Query catalog items from Supabase

    Args:
        client: Supabase client instance
        category: Optional category filter (e.g., 'enclosure', 'breaker')
        limit: Maximum number of results

    Returns:
        list: Catalog items

    Raises:
        SupabaseClientError: If query fails
    """
    try:
        query = client.table("catalog_items").select("*")

        if category:
            query = query.eq("category", category)

        query = query.limit(limit)
        response = query.execute()

        return response.data

    except Exception as e:
        raise SupabaseClientError(f"Failed to query catalog_items: {str(e)}") from e


def insert_quote(client: Client, quote_data: dict) -> dict:
    """
    Insert quote into Supabase

    Args:
        client: Supabase client instance
        quote_data: Quote data dictionary

    Returns:
        dict: Inserted quote with id

    Raises:
        SupabaseClientError: If insert fails
    """
    try:
        response = client.table("quotes").insert(quote_data).execute()

        if not response.data:
            raise SupabaseClientError("Insert failed: No data returned")

        return response.data[0]

    except Exception as e:
        raise SupabaseClientError(f"Failed to insert quote: {str(e)}") from e


def get_quote_by_id(client: Client, quote_id: str) -> dict | None:
    """
    Get quote by ID from Supabase

    Args:
        client: Supabase client instance
        quote_id: Quote UUID

    Returns:
        dict: Quote data or None if not found

    Raises:
        SupabaseClientError: If query fails
    """
    try:
        response = client.table("quotes").select("*").eq("id", quote_id).execute()

        if not response.data:
            return None

        return response.data[0]

    except Exception as e:
        raise SupabaseClientError(f"Failed to get quote: {str(e)}") from e


# Singleton instance (optional, for convenience)
_client: Client | None = None


def get_cached_client() -> Client:
    """
    Get cached Supabase client instance

    Returns:
        Client: Cached Supabase client
    """
    global _client

    if _client is None:
        _client = get_supabase_client()

    return _client


if __name__ == "__main__":
    # Connection test
    print("Testing Supabase connection...")
    result = test_supabase_connection()

    print(f"\nStatus: {result['status']}")
    print(f"Connected: {result['connected']}")

    if result["connected"]:
        print(f"Table: {result['table']}")
        print(f"Record Count: {result['record_count']}")
        print(f"URL: {result['url']}")
    else:
        print(f"Error Type: {result['error_type']}")
        print(f"Message: {result['message']}")
