"""
Unit Tests for engine/fix4_pipeline.py
Coverage target: >68% for FIX4Pipeline class

Zero-Mock exception: Unit tests may use unittest.mock for external dependencies
to avoid requiring full pipeline infrastructure in CI environment.
"""

import re
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestFIX4PipelineInit:
    """Tests for FIX4Pipeline initialization"""

    def test_init_creates_instance(self):
        """Test initialization creates pipeline instance"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        assert pipeline._workflow_engine is None  # Lazy initialization

    def test_workflow_engine_lazy_init(self):
        """Test workflow_engine property creates engine on first access"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # First access creates engine
        with patch("kis_estimator_core.engine.fix4_pipeline.WorkflowEngine") as mock_engine:
            mock_engine.return_value = MagicMock()
            engine = pipeline.workflow_engine

            assert engine is not None
            mock_engine.assert_called_once()

    def test_workflow_engine_singleton(self):
        """Test workflow_engine returns same instance on multiple access"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        with patch("kis_estimator_core.engine.fix4_pipeline.WorkflowEngine") as mock_engine:
            mock_instance = MagicMock()
            mock_engine.return_value = mock_instance

            engine1 = pipeline.workflow_engine
            engine2 = pipeline.workflow_engine

            assert engine1 is engine2
            # Engine created only once
            mock_engine.assert_called_once()


class TestParseBrekakerModel:
    """Tests for _parse_breaker_model method"""

    def test_parse_sangdo_mccb_model(self):
        """Test parsing SANGDO MCCB model"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # SBE-104 = 상도/배선용/경제형/100AF/4극
        frame_af, breaker_type = pipeline._parse_breaker_model("SBE-104")

        assert frame_af == 100
        assert breaker_type == "MCCB"

    def test_parse_sangdo_elb_model(self):
        """Test parsing SANGDO ELB model"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # SEE-52 = 상도/누전/경제형/50AF/2극
        frame_af, breaker_type = pipeline._parse_breaker_model("SEE-52")

        assert frame_af == 50
        assert breaker_type == "ELB"

    def test_parse_sangdo_compact_model(self):
        """Test parsing SANGDO COMPACT model"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # SCE-54 = 상도/컴팩트/경제형/50AF/4극
        frame_af, breaker_type = pipeline._parse_breaker_model("SCE-54")

        assert frame_af == 50
        assert breaker_type == "COMPACT"

    def test_parse_ls_mccb_model(self):
        """Test parsing LS MCCB model"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # ABN-54 = LS/배선용/경제형/50AF/4극
        frame_af, breaker_type = pipeline._parse_breaker_model("ABN-54")

        assert frame_af == 50
        assert breaker_type == "MCCB"

    def test_parse_ls_elb_model(self):
        """Test parsing LS ELB model"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # EBN-103 = LS/누전/경제형/100AF/3극
        frame_af, breaker_type = pipeline._parse_breaker_model("EBN-103")

        assert frame_af == 100
        assert breaker_type == "ELB"

    def test_parse_small_breaker_sib32(self):
        """Test parsing small breaker SIB-32"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        frame_af, breaker_type = pipeline._parse_breaker_model("SIB-32")

        assert frame_af == 30
        assert breaker_type == "MCCB"

    def test_parse_small_breaker_32grhs(self):
        """Test parsing small breaker 32GRHS"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        frame_af, breaker_type = pipeline._parse_breaker_model("32GRHS")

        assert frame_af == 30
        assert breaker_type == "ELB"

    def test_parse_empty_model_returns_defaults(self):
        """Test empty model returns defaults"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        frame_af, breaker_type = pipeline._parse_breaker_model("")

        assert frame_af == 100  # Default
        assert breaker_type == "MCCB"  # Default

    def test_parse_none_model_returns_defaults(self):
        """Test None model returns defaults"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        frame_af, breaker_type = pipeline._parse_breaker_model(None)

        assert frame_af == 100
        assert breaker_type == "MCCB"

    def test_parse_unknown_model_extracts_digits(self):
        """Test unknown model extracts digits as frame"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Unknown pattern with digits
        frame_af, breaker_type = pipeline._parse_breaker_model("UNKNOWN-200")

        assert frame_af == 200
        assert breaker_type == "MCCB"


class TestConvertRequestToWorkflowInput:
    """Tests for _convert_request_to_workflow_input method"""

    def test_convert_basic_request(self):
        """Test converting basic request to workflow input"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Create mock request
        mock_request = MagicMock()
        mock_request.customer_name = "Test Customer"
        mock_request.project_name = "Test Project"
        mock_request.options = None

        # Mock panel with main breaker
        mock_panel = MagicMock()
        mock_panel.panel_name = "LP-M"
        mock_panel.main_breaker = MagicMock()
        mock_panel.main_breaker.model = "SBE-104"
        mock_panel.main_breaker.poles = 4
        mock_panel.main_breaker.ampere = 100
        mock_panel.branch_breakers = []
        mock_panel.accessories = []
        mock_panel.enclosure = None

        mock_request.panels = [mock_panel]

        result = pipeline._convert_request_to_workflow_input(mock_request, panel_index=0)

        assert result["customer_name"] == "Test Customer"
        assert result["project_name"] == "Test Project"
        assert result["main_breaker"]["poles"] == 4
        assert result["main_breaker"]["current"] == 100
        assert result["main_breaker"]["frame_af"] == 100

    def test_convert_request_with_branch_breakers(self):
        """Test converting request with branch breakers"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Create mock request
        mock_request = MagicMock()
        mock_request.customer_name = "Test"
        mock_request.project_name = ""
        mock_request.options = None

        # Mock panel
        mock_panel = MagicMock()
        mock_panel.panel_name = "LP-M"
        mock_panel.main_breaker = MagicMock()
        mock_panel.main_breaker.model = "SBE-104"
        mock_panel.main_breaker.poles = 4
        mock_panel.main_breaker.ampere = 100

        # Branch breakers
        branch1 = MagicMock()
        branch1.model = "SBE-52"
        branch1.poles = 2
        branch1.ampere = 20
        branch1.quantity = 5

        mock_panel.branch_breakers = [branch1]
        mock_panel.accessories = []
        mock_panel.enclosure = None

        mock_request.panels = [mock_panel]

        result = pipeline._convert_request_to_workflow_input(mock_request, panel_index=0)

        assert len(result["branch_breakers"]) == 1
        assert result["branch_breakers"][0]["poles"] == 2
        assert result["branch_breakers"][0]["current"] == 20
        assert result["branch_breakers"][0]["quantity"] == 5

    def test_convert_request_with_enclosure(self):
        """Test converting request with enclosure info"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Create mock request
        mock_request = MagicMock()
        mock_request.customer_name = "Test"
        mock_request.project_name = ""
        mock_request.options = None

        # Mock panel with enclosure
        mock_panel = MagicMock()
        mock_panel.panel_name = "LP-M"
        mock_panel.main_breaker = None
        mock_panel.branch_breakers = []
        mock_panel.accessories = []

        mock_panel.enclosure = MagicMock()
        mock_panel.enclosure.material = "STEEL 1.6T"
        mock_panel.enclosure.type = "옥내노출"

        mock_request.panels = [mock_panel]

        result = pipeline._convert_request_to_workflow_input(mock_request, panel_index=0)

        assert result["enclosure_material"] == "STEEL 1.6T"
        assert result["enclosure_type"] == "옥내노출"


