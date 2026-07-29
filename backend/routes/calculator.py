"""
Calculator routes - Main tariff calculation endpoint
Extracted from server.py for better maintainability
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from constants import AFRICAN_COUNTRIES
from data_loader import get_tariff_corrections
from etl.country_hs6_detailed import get_all_sub_positions, get_sub_position_rate, has_varying_rates
from etl.country_hs6_tariffs import get_country_hs6_tariff
from etl.country_tariffs_complete import (
    get_other_taxes_for_country,
    get_tariff_rate_for_country,
    get_vat_rate_for_country,
)
from fastapi import APIRouter, HTTPException
from models import TariffCalculationRequest, TariffCalculationResponse
from services.crawled_data_service import crawled_service
from services.tariff_data_service import tariff_service
from services.tariff_enrichment_service import get_country_enrichment

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Calculator"])


# API Clients for external data
class WorldBankAPIClient:
    def __init__(self):
        self.base_url = "https://api.worldbank.org/v2"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "ZLECAf-API/1.0"})

    async def get_country_data(
        self, country_codes: List[str], indicators: List[str] = None
    ) -> Dict[str, Any]:
        """Fetch economic data from World Bank"""
        if indicators is None:
            indicators = ["NY.GDP.MKTP.CD", "SP.POP.TOTL", "NY.GDP.PCAP.CD", "FP.CPI.TOTL.ZG"]

        try:
            all_data = {}
            for country in country_codes:
                country_data = {}
                for indicator in indicators:
                    url = f"{self.base_url}/country/{country}/indicator/{indicator}"
                    params = {"format": "json", "date": "2020:2023", "per_page": 10}

                    response = self.session.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 1 and data[1]:
                            latest_data = data[1][0] if data[1] else None
                            if latest_data and latest_data["value"]:
                                country_data[indicator] = {
                                    "value": latest_data["value"],
                                    "date": latest_data["date"],
                                }

                all_data[country] = country_data

            return all_data
        except Exception as e:
            logging.error(f"World Bank API error: {e}")
            return {}


class OECAPIClient:
    def __init__(self):
        self.base_url = "https://api-v2.oec.world"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "ZLECAf-API/1.0"})

    async def get_top_producers(self, hs_code: str, year: int = 2021) -> List[Dict[str, Any]]:
        """Get top 5 African producers for an HS code"""
        try:
            endpoint = "tesseract/data.jsonrecords"
            params = {
                "cube": "trade_i_hs4_eci",
                "drilldowns": "Reporter",
                "measures": "Export Value",
                "Product": hs_code[:4] if len(hs_code) > 4 else hs_code,
                "time": str(year),
                "Trade Flow": "2",
            }

            response = self.session.get(f"{self.base_url}/{endpoint}", params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    african_codes = [country["iso3"] for country in AFRICAN_COUNTRIES]
                    african_exports = []

                    for item in data["data"]:
                        if item.get("Reporter") in african_codes:
                            african_exports.append(
                                {
                                    "country_code": item.get("Reporter"),
                                    "country_name": next(
                                        (
                                            c["name"]
                                            for c in AFRICAN_COUNTRIES
                                            if c["iso3"] == item.get("Reporter")
                                        ),
                                        item.get("Reporter"),
                                    ),
                                    "export_value": item.get("Export Value", 0),
                                    "year": year,
                                }
                            )

                    african_exports.sort(key=lambda x: x["export_value"], reverse=True)
                    return african_exports[:5]

            return []
        except Exception as e:
            logging.error(f"OEC API error: {e}")
            return []


# Global API clients
wb_client = WorldBankAPIClient()
oec_client = OECAPIClient()

# Database reference (will be set by server.py)
db = None


def set_database(database):
    """Set the database reference from server.py"""
    global db
    db = database


@router.post("/calculate-tariff", response_model=TariffCalculationResponse)
async def calculate_comprehensive_tariff(request: TariffCalculationRequest):
    """Calculate complete tariffs with collected and verified tariff data

    Accepts ISO2 (e.g., DZ) or ISO3 (e.g., DZA) country codes
    Supports HS codes from 6 to 12 digits for more precision

    DATA SOURCES:
    - Primary: Collected tariff data (1.18M positions, 54 countries)
    - Fallback: ETL modules if collected data unavailable

    TARIFF PRIORITY ORDER:
    1. National sub-position (8-12 digits) if provided
    2. Country-specific HS6 tariff
    3. Country chapter tariff
    """

    # Find country by ISO3 first, then ISO2 (backward compatibility)
    origin_country = next(
        (c for c in AFRICAN_COUNTRIES if c["iso3"] == request.origin_country.upper()), None
    )
    if not origin_country:
        origin_country = next(
            (c for c in AFRICAN_COUNTRIES if c["code"] == request.origin_country.upper()), None
        )

    dest_country = next(
        (c for c in AFRICAN_COUNTRIES if c["iso3"] == request.destination_country.upper()), None
    )
    if not dest_country:
        dest_country = next(
            (c for c in AFRICAN_COUNTRIES if c["code"] == request.destination_country.upper()), None
        )

    if not origin_country or not dest_country:
        raise HTTPException(
            status_code=400, detail="L'un des pays sélectionnés n'est pas membre de la ZLECAf"
        )

    # Use ISO3 for calculations
    dest_iso3 = dest_country["iso3"]
    # origin_iso3 available if needed for bilateral calculations

    # Clean and normalize HS code
    hs_code_clean = request.hs_code.replace(".", "").replace(" ", "")
    hs6_code = hs_code_clean[:6].zfill(6)
    sector_code = hs6_code[:2]

    tariff_precision = "chapter"
    sub_position_used = None
    sub_position_description = None
    data_source = "etl_fallback"

    # Valeurs par défaut sûres + champs de statut d'honnêteté.
    # line_zlecaf_rate_pct : taux préférentiel réellement présent dans LA LIGNE
    # de la source (jamais un facteur générique calculé) — None si absent,
    # transmis tel quel au garde-fou central qui seul décide de l'appliquer.
    line_zlecaf_rate_pct = None
    dd_available = True  # False -> droit absent de la source (≠ 0 % vérifié)
    duty_status = "PAYABLE"  # PAYABLE | INDICATIVE_MFN | UNAVAILABLE
    duty_notice = None
    is_partial_mfn_aggregate = False

    collected_taxes_detail = []
    collected_fiscal_advantages = []
    collected_admin_formalities = []
    crawled_raw_taxes = []
    other_taxes_detail = {}

    # ============================================================
    # PRIORITY 1: Authentic crawled data (official sources)
    # ============================================================
    if crawled_service.is_loaded():
        crawled_result = crawled_service.lookup(dest_iso3, hs_code_clean)
        if crawled_result:
            # WITS/UNCTAD-TRAINS n'est qu'une source de niveau 3 (agrégat MFN
            # SimpleAverage au SH6, pas une position tarifaire nationale) :
            # ne jamais l'étiqueter comme un crawl national officiel vérifié.
            is_partial_mfn_aggregate = (
                crawled_result.get("source_quality") == "crawled_authentic_partial_national"
            )
            data_source = (
                "crawled_partial_mfn_average" if is_partial_mfn_aggregate else "crawled_authentic"
            )
            if is_partial_mfn_aggregate:
                duty_status = "INDICATIVE_MFN"
            sub_position_used = crawled_result["code_raw"]
            sub_position_description = crawled_result["designation"]
            tariff_precision = (
                "sh6_mfn_average_unverified" if is_partial_mfn_aggregate else "national_position"
            )
            crawled_raw_taxes = crawled_result["taxes"]
            raw_advantages = crawled_result.get("fiscal_advantages", [])
            collected_fiscal_advantages = [
                (
                    item
                    if isinstance(item, dict)
                    else {"description": item, "source": crawled_result["source"]}
                )
                for item in raw_advantages
            ]
            raw_formalities = crawled_result.get("administrative_formalities", [])
            collected_admin_formalities = [
                (
                    item
                    if isinstance(item, dict)
                    else {"description": item, "source": crawled_result["source"]}
                )
                for item in raw_formalities
            ]

            dd_tax = next(
                (
                    t
                    for t in crawled_raw_taxes
                    if t["code"]
                    in ("DD", "DI", "DDDROIT", "ID", "GENERAL", "Droit d'Importation (DI)")
                    or "Import Duty" in t.get("name", "")
                    or "Customs Duty" in t.get("name", "")
                ),
                None,
            )
            if dd_tax and dd_tax.get("rate_pct") is not None:
                normal_rate = dd_tax["rate_pct"] / 100.0
            else:
                # Aucun droit de douane dans la source officielle : ne PAS
                # fabriquer un 0 % vérifié — signaler l'absence de donnée.
                normal_rate = 0.0
                dd_available = False
            if is_partial_mfn_aggregate:
                npf_source = (
                    f"{crawled_result['source']} — moyenne MFN au niveau SH6, "
                    f"source de niveau 3 (agrégateur), non une position tarifaire "
                    f"nationale vérifiée"
                )
            else:
                npf_source = f"Source officielle: {crawled_result['source']}"

            vat_tax = next(
                (
                    t
                    for t in crawled_raw_taxes
                    if t["code"] in ("TVA", "TVA/APTAXE", "VAT")
                    or "TVA" in t.get("name", "").upper()
                    or "VAT" in t.get("name", "").upper()
                    or "Valeur Ajoutée" in t.get("name", "")
                    or "Value Added Tax" in t.get("name", "")
                ),
                None,
            )
            if vat_tax and vat_tax.get("rate_pct") is not None:
                vat_rate = vat_tax["rate_pct"] / 100.0
                vat_source = f"{vat_tax['name']} ({crawled_result['source']})"
            else:
                vat_rate, vat_source = get_vat_rate_for_country(dest_iso3)

            other_taxes_rate = 0.0
            dd_codes = ("DD", "DI", "DDDROIT", "ID", "GENERAL", "Droit d'Importation (DI)")
            for t in crawled_raw_taxes:
                is_dd = (
                    t["code"] in dd_codes
                    or "Import Duty" in t.get("name", "")
                    or "Customs Duty" in t.get("name", "")
                )
                is_vat = (
                    t["code"] in ("TVA", "TVA/APTAXE", "VAT")
                    or "TVA" in t.get("code", "").upper()
                    or "VAT" in t.get("name", "").upper()
                    or "Valeur Ajoutée" in t.get("name", "")
                    or "Value Added Tax" in t.get("name", "")
                )
                is_preferential = t.get("is_preferential", False)
                if not is_dd and not is_vat and not is_preferential:
                    if t.get("rate_pct") is not None:
                        other_taxes_rate += t["rate_pct"] / 100.0
                        other_taxes_detail[t["code"]] = t["rate_pct"]

            collected_taxes_detail = [
                {
                    "tax": t["name"],
                    "rate": t["rate_pct"] if t.get("rate_pct") is not None else 0,
                    "raw_value": t.get("raw_value", ""),
                    "observation": f"Source: {t.get('source', crawled_result['source'])}",
                }
                for t in crawled_raw_taxes
            ]

            # Taux préférentiel réellement présent SUR CETTE LIGNE (jamais un
            # facteur générique calculé) : colonne dédiée du barème source
            # (ex. "AfCFTA" chez SARS/ZAF), si elle existe. None sinon — le
            # garde-fou central décide seul s'il peut être appliqué.
            zlecaf_tax = next(
                (
                    t
                    for t in crawled_raw_taxes
                    if t["code"].upper() in ("AFCFTA", "ZLECAF", "ZLECAF_RATE")
                ),
                None,
            )
            if zlecaf_tax and zlecaf_tax.get("rate_pct") is not None:
                line_zlecaf_rate_pct = zlecaf_tax["rate_pct"]

            # GHA guard: neutraliser la paire synthétique GHA `zlecaf_rate=0.0`/
            # `zlecaf_source="ZLECAf"` détectée dans crawled_data — elle est
            # fabriquée, non sourcée, et ne doit jamais produire une préférence.
            # Ce garde-fou est provisoire ; le nettoyage physique du fichier
            # `backend/data/crawled/GHA_tariffs.json` sera traité en branche
            # séparée (`claude/ghana-zlecaf-neutralization`).
            if (
                dest_iso3 == "GHA"
                and crawled_result.get("zlecaf_rate") == 0.0
                and crawled_result.get("zlecaf_source") == "ZLECAf"
            ):
                line_zlecaf_rate_pct = None

    # ============================================================
    # PRIORITY 2: Collected ETL enriched data
    # ============================================================
    if (
        data_source not in ("crawled_authentic", "crawled_partial_mfn_average")
        and tariff_service.is_loaded()
    ):
        tariff_info = tariff_service.get_tariff_precision_info(dest_iso3, hs_code_clean)
        if tariff_info:
            normal_rate = tariff_info["rate"]
            npf_source = tariff_info["source"]
            tariff_precision = tariff_info["precision"]
            sub_position_used = tariff_info.get("sub_position_code")
            sub_position_description = tariff_info.get("sub_position_description")
            data_source = "collected_verified"

            collected_taxes_detail = tariff_info.get("taxes_detail", [])
            collected_fiscal_advantages = tariff_info.get("fiscal_advantages", [])
            collected_admin_formalities = tariff_info.get("administrative_formalities", [])

            # Taux préférentiel réellement présent sur cette ligne (jamais un
            # facteur générique) — None si absent, transmis au garde-fou central.
            zlecaf_rate_val, _zlecaf_line_source = tariff_service.get_zlecaf_rate(
                dest_iso3, hs6_code
            )
            if zlecaf_rate_val is not None:
                line_zlecaf_rate_pct = zlecaf_rate_val * 100.0

            vat_rate, vat_source = tariff_service.get_vat_rate(dest_iso3)

            if collected_taxes_detail:
                product_other = (
                    sum(
                        t["rate"]
                        for t in collected_taxes_detail
                        if t["tax"] not in ("D.D", "T.V.A")
                    )
                    / 100.0
                )
                other_taxes_rate = product_other
                other_taxes_detail = {
                    t["tax"].lower().replace(".", ""): t["rate"]
                    for t in collected_taxes_detail
                    if t["tax"] not in ("D.D", "T.V.A")
                }
                vat_from_detail = next(
                    (t["rate"] for t in collected_taxes_detail if t["tax"] == "T.V.A"), None
                )
                if vat_from_detail is not None:
                    vat_rate = vat_from_detail / 100.0
            else:
                other_taxes_rate, other_taxes_detail = tariff_service.get_other_taxes(dest_iso3)

    # ============================================================
    # PRIORITY 3: ETL modules (fallback)
    # ============================================================
    if data_source not in (
        "crawled_authentic",
        "crawled_partial_mfn_average",
        "collected_verified",
    ):
        if len(hs_code_clean) > 6:
            rate, description, source = get_sub_position_rate(dest_iso3, hs_code_clean)
            if rate is not None:
                normal_rate = rate
                npf_source = f"Sous-position nationale {dest_iso3} ({hs_code_clean})"
                tariff_precision = "sub_position"
                sub_position_used = hs_code_clean
                sub_position_description = description

        if tariff_precision == "chapter":
            hs6_tariff = get_country_hs6_tariff(dest_iso3, hs6_code)
            if hs6_tariff:
                normal_rate = hs6_tariff["dd"]
                npf_source = f"Tarif SH6 {dest_iso3} ({hs6_code})"
                tariff_precision = "hs6_country"
            else:
                normal_rate, npf_source = get_tariff_rate_for_country(dest_iso3, hs6_code)
                tariff_precision = "chapter"

        # Aucune donnée par ligne disponible à ce niveau de repli (chapitre/SH6
        # générique) : line_zlecaf_rate_pct reste None — pas de facteur
        # générique fabriqué. Le garde-fou central conservera le taux NPF.

        vat_rate, vat_source = get_vat_rate_for_country(dest_iso3)
        other_taxes_rate, other_taxes_detail = get_other_taxes_for_country(dest_iso3)

    # ============================================================
    # GARDE-FOU CENTRAL ZLECAf — SOURCE UNIQUE DE VÉRITÉ.
    # Toutes les préférences ZLECAf passent par resolve_zlecaf_context
    # (services.authentic_tariff_service, déjà présent et testé sur `main`,
    # indépendamment de ce correctif — commit cbc5610d) : union douanière
    # (SACU/EAC/CEMAC/UEMOA, 0 % prioritaire), ratification continentale,
    # calendrier DZA (circulaire DGD 482/2024) et ZAF (newsletter dtic/SARS)
    # sourcés et datés, et pour les autres pays ratifiés : le taux ZLECAf
    # UNIQUEMENT s'il existe sur la ligne (line_zlecaf_rate_pct, jamais
    # calculé) ET si la destination a une preuve d'application réelle
    # (is_active_implementer). Aucun facteur générique n'est jamais appliqué.
    # ============================================================
    from services.authentic_tariff_service import resolve_zlecaf_context

    _zctx = resolve_zlecaf_context(
        dest_iso3,
        origin_country.get("iso3", "") if origin_country else "",
        hs_code_clean,
        round(normal_rate * 100, 6),
        line_zlecaf_rate_pct,
    )
    _eff_dd_pct = _zctx["dd_rate_pct"]
    _preference_rate_verified = (
        _eff_dd_pct is not None
    )  # Flag pour détecter si une préférence vérifiée existe
    zlecaf_preference_applied = bool(_zctx["preference_applied"])
    trade_regime = _zctx["trade_regime"]
    trade_regime_code = _zctx["trade_regime_code"]
    zlecaf_note = _zctx["trade_regime_note"] or _zctx["zlecaf_note"]

    if _eff_dd_pct is None:
        # Éligibilité éventuelle mais aucun barème préférentiel vérifié par
        # ligne : le taux NPF est conservé (jamais un 0 % ou un facteur
        # fabriqué), l'absence de préférence est signalée explicitement.
        _eff_dd_pct = round(normal_rate * 100, 6)
        zlecaf_preference_applied = False
        if not zlecaf_note:
            zlecaf_note = "Préférence ZLECAf non disponible — taux NPF appliqué"

    zlecaf_rate = _eff_dd_pct / 100.0
    zlecaf_source = zlecaf_note or f"Régime {trade_regime}"

    # WITS/UNCTAD-TRAINS : agrégat MFN de niveau 3 — information seulement. Un
    # tel agrégat ne peut JAMAIS produire un droit exigible ni une économie
    # ZLECAf calculée, quel que soit ce que le garde-fou central déciderait
    # par ailleurs (ex. union douanière) : on neutralise toute préférence.
    #
    # Préférence non appliquée : même si un régime est éligible, absence de
    # taux préférentiel vérifié OU non-ratification OU non-activation partenaire
    # signifie zlecaf_response_rate = None — jamais un 0 % ou un NPF copié.
    if is_partial_mfn_aggregate:
        zlecaf_response_rate = None  # API response: pas de préférence (WITS est indicatif)
        zlecaf_rate = normal_rate  # Engine calculation: taux NPF appliqué
        zlecaf_preference_applied = False
        zlecaf_note = (
            "Base WITS/UNCTAD-TRAINS (moyenne MFN au niveau SH6, source de "
            "niveau 3) : information seulement — aucun droit exigible ni "
            "économie ZLECAf calculée."
        )
        zlecaf_source = zlecaf_note
    elif zlecaf_preference_applied:
        # Préférence appliquée : taux applicable (avec ou sans économie effective)
        zlecaf_response_rate = zlecaf_rate
    elif _preference_rate_verified and trade_regime in ("CUSTOMS_UNION", "ZLECAF"):
        # Régime préférentiel vérifié avec un taux (même sans économie
        # effective, ex. SACU 0%→0%) : réponse API montre le taux du régime
        zlecaf_response_rate = zlecaf_rate
    else:
        # Pas de préférence appliquée : aucune résolution de taux préférentiel
        # pour cette ligne — réponse API indique l'absence
        zlecaf_response_rate = None
        zlecaf_rate = normal_rate  # Engine: utilise NPF

    # Statut de la préférence ZLECAf elle-même : DOCUMENTED uniquement quand
    # une source tracée et datée a produit le taux exposé côté API
    # (zlecaf_response_rate is not None — 0.0 est un taux valide, ex. union
    # douanière à 0 %, et ne doit pas être confondu avec une absence) ;
    # NOT_AVAILABLE sinon — jamais déduit d'un 0 % ou d'un taux NPF recopié.
    zlecaf_status = "DOCUMENTED" if zlecaf_response_rate is not None else "NOT_AVAILABLE"

    # Droit de douane absent de la source : la valeur 0 n'est pas un taux
    # vérifié — signaler explicitement l'absence de donnée plutôt qu'un 0 %.
    if not dd_available:
        duty_status = "UNAVAILABLE"
        duty_notice = (
            "Aucun droit de douane trouvé dans la source officielle pour cette "
            "position : la valeur 0 affichée traduit une absence de donnée, non "
            "un taux 0 % vérifié."
        )

    # Source for display — "Tarif officiel" ne doit jamais qualifier un agrégat
    # de niveau 3 (WITS/TRAINS) : npf_source porte déjà l'avertissement dans ce cas.
    if is_partial_mfn_aggregate:
        rate_source = npf_source
    else:
        rate_source = f"Tarif officiel {dest_iso3} - {npf_source}"

    # Transition period by sector
    tariff_corrections = get_tariff_corrections()
    transition_periods = tariff_corrections.get("transition_periods", {})
    transition_period = transition_periods.get(sector_code, "immediate")

    # ============================================================
    # DÉTAIL COMPLET des droits et taxes — MOTEUR UNIQUE (NPF vs ZLECAf)
    # Chaque taxe est calculée sur SA base déclarée (assiette propre au pays) ;
    # à défaut, méthode nationale par défaut. Source unique de vérité : tous les
    # montants agrégés, le détail par taxe et les journaux en dérivent.
    # ============================================================
    from services.tax_computation import build_journal, compute_dual_breakdown

    _engine_lines: List[Dict[str, Any]] = []
    if crawled_raw_taxes:
        for t in crawled_raw_taxes:
            if t.get("rate_pct") is None:
                continue
            _engine_lines.append(
                {
                    "code": t.get("code", ""),
                    "name": t.get("name", t.get("code", "")),
                    "rate_pct": t["rate_pct"],
                    "base": t.get("base", ""),
                    "source": t.get("source", npf_source),
                }
            )
    elif collected_taxes_detail:
        for t in collected_taxes_detail:
            if t.get("rate") is None:
                continue
            _engine_lines.append(
                {
                    "code": t.get("tax", ""),
                    "name": t.get("tax", ""),
                    "rate_pct": t["rate"],
                    "base": "",
                    "source": t.get("observation", npf_source),
                }
            )
    else:
        _engine_lines.append(
            {
                "code": "DD",
                "name": "Droit de douane",
                "rate_pct": round(normal_rate * 100, 4),
                "base": "CIF",
                "source": npf_source,
            }
        )
        for _k, _rp in (other_taxes_detail or {}).items():
            if _k == "other" or not isinstance(_rp, (int, float)) or _rp == 0:
                continue
            _engine_lines.append(
                {
                    "code": _k.upper(),
                    "name": _k.upper(),
                    "rate_pct": _rp,
                    "base": "CIF",
                    "source": npf_source,
                }
            )
        _engine_lines.append(
            {
                "code": "TVA",
                "name": "Taxe sur la valeur ajoutée",
                "rate_pct": round(vat_rate * 100, 4),
                "base": "",
                "source": vat_source,
            }
        )

    if not _engine_lines:
        _engine_lines.append(
            {
                "code": "DD",
                "name": "Droit de douane",
                "rate_pct": round(normal_rate * 100, 4),
                "base": "CIF",
                "source": npf_source,
            }
        )

    # DZA : le DAPS est exonéré pour les listes (A)/(B) non gelées avec un
    # partenaire ZLECAf actif (circulaire 482/2024, partie II-2 + art. 2 de
    # la loi de finances complémentaire 2018) — provision distincte du
    # calendrier de démantèlement du DD, donc le DAPS doit être retiré du
    # détail envoyé au moteur fiscal, pas seulement du taux DD affiché.
    if dest_iso3 == "DZA":
        from services.zlecaf_schedule_dza import daps_exempt

        if daps_exempt(hs_code_clean, origin_country.get("iso3", "") if origin_country else ""):
            _engine_lines = [
                ln for ln in _engine_lines if str(ln.get("code", "")).upper() != "DAPS"
            ]

    legal_refs = {
        "cif": {
            "ref": "Incoterms 2020 - CIF",
            "url": "https://iccwbo.org/resources-for-business/incoterms-rules/incoterms-2020/",
        },
        "dd": {"ref": f"Tarif douanier {dest_iso3}", "url": None},
        "rs": {"ref": "Règlement UEMOA 02/97/CM", "url": None},
        "pcs": {"ref": "Règlement UEMOA 01/2019", "url": None},
        "cedeao": {"ref": "Protocole CEDEAO A/P1/1/03", "url": None},
        "tci": {"ref": "Règlement CEMAC 02/01", "url": None},
        "vat": {"ref": f"Code Général des Impôts {dest_iso3}", "url": None},
        "zlecaf": {
            "ref": "Accord ZLECAf Art. 8",
            "url": "https://au.int/en/treaties/agreement-establishing-african-continental-free-trade-area",
        },
        "daps": {"ref": f"Décret exécutif - DAPS {dest_iso3}", "url": None},
        "prct": {"ref": f"Loi de Finances {dest_iso3}", "url": None},
        "tcs": {"ref": f"Réglementation sanitaire {dest_iso3}", "url": None},
    }

    # Taux de change (USD -> devise locale) — récupéré ici car requis AUSSI pour
    # les plafonds spécifiques exprimés en devise locale (ex. RI CEMAC ≤ 15 000 XAF).
    from currencies.service import get_by_country as _get_currency
    from exchange_rates import get_service as _get_fx_service
    from services.tax_computation import parse_cap as _parse_cap

    _ccy = _get_currency(dest_country.get("code", ""))
    _rate_obj = None
    if _ccy:
        try:
            _rate_obj = _get_fx_service().get_rate("USD", _ccy.currency_code)
        except Exception as _fx_err:  # réseau/provider indisponible
            logger.warning(f"Taux de change indisponible ({_ccy.currency_code}): {_fx_err}")
    _fx_rate = _rate_obj.rate if (_rate_obj and _rate_obj.rate) else None

    # Plafonds spécifiques convertis dans la devise du calcul (USD) : 1 USD =
    # _fx_rate <devise locale> => plafond_usd = plafond_local / _fx_rate.
    _caps: Dict[str, float] = {}
    if _fx_rate:
        for _ln in _engine_lines:
            _cap = _parse_cap(_ln.get("base"))
            if _cap and _ccy and _cap["currency"] == _ccy.currency_code:
                _caps[str(_ln.get("code", "")).upper()] = round(_cap["amount"] / _fx_rate, 2)

    _dual = compute_dual_breakdown(
        request.value,
        _engine_lines,
        npf_dd_rate_pct=round(normal_rate * 100, 4),
        zlecaf_dd_rate_pct=round(zlecaf_rate * 100, 4),
        caps=_caps,
    )
    taxes_breakdown = _dual["breakdown"]
    taxes_summary = _dual["summary"]
    _npf = taxes_summary["npf"]
    _zlc = taxes_summary["zlecaf"]

    # --- Champs agrégés dérivés du moteur (cohérence garantie) ---
    normal_customs = _npf["droit_douane"]
    zlecaf_customs = _zlc["droit_douane"]
    other_taxes_amount = _npf["autres_taxes"]
    zlecaf_other_amount = _zlc["autres_taxes"]
    normal_vat_amount = _npf["tva"]
    zlecaf_vat_amount = _zlc["tva"]
    normal_total = _npf["cout_total"]
    zlecaf_total = _zlc["cout_total"]

    # Aucune préférence ZLECAf traçable (zlecaf_response_rate=None) : aucune
    # économie n'a été calculée, donc aucune ne doit être exposée. Un 0
    # affirmerait à tort qu'un calcul préférentiel a eu lieu et n'a rien
    # trouvé à réduire — au lieu qu'aucun calcul préférentiel n'ait eu lieu.
    if zlecaf_response_rate is None:
        savings = None
        savings_percentage = None
        total_savings_with_taxes = None
        total_savings_percentage = None
    else:
        savings = taxes_summary["economie_droits"]
        savings_percentage = (savings / normal_customs) * 100 if normal_customs > 0 else 0
        total_savings_with_taxes = taxes_summary["economie_totale"]
        total_savings_percentage = (
            (total_savings_with_taxes / normal_total) * 100 if normal_total > 0 else 0
        )

    # Montants par prélèvement (champs dédiés de la réponse).
    def _sum_codes(regime_key: str, codes: set) -> float:
        return round(
            sum(
                b[f"amount_{regime_key}"]
                for b in taxes_breakdown
                if str(b["code"]).upper() in codes
            ),
            2,
        )

    _normal_tax_amounts = {
        "rs": _sum_codes("npf", {"RS"}),
        "pcs": _sum_codes("npf", {"PCS"}),
        "cedeao": _sum_codes("npf", {"PCC", "PC"}),
        "tci": _sum_codes("npf", {"TCI"}),
    }
    _zlecaf_tax_amounts = {
        "rs": _sum_codes("zlecaf", {"RS"}),
        "pcs": _sum_codes("zlecaf", {"PCS"}),
        "cedeao": _sum_codes("zlecaf", {"PCC", "PC"}),
        "tci": _sum_codes("zlecaf", {"TCI"}),
    }

    # Journaux dérivés du même détail → parfaitement cohérents avec les totaux.
    normal_journal = build_journal(request.value, taxes_breakdown, "npf", legal_refs)
    zlecaf_journal = build_journal(request.value, taxes_breakdown, "zlecaf", legal_refs)

    # ============================================================
    # Bi-devise : montants en USD (valeur du calcul) ET en monnaie locale du
    # pays de destination, via le sous-module de change (banque). Dégradation
    # propre si le taux est indisponible (montants en USD uniquement).
    # ============================================================
    from services.tax_computation import localize_breakdown

    currency_block: Optional[Dict[str, Any]] = None
    if _ccy:
        if _fx_rate:
            _r = _fx_rate
            # _dual a été recalculé plafonds inclus ; on localise le détail courant.
            _loc = localize_breakdown({"breakdown": taxes_breakdown, "summary": taxes_summary}, _r)
            taxes_breakdown = _loc["breakdown"]  # enrichi des montants locaux
            currency_block = {
                "local_code": _ccy.currency_code,
                "local_name": _ccy.currency_name_fr,
                "local_symbol": _ccy.currency_symbol,
                "usd_to_local_rate": round(_r, 6),
                "rate_source": _rate_obj.source,
                "rate_as_of": _rate_obj.timestamp.isoformat(),
                "available": True,
                "value_usd": round(request.value, 2),
                "value_local": round(request.value * _r, 2),
                "summary_local": _loc["summary_local"],
            }
        else:
            currency_block = {
                "local_code": _ccy.currency_code,
                "local_name": _ccy.currency_name_fr,
                "local_symbol": _ccy.currency_symbol,
                "usd_to_local_rate": None,
                "available": False,
                "note": "Taux de change indisponible — montants en USD uniquement.",
                "value_usd": round(request.value, 2),
            }

    # Rules of origin - Use official AfCFTA Annex II rules (single source of
    # truth shared with the dedicated /rules-of-origin/{hs_code} endpoint;
    # see routes/rules_of_origin.py for why this replaced the formerly
    # separate, drifting etl.afcfta_rules_of_origin dataset).
    from routes.rules_of_origin import get_rule_of_origin

    roo_data = get_rule_of_origin(hs6_code, "fr")

    # Build rules_of_origin object for calculator
    if roo_data.get("status") == "UNKNOWN":
        rules = {
            "rule": "Règle non définie",
            "requirement": "Consulter le Secrétariat ZLECAf",
            "regional_content": 0,
            "status": "UNKNOWN",
            "source": "AfCFTA Annex II - Appendix IV",
        }
    else:
        primary_rule = roo_data.get("primary_rule", {})
        rule_name = primary_rule.get("name", "")
        rule_code = primary_rule.get("code", "")
        # None here means "not applicable" (e.g. CTH/CTSH/SP rules have no
        # percentage threshold in the dataset) - never substitute a
        # fabricated number, only adjust how it's rendered below.
        regional_content = roo_data.get("regional_content")
        status = roo_data.get("status", "AGREED")
        chapter_desc = roo_data.get("chapter_description", "")

        # Build requirement based on rule type
        if rule_code == "WO":
            requirement = "Entièrement obtenu dans la ZLECAf (100%)"
        elif rule_code in ["CTH", "CTSH"]:
            requirement = f"Changement de position tarifaire ({rule_code})"
            if regional_content is not None:
                requirement += f" avec {regional_content}% minimum de contenu régional"
        elif rule_code == "VA":
            requirement = f"{regional_content}% minimum de valeur ajoutée africaine"
        elif rule_code == "SP":
            requirement = "Processus spécifique requis"
            if regional_content is not None:
                requirement += f" avec {regional_content}% minimum de contenu régional"
        else:
            requirement = (
                f"{regional_content}% valeur ajoutée africaine"
                if regional_content is not None
                else "Consulter le Secrétariat ZLECAf pour le seuil applicable"
            )

        # Add alternative if available
        alt_rule = roo_data.get("alternative_rule", {})
        if alt_rule:
            requirement += f" OU {alt_rule.get('name', '')}"

        rules = {
            "rule": rule_name,
            "rule_code": rule_code,
            "requirement": requirement,
            "regional_content": regional_content,
            "status": status,
            "status_label": "Convenu" if status == "AGREED" else "En négociation",
            "chapter_description": chapter_desc,
            "notes": roo_data.get("notes", ""),
            "source": "AfCFTA Protocol on Trade in Goods - Annex II, Appendix IV",
            "reference_url": "https://au.int/sites/default/files/treaties/36437-ax-AfCFTA_RULES_OF_ORIGIN_MANUAL.pdf",
        }

    # Get top African producers
    top_producers = await oec_client.get_top_producers(request.hs_code)

    # Get country economic data
    wb_data = await wb_client.get_country_data([origin_country["wb_code"], dest_country["wb_code"]])

    # Check if alternative sub-positions exist for this HS6
    if tariff_service.is_loaded() and data_source == "collected_verified":
        collected_subs = tariff_service.get_sub_positions_for_hs6(dest_iso3, hs6_code)
        if collected_subs:
            sub_positions_available = collected_subs
            rates = [sp.get("dd", 0) / 100.0 for sp in collected_subs]
            has_varying = len(set(rates)) > 1
            min_rate = min(rates) if rates else 0
            max_rate = max(rates) if rates else 0
        else:
            sub_positions_available = get_all_sub_positions(dest_iso3, hs6_code)
            has_varying, min_rate, max_rate = has_varying_rates(dest_iso3, hs6_code)
    else:
        sub_positions_available = get_all_sub_positions(dest_iso3, hs6_code)
        has_varying, min_rate, max_rate = has_varying_rates(dest_iso3, hs6_code)

    # Build warning and details if varying rates
    rate_warning = None
    sub_positions_details = None

    if has_varying and len(sub_positions_available) > 0:
        rate_warning = {
            "has_variation": True,
            "message_fr": f"⚠️ Attention: Ce code SH6 ({hs6_code}) a des taux de droits de douane variables selon les sous-positions nationales. Le taux peut varier de {min_rate*100:.1f}% à {max_rate*100:.1f}%.",
            "message_en": f"⚠️ Warning: This HS6 code ({hs6_code}) has varying duty rates depending on national sub-headings. Rates range from {min_rate*100:.1f}% to {max_rate*100:.1f}%.",
            "min_rate": min_rate,
            "max_rate": max_rate,
            "min_rate_pct": f"{min_rate*100:.1f}%",
            "max_rate_pct": f"{max_rate*100:.1f}%",
            "rate_used": normal_rate,
            "rate_used_pct": f"{normal_rate*100:.1f}%",
            "recommendation_fr": "Pour un calcul plus précis, veuillez spécifier la sous-position nationale complète (8-12 chiffres).",
            "recommendation_en": "For a more accurate calculation, please specify the complete national sub-heading (8-12 digits).",
        }
        sub_positions_details = sub_positions_available

    # Create complete response with all taxes
    result = TariffCalculationResponse(
        origin_country=request.origin_country,
        destination_country=request.destination_country,
        hs_code=request.hs_code,
        hs6_code=hs6_code,
        value=request.value,
        # Customs tariffs
        normal_tariff_rate=normal_rate,
        normal_tariff_amount=round(normal_customs, 2),
        zlecaf_tariff_rate=zlecaf_response_rate,
        zlecaf_tariff_amount=round(zlecaf_customs, 2) if zlecaf_response_rate is not None else None,
        normal_vat_rate=vat_rate,
        normal_vat_amount=round(normal_vat_amount, 2),
        normal_statistical_fee=_normal_tax_amounts.get("rs", 0),
        normal_community_levy=_normal_tax_amounts.get("pcs", 0),
        normal_ecowas_levy=_normal_tax_amounts.get("cedeao", 0),
        normal_other_taxes_total=round(other_taxes_amount, 2),
        normal_total_cost=round(normal_total, 2),
        zlecaf_vat_rate=vat_rate,
        zlecaf_vat_amount=round(zlecaf_vat_amount, 2),
        zlecaf_statistical_fee=_zlecaf_tax_amounts.get("rs", 0),
        zlecaf_community_levy=_zlecaf_tax_amounts.get("pcs", 0),
        zlecaf_ecowas_levy=_zlecaf_tax_amounts.get("cedeao", 0),
        zlecaf_other_taxes_total=round(zlecaf_other_amount, 2),
        zlecaf_total_cost=round(zlecaf_total, 2),
        # Savings (None si aucune préférence ZLECAf traçable)
        savings=round(savings, 2) if savings is not None else None,
        savings_percentage=round(savings_percentage, 1) if savings_percentage is not None else None,
        total_savings_with_taxes=(
            round(total_savings_with_taxes, 2) if total_savings_with_taxes is not None else None
        ),
        total_savings_percentage=(
            round(total_savings_percentage, 1) if total_savings_percentage is not None else None
        ),
        # Calculation journal and traceability
        normal_calculation_journal=normal_journal,
        zlecaf_calculation_journal=zlecaf_journal,
        computation_order_ref="Codes douaniers nationaux + Directives CEDEAO/UEMOA/CEMAC/EAC/SACU",
        last_verified="2025-01",
        confidence_level=(
            "high"
            if data_source == "collected_verified"
            or tariff_precision in ["sub_position", "hs6_country", "hs6_collected"]
            else "medium"
        ),
        tariff_precision=tariff_precision,
        sub_position_used=sub_position_used,
        sub_position_description=sub_position_description,
        has_varying_sub_positions=has_varying,
        available_sub_positions_count=len(sub_positions_available),
        rate_warning=rate_warning,
        sub_positions_details=sub_positions_details,
        taxes_detail=collected_taxes_detail if collected_taxes_detail else None,
        taxes_breakdown=taxes_breakdown,
        taxes_summary=taxes_summary,
        currency=currency_block,
        fiscal_advantages=collected_fiscal_advantages if collected_fiscal_advantages else None,
        administrative_formalities=(
            collected_admin_formalities if collected_admin_formalities else None
        ),
        country_enrichment=get_country_enrichment(dest_iso3),
        data_source=data_source,
        duty_status=duty_status,
        duty_notice=duty_notice,
        dd_available=dd_available,
        trade_regime=trade_regime,
        trade_regime_code=trade_regime_code,
        zlecaf_preference_applied=zlecaf_preference_applied,
        zlecaf_note=zlecaf_note,
        zlecaf_status=zlecaf_status,
        rules_of_origin=rules,
        top_african_producers=top_producers,
        origin_country_data=wb_data.get(origin_country["wb_code"], {}),
        destination_country_data=wb_data.get(dest_country["wb_code"], {}),
    )

    if db is not None:
        await db.comprehensive_calculations.insert_one(result.dict())

    return result
