# 시스템 미구현 기능 분석 보고서

**작성일**: 2025-12-07
**작성자**: 나베랄 감마
**목적**: 대표님 요구사항 기준 미구현 기능 전수 조사

---

## 🎯 대표님 요구사항 요약

### 1. 데이터 저장 기능
- ✅ **매출전표**: 구현 완료 (POST /erp/sales)
- ❌ **견적서 저장**: 미구현
- ❌ **매입전표**: 미구현
- ❌ **수금전표**: 미구현
- ❌ **지급전표**: 미구현
- ❌ **재고 이월**: 미구현
- ❌ **기타 ERP 메뉴**: 대부분 미구현

### 2. AI 매니저 시스템
- ❌ **AI 매니저 탭**: 미구현
- ❌ **자연어 쿼리 처리**: 미구현
- ❌ **데이터 분석 및 그래프 생성**: 미구현
- ❌ **A4 2장 분량 보고서 작성**: 미구현
- ❌ **모든 메뉴 접근/통제/수정 권한**: 미구현

### 3. 데이터베이스 통합
- ⚠️ **현재 상태**: JSON 파일 기반 (`data/erp/*.json`)
- ❌ **PostgreSQL 통합**: 미구현 (Supabase 연결 필요)
- ❌ **트랜잭션 관리**: 부분 구현 (롤백 로직만 존재)

---

## 📋 카테고리별 미구현 기능 상세

### A. 견적 시스템 (Estimator)

#### 구현 완료
- ✅ 견적 생성 API (POST /v1/estimates)
- ✅ FIX-4 파이프라인 (외함 계산 → 브레이커 배치 → 문서 생성)
- ✅ PDF/Excel 문서 자동 생성

#### 미구현
- ❌ **견적서 저장 버튼**: 프론트엔드 UI에 저장 기능 없음
- ❌ **저장된 견적 목록 조회**: GET /v1/estimates 호출 UI 없음
- ❌ **견적서 수정 기능**: PATCH /v1/estimates/{id} 미구현
- ❌ **견적서 삭제 기능**: DELETE /v1/estimates/{id} 미구현
- ❌ **견적서 → 매출전표 변환**: 견적 확정 시 자동 매출 생성 없음

**예상 파일**:
- `frontend/src/app/quote/page.tsx` - 견적 입력 화면 (저장 버튼 없음)
- `frontend/src/components/QuoteHistory.tsx` - 견적 이력 화면 (미존재)

---

### B. ERP 시스템 (전표 입력)

#### 구현 완료
- ✅ 매출전표 (POST /erp/sales)
- ✅ 거래처 조회 (GET /erp/customers)
- ✅ 상품 조회 (GET /erp/products)

#### 미구현 (총 15개 윈도우 중 12개 미구현)

**1. 전표 입력 (5개 중 4개 미구현)**
- ✅ 매출전표 (SalesVoucherWindow.tsx) - 구현 완료
- ❌ 매입전표 (PurchaseVoucherWindow.tsx) - UI만 존재, 저장 로직 없음
- ❌ 수금전표 (CollectionVoucherWindow.tsx) - UI만 존재, 저장 로직 없음
- ❌ 지급전표 (PaymentDisbursementWindow.tsx) - UI만 존재, 저장 로직 없음
- ❌ 입출금전표 (IncomeExpenseSlipWindow.tsx) - 미존재

**2. 기초자료 (7개 모두 미구현)**
- ❌ 거래처 등록 (CustomerWindow.tsx) - 조회만 가능, CRUD 없음
- ❌ 상품 등록 (ProductWindow.tsx) - 조회만 가능, CRUD 없음
- ❌ 사원 등록 (EmployeeWindow.tsx) - 미존재
- ❌ 은행계좌 등록 (BankAccountWindow.tsx) - 미존재
- ❌ 신용카드 등록 (CreditCardWindow.tsx) - 미존재
- ❌ 입출금항목 등록 (IncomeExpenseItemWindow.tsx) - 미존재
- ❌ 환경설정 (SettingsWindow.tsx) - UI만 존재, 저장 로직 없음

