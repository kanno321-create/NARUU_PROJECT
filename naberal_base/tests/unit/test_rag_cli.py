"""
Unit Tests for rag/cli.py
Coverage target: CLI argument parsing and cmd_validate
"""

import argparse
from unittest.mock import MagicMock, patch


class TestRagCliValidate:
    """Tests for cmd_validate function"""

    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_validate_success(self, mock_config_class, capsys):
        """Test validate command with valid config"""
        from kis_estimator_core.rag.cli import cmd_validate

        # Setup mock
        mock_config = MagicMock()
        mock_config.validate.return_value = (True, ["[OK] Config valid"])
        mock_config.to_dict.return_value = {"key": "value"}
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(json=False)
        result = cmd_validate(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "[OK]" in captured.out

    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_validate_failure(self, mock_config_class, capsys):
        """Test validate command with invalid config"""
        from kis_estimator_core.rag.cli import cmd_validate

        mock_config = MagicMock()
        mock_config.validate.return_value = (False, ["[ERROR] Missing path"])
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(json=False)
        result = cmd_validate(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[FAIL]" in captured.out

    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_validate_with_json(self, mock_config_class, capsys):
        """Test validate command with --json flag"""
        from kis_estimator_core.rag.cli import cmd_validate

        mock_config = MagicMock()
        mock_config.validate.return_value = (True, [])
        mock_config.to_dict.return_value = {"embedding_model": "test", "persist_dir": "/tmp"}
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(json=True)
        result = cmd_validate(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "embedding_model" in captured.out


class TestRagCliMain:
    """Tests for main CLI entry point"""

    def test_main_no_args(self, capsys):
        """Test main() without arguments shows help"""
        from kis_estimator_core.rag.cli import main

        with patch("sys.argv", ["kis-rag"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "KIS RAG" in captured.out or "usage" in captured.out.lower()

    @patch("kis_estimator_core.rag.cli.cmd_validate")
    def test_main_validate_command(self, mock_cmd):
        """Test main() with validate command"""
        from kis_estimator_core.rag.cli import main

        mock_cmd.return_value = 0

        with patch("sys.argv", ["kis-rag", "validate"]):
            result = main()

        mock_cmd.assert_called_once()
        assert result == 0


class TestRagCliStats:
    """Tests for cmd_stats function"""

    @patch("kis_estimator_core.rag.indexer.VectorIndexer")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_stats_success(self, mock_config_class, mock_indexer_class, capsys):
        """Test stats command success"""
        from kis_estimator_core.rag.cli import cmd_stats

        mock_indexer = MagicMock()
        mock_indexer.get_stats.return_value = {
            "collection_name": "test_collection",
            "total_chunks": 100,
            "embedding_model": "test-model",
            "categories_sample": {"BREAKER": 50, "ENCLOSURE": 30},
        }
        mock_indexer_class.return_value = mock_indexer

        args = argparse.Namespace(json=False)
        result = cmd_stats(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "test_collection" in captured.out
        assert "100" in captured.out

    @patch("kis_estimator_core.rag.indexer.VectorIndexer")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_stats_with_json(self, mock_config_class, mock_indexer_class, capsys):
        """Test stats command with --json flag"""
        from kis_estimator_core.rag.cli import cmd_stats

        mock_indexer = MagicMock()
        mock_indexer.get_stats.return_value = {
            "total_chunks": 50,
            "categories_sample": {},
        }
        mock_indexer_class.return_value = mock_indexer

        args = argparse.Namespace(json=True)
        result = cmd_stats(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "total_chunks" in captured.out

    @patch("kis_estimator_core.rag.indexer.VectorIndexer")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_stats_file_not_found(self, mock_config_class, mock_indexer_class, capsys):
        """Test stats command when index doesn't exist"""
        from kis_estimator_core.rag.cli import cmd_stats

        mock_indexer = MagicMock()
        mock_indexer.get_stats.side_effect = FileNotFoundError("Index not found")
        mock_indexer_class.return_value = mock_indexer

        args = argparse.Namespace(json=False)
        result = cmd_stats(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "존재하지 않습니다" in captured.out

    @patch("kis_estimator_core.rag.indexer.VectorIndexer")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_stats_error(self, mock_config_class, mock_indexer_class, capsys):
        """Test stats command with error"""
        from kis_estimator_core.rag.cli import cmd_stats

        mock_indexer = MagicMock()
        mock_indexer.get_stats.side_effect = Exception("DB error")
        mock_indexer_class.return_value = mock_indexer

        args = argparse.Namespace(json=False)
        result = cmd_stats(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out


class TestRagCliClear:
    """Tests for cmd_clear function"""

    @patch("kis_estimator_core.rag.indexer.VectorIndexer")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_clear_force(self, mock_config_class, mock_indexer_class, capsys):
        """Test clear command with --force"""
        from kis_estimator_core.rag.cli import cmd_clear

        mock_indexer = MagicMock()
        mock_indexer.delete_all.return_value = 50
        mock_indexer_class.return_value = mock_indexer

        args = argparse.Namespace(force=True)
        result = cmd_clear(args)

        assert result == 0
        mock_indexer.delete_all.assert_called_once()
        captured = capsys.readouterr()
        assert "50" in captured.out

    @patch("builtins.input", return_value="no")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_clear_cancelled(self, mock_config_class, mock_input, capsys):
        """Test clear command cancelled by user"""
        from kis_estimator_core.rag.cli import cmd_clear

        args = argparse.Namespace(force=False)
        result = cmd_clear(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "취소" in captured.out


class TestRagCliSearch:
    """Tests for cmd_search function"""

    @patch("kis_estimator_core.rag.retriever.HybridRetriever")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_search_no_results(self, mock_config_class, mock_retriever_class, capsys):
        """Test search command with no results"""
        from kis_estimator_core.rag.cli import cmd_search

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = []
        mock_retriever_class.return_value = mock_retriever

        args = argparse.Namespace(
            query="test query",
            top_k=5,
            category=None,
            type="hybrid",
            save_evidence=False,
        )
        result = cmd_search(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "결과가 없습니다" in captured.out

    @patch("kis_estimator_core.rag.retriever.HybridRetriever")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_search_with_results(self, mock_config_class, mock_retriever_class, capsys):
        """Test search command with results"""
        from kis_estimator_core.rag.cli import cmd_search

        mock_result = MagicMock()
        mock_result.score = 0.95
        mock_result.category = "BREAKER"
        mock_result.id = "test-id-123"
        mock_result.content = "Test content"

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = [mock_result]
        mock_retriever.get_stats.return_value = {"total_searches": 1}
        mock_retriever_class.return_value = mock_retriever

        args = argparse.Namespace(
            query="차단기",
            top_k=5,
            category=None,
            type="hybrid",
            save_evidence=False,
        )
        result = cmd_search(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "0.95" in captured.out
        assert "BREAKER" in captured.out

    @patch("kis_estimator_core.rag.retriever.HybridRetriever")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_search_file_not_found(self, mock_config_class, mock_retriever_class, capsys):
        """Test search command when index doesn't exist"""
        from kis_estimator_core.rag.cli import cmd_search

        mock_retriever = MagicMock()
        mock_retriever.search.side_effect = FileNotFoundError("Index not found")
        mock_retriever_class.return_value = mock_retriever

        args = argparse.Namespace(
            query="test",
            top_k=5,
            category=None,
            type="hybrid",
            save_evidence=False,
        )
        result = cmd_search(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "인덱스가 존재하지 않습니다" in captured.out

    @patch("kis_estimator_core.rag.retriever.HybridRetriever")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_search_with_category(self, mock_config_class, mock_retriever_class, capsys):
        """Test search command with category filter"""
        from kis_estimator_core.rag.cli import cmd_search

        mock_retriever = MagicMock()
        mock_retriever.search.return_value = []
        mock_retriever_class.return_value = mock_retriever

        args = argparse.Namespace(
            query="test",
            top_k=5,
            category="BREAKER",
            type="semantic",
            save_evidence=False,
        )
        result = cmd_search(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "BREAKER" in captured.out


class TestRagCliIndex:
    """Tests for cmd_index function"""

    @patch("kis_estimator_core.rag.indexer.VectorIndexer")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_index_success(self, mock_config_class, mock_indexer_class, capsys):
        """Test index command success"""
        from kis_estimator_core.rag.cli import cmd_index

        mock_config = MagicMock()
        mock_config.validate.return_value = (True, ["[OK] Valid"])
        mock_config_class.return_value = mock_config

        mock_indexer = MagicMock()
        mock_indexer.index_all.return_value = {
            "total_chunks": 100,
            "indexed": 90,
            "skipped": 10,
            "errors": 0,
            "by_category": {"BREAKER": 50, "ENCLOSURE": 40},
        }
        mock_indexer.save_evidence.return_value = "/tmp/evidence.json"
        mock_indexer_class.return_value = mock_indexer

        args = argparse.Namespace(force=False, batch_size=32)
        result = cmd_index(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "100" in captured.out
        assert "90" in captured.out

    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_index_config_invalid(self, mock_config_class, capsys):
        """Test index command with invalid config"""
        from kis_estimator_core.rag.cli import cmd_index

        mock_config = MagicMock()
        mock_config.validate.return_value = (False, ["[ERROR] Missing path"])
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(force=False, batch_size=32)
        result = cmd_index(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out

    @patch("kis_estimator_core.rag.indexer.VectorIndexer")
    @patch("kis_estimator_core.rag.cli.RAGConfig")
    def test_cmd_index_with_force(self, mock_config_class, mock_indexer_class, capsys):
        """Test index command with --force flag"""
        from kis_estimator_core.rag.cli import cmd_index

        mock_config = MagicMock()
        mock_config.validate.return_value = (True, [])
        mock_config_class.return_value = mock_config

        mock_indexer = MagicMock()
        mock_indexer.delete_all.return_value = 50
        mock_indexer.index_all.return_value = {
            "total_chunks": 100,
            "indexed": 100,
            "skipped": 0,
            "errors": 0,
            "by_category": {},
        }
        mock_indexer.save_evidence.return_value = "/tmp/evidence.json"
        mock_indexer_class.return_value = mock_indexer

        args = argparse.Namespace(force=True, batch_size=64)
        result = cmd_index(args)

        assert result == 0
        mock_indexer.delete_all.assert_called_once()
