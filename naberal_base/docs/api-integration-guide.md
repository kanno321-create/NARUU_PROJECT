# KIS Estimator API Integration Guide

API 클라이언트 통합 가이드 (v2.0.0)

## 1. 개요

KIS Estimator API는 전기 패널 견적 시스템을 위한 RESTful API입니다.

### 1.1 Base URL

| 환경 | URL |
|------|-----|
| Production | `https://api.kis-estimator.com/v1` |
| Staging | `https://staging-api.kis-estimator.com/v1` |
| Local Dev | `http://localhost:8000/v1` |

### 1.2 OpenAPI Specification

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## 2. 인증

### 2.1 JWT Bearer Token

```http
Authorization: Bearer <jwt_token>
```

JWT 토큰은 Supabase Auth 또는 자체 인증 서버에서 발급받습니다.

**토큰 구조**:
```json
{
  "sub": "user-uuid",
  "role": "authenticated",
  "email": "user@example.com",
  "exp": 1735084800
}
```

### 2.2 API Key (서비스 간 통신)

```http
X-API-Key: <api_key>
```

API Key는 관리자 콘솔에서 발급받습니다.

### 2.3 인증 예시

```bash
# JWT Token
curl -X GET "https://api.kis-estimator.com/v1/quotes/123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# API Key
curl -X GET "https://api.kis-estimator.com/v1/quotes/123" \
  -H "X-API-Key: sk_live_abc123..."
```

## 3. API 엔드포인트

### 3.1 Health Check

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/v1/health/live` | Liveness probe (서버 실행 여부) |
| GET | `/v1/health/ready` | Readiness probe (DB 연결 상태 포함) |

```bash
# Liveness Check
curl https://api.kis-estimator.com/v1/health/live

# Response
{
  "status": "ok",
  "service": "kis-estimator-api",
  "version": "2.0.0"
}
```

### 3.2 Estimates API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/v1/estimates` | 견적 생성 (FIX-4 파이프라인) |
| GET | `/v1/estimates/{id}` | 견적 조회 |
| POST | `/v1/estimates/validate` | 견적 검증 (7가지 체크) |

**견적 생성 예시**:
```bash
curl -X POST "https://api.kis-estimator.com/v1/estimates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "ABC건설",
    "project_name": "신축 아파트",
    "panels": [
      {
        "panel_name": "분전반1",
        "main_breaker": {
          "model": "SBE-104",
          "ampere": 75,
          "poles": 4,
          "quantity": 1
        },
        "branch_breakers": [
          {"model": "SBE-102", "ampere": 30, "poles": 2, "quantity": 5}
        ],
        "enclosure": {
          "type": "옥내노출",
          "material": "STEEL 1.6T"
        }
      }
    ]
  }'
```

### 3.3 Quotes API (Phase X)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/v1/quotes` | Quote 생성 |
| GET | `/v1/quotes/{id}` | Quote 조회 |
| POST | `/v1/quotes/{id}/approve` | Quote 승인 |
| POST | `/v1/quotes/{id}/pdf` | PDF 생성 |
| GET | `/v1/quotes/{id}/url` | PDF URL 조회 |

**Quote 생성 예시**:
```bash
curl -X POST "https://api.kis-estimator.com/v1/quotes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "sku": "SBE-104-75A",
        "quantity": 10,
        "unit_price": 12500,
        "uom": "EA",
        "discount_tier": "A"
      }
    ],
    "client": "삼성전자",
    "terms_ref": "NET30"
  }'

# Response (201 Created)
{
  "quote_id": "550e8400-e29b-41d4-a716-446655440000",
  "totals": {
    "subtotal": 125000,
    "discount": 12500,
    "vat": 11250,
    "total": 123750,
    "currency": "KRW"
  },
  "approval_required": false,
  "evidence_hash": "a3b2c1d4e5f6...",
  "created_at": "2025-11-29T10:30:00+09:00"
}
```

**Quote 승인 예시**:
```bash
curl -X POST "https://api.kis-estimator.com/v1/quotes/550e8400.../approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "actor": "admin@example.com",
    "comment": "가격 검토 완료"
  }'

# Response (200 OK)
{
  "quote_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "APPROVED",
  "approved_at": "2025-11-29T11:00:00+09:00",
  "approved_by": "admin@example.com",
  "evidence_entry": "audit-123e4567..."
}
```

### 3.4 Catalog API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/v1/catalog/breakers` | 차단기 카탈로그 조회 |
| GET | `/v1/catalog/enclosures` | 외함 카탈로그 조회 |
| GET | `/v1/catalog/accessories` | 부속자재 카탈로그 조회 |