**3. 이월 (6개 모두 미구현)**
- ❌ 상품재고이월 (ProductInventoryCarryoverWindow.tsx) - 미존재
- ❌ 은행잔고이월 (BankBalanceCarryoverWindow.tsx) - 미존재
- ❌ 현금잔고이월 (CashBalanceCarryoverWindow.tsx) - 미존재
- ❌ 어음이월 (BillCarryoverWindow.tsx) - 미존재
- ❌ 미수미지급이월 (ReceivablePayableCarryoverWindow.tsx) - 미존재
- ❌ 채권채무이월 (DebtCreditCarryoverWindow.tsx) - 미존재

**4. 기타 메뉴 (7개 모두 미구현)**
- ❌ 견적서 발행 (QuotationWindow.tsx) - 미존재
- ❌ 발주서 발행 (PurchaseOrderWindow.tsx) - 미존재
- ❌ 거래명세서 관리 (TransactionStatementWindow.tsx) - 미존재
- ❌ 급여대장 (PayrollWindow.tsx) - 미존재
- ❌ 사업장일일거래 (BusinessDailyTransactionWindow.tsx) - 미존재
- ❌ 팩스전송 (FaxWindow.tsx) - 미존재
- ❌ 문자발송 (SmsWindow.tsx) - 미존재

**백엔드 API 누락**:
```
POST /erp/purchases (매입전표)
POST /erp/collections (수금전표)
POST /erp/payments (지급전표)
POST /erp/income-expense (입출금전표)

POST /erp/customers (거래처 생성)
PATCH /erp/customers/{id} (거래처 수정)
DELETE /erp/customers/{id} (거래처 삭제)

POST /erp/products (상품 생성)
PATCH /erp/products/{id} (상품 수정)
DELETE /erp/products/{id} (상품 삭제)

POST /erp/employees (사원 등록)
POST /erp/bank-accounts (은행계좌 등록)
POST /erp/credit-cards (신용카드 등록)

POST /erp/carryover/inventory (재고 이월)
POST /erp/carryover/bank-balance (은행잔고 이월)
POST /erp/carryover/cash-balance (현금잔고 이월)
... (총 30+ API 누락)
```

---

### C. 데이터베이스 통합

#### 현재 상태
```
📂 data/erp/
├── customers.json (거래처 데이터)
├── products.json (상품 데이터)
└── sales.json (매출전표 데이터)
```

#### 문제점
- ❌ **PostgreSQL 미사용**: Supabase 연결 설정은 있으나 실제 사용 안 함
- ❌ **JSON 파일 동시 쓰기 위험**: 다중 사용자 환경에서 데이터 손실 가능
- ❌ **트랜잭션 없음**: ACID 보장 불가
- ❌ **백업/복구 시스템 없음**: 데이터 손실 시 복구 불가

#### 필요 작업
1. **Supabase PostgreSQL 스키마 설계**
   - `erp.customers` 테이블
   - `erp.products` 테이블
   - `erp.sales` 테이블
   - `erp.purchases` 테이블
   - `erp.collections` 테이블
   - `erp.payments` 테이블
   - `erp.inventory_carryover` 테이블
   - ... (총 20+ 테이블)

2. **마이그레이션 스크립트**
   - JSON → PostgreSQL 데이터 이전

3. **백엔드 수정**
   - JSON 파일 읽기/쓰기 → PostgreSQL 쿼리로 변경

---

### D. AI 매니저 시스템 (완전 미구현)

#### 요구사항
1. **자연어 쿼리 처리**
   - "한국산업에 7월에 판매한 금액 알려줘"
   - "1분기 2분기 매출 비교해줘"
   - "재고가 부족한 상품 알려줘"

2. **데이터 분석 및 시각화**
   - 매출 그래프 생성 (Chart.js, Recharts)
   - 분기별 매출 비교 차트
   - 고객별 매출 분석
   - 상품별 판매량 분석

3. **보고서 자동 작성**
   - A4 2장 분량 PDF 생성
   - 텍스트 설명 + 그래프 포함
   - 인사이트 및 권장사항

4. **모든 메뉴 통제/수정 권한**
   - 모든 ERP 데이터 CRUD 권한
   - 견적서 생성/수정/삭제
   - 시스템 설정 변경
   - 사용자 권한 관리

