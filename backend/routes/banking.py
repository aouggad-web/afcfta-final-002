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
  GET  /banking/forex/rates            ← new: taux de change live des devises africaines
  GET  /banking/forex/convert          ← new: conversion USD → monnaie locale en temps réel
  GET  /banking/compliance/{country_code}
  GET  /banking/register         ← global searchable banks directory
  GET  /banking/regulations/summary ← all-countries regulation overview
  POST /banking/transaction/validate
"""

from fastapi import APIRouter, HTTPException, Query
from collections import defaultdict
from pydantic import BaseModel, Field
from typing import Optional
import logging

from banking_system import (
    get_country_banks,
    get_regional_banks,
    get_banks_register,
    get_forex_profile,
    get_domiciliation_rules,
    get_currency_meta,
    get_all_currency_meta,
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
from banking_system.foreign_exchange import FOREX_PROFILES
from banking_system.models import ExchangeRateInfo
from exchange_rates import get_service as get_rate_service, AFRICAN_CURRENCY_CODES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banking")


# ---------------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------------

def _build_exchange_rate_info(country_code: str) -> Optional[ExchangeRateInfo]:
    """
    Fetch live exchange rate for a country's local currency vs USD and EUR.

    Uses the ExchangeRateService provider chain (CurrencyFreaks → Fixer → Frankfurter).
    Returns None if all providers fail (network error, missing API keys, etc.).
    """
    code = country_code.upper()
    currency_code, currency_name, convertibility = get_currency_meta(code)
    if not currency_code or currency_code == "USD":
        return ExchangeRateInfo(
            currency_code=currency_code or "USD",
            currency_name=currency_name or "Dollar américain",
            rate_usd=1.0,
            rate_eur=None,
            rate_source="N/A",
            rate_timestamp=None,
            convertibility=convertibility or "freely_convertible",
        )
    try:
        svc = get_rate_service()
        rate_obj = svc.get_rate("USD", currency_code)
        rate_eur_obj = svc.get_rate("EUR", currency_code)
        return ExchangeRateInfo(
            currency_code=currency_code,
            currency_name=currency_name,
            rate_usd=rate_obj.rate if rate_obj else None,
            rate_eur=rate_eur_obj.rate if rate_eur_obj else None,
            rate_source=rate_obj.source if rate_obj else None,
            rate_timestamp=(
                rate_obj.timestamp.isoformat() if rate_obj else None
            ),
            convertibility=convertibility,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
            "Could not fetch live exchange rate for %s (%s): %s",
            code, currency_code, exc,
        )
        return ExchangeRateInfo(
            currency_code=currency_code,
            currency_name=currency_name,
            rate_usd=None,
            rate_eur=None,
            rate_source="unavailable",
            rate_timestamp=None,
            convertibility=convertibility,
        )


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

    - **country_code**: Code ISO2 ou ISO3 du pays (ex: MA, DZ, NG ou MAR, DZA, NGA)
    """
    code = country_code.upper()
    _ISO3_TO_ISO2 = {
        "DZA": "DZ", "MAR": "MA", "TUN": "TN", "EGY": "EG", "LBY": "LY",
        "SDN": "SD", "NGA": "NG", "GHA": "GH", "CIV": "CI", "SEN": "SN",
        "CMR": "CM", "ETH": "ET", "KEN": "KE", "TZA": "TZ", "UGA": "UG",
        "ZAF": "ZA", "AGO": "AO", "MOZ": "MZ", "ZMB": "ZM", "ZWE": "ZW",
        "MDG": "MG", "MUS": "MU", "NAM": "NA", "BWA": "BW", "SWZ": "SZ",
        "LSO": "LS", "MWI": "MW", "RWA": "RW", "BDI": "BI", "SOM": "SO",
        "DJI": "DJ", "ERI": "ER", "COD": "CD", "COG": "CG", "GAB": "GA",
        "GNQ": "GQ", "CAF": "CF", "TCD": "TD", "NER": "NE", "MLI": "ML",
        "BFA": "BF", "GIN": "GN", "SLE": "SL", "LBR": "LR", "MRT": "MR",
        "GMB": "GM", "GNB": "GW", "CPV": "CV", "STP": "ST", "COM": "KM",
        "SYC": "SC", "TGO": "TG", "BEN": "BJ",
    }
    if len(code) == 3:
        code = _ISO3_TO_ISO2.get(code, code)
    if code not in CENTRAL_BANKS:
        raise HTTPException(
            status_code=404,
            detail=f"Pays '{country_code.upper()}' non trouvé dans le registre bancaire africain.",
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
    summary="Réglementations de change d'un pays (+ taux de change live)",
    tags=["Banking"],
)
async def get_forex_regulations(country_code: str):
    """
    Retourne le profil complet de réglementation des changes pour un pays,
    incluant les règles de domiciliation, seuils, obligations, références légales
    et le taux de change live de la monnaie locale vs USD et EUR.

    - **country_code**: Code ISO2 du pays (ex: MA, DZ, NG, ET)
    """
    code = country_code.upper()
    profile = get_forex_profile(code)
    # Enrich with live exchange rate info
    rate_info = _build_exchange_rate_info(code)
    enriched = profile.model_copy(update={"exchange_rate_info": rate_info})
    return enriched.model_dump()


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
            "imf_article_status": profile.forex_regulation.imf_article_status,
            "regulatory_body": profile.forex_regulation.regulatory_body,
        }
        for code, profile in FOREX_PROFILES.items()
    ]


