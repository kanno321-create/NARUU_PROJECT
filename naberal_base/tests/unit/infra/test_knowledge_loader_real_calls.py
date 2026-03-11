"""
knowledge_loader.py 실제 호출 테스트 (P4-2 Phase I-4)

목적: 지식 시스템 핵심 모듈 coverage 측정 (0% → 70%)
원칙: Zero-Mock, SSOT 정책 사용, 실제 파일 I/O

일관성 규칙:
- 실제 KnowledgeLoader 인터페이스에 맞춤
- REQUIRED_FILES: 1_breakers.json, 2_enclosures.json, 3_accessories.json, 4_calculations.json, 5_validation.json
- (참조: src/kis_estimator_core/infra/knowledge_loader.py)
"""

import pytest
import json
import hashlib

from kis_estimator_core.infra.knowledge_loader import (
    KnowledgeLoader,
    get_knowledge_loader,
    KnowledgeFileNotFoundError,
    KnowledgeValidationError,
)


# ============================================================
# Fixture: Knowledge Directory Setup
# ============================================================
@pytest.fixture
def temp_knowledge_dir(tmp_path):
    """임시 지식 디렉토리 생성 (실제 REQUIRED_FILES 기준)"""
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()

    # 실제 REQUIRED_FILES 5개 생성 (knowledge_loader.py 기준)
    required_files = [
        "1_breakers.json",
        "2_enclosures.json",
        "3_accessories.json",
        "4_calculations.json",
        "5_validation.json",
    ]

    for filename in required_files:
        file_path = knowledge_dir / filename
        content = {
            "meta": {
                "version": "1.0.0",
                "description": f"Test {filename}",
            },
            "data": {"test_key": "test_value"},
        }
        file_path.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")

    return knowledge_dir


@pytest.fixture
def loader(temp_knowledge_dir):
    """KnowledgeLoader 인스턴스"""
    return KnowledgeLoader(temp_knowledge_dir)


# ============================================================
# Test: KnowledgeLoader Initialization
# ============================================================
def test_knowledge_loader_init_success(temp_knowledge_dir):
    """KnowledgeLoader 초기화 성공"""
    # 실제 호출
    loader = KnowledgeLoader(temp_knowledge_dir)

    # 검증
    assert loader.knowledge_dir == temp_knowledge_dir
    assert isinstance(loader.REQUIRED_FILES, list)
    assert len(loader.REQUIRED_FILES) == 5  # 실제: 5개 파일


def test_knowledge_loader_init_directory_not_found(tmp_path):
    """디렉토리 없음 → KnowledgeFileNotFoundError"""
    nonexistent_dir = tmp_path / "nonexistent"

    # 실제 호출
    with pytest.raises(
        KnowledgeFileNotFoundError, match="Knowledge directory not found"
    ):
        KnowledgeLoader(nonexistent_dir)


def test_knowledge_loader_init_not_directory(tmp_path):
    """파일이 디렉토리가 아님 → KnowledgeFileNotFoundError"""
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("test")

    # 실제 호출
    with pytest.raises(KnowledgeFileNotFoundError, match="not a directory"):
        KnowledgeLoader(file_path)


def test_knowledge_loader_init_missing_required_file(tmp_path):
    """필수 파일 누락 → KnowledgeValidationError"""
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()

    # 1_breakers.json만 생성 (나머지 4개 누락)
    (knowledge_dir / "1_breakers.json").write_text('{"test": "data"}')

    # 실제 호출
    with pytest.raises(
        KnowledgeValidationError, match="Required knowledge files missing"
    ):
        KnowledgeLoader(knowledge_dir)


# ============================================================
# Test: load() Method
# ============================================================
def test_load_success(loader, temp_knowledge_dir):
    """파일 로드 성공"""
    # 실제 호출
    data = loader.load("1_breakers.json")

    # 검증
    assert isinstance(data, dict)
    assert "meta" in data
    assert data["meta"]["version"] == "1.0.0"


