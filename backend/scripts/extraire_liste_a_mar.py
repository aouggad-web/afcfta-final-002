#!/usr/bin/env python3
"""Liste A marocaine telle que l'avenant n° 6627/223 du 09/01/2025 la publie.

Le tableau a deux formes d'entrée, que seule la typographie distingue :

* « Chap. NN » suivi de codes en maigre sous « excepté : » — le chapitre
  entier est en liste A, sauf ces positions ;
* des codes en gras, sans en-tête de chapitre — positions incluses une à une
  d'un chapitre qui n'est pas entier en liste A (02, 04, 07, 08…).

La lecture du seul texte confond les deux (vérifié sur la page 2 rendue en
image) : la graisse de la police est donc lue.

    python3 backend/scripts/extraire_liste_a_mar.py
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pymupdf

RACINE = Path(__file__).resolve().parents[1]
SOURCE = (
    RACINE / "data" / "legal_refs" / "zlecaf_application" / "sources" / "MAR_circulaire_6627-223_2025-01-09.pdf"
)
SORTIE = RACINE / "data" / "zlecaf_mar" / "liste_a_6627-223.json"


def main() -> None:
    chapitres, exceptions, inclusions = set(), [], []
    for page in pymupdf.open(SOURCE):
        for bloc in page.get_text("dict")["blocks"]:
            for ligne in bloc.get("lines", []):
                for span in ligne["spans"]:
                    texte = span["text"].strip()
                    chapitre = re.fullmatch(r"Chap\.\s*(\d+)", texte)
                    if chapitre:
                        chapitres.add(f"{int(chapitre.group(1)):02d}")
                    elif re.fullmatch(r"\d{4,10}", texte):
                        gras = "Bold" in span["font"] or span["flags"] & 16
                        (inclusions if gras else exceptions).append(texte)
    # Une exception vit sous son chapitre entier, une inclusion hors de lui.
    assert all(code[:2] in chapitres for code in exceptions)
    assert not any(code[:2] in chapitres for code in inclusions)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    resultat = {
        "_objet": (
            "Liste A du Maroc (démantèlement du DI et de la TPI) : chapitres "
            "entiers, leurs exceptions, et les positions incluses une à une."
        ),
        "_instrument": "Avenant n° 6627/223 du 09/01/2025 à la circulaire ADII n° 6530/223 (SH 2022)",
        "_source": "backend/data/legal_refs/zlecaf_application/sources/MAR_circulaire_6627-223_2025-01-09.pdf",
        "_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "chapitres_entiers": sorted(chapitres),
        "exceptions": sorted(set(exceptions)),
        "inclusions": sorted(set(inclusions)),
    }
    SORTIE.write_text(json.dumps(resultat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(chapitres)} chapitres, {len(exceptions)} exceptions, {len(inclusions)} inclusions -> {SORTIE}")


if __name__ == "__main__":
    main()