# ---------------------------------------------------------------------------
# LIVE FOREX RATES ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/forex/rates",
    summary="Taux de change live des devises africaines vs USD",
    tags=["Banking"],
)
async def get_african_forex_rates(
    base: str = Query(
        default="USD",
        description="Devise de base (ISO 4217). Ex: USD, EUR",
    ),
):
    """
    Retourne les taux de change en temps réel de toutes les devises africaines
    disponibles par rapport à la devise de base spécifiée (USD par défaut).

    Les taux sont récupérés depuis une chaîne de fournisseurs :
    CurrencyFreaks → Fixer.io → Frankfurter (ECB).

    Inclut pour chaque devise :
    - Le code ISO 4217 et le nom de la devise
    - Le taux de change (1 [base] = X [devise locale])
    - La source du taux et l'horodatage
    - La convertibilité de la devise
    """
    try:
        svc = get_rate_service()
        bundle = svc.get_latest(base.upper())
        if bundle is None:
            raise HTTPException(
                status_code=503,
                detail="Service de taux de change temporairement indisponible.",
            )
        # Filter to African currencies and enrich with metadata
        currency_meta = get_all_currency_meta()
        # Build reverse map: currency_code → {currency_name, convertibility, countries}
        currency_countries: dict = defaultdict(lambda: {"currency_name": "", "convertibility": "unknown", "countries": []})
        for country_code, (ccode, cname, conv) in currency_meta.items():
            currency_countries[ccode]["currency_name"] = cname
            currency_countries[ccode]["convertibility"] = conv
            currency_countries[ccode]["countries"].append(country_code)

        results = []
        for currency_code in AFRICAN_CURRENCY_CODES:
            rate_value = bundle.rates.get(currency_code)
            if rate_value is None:
                continue
            meta_info = currency_countries.get(currency_code, {})
            results.append({
                "currency_code": currency_code,
                "currency_name": meta_info.get("currency_name", currency_code),
                "convertibility": meta_info.get("convertibility", "unknown"),
                "countries": meta_info.get("countries", []),
                f"rate_{base.lower()}": rate_value,
                "rate_display": f"1 {base.upper()} = {rate_value:,.4f} {currency_code}",
                "source": bundle.source,
                "timestamp": bundle.timestamp.isoformat(),
            })

        results.sort(key=lambda x: x["currency_code"])
        return {
            "base_currency": base.upper(),
            "total": len(results),
            "source": bundle.source,
            "timestamp": bundle.timestamp.isoformat(),
            "rates": results,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erreur lors de la récupération des taux de change: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=f"Service de taux de change indisponible : {exc}",
        ) from exc


