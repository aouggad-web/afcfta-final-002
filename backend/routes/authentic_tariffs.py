"""
Authentic Tariff Routes
API endpoints for authentic African tariff data with sub-positions,
detailed taxes, fiscal advantages, and administrative formalities
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging

from services.authentic_tariff_service import (
    get_available_countries,
    get_tariff_line,
    get_sub_positions,
    get_taxes_detail,
    get_fiscal_advantages,
    get_administrative_formalities,
    calculate_import_taxes,
    search_tariff_lines,
    get_country_summary
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authentic-tariffs", tags=["Authentic Tariffs"])


@router.get("/countries")
async def list_available_countries():
    """
    Liste des pays avec données tarifaires authentiques
    
    Returns:
        Liste des pays et leurs statistiques tarifaires
    """
    countries = get_available_countries()
    return {
        "success": True,
        "total": len(countries),
        "countries": countries,
        "data_format": "enhanced_v2",
        "source": "Official African Customs Tariffs"
    }


@router.get("/country/{country_iso3}/summary")
async def get_tariff_summary(country_iso3: str):
    """
    Résumé des données tarifaires d'un pays
    
    Args:
        country_iso3: Code ISO3 du pays (ex: DZA, ETH)
    
    Returns:
        Statistiques et résumé des tarifs
    """
    summary = get_country_summary(country_iso3.upper())
    
    if not summary:
        raise HTTPException(
            status_code=404, 
            detail=f"No tariff data found for country {country_iso3}"
        )
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "summary": summary
    }


@router.get("/country/{country_iso3}/line/{hs_code}")
async def get_tariff_line_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir une ligne tarifaire complète avec sous-positions
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)
        language: Langue pour les descriptions
    
    Returns:
        Ligne tarifaire complète avec taxes, avantages, formalités
    """
    tariff = get_tariff_line(country_iso3.upper(), hs_code)
    
    if not tariff:
        raise HTTPException(
            status_code=404,
            detail=f"No tariff found for {country_iso3}/{hs_code}"
        )
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "tariff_line": tariff
    }


@router.get("/country/{country_iso3}/sub-positions/{hs6}")
async def get_sub_positions_endpoint(
    country_iso3: str,
    hs6: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir toutes les sous-positions nationales pour un code HS6
    
    Args:
        country_iso3: Code ISO3 du pays
        hs6: Code HS6 (6 chiffres)
    
    Returns:
        Liste des sous-positions avec leurs taux DD spécifiques
    """
    sub_positions = get_sub_positions(country_iso3.upper(), hs6[:6])
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs6": hs6[:6],
        "total": len(sub_positions),
        "sub_positions": sub_positions,
        "note_fr": "Les sous-positions nationales peuvent avoir des taux DD différents du code HS6 parent",
        "note_en": "National sub-positions may have different DD rates than the parent HS6 code"
    }


@router.get("/country/{country_iso3}/taxes/{hs_code}")
async def get_taxes_detail_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir le détail des taxes pour un code HS
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS
    
    Returns:
        Détail de chaque taxe (DD, TVA, PRCT, TCS, etc.)
    """
    taxes = get_taxes_detail(country_iso3.upper(), hs_code)
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "taxes": taxes
    }


@router.get("/country/{country_iso3}/advantages/{hs_code}")
async def get_fiscal_advantages_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir les avantages fiscaux (dont ZLECAf) pour un code HS
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS
    
    Returns:
        Liste des avantages fiscaux applicables
    """
    advantages = get_fiscal_advantages(country_iso3.upper(), hs_code)
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "advantages": advantages
    }


@router.get("/country/{country_iso3}/formalities/{hs_code}")
async def get_formalities_endpoint(
    country_iso3: str,
    hs_code: str,
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Obtenir les formalités administratives requises pour un code HS
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS
    
    Returns:
        Liste des documents/formalités requis
    """
    formalities = get_administrative_formalities(country_iso3.upper(), hs_code)
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "hs_code": hs_code,
        "formalities": formalities
    }


@router.post("/calculate")
async def calculate_taxes_endpoint(
    country_iso3: str = Query(..., description="ISO3 country code"),
    hs_code: str = Query(..., description="HS code (6-12 digits)"),
    cif_value: float = Query(..., description="CIF value in USD"),
    language: str = Query("fr", description="Language: fr or en")
):
    """
    Calculer les taxes d'importation avec données authentiques
    
    Calcule et compare:
    - Régime NPF (Normal)
    - Régime ZLECAf (avec exonérations)
    - Économies réalisées
    
    Args:
        country_iso3: Code ISO3 du pays
        hs_code: Code HS (6-12 chiffres)
        cif_value: Valeur CIF en USD
        language: Langue pour les descriptions
    
    Returns:
        Calcul détaillé NPF vs ZLECAf avec économies
    """
    result = calculate_import_taxes(
        country_iso3=country_iso3.upper(),
        hs_code=hs_code,
        cif_value=cif_value,
        language=language
    )
    
    if 'error' in result:
        raise HTTPException(status_code=404, detail=result['error'])
    
    _enrich_with_dual_breakdown(result, cif_value, country_iso3.upper())
    return result


