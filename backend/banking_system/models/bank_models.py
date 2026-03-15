"""
Pydantic models for African banks
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class CentralBank(BaseModel):
    """Modèle d'une banque centrale africaine"""
    country_code: str = Field(..., description="Code ISO2 du pays")
    country_name: str
    name: str = Field(..., description="Nom de la banque centrale")
    abbreviation: str = Field(..., description="Sigle / abréviation")
    website: Optional[str] = None
    swift_code: Optional[str] = None
    forex_regulation: str = Field(
        default="moderate",
        description="Niveau de réglementation: strict | moderate | liberal",
    )
    currency_code: str = Field(..., description="Code ISO 4217 de la devise")
    currency_name: str


class CommercialBank(BaseModel):
    """Banque commerciale autorisée au commerce extérieur"""
    name: str
    abbreviation: Optional[str] = None
    country_code: str
    swift_code: Optional[str] = None
    trade_finance: bool = False
    correspondent_banks: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)


class RegionalBank(BaseModel):
    """Banque régionale ou de développement africaine"""
    name: str
    abbreviation: str
    region: str
    headquarters: str
    website: Optional[str] = None
    member_countries: List[str] = Field(default_factory=list)
    focus_areas: List[str] = Field(default_factory=list)


class BankingSystemInfo(BaseModel):
    """Informations bancaires complètes pour un pays"""
    country_code: str
    country_name: str
    central_bank: CentralBank
    commercial_banks: List[CommercialBank] = Field(default_factory=list)
    regional_banks: List[RegionalBank] = Field(default_factory=list)
