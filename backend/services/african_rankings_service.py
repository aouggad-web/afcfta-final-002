"""
Classement africain des indices majeurs (pays membres de la ZLECAf).

Le rang d'un pays est calculé parmi les pays africains qui publient l'indice
pour la MÊME année (ou la même édition) que la valeur affichée sur sa fiche :
une valeur 2022 n'est jamais comparée à des valeurs 2025. Les ex aequo
partagent leur rang (classement « 1, 2, 2, 4 »).

1 = valeur la plus élevée, sauf pour l'inflation, le chômage et la dette
publique, où 1 = la plus faible.

Sources : Banque mondiale (WDI, dataset auto-actualisé), FMI (WEO), PNUD
(RDH 2025) et Banque mondiale (LPI 2023, dimension infrastructure).
"""

from datetime import datetime
from typing import Dict, Optional

from constants import AFRICAN_COUNTRIES
from country_data import REAL_COUNTRY_DATA
from data_loader import load_infrastructure_ranking
from services import imf_projections_service, wb_macro_service

# indice -> (clé du service BM, plus élevé = mieux). Année : la dernière
# disponible pour le pays, comme sur sa fiche.
_WB_INDICES = {
    "gdp": ("gdp_usd", True),
    "gdp_per_capita": ("gdp_per_capita_usd", True),
    "population": ("population", True),
    "gdp_growth": ("gdp_growth_percent", True),
    "inflation": ("inflation_percent", False),
    "unemployment": ("unemployment_percent", False),
    "life_expectancy": ("life_expectancy_years", True),
    "internet_users": ("internet_users_pct", True),
    "electricity_access": ("electricity_access_pct", True),
}

# indice -> (série WEO, année relative à l'année en cours, plus élevé = mieux)
_IMF_INDICES = {
    "gdp_growth_projection": ("gdp_growth", 0, True),
    "gov_debt": ("gov_debt", -1, False),
    "fiscal_balance": ("fiscal_balance", -1, True),
    "current_account": ("current_account", -1, True),
}

# IDH du dataset Profils Pays : PNUD, RDH 2025 (année de référence 2023).
_HDI_YEAR = 2023
# Seule l'édition 2023 du LPI est classée : les éditions antérieures
# (2018, 2016) ne sont pas comparables.
_LPI_EDITION = 2023


def _rank(values: Dict[str, float], iso3: str, higher_is_better: bool, year: int) -> Optional[Dict]:
    """Rang de ``iso3`` parmi ``values`` ({iso3: valeur}), ou None s'il n'y figure pas."""
    value = values.get(iso3)
    if value is None:
        return None
    ahead = sum(1 for v in values.values() if (v > value if higher_is_better else v < value))
    return {"rank": ahead + 1, "total": len(values), "year": year}


def get_rankings(iso3: str) -> Dict[str, Dict]:
    """
    Rangs africains d'un pays : ``{indice: {"rank", "total", "year"}}``.
    Un indice sans valeur pour ce pays est absent — jamais un rang inventé.
    """
    iso3 = (iso3 or "").strip().upper()
    members = [c["iso3"] for c in AFRICAN_COUNTRIES]
    out: Dict[str, Dict] = {}

    for name, (key, higher) in _WB_INDICES.items():
        own = wb_macro_service.get_series(iso3, key)
        if not own:
            continue
        year = max(own)
        values = {}
        for m in members:
            v = wb_macro_service.get_series(m, key).get(year)
            if v is not None:
                values[m] = v
        ranked = _rank(values, iso3, higher, year)
        if ranked:
            out[name] = ranked

    current_year = datetime.now().year
    for name, (key, offset, higher) in _IMF_INDICES.items():
        year = current_year + offset
        values = {}
        for m in members:
            v = ((imf_projections_service.get_projections(m) or {}).get(key) or {}).get(str(year))
            if v is not None:
                values[m] = v
        ranked = _rank(values, iso3, higher, year)
        if ranked:
            out[name] = ranked

    hdi = {
        m: REAL_COUNTRY_DATA[m]["development_index"]
        for m in members
        if REAL_COUNTRY_DATA.get(m, {}).get("development_index") is not None
    }
    ranked = _rank(hdi, iso3, True, _HDI_YEAR)
    if ranked:
        out["hdi"] = ranked

    lpi = {
        e["iso3"]: e["score_infrastructure_ipl"]
        for e in load_infrastructure_ranking()
        if e.get("edition_ipl") == _LPI_EDITION and e.get("score_infrastructure_ipl") is not None
    }
    ranked = _rank(lpi, iso3, True, _LPI_EDITION)
    if ranked:
        out["lpi"] = ranked

    return out
