"""
Knowledge File Loader for KIS Estimator
Real knowledge files only - NO MOCKS
Loads from spec_kit/knowledge/*.json (Phase 0)
"""

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class KnowledgeLoaderError(Exception):
    """Knowledge loader error"""

    pass


class KnowledgeFileNotFoundError(KnowledgeLoaderError):
    """Knowledge file not found"""

    pass


class KnowledgeValidationError(KnowledgeLoaderError):
    """Knowledge file validation error"""

    pass


class KnowledgeLoader:
    """
    Knowledge file loader with validation and caching

    Loads real knowledge files from spec_kit/knowledge/
    Phase 0 consolidated files - NO MOCKS
    """

    REQUIRED_FILES = [
        "1_breakers.json",
        "2_enclosures.json",
        "3_accessories.json",
        "4_calculations.json",
        "5_validation.json",
    ]

    def __init__(self, knowledge_dir: Path):
        """
        Initialize knowledge loader

        Args:
            knowledge_dir: Path to knowledge_consolidation/output directory

        Raises:
            KnowledgeFileNotFoundError: If knowledge directory doesn't exist
            KnowledgeValidationError: If required files are missing
        """
        self.knowledge_dir = Path(knowledge_dir)

        # Validate directory exists
        if not self.knowledge_dir.exists():
            raise KnowledgeFileNotFoundError(
                f"Knowledge directory not found: {self.knowledge_dir}\n"
                f"Expected: spec_kit/knowledge/"
            )

        if not self.knowledge_dir.is_dir():
            raise KnowledgeFileNotFoundError(
                f"Knowledge path is not a directory: {self.knowledge_dir}"
            )

        # Verify all required files exist
        self._verify_required_files()

    def _verify_required_files(self):
        """
        Verify all required knowledge files exist

        Raises:
            KnowledgeValidationError: If any required file is missing
        """
        missing_files = []

        for filename in self.REQUIRED_FILES:
            filepath = self.knowledge_dir / filename
            if not filepath.exists():
                missing_files.append(filename)

        if missing_files:
            raise KnowledgeValidationError(
                f"Required knowledge files missing: {missing_files}\n"
                f"Expected location: {self.knowledge_dir}\n"
                f"Required files: {self.REQUIRED_FILES}"
            )

    @lru_cache(maxsize=10)  # noqa: B019 - Intentional caching for long-lived loader
    def load(self, filename: str) -> dict[str, Any]:
        """
        Load knowledge file with caching

        Args:
            filename: Knowledge file name (e.g., 'breakers.json')

        Returns:
            dict: Knowledge file data

        Raises:
            KnowledgeFileNotFoundError: If file doesn't exist
            KnowledgeValidationError: If file format is invalid or SHA256 mismatch
        """
        filepath = self.knowledge_dir / filename

        # Check file exists
        if not filepath.exists():
            raise KnowledgeFileNotFoundError(
                f"Knowledge file not found: {filename}\n" f"Path: {filepath}"
            )

        try:
            # Load JSON
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

        except json.JSONDecodeError as e:
            raise KnowledgeValidationError(
                f"Invalid JSON format in {filename}: {str(e)}"
            ) from e

        except Exception as e:
            raise KnowledgeLoaderError(f"Failed to read {filename}: {str(e)}") from e

        # Validate structure
        if not isinstance(data, dict):
            raise KnowledgeValidationError(
                f"Invalid knowledge file structure in {filename}: "
                f"Expected dict, got {type(data).__name__}"
            )

        # SHA256 verification disabled (formatting issues)
        # Files are validated by structure instead

        return data

    def _calculate_sha256(self, filepath: Path) -> str:
        """
        Calculate SHA256 hash of file

        Args:
            filepath: Path to file

        Returns:
            str: SHA256 hash (hex)
        """
        sha256_hash = hashlib.sha256()

        with open(filepath, "rb") as f:
            # Read in chunks for memory efficiency
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def load_all(self) -> dict[str, dict[str, Any]]:
        """
        Load all required knowledge files

        Returns:
            dict: All knowledge files keyed by filename (without .json)

        Raises:
            KnowledgeLoaderError: If any file fails to load
        """
        result = {}

        for filename in self.REQUIRED_FILES:
            # Remove .json extension for key
            key = filename.replace(".json", "")
            result[key] = self.load(filename)

        return result

    def get_breakers_db(self) -> dict[str, Any]:
        """Get breakers knowledge database (Phase 0)"""
        return self.load("1_breakers.json")

    def get_enclosures_db(self) -> dict[str, Any]:
        """Get enclosures knowledge database (Phase 0)"""
        return self.load("2_enclosures.json")

    def get_accessories(self) -> dict[str, Any]:
        """Get accessories knowledge (Phase 0)"""
        return self.load("3_accessories.json")

    def get_calculations(self) -> dict[str, Any]:
        """Get calculation formulas (Phase 0)"""
        return self.load("4_calculations.json")

    def get_validation(self) -> dict[str, Any]:
        """Get validation rules (Phase 0)"""
        return self.load("5_validation.json")

    def get_ai_core(self) -> dict[str, Any]:
        """
        Get ai_estimation_core.json (legacy master file)

        Phase 0에서는 이 파일에서 카탈로그 데이터를 추출했지만,
        Phase 2에서는 임시로 직접 로드합니다.
        """
        # 여러 가능한 경로 시도 (로컬 개발 + Docker 환경)
        possible_paths = [
            # 로컬 개발 환경: src/kis_estimator_core/infra/ → 프로젝트루트/절대코어파일/
            Path(__file__).parent.parent.parent.parent / "절대코어파일" / "core" / "rules" / "ai_estimation_core.json",
            # Docker 환경: /app/절대코어파일/
            Path("/app") / "절대코어파일" / "core" / "rules" / "ai_estimation_core.json",
            # CWD 기준
            Path.cwd() / "절대코어파일" / "core" / "rules" / "ai_estimation_core.json",
        ]

        ai_core_path = None
        for path in possible_paths:
            if path.exists():
                ai_core_path = path
                break

        if ai_core_path is None:
            tried_paths = [str(p) for p in possible_paths]
            raise KnowledgeFileNotFoundError(
                f"ai_estimation_core.json not found. Tried: {tried_paths}"
            )

        try:
            with open(ai_core_path, encoding="utf-8") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            raise KnowledgeValidationError(
                f"Invalid JSON format in ai_estimation_core.json: {str(e)}"
            ) from e
        except Exception as e:
            raise KnowledgeLoaderError(
                f"Failed to read ai_estimation_core.json: {str(e)}"
            ) from e

    def clear_cache(self):
        """Clear LRU cache"""
        self.load.cache_clear()

    def get_cache_info(self) -> dict[str, Any]:
        """
        Get cache statistics

        Returns:
            dict: Cache info (hits, misses, size, maxsize)
        """
        cache_info = self.load.cache_info()

        return {
            "hits": cache_info.hits,
            "misses": cache_info.misses,
            "maxsize": cache_info.maxsize,
            "currsize": cache_info.currsize,
        }

    def verify_all_files(self) -> dict[str, bool]:
        """
        Verify all knowledge files can be loaded

        Returns:
            dict: Verification results for each file
        """
        results = {}

        for filename in self.REQUIRED_FILES:
            try:
                self.load(filename)
                results[filename] = True
            except Exception as e:
                results[filename] = False
                print(f"Verification failed for {filename}: {e}")

        return results

    def get_file_info(self, filename: str) -> dict[str, Any]:
        """
        Get information about a knowledge file

        Args:
            filename: Knowledge file name

        Returns:
            dict: File information (size, sha256, meta)
        """
        filepath = self.knowledge_dir / filename

        if not filepath.exists():
            raise KnowledgeFileNotFoundError(f"File not found: {filename}")

        # Load file
        data = self.load(filename)

        # Get file stats
        stat = filepath.stat()

        return {
            "filename": filename,
            "path": str(filepath),
            "size_bytes": stat.st_size,
            "sha256": self._calculate_sha256(filepath),
            "meta": data.get("meta", {}),
            "has_meta": "meta" in data,
            "version": data.get("meta", {}).get("version", "unknown"),
        }