class TestGenerateEstimateId:
    """Tests for _generate_estimate_id method"""

    def test_generate_estimate_id_format(self):
        """Test estimate ID format: EST-YYYYMMDD-NNNN"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        estimate_id = pipeline._generate_estimate_id()

        # Check format: EST-YYYYMMDD-NNNN
        pattern = r"^EST-\d{8}-\d{4}$"
        assert re.match(pattern, estimate_id)

    def test_generate_estimate_id_contains_date(self):
        """Test estimate ID contains current date"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        estimate_id = pipeline._generate_estimate_id()
        today = datetime.now().strftime("%Y%m%d")

        assert today in estimate_id


class TestGetPipeline:
    """Tests for get_pipeline singleton function"""

    def test_get_pipeline_returns_instance(self):
        """Test get_pipeline returns pipeline instance"""
        from kis_estimator_core.engine import fix4_pipeline

        # Reset singleton
        fix4_pipeline._pipeline = None

        pipeline = fix4_pipeline.get_pipeline()

        assert pipeline is not None

    def test_get_pipeline_singleton(self):
        """Test get_pipeline returns same instance"""
        from kis_estimator_core.engine import fix4_pipeline

        # Reset singleton
        fix4_pipeline._pipeline = None

        pipeline1 = fix4_pipeline.get_pipeline()
        pipeline2 = fix4_pipeline.get_pipeline()

        assert pipeline1 is pipeline2

        # Cleanup
        fix4_pipeline._pipeline = None


