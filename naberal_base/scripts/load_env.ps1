# 환경변수 로드 스크립트 (PowerShell)
# 사용법: .\scripts\load_env.ps1 [production|staging|test]

param(
    [string]$EnvFile = ".env.production"
)

if (-not (Test-Path $EnvFile)) {
    Write-Host "❌ 오류: $EnvFile 파일이 없습니다." -ForegroundColor Red
    exit 1
}

Write-Host "📋 환경변수 로드: $EnvFile" -ForegroundColor Cyan

# .env 파일 파싱 및 로드
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()

        # 따옴표 제거
        $value = $value -replace '^["'']|["'']$', ''

        # 환경변수 설정
        [System.Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
    }
}

# 필수 환경변수 검증
$RequiredVars = @(
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_DB_URL"
)

$MissingVars = @()

foreach ($var in $RequiredVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var, [System.EnvironmentVariableTarget]::Process)
    if ([string]::IsNullOrEmpty($value)) {
        $MissingVars += $var
    }
}

if ($MissingVars.Count -gt 0) {
    Write-Host "⚠️  경고: 다음 필수 환경변수가 설정되지 않았습니다:" -ForegroundColor Yellow
    foreach ($var in $MissingVars) {
        Write-Host "  - $var" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "✅ 환경변수 로드 완료" -ForegroundColor Green
Write-Host ""
Write-Host "📊 로드된 환경변수:" -ForegroundColor Cyan

$SUPABASE_URL = [System.Environment]::GetEnvironmentVariable("SUPABASE_URL", [System.EnvironmentVariableTarget]::Process)
$SUPABASE_ANON_KEY = [System.Environment]::GetEnvironmentVariable("SUPABASE_ANON_KEY", [System.EnvironmentVariableTarget]::Process)
$SUPABASE_SERVICE_ROLE_KEY = [System.Environment]::GetEnvironmentVariable("SUPABASE_SERVICE_ROLE_KEY", [System.EnvironmentVariableTarget]::Process)
$SUPABASE_DB_URL = [System.Environment]::GetEnvironmentVariable("SUPABASE_DB_URL", [System.EnvironmentVariableTarget]::Process)

Write-Host "  - SUPABASE_URL: $($SUPABASE_URL.Substring(0, [Math]::Min(30, $SUPABASE_URL.Length)))..."
Write-Host "  - SUPABASE_ANON_KEY: $($SUPABASE_ANON_KEY.Substring(0, [Math]::Min(20, $SUPABASE_ANON_KEY.Length)))..."
Write-Host "  - SUPABASE_SERVICE_ROLE_KEY: $($SUPABASE_SERVICE_ROLE_KEY.Substring(0, [Math]::Min(20, $SUPABASE_SERVICE_ROLE_KEY.Length)))..."
Write-Host "  - SUPABASE_DB_URL: $($SUPABASE_DB_URL.Substring(0, [Math]::Min(30, $SUPABASE_DB_URL.Length)))..."
Write-Host ""
Write-Host "🚀 준비 완료. API 서버를 실행할 수 있습니다." -ForegroundColor Green
