"""
Macro étendu — valeur ajoutée sectorielle & croissance PIB (World Bank WDI)
==========================================================================
Rafraîchit et enrichit la dimension « value_added_macro » du module Production
avec des valeurs RÉELLES publiées par le World Bank (World Development Indicators),
récupérées via l'API publique et figées dans ``etl/macro_wdi_data.py`` (généré par
``scripts/fetch_wdi_macro.py``).

  • Séries 2015-2024 pour les 54 pays africains.
  • Parts sectorielles : agriculture / industrie / manufacturier / services
    (% du PIB) + croissance du PIB réel (% annuel).
  • Montants : les mêmes agrégats en USD courants, plus le PIB. Une part de PIB
    situe un secteur dans son économie ; elle ne dit pas sa taille, et ne permet
    donc pas de comparer deux pays autrement qu'en structure.

Les deux familles cohabitent dans la même dimension et se distinguent par
``unit`` (``percent`` / ``USD``) — jamais par le seul libellé de secteur.

Principe impératif : chiffres PUBLIÉS uniquement (World Bank WDI). Aucune valeur
hand-curée ni extrapolée. Un couple (pays, indicateur, année) sans donnée publiée
est simplement omis. Pour rafraîchir les valeurs, relancer
``python3 scripts/fetch_wdi_macro.py`` là où l'API World Bank est joignable.

Source : World Bank — World Development Indicators
  Parts : NV.AGR.TOTL.ZS, NV.IND.TOTL.ZS, NV.IND.MANF.ZS, NV.SRV.TOTL.ZS,
          NY.GDP.MKTP.KD.ZG
  USD   : NV.AGR.TOTL.CD, NV.IND.TOTL.CD, NV.IND.MANF.CD, NV.SRV.TOTL.CD,
          NY.GDP.MKTP.CD
  https://data.worldbank.org/
"""

from __future__ import annotations

from typing import Dict, List

from etl.mining_extended import ISO3_FR_NAME

try:
    from etl.macro_wdi_data import WDI_FETCHED_AT, WDI_MACRO
except Exception:  # pragma: no cover - module généré absent
    WDI_MACRO = {}
    WDI_FETCHED_AT = None

# clef WDI -> (section ISIC, sector_detail, indicator_code, indicator_label,
#              unit, currency)
_INDICATORS = [
    (
        "agri",
        "A",
        "Agriculture, forestry and fishing",
        "NV.AGR.TOTL.ZS",
        "Agriculture, value added (% of GDP)",
        "percent",
        None,
    ),
    (
        "ind",
        "B-F",
        "Industry (including construction)",
        "NV.IND.TOTL.ZS",
        "Industry, value added (% of GDP)",
        "percent",
        None,
    ),
    (
        "manuf",
        "C",
        "Manufacturing",
        "NV.IND.MANF.ZS",
        "Manufacturing, value added (% of GDP)",
        "percent",
        None,
    ),
    (
        "serv",
        "G-T",
        "Services",
        "NV.SRV.TOTL.ZS",
        "Services, value added (% of GDP)",
        "percent",
        None,
    ),
    (
        "gdp_growth",
        "TOTAL",
        "Gross domestic product",
        "NY.GDP.MKTP.KD.ZG",
        "GDP growth (annual %)",
        "percent",
        None,
    ),
    (
        "agri_usd",
        "A",
        "Agriculture, forestry and fishing",
        "NV.AGR.TOTL.CD",
        "Agriculture, value added (current US$)",
        "USD",
        "USD",
    ),
    (
        "ind_usd",
        "B-F",
        "Industry (including construction)",
        "NV.IND.TOTL.CD",
        "Industry, value added (current US$)",
        "USD",
        "USD",
    ),
    (
        "manuf_usd",
        "C",
        "Manufacturing",
        "NV.IND.MANF.CD",
        "Manufacturing, value added (current US$)",
        "USD",
        "USD",
    ),
    (
        "serv_usd",
        "G-T",
        "Services",
        "NV.SRV.TOTL.CD",
        "Services, value added (current US$)",
        "USD",
        "USD",
    ),
    (
        "gdp_usd",
        "TOTAL",
        "Gross domestic product",
        "NY.GDP.MKTP.CD",
        "GDP (current US$)",
        "USD",
        "USD",
    ),
]


def build_macro_series() -> List[Dict]:
    """Enregistrements macro (schéma value_added_macro) depuis les données WDI réelles.

    Émet, pour chaque pays et chaque année disponibles (2015-2024), un
    enregistrement par indicateur publié — parts de PIB (``unit="percent"``) et
    montants en USD courants (``unit="USD"``). Source : World Bank WDI (aucune
    valeur synthétisée). Pas de projection ni d'``is_projection`` : uniquement
    des observations publiées.

    Les deux familles partagent le même ``sector_detail`` : un consommateur qui
    les agrège doit filtrer sur ``unit``, sous peine d'additionner un
    pourcentage et un montant.
    """
    records: List[Dict] = []
    for iso3 in sorted(WDI_MACRO):
        country_name = ISO3_FR_NAME.get(iso3, iso3)
        by_year = WDI_MACRO[iso3]
        for year in sorted(by_year):
            vals = by_year[year]
            for key, section, detail, ind_code, ind_label, unit, currency in _INDICATORS:
                value = vals.get(key)
                if value is None:
                    continue
                records.append(
                    {
                        "country_name": country_name,
                        "country_iso3": iso3,
                        "year": int(year),
                        "sector_isic_section": section,
                        "sector_detail": detail,
                        "indicator_code": ind_code,
                        "indicator_label": ind_label,
                        "value": value,
                        "unit": unit,
                        "currency": currency,
                        "price_base_year": None,
                        "source_institution": "World Bank",
                        "source_dataset": "World Development Indicators",
                        "source_url": f"https://data.worldbank.org/indicator/{ind_code}",
                        "wb_indicator_code": ind_code,
                        "wdi_fetched_at": WDI_FETCHED_AT,
                    }
                )
    return records


if __name__ == "__main__":
    recs = build_macro_series()
    years = sorted({r["year"] for r in recs})
    countries = sorted({r["country_iso3"] for r in recs})
    print(f"{len(recs)} enreg. macro — {len(countries)} pays — années {years} (WDI réel)")
