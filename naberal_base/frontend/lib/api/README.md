# KIS Estimator API Client

Contract-First TypeScript API client for KIS Estimator frontend.

## Overview

This API client provides fully-typed interfaces to the KIS Estimator backend API. All types are derived from the OpenAPI 3.1 specification and follow Contract-First principles.

## Directory Structure

```
lib/
├── api/
│   ├── client.ts          # Base HTTP client with error handling
│   ├── health.ts          # Health check endpoints
│   ├── catalog.ts         # Catalog operations (breakers, enclosures, accessories)
│   ├── estimates.ts       # Estimation pipeline (FIX-4)
│   ├── quotes.ts          # Quote management and approval
│   ├── ai-chat.ts         # AI chat interface
│   └── index.ts           # Unified exports
└── types/
    ├── api.ts             # Core API types (errors, pagination)
    ├── catalog.ts         # Catalog data models
    ├── estimate.ts        # Estimation types
    ├── quote.ts           # Quote types
    └── index.ts           # Unified type exports
```

## Quick Start

### Basic Usage

```typescript
import { apiClient, getHealth } from '@/lib/api';

// Health check
const health = await getHealth();
console.log(health.status); // 'healthy'

// Configure base URL (optional, uses NEXT_PUBLIC_API_URL env var)
apiClient.setBaseUrl('http://localhost:8000');

// Set authentication token
apiClient.setAuthToken('your-jwt-token');
```

### Catalog Operations

```typescript
import { getBreakers, getEnclosures, getAccessories } from '@/lib/api';

// Get breakers with filters
const breakers = await getBreakers({
  category: 'MCCB',
  brand: 'SANGDO',
  poles: 4,
  frameMin: 100,
  frameMax: 250,
});

// Search enclosures
const enclosures = await searchEnclosures('600*800*200');

// Get accessories by type
const magnets = await getAccessories({ type: 'MAGNET' });
```

### Creating Estimates

```typescript
import { createEstimate, validateEstimate } from '@/lib/api';
import type { EstimateRequest } from '@/lib/types';

const request: EstimateRequest = {
  panels: [
    {
      name: '분전반1',
      mainBreaker: {
        category: 'MCCB',
        poles: 4,
        ampere: 100,
        economy: 'economy',
      },
      branchBreakers: [
        { category: 'ELB', poles: 2, ampere: 20, quantity: 10 },
        { category: 'MCCB', poles: 3, ampere: 30, quantity: 5 },
      ],
    },
  ],
  customer: {
    name: '고객사명',
    projectName: '프로젝트명',
  },
};

// Validate first (optional)
const validation = await validateEstimate({ panels: request.panels });
if (validation.valid) {
  // Create estimate
  const estimate = await createEstimate(request);
  console.log(estimate.estimateId);
  console.log(estimate.summary.totalWithVat);
}
```

### Quote Management

```typescript
import { createQuote, approveQuote, generateQuotePdf } from '@/lib/api';

// Create quote from estimate
const quote = await createQuote({
  estimateId: 'est_123',
  customer: {
    name: '고객명',
    email: 'customer@example.com',
    company: '회사명',
  },
  projectName: '프로젝트명',
});

// Approve quote
await approveQuote(quote.quoteId, {
  approvedBy: '담당자명',
});

// Generate PDF
const pdf = await generateQuotePdf(quote.quoteId);
console.log(pdf.pdfUrl);
```

### AI Chat

```typescript
import { sendChatMessage, streamChatMessage } from '@/lib/api';

// One-shot chat
const response = await sendChatMessage({
  messages: [
    { role: 'user', content: '100A 4극 차단기 추천해줘' },
  ],
});

// Streaming chat
for await (const chunk of streamChatMessage({
  messages: [
    { role: 'user', content: '견적서 어떻게 작성하나요?' },
  ],
})) {
  console.log(chunk.message.content);
}
```

## Error Handling

All API functions throw `ApiError` on failure:

```typescript
import { ApiError, createEstimate } from '@/lib/api';

try {
  const estimate = await createEstimate(request);
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`Error ${error.status}: ${error.message}`);
    console.error(`Code: ${error.code}`);
    console.error(`Hint: ${error.hint}`);
    console.error(`Trace ID: ${error.traceId}`);
  }
}
```

## Pagination

All list endpoints return `PaginatedResponse`:

```typescript
import { listEstimates } from '@/lib/api';

const response = await listEstimates({
  page: 1,
  pageSize: 20,
  sortBy: 'createdAt',
  sortOrder: 'desc',
});

console.log(response.items); // EstimateListItem[]
console.log(response.total); // Total count
console.log(response.totalPages); // Total pages
```

## AbortSignal Support

All API functions support request cancellation:

```typescript
const controller = new AbortController();

// Start request
const promise = getBreakers({}, {}, controller.signal);

// Cancel after 5 seconds
setTimeout(() => controller.abort(), 5000);

try {
  const result = await promise;
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Request cancelled');
  }
}
```

## Environment Variables

Configure the API base URL:

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## TypeScript Support

All functions are fully typed:

```typescript
import type {
  BreakerCatalog,
  EstimateResponse,
  QuoteResponse,
  ValidationCheck,
} from '@/lib/types';

// Type inference works automatically
const breakers = await getBreakers(); // BreakerCatalog[]
const estimate = await createEstimate(req); // EstimateResponse
```

## Contract Compliance

This client follows Contract-First principles:

- **Zero Mocks**: All types match real API responses
- **OpenAPI Alignment**: Types derived from OpenAPI 3.1 spec
- **Evidence-Based**: All responses include traceId for debugging
- **Error Schema**: Standard error format with code/message/hint

## Health Monitoring

```typescript
import { getHealth, getLiveness, getReadiness } from '@/lib/api/health';

// Full health check
const health = await getHealth();

// Liveness probe (fast)
const alive = await getLiveness();

// Readiness probe (includes DB check)
const ready = await getReadiness();

// Quick boolean check
import { quickHealthCheck } from '@/lib/api/health';
const isHealthy = await quickHealthCheck(); // boolean
```

## Best Practices

1. **Use AbortSignal** for user-cancellable requests
2. **Validate before creating** estimates to catch errors early
3. **Handle ApiError** explicitly for better UX
4. **Use pagination** for large datasets
5. **Cache catalog data** (breakers, enclosures) as it changes infrequently
6. **Stream AI chat** responses for better perceived performance

## API Reference

See individual files for complete API documentation:

- **client.ts**: Base HTTP client, ApiError class
- **health.ts**: Health check endpoints
- **catalog.ts**: Catalog CRUD operations
- **estimates.ts**: FIX-4 pipeline execution
- **quotes.ts**: Quote lifecycle management
- **ai-chat.ts**: Conversational AI interface
