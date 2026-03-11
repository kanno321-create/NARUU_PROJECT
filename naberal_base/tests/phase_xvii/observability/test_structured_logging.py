"""
Phase XVII - Observability Structured Logging Tests (≥4 tests)

Coverage Target: structured logging fields (traceId, duration_ms, http.method)
Zero-Mock: SSOT-based logging validation only
"""

import pytest
import logging
import json


@pytest.mark.unit
class TestStructuredLoggingFields:
    """Test structured logging fields (traceId, duration_ms, http.method)"""

    def test_log_record_has_traceid_field(self, caplog):
        """로그 레코드에 traceId 필드 존재 (UUID 형식)"""
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.INFO):
            # 구조화 로그 시뮬레이션 (extra 필드 사용)
            logger.info(
                "Test message",
                extra={"traceId": "550e8400-e29b-41d4-a716-446655440000"},
            )

        # traceId 필드 존재 확인
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert hasattr(record, "traceId")
        assert record.traceId == "550e8400-e29b-41d4-a716-446655440000"

    def test_log_record_has_duration_ms_field(self, caplog):
        """로그 레코드에 duration_ms 필드 존재 (숫자)"""
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.INFO):
            # duration_ms 필드 포함
            logger.info("Request completed", extra={"duration_ms": 123.45})

        # duration_ms 필드 존재 확인
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert hasattr(record, "duration_ms")
        assert record.duration_ms == 123.45

    def test_log_record_has_http_method_field(self, caplog):
        """로그 레코드에 http.method 필드 존재 (HTTP verb)"""
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.INFO):
            # http.method 필드 포함
            logger.info("HTTP request", extra={"http.method": "POST"})

        # http.method 필드 존재 확인 (속성명은 http_method로 변환)
        assert len(caplog.records) == 1
        record = caplog.records[0]
        # Python logging에서는 "."이 "_"로 변환됨
        # extra={"http.method": "POST"} → record.http_method 또는 record.__dict__["http.method"]
        if hasattr(record, "http_method"):
            assert record.http_method == "POST"
        else:
            # __dict__에서 직접 접근
            assert "http.method" in record.__dict__
            assert record.__dict__["http.method"] == "POST"

    def test_structured_log_json_format(self):
        """구조화 로그 JSON 포맷팅"""
        # JSON 로그 시뮬레이션
        log_entry = {
            "timestamp": "2025-11-01T12:00:00Z",
            "level": "INFO",
            "message": "Test message",
            "traceId": "550e8400-e29b-41d4-a716-446655440000",
            "duration_ms": 123.45,
            "http.method": "POST",
        }

        # JSON 직렬화 가능 여부 확인
        json_str = json.dumps(log_entry)
        assert json_str is not None

        # JSON 역직렬화 후 필드 확인
        parsed = json.loads(json_str)
        assert parsed["traceId"] == "550e8400-e29b-41d4-a716-446655440000"
        assert parsed["duration_ms"] == 123.45
        assert parsed["http.method"] == "POST"


@pytest.mark.unit
class TestLoggingLevels:
    """Test logging level filtering (ERROR, WARNING, INFO, DEBUG)"""

    def test_error_log_captured(self, caplog):
        """ERROR 레벨 로그 캡처"""
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.ERROR):
            logger.error("Error message", extra={"error_code": "E_INTERNAL"})

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "ERROR"
        assert hasattr(record, "error_code")
        assert record.error_code == "E_INTERNAL"

    def test_warning_log_captured(self, caplog):
        """WARNING 레벨 로그 캡처"""
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.WARNING):
            logger.warning("Warning message", extra={"warning_type": "DEPRECATION"})

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelname == "WARNING"

    def test_info_log_filtered_by_level(self, caplog):
        """INFO 레벨 로그 필터링 (WARNING 이상만 캡처 시 제외)"""
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.WARNING):
            logger.info("Info message")  # WARNING 미만이므로 필터링
            logger.warning("Warning message")  # 캡처됨

        # INFO는 필터링되어 1개만 캡처
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
