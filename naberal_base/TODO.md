# TODO.md - NABERAL KIS Estimator 남은 작업 목록

**마지막 업데이트**: 2026-02-06 19:00 KST
**기준**: Railway 배포 완료, LINE WORKS OAuth 이메일 발송 확인 후

---

## 긴급 (P0) - 재배포 시 즉시 필요

### OAuth 토큰 영속성 개선 ✅ (2026-02-06 완료)
- [x] `nw_oauth_tokens` 테이블 Supabase에 생성 (migration: 20260206_nw_oauth_tokens.py)
- [x] `email.py`의 토큰 저장/읽기를 파일 → DB로 전환
- [x] `nw_api_config.json` 의존성 제거 (파일은 폴백으로만 사용)
- [ ] **Railway 재배포 후 Migration 실행 필요**: `alembic upgrade head`
- [ ] **Railway 재배포 후 OAuth 재인증**: `/v1/email/oauth/authorize`

### LINE WORKS API 자격증명 환경변수화 ✅ (2026-02-06 완료)
- [x] `email.py`에서 환경변수 우선 읽기 → DB → 파일 폴백 로직 구현
- [ ] Railway 환경변수 등록 필요 (선택적):
  - `NW_CLIENT_ID`, `NW_CLIENT_SECRET`, `NW_SERVICE_ACCOUNT`, `NW_PRIVATE_KEY`
- [ ] `BASE_URL` 환경변수 Railway에 등록 (`https://naberalproject-production.up.railway.app`)

---

## 중요 (P1) - 기능 완성

### CORS/환경변수 검증 (감마 에이전트 미착수)
- [ ] Railway 환경변수 전체 목록 확인 및 누락분 등록
- [ ] 프론트엔드 CORS origin 검증 (localhost:3000, Electron file://, Vercel)
- [ ] Electron 앱에서 Railway API 호출 테스트
- [ ] CSP 헤더가 Railway 도메인 허용하는지 확인
- **참조**: `.claude/plans/concurrent-tinkering-peacock.md` 감마 섹션

### 전체 API 전수 검사 (델타 에이전트 미착수)
- [ ] Health 엔드포인트 전체 프로브
- [ ] Auth: 로그인 → 토큰 → 인증 요청 검증
- [ ] Estimates: 견적 생성 → 검증 → 조회
- [ ] Catalog: 차단기/외함/부속자재 조회
- [ ] AI Chat: 대화 → 응답 → 세션 저장 → 재로드
- [ ] ERP: 고객/제품/매출/매입 CRUD
- [ ] Drawings: 도면 생성/조회
- [ ] Calendar: 일정 CRUD (per-user)
- [ ] Email: 이메일 발송 테스트
- [ ] Prediction: 예측 분석
- [ ] 검증 보고서 `claudedocs/RAILWAY_VERIFICATION_REPORT.md` 작성
- **참조**: `.claude/plans/concurrent-tinkering-peacock.md` 델타 섹션

### AI 대화 연속성 강화
- [ ] 대화 요약 MD 생성 품질 확인
- [ ] 새 대화 시작 시 이전 요약 자동 참조 검증
- [ ] 세션 목록 API에 요약 포함 확인
- [ ] Railway 재시작 후 세션 복원 테스트

---

## 일반 (P2) - 개선사항

### Dockerfile 최적화
- [ ] `__pycache__` 폴더 .dockerignore에 추가
- [ ] 멀티스테이지 빌드 캐시 효율 검증
- [ ] 이미지 사이즈 측정 및 40% 감소 목표 확인

### 프론트엔드 연동
- [ ] Next.js 프론트엔드 → Railway 백엔드 전체 통신 테스트
- [ ] Electron 데스크탑 빌드 → Railway API 연동 확인
- [ ] 이메일 발송 UI 구현 (프론트엔드)
- [ ] 캘린더 UI 연동 확인
- [ ] ERP 대시보드 연동 확인

### 코드 품질
- [ ] `__pycache__` 바이너리 파일 git에서 제거
- [ ] 불필요한 임시 파일 정리 (`test_email.json`, `nw_api_config.json` 등)
- [ ] email.py 코드 리팩토링 (1500줄+ → 모듈 분리 고려)
- [ ] DB migration Alembic 스크립트 정리

---

## 완료된 작업 (참고용)

### 2026-02-06 완료
- [x] LINE WORKS OAuth 이메일 발송 (실제 수신 확인)
- [x] ERP 라우터 JSON → Supabase DB 마이그레이션
- [x] 도면(Drawings) 라우터 JSON → Supabase DB 마이그레이션
- [x] 캘린더 DB 마이그레이션 (per-user)
- [x] AI 대화 연속성 시스템 (대화 요약 MD 저장)
- [x] ERP 원장/리포트 API 엔드포인트
- [x] 견적서 저장 + AI 내보내기 + 이메일 연동

### 이전 세션 완료
- [x] Railway 배포 및 서버 가동
- [x] Supabase PostgreSQL 연결
- [x] 16개 라우터 등록
- [x] JWT 인증 시스템
- [x] FIX-4 파이프라인
- [x] AI 검증 6단계

---

## 참고 문서

| 문서 | 위치 | 내용 |
|------|------|------|
| CLAUDE.md | `./CLAUDE.md` | 백엔드 개발 가이드 (시스템 프롬프트) |
| WORK_HANDOFF.md | `./WORK_HANDOFF.md` | 작업 인수인계 (현재 상태) |
| CLAUDE_KNOWLEDGE.md | `./CLAUDE_KNOWLEDGE.md` | 학습 데이터 분석 지식 |
| 전체 계획 | `.claude/plans/concurrent-tinkering-peacock.md` | 서브에이전트 운용 계획 |

---

*이 문서는 Claude Code가 자동으로 읽어야 합니다.*
