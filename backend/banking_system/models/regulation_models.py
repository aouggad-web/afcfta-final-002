"""
Pydantic models for foreign-exchange regulations and domiciliation
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class DomiciliationRule(BaseModel):
    """Règle de domiciliation bancaire pour une opération d'import/export"""
    required: bool = Field(..., description="Domiciliation obligatoire (true/false)")
    conditional: bool = Field(default=False, description="Domiciliation conditionnelle")
    threshold_usd: Optional[float] = Field(
        default=None, description="Seuil (USD) déclenchant l'obligation"
    )
    mandatory_documents: List[str] = Field(
        default_factory=list,
        description="Documents obligatoires pour la domiciliation",
    )
    timeline_days: Optional[int] = Field(
        default=None,
        description="Délai réglementaire de rapatriement des fonds (jours)",
    )
    notes: Optional[str] = None


class ForexRegulation(BaseModel):
    """Réglementation de change pour un pays"""
    regulation_level: str = Field(
        ...,
        description="Niveau: strict | moderate | liberal",
    )
    prior_authorization_required: bool = False
    authorization_threshold_usd: Optional[float] = None
    declaration_threshold_usd: Optional[float] = None
    repatriation_deadline_days: Optional[int] = None
    penalties: Optional[str] = None
    notes: Optional[str] = None


class CountryForexProfile(BaseModel):
    """Profil complet de réglementation des changes pour un pays"""
    country_code: str
    country_name: str
    central_bank_name: str
    domiciliation: DomiciliationRule
    forex_regulation: ForexRegulation
    authorized_currencies: List[str] = Field(default_factory=list)
    restricted_operations: List[str] = Field(default_factory=list)
    special_regimes: List[str] = Field(default_factory=list)
