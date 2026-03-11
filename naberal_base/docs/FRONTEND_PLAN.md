# KIS Estimator Frontend 제작 계획서

**작성일**: 2025-11-30
**버전**: v1.0.0
**작성자**: 나베랄 감마 AI
**목표**: frontend-kis-complete.html 디자인 기반 Next.js 프론트엔드 구현

---

## 1. 개요

### 1.1 프로젝트 정의
- **목표**: 백엔드 API와 완벽 호환되는 프로덕션 프론트엔드 구축
- **참조 디자인**: `절대코어파일/frontend-kis-complete.html` (수정 금지, 참조용)
- **기술 스택**: Next.js 14 App Router + TypeScript + Tailwind CSS

### 1.2 핵심 원칙
```
Contract-First: OpenAPI 스키마 기반 타입 자동 생성
Evidence-Gated: 모든 API 호출 추적 및 증거 저장
Zero-Mock: 실제 API 연동만 (목업 금지)
SSOT: 상수/검증 규칙은 백엔드 SSOT와 동기화
```

---

## 2. 백엔드 API 분석 결과

### 2.1 엔드포인트 맵 (총 20+ 엔드포인트)

#### Health Check APIs
| 엔드포인트 | 메서드 | 설명 | 프론트 사용 |
|-----------|--------|------|------------|
| `/v1/health` | GET | 기본 헬스 체크 | 연결 상태 표시 |
| `/v1/health/live` | GET | 활성 상태 | 사이드바 상태 |
| `/v1/health/db` | GET | DB 연결 상태 | 관리자 대시보드 |
| `/v1/health/readyz` | GET | 준비 상태 | 초기 로딩 |

#### Catalog APIs (자재 카탈로그)
| 엔드포인트 | 메서드 | 설명 | 프론트 사용 |
|-----------|--------|------|------------|
| `/v1/catalog/items` | GET | 전체 카탈로그 | 자재 검색 |
| `/v1/catalog/breakers` | GET | 차단기 목록 | 차단기 선택 드롭다운 |
| `/v1/catalog/enclosures` | GET | 외함 목록 | 외함 선택 드롭다운 |
| `/v1/catalog/accessories` | GET | 부속자재 목록 | 부속자재 선택 |

**필터 파라미터** (차단기):
```typescript
interface BreakerFilter {
  category?: 'MCCB' | 'ELB';
  brand?: '상도' | 'LS';
  series?: '경제형' | '표준형';
  poles?: 2 | 3 | 4;
  frame?: 50 | 100 | 200 | 400 | 600 | 800;
}
```

#### Estimates APIs (견적)
| 엔드포인트 | 메서드 | 설명 | 프론트 사용 |
|-----------|--------|------|------------|
| `/v1/estimates` | POST | 견적 생성 | 견적 계산 버튼 |
| `/v1/estimates` | GET | 견적 목록 | 히스토리 탭 |
| `/v1/estimates/{id}` | GET | 견적 상세 | 견적 상세 보기 |
| `/v1/estimates/validate` | POST | 견적 검증 | 실시간 검증 |

**요청 스키마**:
```typescript
interface EstimateRequest {
  customer_name?: string;
  project_name?: string;
  panels: PanelInput[];
  options?: EstimateOptions;
}

interface PanelInput {
  panel_name: string;
  main_breaker: BreakerInput;
  branch_breakers: BreakerInput[];
  accessories?: AccessoryInput[];
  enclosure?: EnclosureInput;
}

interface BreakerInput {
  model: string;
  ampere: number;
  poles: number;
  quantity: number;
}
```

