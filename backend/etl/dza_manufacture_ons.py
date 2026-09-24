"""
Algérie — l'entrée Manufacture bâtie sur les comptes de l'ONS
=============================================================

L'entrée UNIDO de l'Algérie reposait sur la structure INDSTAT de 2015, la
dernière que l'ONS ait transmise à l'ONUDI. L'ONS publie pourtant sa valeur
ajoutée par branche jusqu'en 2024 (« Les comptes économiques de 2021 à 2024 »,
n° 1067) : ``data/json/dza_industrie.json`` la reprend, avec une estimation
2025 par branche (fourchette et note de confiance). Ce module en tire une
entrée au format de ``UNIDO_INDUSTRY_DATA`` : Production › Manufacture et les
classements continentaux servent ainsi l'Algérie comme les autres pays, sur
des chiffres de 2023-2024, et chaque champ dit sa nature.

Natures (celles de ``dza_industrie.json``) :
- ``officiel`` : chiffre publié par l'ONS (ou repris tel quel par la Banque
  mondiale) ;
- ``calcul_officiel`` : dérivé exactement de chiffres officiels (croissance
  du total agrégée depuis les branches, part du PIB, valeur par habitant) ;
- ``estimation`` : projection 2025, avec fourchette, confiance et méthode ;
- ``unido`` : champ que l'ONS ne publie pas (emploi, exportations
  manufacturières, indice CIP) — valeur UNIDO conservée, datée par sa source.
"""

import json
from pathlib import Path
from typing import Dict

_RACINE = Path(__file__).resolve().parents[2]
_ONS = _RACINE / "data" / "json" / "dza_industrie.json"
_BANQUE_MONDIALE = _RACINE / "data" / "json" / "worldbank_data_latest.json"

# Division CITI à laquelle chaque branche ONS groupée est rattachée pour les
# classements (capacités, flux stratégiques). La VA de la branche entière y
# est portée : c'est un majorant de la division, marqué comme estimation.
# Sans rattachement défendable, une branche reste à l'écran mais hors des
# classements :
# - 16-18 (bois, papier, imprimerie) : part de chaque division inconnue ;
# - 29-33 : l'ONS ne précise pas où il classe le matériel de transport ;
# - 26-bur, 26-com : partage entre les divisions 26 et 32 non publié. Portée
#   sur la division 26, leur valeur estimée lèverait aussi le garde-fou de
#   couverture partielle des classements électroniques (deux pays africains
#   couverts), alors que l'Égypte, grand producteur, n'y figure pas.
_RATTACHEMENT = {
    "10-12": "10",
    "13-14": "13",
    "20-22": "20",
    "24-25": "24",
    "16-18": None,
    "29-33": None,
    "26-bur": None,
    "26-com": None,
}
# Divisions sans correspondance SH dans la table des capacités
# (services/production_capacity_service.HS_TO_COMMODITY) : elles restent à
# l'écran mais n'entrent pas dans les classements.
_SANS_CORRESPONDANCE_SH = {"15", "28"}

SOURCE_ONS = "ONS Algérie"
SOURCE_ONS_DATASET = "Les comptes économiques de 2021 à 2024 (n° 1067)"
SOURCE_ONS_URL = "https://www.ons.dz"


def _croissance_volume(branches, annee: int) -> float:
    """Croissance en volume du total : somme des VA de l'année précédente
    portées par la croissance de chaque branche (prix de l'année précédente,
    donc additives), rapportée à leur somme. Exacte sur chiffres officiels."""
    num = den = 0.0
    for b in branches:
        prec = b["annees"][str(annee - 1)]
        g = b["annees"][str(annee)]["croissance_volume_pct"]
        num += prec["va_mda"] * (1 + g / 100)
        den += prec["va_mda"]
    return (num / den - 1) * 100


def _secteurs_2024(branches, total_2024: float):
    """Les treize branches ONS de 2024, de la plus grande à la plus petite, au
    format ``top_sectors``. ``isic`` est la division de rattachement (ou le code
    de branche ONS quand il n'y en a pas) ; ``divisions`` la liste des divisions
    couvertes ; ``rattachement_isic`` la division qui alimente les classements
    (``None`` : la branche n'y entre pas)."""
    secteurs = []
    for b in branches:
        code, divisions = b["code"], b["citi_rev4"]
        rattachement = _RATTACHEMENT.get(code, divisions[0])
        va = b["annees"]["2024"]["va_musd"]
        secteur = {
            "isic": rattachement or code,
            "code_ons": code,
            "divisions": divisions,
            "name": b["libelle_fr"],
            "name_en": b["libelle_en"],
            "value_mln_usd": round(va, 1),
            "share_mva": round(va / total_2024 * 100, 1),
            "nature": "officiel",
            "rattachement_isic": rattachement,
        }
        if rattachement in _SANS_CORRESPONDANCE_SH:
            secteur["rattachement_isic"] = None
            secteur["rattachement_note"] = (
                f"Division {rattachement} sans correspondance SH dans la table des "
                "capacités : hors classements"
            )
        elif rattachement is None:
            secteur["rattachement_note"] = (
                f"Branche ONS {code} (CITI {', '.join(divisions)}), sans division de "
                "rattachement : hors classements"
            )
        elif len(divisions) > 1:
            secteur["rattachement_note"] = (
                f"Branche ONS {code} (CITI {', '.join(divisions)}), rattachée à la "
                f"division {rattachement}"
            )
        secteurs.append(secteur)
    return sorted(secteurs, key=lambda s: -s["value_mln_usd"])


_ANNEES_ONS = ("2021", "2022", "2023", "2024")


