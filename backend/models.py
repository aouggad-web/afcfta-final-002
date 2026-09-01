"""
Pydantic models for ZLECAf API
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Closed vocabularies for documentary quality.
QUALITY_DIMENSION_KEYS = (
    "source",
    "temporal_validity",
    "classification",
    "taxes_and_levies",
    "preference_and_origin",
    "formalities",
)
QUALITY_DIMENSION_VALUES = frozenset(
    {"DOCUMENTED", "PARTIAL", "UNVERIFIED", "NOT_AVAILABLE", "NOT_APPLICABLE"}
)
OVERALL_STATUS_ALIASES = {
    "BLOCKED_BASE_TARIFF": "CALCULATION_UNAVAILABLE",
    "UNVERIFIED_SOURCE": "REVIEW_REQUIRED",
    "CONFLICT_REVIEW": "REVIEW_REQUIRED",
    "VERIFIED_COMPLETE": "INFORMATIVE_COMPLETE",
    "VERIFIED_PARTIAL": "INFORMATIVE_PARTIAL",
}
OVERALL_STATUS_VALUES = frozenset(
    {"INFORMATIVE_COMPLETE", "INFORMATIVE_PARTIAL", "CALCULATION_UNAVAILABLE", "REVIEW_REQUIRED"}
)


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

    origin_country: str = Field(
        ..., description="ISO2 or ISO3 country code for origin", min_length=2, max_length=3
    )
    destination_country: str = Field(
        ..., description="ISO2 or ISO3 country code for destination", min_length=2, max_length=3
    )
    hs_code: str = Field(..., description="HS code (2-12 digits)", min_length=2, max_length=12)
    value: float = Field(..., description="Customs value in USD", gt=0)

    @field_validator("origin_country", "destination_country")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{2,3}$", v):
            raise ValueError("Country code must be 2-3 uppercase letters")
        return v

    @field_validator("hs_code")
    @classmethod
    def validate_hs_code(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{2,12}$", v):
            raise ValueError("HS code must contain 2-12 digits only")
        return v


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
    # Tarifs ZLECAf (None si aucune préférence vérifiée disponible)
    zlecaf_tariff_rate: Optional[float] = None
    zlecaf_tariff_amount: Optional[float] = None
    # TVA et autres taxes - Normal
    normal_vat_rate: Optional[float] = None
    normal_vat_amount: Optional[float] = None
    normal_statistical_fee: float
    normal_community_levy: float
    normal_ecowas_levy: float
    normal_other_taxes_total: float
    normal_total_cost: float
    # TVA et autres taxes - ZLECAf
    zlecaf_vat_rate: Optional[float] = None
    zlecaf_vat_amount: Optional[float] = None
    zlecaf_statistical_fee: float
    zlecaf_community_levy: float
    zlecaf_ecowas_levy: float
    zlecaf_other_taxes_total: float
    zlecaf_total_cost: float
    # Économies (None si aucune préférence ZLECAf traçable : un 0 numérique
    # affirmerait à tort qu'un calcul préférentiel a été effectué)
    savings: Optional[float] = None
    savings_percentage: Optional[float] = None
    total_savings_with_taxes: Optional[float] = None
    total_savings_percentage: Optional[float] = None
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
    # ── Champs de statut d'honnêteté (additifs, ne cassent pas le contrat) ──
    # Statut du droit de douane servi :
    #   PAYABLE        → droit exigible issu d'une position tarifaire.
    #   INDICATIVE_MFN → agrégat WITS/UNCTAD-TRAINS (moyenne MFN SH6, niveau 3) :
    #                    information seulement, JAMAIS un droit exigible ni une
    #                    base d'économie ZLECAf.
    #   UNAVAILABLE    → aucun droit de douane trouvé dans la source officielle ;
    #                    la valeur 0 affichée n'est PAS un taux vérifié (absence
    #                    de donnée, pas un 0 % réel).
    duty_status: str = "PAYABLE"
    duty_notice: Optional[str] = None
    dd_available: bool = True  # False = droit absent de la source (≠ 0 % vérifié)
    # Régime commercial préférentiel effectivement appliqué, résolu par le
    # garde-fou central (services.authentic_tariff_service.resolve_zlecaf_context) :
    # CUSTOMS_UNION | ZLECAF | FTA_CONDITIONAL | NPF.
    trade_regime: Optional[str] = None
    trade_regime_code: Optional[str] = None  # SACU, UEMOA, ECOWAS, ZLECAF…
    zlecaf_preference_applied: bool = False  # une préférence réduit-elle le droit ?
    zlecaf_note: Optional[str] = None
    # Statut de la préférence ZLECAf elle-même (distinct de duty_status, qui
    # porte sur le droit NPF) :
    #   DOCUMENTED             → taux préférentiel résolu à partir d'une source
    #                             tracée et datée (union douanière, calendrier
    #                             DZA/ZAF, taux réel de ligne + preuve
    #                             d'application).
    #   OFFER_ONLY              → une offre tarifaire officielle est archivée
    #                             pour cette destination mais aucune preuve
    #                             nationale d'application/réciprocité n'a été
    #                             vérifiée.
    #   PARTNER_NOTICE_REQUIRED → domestication en vigueur, mais la liste
    #                             officielle des partenaires réciproques n'a
    #                             pas été publiée.
    #   NOT_AVAILABLE          → aucune préférence traçable : zlecaf_tariff_rate=null,
    #                             zlecaf_tariff_amount=null, savings=null.
    # OFFER_ONLY et PARTNER_NOTICE_REQUIRED ne sont jamais calculés (comme
    # NOT_AVAILABLE), mais restent distincts pour l'affichage : le frontend
    # les présente comme « à vérifier avec les douanes locales » plutôt que
    # comme une absence pure de source.
    zlecaf_status: str = "NOT_AVAILABLE"
    # Taux publié au e-Tariff Book officiel de la ZLECAf pour cette ligne, mais
    # NON vérifié comme légalement applicable (zlecaf_status OFFER_ONLY ou
    # PARTNER_NOTICE_REQUIRED). STRICTEMENT informatif : il n'entre dans aucun
    # calcul — zlecaf_tariff_rate, les totaux et les économies restent ceux du
    # régime NPF. Affiché « à vérifier avec les douanes locales ».
    zlecaf_offer_rate_pct: Optional[float] = None
    zlecaf_offer_rate_expression: Optional[str] = None
    zlecaf_offer_rate_source: Optional[Dict[str, Any]] = None
    has_varying_sub_positions: bool = False  # Si d'autres taux existent pour ce HS6
    available_sub_positions_count: int = 0
    # WARNING: Taux variables selon sous-positions
    rate_warning: Optional[Dict[str, Any]] = None
    sub_positions_details: Optional[List[Dict[str, Any]]] = None
    # Taxes détaillées par produit (format enrichi)
    taxes_detail: Optional[List[Dict[str, Any]]] = None
    # Ventilation complète NPF vs ZLECAf, taxe par taxe, calculée sur la base
    # (assiette) déclarée propre à chaque pays. Chaque entrée : code, name,
    # category (droit_douane|tva|autre_taxe), base_expr, rate_npf_pct,
    # rate_zlecaf_pct, base_value_npf, base_value_zlecaf, amount_npf,
    # amount_zlecaf, affected_by_zlecaf, source.
    taxes_breakdown: Optional[List[Dict[str, Any]]] = None
    # Récapitulatif par régime : {npf:{droit_douane, autres_taxes, tva,
    # total_taxes_et_droits, cout_total}, zlecaf:{...}, economie_droits,
    # economie_totale}.
    taxes_summary: Optional[Dict[str, Any]] = None
    # Conversion bi-devise (USD <-> monnaie locale du pays de destination) via le
    # sous-module de change. {local_code, local_name, local_symbol,
    # usd_to_local_rate, rate_source, rate_as_of, available, value_usd,
    # value_local, summary_local{npf,zlecaf,...}}. Quand le taux est indisponible,
    # available=False et les montants restent en USD (taxes_breakdown porte aussi
    # amount_*_local quand disponible).
    currency: Optional[Dict[str, Any]] = None
    fiscal_advantages: Optional[List[Dict[str, Any]]] = None
    administrative_formalities: Optional[List[Dict[str, Any]]] = None
    # Formalités d'importation et prestataires/mandataires du pays de destination
    # (source : services.regulatory_compliance_service — registre fail-closed,
    # sourcé et daté). Bloc STRICTEMENT SÉPARÉ des droits et taxes : il n'entre
    # JAMAIS dans normal_total_cost / zlecaf_total_cost / taxes_summary. Les
    # frais autorisés des prestataires y figurent à titre informatif — chiffrés
    # + sourcés lorsque prouvés, sinon NOT_AVAILABLE — et ne sont jamais additionnés
    # au coût douanier (nature distincte : coût opérationnel privé ≠ droit exigible).
    # None quand le pays de destination n'a pas encore de registre conforme.
    regulatory_compliance: Optional[Dict[str, Any]] = None
    # Ventilation calculée des frais de formalité et de prestataire mandaté
    # (services.regulatory_fee_service), pour le pays d'import ET/OU d'export dès
    # qu'un prestataire mandaté ACTIF est confirmé. Chaque ligne porte un statut
    # canonique (CALCULABLE, DOCUMENTED_FIXED_AMOUNT, DOCUMENTED_PERCENTAGE,
    # FEE_EXISTS_AMOUNT_NOT_AVAILABLE, PARTIAL, NOT_AVAILABLE, NOT_APPLICABLE).
    # Les frais du prestataire (perçu privé) sont rangés séparément des frais de
    # formalité (perçu public) et TOUS restent distincts des droits et taxes.
    # `complete=False` signale un coût total encore partiel ; un montant inconnu
    # reste None (jamais 0). None quand aucun prestataire actif n'est confirmé.
    regulatory_cost: Optional[Dict[str, Any]] = None
    # Couche « indications secondaires » (services.regulatory_reported_service) :
    # prestataires et frais REPORTÉS par une synthèse secondaire non vérifiée, pour
    # les pays pas encore couverts par le registre conforme. Purement informatif,
    # étiqueté « à confirmer », JAMAIS sommé à un total ni marqué CALCULABLE, jamais
    # présenté comme officiel. Strictement distinct de regulatory_compliance/cost.
    regulatory_reported: Optional[Dict[str, Any]] = None
    # Couverture tarifaire, fiscale, documentaire et réglementaire traçable.
    # Les lacunes restent explicitement NOT_AVAILABLE ; aucune valeur de
    # remplacement n'est générée par ce bloc.
    country_enrichment: Optional[Dict[str, Any]] = None
    data_source: Optional[str] = None
    # Enveloppe de qualité documentaire : ces champs décrivent la portée de
    # l'information disponible et ne constituent pas une garantie juridique.
    informational_only: bool = True
    legally_binding: bool = False
    overall_status: str = "INFORMATIVE_PARTIAL"
    quality_dimensions: Dict[str, str] = Field(
        default_factory=lambda: {
            "source": "PARTIAL",
            "temporal_validity": "PARTIAL",
            "classification": "DOCUMENTED",
            "taxes_and_levies": "PARTIAL",
            "preference_and_origin": "UNVERIFIED",
            "formalities": "NOT_AVAILABLE",
        }
    )
    known_data_gaps: List[str] = Field(default_factory=list)
    administrative_confirmation_recommended: bool = True
    administrative_confirmation_required: bool = True
    disclaimer: Dict[str, Any] = Field(
        default_factory=lambda: {
            "informational_only": True,
            "legally_binding": False,
            "message": "Simulation informative fondée sur les données disponibles.",
        }
    )
    technical_validation_status: Optional[str] = None
    source_authority: Optional[str] = None
    source_title: Optional[str] = None
    source_date: Optional[str] = None
    effective_date: Optional[str] = None
    completeness_status: Optional[str] = None

    @field_validator("quality_dimensions", mode="before")
    @classmethod
    def validate_quality_dimensions(cls, value: Any) -> Dict[str, str]:
        """Normalize legacy payloads while enforcing the six-value vocabulary."""
        defaults = {
            "source": "PARTIAL",
            "temporal_validity": "PARTIAL",
            "classification": "DOCUMENTED",
            "taxes_and_levies": "PARTIAL",
            "preference_and_origin": "UNVERIFIED",
            "formalities": "NOT_AVAILABLE",
        }
        if value is None:
            return defaults
        if not isinstance(value, dict):
            raise TypeError("quality_dimensions must be an object")
        unknown = set(value) - set(QUALITY_DIMENSION_KEYS)
        if unknown:
            raise ValueError(f"Unknown quality dimension(s): {sorted(unknown)}")
        invalid = {key: item for key, item in value.items() if item not in QUALITY_DIMENSION_VALUES}
        if invalid:
            raise ValueError(f"Invalid quality dimension value(s): {invalid}")
        return {**defaults, **value}

    @field_validator("overall_status", mode="before")
    @classmethod
    def validate_overall_status(cls, value: Any) -> str:
        token = str(value or "INFORMATIVE_PARTIAL").strip().upper()
        token = OVERALL_STATUS_ALIASES.get(token, token)
        if token not in OVERALL_STATUS_VALUES:
            raise ValueError(f"Invalid overall_status: {value}")
        return token

    @field_validator("informational_only", mode="before")
    @classmethod
    def force_informational_only(cls, value: Any) -> bool:
        # Normalize legacy false payloads without breaking their consumers.
        return True

    @field_validator("legally_binding", mode="before")
    @classmethod
    def force_non_binding(cls, value: Any) -> bool:
        # Normalize legacy true payloads at the response boundary.
        return False

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