def test_load_file_not_found(loader):
    """파일 없음 → KnowledgeFileNotFoundError"""
    # 실제 호출
    with pytest.raises(KnowledgeFileNotFoundError, match="Knowledge file not found"):
        loader.load("nonexistent.json")


def test_load_invalid_json(loader, temp_knowledge_dir):
    """잘못된 JSON → KnowledgeValidationError"""
    # 잘못된 JSON 파일 생성
    invalid_file = temp_knowledge_dir / "invalid.json"
    invalid_file.write_text("{invalid json content")

    # 실제 호출
    with pytest.raises(KnowledgeValidationError, match="Invalid JSON format"):
        loader.load("invalid.json")


def test_load_non_dict_json(loader, temp_knowledge_dir):
    """JSON이 dict가 아님 → KnowledgeValidationError"""
    # 리스트 JSON 생성
    list_file = temp_knowledge_dir / "list.json"
    list_file.write_text("[1, 2, 3]")

    # 실제 호출
    with pytest.raises(
        KnowledgeValidationError, match="Invalid knowledge file structure"
    ):
        loader.load("list.json")


def test_load_caching(loader):
    """캐싱 동작 확인 (functools.lru_cache)"""
    # 실제 호출: 첫 번째 로드
    data1 = loader.load("1_breakers.json")

    # 실제 호출: 두 번째 로드 (캐시 히트)
    data2 = loader.load("1_breakers.json")

    # 검증: 동일 객체 (캐시됨)
    assert data1 is data2


# ============================================================
# Test: Specialized Getters (5 functions - 실제 인터페이스)
# ============================================================
def test_get_breakers_db(loader):
    """get_breakers_db() 호출"""
    data = loader.get_breakers_db()
    assert isinstance(data, dict)
    assert "meta" in data


def test_get_enclosures_db(loader):
    """get_enclosures_db() 호출"""
    data = loader.get_enclosures_db()
    assert isinstance(data, dict)
    assert "meta" in data


def test_get_accessories(loader):
    """get_accessories() 호출"""
    data = loader.get_accessories()
    assert isinstance(data, dict)
    assert "meta" in data


def test_get_calculations(loader):
    """get_calculations() 호출 (실제 인터페이스)"""
    data = loader.get_calculations()
    assert isinstance(data, dict)
    assert "meta" in data


def test_get_validation(loader):
    """get_validation() 호출 (실제 인터페이스)"""
    data = loader.get_validation()
    assert isinstance(data, dict)
    assert "meta" in data


# ============================================================
# Test: load_all() Method
# ============================================================
def test_load_all_success(loader):
    """모든 파일 로드"""
    # 실제 호출
    all_data = loader.load_all()

    # 검증: 5개 파일 (실제 REQUIRED_FILES 기준)
    assert isinstance(all_data, dict)
    assert len(all_data) == 5
    assert "1_breakers" in all_data
    assert "2_enclosures" in all_data
    assert "3_accessories" in all_data
    assert "4_calculations" in all_data
    assert "5_validation" in all_data


# ============================================================
# Test: verify_all_files() Method
# ============================================================
def test_verify_all_files_success(loader):
    """모든 파일 검증 성공"""
    # 실제 호출
    result = loader.verify_all_files()

    # 검증: Dict[str, bool] 반환, 5개 파일
    assert isinstance(result, dict)
    assert len(result) == 5
    assert all(result.values())  # 모두 True


def test_verify_all_files_missing_file(loader, temp_knowledge_dir):
    """파일 1개 삭제 후 검증 실패"""
    # 1_breakers.json 삭제
    (temp_knowledge_dir / "1_breakers.json").unlink()

    # 캐시 클리어 (삭제 반영)
    loader.clear_cache()

    # 실제 호출
    result = loader.verify_all_files()

    # 검증: 1_breakers.json은 False
    assert isinstance(result, dict)
    assert result["1_breakers.json"] is False
    assert result["2_enclosures.json"] is True  # 나머지는 성공


