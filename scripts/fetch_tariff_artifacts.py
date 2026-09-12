#!/usr/bin/env python3
"""Récupère et vérifie les artefacts tarifaires déclarés par le manifeste.

Les données tarifaires changent une à trois fois par an et par pays : ce sont
des publications, pas des sources. Elles sont donc servies comme artefacts
immuables versionnés, épinglés dans ``backend/data/source_registry_v2.json``
par leur empreinte SHA-256, et non versionnées dans git.

Ce script est le point d'entrée du déploiement :

  1. lit le manifeste ;
  2. résout les pays hérités (``_shared``) vers leur source réelle ;
  3. télécharge ``artifact_url`` quand il est renseigné, sinon se rabat sur
     ``artifact_path`` déjà présent dans le dépôt ;
  4. **vérifie l'empreinte avant de publier le fichier**, et refuse en cas
     d'écart plutôt que de servir une donnée dont l'origine n'est pas établie.

L'hébergement des artefacts n'étant pas encore tranché, tous les
``artifact_url`` valent ``null`` : le script fonctionne alors entièrement sur
les fichiers du dépôt. Renseigner une URL suffira à basculer un pays sans
toucher au code.

Usage :
    python scripts/fetch_tariff_artifacts.py            # tous les pays
    python scripts/fetch_tariff_artifacts.py --country DZA
    python scripts/fetch_tariff_artifacts.py --verify-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "backend" / "data" / "source_registry_v2.json"
DEST_DIR = REPO_ROOT / "backend" / "data" / "crawled"


class ArtifactError(RuntimeError):
    """Un artefact est introuvable, ou son contenu ne correspond pas au manifeste."""


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def resolve(countries: dict, iso: str) -> tuple[str, dict]:
    """Suit la chaîne ``_shared`` jusqu'à l'entrée qui publie réellement.

    Une entrée héritée ne porte pas d'artefact propre : les membres d'une union
    douanière partagent le tarif extérieur commun de la source citée.
    """
    seen: list[str] = []
    current = iso
    while True:
        entry = countries.get(current)
        if entry is None:
            raise ArtifactError(f"{iso}: pays absent du manifeste (via {' → '.join(seen)})")
        shared = entry.get("_shared")
        if not shared:
            return current, entry
        parent = shared.split()[0].upper()
        if parent in seen:
            raise ArtifactError(f"{iso}: chaîne _shared circulaire ({' → '.join(seen + [parent])})")
        seen.append(current)
        current = parent


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=300) as response, open(tmp, "wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(dest)


def process(iso: str, countries: dict, verify_only: bool) -> Optional[str]:
    """Retourne un message d'anomalie, ou None si le pays est en ordre."""
    source_iso, entry = resolve(countries, iso)
    if source_iso != iso:
        return None  # publié par son parent, rien à récupérer

    path_value = entry.get("artifact_path")
    if not path_value:
        return f"{iso}: aucun artifact_path déclaré"
    dest = REPO_ROOT / path_value
    expected = entry.get("sha256")
    url = entry.get("artifact_url")

    if url and not verify_only:
        try:
            download(url, dest)
        except Exception as exc:  # noqa: BLE001 — le message doit rester lisible
            return f"{iso}: téléchargement impossible depuis {url} ({exc})"

    if not dest.exists():
        return f"{iso}: artefact absent ({path_value}) et aucun artifact_url pour le récupérer"

    if not expected or expected == "pending":
        # Sans empreinte de référence, on ne peut rien affirmer : c'est un
        # trou de traçabilité à combler, pas une validation.
        return f"{iso}: empreinte absente du manifeste, intégrité non vérifiable"

    actual = sha256_of(dest)
    if actual != expected:
        return (
            f"{iso}: empreinte non conforme\n"
            f"        attendue {expected}\n"
            f"        obtenue  {actual}"
        )
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", help="ne traiter qu'un pays (ISO3)")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="vérifier les empreintes sans rien télécharger",
    )
    args = parser.parse_args()

    countries = load_manifest()["countries"]
    targets = [args.country.upper()] if args.country else sorted(countries)

    problems = []
    for iso in targets:
        try:
            problem = process(iso, countries, args.verify_only)
        except ArtifactError as exc:
            problem = str(exc)
        if problem:
            problems.append(problem)

    checked = len(targets) - len(problems)
    print(f"{checked}/{len(targets)} pays conformes au manifeste")
    if problems:
        print(f"\n{len(problems)} anomalie(s) :", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
