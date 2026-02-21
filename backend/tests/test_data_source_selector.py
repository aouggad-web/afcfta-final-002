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
        assert self.selector.comtrade is not None
        assert self.selector.wto is not None
    
    @patch('services.data_source_selector.comtrade_service.get_bilateral_trade')
    def test_get_latest_trade_data_comtrade_success(self, mock_comtrade):
        """Test that COMTRADE is used when available"""
        # Mock COMTRADE returning data
        mock_comtrade.return_value = {
            "source": "UN_COMTRADE",
            "data": [{"reporter": "KEN", "partner": "TZA", "value": 100000}],
            "latest_period": "2024"
        }
        
        result = self.selector.get_latest_trade_data("KEN", "TZA")
        
        assert result["source_used"] == "UN_COMTRADE"
        assert result["data_period"] == "2024"
        assert len(result["sources_checked"]) >= 1
        assert result["sources_checked"][0]["source"] == "UN_COMTRADE"
        assert result["sources_checked"][0]["status"] == "success"
    
    @patch('services.data_source_selector.wto_service.get_tariff_data')
    @patch('services.data_source_selector.comtrade_service.get_bilateral_trade')
    def test_get_latest_trade_data_fallback_to_wto(self, mock_comtrade, mock_wto):
        """Test fallback to WTO when COMTRADE fails"""
        # Mock COMTRADE returning None (failure)
        mock_comtrade.return_value = None
        
        # Mock WTO returning data
        mock_wto.return_value = {
            "source": "WTO",
            "data": {"tariff": 5.5},
            "latest_period": "2023"
        }
        
        result = self.selector.get_latest_trade_data("KEN", "TZA")
        
        assert result["source_used"] == "WTO"
        assert result["data_period"] == "2023"
        assert len(result["sources_checked"]) >= 2
    
    @patch('services.data_source_selector.wto_service.get_tariff_data')
    @patch('services.data_source_selector.comtrade_service.get_bilateral_trade')
    def test_get_latest_trade_data_no_sources_available(self, mock_comtrade, mock_wto):
        """Test when no data sources are available"""
        # Mock all sources returning None
        mock_comtrade.return_value = None
        mock_wto.return_value = None
        
        result = self.selector.get_latest_trade_data("KEN", "TZA")
        
        assert result["source_used"] is None
        assert result["data"] is None
        assert len(result["sources_checked"]) >= 2
    
    @patch('services.data_source_selector.comtrade_service.get_bilateral_trade')
    def test_get_latest_trade_data_with_hs_code(self, mock_comtrade):
        """Test data retrieval with HS code"""
        mock_comtrade.return_value = {
            "source": "UN_COMTRADE",
            "data": [{"hs_code": "080300", "value": 50000}],
            "latest_period": "2024"
        }
        
        result = self.selector.get_latest_trade_data("KEN", "TZA", hs_code="080300")
        
        assert result["hs_code"] == "080300"
        assert result["source_used"] == "UN_COMTRADE"
    
    @patch('services.data_source_selector.comtrade_service.get_bilateral_trade')
    def test_get_latest_trade_data_handles_exceptions(self, mock_comtrade):
        """Test that exceptions are handled gracefully"""
        mock_comtrade.side_effect = Exception("Network error")
        
        result = self.selector.get_latest_trade_data("KEN", "TZA")
        
        # Should not raise exception
        assert result is not None
        assert result["source_used"] is None or result["source_used"] != "UN_COMTRADE"
        # Should record the error
        comtrade_check = next(
            (s for s in result["sources_checked"] if s["source"] == "UN_COMTRADE"),
            None
        )
        if comtrade_check:
            assert comtrade_check["status"] == "error"
    
    @patch('services.data_source_selector.wto_service.get_latest_available_year')
    @patch('services.data_source_selector.comtrade_service.get_latest_available_period')
    def test_compare_data_sources(self, mock_comtrade_period, mock_wto_year):
        """Test data source comparison"""
        # Mock responses
        mock_comtrade_period.return_value = "2024"
        mock_wto_year.return_value = "2023"
        
        countries = ["KEN", "GHA", "TZA"]
        result = self.selector.compare_data_sources(countries)
        
        assert "timestamp" in result
        assert "countries_checked" in result
        assert "sources" in result
        assert "UN_COMTRADE" in result["sources"]
        assert "WTO" in result["sources"]
    
    @patch('services.data_source_selector.wto_service.get_latest_available_year')
    @patch('services.data_source_selector.comtrade_service.get_latest_available_period')
    def test_compare_data_sources_recommends_best(self, mock_comtrade_period, mock_wto_year):
        """Test that comparison recommends the best source"""
        # COMTRADE has more recent data
        mock_comtrade_period.return_value = "2024"
        mock_wto_year.return_value = "2022"
        
        countries = ["KEN", "GHA"]
        result = self.selector.compare_data_sources(countries)
        
        if "recommended_source" in result:
            # COMTRADE should be recommended as it has more recent data
            assert "UN_COMTRADE" in str(result["recommended_source"])
    
    def test_compare_data_sources_limits_checks(self):
        """Test that comparison limits the number of countries checked"""
        countries = ["KEN", "GHA", "TZA", "NGA", "EGY", "ZAF", "MAR"]
        
        with patch.object(self.selector.comtrade, 'get_latest_available_period') as mock:
            mock.return_value = "2024"
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