#### Quotes APIs (견적서 라이프사이클)
| 엔드포인트 | 메서드 | 설명 | 프론트 사용 |
|-----------|--------|------|------------|
| `/v1/quotes` | POST | 견적서 생성 | 견적서 저장 |
| `/v1/quotes` | GET | 견적서 목록 | 견적서 리스트 |
| `/v1/quotes/{id}` | GET | 견적서 상세 | 견적서 보기 |
| `/v1/quotes/{id}` | PUT | 견적서 수정 | 견적서 편집 |
| `/v1/quotes/{id}/approve` | POST | 견적서 승인 | 승인 버튼 |
| `/v1/quotes/{id}/pdf` | POST | PDF 생성 | PDF 다운로드 |
| `/v1/quotes/{id}/url` | GET | Pre-signed URL | PDF 공유 링크 |

#### AI Chat APIs (자연어 처리)
| 엔드포인트 | 메서드 | 설명 | 프론트 사용 |
|-----------|--------|------|------------|
| `/v1/ai/chat` | POST | AI 채팅 | Hero 입력창 |
| `/v1/ai/models` | GET | AI 모델 목록 | 모델 선택 |
| `/v1/ai/intents` | GET | 인텐트 목록 | 인텐트 가이드 |

**AI Chat 인텐트 분류**:
```typescript
type AIIntent =
  | 'estimate'    // 견적 관련 질문
  | 'drawing'     // 도면 관련
  | 'email'       // 이메일 작성
  | 'erp'         // ERP 연동
  | 'help'        // 도움말
  | 'knowledge';  // 지식 검색
```

---

## 3. 디자인 시스템

### 3.1 CSS Variables (frontend-kis-complete.html 참조)
```css
:root {
  /* Brand Colors */
  --color-brand: #10a37f;
  --color-brand-strong: #0e8f71;
  --color-brand-light: rgba(16, 163, 127, 0.1);

  /* Background */
  --color-bg: #f7f7f8;
  --color-surface: #ffffff;
  --color-surface-secondary: #f9f9f9;

  /* Border */
  --color-border: #e1dfdd;
  --color-border-light: #edebe9;

  /* Text */
  --color-text: #323130;
  --color-text-secondary: #605e5c;
  --color-text-tertiary: #a19f9d;

  /* Status Colors */
  --color-success: #107c10;
  --color-warning: #ffb900;
  --color-error: #d13438;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* Spacing */
  --sidebar-width: 280px;
  --sidebar-collapsed: 80px;
  --header-height: 60px;
}
```

### 3.2 Typography
```css
body {
  font-family: 'Segoe UI', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
}

/* Headings */
h1 { font-size: 24px; font-weight: 600; }
h2 { font-size: 20px; font-weight: 600; }
h3 { font-size: 16px; font-weight: 600; }

/* Labels */
.label { font-size: 13px; font-weight: 500; color: var(--color-text-secondary); }

/* Input */
input, select, textarea {
  font-size: 14px;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
```

### 3.3 Component Styles

#### Buttons
```css
.btn-primary {
  background: var(--color-brand);
  color: white;
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-weight: 500;
  transition: background 0.2s;
}
.btn-primary:hover {
  background: var(--color-brand-strong);
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
```

#### Cards
```css
.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);
}
```

---

## 4. 컴포넌트 구조

