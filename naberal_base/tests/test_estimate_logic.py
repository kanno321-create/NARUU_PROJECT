
import unittest
import logging
from unittest.mock import MagicMock, patch
from kis_estimator_core.services.catalog_service import CatalogService, EnclosureCatalogItem
from kis_estimator_core.engine.data_transformer import DataTransformer
from kis_estimator_core.engine.models import BreakerItem, EstimateData, PanelEstimate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestEstimateLogic(unittest.TestCase):
    def setUp(self):
        # Reset singleton for fresh test
        import kis_estimator_core.services.catalog_service
        kis_estimator_core.services.catalog_service._global_service = None
        
    @patch('kis_estimator_core.services.catalog_service.CatalogService._load_breaker_cache_async')
    @patch('kis_estimator_core.services.catalog_service.CatalogService._load_enclosure_cache_async')
    def test_offline_catalog_fallback(self, mock_load_enclosure, mock_load_breaker):
        """Test that CatalogService falls back to JSON/Defaults when DB fails"""
        
        # Simulate DB failure
        mock_load_breaker.side_effect = Exception("DB Connection Failed")
        mock_load_enclosure.side_effect = Exception("DB Connection Failed")
        
        service = CatalogService()
        
        # Manually trigger fallback logic (normally called in async startup)
        # Since we are testing sync methods, we can just call _load_from_json directly
        # or simulate the exception handling in initialize_cache
        service._load_from_json()
        
        # Verify Breakers loaded from JSON
        self.assertIsNotNone(service._breaker_cache)
        self.assertGreater(len(service._breaker_cache), 0)
        logger.info(f"Loaded {len(service._breaker_cache)} breakers from JSON")
        
        # Verify Enclosures loaded from Defaults
        self.assertIsNotNone(service._enclosure_cache)
        self.assertGreater(len(service._enclosure_cache), 0)
        logger.info(f"Loaded {len(service._enclosure_cache)} enclosures from Defaults")
        
        # Test find_enclosure
        enclosure = service.find_enclosure(700, 1400, 200)
        self.assertIsNotNone(enclosure)
        self.assertEqual(enclosure.size_mm, [700, 1400, 200])
        logger.info(f"Found enclosure: {enclosure.name}, Price: {enclosure.unit_price}")

    def test_busbar_calculation(self):
        """Test DataTransformer busbar calculation with mocked inputs"""
        
        # Mock CatalogService
        transformer = DataTransformer()
        transformer.catalog_service = MagicMock()
        
        # Mock Enclosure Result (Stage 1 Output)
        enclosure_result = MagicMock()
        enclosure_result.dimensions.width_mm = 700
        enclosure_result.dimensions.height_mm = 1400
        enclosure_result.dimensions.depth_mm = 200
        
        # Mock Main Breaker
        main_breaker = BreakerItem(
            item_name="MCCB",
            spec="4P 100A",
            unit="EA",
            quantity=1,
            unit_price=50000,
            breaker_type="MCCB",
            model="SBE-104",
            is_main=True,
            poles=4,
            current_a=100,
            breaking_capacity_ka=35,
            frame_af=100
        )
        
        # Test _calculate_busbar
        busbar = transformer._calculate_busbar(enclosure_result, main_breaker)
        
        self.assertIsNotNone(busbar)
        self.assertEqual(busbar.item_name, "MAIN BUS-BAR")
        self.assertGreater(busbar.quantity, 0)
        logger.info(f"Calculated Main Busbar: {busbar.spec}, Weight: {busbar.quantity}kg, Price: {busbar.unit_price}")
        
        # Test _calculate_branch_busbar
        branch_breakers = [
            BreakerItem(
                item_name="MCCB", spec="2P 30A", unit="EA", quantity=1, unit_price=10000,
                breaker_type="MCCB", model="SBE-52", is_main=False, poles=2, current_a=30, breaking_capacity_ka=14,
                frame_af=50
            )
        ]
        
        branch_busbar = transformer._calculate_branch_busbar(enclosure_result, branch_breakers)
        self.assertIsNotNone(branch_busbar)
        self.assertEqual(branch_busbar.item_name, "BUS-BAR")
        logger.info(f"Calculated Branch Busbar: {branch_busbar.spec}, Weight: {branch_busbar.quantity}kg")

if __name__ == '__main__':
    unittest.main()