def _enrich_with_dual_breakdown(result: dict, value: float, country_iso3: str) -> None:
    """Enrichit in-place le résultat authentic avec taxes_breakdown, taxes_summary et currency.

    Stratégie :
    - taxes_breakdown : mappé DIRECTEMENT depuis calculation_steps (NPF) +
      calculation_steps_zlecaf (ZLECAf) — vrais montants calculés, aucune
      re-dérivation depuis les taux. La conversion devise est une multiplication pure.
    - taxes_summary   : mappé depuis npf_calculation / zlecaf_calculation (totaux
      dd / other_taxes / vat / total_to_pay déjà calculés par le moteur authentic).
    - currency        : bloc devise locale (ISO2) + taux USD→local.
    """
    from currencies.service import get_by_country as _get_currency
    from exchange_rates import get_service as _get_fx_service

    steps_npf = result.get("calculation_steps", [])
    steps_zlc = result.get("calculation_steps_zlecaf", [])
    npf_calc  = result.get("npf_calculation", {})
    zlc_calc  = result.get("zlecaf_calculation", {})

    if not steps_npf:
        result["taxes_breakdown"] = []
        result["taxes_summary"]   = {}
        result["currency"]        = None
        return

    # ── Lookup ZLECAf steps par code ─────────────────────────────────────────
    zlc_by_code = {s["code"]: s for s in steps_zlc}

    # ── Catégorisation simplifiée ─────────────────────────────────────────────
    def _cat(code: str) -> str:
        if code == "DD":
            return "droit_douane"
        if code in ("TVA", "VAT", "TPS", "GST"):
            return "tva"
        return "autre_taxe"

    # ── taxes_breakdown — mapping direct depuis calculation_steps ─────────────
    breakdown = []
    for step in steps_npf:
        code     = step["code"]
        zlc_step = zlc_by_code.get(code, {})
        amt_npf  = float(step.get("amount", 0) or 0)
        amt_zlc  = float(zlc_step.get("amount", amt_npf) if zlc_step else amt_npf)
        rate_npf = float(step.get("rate_pct", 0) or 0)
        rate_zlc = float(zlc_step.get("rate_pct", rate_npf) if zlc_step else rate_npf)
        breakdown.append({
            "code":              code,
            "name":              step.get("label", code),
            "category":          _cat(code),
            "base_expr":         step.get("base_formula", "CIF"),
            "rate_npf_pct":      rate_npf,
            "rate_zlecaf_pct":   rate_zlc,
            "amount_npf":        round(amt_npf, 2),
            "amount_zlecaf":     round(amt_zlc, 2),
            "affected_by_zlecaf": rate_zlc != rate_npf,
        })

    # ── taxes_summary — depuis npf_calculation / zlecaf_calculation ──────────
    def _g(calc: dict, key: str) -> float:
        v = calc.get(key, {})
        return float(v.get("amount", 0) if isinstance(v, dict) else (v or 0))

    def _summarize(calc: dict) -> dict:
        dd    = _g(calc, "dd")
        other = _g(calc, "other_taxes")
        vat   = _g(calc, "vat")
        total = dd + other + vat
        cost  = float(calc.get("total_to_pay", value + total) or (value + total))
        return {
            "droit_douane":          round(dd, 2),
            "autres_taxes":          round(other, 2),
            "tva":                   round(vat, 2),
            "total_taxes_et_droits": round(total, 2),
            "cout_total":            round(cost, 2),
        }

    npf_s = _summarize(npf_calc)
    zlc_s = _summarize(zlc_calc)
    taxes_summary = {
        "npf":             npf_s,
        "zlecaf":          zlc_s,
        "economie_droits": round(npf_s["total_taxes_et_droits"] - zlc_s["total_taxes_et_droits"], 2),
        "economie_totale": round(npf_s["cout_total"] - zlc_s["cout_total"], 2),
    }

    # ── Devise locale : conversion = multiplication pure ──────────────────────
    _ISO3_TO_ISO2 = {
        "DZA":"DZ","AGO":"AO","BEN":"BJ","BWA":"BW","BFA":"BF","BDI":"BI",
        "CMR":"CM","CPV":"CV","CAF":"CF","TCD":"TD","COM":"KM","COG":"CG",
        "COD":"CD","CIV":"CI","DJI":"DJ","EGY":"EG","GNQ":"GQ","ERI":"ER",
        "SWZ":"SZ","ETH":"ET","GAB":"GA","GMB":"GM","GHA":"GH","GIN":"GN",
        "GNB":"GW","KEN":"KE","LSO":"LS","LBR":"LR","LBY":"LY","MDG":"MG",
        "MWI":"MW","MLI":"ML","MRT":"MR","MUS":"MU","MAR":"MA","MOZ":"MZ",
        "NAM":"NA","NER":"NE","NGA":"NG","RWA":"RW","STP":"ST","SEN":"SN",
        "SYC":"SC","SLE":"SL","SOM":"SO","ZAF":"ZA","SSD":"SS","SDN":"SD",
        "TZA":"TZ","TGO":"TG","TUN":"TN","UGA":"UG","ZMB":"ZM","ZWE":"ZW",
    }
    _iso2 = _ISO3_TO_ISO2.get(country_iso3, country_iso3[:2])
    _ccy  = _get_currency(_iso2)
    currency_block = None

    if _ccy:
        _rate_obj = None
        try:
            _rate_obj = _get_fx_service().get_rate("USD", _ccy.currency_code)
        except Exception as _fx_err:
            logger.warning("Taux de change indisponible (%s): %s", _ccy.currency_code, _fx_err)

        if _rate_obj and _rate_obj.rate:
            _r = _rate_obj.rate
            # Enrichir chaque ligne breakdown avec le montant local
            for entry in breakdown:
                entry["amount_npf_local"]    = round(entry["amount_npf"] * _r, 2)
                entry["amount_zlecaf_local"] = round(entry["amount_zlecaf"] * _r, 2)
            # Convertir summary_local (multiplication pure)
            def _localize_summary(s: dict) -> dict:
                return {k: round(v * _r, 2) for k, v in s.items()}
            summary_local = {
                "npf":             _localize_summary(npf_s),
                "zlecaf":          _localize_summary(zlc_s),
                "economie_droits": round(taxes_summary["economie_droits"] * _r, 2),
                "economie_totale": round(taxes_summary["economie_totale"] * _r, 2),
            }
            currency_block = {
                "local_code":        _ccy.currency_code,
                "local_name":        _ccy.currency_name_fr,
                "local_symbol":      _ccy.currency_symbol,
                "usd_to_local_rate": round(_r, 6),
                "rate_source":       _rate_obj.source,
                "rate_as_of":        _rate_obj.timestamp.isoformat(),
                "available":         True,
                "value_usd":         round(value, 2),
                "value_local":       round(value * _r, 2),
                "summary_local":     summary_local,
            }
        else:
            currency_block = {
                "local_code":        _ccy.currency_code,
                "local_name":        _ccy.currency_name_fr,
                "local_symbol":      _ccy.currency_symbol,
                "usd_to_local_rate": None,
                "available":         False,
                "note":              "Taux de change indisponible — montants en USD uniquement.",
                "value_usd":         round(value, 2),
            }

    result["taxes_breakdown"] = breakdown
    result["taxes_summary"]   = taxes_summary
    result["currency"]        = currency_block


