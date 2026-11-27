#!/usr/bin/env python3
"""
Minerais africains — DÉRIVÉS des fiches USGS, plus saisis à la main
====================================================================
Écrit ``backend/etl/mining_usgs_tables.py`` à partir des fiches par minerai
des *Mineral Commodity Summaries* (MCS) 2024, 2025 et 2026 publiées sur
pubs.usgs.gov. Chaque fiche porte un tableau « World Mine Production and
Reserves » qui publie deux années : l'avant-dernière, révisée, et la
dernière, estimée (MCS 2026 : 2024 révisé, 2025 estimé).

Années 2022 à 2025. Chaque valeur pays-année vient de la PLUS RÉCENTE
édition qui la publie pour ce pays : 2024 de MCS 2026 ; à défaut — l'USGS a
pu renvoyer le pays dans « Other countries » — de l'estimation de MCS 2025.
L'édition retenue est inscrite avec chaque valeur.

POURQUOI LES FICHES PDF ET NON LE CSV
--------------------------------------
Un premier générateur lisait le CSV de la publication ScienceBase (MCS 2025
Data Release), mais ScienceBase oppose une page de vérification aux clients
automatisés, et le CSV ne couvre que MCS 2025. Les fiches PDF de pubs.usgs.gov sont publiques,
stables, et couvrent toutes les éditions. Comparées au CSV sur 2023-2024, elles
concordent pour 22 commodités sur 24 ; les deux écarts tiennent au CSV (le
Lesotho manquant aux pierres gemmes ; le mica de Madagascar décalé d'une année,
repris de MCS 2024). Ce script remplace les tables qui
étaient recopiées à la main dans ``etl/mining_extended.py`` et dans le socle :
sur 327 valeurs citées « MCS », 24 seulement concordaient avec les fiches.

LECTURE DES TABLEAUX
---------------------
``pdftotext -layout`` (poppler-utils) restitue les colonnes à leur position.
Chaque nombre est rattaché à la colonne d'année dont il est le plus proche ;
ce qui ne tombe sous aucune année (réserves, renvois de note) est ignoré.
Quand l'USGS marque une estimation (« e » en exposant), les chiffres passent
à la ligne suivante : cette ligne de suite l'emporte sur la ligne du pays,
où ne reste alors qu'un renvoi de note.

CE QUE CE SCRIPT REFUSE DE FAIRE
----------------------------------
- **Deviner une valeur.** « — », ``W`` (secret statistique), ``NA`` et les
  valeurs entre parenthèses sont ignorés, jamais lus comme zéro.
- **Compter un pays absent.** Un pays qui ne figure pas au tableau est
  rangé par l'USGS dans « Other countries » : il n'a pas de chiffre propre.

Usage (nécessite ``pdftotext``) :
    python3 backend/scripts/build_mining_from_usgs_pdfs.py            # écrit
    python3 backend/scripts/build_mining_from_usgs_pdfs.py --dry-run  # affiche
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
OUT_FILE = BACKEND_DIR / "etl" / "mining_usgs_tables.py"

URL = "https://pubs.usgs.gov/periodicals/mcs{edition}/mcs{edition}-{slug}.pdf"
#: Édition -> années publiées par son tableau (révisée, estimée).
EDITIONS = {2026: (2024, 2025), 2025: (2023, 2024), 2024: (2022, 2023)}
ANNEES = (2022, 2023, 2024, 2025)

#: Commodité -> (fiche, facteur vers l'unité servie, unité servie, mesure,
#:               première colonne d'année de la mesure, section du tableau).
#: Le facteur convertit l'unité de la fiche (« Data in thousand metric tons… »).
SPECS = {
    "Gold": ("gold", 1, "tonnes", "Mine production, gold content", 0, None),
    "Copper": ("copper", 1000, "tonnes", "Mine production, copper content", 0, None),
    "Cobalt": ("cobalt", 1, "tonnes", "Mine production, cobalt content", 0, None),
    "Diamonds": ("diamond", 1_000_000, "carats", "Mine production, natural industrial diamond", 0, None),
    "Phosphate": ("phosphate", 1000, "tonnes", "Mine production, marketable phosphate rock", 0, None),
    "Bauxite": ("bauxite-alumina", 1000, "tonnes", "Mine production, bauxite, dry tons", 2, None),
    "Iron ore": ("iron-ore", 1000, "tonnes", "Mine production, usable ore", 0, None),
    "Manganese": ("manganese", 1000, "tonnes", "Mine production, manganese content", 0, None),
    "Platinum": ("platinum-group", 0.001, "tonnes", "Mine production, platinum", 2, None),
    "Palladium": ("platinum-group", 0.001, "tonnes", "Mine production, palladium", 0, None),
    "Zinc": ("zinc", 1000, "tonnes", "Mine production, zinc content", 0, None),
    "Lead": ("lead", 1000, "tonnes", "Mine production, lead content", 0, None),
    "Tin": ("tin", 1, "tonnes", "Mine production, tin content", 0, None),
    "Nickel": ("nickel", 1, "tonnes", "Mine production, nickel content", 0, None),
    "Chromium": ("chromium", 1000, "tonnes", "Mine production, marketable chromite ore", 0, None),
    "Lithium": ("lithium", 1, "tonnes", "Mine production, lithium content", 0, None),
    "Graphite": ("graphite", 1, "tonnes", "Mine production", 0, None),
    "Tantalum": ("tantalum", 1, "tonnes", "Mine production, tantalum content", 0, None),
    "Vanadium": ("vanadium", 1, "tonnes", "Mine production, vanadium content", 0, None),
    "Antimony": ("antimony", 1, "tonnes", "Mine production, antimony content", 0, None),
    "Silver": ("silver", 1, "tonnes", "Mine production, silver content", 0, None),
    "Titanium (ilmenite)": ("titanium-minerals", 1000, "tonnes",
                            "Mine production, ilmenite, TiO2 content", 0, "Ilmenite:"),
    "Zircon": ("zirconium-hafnium", 1000, "tonnes",
               "Mine production, zirconium mineral concentrates", 0, None),
    "Fluorspar": ("fluorspar", 1000, "tonnes", "Mine production", 0, None),
    "Salt": ("salt", 1000, "tonnes", "Mine production", 0, None),
    "Gypsum": ("gypsum", 1000, "tonnes", "Mine production", 0, None),
    # Minerais jusqu'ici dérivés du CSV ScienceBase (MCS 2025 seulement) : même
    # unité et même mesure que lui, pour que l'écran et ses traductions restent
    # inchangés. Les fiches couvrent en plus 2022 (MCS 2024) et 2025 (MCS 2026).
    "Arsenic": ("arsenic", 1, "metric tons",
                "Plant production, arsenic trioxide or calculated equivalent.", 0, None),
    "Barite": ("barite", 1, "thousand metric tons", "Mine production, barite, estimated", 0, None),
    "Beryllium": ("beryllium", 1, "metric tons", "Mine production, beryllium content", 0, None),
    "Cement": ("cement", 1, "thousand metric tons", "Cement production, estimated", 0, None),
    "Diatomite": ("diatomite", 1, "thousand metric tons", "Mine production, estimated", 0, None),
    "Feldspar": ("feldspar", 1, "thousand metric tons", "Mine production, estimated", 0, None),
    "Garnet (industrial)": ("garnet", 1, "metric tons", "Mine production, estimated", 0, None),
    "Gemstones": ("gemstones", 1, "thousand carats",
                  "Mine production, thousand carats of gem-quality diamond", 0, None),
    "Helium": ("helium", 1, "million cubic meters", "Production, helium gas content", 0, None),
    "Lime": ("lime", 1, "thousand metric tons", "Plant production, lime", 0, None),
    "Mercury": ("mercury", 1, "metric tons", "Mine production, mercury content", 0, None),
    "Mica (Natural)": ("mica", 1, "metric tons", "Mine production, mica scrap and flake", 0, None),
    "Niobium": ("niobium", 1, "metric tons", "Mine production, niobium content", 0, None),
    "Nitrogen(fixed) - Ammonia": ("nitrogen", 1, "thousand metric tons",
                                  "Plant production, nitrogen content", 0, None),
    "Perlite": ("perlite", 1, "thousand metric tons", "Mine production, estimated", 0, None),
    "Pumice & Pumicite": ("pumice", 1, "thousand metric tons", "Mine production, estimated", 0, None),
    "Rare earths": ("rare-earths", 1, "metric tons",
                    "Mine production, rare-earth-oxide equivalent", 0, None),
    "Selenium": ("selenium", 1, "metric tons", "Refinery production, selenium content", 0, None),
    "Silicon": ("silicon", 1, "thousand metric tons",
                "Plant production, Ferosilicon, silicon content", 0, None),
    "Soda ash": ("soda-ash", 1, "thousand metric tons", "Mine production, natural", 0, "Natural:"),
    "Talc, crude": ("talc", 1, "thousand metric tons", "Mine production, estimated", 0, None),
    "Tellurium": ("tellurium", 1, "metric tons", "Refinery production, tellurium content", 0, None),
    "Tungsten": ("tungsten", 1, "metric tons", "Mine production, tungsten content", 0, None),
    "Vermiculite": ("vermiculite", 1, "thousand metric tons", "Mine production", 0, None),
}

#: Noms de pays africains tels que l'USGS les écrit -> ISO3.
USGS_AFRICA = {
    "Algeria": "DZA", "Angola": "AGO", "Benin": "BEN", "Botswana": "BWA",
    "Burkina Faso": "BFA", "Burundi": "BDI", "Cameroon": "CMR",
    "Central African Republic": "CAF", "Chad": "TCD", "Congo (Brazzaville)": "COG",
    "Congo (Kinshasa)": "COD", "Cote d'Ivoire": "CIV", "Côte d'Ivoire": "CIV",
    "Côte d’Ivoire": "CIV", "Egypt": "EGY", "Eritrea": "ERI", "Eswatini": "SWZ",
    "Ethiopia": "ETH", "Gabon": "GAB", "Ghana": "GHA", "Guinea": "GIN",
    "Kenya": "KEN", "Lesotho": "LSO", "Liberia": "LBR", "Libya": "LBY",
    "Madagascar": "MDG", "Malawi": "MWI", "Mali": "MLI", "Mauritania": "MRT",
    "Morocco": "MAR", "Mozambique": "MOZ", "Namibia": "NAM", "Niger": "NER",
    "Nigeria": "NGA", "Rwanda": "RWA", "Senegal": "SEN", "Sierra Leone": "SLE",
    "South Africa": "ZAF", "South Sudan": "SSD", "Sudan": "SDN", "Tanzania": "TZA",
    "Togo": "TGO", "Tunisia": "TUN", "Uganda": "UGA", "Zambia": "ZMB", "Zimbabwe": "ZWE",
}

_PAYS = re.compile(
    r"^\s*(" + "|".join(re.escape(n) for n in sorted(USGS_AFRICA, key=len, reverse=True))
    + r")(?:\d+(?:, ?\d+)*)?(?=\s|$)"  # renvoi de note collé : « Madagascar11 »
)
_ANNEE = re.compile(r"(?<![\d,])((?:19|20)\d{2})e?(?![\d,])")
_JETON = re.compile(r"\S+")
_NOMBRE = re.compile(r"^\d{1,3}(?:,\d{3})*(?:\.\d+)?$|^\d+(?:\.\d+)?$")
#: Ligne de suite : indentée, et commençant par un nombre, un « e » ou un tiret.
#: Du texte peut suivre à droite (colonne « réserves » rédigée) : il ne tombe
#: sous aucune année et n'est pas lu.
_SUITE = re.compile(r"^\s+(?:e?[\d,.]+|e|—|--|W|NA|\(\d+\))(?=\s|$)")


def _tableau(lignes: list) -> list:
    """Lignes du tableau mondial de production, de son titre à « World total »."""
    debut = next(
        (i for i, l in enumerate(lignes) if re.match(r"\s*World .*[Pp]roduction", l)), None
    )
    if debut is None:
        raise ValueError("tableau « World … Production » introuvable")
    fin = next(
        (i for i in range(debut, len(lignes)) if re.search(r"World total|World Resources", lignes[i])),
        len(lignes),
    )
    return lignes[debut:fin]


def _colonnes(lignes: list) -> list:
    """(année, position du dernier caractère) des en-têtes d'années, dans l'ordre."""
    for ligne in lignes:
        # Un en-tête commence par une année : une phrase qui cite « 2024 and
        # 2025 » n'en est pas un.
        if not _ANNEE.match(ligne.lstrip()):
            continue
        annees = [(int(m.group(1)), m.end(1) - 1) for m in _ANNEE.finditer(ligne)]
        if len(annees) >= 2:
            return annees
    raise ValueError("en-tête d'années introuvable")


def _nombres(ligne: str, depuis: int = 0) -> list:
    """(valeur, position du dernier caractère) des nombres de la ligne."""
    out = []
    for m in _JETON.finditer(ligne):
        if m.start() < depuis:
            continue
        jeton = m.group(0)
        if jeton[:1] == "e" and _NOMBRE.match(jeton[1:]):
            jeton = jeton[1:]  # « e23 » : estimation collée au nombre
        if _NOMBRE.match(jeton):
            out.append((float(jeton.replace(",", "")), m.end() - 1))
    return out


def _placer(nombres: list, colonnes: list, tolerance: int = 6) -> dict:
    """Rattache chaque nombre à la colonne d'année la plus proche."""
    places = {}
    for valeur, fin in nombres:
        rang, ecart = min(
            ((k, abs(fin - pos)) for k, (_, pos) in enumerate(colonnes)), key=lambda x: x[1]
        )
        if ecart <= tolerance:
            places.setdefault(rang, valeur)
    return places


