"""
Tests for export endpoints
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from backend.routers.export_router import router, init_db
import io
import pandas as pd


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()

    # Mock data structure
    sample_data = {
        "country_code": "KE",
        "imported_at": "2024-01-01T00:00:00Z",
        "tariffs": {
            "tariff_lines": [
                {
                    "hs_code": "010110",
                    "description": "Live horses for breeding",
                    "unit": "Number",
                    "customs_duty": "10%",
                    "vat": "16%",
                    "source": "Kenya Revenue Authority"
                },
                {
                    "hs_code": "010120",
                    "description": "Live horses, other than breeding",
                    "unit": "Number",
                    "customs_duty": "25%",
                    "vat": "16%",
                    "source": "Kenya Revenue Authority"
                }
            ]
        },
        "regulations": [
            {"type": "import_license", "description": "Import license required"}
        ],
        "validation": {
            "is_valid": True,
            "score": 95.5,
            "issues": [],
            "warnings": ["Minor data inconsistency"]
        }
    }

    # Create mock collection
    mock_collection = MagicMock()

    # Mock find_one
    async def mock_find_one(*args, **kwargs):
        query = args[0] if args else kwargs.get('filter', {})
        country = query.get('country_code', 'KE')
        data = sample_data.copy()
        data['country_code'] = country
        return data

    mock_collection.find_one = mock_find_one

    # Mock find - return synchronous mock cursor
    class MockCursor:
        def __init__(self, data_list):
            self.data_list = data_list

        def sort(self, *args, **kwargs):
            return self

        async def to_list(self, length=None):
            return self.data_list

    def mock_find(*args, **kwargs):
        query = args[0] if args else {}
        country = query.get('country_code')

        if country:
            # Single country
            data = sample_data.copy()
            data['country_code'] = country
            return MockCursor([data])
        else:
            # Multiple countries
            ke_data = sample_data.copy()
            ke_data['country_code'] = 'KE'
            tz_data = sample_data.copy()
            tz_data['country_code'] = 'TZ'
            return MockCursor([ke_data, tz_data])

    mock_collection.find = mock_find

    # Mock __getitem__ to return the mock collection
    db.__getitem__ = MagicMock(return_value=mock_collection)

    return db


@pytest.fixture
def client_with_mock_db(mock_db):
    """Create test client with mocked database"""
    init_db(mock_db)
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestExportTariffsCSV:
    """Test CSV export endpoint"""

    @pytest.mark.asyncio
    async def test_export_csv_success(self, client_with_mock_db):
        """Test successful CSV export"""
        response = client_with_mock_db.get("/api/export/tariffs/csv?country=KE")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "tariffs_KE" in response.headers["content-disposition"]

        # Check CSV content
        content = response.text
        assert "hs_code" in content
        assert "010110" in content
        assert "Live horses" in content

    @pytest.mark.asyncio
    async def test_export_csv_latest_only(self, client_with_mock_db):
        """Test CSV export with latest=true"""
        response = client_with_mock_db.get("/api/export/tariffs/csv?country=TZ&latest=true")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_csv_missing_country(self, mock_db):
        """Test CSV export with missing country code"""
        # Mock no data found
        async def mock_find_one_none(*args, **kwargs):
            return None

        mock_db["customs_data"].find_one = mock_find_one_none
        init_db(mock_db)

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/api/export/tariffs/csv?country=XX")
        assert response.status_code == 404


class TestExportTariffsExcel:
    """Test Excel export endpoint"""

    @pytest.mark.asyncio
    async def test_export_excel_single_country(self, client_with_mock_db):
        """Test Excel export for single country"""
        response = client_with_mock_db.get("/api/export/tariffs/excel?countries=KE")
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert ".xlsx" in response.headers["content-disposition"]

    @pytest.mark.asyncio
    async def test_export_excel_multiple_countries(self, client_with_mock_db):
        """Test Excel export for multiple countries"""
        response = client_with_mock_db.get("/api/export/tariffs/excel?countries=KE,TZ,UG")
        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_excel_validates_sheets(self, client_with_mock_db):
        """Test that Excel has proper sheets"""
        response = client_with_mock_db.get("/api/export/tariffs/excel?countries=KE")
        assert response.status_code == 200

        # Read Excel to verify structure
        excel_bytes = io.BytesIO(response.content)
        df_dict = pd.read_excel(excel_bytes, sheet_name=None, engine='openpyxl')

        assert "KE" in df_dict
        df = df_dict["KE"]
        assert "HS Code" in df.columns
        assert "Description" in df.columns


class TestValidationReportJSON:
    """Test validation report endpoint"""

    @pytest.mark.asyncio
    async def test_validation_report_all_countries(self, client_with_mock_db):
        """Test validation report for all countries"""
        response = client_with_mock_db.get("/api/export/validation-report/json")
        assert response.status_code == 200

        data = response.json()
        assert "generated_at" in data
        assert "summary" in data
        assert "records" in data
        assert data["summary"]["total_records"] >= 0

    @pytest.mark.asyncio
    async def test_validation_report_single_country(self, client_with_mock_db):
        """Test validation report filtered by country"""
        response = client_with_mock_db.get("/api/export/validation-report/json?country=KE")
        assert response.status_code == 200

        data = response.json()
        assert data["filters"]["country"] == "KE"
        assert "summary" in data

    @pytest.mark.asyncio
    async def test_validation_report_min_score_filter(self, client_with_mock_db):
        """Test validation report with minimum score filter"""
        response = client_with_mock_db.get("/api/export/validation-report/json?min_score=90.0")
        assert response.status_code == 200

        data = response.json()
        assert data["filters"]["min_score"] == 90.0
        # All records should have score >= 90
        for record in data["records"]:
            assert record["validation"]["score"] >= 90.0

    @pytest.mark.asyncio
    async def test_validation_report_structure(self, client_with_mock_db):
        """Test validation report has correct structure"""
        response = client_with_mock_db.get("/api/export/validation-report/json")
        assert response.status_code == 200

        data = response.json()

        # Check summary structure
        assert "total_records" in data["summary"]
        assert "validated_records" in data["summary"]
        assert "failed_validations" in data["summary"]
        assert "average_score" in data["summary"]

        # Check records structure
        if data["records"]:
            record = data["records"][0]
            assert "country_code" in record
            assert "validation" in record
            assert "tariff_count" in record


class TestComparisonCSV:
    """Test tariff comparison endpoint"""

    @pytest.mark.asyncio
    async def test_comparison_two_countries(self, client_with_mock_db):
        """Test comparison between two countries"""
        response = client_with_mock_db.get("/api/export/comparison/csv?countries=KE,TZ")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

        content = response.text
        assert "hs_code" in content
        assert "KE_duty" in content
        assert "TZ_duty" in content

    @pytest.mark.asyncio
    async def test_comparison_multiple_countries(self, client_with_mock_db):
        """Test comparison with more than 2 countries"""
        response = client_with_mock_db.get("/api/export/comparison/csv?countries=KE,TZ,UG,RW")
        assert response.status_code == 200

        content = response.text
        assert "KE_duty" in content
        assert "UG_duty" in content

    @pytest.mark.asyncio
    async def test_comparison_with_hs_filter(self, client_with_mock_db):
        """Test comparison with HS code filter"""
        response = client_with_mock_db.get(
            "/api/export/comparison/csv?countries=KE,TZ&hs_codes=010110,010120"
        )
        assert response.status_code == 200

        content = response.text
        # Should only contain specified HS codes
        lines = content.split('\n')
        assert any("010110" in line for line in lines)

    @pytest.mark.asyncio
    async def test_comparison_requires_min_countries(self, client_with_mock_db):
        """Test that comparison requires at least 2 countries"""
        response = client_with_mock_db.get("/api/export/comparison/csv?countries=KE")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_comparison_filename(self, client_with_mock_db):
        """Test comparison CSV filename format"""
        response = client_with_mock_db.get("/api/export/comparison/csv?countries=KE,TZ")
        assert response.status_code == 200

        filename = response.headers["content-disposition"]
        assert "comparison_KE_TZ" in filename
        assert ".csv" in filename


class TestExportErrorHandling:
    """Test error handling in export endpoints"""

    @pytest.mark.asyncio
    async def test_handles_database_errors(self, mock_db):
        """Test graceful handling of database errors"""
        # Mock database error
        async def mock_error(*args, **kwargs):
            raise Exception("Database connection failed")

        mock_db["customs_data"].find_one = mock_error
        init_db(mock_db)

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/api/export/tariffs/csv?country=KE")
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_handles_missing_parameters(self, client_with_mock_db):
        """Test handling of missing required parameters"""
        # Missing country parameter for CSV
        response = client_with_mock_db.get("/api/export/tariffs/csv")
        assert response.status_code == 422  # Validation error

        # Missing countries parameter for Excel
        response = client_with_mock_db.get("/api/export/tariffs/excel")
        assert response.status_code == 422