### 3.5 AI Chat API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/v1/ai/chat` | 자연어 기반 견적 요청 |

```bash
curl -X POST "https://api.kis-estimator.com/v1/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "4P 100A 메인차단기와 2P 30A 분기 5개로 견적 만들어줘"
  }'
```

## 4. 응답 형식

### 4.1 성공 응답

```json
{
  "quote_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "APPROVED",
  "data": { ... }
}
```

### 4.2 에러 응답

```json
{
  "code": "E_VALIDATION",
  "message": "Invalid UOM 'INVALID'",
  "hint": "Valid UOMs: EA, KG, M, 식, 면",
  "traceId": "trace-123456",
  "meta": {
    "field": "items[0].uom"
  }
}
```

### 4.3 에러 코드 목록

| 코드 | HTTP 상태 | 설명 |
|------|-----------|------|
| `E_VALIDATION` | 400 | 입력 검증 실패 |
| `E_NOT_FOUND` | 404 | 리소스 없음 |
| `E_CONFLICT` | 409 | 상태 충돌 (예: 이미 승인됨) |
| `E_AUTH_REQUIRED` | 401 | 인증 필요 |
| `E_RBAC` | 403 | 권한 없음 |
| `E_REDIS_RATE` | 429 | Rate Limit 초과 |
| `E_PDF_POLICY` | 422 | PDF 정책 위반 |
| `E_INTERNAL` | 500 | 서버 내부 오류 |

## 5. Rate Limiting

| 플랜 | 요청 제한 | 시간 단위 |
|------|-----------|-----------|
| Free | 100 | 시간당 |
| Pro | 1,000 | 시간당 |
| Enterprise | 10,000 | 시간당 |

**Rate Limit 헤더**:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1735084800
```

## 6. SDK & 클라이언트

### 6.1 Python

```python
import httpx

class KISClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    async def create_quote(self, items: list, client: str) -> dict:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                f"{self.base_url}/v1/quotes",
                headers=self.headers,
                json={"items": items, "client": client}
            )
            response.raise_for_status()
            return response.json()

# 사용 예시
client = KISClient("https://api.kis-estimator.com", "your-token")
quote = await client.create_quote(
    items=[{"sku": "SBE-104", "quantity": 1, "unit_price": 12500, "uom": "EA"}],
    client="ABC건설"
)
```

### 6.2 JavaScript/TypeScript

```typescript
const KIS_API_URL = "https://api.kis-estimator.com/v1";

interface QuoteCreateRequest {
  items: Array<{
    sku: string;
    quantity: number;
    unit_price: number;
    uom: string;
    discount_tier?: string;
  }>;
  client: string;
  terms_ref?: string;
}

async function createQuote(token: string, request: QuoteCreateRequest) {
  const response = await fetch(`${KIS_API_URL}/quotes`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`${error.code}: ${error.message}`);
  }

  return response.json();
}

// 사용 예시
const quote = await createQuote("your-token", {
  items: [{ sku: "SBE-104", quantity: 1, unit_price: 12500, uom: "EA" }],
  client: "ABC건설",
});
```

## 7. Webhook (준비 중)

Quote 상태 변경 시 Webhook 알림을 받을 수 있습니다.

```json
{
  "event": "quote.approved",
  "quote_id": "550e8400...",
  "timestamp": "2025-11-29T11:00:00Z",
  "data": {
    "approved_by": "admin@example.com",
    "total": 123750
  }
}
```

## 8. Best Practices

### 8.1 에러 처리

```python
try:
    quote = await client.create_quote(...)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 400:
        error = e.response.json()
        print(f"Validation error: {error['message']}")
        print(f"Hint: {error['hint']}")
    elif e.response.status_code == 429:
        # Rate limit - 재시도
        retry_after = e.response.headers.get("Retry-After", 60)
        await asyncio.sleep(int(retry_after))
```

### 8.2 재시도 로직

```python
import tenacity

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
    retry=tenacity.retry_if_exception_type(httpx.HTTPStatusError),
)
async def create_quote_with_retry(client, **kwargs):
    return await client.create_quote(**kwargs)
```

### 8.3 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_catalog_breakers():
    """차단기 카탈로그는 자주 변경되지 않으므로 캐싱"""
    response = httpx.get(f"{KIS_API_URL}/catalog/breakers")
    return response.json()
```

## 9. 지원 및 문의

- **API 문서**: https://api.kis-estimator.com/docs
- **GitHub Issues**: https://github.com/naberal/kis-estimator/issues
- **이메일**: api-support@naberal.com

---

*문서 버전: v2.0.0 / 최종 수정: 2025-11-29*