### 4.1 폴더 구조
```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home (Hero + Chat)
│   ├── quotes/
│   │   ├── page.tsx            # Quote list
│   │   └── [id]/
│   │       └── page.tsx        # Quote detail
│   ├── estimates/
│   │   └── page.tsx            # Estimate workspace
│   └── globals.css             # Global styles
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx         # Collapsible sidebar
│   │   ├── Header.tsx          # Top header
│   │   └── MainLayout.tsx      # Layout wrapper
│   ├── hero/
│   │   ├── HeroSection.tsx     # Hero section
│   │   └── ChatInput.tsx       # AI chat input
│   ├── quotes/
│   │   ├── QuoteTabs.tsx       # Multi-tab quote system
│   │   ├── QuoteTabContent.tsx # Tab content
│   │   ├── CustomerForm.tsx    # Customer info form
│   │   ├── EnclosureForm.tsx   # Enclosure form
│   │   ├── BreakerForm.tsx     # Breaker selection
│   │   ├── AccessoryForm.tsx   # Accessory selection
│   │   └── EstimatePreview.tsx # Estimate preview panel
│   ├── catalog/
│   │   ├── BreakerSelector.tsx # Breaker dropdown
│   │   ├── EnclosureSelector.tsx
│   │   └── AccessorySelector.tsx
│   └── common/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Select.tsx
│       ├── Card.tsx
│       └── LoadingSpinner.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts           # API client (fetch wrapper)
│   │   ├── health.ts           # Health API
│   │   ├── catalog.ts          # Catalog API
│   │   ├── estimates.ts        # Estimates API
│   │   ├── quotes.ts           # Quotes API
│   │   └── ai-chat.ts          # AI Chat API
│   ├── types/
│   │   ├── api.ts              # Generated from OpenAPI
│   │   ├── catalog.ts
│   │   ├── estimate.ts
│   │   └── quote.ts
│   ├── hooks/
│   │   ├── useQuoteTabs.ts     # Multi-tab state
│   │   ├── useCatalog.ts       # Catalog data hooks
│   │   └── useEstimate.ts      # Estimate calculation
│   └── utils/
│       ├── format.ts           # Number/currency formatting
│       └── validation.ts       # Form validation
├── public/
│   └── images/
└── package.json
```

### 4.2 주요 컴포넌트 명세

#### 4.2.1 Sidebar (280px ↔ 80px)
```typescript
interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

// 메뉴 항목
const menuItems = [
  { icon: 'home', label: '홈', path: '/' },
  { icon: 'calculator', label: '견적 작성', path: '/estimates' },
  { icon: 'folder', label: '견적서 관리', path: '/quotes' },
  { icon: 'catalog', label: '자재 카탈로그', path: '/catalog' },
  { icon: 'settings', label: '설정', path: '/settings' },
];
```

#### 4.2.2 Hero Section
```typescript
interface HeroSectionProps {
  onChatSubmit: (message: string) => Promise<void>;
  onQuickAction: (action: 'new-quote' | 'browse-catalog') => void;
}

// Hero 레이아웃
// - 타이틀: "NABERAL KIS Estimator"
// - 서브타이틀: "AI 기반 전기 패널 견적 시스템"
// - 채팅 입력창 (중앙 배치)
// - 빠른 액션 버튼들
```

#### 4.2.3 Quote Tabs (Multi-Tab System)
```typescript
interface Tab {
  id: number;
  title: string;
  customerInfo: CustomerInfo;
  enclosureInfo: EnclosureInfo;
  mainBreakerInfo: BreakerInfo;
  branchBreakers: BreakerItem[];
  accessories: AccessoryItem[];
  estimateVisible: boolean;
  estimateResult?: EstimateResponse;
}

interface QuoteTabsState {
  tabs: Tab[];
  activeTabId: number;
}

// 탭 작업
const tabActions = {
  addTab: () => void;
  closeTab: (id: number) => void;
  switchTab: (id: number) => void;
  updateTab: (id: number, data: Partial<Tab>) => void;
};
```

#### 4.2.4 Form Components

**CustomerForm**:
```typescript
interface CustomerInfo {
  company: string;      // 거래처명
  contact: string;      // 담당자
  email: string;        // 이메일
  phone: string;        // 전화번호
  address: string;      // 주소
  projectName: string;  // 건명
}
```

**EnclosureForm**:
```typescript
interface EnclosureInfo {
  type: '옥내노출' | '옥외노출' | '옥내자립' | '옥외자립' | '전주부착형' | '매입함';
  material: 'STEEL 1.6T' | 'SUS201 1.2T' | 'STEEL 1.0T';
  customSize?: { w: number; h: number; d: number };
  request: string;      // 특이사항
}
```

