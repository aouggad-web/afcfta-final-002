"""
Algérie — remplace ses enregistrements manufacturiers par ceux de l'ONS
=======================================================================

``data/json/production_africaine.json`` porte, pour l'Algérie, cinq valeurs
« UNIDO 2024 » dérivées d'une structure de 2015. L'entrée UNIDO de l'Algérie
est désormais recalculée sur les comptes de l'ONS 2021-2024
(``etl/dza_manufacture_ons.py``) : ce script régénère ses enregistrements par
``build_manufacturing()`` — le même constructeur que pour les autres pays — et
ne touche à aucun autre pays ni à aucune autre dimension. Idempotent.

Usage (depuis la racine du dépôt) : python3 backend/scripts/maj_manufacture_dza.py
"""

import json
import sys
from pathlib import Path

_RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_RACINE / "backend"))
sys.path.insert(0, str(_RACINE / "backend" / "scripts"))

from build_production_real import build_manufacturing  # noqa: E402

FICHIER = _RACINE / "data" / "json" / "production_africaine.json"
PAYS = "DZA"


def main() -> None:
    donnees = json.loads(FICHIER.read_text(encoding="utf-8"))
    anciens = donnees["manufacturing_unido"]
    nouveaux = [r for r in build_manufacturing() if r["country_iso3"] == PAYS]
    position = next((i for i, r in enumerate(anciens) if r["country_iso3"] == PAYS), len(anciens))
    autres = [r for r in anciens if r["country_iso3"] != PAYS]
    donnees["manufacturing_unido"] = autres[:position] + nouveaux + autres[position:]

    meta = donnees["metadata"]
    ecart = len(donnees["manufacturing_unido"]) - meta["record_counts"]["manufacturing"]
    meta["record_counts"]["manufacturing"] += ecart
    meta["record_counts"]["total"] += ecart
    meta["sources"]["manufacturing"] = (
        "UNIDO INDSTAT4 — valeurs publiées (2024, inchangées) ; Algérie : ONS, "
        "Les comptes économiques de 2021 à 2024 (etl/dza_manufacture_ons.py)"
    )
    FICHIER.write_text(json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{PAYS} : {len(nouveaux)} enregistrements manufacturiers (ONS), écart {ecart:+d}")


if __name__ == "__main__":
    main()
