"""
UN COMTRADE Service Tests
=========================
Tests for the UN COMTRADE API service integration.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.comtrade_service import COMTRADEService


class TestCOMTRADEService:
    """Tests for COMTRADE service"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = COMTRADEService()
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        assert self.service.BASE_URL == "https://comtradeapi.un.org/data/v1"
        assert self.service.max_calls_per_day == 500
        assert self.service.calls_today == 0
        assert self.service.last_error is None
    
    @patch('services.comtrade_service.requests.get')
    def test_get_bilateral_trade_success(self, mock_get):
        """Test successful bilateral trade data retrieval"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"reporter": "KEN", "partner": "TZA", "value": 1000000}
            ],
            "metadata": {"recordCount": 1}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Call service
        result = self.service.get_bilateral_trade("KEN", "TZA", "2023")
        
        # Assertions
        assert result is not None
        assert result["source"] == "UN_COMTRADE"
        assert len(result["data"]) == 1
        assert result["data"][0]["reporter"] == "KEN"
        assert result["latest_period"] == "2023"
        assert self.service.calls_today == 1
    
    @patch('services.comtrade_service.requests.get')
    def test_get_bilateral_trade_with_hs_code(self, mock_get):
        """Test bilateral trade with HS code filter"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"hs_code": "080300", "value": 50000}],
            "metadata": {}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = self.service.get_bilateral_trade("KEN", "TZA", "2023", hs_code="080300")
        
        assert result is not None
        assert len(result["data"]) == 1
        
        # Verify HS code was passed in params
        call_args = mock_get.call_args
        assert call_args[1]["params"]["cmdCode"] == "080300"
    
    @patch('services.comtrade_service.requests.get')
    def test_get_bilateral_trade_api_error(self, mock_get):
        """Test handling of API errors"""
        mock_get.side_effect = Exception("API connection failed")
        
        result = self.service.get_bilateral_trade("KEN", "TZA", "2023")
        
        assert result is None
    
    def test_api_rate_limit_enforcement(self):
        """Test that API rate limit is enforced"""
        self.service.calls_today = 500
        
        with pytest.raises(Exception, match="daily limit"):
            self.service.get_bilateral_trade("KEN", "TZA", "2023")
    
    @patch('services.comtrade_service.requests.get')
    def test_get_african_trade_data(self, mock_get):
        """Test fetching trade data for multiple African countries"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"reporter": "KEN", "value": 100000}],
            "metadata": {}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        countries = ["KEN", "GHA", "NGA"]
        results = self.service.get_african_trade_data(countries, "2023")
        
        assert len(results) == 3
        assert all(r["source"] == "UN_COMTRADE" for r in results)
    
    @patch('services.comtrade_service.requests.get')
    def test_get_latest_available_period(self, mock_get):
        """Test finding latest available data period"""
        # Mock successful response for 2024
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"year": "2024", "value": 100000}],
            "metadata": {}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        latest_period = self.service.get_latest_available_period("KEN")
        
        assert latest_period is not None
        # Should return current year or close to it
        assert len(latest_period) == 4  # YYYY format
    
    @patch('services.comtrade_service.requests.get')
    def test_health_check_success(self, mock_get):
        """Test health check with successful connection"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"value": 100000}],
            "metadata": {}
        }
        mock_get.return_value = mock_response
        
        health = self.service.health_check()
        
        assert health is not None
        assert health["connected"] is True
        assert "using_secondary" in health
        assert "calls_today" in health
        assert "rate_limit_remaining" in health
        assert health["last_error"] is None
        assert "timestamp" in health
    
    @patch('services.comtrade_service.requests.get')
    def test_health_check_auth_failure(self, mock_get):
        """Test health check with authentication failure"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        health = self.service.health_check()
        
        assert health is not None
        assert health["connected"] is False
        assert "Authentication failed" in health["last_error"]
    
    @patch('services.comtrade_service.requests.get')
    def test_health_check_rate_limit(self, mock_get):
        """Test health check with rate limit"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        health = self.service.health_check()
        
        assert health is not None
        assert health["connected"] is False
        assert "Rate limit" in health["last_error"]
    
    @patch('services.comtrade_service.requests.get')
    def test_error_tracking(self, mock_get):
        """Test that errors are tracked in last_error"""
        mock_get.side_effect = Exception("Test error")
        
        result = self.service.get_bilateral_trade("KEN", "TZA", "2023")
        
        assert result is None
        assert self.service.last_error == "Test error"
    
    def test_get_service_status(self):
        """Test getting service status"""
        status = self.service.get_service_status()
        
        assert "primary_key_configured" in status
        assert "secondary_key_configured" in status
        assert "current_key" in status
        assert "calls_today" in status
        assert "calls_remaining" in status
        assert "can_switch_to_secondary" in status


class TestCOMTRADEIntegration:
    """Integration tests for COMTRADE API (requires internet)"""
    
    @pytest.mark.skip(reason="Requires internet and API key")
    def test_real_api_call(self):
        """Test actual API call (skipped by default)"""
        service = COMTRADEService()
        result = service.get_bilateral_trade("KEN", "TZA", "2023")
        
        assert result is not None
        assert "data" in result
        assert "metadata" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