class TestExtractStageResults:
    """Tests for _extract_stage*_result methods"""

    def test_extract_stage1_result_success(self):
        """Test extracting Stage 1 result from successful phase"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock phase result
        mock_phase = MagicMock()
        mock_phase.success = True
        mock_phase.output = {
            "fit_score": 0.95,
            "dimensions": {"W": 600, "H": 800, "D": 200}
        }

        result = pipeline._extract_stage1_result(mock_phase)

        assert result.status == "passed"
        assert result.fit_score == 0.95
        assert result.enclosure_size == [600, 800, 200]

    def test_extract_stage1_result_failure(self):
        """Test extracting Stage 1 result from failed phase"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock failed phase
        mock_phase = MagicMock()
        mock_phase.success = False

        result = pipeline._extract_stage1_result(mock_phase)

        assert result.status == "failed"
        assert result.fit_score == 0.0
        assert result.enclosure_size == [0, 0, 0]

    def test_extract_stage1_result_none(self):
        """Test extracting Stage 1 result from None phase"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        result = pipeline._extract_stage1_result(None)

        assert result.status == "failed"

    def test_extract_stage2_result_success(self):
        """Test extracting Stage 2 result from successful phase"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock phase result
        mock_phase = MagicMock()
        mock_phase.success = True
        mock_phase.output = {
            "validation": {
                "phase_imbalance_pct": 2.5,
                "clearance_violations": 0
            }
        }

        result = pipeline._extract_stage2_result(mock_phase)

        assert result.status == "passed"
        assert result.phase_balance == 2.5
        assert result.clearance_violations == 0
        assert result.thermal_violations == 0

    def test_extract_stage2_result_failure(self):
        """Test extracting Stage 2 result from failed phase"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        mock_phase = MagicMock()
        mock_phase.success = False

        result = pipeline._extract_stage2_result(mock_phase)

        assert result.status == "failed"
        assert result.phase_balance == 100.0
        assert result.clearance_violations == 1

    def test_extract_stage3_result_success(self):
        """Test extracting Stage 3 result from successful phase"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        mock_phase = MagicMock()
        mock_phase.success = True
        mock_phase.output = {
            "validation": {"formula_preservation_pct": 100}
        }

        result = pipeline._extract_stage3_result(mock_phase)

        assert result.status == "passed"
        assert result.formula_preservation == 100


