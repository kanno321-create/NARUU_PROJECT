import pytest
from unittest.mock import MagicMock, AsyncMock
from kis_estimator_core.services.drawing_service import DrawingService
from kis_estimator_core.core.ssot.errors import EstimatorError
import json

@pytest.mark.asyncio
async def test_generate_drawing_success():
    # Setup
    mock_db = AsyncMock()
    service = DrawingService(mock_db)
    
    # Mock DB result for Layout stage
    mock_result = MagicMock()
    placements = [
        {"id": "MAIN", "x": 10, "y": 10, "width_mm": 100, "height_mm": 130},
        {"id": "BR1", "x": 120, "y": 10, "width_mm": 50, "height_mm": 130}
    ]
    stage_output = {"placements": placements}
    mock_result.fetchone.return_value = [json.dumps(stage_output)]
    mock_db.execute.return_value = mock_result
    
    # Execute
    result = await service.generate_drawing("EST-123")
    
    # Verify
    assert result["estimate_id"] == "EST-123"
    assert result["drawing_type"] == "SVG"
    assert result["path"] == "drawings/EST-123.svg"
    assert "<svg" in result["content_preview"]
    assert "rect" in result["content_preview"]

@pytest.mark.asyncio
async def test_generate_drawing_no_layout_data():
    # Setup
    mock_db = AsyncMock()
    service = DrawingService(mock_db)
    
    # Mock empty DB result
    mock_result = MagicMock()
    mock_result.fetchone.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Execute & Verify
    with pytest.raises(EstimatorError) as excinfo:
        await service.generate_drawing("EST-123")
    
    assert excinfo.value.payload.code == "E_NOT_FOUND"