def _comptes_ons(ons: Dict) -> Dict:
    """Tableau des branches des comptes économiques, pour l'écran : valeur
    ajoutée 2021-2024 (M$ courants) avec le statut ONS de chaque millésime,
    croissance en volume et part privée 2024, estimation 2025 et sa note de
    confiance. Remplace, pour l'Algérie, le détail ISIC4 d'UNIDO (2005-2017)."""
    branches = ons["branches"]
    reference = next(b for b in branches if b["code"] == "19")["annees"]
    lignes = []
    for b in branches:
        a = b["annees"]
        e = a["2025"]
        lignes.append(
            {
                "code": b["code"],
                "libelle_fr": b["libelle_fr"],
                "libelle_en": b["libelle_en"],
                "citi": b["citi_rev4"],
                "note_citi": b["note_citi"],
                "va_musd": {y: a[y]["va_musd"] for y in _ANNEES_ONS},
                "croissance_volume_2024_pct": a["2024"]["croissance_volume_pct"],
                "part_privee_va_2024_pct": a["2024"].get("part_privee_va_pct"),
                "estimation_2025": {
                    "va_musd": e["va_musd"],
                    "croissance_volume_pct": e["croissance_volume_pct"],
                    "confiance": e["confiance"],
                },
            }
        )
    lignes.sort(key=lambda r: -r["va_musd"]["2024"])
    total = ons["total"]
    return {
        "source": ons["meta"]["sources"]["ons_comptes"]["titre"],
        "source_url": ons["meta"]["sources"]["ons_comptes"]["url"],
        "unite": "millions de USD courants, taux de change annuel moyen",
        "statuts": {y: reference[y]["statut_ons"] for y in _ANNEES_ONS},
        "branches": lignes,
        "total": {
            "va_musd": {y: total[y]["va_musd"] for y in _ANNEES_ONS},
            "estimation_2025": {
                "va_musd": total["2025"]["va_musd"],
                "croissance_volume_pct": total["2025"]["croissance_volume_pct"],
            },
        },
    }


def entree_dza(base: Dict) -> Dict:
    """L'entrée UNIDO de l'Algérie, recalculée sur les comptes de l'ONS.

    ``base`` est l'entrée curée d'origine : on en garde les champs que l'ONS
    ne publie pas (emploi, exportations manufacturières, CIP, part des
    technologies moyennes et hautes, produits clés, zones industrielles).
    """
    ons = json.loads(_ONS.read_text(encoding="utf-8"))
    bm = json.loads(_BANQUE_MONDIALE.read_text(encoding="utf-8"))["data"]["DZA"]["indicators"]
    branches, total = ons["branches"], ons["total"]
    va_2023, va_2024 = total["2023"]["va_musd"], total["2024"]["va_musd"]
    e25 = total["2025"]

    # Part de la VA 2024 portée par des branches dont l'estimation 2025 est
    # notée B, puis C : la confiance du total se lit ainsi, branche par branche.
    poids = {}
    for b in branches:
        c = b["annees"]["2025"]["confiance"]
        poids[c] = poids.get(c, 0.0) + b["annees"]["2024"]["va_musd"]
    confiance = {c: round(v / va_2024 * 100, 1) for c, v in sorted(poids.items())}

    entree = {k: v for k, v in base.items() if k not in ("top_sectors", "growth_rate_2024_est")}
    # La structure INDSTAT 2015 reste consultable : elle recoupe exactement
    # le détail ISIC4 (classes 2005-2017) que l'écran affiche encore.
    entree["structure_indstat_2015"] = base.get("top_sectors", [])
    entree.update(
        {
            "mva_2023_mln_usd": va_2023,
            "mva_2024_mln_usd": va_2024,
            "growth_rate_2023": round(_croissance_volume(branches, 2023), 1),
            "growth_rate_2024": round(_croissance_volume(branches, 2024), 1),
            "mva_gdp_percent": round(va_2023 * 1e6 / bm["GDP"]["2023"] * 100, 2),
            "mva_per_capita_usd": round(va_2023 * 1e6 / bm["Population"]["2023"]),
            "top_sectors": _secteurs_2024(branches, va_2024),
            "comptes_ons": _comptes_ons(ons),
            "data_year": 2024,
            "estimation_2025": {
                "annee": 2025,
                "va_mln_usd": e25["va_musd"],
                "croissance_volume_pct": e25["croissance_volume_pct"],
                "base_prix": e25["base_prix"],
                "confiance_part_va_pct": confiance,
                "methode": ons["meta"]["methode_2025"],
                "note": e25["note"],
            },
            "natures": {
                "mva_2023_mln_usd": "officiel",
                "mva_2024_mln_usd": "officiel",
                "top_sectors": "officiel",
                "growth_rate_2023": "calcul_officiel",
                "growth_rate_2024": "calcul_officiel",
                "mva_gdp_percent": "calcul_officiel",
                "mva_per_capita_usd": "calcul_officiel",
                "industry_employment": "unido",
                "exports_manuf_mln_usd": "unido",
                "cip_index_rank": "unido",
            },
            "source_institution": SOURCE_ONS,
            "source_dataset": SOURCE_ONS_DATASET,
            "source_url": SOURCE_ONS_URL,
            "source": (
                f"{SOURCE_ONS}, {SOURCE_ONS_DATASET} : valeur ajoutée par branche 2021-2024 ; "
                "Banque mondiale (WDI) : PIB, population, taux de change ; estimation 2025 : "
                "comptes trimestriels de l'ONS, worldsteel, OPEP, OICA, USDA et IPI. "
                "Emploi, exportations manufacturières et indice CIP : UNIDO."
            ),
        }
    )
    return entree