def lire_tableau(texte: str, section: str | None = None) -> tuple:
    """Rend (colonnes, {iso3: {rang de colonne: valeur}}) pour les pays africains."""
    lignes = _tableau(texte.splitlines())
    colonnes = _colonnes(lignes)
    if section:
        debut = next(i for i, l in enumerate(lignes) if l.strip() == section)
        fin = next(
            (i for i in range(debut + 1, len(lignes)) if re.match(r"^[A-Z][a-z]+:\s*$", lignes[i].strip())),
            len(lignes),
        )
        lignes = lignes[debut:fin]
    pays = {}
    for i, ligne in enumerate(lignes):
        m = _PAYS.match(ligne)
        if not m:
            continue
        valeurs = _placer(_nombres(ligne, m.end()), colonnes)
        # Lignes de suite (chiffres renvoyés sous un « e ») : elles font foi.
        for suite in lignes[i + 1:i + 3]:
            if _PAYS.match(suite) or not _SUITE.match(suite):
                break
            valeurs.update(_placer(_nombres(suite), colonnes))
        pays[USGS_AFRICA[m.group(1)]] = valeurs
    return colonnes, pays


def extraire(texte: str, spec: tuple, annees: tuple) -> dict:
    """{iso3: {année: valeur convertie}} pour une fiche et une mesure."""
    _slug, facteur, _unite, _mesure, premiere, section = spec
    colonnes, pays = lire_tableau(texte, section)
    rangs = {premiere: colonnes[premiere][0], premiere + 1: colonnes[premiere + 1][0]}
    out = {}
    for iso3, valeurs in pays.items():
        for rang, annee in rangs.items():
            if annee in annees and rang in valeurs:
                out.setdefault(iso3, {})[annee] = round(valeurs[rang] * facteur, 6)
    return out


