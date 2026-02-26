"""
Pydantic models for ZLECAf API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class CountryInfo(BaseModel):
    """Country information model"""
    code: str  # ISO3 (code principal)
    iso2: str = ""  # ISO2 (pour les drapeaux)
    iso3: str  # ISO3 
    name: str
    region: str
    wb_code: str
    population: int


class TariffCalculationRequest(BaseModel):
    """Request model for tariff calculation"""
    origin_country: str
    destination_country: str
    hs_code: str
    value: float


class TariffCalculationResponse(BaseModel):
    """Response model for tariff calculation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    origin_country: str
    destination_country: str
    hs_code: str
    hs6_code: Optional[str] = None  # Code SH6 extrait
    value: float
    # Tarifs normaux (hors ZLECAf)
    normal_tariff_rate: float
    normal_tariff_amount: float
    # Tarifs ZLECAf
    zlecaf_tariff_rate: float
    zlecaf_tariff_amount: float
    # TVA et autres taxes - Normal
    normal_vat_rate: float
    normal_vat_amount: float
    normal_statistical_fee: float
    normal_community_levy: float
    normal_ecowas_levy: float
    normal_other_taxes_total: float
    normal_total_cost: float
    # TVA et autres taxes - ZLECAf
    zlecaf_vat_rate: float
    zlecaf_vat_amount: float
    zlecaf_statistical_fee: float
    zlecaf_community_levy: float
    zlecaf_ecowas_levy: float
    zlecaf_other_taxes_total: float
    zlecaf_total_cost: float
    # Économies
    savings: float
    savings_percentage: float
    total_savings_with_taxes: float
    total_savings_percentage: float
    # Journal de calcul et traçabilité
    normal_calculation_journal: List[Dict[str, Any]]
    zlecaf_calculation_journal: List[Dict[str, Any]]
    computation_order_ref: str
    last_verified: str
    confidence_level: str
    # Précision tarifaire et sous-positions nationales
    tariff_precision: str = "chapter"  # sub_position, hs6_country, chapter
    sub_position_used: Optional[str] = None  # Code 8-12 chiffres si utilisé
    sub_position_description: Optional[str] = None
    has_varying_sub_positions: bool = False  # Si d'autres taux existent pour ce HS6
    available_sub_positions_count: int = 0
    # WARNING: Taux variables selon sous-positions
    rate_warning: Optional[Dict[str, Any]] = None
    sub_positions_details: Optional[List[Dict[str, Any]]] = None
    # Taxes détaillées par produit (format enrichi)
    taxes_detail: Optional[List[Dict[str, Any]]] = None
    fiscal_advantages: Optional[List[Dict[str, Any]]] = None
    administrative_formalities: Optional[List[Dict[str, Any]]] = None
    data_source: Optional[str] = None
    # Règles d'origine
    rules_of_origin: Dict[str, Any]
    # Top producteurs africains
    top_african_producers: List[Dict[str, Any]]
    # Données économiques des pays
    origin_country_data: Dict[str, Any]
    destination_country_data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


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
                "fetched_at": "2026-02-01T10:00:00"
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
                "details": {}
            }
        }
