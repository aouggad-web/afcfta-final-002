"""
Enrichissement ISIC (Rev.4) & IDSB du module Opportunités
=========================================================

Ce service rattache une opportunité commerciale (code SH) à sa **division
industrielle ISIC Rev.4**, puis confronte l'**offre industrielle réelle** de
l'origine et la **demande réelle** de la destination à partir des données UNIDO
**IDSB** (Industrial Demand-Supply Balance) et **INDSTAT** — une véritable
lecture offre-demande, pas un score inventé.

Principe « zéro fabrication »
----------------------------
Aucun indicateur n'est estimé ici. Toutes les valeurs proviennent de sources
réelles déjà embarquées :

  • Classification ISIC↔SH : correspondance officielle UNSD portée par
    ``services.unido_hs_mapping`` (divisions manufacturières C, labels FR/EN,
    chaîne intrant → procédé, produits SH4 exportables).
  • Offre & demande industrielles : ``etl.isic4_idsb_data`` — UNIDO IDSB
    (Output, Imports World, Exports World, Apparent Consumption) + INDSTAT
    (Value added, Employees, Establishments), au niveau ISIC 4 chiffres, pour
    20 pays africains (2018-2024). Un pays hors couverture, ou une division sans
    relevé, renvoie ``available: False`` — jamais une estimation.
  • Demande fine (optionnelle) : imports OEC du marché destination pour le SH
    exact, passés par l'appelant (``market_potential_usd``).

Un produit hors section manufacturière ISIC (agriculture/extraction primaire)
renvoie ``available: False`` : ce module éclaire la transformation industrielle,
la production primaire étant couverte ailleurs (FAOSTAT/USGS).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from etl import isic4_idsb_data as idsb
from services import unido_hs_mapping as isic_map

logger = logging.getLogger(__name__)

# Indicateurs IDSB/INDSTAT (USD) additifs à l'échelle d'une division ISIC.
_SUPPLY_FIELDS = ("output_usd", "output_usd_official", "value_added_usd", "exports_world_usd")
_DEMAND_FIELDS = ("apparent_consumption_usd", "imports_world_usd")
_COUNT_FIELDS = ("employees", "establishments")


def _norm(hs_code: Optional[str]) -> str:
    if not hs_code:
        return ""
    return "".join(ch for ch in str(hs_code) if ch.isdigit())


def _division_subsectors(country_iso3: str, division: str) -> List[Dict]:
    """Sous-secteurs ISIC 4 chiffres d'une division pour un pays (données IDSB réelles)."""
    summary = idsb.get_country_isic4_summary(country_iso3)
    if not summary:
        return []
    return [s for s in summary.get("sectors", []) if str(s.get("isic4", "")).startswith(division)]


def _aggregate(subsectors: List[Dict], fields) -> Dict[str, Dict]:
    """
    Agrège (somme) un indicateur additif sur les sous-secteurs d'une division, en
    prenant pour chaque sous-secteur sa dernière année disponible. Retourne, par
    champ, la somme, l'étendue d'années réellement utilisées, le nombre de
    sous-secteurs contributeurs et la présence de statistiques officielles.
    """
    out: Dict[str, Dict] = {}
    for field in fields:
        total = 0.0
        years: List[int] = []
        n = 0
        official = False
        for s in subsectors:
            cell = (s.get("indicators") or {}).get(field)
            if not cell or cell.get("value") is None:
                continue
            total += float(cell["value"])
            years.append(int(cell["year"]))
            n += 1
            if cell.get("data_nature") == "OFFICIAL_STATISTICS":
                official = True
        if n:
            out[field] = {
                "value": round(total, 1),
                "subsectors_counted": n,
                "year_min": min(years),
                "year_max": max(years),
                "has_official": official,
            }
    return out


