#!/bin/bash
# 환경변수 로드 스크립트
# 사용법: source scripts/load_env.sh [production|staging|test]

ENV_FILE="${1:-.env.production}"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 오류: $ENV_FILE 파일이 없습니다."
    exit 1
fi

echo "📋 환경변수 로드: $ENV_FILE"

# .env 파일에서 환경변수 로드
set -a
source "$ENV_FILE"
set +a

# 필수 환경변수 검증
REQUIRED_VARS=(
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_ROLE_KEY"
    "SUPABASE_DB_URL"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "⚠️  경고: 다음 필수 환경변수가 설정되지 않았습니다:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

echo "✅ 환경변수 로드 완료"
echo ""
echo "📊 로드된 환경변수:"
echo "  - SUPABASE_URL: ${SUPABASE_URL:0:30}..."
echo "  - SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:20}..."
echo "  - SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY:0:20}..."
echo "  - SUPABASE_DB_URL: ${SUPABASE_DB_URL:0:30}..."
echo ""
echo "🚀 준비 완료. API 서버를 실행할 수 있습니다."
