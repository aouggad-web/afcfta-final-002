#!/usr/bin/env python3
"""
Minerais africains — DÉRIVÉS du fichier USGS, plus saisis à la main
===================================================================
Écrit ``backend/etl/mining_usgs_mcs.py`` à partir du membre
``MCS2025_World_Data.csv`` de la publication ScienceBase du *Mineral Commodity
Summaries 2025 Data Release*. Ce fichier publie, par commodité et par pays, la
production 2023 (révisée) et l'estimation 2024.

POURQUOI UN GÉNÉRATEUR PLUTÔT QU'UN AJOUT AU DICTIONNAIRE
-----------------------------------------------------------
Les minerais vivaient dans des dictionnaires Python transcrits à la main
depuis les publications USGS. Trente commodités y figuraient, quarante-six
sont dans le fichier. L'écart ne tenait pas à la disponibilité — le fichier
est public et lisible par machine — mais au coût de la recopie. Dériver
supprime ce coût, et surtout supprime la classe d'erreur qui va avec :
un chiffre mal recopié ne se voit pas.

CE QUE CE SCRIPT REFUSE DE FAIRE
----------------------------------
- **Mélanger des mesures.** La colonne ``TYPE`` distingue production minière,
  de raffinerie, d'usine, fonte brute, acier brut. Ce ne sont pas la même
  chose : classer ensemble la production minière d'un pays et la production
  de raffinerie d'un autre donnerait un palmarès faux. Le script retient donc,
  pour chaque commodité, UNE seule mesure — la plus représentée parmi les pays
  africains — et l'inscrit dans chaque enregistrement.
- **Recouvrir les séries existantes.** Les hydrocarbures (EIA/OPEC) et
  l'uranium (WNA) ne sont pas dans MCS ; les commodités déjà ingérées ne sont
  pas réémises. Le générateur complète, il ne remplace pas.
- **Deviner une valeur.** Les cellules vides, ``--``, ``W`` (retenu par le
  secret statistique) et ``NA`` sont ignorées, jamais interprétées comme zéro.

Usage :
    python3 backend/scripts/build_mining_from_usgs_mcs.py            # écrit
    python3 backend/scripts/build_mining_from_usgs_mcs.py --dry-run  # affiche
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

OUT_FILE = BACKEND_DIR / "etl" / "mining_usgs_mcs.py"
SCIENCEBASE_ITEM = "https://www.sciencebase.gov/catalog/item/677eaf95d34e760b392c4970"
EDITION = "Mineral Commodity Summaries 2025"
MEMBER = "MCS2025_World_Data.csv"

#: Noms de pays africains tels que l'USGS les écrit → ISO3.
USGS_AFRICA = {
    "Algeria": "DZA", "Angola": "AGO", "Benin": "BEN", "Botswana": "BWA",
    "Burkina Faso": "BFA", "Burundi": "BDI", "Cameroon": "CMR",
    "Central African Republic": "CAF", "Chad": "TCD", "Congo (Brazzaville)": "COG",
    "Congo (Kinshasa)": "COD", "Cote d'Ivoire": "CIV", "Côte d'Ivoire": "CIV",
    "Egypt": "EGY", "Eritrea": "ERI", "Eswatini": "SWZ", "Ethiopia": "ETH",
    "Gabon": "GAB", "Ghana": "GHA", "Guinea": "GIN", "Kenya": "KEN",
    "Liberia": "LBR", "Libya": "LBY", "Madagascar": "MDG", "Malawi": "MWI",
    "Mali": "MLI", "Mauritania": "MRT", "Morocco": "MAR", "Mozambique": "MOZ",
    "Namibia": "NAM", "Niger": "NER", "Nigeria": "NGA", "Rwanda": "RWA",
    "Senegal": "SEN", "Sierra Leone": "SLE", "Somalia": "SOM", "South Africa": "ZAF",
    "South Sudan": "SSD", "Sudan": "SDN", "Tanzania": "TZA", "Togo": "TGO",
    "Tunisia": "TUN", "Uganda": "UGA", "Zambia": "ZMB", "Zimbabwe": "ZWE",
}

#: L'USGS et nos tables curées ne nomment pas toujours la même chose pareil.
#: Sans ce pont, « Iron Ore » passerait pour une commodité nouvelle à côté de
#: notre « Iron ore », et l'écran afficherait deux classements du même minerai.
MCS_TO_CURATED = {
    "Iron Ore": "Iron ore",
    "Titanium Mineral Concentrates": "Titanium (ilmenite)",
    "Zirconium and Hafnium": "Zircon",
    "Platinum-Group metals": "Platinum",
    "Phosphate rock": "Phosphate",
    "Diamond (industrial)": "Diamonds",
}


def curated_commodities() -> set:
    """Ce que les tables ÉCRITES À LA MAIN couvrent déjà.

    Calculé depuis ces tables, et non depuis le jeu construit : l'autorité sur
    « qu'est-ce qui est déjà curé » est le code source, pas un artefact de
    build qui peut être en retard d'une exécution.
    """
    import importlib.util

    from etl.mining_extended import MINING_EXTENDED, MINING_YEAR_2024

    spec = importlib.util.spec_from_file_location(
        "_socle", SCRIPT_DIR / "build_production_faostat_usgs.py"
    )
    socle = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(socle)
    except SystemExit:  # le script du socle a un main() qui peut sortir
        pass
    return (
        set(MINING_EXTENDED)
        | set(MINING_YEAR_2024)
        | set(getattr(socle, "USGS_MULTI_YEAR", {}))
    )

#: Cellules qui ne sont pas des nombres. ``W`` = retenu par le secret
#: statistique : une absence de publication, surtout pas un zéro.
NON_VALUES = {"", "--", "NA", "W", "XX", "(1)", "NaN"}


def clean(text: str) -> str:
    return (text or "").replace("\xa0", " ").strip()


def is_production(type_label: str) -> bool:
    """La ligne mesure-t-elle une PRODUCTION, et non une capacité ou une réserve ?"""
    low = type_label.lower()
    if "capacity" in low or "reserve" in low:
        return False
    return "production" in low or low in {"pig iron", "raw steel"}


def fetch_csv() -> tuple:
    """Télécharge le membre CSV depuis ScienceBase et rend (texte, empreinte).

    L'empreinte est inscrite dans le fichier produit : sans elle, on ne peut
    pas dire de QUEL octet la dérivation est sortie, et « régénérer » ne
    permet plus de vérifier qu'on retombe sur la même chose.
    """
    with urllib.request.urlopen(f"{SCIENCEBASE_ITEM}?format=json", timeout=90) as resp:
        item = json.load(resp)
    url = next(
        f["url"] for f in item["files"] if f["name"].startswith("World_Data_Release")
    )
    with urllib.request.urlopen(url, timeout=180) as resp:
        blob = resp.read()
    member = zipfile.ZipFile(io.BytesIO(blob)).read(MEMBER)
    return member.decode("utf-8-sig"), hashlib.sha256(member).hexdigest()


def derive(raw_csv: str) -> dict:
    rows = list(csv.DictReader(io.StringIO(raw_csv)))
    already = curated_commodities()

    # 1. Ne garder que les lignes africaines qui MESURENT une production.
    keep = []
    for row in rows:
        iso3 = USGS_AFRICA.get(clean(row["COUNTRY"]))
        type_label = clean(row["TYPE"])
        if not iso3 or not is_production(type_label):
            continue
        keep.append((clean(row["COMMODITY"]), iso3, type_label, row))

    # 2. Pour chaque commodité, UNE seule mesure : la plus représentée. Mêler
    #    production minière et production de raffinerie dans un même classement
    #    comparerait des grandeurs différentes sans le dire.
    by_commodity = collections.defaultdict(collections.Counter)
    for commodity, _iso3, type_label, _row in keep:
        by_commodity[commodity][type_label] += 1
    chosen = {c: types.most_common(1)[0][0] for c, types in by_commodity.items()}

    out = {}
    for commodity, iso3, type_label, row in keep:
        # Une commodité déjà curée n'est pas réémise : deux séries pour le
        # même minerai donneraient deux classements concurrents, sans que
        # rien à l'écran ne dise lequel fait foi. Remplacer les tables
        # écrites à la main par cette dérivation est souhaitable, mais c'est
        # un autre geste — il changerait des chiffres déjà publiés.
        if MCS_TO_CURATED.get(commodity, commodity) in already:
            continue
        if type_label != chosen[commodity]:
            continue
        unit = clean(row["UNIT_MEAS"])
        for column, year in (("PROD_2023", 2023), ("PROD_EST_ 2024", 2024)):
            cell = clean(row.get(column, "")).replace(",", "")
            if cell in NON_VALUES:
                continue
            try:
                value = float(cell)
            except ValueError:
                continue
            entry = out.setdefault(commodity, {"unit": unit, "measure": type_label, "by": {}})
            entry["by"].setdefault(iso3, {})[year] = value
    return out


def render(derived: dict, sha256: str) -> str:
    body = []
    for commodity in sorted(derived):
        spec = derived[commodity]
        countries = ",\n".join(
            f"            {iso3!r}: {{"
            + ", ".join(f"{y}: {v!r}" for y, v in sorted(spec['by'][iso3].items()))
            + "}"
            for iso3 in sorted(spec["by"])
        )
        body.append(
            f"    {commodity!r}: {{\n"
            f"        'unit': {spec['unit']!r},\n"
            f"        'measure': {spec['measure']!r},\n"
            f"        'by_country': {{\n{countries},\n        }},\n"
            f"    }},"
        )
    countries_total = len({i for s in derived.values() for i in s["by"]})
    points = sum(len(y) for s in derived.values() for y in s["by"].values())
    return f'''"""
