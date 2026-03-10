"""
Banking system API routes – ZLECAf

Endpoints:
  GET  /banking/countries/{country_code}/banks
  GET  /banking/countries/{country_code}/regulations
  GET  /banking/countries/{country_code}/risk-assessment
  GET  /banking/trade-finance/instruments
  GET  /banking/trade-finance/recommend
  GET  /banking/payment-systems/regional
  GET  /banking/forex/domiciliation-rules
  GET  /banking/compliance/{country_code}
  POST /banking/transaction/validate
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import logging

from banking_system import (
    get_country_banks,
    get_regional_banks,
    get_forex_profile,
    get_domiciliation_rules,
    get_trade_finance_instruments,
    recommend_instruments,
    get_payment_systems,
    get_regional_systems,
    get_country_compliance,
    check_compliance,
    get_country_risk,
    assess_transaction_risk,
)
from banking_system.banks_registry import CENTRAL_BANKS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banking")


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE SCHEMAS
# ---------------------------------------------------------------------------

class TransactionValidationRequest(BaseModel):
    """Request body for transaction validation"""
    origin_country: str = Field(..., description="ISO2 code du pays exportateur")
    destination_country: str = Field(..., description="ISO2 code du pays importateur")
    amount_usd: float = Field(..., gt=0, description="Montant de la transaction en USD")
    transaction_type: str = Field(
        default="export",
        description="Type : export | import",
    )
    sector: Optional[str] = Field(default=None, description="Secteur d'activité")


# ---------------------------------------------------------------------------
# BANKS ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/countries/{country_code}/banks",
    summary="Informations bancaires d'un pays",
    tags=["Banking"],
)
async def get_banks_by_country(country_code: str):
    """
    Retourne les informations bancaires complètes d'un pays africain :
    banque centrale, banques commerciales agréées, banques régionales.

    - **country_code**: Code ISO2 du pays (ex: MA, NG, KE, ZA)
    """
    code = country_code.upper()
    if code not in CENTRAL_BANKS:
        raise HTTPException(
            status_code=404,
            detail=f"Pays '{code}' non trouvé dans le registre bancaire africain.",
        )
    info = get_country_banks(code)
    return info.model_dump()


@router.get(
    "/regional-banks",
    summary="Banques régionales et de développement africaines",
    tags=["Banking"],
)
async def get_all_regional_banks(region: Optional[str] = Query(default=None, description="Filtrer par région")):
    """
    Retourne les banques régionales et de développement africaines
    (AfDB, Afreximbank, BOAD, EADB, DBSA, etc.).
    """
    banks = get_regional_banks(region)
    return [b.model_dump() for b in banks]


@router.get(
    "/countries",
    summary="Liste des pays avec registre bancaire",
    tags=["Banking"],
)
async def list_banking_countries():
    """Liste des pays africains disponibles dans le registre bancaire."""
    return [
        {
            "country_code": code,
            "country_name": cb.country_name,
            "central_bank": cb.name,
            "currency_code": cb.currency_code,
            "forex_regulation": cb.forex_regulation,
        }
        for code, cb in CENTRAL_BANKS.items()
    ]


# ---------------------------------------------------------------------------
# FOREX / DOMICILIATION ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/countries/{country_code}/regulations",
    summary="Réglementations de change d'un pays",
    tags=["Banking"],
)
async def get_forex_regulations(country_code: str):
    """
    Retourne le profil complet de réglementation des changes pour un pays,
    incluant les règles de domiciliation, seuils et obligations.

    - **country_code**: Code ISO2 du pays (ex: MA, DZ, NG, ET)
    """
    profile = get_forex_profile(country_code.upper())
    return profile.model_dump()


@router.get(
    "/forex/domiciliation-rules",
    summary="Règles de domiciliation par pays",
    tags=["Banking"],
)
async def get_all_domiciliation_rules():
    """
    Retourne les règles de domiciliation pour tous les pays disponibles.
    Indique si la domiciliation est obligatoire, conditionnelle ou non requise.
    """
    from banking_system.foreign_exchange import FOREX_PROFILES
    return [
        {
            "country_code": code,
            "country_name": profile.country_name,
            "domiciliation_required": profile.domiciliation.required,
            "domiciliation_conditional": profile.domiciliation.conditional,
            "threshold_usd": profile.domiciliation.threshold_usd,
            "timeline_days": profile.domiciliation.timeline_days,
            "regulation_level": profile.forex_regulation.regulation_level,
        }
        for code, profile in FOREX_PROFILES.items()
    ]


# ---------------------------------------------------------------------------
# TRADE FINANCE ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/trade-finance/instruments",
    summary="Catalogue des instruments de financement du commerce",
    tags=["Banking"],
)
async def list_trade_finance_instruments():
    """
    Retourne le catalogue complet des instruments de financement du commerce :
    crédits documentaires, remises documentaires, garanties bancaires,
    financements pré/post-expédition, affacturage, etc.
    """
    instruments = get_trade_finance_instruments()
    return [i.model_dump() for i in instruments]


@router.get(
    "/trade-finance/recommend",
    summary="Recommander des instruments selon le pays et le type de transaction",
    tags=["Banking"],
)
async def recommend_trade_finance(
    country_code: str = Query(..., description="ISO2 code du pays partenaire"),
    transaction_type: str = Query(default="export", description="export | import"),
    amount_usd: float = Query(default=0.0, ge=0, description="Montant en USD"),
):
    """
    Recommande les instruments de financement les plus adaptés pour une
    transaction avec un pays donné, en tenant compte de la réglementation
    locale et du risque pays.
    """
    instruments = recommend_instruments(
        country_code=country_code,
        transaction_type=transaction_type,
        amount_usd=amount_usd,
    )
    return {
        "country_code": country_code.upper(),
        "transaction_type": transaction_type,
        "amount_usd": amount_usd,
        "recommended_instruments": [i.model_dump() for i in instruments],
    }


# ---------------------------------------------------------------------------
# PAYMENT SYSTEMS ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/payment-systems/regional",
    summary="Systèmes de paiement régionaux africains",
    tags=["Banking"],
)
async def get_regional_payment_systems(
    region: Optional[str] = Query(default=None, description="Filtrer par région"),
):
    """
    Retourne les systèmes de paiement régionaux africains :
    BCEAO STAR, GIMAC, SIRESS SADC, EAPS, PAPSS, etc.
    """
    systems = get_regional_systems(region)
    return [s.model_dump() for s in systems]


@router.get(
    "/payment-systems",
    summary="Tous les systèmes de paiement (SWIFT, régionaux, mobile money, digital)",
    tags=["Banking"],
)
async def get_all_payment_systems(
    country_code: Optional[str] = Query(
        default=None, description="Filtrer par pays (ISO2)"
    ),
):
    """
    Retourne tous les systèmes de paiement disponibles, avec filtrage optionnel
    par pays : SWIFT, systèmes régionaux, mobile money (M-Pesa, MTN MoMo, Wave)
    et plateformes digitales (Flutterwave, Paystack).
    """
    systems = get_payment_systems(country_code)
    return [s.model_dump() for s in systems]


# ---------------------------------------------------------------------------
# RISK ASSESSMENT ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/countries/{country_code}/risk-assessment",
    summary="Évaluation du risque pays",
    tags=["Banking"],
)
async def get_risk_assessment(
    country_code: str,
    amount_usd: float = Query(default=100_000.0, ge=0, description="Montant de la transaction en USD"),
    transaction_type: str = Query(default="export", description="export | import"),
):
    """
    Évalue le risque d'une opération commerciale avec un pays donné :
    risque pays (notation Coface), risque de change, risque de transfert,
    risque politique, et recommandations d'instruments adaptés.

    - **country_code**: Code ISO2 (ex: NG, ET, ZW)
    - **amount_usd**: Montant de la transaction (influence les recommandations)
    - **transaction_type**: export ou import
    """
    return assess_transaction_risk(
        country_code=country_code.upper(),
        amount_usd=amount_usd,
        transaction_type=transaction_type,
    )


# ---------------------------------------------------------------------------
# COMPLIANCE ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/compliance/{country_code}",
    summary="Exigences de conformité (KYC/AML) d'un pays",
    tags=["Banking"],
)
async def get_compliance_requirements(country_code: str):
    """
    Retourne les exigences de conformité réglementaire pour les opérations
    commerciales avec un pays africain : cadre AML, exigences KYC,
    contrôle des sanctions, seuils de déclaration.

    - **country_code**: Code ISO2 du pays
    """
    return get_country_compliance(country_code.upper())


# ---------------------------------------------------------------------------
# TRANSACTION VALIDATION ENDPOINT
# ---------------------------------------------------------------------------

@router.post(
    "/transaction/validate",
    summary="Valider une transaction commerciale (conformité + risque)",
    tags=["Banking"],
)
async def validate_transaction(body: TransactionValidationRequest):
    """
    Effectue une analyse complète d'une transaction commerciale :

    1. **Réglementation de change** du pays destinataire
    2. **Vérification de conformité** (AML/KYC, sanctions)
    3. **Évaluation du risque** pays
    4. **Instruments financiers** recommandés
    5. **Obligations de domiciliation** applicables
    """
    dest = body.destination_country.upper()
    orig = body.origin_country.upper()

    # Domiciliation rules for destination country
    domiciliation = get_domiciliation_rules(dest)

    # Compliance check
    compliance = check_compliance(
        country_code=dest,
        transaction_value_usd=body.amount_usd,
        sector=body.sector,
    )

    # Risk assessment
    risk = assess_transaction_risk(
        country_code=dest,
        amount_usd=body.amount_usd,
        transaction_type=body.transaction_type,
    )

    # Recommended instruments
    instruments = recommend_instruments(
        country_code=dest,
        transaction_type=body.transaction_type,
        amount_usd=body.amount_usd,
    )

    # Domiciliation alert
    domiciliation_alert = None
    if domiciliation.required or (
        domiciliation.conditional
        and domiciliation.threshold_usd is not None
        and body.amount_usd >= domiciliation.threshold_usd
    ):
        domiciliation_alert = {
            "required": True,
            "message": (
                f"Domiciliation bancaire obligatoire pour ce pays "
                f"(seuil: {domiciliation.threshold_usd:,.0f} USD). "
                f"Documents requis: {', '.join(domiciliation.mandatory_documents)}."
            ),
            "timeline_days": domiciliation.timeline_days,
        }

    return {
        "transaction": {
            "origin_country": orig,
            "destination_country": dest,
            "amount_usd": body.amount_usd,
            "transaction_type": body.transaction_type,
        },
        "domiciliation_alert": domiciliation_alert,
        "compliance": compliance,
        "risk_assessment": risk,
        "recommended_instruments": [i.model_dump() for i in instruments[:3]],
        "summary": {
            "alert_level": risk["alert_level"],
            "domiciliation_required": domiciliation.required or (
                domiciliation.conditional
                and domiciliation.threshold_usd is not None
                and body.amount_usd >= domiciliation.threshold_usd
            ),
            "compliance_warnings": compliance["warnings"],
            "top_instrument": instruments[0].code if instruments else None,
        },
    }