def _industrial_base(origin_iso3: str, division: str, fr: bool) -> Dict:
    """
    Base industrielle RÉELLE de l'origine dans la division (UNIDO IDSB/INDSTAT) :
    production, valeur ajoutée, exports, emploi, plus les 5 principaux
    sous-secteurs par production. ``available: False`` hors couverture.
    """
    iso3 = (origin_iso3 or "").strip().upper()
    if not idsb.is_country_covered(iso3):
        return {"available": False, "reason": "country_not_in_unido_idsb_coverage"}

    subsectors = _division_subsectors(iso3, division)
    supply = _aggregate(subsectors, _SUPPLY_FIELDS)
    counts = _aggregate(subsectors, _COUNT_FIELDS)
    if not supply and not counts:
        return {"available": False, "reason": "no_division_data"}

    # Production de référence : Output IDSB, à défaut Output officiel INDSTAT.
    output = supply.get("output_usd") or supply.get("output_usd_official")

    # 5 principaux sous-secteurs par production (réels, avec libellé).
    def _sub_output(s):
        ind = s.get("indicators") or {}
        cell = ind.get("output_usd") or ind.get("output_usd_official")
        return (cell or {}).get("value") or 0

    top = sorted(
        (s for s in subsectors if _sub_output(s) > 0), key=_sub_output, reverse=True
    )[:5]
    top_subsectors = [
        {
            "isic4": s["isic4"],
            "label": s.get("isic_description"),
            "output_usd": _sub_output(s),
        }
        for s in top
    ]

    return {
        "available": True,
        "output_usd": (output or {}).get("value"),
        "value_added_usd": supply.get("value_added_usd", {}).get("value"),
        "exports_world_usd": supply.get("exports_world_usd", {}).get("value"),
        "employees": counts.get("employees", {}).get("value"),
        "establishments": counts.get("establishments", {}).get("value"),
        "year_range": _year_range(supply, counts),
        "has_official": any(v.get("has_official") for v in {**supply, **counts}.values()),
        "top_subsectors": top_subsectors,
        "source": "UNIDO IDSB + INDSTAT (ISIC Rev.4)",
    }


def _market_demand(destination_iso3: str, division: str) -> Dict:
    """
    Demande RÉELLE de la destination dans la division (UNIDO IDSB) : consommation
    apparente et imports mondiaux. ``available: False`` hors couverture.
    """
    iso3 = (destination_iso3 or "").strip().upper()
    if not idsb.is_country_covered(iso3):
        return {"available": False, "reason": "country_not_in_unido_idsb_coverage"}

    demand = _aggregate(_division_subsectors(iso3, division), _DEMAND_FIELDS)
    if not demand:
        return {"available": False, "reason": "no_division_data"}

    return {
        "available": True,
        "apparent_consumption_usd": demand.get("apparent_consumption_usd", {}).get("value"),
        "imports_world_usd": demand.get("imports_world_usd", {}).get("value"),
        "year_range": _year_range(demand),
        "source": "UNIDO IDSB (ISIC Rev.4)",
    }


def _year_range(*aggs: Dict) -> Optional[str]:
    years: List[int] = []
    for agg in aggs:
        for v in agg.values():
            years.extend([v["year_min"], v["year_max"]])
    if not years:
        return None
    lo, hi = min(years), max(years)
    return str(lo) if lo == hi else f"{lo}–{hi}"


def _balance(base: Dict, demand: Dict, market_potential_usd: Optional[float], fr: bool) -> Dict:
    """Verdict offre-demande, fonction TRANSPARENTE de faits réels (jamais un score opaque)."""
    # Offre mesurée = toute preuve industrielle réelle (production, valeur ajoutée,
    # exports, emploi, établissements), pas seulement l'Output.
    has_supply = bool(base.get("available")) and any(
        base.get(k)
        for k in ("output_usd", "value_added_usd", "exports_world_usd", "employees", "establishments")
    )
    # Demande mesurée = consommation apparente ou imports UNIDO, ou imports OEC du SH exact.
    has_demand = (
        bool(demand.get("available"))
        and any(demand.get(k) for k in ("apparent_consumption_usd", "imports_world_usd"))
    ) or (market_potential_usd is not None and market_potential_usd > 0)
    origin_exports = bool(base.get("available") and base.get("exports_world_usd"))

    if has_supply and has_demand:
        verdict = "supply_and_demand"
        text = (
            "Activité industrielle mesurée à l'origine ET demande mesurée à "
            "destination : appariement offre-demande favorable"
            + (
                ", l'origine exportant déjà cette division."
                if origin_exports
                else " (l'origine ne déclare pas encore d'exports sur la division)."
            )
            if fr
            else "Industrial activity measured at origin AND demand measured at "
            "destination: favourable supply–demand match"
            + (
                ", with the origin already exporting this division."
                if origin_exports
                else " (origin reports no exports in the division yet)."
            )
        )
    elif has_demand and not has_supply:
        verdict = "demand_without_supply"
        text = (
            "Demande mesurée à destination, mais aucune production industrielle "
            "UNIDO mesurée à l'origine sur cette division : débouché réel, "
            "capacité d'offre à établir."
            if fr
            else "Demand measured at destination, but no UNIDO industrial output "
            "measured at origin in this division: real outlet, supply capacity to "
            "be established."
        )
    elif has_supply and not has_demand:
        verdict = "supply_without_demand"
        text = (
            "Production mesurée à l'origine, mais aucune demande UNIDO/OEC mesurée "
            "à destination : capacité présente, débouché à confirmer."
            if fr
            else "Output measured at origin, but no UNIDO/OEC demand measured at "
            "destination: capacity present, outlet to confirm."
        )
    else:
        verdict = "insufficient_data"
        text = (
            "Ni offre ni demande industrielles mesurées pour cette paire dans la "
            "couverture UNIDO — aucun appariement à évaluer."
            if fr
            else "Neither industrial supply nor demand measured for this pair "
            "within UNIDO coverage — no match to assess."
        )

    return {
        "verdict": verdict,
        "supply_measured": has_supply,
        "demand_measured": has_demand,
        "origin_exports_division": origin_exports,
        "hs_import_demand_usd": market_potential_usd if (market_potential_usd or 0) > 0 else None,
        "interpretation": text,
    }