Minerais africains dérivés du fichier USGS — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===========================================================================
Produit par ``backend/scripts/build_mining_from_usgs_mcs.py`` depuis le membre
``{MEMBER}`` de la publication ScienceBase du *{EDITION} Data Release*.
{SCIENCEBASE_ITEM}

{len(derived)} commodités, {countries_total} pays, {points} points (2023 publié, 2024 estimé).

CHAQUE COMMODITÉ PORTE SA MESURE
----------------------------------
``measure`` reprend la colonne ``TYPE`` du fichier. Elle n'est pas
décorative : « Mine production » et « Refinery production » ne se comparent
pas. Le générateur ne retient qu'une mesure par commodité, précisément pour
qu'un classement ne mêle jamais les deux — mais un consommateur qui agrège
plusieurs commodités doit continuer à la lire.

Régénérer :
    python3 backend/scripts/build_mining_from_usgs_mcs.py
"""

from __future__ import annotations

from typing import Dict

USGS_MCS_EDITION = {EDITION!r}
USGS_MCS_MEMBER = {MEMBER!r}
#: Empreinte du membre CSV dont ces chiffres sont issus. Une régénération qui
#: la change signale une nouvelle édition — donc une relecture, pas un simple
#: rafraîchissement.
USGS_MCS_SHA256 = {sha256!r}
USGS_MCS_SOURCE_URL = {SCIENCEBASE_ITEM!r}

#: commodité -> {{unit, measure, by_country: {{iso3: {{année: valeur}}}}}}
MCS_DERIVED: Dict[str, dict] = {{
{chr(10).join(body)}
}}
'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Affiche sans écrire")
    args = ap.parse_args()

    raw_csv, sha256 = fetch_csv()
    derived = derive(raw_csv)
    points = sum(len(y) for s in derived.values() for y in s["by"].values())
    print(f"   {len(derived)} commodités, {points} points — sha256 {sha256[:16]}…")
    for commodity in sorted(derived, key=lambda c: -len(derived[c]["by"]))[:10]:
        spec = derived[commodity]
        print(f"      {commodity:34} {len(spec['by']):>2} pays  [{spec['measure'][:34]}]")

    if args.dry_run:
        print("\n(--dry-run) Fichier NON écrit.")
        return
    OUT_FILE.write_text(render(derived, sha256), encoding="utf-8")
    print(f"\n✅ Écrit : {OUT_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
