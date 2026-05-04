"""
Data Source Selector Tests
===========================
Tests for the smart data source selector service.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.data_source_selector import DataSourceSelector


class TestDataSourceSelector:
    """Tests for data source selector"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.selector = DataSourceSelector()
    
    def test_selector_initialization(self):
        """Test selector initializes correctly"""
        assert self.selector.wto is not None
    
    @patch('services.data_source_selector.wto_service.get_tariff_data')
    def test_get_latest_trade_data_wto_success(self, mock_wto):
        """Test that WTO is used when available"""
        mock_wto.return_value = {
            "source": "WTO",
            "data": {"tariff": 5.5},
            "latest_period": "2023"
        }
        
        result = self.selector.get_latest_trade_data("KEN", "TZA")
        
        assert result["source_used"] == "WTO"
        assert result["data_period"] == "2023"
        assert len(result["sources_checked"]) >= 1
    
    @patch('services.data_source_selector.wto_service.get_tariff_data')
    def test_get_latest_trade_data_no_sources_available(self, mock_wto):
        """Test when no data sources are available"""
        mock_wto.return_value = None
        
        result = self.selector.get_latest_trade_data("KEN", "TZA")
        
        assert result["source_used"] is None
        assert result["data"] is None
    
    @patch('services.data_source_selector.wto_service.get_tariff_data')
    def test_get_latest_trade_data_with_hs_code(self, mock_wto):
        """Test data retrieval with HS code"""
        mock_wto.return_value = {
            "source": "WTO",
            "data": {"hs_code": "080300", "tariff": 5.5},
            "latest_period": "2023"
        }
        
        result = self.selector.get_latest_trade_data("KEN", "TZA", hs_code="080300")
        
        assert result["hs_code"] == "080300"
    
    @patch('services.data_source_selector.wto_service.get_tariff_data')
    def test_get_latest_trade_data_handles_exceptions(self, mock_wto):
        """Test that exceptions are handled gracefully"""
        mock_wto.side_effect = Exception("Network error")
        
        result = self.selector.get_latest_trade_data("KEN", "TZA")
        
        # Should not raise exception
        assert result is not None
        assert result["source_used"] is None
    
    @patch('services.data_source_selector.wto_service.get_latest_available_year')
    def test_compare_data_sources(self, mock_wto_year):
        """Test data source comparison"""
        mock_wto_year.return_value = "2023"
        
        countries = ["KEN", "GHA", "TZA"]
        result = self.selector.compare_data_sources(countries)
        
        assert "timestamp" in result
        assert "countries_checked" in result
        assert "sources" in result
        assert "WTO" in result["sources"]
    
    def test_compare_data_sources_limits_checks(self):
        """Test that comparison limits the number of countries checked"""
        countries = ["KEN", "GHA", "TZA", "NGA", "EGY", "ZAF", "MAR"]
        
        with patch.object(self.selector.wto, 'get_latest_available_year') as mock:
            mock.return_value = "2023"
            result = self.selector.compare_data_sources(countries)
            
            # Should only check first 5 countries
            assert mock.call_count <= 5


class TestDataSourceSelectorIntegration:
    """Integration tests for data source selector"""
    
    @pytest.mark.skip(reason="Requires internet and API access")
    def test_real_data_source_selection(self):
        """Test actual data source selection (skipped by default)"""
        selector = DataSourceSelector()
        result = selector.get_latest_trade_data("KEN", "TZA")
        
        assert result is not None
        assert "sources_checked" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
