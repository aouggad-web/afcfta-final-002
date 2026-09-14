#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coût de la politique d'indisponibilité, mesuré sur les fichiers collectés.

`docs/DECISION_INDISPONIBILITE_CALCULATEUR.md` arbitre entre trois options
d'affichage quand une taxe n'est pas liquidable. La règle 2 de l'option (A) —
une seule taxe indisponible rend le total indisponible — a un coût à l'écran
qu'il faut chiffrer avant de trancher.

Ce script existe parce que la mesure précédente n'existait pas : elle avait été
faite en session, ses chiffres cités dans la note et dans la description de la
demande de fusion, mais aucun fichier du dépôt ne la portait. Elle n'était donc
ni rejouable ni opposable, et elle est devenue fausse sans que rien ne le
signale quand l'inventaire fiscal a été corrigé.

La politique distingue trois causes d'indisponibilité, et ce rapport les sépare
au lieu de les additionner : elles n'appellent pas le même remède.

  ABSENTE                   la source ne porte aucune entrée pour cette taxe
  SPECIFIQUE_SANS_QUANTITE  un droit spécifique publié, calculable dès que la
                            quantité est fournie — un paramètre manquant, pas
                            une donnée manquante (règle 3 de la note)
  ASSIETTE_NON_DOCUMENTEE   un taux publié, mais aucune assiette déclarée

Aucun taux n'est inventé et aucune absence n'est convertie en zéro : le script
mesure ce que les fichiers portent, rien d'autre.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from tax_coverage_inventory import (  # noqa: E402
    CRAWLED_DIR,
    _repo_helpers,
    declared_base,
    numeric_rate,
    positions,
    specific_expression,
    tax_entries,
)

DOCUMENTE = "DOCUMENTE"
ABSENTE = "ABSENTE"
SPECIFIQUE_SANS_QUANTITE = "SPECIFIQUE_SANS_QUANTITE"
ASSIETTE_NON_DOCUMENTEE = "ASSIETTE_NON_DOCUMENTEE"

#: Les deux taxes qui décident du total dans la cascade servie à l'utilisateur.
TAXES_DECISIVES = ("DD", "TVA")

#: Causes qui rendent une ligne non liquidable au sens de la note.
CAUSES = (ABSENTE, SPECIFIQUE_SANS_QUANTITE, ASSIETTE_NON_DOCUMENTEE)


def _national_vat() -> Dict[str, dict]:
    """Taux de TVA nationaux documentés dans le dépôt, avec leur source."""
    from etl.country_tariffs_complete import COUNTRY_VAT_RATES

    return dict(COUNTRY_VAT_RATES)


def _state(value: Any) -> str:
    """État d'une entrée de taxe présente dans la source."""
    if numeric_rate(value) is not None:
        return DOCUMENTE if declared_base(value) else ASSIETTE_NON_DOCUMENTEE
    if specific_expression(value):
        return SPECIFIQUE_SANS_QUANTITE
    return ABSENTE


