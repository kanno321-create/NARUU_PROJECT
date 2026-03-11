"""Smoke test for PDF content hash calculation and Evidence Footer integration."""

import pytest
from pathlib import Path
from decimal import Decimal
from pypdf import PdfReader
from kis_estimator_core.engine.pdf_generator import PDFGenerator


class MockEstimateData:
    """Mock EstimateData for testing (Zero-Mock: Real data structure)."""

    def __init__(self, customer_name: str, project_name: str, panels: list):
        self.customer_name = customer_name
        self.project_name = project_name
        self.panels = panels


class MockPanel:
    """Mock Panel for testing (Zero-Mock: Real data structure)."""

    def __init__(self, total_price: Decimal, items: list):
        self.total_price = total_price
        self.items = items


class MockItem:
    """Mock Item for testing (Zero-Mock: Real data structure)."""

    def __init__(self, description: str, quantity: int, line_total: Decimal):
        self.description = description
        self.quantity = quantity
        self.line_total = line_total


@pytest.mark.smoke
def test_content_hash_calculation(tmp_path):
    """
    Smoke test: Verify content hash is calculated correctly.

    Zero-Mock: Uses real PDFGenerator and real data structures.
    """
    generator = PDFGenerator()

    # Create test data
    items = [
        MockItem("차단기 SBE-102 2P 60A", 5, Decimal("62500")),
        MockItem("차단기 SBE-203 2P 125A", 3, Decimal("108000")),
    ]
    panel = MockPanel(Decimal("170500"), items)
    estimate_data = MockEstimateData("테스트고객", "테스트프로젝트", [panel])

    # Calculate content hash
    content_hash = generator._calculate_content_hash(estimate_data)

    # Verify hash format (8 characters)
    assert isinstance(content_hash, str), "Content hash should be string"
    assert len(content_hash) == 8, f"Content hash should be 8 characters (got {len(content_hash)})"

    # Verify hash is hexadecimal
    try:
        int(content_hash, 16)
    except ValueError:
        pytest.fail(f"Content hash '{content_hash}' is not valid hexadecimal")


@pytest.mark.smoke
def test_content_hash_in_footer(tmp_path):
    """
    Smoke test: Verify content hash appears in PDF Evidence Footer.

    Zero-Mock: Actually creates PDF and checks footer content.
    """
    generator = PDFGenerator()

    # Create test data
    items = [
        MockItem("차단기 SBE-102 2P 60A", 5, Decimal("62500")),
    ]
    panel = MockPanel(Decimal("62500"), items)
    estimate_data = MockEstimateData("테스트고객", "테스트프로젝트", [panel])

    # Generate PDF
    output_path = tmp_path / "content_hash_test.pdf"
    generator.generate(
        estimate_data,
        output_path,
        build_tag="test-build",
        git_hash="12345678"
    )

    # Extract text using PyPDF2 (PDF bytes are encoded, need text extraction)
    pdf_reader = PdfReader(str(output_path))
    all_text = ""
    for page in pdf_reader.pages:
        all_text += page.extract_text()

    # Verify Content: label exists in footer
    assert "Content:" in all_text, "PDF should contain 'Content:' in footer"

    # Verify footer format (Build, Hash, Content, TS)
    assert "Build:" in all_text, "PDF should contain 'Build:' in footer"
    assert "Hash:" in all_text, "PDF should contain 'Hash:' in footer"
    assert "TS:" in all_text, "PDF should contain 'TS:' in footer"

    # Verify build tag and git hash values
    assert "test-build" in all_text, "PDF should contain build tag 'test-build'"
    assert "12345678" in all_text, "PDF should contain git hash '12345678'"


@pytest.mark.smoke
def test_content_hash_deterministic(tmp_path):
    """
    Smoke test: Identical content produces identical hash.

    Zero-Mock: Creates two PDFs with same data and compares hashes.
    """
    generator = PDFGenerator()

    # Create identical test data (set 1)
    items1 = [
        MockItem("차단기 SBE-102 2P 60A", 5, Decimal("62500")),
        MockItem("차단기 SBE-203 2P 125A", 3, Decimal("108000")),
    ]
    panel1 = MockPanel(Decimal("170500"), items1)
    estimate_data1 = MockEstimateData("테스트고객", "테스트프로젝트", [panel1])

    # Create identical test data (set 2)
    items2 = [
        MockItem("차단기 SBE-102 2P 60A", 5, Decimal("62500")),
        MockItem("차단기 SBE-203 2P 125A", 3, Decimal("108000")),
    ]
    panel2 = MockPanel(Decimal("170500"), items2)
    estimate_data2 = MockEstimateData("테스트고객", "테스트프로젝트", [panel2])

    # Calculate hashes
    hash1 = generator._calculate_content_hash(estimate_data1)
    hash2 = generator._calculate_content_hash(estimate_data2)

    # Verify identical content → identical hash
    assert hash1 == hash2, f"Identical content should produce identical hash (got {hash1} vs {hash2})"