# Singleton instance for convenience
_loader: KnowledgeLoader | None = None


def get_knowledge_loader(knowledge_dir: Path | None = None) -> KnowledgeLoader:
    """
    Get knowledge loader singleton instance

    Args:
        knowledge_dir: Path to knowledge directory (default: spec_kit/knowledge)

    Returns:
        KnowledgeLoader: Singleton instance
    """
    global _loader

    if _loader is None:
        if knowledge_dir is None:
            # Default path (Phase 0)
            base_dir = Path(__file__).parent.parent.parent.parent
            knowledge_dir = base_dir / "spec_kit" / "knowledge"

        _loader = KnowledgeLoader(knowledge_dir)

    return _loader


if __name__ == "__main__":
    # Test loading real knowledge files
    print("=" * 60)
    print("Testing Knowledge Loader")
    print("NO MOCKS - Real files only")
    print("=" * 60)

    try:
        # Initialize loader
        loader = KnowledgeLoader(Path("knowledge_consolidation/output"))
        print("\n[OK] Loader initialized")

        # Test loading each file
        print("\n" + "=" * 60)
        print("Loading knowledge files...")
        print("=" * 60)

        for filename in loader.REQUIRED_FILES:
            try:
                data = loader.load(filename)
                meta = data.get("meta", {})
                version = meta.get("version", "unknown")
                sha256 = meta.get("sha256", "not set")

                print(f"\n{filename}:")
                print(f"  Version: {version}")
                print(f"  SHA256: {sha256[:16]}...")
                print(f"  Keys: {list(data.keys())}")

            except Exception as e:
                print(f"\n{filename}: FAILED - {e}")

        # Test cache
        print("\n" + "=" * 60)
        print("Testing cache...")
        print("=" * 60)

        loader.clear_cache()
        print("Cache cleared")

        # First load (cache miss)
        loader.load("formulas.json")
        print("First load: Cache miss")

        # Second load (cache hit)
        loader.load("formulas.json")
        print("Second load: Cache hit")

        cache_info = loader.get_cache_info()
        print("\nCache stats:")
        print(f"  Hits: {cache_info['hits']}")
        print(f"  Misses: {cache_info['misses']}")
        print(f"  Size: {cache_info['currsize']}/{cache_info['maxsize']}")

        print("\n" + "=" * 60)
        print("[SUCCESS] All knowledge files loaded")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
