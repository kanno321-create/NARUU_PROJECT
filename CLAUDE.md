# NARUU AI Tourism Platform

일본인 대상 대구 의료/미용/관광 알선 AI 플랫폼.
AI 코어 오케스트레이터 + 모듈식 플러그인 아키텍처.

## Architecture

```
[AI Core Orchestrator] ← 중앙 두뇌 (Claude API)
    ├── Plugin Manager  ← 모듈 붙이기/떼기
    ├── Event Bus       ← 모듈 간 이벤트 전달
    └── Plugins/        ← 모듈 디렉토리
        ├── echo/       ← 시스템 검증용
        ├── (content/)  ← 콘텐츠 자동화 (Phase 2)
        ├── (crm/)      ← 고객 CRM (Phase 3)
        └── (sns/)      ← SNS 관리 (Phase 5)
```

## Tech Stack

- Backend: Python 3.12 / FastAPI / Pydantic v2
- Frontend: Next.js (Phase 4)
- Deploy: Railway (backend) / Vercel (frontend)

## MUST

- M1: 목업/가짜 테스트 금지
- M2: 불완전한 구현 금지
- M3: 플러그인은 반드시 NaruuPlugin 인터페이스 구현
- M4: 수정 후 pytest + mypy + ruff 검증 필수

## Plugin Development

새 플러그인 추가:
1. `naruu_core/plugins/{name}/` 디렉토리 생성
2. `plugin.py`에 `Plugin` 클래스 정의 (NaruuPlugin 상속)
3. 서버 재시작 시 자동 디스커버리