def telecharger(edition: int, slug: str, dossier: Path) -> tuple:
    """Rend (texte de la fiche, empreinte SHA-256 du PDF, URL)."""
    url = URL.format(edition=edition, slug=slug)
    # pubs.usgs.gov refuse l'agent par défaut de urllib ; le script se nomme.
    requete = urllib.request.Request(url, headers={"User-Agent": "afcfta-production-etl/1.0"})
    with urllib.request.urlopen(requete, timeout=120) as resp:
        blob = resp.read()
    pdf = dossier / f"mcs{edition}-{slug}.pdf"
    pdf.write_bytes(blob)
    texte = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True
    ).stdout
    return texte, hashlib.sha256(blob).hexdigest(), url


def combiner(lectures: dict) -> dict:
    """{édition: {iso3: {année: valeur}}} -> {iso3: {année: (valeur, édition)}}.

    Pour chaque pays et chaque année, la PLUS RÉCENTE édition qui la publie
    l'emporte ; une édition plus ancienne ne comble que ce que les suivantes
    ne publient pas pour ce pays.
    """
    out = {}
    for edition in sorted(lectures, reverse=True):
        for iso3, ans in lectures[edition].items():
            for annee, valeur in ans.items():
                out.setdefault(iso3, {}).setdefault(annee, (valeur, edition))
    return {i: dict(sorted(a.items())) for i, a in sorted(out.items())}


