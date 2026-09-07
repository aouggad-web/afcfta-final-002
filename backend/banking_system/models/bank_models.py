"""
Pydantic models for African banks
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class BankContact(BaseModel):
    """Contact information for a bank"""

    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    contact_person: Optional[str] = None
    department: Optional[str] = None


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
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    established_year: Optional[int] = None
    banking_act: Optional[str] = None
    contact: Optional[BankContact] = None
    # ── Champs enrichis ───────────────────────────────────────────────────
    imf_article_status: Optional[str] = Field(
        default=None,
        description=(
            "Statut FMI : 'Article VIII' (compte courant libéré) ou "
            "'Article XIV' (régime transitoire)"
        ),
    )
    total_assets_usd_bn: Optional[float] = Field(
        default=None,
        description="Total des actifs de la banque centrale (milliards USD, dernière publication)",
    )


class CommercialBank(BaseModel):
    """Banque commerciale autorisée au commerce extérieur"""

    name: str
    abbreviation: Optional[str] = None
    country_code: str
    swift_code: Optional[str] = None
    trade_finance: bool = False
    correspondent_banks: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    website: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_type: Optional[str] = None
    contact: Optional[BankContact] = None


class RegionalBank(BaseModel):
    """Banque régionale ou de développement africaine"""

    name: str
    abbreviation: str
    region: str
    headquarters: str
    website: Optional[str] = None
    member_countries: List[str] = Field(default_factory=list)
    focus_areas: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[BankContact] = None


class BankingSystemInfo(BaseModel):
    """Informations bancaires complètes pour un pays"""

    country_code: str
    country_name: str
    central_bank: CentralBank
    commercial_banks: List[CommercialBank] = Field(default_factory=list)
    regional_banks: List[RegionalBank] = Field(default_factory=list)