# ============================================================
# Test: get_file_info() Method
# ============================================================
def test_get_file_info_success(loader):
    """파일 정보 조회"""
    # 실제 호출
    info = loader.get_file_info("1_breakers.json")

    # 검증
    assert isinstance(info, dict)
    assert "filename" in info
    assert info["filename"] == "1_breakers.json"
    assert "path" in info
    assert "size_bytes" in info
    assert info["size_bytes"] > 0
    assert "sha256" in info
    assert "version" in info


def test_get_file_info_nonexistent(loader):
    """존재하지 않는 파일 정보 → KnowledgeFileNotFoundError"""
    # 실제 호출
    with pytest.raises(KnowledgeFileNotFoundError, match="File not found"):
        loader.get_file_info("nonexistent.json")


# ============================================================
# Test: _calculate_sha256() Method
# ============================================================
def test_calculate_sha256(loader, temp_knowledge_dir):
    """SHA256 해시 계산"""
    # 테스트 파일 생성
    test_file = temp_knowledge_dir / "test_hash.json"
    test_content = '{"test": "content"}'
    test_file.write_text(test_content, encoding="utf-8")

    # 예상 해시 계산
    expected_hash = hashlib.sha256(test_content.encode("utf-8")).hexdigest()

    # 실제 호출
    actual_hash = loader._calculate_sha256(test_file)

    # 검증
    assert actual_hash == expected_hash


# ============================================================
# Test: clear_cache() and get_cache_info() Methods
# ============================================================
def test_clear_cache(loader):
    """캐시 클리어"""
    # 실제 호출: 파일 로드 (캐시 생성)
    loader.load("1_breakers.json")

    # 캐시 정보 확인
    cache_info_before = loader.get_cache_info()
    assert cache_info_before["hits"] >= 0

    # 실제 호출: 캐시 클리어
    loader.clear_cache()

    # 캐시 정보 확인: 초기화됨
    cache_info_after = loader.get_cache_info()
    assert cache_info_after["hits"] == 0
    assert cache_info_after["misses"] == 0


def test_get_cache_info(loader):
    """캐시 정보 조회"""
    # 캐시 클리어 (초기 상태)
    loader.clear_cache()

    # 실제 호출: 파일 로드 (캐시 미스)
    loader.load("1_breakers.json")

    # 실제 호출: 캐시 정보
    cache_info = loader.get_cache_info()

    # 검증
    assert isinstance(cache_info, dict)
    assert "hits" in cache_info
    assert "misses" in cache_info
    assert "maxsize" in cache_info
    assert "currsize" in cache_info
    assert cache_info["misses"] >= 1


# ============================================================
# Test: get_knowledge_loader() Singleton
# ============================================================
def test_get_knowledge_loader_singleton(temp_knowledge_dir, monkeypatch):
    """싱글톤 패턴 검증"""
    # 모듈 레벨 _loader 초기화
    import kis_estimator_core.infra.knowledge_loader as kl_module
    kl_module._loader = None

    # 실제 호출: 첫 번째 인스턴스 (temp_knowledge_dir 사용)
    loader1 = get_knowledge_loader(temp_knowledge_dir)

    # 실제 호출: 두 번째 인스턴스
    loader2 = get_knowledge_loader()

    # 검증: 동일 인스턴스
    assert loader1 is loader2

    # 정리: 다음 테스트에 영향 없도록 리셋
    kl_module._loader = None


def test_get_knowledge_loader_default_path(monkeypatch):
    """기본 경로 사용 (환경변수 없음)"""
    # 모듈 레벨 _loader 초기화
    import kis_estimator_core.infra.knowledge_loader as kl_module
    kl_module._loader = None

    # 실제 호출: 기본 경로 사용 (실제 프로젝트 경로)
    # 이 테스트는 실제 지식 파일이 있을 때만 성공
    try:
        loader = get_knowledge_loader()
        assert loader is not None
    except (FileNotFoundError, KnowledgeFileNotFoundError):
        # 실제 지식 파일이 없으면 스킵
        pytest.skip("Real knowledge files not available")
    finally:
        # 정리
        kl_module._loader = None