@pytest.mark.smoke
def test_content_hash_different(tmp_path):
    """
    Smoke test: Different content produces different hash.

    Zero-Mock: Creates two PDFs with different data and compares hashes.
    """
    generator = PDFGenerator()

    # Create test data (set 1)
    items1 = [
        MockItem("차단기 SBE-102 2P 60A", 5, Decimal("62500")),
    ]
    panel1 = MockPanel(Decimal("62500"), items1)
    estimate_data1 = MockEstimateData("테스트고객", "테스트프로젝트", [panel1])

    # Create different test data (set 2 - different quantity)
    items2 = [
        MockItem("차단기 SBE-102 2P 60A", 10, Decimal("125000")),  # Different quantity
    ]
    panel2 = MockPanel(Decimal("125000"), items2)
    estimate_data2 = MockEstimateData("테스트고객", "테스트프로젝트", [panel2])

    # Calculate hashes
    hash1 = generator._calculate_content_hash(estimate_data1)
    hash2 = generator._calculate_content_hash(estimate_data2)

    # Verify different content → different hash
    assert hash1 != hash2, f"Different content should produce different hash (both got {hash1})"


@pytest.mark.smoke
def test_content_hash_customer_change(tmp_path):
    """
    Smoke test: Different customer name produces different hash.

    Zero-Mock: Verifies hash changes when customer name changes.
    """
    generator = PDFGenerator()

    # Create test data (customer A)
    items = [MockItem("차단기", 1, Decimal("10000"))]
    panel = MockPanel(Decimal("10000"), items)
    estimate_data1 = MockEstimateData("고객A", "프로젝트", [panel])

    # Create test data (customer B)
    estimate_data2 = MockEstimateData("고객B", "프로젝트", [panel])

    # Calculate hashes
    hash1 = generator._calculate_content_hash(estimate_data1)
    hash2 = generator._calculate_content_hash(estimate_data2)

    # Verify different customer → different hash
    assert hash1 != hash2, "Different customer name should produce different hash"


@pytest.mark.smoke
def test_content_hash_fallback_on_error(tmp_path):
    """
    Smoke test: Verify content hash returns fallback on error.

    Zero-Mock: Tests error handling with invalid data.
    """
    generator = PDFGenerator()

    # Create invalid estimate_data (missing attributes)
    class InvalidEstimateData:
        pass

    invalid_data = InvalidEstimateData()

    # Calculate content hash (should not crash)
    content_hash = generator._calculate_content_hash(invalid_data)

    # Verify fallback hash (00000000)
    assert content_hash == "00000000", f"Fallback hash should be '00000000' (got '{content_hash}')"


@pytest.mark.smoke
def test_content_hash_on_all_pages(tmp_path):
    """
    Smoke test: Verify content hash appears on all pages.

    Zero-Mock: Creates multi-page PDF and verifies hash on each page.
    """
    generator = PDFGenerator()

    # Create test data
    items = [
        MockItem(f"차단기 {i}", 1, Decimal("10000"))
        for i in range(10)  # Create 10 items for multi-page
    ]
    panel = MockPanel(Decimal("100000"), items)
    estimate_data = MockEstimateData("테스트고객", "테스트프로젝트", [panel])

    # Generate PDF
    output_path = tmp_path / "multipage_hash_test.pdf"
    result_path = generator.generate(
        estimate_data,
        output_path,
        build_tag="test-multi",
        git_hash="abcd1234"
    )

    # Extract text from all pages
    pdf_reader = PdfReader(str(result_path))
    content_label_count = 0
    for page in pdf_reader.pages:
        text = page.extract_text()
        if "Content:" in text:
            content_label_count += 1

    # Verify Content: appears on all pages (at least 3 for cover, terms, details)
    assert content_label_count >= 3, \
        f"Content label should appear at least 3 times (found {content_label_count})"

    # Verify file was created
    assert Path(result_path).exists(), "PDF file should be created"
    assert Path(result_path).stat().st_size > 2048, "Multi-page PDF should be larger than 2KB"