def deriver() -> tuple:
    tables, empreintes = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        cache = {}
        for commodite, spec in SPECS.items():
            slug, _facteur, unite, mesure, _premiere, _section = spec
            lectures = {}
            for edition, publiees in EDITIONS.items():
                annees = tuple(a for a in publiees if a in ANNEES)
                if (edition, slug) not in cache:
                    cache[(edition, slug)] = telecharger(edition, slug, Path(tmp))
                texte, sha, url = cache[(edition, slug)]
                empreintes[url] = sha
                lectures[edition] = extraire(texte, spec, annees)
            par_pays = combiner(lectures)
            if par_pays:
                tables[commodite] = {
                    "slug": slug, "unit": unite, "measure": mesure, "by_country": par_pays,
                }
    return tables, empreintes


def render(tables: dict, empreintes: dict, absentes: list) -> str:
    corps = []
    for commodite, spec in tables.items():
        pays = ",\n".join(
            f"            {iso3!r}: {{" + ", ".join(f"{a}: {v!r}" for a, v in ans.items()) + "}"
            for iso3, ans in spec["by_country"].items()
        )
        corps.append(
            f"    {commodite!r}: {{\n"
            f"        'slug': {spec['slug']!r},\n"
            f"        'unit': {spec['unit']!r},\n"
            f"        'measure': {spec['measure']!r},\n"
            f"        'by_country': {{\n{pays},\n        }},\n"
            f"    }},"
        )
    sha = "\n".join(f"    {u!r}: {s!r}," for u, s in sorted(empreintes.items()))
    points = sum(len(a) for s in tables.values() for a in s["by_country"].values())
    return f'''"""
Minerais africains dérivés des fiches USGS MCS — FICHIER GÉNÉRÉ, NE PAS ÉDITER
===============================================================================
Produit par ``backend/scripts/build_mining_from_usgs_pdfs.py`` depuis les
fiches par minerai des Mineral Commodity Summaries {", ".join(str(e) for e in sorted(EDITIONS))}
(https://pubs.usgs.gov/periodicals/mcs<édition>/).

{len(tables)} commodités, {points} points, années {ANNEES[0]}-{ANNEES[-1]}. Chaque valeur est
un couple (valeur, édition MCS qui la publie) : la plus récente édition qui
publie l'année pour ce pays. La dernière année d'une édition est son estimation.

Sans aucun pays africain au tableau de production : {", ".join(absentes) or "aucune"}.
Ces commodités n'ont pas de série : l'USGS range leurs producteurs africains
dans « Other countries ».

Régénérer :
    python3 backend/scripts/build_mining_from_usgs_pdfs.py
"""

from __future__ import annotations

from typing import Dict

URL_FICHE = {URL!r}

#: Empreinte SHA-256 de chaque fiche lue. Une régénération qui en change une
#: signale une révision de l'USGS — donc une relecture, pas un simple rafraîchissement.
USGS_PDF_SHA256: Dict[str, str] = {{
{sha}
}}

#: commodité -> {{slug, unit, measure, by_country: {{iso3: {{année: (valeur, édition)}}}}}}
MCS_TABLES: Dict[str, dict] = {{
{chr(10).join(corps)}
}}
'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Affiche sans écrire")
    args = ap.parse_args()

    tables, empreintes = deriver()
    absentes = [c for c in SPECS if c not in tables]
    for commodite, spec in tables.items():
        print(f"   {commodite:22} {len(spec['by_country']):>2} pays  {spec['measure']}")
    print(f"   sans pays africain : {', '.join(absentes) or '—'}")
    if args.dry_run:
        print("\n(--dry-run) Fichier NON écrit.")
        return
    OUT_FILE.write_text(render(tables, empreintes, absentes), encoding="utf-8")
    print(f"\n✅ Écrit : {OUT_FILE.relative_to(BACKEND_DIR.parent)}")


if __name__ == "__main__":
    sys.exit(main())