class TestExtractValidationChecks:
    """Tests for _extract_validation_checks method"""

    def test_extract_validation_checks_success(self):
        """Test extracting validation checks from successful result"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock request
        mock_request = MagicMock()
        mock_panel = MagicMock()
        mock_panel.accessories = []
        mock_request.panels = [mock_panel]

        # Mock workflow result
        mock_result = MagicMock()
        mock_result.success = True

        result = pipeline._extract_validation_checks(mock_request, mock_result)

        assert result.CHK_ENCLOSURE_H_FORMULA == "passed"
        assert result.CHK_PHASE_BALANCE == "passed"
        assert result.CHK_CLEARANCE_VIOLATIONS == "passed"
        assert result.CHK_THERMAL_VIOLATIONS == "passed"
        assert result.CHK_FORMULA_PRESERVATION == "passed"
        # No magnet/timer
        assert result.CHK_BUNDLE_MAGNET == "skipped"
        assert result.CHK_BUNDLE_TIMER == "skipped"

    def test_extract_validation_checks_with_magnet(self):
        """Test validation checks with magnet accessory"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock request with magnet
        mock_request = MagicMock()
        mock_panel = MagicMock()
        mock_accessory = MagicMock()
        mock_accessory.type = "magnet"
        mock_panel.accessories = [mock_accessory]
        mock_request.panels = [mock_panel]

        mock_result = MagicMock()
        mock_result.success = True

        result = pipeline._extract_validation_checks(mock_request, mock_result)

        assert result.CHK_BUNDLE_MAGNET == "passed"

    def test_extract_validation_checks_with_timer(self):
        """Test validation checks with timer accessory"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock request with timer
        mock_request = MagicMock()
        mock_panel = MagicMock()
        mock_accessory = MagicMock()
        mock_accessory.type = "timer"
        mock_panel.accessories = [mock_accessory]
        mock_request.panels = [mock_panel]

        mock_result = MagicMock()
        mock_result.success = True

        result = pipeline._extract_validation_checks(mock_request, mock_result)

        assert result.CHK_BUNDLE_TIMER == "passed"


class TestExtractPrices:
    """Tests for _extract_prices method"""

    def test_extract_prices_no_output(self):
        """Test price extraction with no final_output"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        mock_result = MagicMock()
        mock_result.final_output = None

        subtotal, total_with_vat = pipeline._extract_prices(mock_result)

        assert subtotal == 0
        assert total_with_vat == 0

    def test_extract_prices_file_not_found(self):
        """Test price extraction with non-existent file"""
        from pathlib import Path

        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        mock_result = MagicMock()
        mock_result.final_output = Path("/nonexistent/file.xlsx")

        subtotal, total_with_vat = pipeline._extract_prices(mock_result)

        assert subtotal == 0
        assert total_with_vat == 0


class TestCalculateSubtotalFromCells:
    """Tests for _calculate_subtotal_from_cells method"""

    def test_calculate_subtotal_basic(self):
        """Test basic subtotal calculation from cells"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock worksheet
        mock_ws = MagicMock()

        # Setup cell values
        def get_cell(cell_ref):
            mock_cell = MagicMock()
            row = int(cell_ref[1:])
            col = cell_ref[0]

            if row == 3:
                if col == "E":
                    mock_cell.value = 2  # quantity
                elif col == "F":
                    mock_cell.value = 1000  # price
            elif row == 4:
                if col == "E":
                    mock_cell.value = 3
                elif col == "F":
                    mock_cell.value = 2000
            else:
                mock_cell.value = None

            return mock_cell

        mock_ws.__getitem__ = MagicMock(side_effect=get_cell)

        total = pipeline._calculate_subtotal_from_cells(mock_ws)

        # 2*1000 + 3*2000 = 8000
        assert total == 8000

    def test_calculate_subtotal_with_none_values(self):
        """Test subtotal calculation handles None values"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        mock_ws = MagicMock()

        def get_cell(cell_ref):
            mock_cell = MagicMock()
            mock_cell.value = None
            return mock_cell

        mock_ws.__getitem__ = MagicMock(side_effect=get_cell)

        total = pipeline._calculate_subtotal_from_cells(mock_ws)

        assert total == 0