@router.get(
    "/forex/convert",
    summary="Convertir un montant USD en monnaie locale d'un pays africain",
    tags=["Banking"],
)
async def convert_to_local_currency(
    country_code: str = Query(..., description="Code ISO2 du pays (ex: MA, NG, KE)"),
    amount: float = Query(..., gt=0, description="Montant à convertir (doit être > 0)"),
    from_currency: str = Query(
        default="USD",
        description="Devise source (ISO 4217). Ex: USD, EUR, GBP",
    ),
):
    """
    Convertit un montant en devise source vers la monnaie locale du pays spécifié.

    Le taux de change est récupéré en temps réel depuis une chaîne de fournisseurs
    (CurrencyFreaks → Fixer.io → Frankfurter/ECB). Aucune donnée mockée n'est utilisée.

    - **country_code**: Code ISO2 du pays (ex: MA, NG, KE, ZA)
    - **amount**: Montant à convertir
    - **from_currency**: Devise source (par défaut USD)
    """
    code = country_code.upper()
    currency_code, currency_name, convertibility = get_currency_meta(code)

    # Get country name from registry if available
    cb = CENTRAL_BANKS.get(code)
    country_name = cb.country_name if cb else code

    try:
        svc = get_rate_service()
        result = svc.convert(from_currency.upper(), currency_code, amount)
        if result is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Impossible d'obtenir le taux de change {from_currency.upper()}/{currency_code}. "
                    "Le service de change est temporairement indisponible."
                ),
            )
        return {
            "country_code": code,
            "country_name": country_name,
            "from_currency": result.from_currency,
            "to_currency": result.to_currency,
            "currency_name": currency_name,
            "convertibility": convertibility,
            "amount": result.amount,
            "converted_amount": result.converted_amount,
            "rate": result.rate,
            "rate_display": f"1 {result.from_currency} = {result.rate:,.4f} {result.to_currency}",
            "source": result.source,
            "timestamp": result.timestamp.isoformat(),
            "disclaimer": (
                "Taux indicatif issu de données de marché publiques. "
                "Consulter votre banque agréée pour les taux commerciaux applicables."
            ),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Erreur conversion %s→%s: %s", from_currency, currency_code, exc)
        raise HTTPException(
            status_code=503,
            detail=f"Service de conversion indisponible : {exc}",
        ) from exc


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
# BANKS REGISTER ENDPOINT
# ---------------------------------------------------------------------------

@router.get(
    "/register",
    summary="Registre global et consultable de toutes les banques africaines",
    tags=["Banking"],
)
async def get_banks_register_endpoint(
    search: Optional[str] = Query(default=None, description="Recherche textuelle (nom, sigle, pays)"),
    country_code: Optional[str] = Query(default=None, description="Filtrer par code ISO2 du pays"),
    bank_type: Optional[str] = Query(default=None, description="Type de banque: central | commercial | regional"),
    trade_finance_only: bool = Query(default=False, description="Seulement les banques avec services trade finance"),
):
    """
    Retourne le registre global de toutes les banques africaines (centrales, commerciales, régionales)
    avec leurs coordonnées complètes (adresse, téléphone, email, site web).

    Permet une recherche textuelle et plusieurs filtres combinables.
    """
    results = get_banks_register(
        search=search,
        country_code=country_code.upper() if country_code else None,
        bank_type=bank_type,
        trade_finance_only=trade_finance_only,
    )
    return {"total": len(results), "results": results}


# ---------------------------------------------------------------------------
# REGULATIONS SUMMARY ENDPOINT
# ---------------------------------------------------------------------------

@router.get(
    "/regulations/summary",
    summary="Synthèse des réglementations de change pour tous les pays africains",
    tags=["Banking"],
)
async def get_regulations_summary(
    regulation_level: Optional[str] = Query(
        default=None,
        description="Filtrer par niveau: strict | moderate | liberal",
    ),
):
    """
    Retourne une synthèse comparative des réglementations de change pour tous les
    pays africains disponibles : domiciliation, rapatriement, autorisation préalable,
    niveau de contrôle des changes.

    Inclut également les données de base des banques centrales (devise, SWIFT).
    """
    summary = []
    for code, profile in FOREX_PROFILES.items():
        level = profile.forex_regulation.regulation_level
        if regulation_level and level != regulation_level:
            continue
        cb = CENTRAL_BANKS.get(code)
        currency_code, currency_name, convertibility = get_currency_meta(code)
        summary.append({
            "country_code": code,
            "country_name": profile.country_name,
            "central_bank": profile.central_bank_name,
            "currency_code": profile.currency_code or (cb.currency_code if cb else currency_code),
            "currency_name": profile.currency_name or (cb.currency_name if cb else currency_name),
            "convertibility": convertibility,
            "regulation_level": level,
            "imf_article_status": profile.forex_regulation.imf_article_status,
            "regulatory_body": profile.forex_regulation.regulatory_body,
            "legal_reference": profile.forex_regulation.legal_reference,
            "domiciliation_required": profile.domiciliation.required,
            "domiciliation_conditional": profile.domiciliation.conditional,
            "threshold_usd": profile.domiciliation.threshold_usd,
            "repatriation_days": profile.forex_regulation.repatriation_deadline_days,
            "prior_authorization": profile.forex_regulation.prior_authorization_required,
            "authorization_threshold_usd": profile.forex_regulation.authorization_threshold_usd,
            "declaration_threshold_usd": profile.forex_regulation.declaration_threshold_usd,
            "penalties": profile.forex_regulation.penalties,
            "banking_act": cb.banking_act if cb else None,
            "central_bank_website": cb.website if cb else None,
            "central_bank_phone": cb.phone if cb else None,
            "central_bank_email": cb.email if cb else None,
        })

    summary.sort(key=lambda x: x["country_name"])
    return {"total": len(summary), "results": summary}


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
    domiciliation_triggered = domiciliation.required or (
        domiciliation.conditional
        and domiciliation.threshold_usd is not None
        and body.amount_usd >= domiciliation.threshold_usd
    )
    if domiciliation_triggered:
        docs = ", ".join(str(d) for d in (domiciliation.mandatory_documents or []))
        threshold_str = (
            "toutes opérations"
            if domiciliation.threshold_usd == 0
            else f"{domiciliation.threshold_usd:,.0f} USD"
        )
        domiciliation_alert = {
            "required": True,
            "message": (
                f"Domiciliation bancaire obligatoire pour ce pays "
                f"(seuil: {threshold_str}). "
                f"Documents requis: {docs}."
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
            "domiciliation_required": domiciliation_triggered,
            "compliance_warnings": compliance["warnings"],
            "top_instrument": instruments[0].code if instruments else None,
        },
    }