@router.get("/calculate/{country_iso3}/{hs_code}")
async def calculate_taxes_get_endpoint(
    country_iso3: str,
    hs_code: str,
    value: float = Query(10000, description="CIF value in USD"),
    language: str = Query("fr", description="Language: fr or en")
):
    """Version GET du calculateur avec ventilation bi-devise NPF vs ZLECAf."""
    result = await calculate_taxes_endpoint(
        country_iso3=country_iso3,
        hs_code=hs_code,
        cif_value=value,
        language=language
    )
    _enrich_with_dual_breakdown(result, value, country_iso3.upper())
    return result


@router.get("/search/{country_iso3}")
async def search_tariffs_endpoint(
    country_iso3: str,
    q: str = Query(..., min_length=2, description="Search query"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, le=100, description="Max results")
):
    """
    Rechercher dans les lignes tarifaires d'un pays
    
    Args:
        country_iso3: Code ISO3 du pays
        q: Requête de recherche (code HS ou description)
        language: Langue
        limit: Nombre max de résultats
    
    Returns:
        Liste des lignes tarifaires correspondantes
    """
    results = search_tariff_lines(
        country_iso3=country_iso3.upper(),
        query=q,
        language=language,
        limit=limit
    )
    
    return {
        "success": True,
        "country_iso3": country_iso3.upper(),
        "query": q,
        "total": len(results),
        "results": results
    }


def register_routes(api_router):
    """Register authentic tariff routes with the main API router"""
    api_router.include_router(router)
