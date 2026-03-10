"""
Pydantic models for trade finance instruments, payment systems and risk assessment
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class TradeFinanceInstrument(BaseModel):
    """Instrument de financement du commerce"""
    code: str = Field(..., description="Code interne de l'instrument")
    name: str
    name_fr: str
    description: str
    applicable_to: List[str] = Field(
        default_factory=list,
        description="import | export",
    )
    typical_cost_pct: Optional[float] = Field(
        default=None, description="Coût typique en % du montant"
    )
    typical_duration_days: Optional[int] = None
    risk_coverage: str = Field(
        default="partial",
        description="Niveau de couverture du risque: full | partial | none",
    )
    requirements: List[str] = Field(default_factory=list)


class PaymentSystem(BaseModel):
    """Système de paiement régional ou international"""
    code: str
    name: str
    type: str = Field(
        ...,
        description="Type: swift | regional | mobile_money | digital",
    )
    region: str
    member_countries: List[str] = Field(default_factory=list)
    currency: Optional[str] = None
    operator: Optional[str] = None
    notes: Optional[str] = None


class CountryRiskProfile(BaseModel):
    """Profil de risque pays pour les opérations de commerce extérieur"""
    country_code: str
    country_name: str
    country_risk_rating: str = Field(
        ...,
        description="Notation risque pays: A1..A4, B, C, D",
    )
    forex_risk: str = Field(
        ...,
        description="Risque de change: low | moderate | high | very_high",
    )
    political_risk: str = Field(
        ...,
        description="Risque politique: low | moderate | high | very_high",
    )
    transfer_risk: str = Field(
        ...,
        description="Risque de transfert: low | moderate | high | very_high",
    )
    recommended_instruments: List[str] = Field(
        default_factory=list,
        description="Instruments financiers recommandés pour ce pays",
    )
    credit_insurance_available: bool = True
    max_exposure_usd: Optional[float] = Field(
        default=None, description="Limite d'exposition bancaire recommandée (USD)"
    )
    notes: Optional[str] = None
