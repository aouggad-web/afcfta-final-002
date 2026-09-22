"""
Manufacturier mesuré — agrégats nationaux UNSD (base ODD, source UNIDO)
=======================================================================
Construit la dimension « manufacturing_unsd » du module Production à partir de
valeurs RÉELLES publiées par l'UNSD, récupérées via l'API ODD publique et
figées dans ``etl/unsd_manufacturing_data.py`` (généré par
``scripts/fetch_unsd_manufacturing.py``).

CE QUE CETTE DIMENSION EST, ET CE QU'ELLE N'EST PAS
---------------------------------------------------
Le portail d'UNIDO répond 403 : le détail INDSTAT par division ISIC n'est pas
téléchargeable librement, et 32 pays sur 54 n'ont chez nous qu'une structure
*estimée* (``manufacturing_unido``, ``is_estimation``).

Cette dimension ne comble pas ce trou-là — aucune source libre ne publie la
ventilation par division. Elle en comble un autre, et c'est pour cela qu'elle
est tenue à part plutôt que fondue dans ``manufacturing_unido`` : elle donne
trois grandeurs manufacturières **mesurées** au niveau national, qui
permettent de situer un pays sans s'appuyer sur l'estimation de structure.

  • taille rapportée à la population (VAM par habitant, USD constants 2020) ;
  • poids dans l'emploi (part de l'emploi manufacturier) ;
  • sophistication (part de la moyenne et haute technologie dans la VAM) —
    indicateur que la plateforme n'avait sous aucune forme, et qui distingue
    un pays qui transforme d'un pays qui assemble.

Ne jamais mélanger les deux dimensions dans une même série : l'une mesure des
divisions (souvent estimées), l'autre des agrégats (mesurés).

Principe impératif : chiffres PUBLIÉS uniquement. Aucune valeur hand-curée ni
extrapolée. Un couple (pays, série, année) sans donnée publiée est omis.

Source : UNSD — base de données des indicateurs ODD, cible 9.2
  NV_IND_MANFPC, SL_TLF_MANF, NV_IND_TECH
  https://unstats.un.org/sdgapi/
"""

from __future__ import annotations

from typing import Dict, List

from etl.mining_extended import ISO3_FR_NAME

try:
    from etl.unsd_manufacturing_data import UNSD_FETCHED_AT, UNSD_MANUFACTURING
except Exception:  # pragma: no cover - module généré absent
    UNSD_MANUFACTURING = {}
    UNSD_FETCHED_AT = None

# clef -> (code série, libellé, unité, devise, base de prix)
_SERIES = [
    (
        "mva_per_capita_usd",
        "NV_IND_MANFPC",
        "Manufacturing value added per capita",
        "USD",
        "USD",
        "constant 2020",
    ),
    (
        "employment_share_pct",
        "SL_TLF_MANF",
        "Manufacturing employment as a proportion of total employment",
        "percent",
        None,
        None,
    ),
    (
        "medium_high_tech_share_pct",
        "NV_IND_TECH",
        "Medium and high-tech manufacturing value added as a proportion of total MVA",
        "percent",
        None,
        None,
    ),
]

_SERIES_URL = "https://unstats.un.org/sdgapi/v1/sdg/Series/Data?seriesCode={code}"


def build_manufacturing_unsd() -> List[Dict]:
    """Enregistrements manufacturiers mesurés, un par (pays, série, année).

    Schéma aligné sur les autres dimensions de production : même en-tête pays /
    année / secteur / indicateur / valeur / unité / source, afin qu'un
    consommateur puisse les lire sans cas particulier.
    """
    records: List[Dict] = []
    for iso3 in sorted(UNSD_MANUFACTURING):
        country_name = ISO3_FR_NAME.get(iso3, iso3)
        by_year = UNSD_MANUFACTURING[iso3]
        for year in sorted(by_year):
            values = by_year[year]
            for key, code, label, unit, currency, price_base in _SERIES:
                value = values.get(key)
                if value is None:
                    continue
                records.append(
                    {
                        "country_name": country_name,
                        "country_iso3": iso3,
                        "year": int(year),
                        "sector_isic_section": "C",
                        "sector_detail": "Manufacturing",
                        "indicator_code": code,
                        "indicator_label": label,
                        "value": value,
                        "unit": unit,
                        "currency": currency,
                        "price_base_year": price_base,
                        "source_institution": "UNSD / UNIDO",
                        "source_dataset": "UN SDG Indicators Database — target 9.2",
                        "source_url": _SERIES_URL.format(code=code),
                        "data_nature": "OFFICIAL_STATISTICS",
                        "unsd_fetched_at": UNSD_FETCHED_AT,
                    }
                )
    return records


if __name__ == "__main__":
    recs = build_manufacturing_unsd()
    years = sorted({r["year"] for r in recs})
    countries = sorted({r["country_iso3"] for r in recs})
    by_code: Dict[str, int] = {}
    for r in recs:
        by_code[r["indicator_code"]] = by_code.get(r["indicator_code"], 0) + 1
    print(f"{len(recs)} enreg. — {len(countries)} pays — années {years[0]}-{years[-1]}")
    print(f"  par série : {by_code}")
