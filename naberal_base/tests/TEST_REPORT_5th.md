# 5차 테스트 결과 보고서 (커밋 8ac2f620)
> 테스트 일시: 2026-02-09 06:21 KST

## 총괄

| 테스트 | 결과 | 비고 |
|--------|------|------|
| issue_verification | **41/46** (89%) | |
| full_button_audit | **76/130** (58%) | 20건 ERP SKIP |
| e2e_backend_api | **32/35** (91%) | Railway 배포 후 +3 |

---

## 1. issue_verification FAIL 5건

### #2 — 대시보드 "진행 중인 프로젝트" 카드
- **증상**: 클릭 후 `/dashboard`에 머묾 (→ `/erp` 이동해야 함)
- **원인**: 테스트 셀렉터 인덱스 ≠ 실제 DOM 순서. full_button_audit StatCard[2]에서는 `/erp` PASS
- **판정**: 테스트 셀렉터 수정 또는 코드에서 카드 순서 확인

### #9 — "사용 가이드" 빠른액션
- **증상**: 메시지 수 10→8 (감소). 정상이면 10→11+
- **간헐적**: 3차 PASS(10→11), 4차·5차 FAIL(10→8)
- **원인**: "사용 가이드" 클릭 시 새 채팅 생성되면서 이전 메시지 초기화 추정
- **판정**: 코드 수정 필요 — 새 채팅 생성 대신 현재 채팅에 메시지 전송해야 함

### #13 — 세션 ID 미전달
- **증상**: 사이드바 최근대화 클릭 → `/ai-manager` 이동 → `localStorage('kis-load-session-id')` = null
- **원인**: useRef 재시도 패턴 적용했다고 보고됐으나 여전히 null
- **판정**: 코드 수정 필요 (P0)

### #21 — 자사정보 주소 검색 버튼
- **증상**: `button:has-text("주소 검색")` 셀렉터 매칭 안 됨
- **실제 코드**: `BasicDataCompanyInfoWindow.tsx` 버튼 텍스트 = `"검색"`
- **판정**: 테스트 셀렉터 `"검색"`으로 변경 또는 버튼 텍스트를 `"주소 검색"`으로 변경

### #46 — 비밀번호 8자 검증
- **증상**: "short" 입력 후 8자 경고 미표시
- **실제 코드**: `settings/page.tsx:310`에서 불일치 검증이 먼저 실행 → 8자 검증(line 314)까지 미도달
- **테스트**: confirm 필드(`pwInputs[2]`) 미입력
- **판정**: 코드에서 8자 검증 순서를 불일치 검증 앞으로 이동, 또는 테스트에서 confirm 입력 추가

---

## 2. full_button_audit FAIL 4건 + SKIP 20건

### FAIL 4건

| 항목 | 원인 |
|------|------|
| /login ID Input | 인증 상태에서 /login 접근 → /dashboard 리다이렉트. 테스트를 비인증 컨텍스트로 변경 필요 |
| /login Password Input | 동일 |
| /login Submit Button | 동일 |
| /ai-manager Send Button | 전송 버튼이 아이콘(SVG)만 있고 텍스트 없음. 셀렉터 수정 필요 |

### SKIP 20건 (ERP 윈도우 전체)

company-info, customer, product, employee, sales-voucher, purchase-voucher, collection-voucher, sales-statement, purchase-statement, stock-status, inventory-adjust, collection-statement, payment-statement, cash-statement, bank-statement, profit-loss, monthly-chart, basic-settings, email-settings, estimate-management

- **원인**: 테스트가 `data-window-id` 영문 어트리뷰트로 메뉴 찾음. 실제 DOM은 한글 텍스트 기반(`"자사정보등록"` 등)
- **참고**: issue_verification #24-#33에서 ERP 환경설정 9/9 PASS → 윈도우 자체는 정상

### 주요 WARN (참고)

| 페이지 | 항목 | 상세 |
|--------|------|------|
| /quote | Excel, PDF, 출력 | 해당 이름 버튼 부재. 실제 "저장/인쇄/이메일/생성"만 존재 |
| /ai-manager | 빠른액션 4개 | 채팅 시작 전에만 표시 — visibility 타이밍 |
| /settings | 테마 탭 | 기본 탭이라 변화 감지 안 됨 |
| /settings | Password Fields | 보안 탭 전환 전 기본 탭에서 탐색 → 0개 |

---

## 3. e2e_backend_api FAIL 3건

### CATALOG brand 필터 — 422
- **요청**: `GET /v1/catalog/breakers?brand=상도`
- **원인**: `brand` 쿼리 파라미터 처리 로직 미구현
- **참고**: 필터 없는 기본 조회는 200 PASS (100 items)

### ERP dashboard — 404
- **요청**: `GET /v1/erp/dashboard`
- **원인**: 엔드포인트 자체 미구현
- **참고**: `/v1/erp/customers`, `/v1/erp/products`, `/v1/erp/sales` 모두 200 PASS

### AI sessions list — 404
- **요청**: `GET /v1/ai-sessions/list`
- **원인**: 실제 경로는 `/v1/ai-manager/sessions` (200 PASS). 테스트 경로 오류
- **판정**: 테스트 수정 필요 — `/v1/ai-sessions/list` → `/v1/ai-manager/sessions`

---

## 수정 우선순위

### 코드 수정 (실제 버그)

| 순위 | 항목 | 파일 |
|------|------|------|
| P0 | #13 Session ID null | dashboard/page.tsx, ai-manager/page.tsx |
| P1 | #9 사용 가이드 새 채팅 초기화 | ai-manager 빠른액션 핸들러 |
| P1 | CATALOG brand 422 | 백엔드 catalog 라우터 |
| P2 | ERP dashboard 404 | 백엔드 erp 라우터 |

### 테스트 스크립트 수정 (코드 정상)

| 항목 | 수정 내용 |
|------|----------|
| #2 카드 인덱스 | StatCard 셀렉터 인덱스 조정 |
| #21 주소 검색 | `"주소 검색"` → `"검색"` |
| #46 비밀번호 | confirm 필드 입력 추가 |
| /login 3건 | 비인증 컨텍스트에서 테스트 |
| AI sessions 경로 | `/v1/ai-sessions/list` → `/v1/ai-manager/sessions` |
| ERP 윈도우 20건 | 영문 ID → 한글 텍스트 셀렉터 |

---

## 진행률 추이

```
           이슈검증    버튼감사    API
초기값:     1/30       -          -
P0-P3후:   42/46      76/130     30/35
5차(현재): 41/46      76/130     32/35
```