def _diversification_products(isic_code: str, hs_code: str, limit: int = 8) -> List[Dict]:
    """Autres SH4 exportables de la même division ISIC (même intrant/procédé)."""
    current = _norm(hs_code)[:4]
    products = isic_map.products_for_isic(isic_code)
    return [
        {"hs4": code, "label": label}
        for code, label in products.items()
        if code != current
    ][:limit]


class ISIC4IDSBOpportunityService:
    """Rattache une opportunité à sa division ISIC et confronte offre/demande réelles UNIDO."""

    def get_isic4_for_hs(self, hs_code: str) -> Optional[str]:
        """Division ISIC Rev.4 manufacturière du produit (la plus précise), ou None."""
        codes = isic_map.isic_for_hs(hs_code)
        return codes[0] if codes else None

    def assess_opportunity_by_sector(
        self,
        hs_code: str,
        origin: str,
        destination: str,
        market_potential: Optional[float] = None,
        lang: str = "fr",
    ) -> Dict:
        """
        Analyse ISIC4 + IDSB d'une opportunité bilatérale. ``available: False`` si
        le produit n'appartient à aucune division manufacturière ISIC.
        """
        fr = lang != "en"
        isic4 = self.get_isic4_for_hs(hs_code)
        if not isic4:
            return {
                "available": False,
                "reason": "not_manufacturing",
                "note": (
                    "Produit hors section manufacturière ISIC (production primaire "
                    "agricole ou extractive) — analyse industrielle non applicable."
                    if fr
                    else "Product outside the ISIC manufacturing section (primary "
                    "agricultural or extractive production) — industrial analysis "
                    "not applicable."
                ),
            }

        transform = isic_map.transformation_for_isic(isic4)
        precise_input = isic_map.input_for_hs4(hs_code, fallback=transform.get("input"))
        product_label = isic_map.product_label(hs_code)

        base = _industrial_base(origin, isic4, fr)
        demand = _market_demand(destination, isic4)
        balance = _balance(base, demand, market_potential, fr)

        return {
            "available": True,
            "hs_code": hs_code,
            "origin": origin,
            "destination": destination,
            "isic4": {
                "code": isic4,
                "label": transform.get("isic_label_fr" if fr else "isic_label_en"),
            },
            "product_label": product_label,
            "transformation_chain": {
                "input": precise_input,
                "process": transform.get("process"),
                "output": product_label
                or transform.get("isic_label_fr" if fr else "isic_label_en"),
            },
            "industrial_base": base,
            "market_demand": demand,
            "demand_supply_balance": balance,
            "diversification_products": _diversification_products(isic4, hs_code),
            "coverage": {
                "origin_in_idsb": idsb.is_country_covered(origin),
                "destination_in_idsb": idsb.is_country_covered(destination),
                "covered_countries": idsb.list_covered_countries(),
            },
            "sources": {
                "classification": (
                    "UNSD — Correspondance codes SH ↔ ISIC Rev.4"
                    if fr
                    else "UNSD — HS ↔ ISIC Rev.4 correspondence"
                ),
                "industrial_data": "UNIDO Statistics — IDSB + INDSTAT (ISIC Rev.4, 2018-2024)",
            },
        }


_service_instance: Optional[ISIC4IDSBOpportunityService] = None


def get_isic_idsb_service() -> ISIC4IDSBOpportunityService:
    """Instance partagée (le service est sans état)."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ISIC4IDSBOpportunityService()
    return _service_instance
