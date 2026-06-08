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
    # ── Données authentiques de réglementation ────────────────────────────
    legal_reference: Optional[str] = Field(
        default=None,
        description="Référence légale / texte réglementaire principal (loi, ordonnance, circulaire)",
    )
    regulatory_body: Optional[str] = Field(
        default=None,
        description="Autorité de contrôle des changes (organisme responsable de l'application)",
    )
    imf_article_status: Optional[str] = Field(
        default=None,
        description=(
            "Statut d'acceptation des obligations FMI : "
            "'Article VIII' (convertibilité compte courant acceptée) ou "
            "'Article XIV' (régime transitoire – restrictions maintenues)"
        ),
    )


class ExchangeRateInfo(BaseModel):
    """Informations sur le taux de change d'une devise locale par rapport au USD"""
    currency_code: str = Field(..., description="Code ISO 4217 de la devise locale")
    currency_name: str = Field(..., description="Nom de la devise locale")
    rate_usd: Optional[float] = Field(
        default=None,
        description="Taux de change : 1 USD = X unités de monnaie locale (source live)",
    )
    rate_eur: Optional[float] = Field(
        default=None,
        description="Taux de change : 1 EUR = X unités de monnaie locale (source live)",
    )
    rate_source: Optional[str] = Field(
        default=None,
        description="Source du taux de change (ex: frankfurter, currencyfreaks)",
    )
    rate_timestamp: Optional[str] = Field(
        default=None,
        description="Horodatage UTC du taux de change (ISO 8601)",
    )
    convertibility: Optional[str] = Field(
        default=None,
        description="Convertibilité : freely_convertible | partially_convertible | non_convertible",
    )


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
    # ── Données monétaires ────────────────────────────────────────────────
    currency_code: Optional[str] = Field(
        default=None, description="Code ISO 4217 de la devise nationale"
    )
    currency_name: Optional[str] = Field(
        default=None, description="Nom complet de la devise nationale"
    )
    exchange_rate_info: Optional[ExchangeRateInfo] = Field(
        default=None,
        description=(
            "Informations de taux de change en temps réel – "
            "enrichi dynamiquement via le service de change"
        ),
    )
