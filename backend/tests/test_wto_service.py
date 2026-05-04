"""
WTO Service Tests
=================
Tests for the WTO Data Portal API service integration.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.wto_service import WTOService


class TestWTOService:
    """Tests for WTO service"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = WTOService()
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        assert self.service.BASE_URL == "https://api.wto.org/timeseries/v1"
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_tariff_data_success(self, mock_retry):
        """Test successful tariff data retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "Dataset": {
                "Series": [
                    {
                        "Obs": [
                            {"Time": "2023", "Value": 5.5}
                        ]
                    }
                ]
            }
        }
        mock_retry.return_value = mock_response
        
        # Call service
        result = self.service.get_tariff_data("KEN", "wld")
        
        # Assertions
        assert result is not None
        assert result["source"] == "WTO"
        assert result["latest_period"] == "2023"
        assert "data" in result
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_tariff_data_with_product_code(self, mock_retry):
        """Test tariff data with product code filter"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Dataset": {
                "Series": [
                    {
                        "Obs": [{"Time": "2023", "Value": 10.0}]
                    }
                ]
            }
        }
        mock_retry.return_value = mock_response
        
        result = self.service.get_tariff_data("KEN", "wld", product_code="080300")
        
        assert result is not None
        
        # Verify product code was passed in params
        call_args = mock_retry.call_args
        assert call_args[1]["params"]["pc"] == "080300"
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_tariff_data_api_error(self, mock_retry):
        """Test handling of API errors"""
        mock_retry.side_effect = Exception("API connection failed")
        
        result = self.service.get_tariff_data("KEN", "wld")
        
        assert result is None
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_tariff_data_no_observations(self, mock_retry):
        """Test handling of response with no observations"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Dataset": {
                "Series": []
            }
        }
        mock_retry.return_value = mock_response
        
        result = self.service.get_tariff_data("KEN", "wld")
        
        assert result is not None
        assert result["latest_period"] is None
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_trade_indicators_success(self, mock_retry):
        """Test successful trade indicators retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Dataset": {
                "Indicator": "TRADE_VALUE",
                "Series": [{"Value": 1000000}]
            }
        }
        mock_retry.return_value = mock_response
        
        result = self.service.get_trade_indicators("KEN", "TRADE_VALUE")
        
        assert result is not None
        assert result["source"] == "WTO"
        assert result["indicator"] == "TRADE_VALUE"
        assert "data" in result
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_trade_indicators_api_error(self, mock_retry):
        """Test handling of API errors for trade indicators"""
        mock_retry.side_effect = Exception("Network error")
        
        result = self.service.get_trade_indicators("KEN")
        
        assert result is None
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_latest_available_year(self, mock_retry):
        """Test getting latest available year"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "Dataset": {
                "Series": [
                    {
                        "Obs": [
                            {"Time": "2021", "Value": 5.0},
                            {"Time": "2022", "Value": 5.2},
                            {"Time": "2023", "Value": 5.5}
                        ]
                    }
                ]
            }
        }
        mock_retry.return_value = mock_response
        
        latest_year = self.service.get_latest_available_year("KEN")
        
        assert latest_year == "2023"
    
    @patch('services.wto_service.make_wto_request_with_retry')
    def test_get_tariff_data_retry_returns_none(self, mock_retry):
        """Test handling when retry function returns None"""
        mock_retry.return_value = None
        
        result = self.service.get_tariff_data("KEN", "wld")
        
        assert result is None


class TestWTOIntegration:
    """Integration tests for WTO API (requires internet)"""
    
    @pytest.mark.skip(reason="Requires internet connection")
    def test_real_api_call(self):
        """Test actual API call (skipped by default)"""
        service = WTOService()
        result = service.get_tariff_data("USA", "wld")
        
        assert result is not None
        assert "data" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
