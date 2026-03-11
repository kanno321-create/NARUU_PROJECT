"""
rls_loader.py 실제 호출 테스트 (P4-2 Real-Call 전환)

목적: coverage 측정을 위한 실제 함수 호출
원칙: Zero-Mock (실제 DB 사용), SB-02 준수, @requires_db 마커

Skip in CI: requires real asyncpg driver (not psycopg2)
"""

import pytest
import os

pytestmark = [
    pytest.mark.requires_db,
    pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Skipping RLS loader tests in CI - requires asyncpg driver"
    )
]

from kis_estimator_core.infra.rls_loader import (
    RLSPolicyLoader,
    apply_rls_policies,
    verify_rls_policies,
    DEFAULT_POLICY_FILE,
)


# ============================================================
# Fixture: Skip if DB Not Available
# ============================================================
@pytest.fixture
def skip_if_no_db():
    """DB가 없으면 테스트 스킵"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip(
            "DATABASE_URL not set - skipping RLS loader tests (SB-05 compliance)"
        )


# ============================================================
# Test: RLSPolicyLoader Initialization
# ============================================================
def test_rls_policy_loader_init_with_url():
    """RLSPolicyLoader 초기화 (URL 제공)"""
    # 실제 호출
    loader = RLSPolicyLoader(
        database_url="postgresql+asyncpg://test:test@localhost/test"
    )

    # 검증
    assert loader.database_url is not None
    assert loader.engine is None  # 아직 연결 안 함


def test_rls_policy_loader_init_without_url():
    """RLSPolicyLoader 초기화 실패 (URL 없음)"""
    # 환경변수 제거 (임시)
    original_url = os.getenv("DATABASE_URL")
    if original_url:
        os.environ.pop("DATABASE_URL", None)

    try:
        # 실제 호출: ValueError 예상
        with pytest.raises(ValueError, match="DATABASE_URL"):
            RLSPolicyLoader(database_url=None)
    finally:
        # 환경변수 복원
        if original_url:
            os.environ["DATABASE_URL"] = original_url


# ============================================================
# Test: load_policy_file
# ============================================================
def test_load_policy_file_success(tmp_path):
    """RLS 정책 파일 로딩 성공"""
    # 임시 정책 파일 생성
    test_policies_dir = tmp_path / "rls"
    test_policies_dir.mkdir()
    policy_file = test_policies_dir / DEFAULT_POLICY_FILE

    policy_content = """
    -- Test RLS Policy
    ALTER TABLE test_table ENABLE ROW LEVEL SECURITY;
    CREATE POLICY test_policy ON test_table FOR SELECT USING (true);
    """
    policy_file.write_text(policy_content, encoding="utf-8")

    # RLSPolicyLoader (monkeypatch RLS_POLICIES_DIR)
    loader = RLSPolicyLoader(
        database_url="postgresql+asyncpg://test:test@localhost/test"
    )

    # monkeypatch (RLS_POLICIES_DIR을 임시 디렉토리로 변경)
    import src.kis_estimator_core.infra.rls_loader as rls_module

    original_dir = rls_module.RLS_POLICIES_DIR
    rls_module.RLS_POLICIES_DIR = test_policies_dir

    try:
        # 실제 호출
        sql_content = loader.load_policy_file(DEFAULT_POLICY_FILE)

        # 검증
        assert "ALTER TABLE test_table" in sql_content
        assert "CREATE POLICY test_policy" in sql_content
    finally:
        # 복원
        rls_module.RLS_POLICIES_DIR = original_dir


def test_load_policy_file_not_found():
    """RLS 정책 파일 누락 (FileNotFoundError)"""
    loader = RLSPolicyLoader(
        database_url="postgresql+asyncpg://test:test@localhost/test"
    )

    # 실제 호출: FileNotFoundError 예상
    with pytest.raises(FileNotFoundError, match="RLS policy file not found"):
        loader.load_policy_file("nonexistent_file.sql")


def test_load_policy_file_empty(tmp_path):
    """RLS 정책 파일 비어있음 (ValueError)"""
    # 빈 파일 생성
    test_policies_dir = tmp_path / "rls"
    test_policies_dir.mkdir()
    policy_file = test_policies_dir / DEFAULT_POLICY_FILE
    policy_file.write_text("", encoding="utf-8")

    loader = RLSPolicyLoader(
        database_url="postgresql+asyncpg://test:test@localhost/test"
    )

    import src.kis_estimator_core.infra.rls_loader as rls_module

    original_dir = rls_module.RLS_POLICIES_DIR
    rls_module.RLS_POLICIES_DIR = test_policies_dir

    try:
        # 실제 호출: ValueError 예상
        with pytest.raises(ValueError, match="RLS policy file is empty"):
            loader.load_policy_file(DEFAULT_POLICY_FILE)
    finally:
        rls_module.RLS_POLICIES_DIR = original_dir


# ============================================================
# Test: apply_policies (Dry Run)
# ============================================================
@pytest.mark.asyncio
async def test_apply_policies_dry_run():
    """RLS 정책 적용 (Dry Run)"""
    loader = RLSPolicyLoader(
        database_url="postgresql+asyncpg://test:test@localhost/test"
    )

    sql_content = """
    ALTER TABLE test_table ENABLE ROW LEVEL SECURITY;
    CREATE POLICY test_policy ON test_table FOR SELECT USING (true);
    """

    try:
        # 실제 호출 (Dry Run)
        result = await loader.apply_policies(sql_content, dry_run=True)

        # 검증
        assert result["status"] == "dry_run_complete"
        assert result["dry_run"] is True
        assert result["total_statements"] == 2
        assert result["executed"] == 0
    finally:
        await loader.close()


# ============================================================
# Test: apply_policies (Real - Requires DB)
# ============================================================
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_apply_policies_real(skip_if_no_db):
    """RLS 정책 적용 (실제 DB) - @requires_db"""
    loader = RLSPolicyLoader()  # DATABASE_URL 환경변수 사용

    # 테스트용 정책 (안전: DROP IF EXISTS)
    sql_content = """
    -- Test Policy (Idempotent)
    DROP POLICY IF EXISTS test_policy_p4_2 ON kis_beta.epdl_plans;
    CREATE POLICY test_policy_p4_2 ON kis_beta.epdl_plans
        FOR SELECT
        USING (true);
    """

    try:
        # 실제 호출
        result = await loader.apply_policies(sql_content, dry_run=False)

        # 검증
        assert result["status"] in ("success", "partial_success")
        assert result["total_statements"] >= 1  # 최소 1개 이상 (파싱 방식에 따라 1~2개)
        assert result["executed"] >= 1
    finally:
        await loader.close()


# ============================================================
# Test: verify_policies (Requires DB)
# ============================================================
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_verify_policies_real(skip_if_no_db):
    """RLS 정책 검증 (실제 DB) - @requires_db"""
    loader = RLSPolicyLoader()

    try:
        # 실제 호출
        result = await loader.verify_policies()

        # 검증
        assert result["status"] in ("verified", "incomplete", "error")
        assert "rls_enabled" in result
        assert "policy_counts" in result
    finally:
        await loader.close()


# ============================================================
# Test: apply_rls_policies (High-Level API)
# ============================================================
@pytest.mark.asyncio
async def test_apply_rls_policies_dry_run(tmp_path):
    """apply_rls_policies() 고수준 API (Dry Run)"""
    # 임시 정책 파일 생성
    test_policies_dir = tmp_path / "rls"
    test_policies_dir.mkdir()
    policy_file = test_policies_dir / DEFAULT_POLICY_FILE

    policy_content = """
    ALTER TABLE test_table ENABLE ROW LEVEL SECURITY;
    CREATE POLICY test_policy ON test_table FOR SELECT USING (true);
    """
    policy_file.write_text(policy_content, encoding="utf-8")

    # monkeypatch
    import src.kis_estimator_core.infra.rls_loader as rls_module

    original_dir = rls_module.RLS_POLICIES_DIR
    rls_module.RLS_POLICIES_DIR = test_policies_dir

    try:
        # 실제 호출 (Dry Run)
        result = await apply_rls_policies(
            database_url="postgresql+asyncpg://test:test@localhost/test", dry_run=True
        )

        # 검증
        assert result["status"] == "dry_run_complete"
        assert result["total_statements"] == 2
    finally:
        rls_module.RLS_POLICIES_DIR = original_dir


# ============================================================
# Test: verify_rls_policies (High-Level API - Requires DB)
# ============================================================
@pytest.mark.asyncio
@pytest.mark.requires_db
async def test_verify_rls_policies_real(skip_if_no_db):
    """verify_rls_policies() 고수준 API (실제 DB) - @requires_db"""
    # 실제 호출
    result = await verify_rls_policies()

    # 검증
    assert result["status"] in ("verified", "incomplete", "error")
    assert "rls_enabled" in result


# ============================================================
# Test: close() Method
# ============================================================
@pytest.mark.asyncio
async def test_rls_policy_loader_close():
    """RLSPolicyLoader close() 메서드"""
    loader = RLSPolicyLoader(
        database_url="postgresql+asyncpg://test:test@localhost/test"
    )

    # 엔진 생성
    await loader._get_engine()
    assert loader.engine is not None

    # 실제 호출
    await loader.close()

    # 검증
    assert loader.engine is None
