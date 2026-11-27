#!/usr/bin/env python3
"""
Pétrole, gaz et charbon africains — DÉRIVÉS du fichier EIA, plus saisis à la main
=================================================================================
Écrit ``backend/etl/energy_eia.py`` à partir du fichier complet des
*International Energy Statistics* de l'EIA (U.S. Energy Information
Administration), publié sans clé d'accès :
https://www.eia.gov/opendata/bulk/INTL.zip (membre ``INTL.txt``, une série
JSON par ligne).

Trois séries par pays, années 2022 à 2025 :

- ``INTL.57-1-<ISO3>-TBPD.A`` — pétrole brut, condensats de gisement compris,
  en milliers de barils par jour ;
- ``INTL.26-1-<ISO3>-BCM.A`` — gaz naturel sec, en milliards de m³ ;
- ``INTL.7-1-<ISO3>-MT.A`` — charbon, en milliers de tonnes (servi en tonnes).

Ces séries remplacent les chiffres pétrole, gaz et charbon qui étaient
recopiés à la main, cités « OPEC ASB / EIA » ou « IEA Coal » sans
correspondre à l'une ni à l'autre.

CE QUE CE SCRIPT REFUSE DE FAIRE
----------------------------------
- **Lire « NA » ou « -- » comme un zéro.** Ces cellules sont ignorées.
- **Publier un zéro.** Une production nulle n'est pas une série : le pays
  n'apparaît pas pour ce produit.

Usage :
    python3 backend/scripts/build_energy_from_eia.py            # écrit
    python3 backend/scripts/build_energy_from_eia.py --dry-run  # affiche
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
OUT_FILE = BACKEND_DIR / "etl" / "energy_eia.py"

BULK_URL = "https://www.eia.gov/opendata/bulk/INTL.zip"
MEMBER = "INTL.txt"
ANNEES = ("2022", "2023", "2024", "2025")

#: Commodité -> (série EIA, facteur, unité servie, mesure, décimales).
SERIES = {
    "Crude oil": ("INTL.57-1-{iso3}-TBPD.A", 1, "1000 b/d",
                  "Crude oil including lease condensate production", 2),
    "Natural gas": ("INTL.26-1-{iso3}-BCM.A", 1, "bcm", "Dry natural gas production", 3),
    "Coal": ("INTL.7-1-{iso3}-MT.A", 1000, "tonnes", "Coal production", 0),
}

#: Pays africains (ISO3, codes utilisés par l'EIA dans ses identifiants de série).
AFRIQUE = (
    "DZA AGO BEN BWA BFA BDI CPV CMR CAF TCD COM COG CIV COD DJI EGY GNQ ERI SWZ ETH "
    "GAB GMB GHA GIN GNB KEN LSO LBR LBY MDG MWI MLI MRT MUS MAR MOZ NAM NER NGA RWA "
    "STP SEN SYC SLE SOM ZAF SSD SDN TZA TGO TUN UGA ZMB ZWE"
).split()


def telecharger() -> tuple:
    """Rend (lignes du membre INTL.txt, empreinte SHA-256 du membre)."""
    requete = urllib.request.Request(BULK_URL, headers={"User-Agent": "afcfta-production-etl/1.0"})
    with urllib.request.urlopen(requete, timeout=300) as resp:
        blob = resp.read()
    membre = zipfile.ZipFile(io.BytesIO(blob)).read(MEMBER)
    return membre.decode("utf-8").splitlines(), hashlib.sha256(membre).hexdigest()


def deriver(lignes) -> tuple:
    """Rend ({commodité: {unit, measure, series, by_country}}, dernière mise à jour)."""
    voulues = {
        spec[0].format(iso3=iso3): (commodite, iso3)
        for commodite, spec in SERIES.items()
        for iso3 in AFRIQUE
    }
    out, maj = {}, ""
    for ligne in lignes:
        if '"series_id"' not in ligne:
            continue
        serie = json.loads(ligne)
        cle = voulues.get(serie.get("series_id"))
        if not cle:
            continue
        commodite, iso3 = cle
        _sid, facteur, unite, mesure, decimales = SERIES[commodite]
        valeurs = {}
        for annee, valeur in serie.get("data", []):
            if annee in ANNEES and isinstance(valeur, (int, float)) and valeur > 0:
                v = round(valeur * facteur, decimales)
                if v > 0:
                    valeurs[int(annee)] = float(v)
        if not valeurs:
            continue
        entree = out.setdefault(
            commodite, {"unit": unite, "measure": mesure, "series": _sid, "by_country": {}}
        )
        entree["by_country"][iso3] = dict(sorted(valeurs.items()))
        maj = max(maj, serie.get("last_updated", ""))
    for entree in out.values():
        entree["by_country"] = dict(sorted(entree["by_country"].items()))
    return {c: out[c] for c in SERIES if c in out}, maj


def render(series: dict, sha256: str, maj: str) -> str:
    corps = []
    for commodite, spec in series.items():
        pays = ",\n".join(
            f"            {iso3!r}: {{" + ", ".join(f"{a}: {v!r}" for a, v in ans.items()) + "}"
            for iso3, ans in spec["by_country"].items()
        )
        corps.append(
            f"    {commodite!r}: {{\n"
            f"        'unit': {spec['unit']!r},\n"
            f"        'measure': {spec['measure']!r},\n"
            f"        'series': {spec['series']!r},\n"
            f"        'by_country': {{\n{pays},\n        }},\n"
            f"    }},"
        )
    points = sum(len(a) for s in series.values() for a in s["by_country"].values())
    return f'''"""
Pétrole, gaz et charbon africains dérivés de l'EIA — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===================================================================================
Produit par ``backend/scripts/build_energy_from_eia.py`` depuis le membre
``{MEMBER}`` du fichier {BULK_URL}
(EIA International Energy Statistics).

{len(series)} produits, {points} points, années {ANNEES[0]}-{ANNEES[-1]}.

Régénérer :
    python3 backend/scripts/build_energy_from_eia.py
"""

from __future__ import annotations

from typing import Dict

EIA_DATASET = "EIA International Energy Statistics"
EIA_SOURCE_URL = {BULK_URL!r}
#: Dernière mise à jour EIA des séries retenues.
EIA_LAST_UPDATED = {maj!r}
#: Empreinte SHA-256 du membre {MEMBER} dont ces chiffres sont issus.
EIA_SHA256 = {sha256!r}

#: produit -> {{unit, measure, series, by_country: {{iso3: {{année: valeur}}}}}}
EIA_SERIES: Dict[str, dict] = {{
{chr(10).join(corps)}
}}
'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Affiche sans écrire")
    args = ap.parse_args()

    lignes, sha256 = telecharger()
    series, maj = deriver(lignes)
    for commodite, spec in series.items():
        print(f"   {commodite:12} {len(spec['by_country']):>2} pays  {spec['measure']}")
    print(f"   mise à jour EIA : {maj} — sha256 {sha256[:16]}…")
    if args.dry_run:
        print("\n(--dry-run) Fichier NON écrit.")
        return
    OUT_FILE.write_text(render(series, sha256, maj), encoding="utf-8")
    print(f"\n✅ Écrit : {OUT_FILE.relative_to(BACKEND_DIR.parent)}")


if __name__ == "__main__":
    sys.exit(main())