class TestFIX4PipelineExecute:
    """Tests for FIX4Pipeline.execute method"""

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful pipeline execution"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        # Mock request
        mock_request = MagicMock()
        mock_request.customer_name = "Test"
        mock_request.project_name = "Test Project"
        mock_request.options = None
        mock_request.breaker_brand = "상도차단기"

        mock_panel = MagicMock()
        mock_panel.panel_name = "LP-M"
        mock_panel.main_breaker = MagicMock()
        mock_panel.main_breaker.model = "SBE-104"
        mock_panel.main_breaker.poles = 4
        mock_panel.main_breaker.ampere = 100
        mock_panel.branch_breakers = []
        mock_panel.accessories = []
        mock_panel.enclosure = None

        mock_request.panels = [mock_panel]

        # Mock workflow engine by setting _workflow_engine directly
        mock_engine = MagicMock()
        mock_workflow_result = MagicMock()
        mock_workflow_result.success = True
        mock_workflow_result.phases = []
        mock_workflow_result.final_output = None
        mock_workflow_result.blocking_errors = []
        mock_engine.execute = AsyncMock(return_value=mock_workflow_result)

        pipeline._workflow_engine = mock_engine

        response = await pipeline.execute(mock_request, estimate_id="EST-20251128-0001")

        assert response.estimate_id == "EST-20251128-0001"
        assert response.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_generates_id_if_not_provided(self):
        """Test execute generates estimate_id if not provided"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        mock_request = MagicMock()
        mock_request.customer_name = "Test"
        mock_request.project_name = ""
        mock_request.options = None

        mock_panel = MagicMock()
        mock_panel.panel_name = "LP-M"
        mock_panel.main_breaker = MagicMock()
        mock_panel.main_breaker.model = "SBE-104"
        mock_panel.main_breaker.poles = 4
        mock_panel.main_breaker.ampere = 100
        mock_panel.branch_breakers = []
        mock_panel.accessories = []
        mock_panel.enclosure = None

        mock_request.panels = [mock_panel]

        mock_engine = MagicMock()
        mock_workflow_result = MagicMock()
        mock_workflow_result.success = True
        mock_workflow_result.phases = []
        mock_workflow_result.final_output = None
        mock_workflow_result.blocking_errors = []
        mock_engine.execute = AsyncMock(return_value=mock_workflow_result)

        pipeline._workflow_engine = mock_engine

        response = await pipeline.execute(mock_request, estimate_id=None)

        # Should have generated ID
        assert response.estimate_id.startswith("EST-")

    @pytest.mark.asyncio
    async def test_execute_multiple_panels(self):
        """Test execute with multiple panels"""
        from kis_estimator_core.engine.fix4_pipeline import FIX4Pipeline

        pipeline = FIX4Pipeline()

        mock_request = MagicMock()
        mock_request.customer_name = "Test"
        mock_request.project_name = ""
        mock_request.options = None

        # Two panels
        mock_panel1 = MagicMock()
        mock_panel1.panel_name = "LP-M1"
        mock_panel1.main_breaker = MagicMock()
        mock_panel1.main_breaker.model = "SBE-104"
        mock_panel1.main_breaker.poles = 4
        mock_panel1.main_breaker.ampere = 100
        mock_panel1.branch_breakers = []
        mock_panel1.accessories = []
        mock_panel1.enclosure = None

        mock_panel2 = MagicMock()
        mock_panel2.panel_name = "LP-M2"
        mock_panel2.main_breaker = MagicMock()
        mock_panel2.main_breaker.model = "SBE-52"
        mock_panel2.main_breaker.poles = 2
        mock_panel2.main_breaker.ampere = 50
        mock_panel2.branch_breakers = []
        mock_panel2.accessories = []
        mock_panel2.enclosure = None

        mock_request.panels = [mock_panel1, mock_panel2]

        mock_engine = MagicMock()
        mock_workflow_result = MagicMock()
        mock_workflow_result.success = True
        mock_workflow_result.phases = []
        mock_workflow_result.final_output = None
        mock_workflow_result.blocking_errors = []
        mock_engine.execute = AsyncMock(return_value=mock_workflow_result)

        pipeline._workflow_engine = mock_engine

        response = await pipeline.execute(mock_request, estimate_id="EST-20251128-0002")

        # Should have called workflow engine twice (once per panel)
        assert mock_engine.execute.call_count == 2
