# KIS Estimator Deployment Guide

Production 배포 가이드 (v2.0.0)

## 1. 환경 요구사항

### 1.1 시스템 요구사항

| 구성요소 | 최소 사양 | 권장 사양 |
|----------|-----------|-----------|
| CPU | 2 cores | 4 cores |
| Memory | 4GB | 8GB |
| Storage | 20GB SSD | 50GB SSD |
| OS | Ubuntu 22.04+ / Windows Server 2019+ | Ubuntu 22.04 LTS |

### 1.2 필수 소프트웨어

- **Python**: 3.11+
- **PostgreSQL**: 15+ (Supabase 권장)
- **Redis**: 7+ (선택적, 캐싱/Rate Limiting용)
- **Docker**: 24+ (컨테이너 배포 시)
- **Node.js**: 20+ (프론트엔드 빌드용)

## 2. 환경 변수 설정

### 2.1 필수 환경 변수

```bash
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:[password]@[host]:5432/postgres

# Alembic (psycopg2 DSN for migrations)
ALEMBIC_DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres

# JWT/Authentication
JWT_SECRET=your-32-character-secret-key
JWKS_URL=https://your-auth-provider/.well-known/jwks.json

# API Configuration
APP_DEBUG=false
CORS_ORIGINS=https://your-domain.com
```

### 2.2 선택적 환경 변수

```bash
# Redis (캐싱)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=900

# S3 (PDF 저장소)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET=kis-estimator-pdfs
S3_REGION=ap-northeast-2

# OpenTelemetry (모니터링)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=kis-estimator-api
```

## 3. 데이터베이스 설정

### 3.1 Supabase 프로젝트 생성

1. [Supabase](https://supabase.com) 접속
2. 새 프로젝트 생성
3. Connection String 복사 (Settings → Database)

### 3.2 스키마 마이그레이션

```bash
# 환경 변수 설정
export ALEMBIC_DATABASE_URL="postgresql://postgres:password@host:5432/postgres"

# 마이그레이션 실행
alembic upgrade head
```

### 3.3 필수 스키마 확인

```sql
-- 필수 스키마
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('kis_beta', 'shared');

-- 필수 테이블
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'kis_beta';
```

예상 테이블:
- `quotes`
- `quote_approval_audit`
- `estimates`
- `catalog_items`

## 4. 로컬 개발 환경

### 4.1 가상환경 설정

```bash
# Python 가상환경
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 4.2 개발 서버 실행

```bash
# PYTHONPATH 설정
export PYTHONPATH=.:src

# 개발 서버 실행
uvicorn kis_estimator_core.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.3 Health Check 확인

```bash
curl http://localhost:8000/v1/health/live
# Expected: {"status":"ok","service":"kis-estimator-api",...}

curl http://localhost:8000/v1/health/ready
# Expected: {"status":"ok","database":"connected",...}
```

## 5. Docker 배포

### 5.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY src/ ./src/
COPY spec_kit/ ./spec_kit/

# 환경 변수
ENV PYTHONPATH=/app/src

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health/live || exit 1

# 서버 실행
EXPOSE 8000
CMD ["uvicorn", "kis_estimator_core.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - APP_DEBUG=false
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### 5.3 빌드 및 실행

```bash
# 이미지 빌드
docker build -t kis-estimator:latest .

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

## 6. Production 체크리스트

### 6.1 보안 설정

- [ ] `APP_DEBUG=false` 설정
- [ ] JWT_SECRET 32자 이상 랜덤 문자열
- [ ] CORS_ORIGINS 허용 도메인만 지정
- [ ] Database SSL 연결 활성화
- [ ] API Rate Limiting 설정

### 6.2 성능 설정

- [ ] Redis 캐싱 활성화
- [ ] Database Connection Pool 설정 (min=5, max=20)
- [ ] Gunicorn workers 설정 (CPU cores × 2 + 1)

### 6.3 모니터링 설정

- [ ] Health endpoint 모니터링 설정
- [ ] OpenTelemetry 트레이싱 활성화
- [ ] 에러 알림 설정 (Slack/Email)

## 7. CI/CD 파이프라인

### 7.1 GitHub Actions (CI)

CI 파이프라인은 `.github/workflows/kis-ci.yml`에 정의되어 있습니다.

Gate 순서:
1. **Gate 1**: Lint & Type Check
2. **Gate 2**: SSOT-Hash Gate
3. **Gate 3**: OpenAPI Diff=0
4. **Gate 3.5**: Endpoint Probe
5. **Gate 4**: Tests (Unit + Integration)
6. **Gate 5**: Evidence Pack Generation

### 7.2 CD 파이프라인

```yaml
# .github/workflows/cd.yml (예시)
name: Deploy

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push Docker image
        run: |
          docker build -t gcr.io/$PROJECT_ID/kis-estimator:${{ github.ref_name }} .
          docker push gcr.io/$PROJECT_ID/kis-estimator:${{ github.ref_name }}
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy kis-estimator \
            --image gcr.io/$PROJECT_ID/kis-estimator:${{ github.ref_name }} \
            --region asia-northeast3
```

## 8. 롤백 절차

### 8.1 빠른 롤백

```bash
# 이전 버전으로 롤백
git checkout v1.9.0
docker build -t kis-estimator:rollback .
docker-compose up -d

# 또는 이미지 태그로 롤백
docker pull gcr.io/project/kis-estimator:v1.9.0
docker-compose up -d
```

### 8.2 데이터베이스 롤백

```bash
# 마이그레이션 롤백 (1단계)
alembic downgrade -1

# 특정 버전으로 롤백
alembic downgrade <revision_id>
```

## 9. 문제 해결

### 9.1 일반적인 문제

**Database Connection Error**
```
asyncpg.exceptions.InvalidPasswordError
```
해결: DATABASE_URL의 비밀번호 확인, 특수문자 URL 인코딩

**Module Import Error**
```
ModuleNotFoundError: No module named 'kis_estimator_core'
```
해결: `PYTHONPATH=.:src` 환경 변수 설정

**Health Check Failing**
```
curl: (7) Failed to connect to localhost port 8000
```
해결: 서버 실행 상태 확인, 포트 바인딩 확인

### 9.2 로그 확인

```bash
# Docker 로그
docker-compose logs -f api | grep ERROR

# 애플리케이션 로그
tail -f /var/log/kis-estimator/app.log
```

## 10. 연락처

- **기술 지원**: support@naberal.com
- **긴급 상황**: ops@naberal.com
- **GitHub Issues**: https://github.com/naberal/kis-estimator/issues

---

*문서 버전: v2.0.0 / 최종 수정: 2025-11-29*
