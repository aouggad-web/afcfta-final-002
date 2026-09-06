#!/usr/bin/env python3
"""Doctrine ZLECAf asymétrique par partenaire — à exécuter sur CHAQUE branche
pays (feat/jurisdiction-{iso3}). Documente dans le registre :
- le principe d'asymétrie (le taux dépend du COUPLE importateur/origine) ;
- la preuve par la source (TUN : 14 075 lignes à taux variables par partenaire) ;
- la réciprocité algérienne (circulaire DGD 482/2024).

Usage : backend/.venv311/bin/python backend/scripts/add_zlecaf_asymmetry_doctrine.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ASYM = {
    "principe": (
        "LE TAUX ZLECAf EST ASYMÉTRIQUE PAR PARTENAIRE : le même produit n'a "
        "PAS le même avantage selon le sens du commerce. Le taux applicable à "
        "un produit importé depuis un partenaire Z dépend du CALENDRIER DE "
        "DÉMANTÈLEMENT du pays importateur envers Z ; le même produit exporté "
        "vers Z dépend du calendrier de Z envers le pays exportateur."
    ),
    "preuve_source": (
        "TUN (Tarif Web 2026) : la douane tunisienne publie elle-même, par "
        "sous-position, des taux ZLECAf DIFFÉRENTS PAR PARTENAIRE — 14 075 "
        "lignes à taux variables, 0 à taux uniformes (ex. 01012100015 : "
        "Tanzanie 0%, démantèlement complet sous GTI, vs Cameroun/Ghana/"
        "Afrique du Sud/Kenya 40% sur la même ligne nationale)"
    ),
    "implication_calcul": (
        "le calculateur doit résoudre le taux ZLECAf par COUPLE (pays "
        "importateur, pays origine) et jamais par produit seul — le côté "
        "Algérie utilise la circulaire DGD 482/2024 (listes A/B/C, calendriers "
        "standard/réciprocité) ; le côté destination utilise le calendrier du "
        "pays importateur (colonne AfCFTA SARS pour ZAF, colonne préférences "
        "Tarif Web pour TUN, offres e-Tariff Book pour les autres)"
    ),
    "algeria_reciprocity": {
        "instrument": "Circulaire n° 482/DGD/SP/D.042/24 du 22 octobre 2024 (DGD Algérie)",
        "source_id": "DZA-DGD-CIRC-482-2024",
        "sha256": "483e8d2cf6f8769eb7d3bbfc9dda1a3df2132b6fe504bbd554f7bab1c80bdc99",
        "note": (
            "l'Algérie applique la ZLECAf à l'importation (17 322 lignes "
            "classées A/B/C, calendriers standard et réciprocité) — "
            "l'acceptation algérienne des partenaires ZLECAf prouve la "
            "réciprocité de l'accord"
        ),
    },
}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--register", required=True,
                    help="chemin du registre (ex. data/rwanda/rwa_gazette_register.json)")
    args = ap.parse_args()
    target = Path(args.register)
    if not target.is_file():
        print(f"{target}: absent de cette branche — rien à faire")
        return 0
    reg = json.loads(target.read_text(encoding="utf-8"))
    reg["zlecaf_asymetrie_partenaires"] = ASYM
    target.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{target}: doctrine asymétrie ZLECAf ajoutée")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
