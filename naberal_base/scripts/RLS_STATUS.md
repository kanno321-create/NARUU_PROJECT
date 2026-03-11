# RLS 적용 현황 (2025-10-01)

## ✅ RLS 활성화 완료 (8/11 테이블)

| 테이블 | RLS 상태 | 비고 |
|--------|----------|------|
| estimator.quotes | ✅ ENABLED | |
| estimator.quote_items | ✅ ENABLED | |
| estimator.panels | ✅ ENABLED | |
| estimator.breakers | ✅ ENABLED | |
| estimator.documents | ✅ ENABLED | |
| estimator.evidence_blobs | ✅ ENABLED | |
| estimator.catalog_items | ✅ ENABLED | |
| estimator.customers | ✅ ENABLED | |

## ⚠️ RLS 미적용 (3개 - 의도적)

| 이름 | 타입 | RLS 상태 | 이유 |
|------|------|----------|------|
| estimator.quote_summary | VIEW | ❌ UNRESTRICTED | PostgreSQL VIEW는 RLS 직접 적용 불가 |
| estimator.phase_balance | VIEW | ❌ UNRESTRICTED | PostgreSQL VIEW는 RLS 직접 적용 불가 |
| shared.audit_logs | TABLE | ❌ UNRESTRICTED | 감사 로그는 모든 역할이 조회 가능해야 함 |

## 보안 평가

### 위험도: **낮음**

**근거**:
- 단일 테넌트 시스템 (Multi-tenant 아님)
- 내부 사용자만 접근
- VIEW 데이터는 기본 테이블에서 파생 (기본 테이블은 RLS 적용됨)

### 향후 조치 필요 시점

**Multi-tenant SaaS 전환 시** 다음 작업 필요:
1. VIEW → MATERIALIZED VIEW 변환
2. SECURITY DEFINER 함수로 접근 제어
3. RLS 정책 적용

## 스크립트 파일

변환 스크립트 준비 완료:
- `scripts/enable_rls_phase_quote.sql` (2가지 옵션)
- `scripts/apply_option1_materialized.sql` (MATERIALIZED VIEW)

## 결정 이력

- **2025-10-01**: VIEW unrestricted 상태 유지 결정 (CEO 승인)
- **이유**: 현재 환경에서는 보안 위험 낮음, 지식파일 통합 우선순위 높음
