"""
Pydantic models for ZLECAf API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CountryInfo(BaseModel):
    """Country information model"""

    code: str  # ISO3 (code principal)
    iso2: str = ""  # ISO2 (pour les drapeaux)
    iso3: str  # ISO3
    name: str
    region: str
    wb_code: str
    population: int


class CountryEconomicProfile(BaseModel):
    """Economic profile for a country"""

    country_code: str
    country_name: str
    population: Optional[int] = None
    population_millions: Optional[float] = None
    gdp_usd: Optional[float] = None
    gdp_per_capita: Optional[float] = None
    inflation_rate: Optional[float] = None
    unemployment_rate: Optional[float] = None
    hdi: Optional[float] = None
    hdi_rank: Optional[int] = None
    # Données de dette publique
    total_debt_pct_gdp: Optional[float] = None
    external_debt_bn_usd: Optional[float] = None
    external_debt_pct_gdp: Optional[float] = None
    domestic_debt_pct_gdp: Optional[float] = None
    region: str
    trade_profile: Dict[str, Any] = {}
    projections: Dict[str, Any] = {}
    risk_ratings: Dict[str, Any] = {}
    customs: Dict[str, Any] = {}
    infrastructure_ranking: Dict[str, Any] = {}
    ongoing_projects: List[Dict[str, Any]] = []


class TradeDataSource(BaseModel):
    """Model for trade data from various sources"""

    source: str = Field(..., description="Data source name (WTO, OEC, etc.)")
    reporter_country: str = Field(..., description="ISO3 reporter country code")
    partner_country: str = Field(..., description="ISO3 partner country code")
    hs_code: Optional[str] = Field(None, description="HS product code")
    period: str = Field(..., description="Data period (YYYY or YYYYMM)")
    trade_value: Optional[float] = Field(None, description="Trade value in USD")
    trade_flow: Optional[str] = Field(None, description="Import or Export")
    data: Dict = Field(..., description="Raw data from source")
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "source": "OEC",
                "reporter_country": "KEN",
                "partner_country": "GHA",
                "hs_code": "080300",
                "period": "2025",
                "trade_value": 1500000.50,
                "trade_flow": "Export",
                "data": {},
                "fetched_at": "2026-02-01T10:00:00",
            }
        }


class DataSourceComparison(BaseModel):
    """Model for data source comparison results"""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources_compared: List[str]
    recommended_source: str
    details: Dict

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-01T10:00:00",
                "sources_compared": ["WTO", "OEC"],
                "recommended_source": "OEC",
                "details": {},
            }
        }