#### 필요 기술 스택
- **LLM 통합**: Claude API 또는 OpenAI GPT-4
- **자연어 → SQL 변환**: Text-to-SQL 엔진
- **차트 라이브러리**: Recharts, Chart.js
- **PDF 생성**: jsPDF, Puppeteer
- **RAG 시스템**: 벡터 DB (Pinecone, Weaviate) + 임베딩
- **권한 시스템**: Role-Based Access Control (RBAC)

#### 필요 API
```
POST /ai-manager/query
  - 자연어 쿼리 수신
  - SQL 변환
  - 데이터 조회
  - 분석 결과 반환

POST /ai-manager/report
  - 보고서 주제 수신
  - 데이터 수집 및 분석
  - 그래프 생성
  - PDF 보고서 생성
  - 다운로드 URL 반환

GET /ai-manager/insights
  - 자동 인사이트 생성
  - 이상 패턴 탐지
  - 권장사항 제공
```

#### 필요 UI 컴포넌트
```
frontend/src/components/ai-manager/
├── AIManagerWindow.tsx (메인 AI 매니저 윈도우)
├── NaturalLanguageQuery.tsx (자연어 입력창)
├── AnalysisResults.tsx (분석 결과 표시)
├── ChartViewer.tsx (차트 렌더링)
├── ReportGenerator.tsx (보고서 생성 UI)
└── DataAccessControl.tsx (데이터 접근 권한 UI)
```

---

## 🚨 우선순위 분석

### 즉시 필요 (Priority 1 - 1주 이내)
1. ✅ **매출전표 저장** - 완료
2. ❌ **매입전표 저장** - 미구현
3. ❌ **수금/지급전표 저장** - 미구현
4. ❌ **거래처/상품 CRUD** - 미구현
5. ❌ **PostgreSQL 마이그레이션** - 미구현

### 중요 (Priority 2 - 2주 이내)
1. ❌ **재고 이월 기능** - 미구현
2. ❌ **견적서 → 매출전표 변환** - 미구현
3. ❌ **AI 매니저 기본 기능** (자연어 쿼리) - 미구현

### 향후 (Priority 3 - 1개월 이내)
1. ❌ **AI 보고서 자동 생성** - 미구현
2. ❌ **팩스/문자 발송** - 미구현
3. ❌ **급여대장** - 미구현

---

## 📊 구현 완성도

| 카테고리 | 구현률 | 상태 |
|---------|-------|-----|
| 견적 시스템 | 60% | 🟡 생성/조회 가능, 저장 UI 없음 |
| ERP - 매출전표 | 100% | 🟢 완료 |
| ERP - 매입전표 | 10% | 🔴 UI만 존재 |
| ERP - 수금/지급전표 | 10% | 🔴 UI만 존재 |
| ERP - 기초자료 | 30% | 🔴 조회만 가능 |
| ERP - 이월 | 0% | 🔴 미구현 |
| 데이터베이스 | 0% | 🔴 JSON 파일만 사용 |
| AI 매니저 | 0% | 🔴 완전 미구현 |
| **전체 평균** | **26%** | 🔴 매우 부족 |

---

## 💰 예상 개발 공수

| 기능 | 예상 시간 | 우선순위 |
|------|-----------|---------|
| PostgreSQL 마이그레이션 | 16시간 | P1 |
| 매입/수금/지급전표 | 12시간 | P1 |
| 거래처/상품 CRUD | 8시간 | P1 |
| 재고 이월 | 6시간 | P2 |
| 견적서 저장 UI | 4시간 | P2 |
| AI 매니저 - 자연어 쿼리 | 20시간 | P2 |
| AI 매니저 - 그래프 생성 | 12시간 | P3 |
| AI 매니저 - 보고서 작성 | 16시간 | P3 |
| **총계** | **94시간** | |

---

## 🎯 다음 단계 권장사항

### 단기 (1주 이내)
1. **PostgreSQL 마이그레이션 개발계획서 작성**
2. **매입전표 저장 기능 개발계획서 작성**
3. **거래처/상품 CRUD 개발계획서 작성**

### 중기 (2주 이내)
1. **AI 매니저 시스템 아키텍처 설계**
2. **자연어 쿼리 엔진 개발계획서 작성**

### 장기 (1개월 이내)
1. **AI 보고서 자동 생성 개발계획서 작성**
2. **전체 시스템 통합 테스트 계획**

---

*작성: 나베랄 감마*
*작성일: 2025-12-07*
*상태: 분석 완료*
