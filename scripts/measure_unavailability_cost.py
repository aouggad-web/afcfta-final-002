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


def _bases_du_jeu(payload: dict, canonical) -> Dict[str, str]:
    """Assiettes qu'un fichier déclare une fois pour toutes ses lignes.

    MUS_tariffs.json porte calculation_rules.bases.DD.basis = « CIF » sans le
    répéter position par position. Ne lire que la position comptait Maurice
    comme dépourvue d'assiette sur ses 5 619 lignes, et gonflait d'autant un
    coût d'indisponibilité entièrement imaginaire.
    """
    regles = payload.get("calculation_rules")
    bases = regles.get("bases") if isinstance(regles, dict) else None
    if not isinstance(bases, dict):
        return {}
    declarees: Dict[str, str] = {}
    for code, valeur in bases.items():
        taxe = canonical(code, "")
        if not taxe:
            continue
        expression = valeur.get("basis") if isinstance(valeur, dict) else valeur
        if isinstance(expression, str) and expression.strip():
            declarees[taxe] = expression.strip()
    return declarees


def _state(value: Any, base_du_jeu: Optional[str] = None) -> str:
    """État d'une entrée de taxe présente dans la source.

    Un taux publié à zéro est liquidable SANS assiette : zéro pour cent de
    n'importe quelle assiette vaut zéro. Le classer comme dépourvu d'assiette
    gonflait le coût d'indisponibilité d'entrées qui ne coûtent rien — et
    contredisait la règle posée par la note de décision, selon laquelle un zéro
    explicite est documenté.
    """
    taux = numeric_rate(value)
    if taux is not None:
        if taux == 0:
            return DOCUMENTE
        return DOCUMENTE if (declared_base(value) or base_du_jeu) else ASSIETTE_NON_DOCUMENTEE
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
    total_residu_sans_substitution = 0
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

        bases_du_jeu = _bases_du_jeu(payload, canonical)
        causes = {tax: Counter() for tax in TAXES_DECISIVES}
        pays_indisponible = 0
        pays_indisponible_restreint = 0
        pays_residu = 0
        pays_residu_sans_substitution = 0
        pays_recuperable = 0

        for row in rows:
            etats: Dict[str, str] = {}
            for raw_code, label, value in tax_entries(row):
                code = canonical(raw_code, label)
                if code not in TAXES_DECISIVES:
                    continue
                etat = _state(value, bases_du_jeu.get(code))
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
                # restreinte ET même en servant le taux de TVA national.
                #
                # La version précédente posait « tva_couvrable = iso3 in
                # national_vat » sans regarder l'état de la ligne. Elle tenait
                # donc pour guérie une TVA SPÉCIFIQUE dont la quantité est
                # inconnue, au motif qu'un taux ad valorem national existe
                # ailleurs — ce qu'un taux ad valorem ne peut pas suppléer.
                # Le résidu s'en trouvait minoré, dans le sens qui rend la
                # décision facile.
                dd_manquant = etats.get("DD", ABSENTE) in (
                    ABSENTE,
                    SPECIFIQUE_SANS_QUANTITE,
                )
                # Un taux national ne peut suppléer QUE l'absence pure de TVA
                # publiée. Il ne remplace ni une TVA spécifique sans quantité,
                # ni un droit de douane manquant.
                tva_suppleable = (
                    etats.get("TVA", ABSENTE) == ABSENTE and iso3 in national_vat
                )
                if dd_manquant or not tva_suppleable:
                    pays_residu += 1
                # Lecture stricte du même résidu : elle exige en outre que la
                # substitution ait une assiette documentée. Le taux national
                # n'en porte aucune — c'est l'objection qui a fait suspendre
                # cette sous-décision. Sous cette lecture, aucune substitution
                # ne rend une ligne liquidable, et le résidu égale le compte
                # restreint. Les deux chiffres sont publiés : choisir l'un
                # sans nommer l'autre serait présenter une hypothèse comme un
                # constat.
                pays_residu_sans_substitution += 1
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
        total_residu_sans_substitution += pays_residu_sans_substitution
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
                    "correction_2026-09-14": (
                        "Le calcul précédent tenait une TVA SPÉCIFIQUE sans "
                        "quantité pour couverte dès qu'un taux national existait "
                        "pour le pays, alors qu'un taux ad valorem ne peut pas "
                        "suppléer un montant unitaire dont la quantité est "
                        "inconnue. Le résidu était donc minoré — dans le sens "
                        "qui rend la décision facile."
                    ),
                    "hypothese": (
                        "Ce chiffre suppose acquis que servir le taux de TVA "
                        "national rende la ligne liquidable. Cette substitution "
                        "n'a PAS d'assiette documentée : c'est l'objection qui a "
                        "fait suspendre la sous-décision. Le chiffre ci-dessous "
                        "en est la lecture stricte."
                    ),
                },
                "residu_sans_substitution": {
                    "definition": (
                        "Même résidu, sans admettre la substitution par un taux "
                        "national : aucune ligne n'est alors réputée guérie, "
                        "puisque le taux national ne porte aucune assiette. Ce "
                        "chiffre est le plancher de ce qui reste non liquidable "
                        "si la substitution est refusée."
                    ),
                    "lignes": total_residu_sans_substitution,
                    "pct": _pct(total_residu_sans_substitution),
                },
                "ce_que_l_ecart_signifie": (
                    "L'écart entre les deux résidus mesure exactement ce que la "
                    "substitution par le taux national ferait gagner, et donc "
                    "l'enjeu de la sous-décision suspendue. Présenter le seul "
                    "chiffre optimiste donnerait une hypothèse pour un constat."
                ),
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
    print(f"résidu, substitution admise       : {res['lignes']} ({res['pct']} %)")
    sans = r["residu_sans_substitution"]
    print(f"résidu, substitution refusée      : {sans['lignes']} ({sans['pct']} %)")
    print(f"\nrapport écrit : {sortie.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