**BreakerForm**:
```typescript
interface BreakerInfo {
  type: 'MCCB' | 'ELB';
  brand: '상도' | 'LS';
  series: '경제형' | '표준형' | '소형';
  model: string;
  poles: 2 | 3 | 4;
  frame: number;
  ampere: number;
  quantity: number;
}
```

**AccessoryForm**:
```typescript
interface AccessoryItem {
  type: 'magnet' | 'timer' | 'meter' | 'spd' | 'ct';
  model: string;
  quantity: number;
  options?: Record<string, any>;
}
```

#### 4.2.5 Estimate Preview Panel
```typescript
interface EstimatePreviewProps {
  estimateResult: EstimateResponse | null;
  loading: boolean;
  onRecalculate: () => void;
  onSaveQuote: () => void;
  onDownloadPdf: () => void;
}

// 표시 항목
// - 외함 크기 (W×H×D)
// - 메인차단기 정보
// - 분기차단기 목록
// - 부속자재 목록
// - 합계 금액 (부가세 별도/포함)
// - 검증 결과 (7가지 체크)
```

---

## 5. 상태 관리

### 5.1 Global State (Zustand 또는 Context)
```typescript
interface AppState {
  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Quote Tabs
  tabs: Tab[];
  activeTabId: number;
  addTab: () => void;
  closeTab: (id: number) => void;
  setActiveTab: (id: number) => void;
  updateTab: (id: number, data: Partial<Tab>) => void;

  // Catalog Cache
  breakers: BreakerCatalog[];
  enclosures: EnclosureCatalog[];
  accessories: AccessoryCatalog[];
  loadCatalog: () => Promise<void>;

  // Health Status
  apiStatus: 'connected' | 'disconnected' | 'error';
  checkHealth: () => Promise<void>;
}
```

### 5.2 Tab State Flow
```
┌─────────────────────────────────────────────────────────────┐
│                      QuoteTabs                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───┐                 │
│  │ 견적서1 │ │ 견적서2 │ │ 견적서3 │ │ + │                 │
│  └────┬────┘ └─────────┘ └─────────┘ └───┘                 │
│       │                                                      │
│       ▼                                                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  TabContent                           │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │  │
│  │  │CustomerForm│ │EnclosureForm│ │BreakerForm │       │  │
│  │  └────────────┘ └────────────┘ └────────────┘       │  │
│  │  ┌────────────┐ ┌────────────────────────────┐      │  │
│  │  │AccessoryForm│ │   EstimatePreview          │      │  │
│  │  └────────────┘ │   (visible on calculate)    │      │  │
│  │                  └────────────────────────────┘      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. API 통합

### 6.1 API Client 설정
```typescript
// lib/api/client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiClientConfig {
  baseUrl: string;
  timeout: number;
  headers: Record<string, string>;
}

class ApiClient {
  private config: ApiClientConfig;

  constructor(config: Partial<ApiClientConfig> = {}) {
    this.config = {
      baseUrl: config.baseUrl || API_BASE_URL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
    };
  }

