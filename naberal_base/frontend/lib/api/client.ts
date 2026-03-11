/**
 * KIS Estimator API Client
 * Contract-First HTTP client with typed responses
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public hint?: string,
    public traceId?: string,
    public meta?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface RequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: unknown;
  signal?: AbortSignal;
}

export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = { ...this.defaultHeaders, ...options.headers };

    const fetchOptions: RequestInit = {
      method: options.method,
      headers,
      signal: options.signal,
    };

    if (options.body && options.method !== 'GET') {
      fetchOptions.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, fetchOptions);

      // Parse response body
      const contentType = response.headers.get('content-type');
      let data: unknown;

      if (contentType?.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      // Handle error responses
      if (!response.ok) {
        if (typeof data === 'object' && data !== null) {
          const errorData = data as {
            code?: string;
            message?: string;
            hint?: string;
            traceId?: string;
            meta?: Record<string, unknown>;
          };

          throw new ApiError(
            errorData.message || `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            errorData.code,
            errorData.hint,
            errorData.traceId,
            errorData.meta
          );
        }

        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status
        );
      }

      return data as T;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof Error) {
        throw new ApiError(
          error.message,
          0,
          'NETWORK_ERROR',
          'Failed to connect to API server'
        );
      }

      throw new ApiError(
        'Unknown error occurred',
        0,
        'UNKNOWN_ERROR'
      );
    }
  }

  async get<T>(
    endpoint: string,
    options?: { headers?: Record<string, string>; signal?: AbortSignal }
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'GET',
      ...options,
    });
  }

  async post<T>(
    endpoint: string,
    body?: unknown,
    options?: { headers?: Record<string, string>; signal?: AbortSignal }
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body,
      ...options,
    });
  }

  async put<T>(
    endpoint: string,
    body?: unknown,
    options?: { headers?: Record<string, string>; signal?: AbortSignal }
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body,
      ...options,
    });
  }

  async delete<T>(
    endpoint: string,
    options?: { headers?: Record<string, string>; signal?: AbortSignal }
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
      ...options,
    });
  }

  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken(): void {
    delete this.defaultHeaders['Authorization'];
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }
}

// Default singleton instance
export const apiClient = new ApiClient();