def measure(iso3_filter: Optional[set] = None) -> dict:
    canonical, _preferential = _repo_helpers()
    national_vat = _national_vat()

    par_pays: Dict[str, dict] = {}
    global_causes = {tax: Counter() for tax in TAXES_DECISIVES}
    lignes_totales = 0
    total_indisponible = 0
    total_indisponible_restreint = 0
    total_residu = 0
    tva_recuperable = 0

    for path in sorted(CRAWLED_DIR.glob("*_tariffs.json")):
        iso3 = path.name[:3].upper()
        if iso3_filter and iso3 not in iso3_filter:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        rows = positions(payload)
        if not rows:
            continue

        causes = {tax: Counter() for tax in TAXES_DECISIVES}
        pays_indisponible = 0
        pays_indisponible_restreint = 0
        pays_residu = 0
        pays_recuperable = 0

        for row in rows:
            etats: Dict[str, str] = {}
            for raw_code, label, value in tax_entries(row):
                code = canonical(raw_code, label)
                if code not in TAXES_DECISIVES:
                    continue
                etat = _state(value)
                # Une même taxe peut figurer deux fois : on retient l'état le
                # plus favorable, la source la mieux documentée faisant foi.
                if etats.get(code) != DOCUMENTE:
                    etats[code] = etat

            ligne_indisponible = False
            ligne_indisponible_stricte = False
            for tax in TAXES_DECISIVES:
                etat = etats.get(tax, ABSENTE)
                causes[tax][etat] += 1
                if etat != DOCUMENTE:
                    ligne_indisponible = True
                # Lecture restreinte : une assiette non déclarée n'est pas une
                # donnée absente. Le taux est publié ; seule la convention
                # d'assiette manque, et elle est la même — CIF — dans toutes les
                # nomenclatures douanières concernées. La note ne tranche pas ce
                # point, et c'est lui qui pèse le plus lourd.
                if etat in (ABSENTE, SPECIFIQUE_SANS_QUANTITE):
                    ligne_indisponible_stricte = True

            if ligne_indisponible_stricte:
                pays_indisponible_restreint += 1
                # Résidu : la ligne reste non liquidable même en lecture
                # restreinte ET même en servant le taux de TVA national
                # documenté. C'est le coût irréductible de la règle 2.
                dd_manquant = etats.get("DD", ABSENTE) in (
                    ABSENTE,
                    SPECIFIQUE_SANS_QUANTITE,
                )
                tva_couvrable = iso3 in national_vat
                if dd_manquant or not tva_couvrable:
                    pays_residu += 1
            if ligne_indisponible:
                pays_indisponible += 1
                # Récupérable : la TVA manque, mais le dépôt documente un taux
                # national pour ce pays. Cela ne rend pas la ligne calculable à
                # soi seul — le droit peut manquer aussi — mais cela nomme un
                # remède qui existe déjà.
                if etats.get("TVA", ABSENTE) == ABSENTE and iso3 in national_vat:
                    pays_recuperable += 1

        lignes = len(rows)
        lignes_totales += lignes
        total_indisponible += pays_indisponible
        total_indisponible_restreint += pays_indisponible_restreint
        total_residu += pays_residu
        tva_recuperable += pays_recuperable
        for tax in TAXES_DECISIVES:
            global_causes[tax].update(causes[tax])

        par_pays[iso3] = {
            "lignes": lignes,
            "lignes_total_indisponible": pays_indisponible,
            "pct_total_indisponible": round(100 * pays_indisponible / lignes, 2),
            "lignes_total_indisponible_lecture_restreinte": pays_indisponible_restreint,
            "lignes_residu_irreductible": pays_residu,
            "tva_recuperable_par_taux_national": pays_recuperable,
            "causes": {tax: dict(causes[tax]) for tax in TAXES_DECISIVES},
        }

    def _pct(n: int) -> float:
        return round(100 * n / lignes_totales, 2) if lignes_totales else 0.0

    return {
        "methode": {
            "source": "backend/data/crawled/*_tariffs.json, tels que collectés",
            "canonisation": "services.authentic_tariff_service._canonical_tax_code",
            "taxes_decisives": list(TAXES_DECISIVES),
            "note": (
                "Mesure du coût de la règle 2 de l'option (A) : une seule taxe "
                "décisive non liquidable rend le total indisponible. Les trois "
                "causes sont séparées car elles n'appellent pas le même remède. "
                "Aucun taux n'est inventé, aucune absence n'est convertie en zéro."
            ),
            "limite": (
                "Le périmètre est le droit de douane et la TVA. Les autres "
                "prélèvements sont recensés par tax_coverage_inventory.py et "
                "élargiraient encore le total indisponible."
            ),
        },
        "global": {
            "lignes": lignes_totales,
            "lignes_total_indisponible": total_indisponible,
            "pct_total_indisponible": _pct(total_indisponible),
            "lecture_restreinte": {
                "definition": (
                    "Une assiette non déclarée n'est pas comptée comme une "
                    "indisponibilité : le taux est publié, seule la convention "
                    "d'assiette manque. Seules ABSENTE et "
                    "SPECIFIQUE_SANS_QUANTITE rendent alors le total indisponible."
                ),
                "lignes_total_indisponible": total_indisponible_restreint,
                "pct_total_indisponible": _pct(total_indisponible_restreint),
                "residu_apres_taux_national": {
                    "definition": (
                        "Lignes qui restent non liquidables en lecture "
                        "restreinte même en servant le taux de TVA national "
                        "documenté, provenance déclarée : le droit de douane y "
                        "manque, ou le pays n'a pas de taux national documenté. "
                        "C'est le coût irréductible de la règle 2."
                    ),
                    "lignes": total_residu,
                    "pct": _pct(total_residu),
                },
            },
            "tva_recuperable_par_taux_national": tva_recuperable,
            "par_taxe": {
                tax: {
                    "etats": dict(global_causes[tax]),
                    "pct_non_liquidable": _pct(sum(global_causes[tax][c] for c in CAUSES)),
                }
                for tax in TAXES_DECISIVES
            },
        },
        "par_pays": par_pays,
    }


def main(argv: Optional[list] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    filtre = {a.upper() for a in argv if not a.startswith("-")} or None
    rapport = measure(filtre)
    sortie = REPO_ROOT / "reports" / "COUT_INDISPONIBILITE.json"
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    g = rapport["global"]
    print(f"lignes examinées            : {g['lignes']}")
    print(
        f"total indisponible (règle 2): {g['lignes_total_indisponible']} "
        f"({g['pct_total_indisponible']} %)"
    )
    for tax, bloc in g["par_taxe"].items():
        print(f"  {tax:4} non liquidable      : {bloc['pct_non_liquidable']} % — {bloc['etats']}")
    r = g["lecture_restreinte"]
    print(
        f"total indisponible (lecture restreinte) : "
        f"{r['lignes_total_indisponible']} ({r['pct_total_indisponible']} %)"
    )
    res = r["residu_apres_taux_national"]
    print(f"TVA récupérable par taux national : {g['tva_recuperable_par_taux_national']}")
    print(f"résidu irréductible               : {res['lignes']} ({res['pct']} %)")
    print(f"\nrapport écrit : {sortie.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