  async get<T>(path: string, params?: Record<string, any>): Promise<T> {
    const url = new URL(path, this.config.baseUrl);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) url.searchParams.set(key, String(value));
      });
    }
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: this.config.headers,
    });
    if (!response.ok) throw await this.handleError(response);
    return response.json();
  }

  async post<T>(path: string, data: any): Promise<T> {
    const response = await fetch(`${this.config.baseUrl}${path}`, {
      method: 'POST',
      headers: this.config.headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw await this.handleError(response);
    return response.json();
  }

  private async handleError(response: Response): Promise<Error> {
    const errorData = await response.json().catch(() => ({}));
    return new ApiError(
      errorData.code || 'E_UNKNOWN',
      errorData.message || 'Unknown error',
      errorData.hint,
      errorData.traceId
    );
  }
}

export const apiClient = new ApiClient();
```

### 6.2 API 함수 구현

**Catalog API**:
```typescript
// lib/api/catalog.ts
export const catalogApi = {
  getBreakers: (filter?: BreakerFilter) =>
    apiClient.get<BreakerCatalog[]>('/v1/catalog/breakers', filter),

  getEnclosures: (filter?: EnclosureFilter) =>
    apiClient.get<EnclosureCatalog[]>('/v1/catalog/enclosures', filter),

  getAccessories: (filter?: AccessoryFilter) =>
    apiClient.get<AccessoryCatalog[]>('/v1/catalog/accessories', filter),
};
```

**Estimates API**:
```typescript
// lib/api/estimates.ts
export const estimatesApi = {
  create: (request: EstimateRequest) =>
    apiClient.post<EstimateResponse>('/v1/estimates', request),

  validate: (request: EstimateRequest) =>
    apiClient.post<ValidationResult>('/v1/estimates/validate', request),

  getById: (id: string) =>
    apiClient.get<EstimateResponse>(`/v1/estimates/${id}`),

  list: (params?: { limit?: number; offset?: number }) =>
    apiClient.get<EstimateListResponse>('/v1/estimates', params),
};
```

**Quotes API**:
```typescript
// lib/api/quotes.ts
export const quotesApi = {
  create: (request: QuoteCreateRequest) =>
    apiClient.post<QuoteResponse>('/v1/quotes', request),

  getById: (id: string) =>
    apiClient.get<QuoteResponse>(`/v1/quotes/${id}`),

  update: (id: string, request: QuoteUpdateRequest) =>
    apiClient.put<QuoteResponse>(`/v1/quotes/${id}`, request),

  approve: (id: string) =>
    apiClient.post<QuoteResponse>(`/v1/quotes/${id}/approve`, {}),

  generatePdf: (id: string) =>
    apiClient.post<PdfResponse>(`/v1/quotes/${id}/pdf`, {}),

  getShareUrl: (id: string) =>
    apiClient.get<UrlResponse>(`/v1/quotes/${id}/url`),
};
```

**AI Chat API**:
```typescript
// lib/api/ai-chat.ts
export const aiChatApi = {
  send: (message: string, context?: ChatContext) =>
    apiClient.post<ChatResponse>('/v1/ai/chat', { message, context }),

  getModels: () =>
    apiClient.get<AIModel[]>('/v1/ai/models'),

  getIntents: () =>
    apiClient.get<AIIntent[]>('/v1/ai/intents'),
};
```

---

## 7. TypeScript 타입 정의

### 7.1 OpenAPI 기반 타입 생성
```bash
# OpenAPI에서 타입 자동 생성
npx openapi-typescript api/openapi.yaml -o lib/types/api.generated.ts
```

### 7.2 주요 타입 정의
```typescript
// lib/types/estimate.ts
export interface EstimateRequest {
  customer_name?: string;
  project_name?: string;
  panels: PanelInput[];
  options?: EstimateOptions;
}

export interface PanelInput {
  panel_name: string;
  main_breaker: BreakerInput;
  branch_breakers: BreakerInput[];
  accessories?: AccessoryInput[];
  enclosure?: EnclosureInput;
}

export interface BreakerInput {
  model: string;
  ampere: number;
  poles: number;
  quantity: number;
  phase_assignment?: 'R' | 'S' | 'T' | 'N';
}

export interface EnclosureInput {
  type: string;
  material: string;
  size?: { w: number; h: number; d: number };
}

export interface EstimateResponse {
  estimate_id: string;
  status: 'success' | 'partial' | 'failed';
  pipeline_results: {
    enclosure: EnclosureResult;
    breaker: BreakerResult;
    critic: CriticResult;
    format: FormatResult;
    cover: CoverResult;
  };
  validation_checks: ValidationCheck[];
  total_price: number;
  total_price_vat: number;
  documents: DocumentInfo[];
  evidence: EvidenceInfo;
}

export interface ValidationCheck {
  name: string;
  status: 'pass' | 'fail' | 'warning';
  message: string;
  details?: Record<string, any>;
}
```

---

## 8. 검증 규칙 통합

### 8.1 7가지 필수 검증 (백엔드 SSOT 동기화)
```typescript
// lib/validation/checks.ts
export const VALIDATION_CHECKS = {
  CHK_BUNDLE_MAGNET: {
    name: '마그네트 동반자재',
    description: '마그네트 존재 시 FUSEHOLDER/TERMINAL_BLOCK/PVC DUCT/CABLE_WIRE 포함 필수',
    severity: 'error',
  },
  CHK_ENCLOSURE_H_FORMULA: {
    name: '외함 높이 공식',
    description: 'H = P + 2D + S + M 공식 적용',
    severity: 'error',
  },
  CHK_PHASE_BALANCE: {
    name: '상평형',
    description: '상평형 ≤ 4%',
    severity: 'error',
  },
  CHK_CLEARANCE_VIOLATIONS: {
    name: '간섭 검사',
    description: '차단기 간 간섭 = 0',
    severity: 'error',
  },
  CHK_THERMAL_VIOLATIONS: {
    name: '열 밀도',
    description: '열 밀도 위반 = 0',
    severity: 'error',
  },
  CHK_FORMULA_PRESERVATION: {
    name: '수식 보존',
    description: 'Excel 수식 보존 = 100%',
    severity: 'error',
  },
  CHK_COVER_COMPLIANCE: {
    name: '표지 규칙',
    description: '표지 규칙 준수 = 100%',
    severity: 'error',
  },
};

// 프론트엔드 실시간 검증 (백엔드 검증 전 기본 체크)
export function validateEstimateInput(tab: Tab): ValidationResult[] {
  const results: ValidationResult[] = [];

  // 마그네트 동반자재 체크
  const hasMagnet = tab.accessories.some(a => a.type === 'magnet');
  if (hasMagnet) {
    const hasBundle = tab.accessories.some(a =>
      a.type === 'fuseholder' || a.type === 'terminal_block'
    );
    if (!hasBundle) {
      results.push({
        check: 'CHK_BUNDLE_MAGNET',
        status: 'warning',
        message: '마그네트 선택 시 동반자재가 자동 추가됩니다.',
      });
    }
  }

  // 필수 입력 체크
  if (!tab.mainBreakerInfo.model) {
    results.push({
      check: 'MAIN_BREAKER_REQUIRED',
      status: 'error',
      message: '메인차단기를 선택해주세요.',
    });
  }

  return results;
}
```

---

## 9. 구현 계획 (상세)

### Phase 1: 프로젝트 셋업 (1일)
```bash
# 1. Next.js 프로젝트 생성
npx create-next-app@latest frontend --typescript --tailwind --app

# 2. 의존성 설치
npm install zustand @tanstack/react-query lucide-react

# 3. OpenAPI 타입 생성
npm install -D openapi-typescript
npx openapi-typescript api/openapi.yaml -o lib/types/api.generated.ts

# 4. Tailwind 설정 (design system 반영)
# tailwind.config.ts 수정
```

### Phase 2: 디자인 시스템 (1일)
- [ ] CSS Variables 설정 (globals.css)
- [ ] 기본 컴포넌트 (Button, Input, Select, Card)
- [ ] Typography 설정
- [ ] 아이콘 셋업 (Lucide Icons)

### Phase 3: 레이아웃 (1일)
- [ ] MainLayout 컴포넌트
- [ ] Sidebar (collapsible, 280px ↔ 80px)
- [ ] Header
- [ ] 반응형 처리

### Phase 4: Hero & Chat (1일)
- [ ] HeroSection 컴포넌트
- [ ] ChatInput (AI 입력창)
- [ ] AI Chat API 연동
- [ ] 인텐트 표시

### Phase 5: Quote Tabs System (2일)
- [ ] QuoteTabs 컴포넌트 (탭 관리)
- [ ] Tab State (Zustand)
- [ ] 탭 추가/삭제/전환
- [ ] 탭 내용 저장

### Phase 6: Form Components (2일)
- [ ] CustomerForm
- [ ] EnclosureForm (드롭다운 + API 연동)
- [ ] BreakerForm (카탈로그 검색)
- [ ] AccessoryForm (동반자재 자동 추가)

### Phase 7: Catalog Integration (1일)
- [ ] Catalog API 연동
- [ ] 검색/필터 기능
- [ ] 드롭다운 자동완성
- [ ] 가격 표시

### Phase 8: Estimate Preview (1일)
- [ ] EstimatePreview 패널
- [ ] 실시간 검증 표시
- [ ] 합계 계산 (부가세 포함/별도)
- [ ] PDF 다운로드 버튼

### Phase 9: Quote Management (1일)
- [ ] Quote List 페이지
- [ ] Quote Detail 페이지
- [ ] 저장/수정/삭제
- [ ] 승인 워크플로우

### Phase 10: 테스트 & 배포 (1일)
- [ ] E2E 테스트 (Playwright)
- [ ] API 통합 테스트
- [ ] 빌드 최적화
- [ ] 배포 설정

---

## 10. 품질 게이트

### 10.1 프론트엔드 품질 기준
| 항목 | 기준 | 검증 방법 |
|------|------|----------|
| TypeScript | 100% 타입 커버리지 | `tsc --noEmit` |
| Lint | 0 errors | `eslint .` |
| Build | Success | `npm run build` |
| E2E Tests | All pass | `npx playwright test` |
| API Integration | All endpoints | 실제 백엔드 연동 |
| Mobile Responsive | 768px+ | 브라우저 테스트 |

### 10.2 API 연동 검증
```typescript
// tests/api-integration.spec.ts
test('Health check', async () => {
  const health = await healthApi.check();
  expect(health.status).toBe('healthy');
});

test('Create estimate', async () => {
  const response = await estimatesApi.create(mockEstimateRequest);
  expect(response.status).toBe('success');
  expect(response.validation_checks.every(c => c.status === 'pass')).toBe(true);
});

test('Quote lifecycle', async () => {
  const quote = await quotesApi.create(mockQuoteRequest);
  expect(quote.id).toBeDefined();

  const approved = await quotesApi.approve(quote.id);
  expect(approved.status).toBe('approved');

  const pdf = await quotesApi.generatePdf(quote.id);
  expect(pdf.url).toBeDefined();
});
```

---

## 11. 참조 파일

### 11.1 원본 디자인 (수정 금지)
- `origin/WORKSPACE:절대코어파일/frontend-kis-complete.html`
- 용도: 디자인, UI, 기능, 레이아웃 참조만

### 11.2 백엔드 API
- `api/openapi.yaml` - OpenAPI 3.1 스키마
- `src/kis_estimator_core/api/routes/` - 라우트 구현
- `src/kis_estimator_core/api/schemas/` - Pydantic 스키마

### 11.3 SSOT 규칙
- `src/kis_estimator_core/core/ssot/` - 상수, 검증 규칙

---

## 12. Evidence 체크리스트

구현 완료 시 제출할 증거:

- [ ] `out/evidence/frontend/setup.json` - 프로젝트 셋업 완료
- [ ] `out/evidence/frontend/components.json` - 컴포넌트 구현 완료
- [ ] `out/evidence/frontend/api-integration.json` - API 연동 완료
- [ ] `out/evidence/frontend/e2e-tests.json` - E2E 테스트 결과
- [ ] `out/evidence/frontend/build.json` - 빌드 결과
- [ ] Screenshot: 전체 화면 캡처

---

**계획서 버전**: v1.0.0
**작성 완료**: 2025-11-30
**다음 단계**: Phase 1 - 프로젝트 셋업 실행

---
*Contract-First + Evidence-Gated 원칙에 따라 작성됨*
*참조 디자인을 기반으로 백엔드 API와 100% 호환 설계*
