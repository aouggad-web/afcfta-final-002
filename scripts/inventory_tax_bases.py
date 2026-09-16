#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventaire des assiettes et méthodes de calcul, pays par pays et taxe par taxe.

Ce que le calculateur applique à une taxe n'est pas seulement un taux : c'est un
taux ET une assiette. Le dépôt en détient deux descriptions, et elles ne
s'accordent pas.

  - les fichiers collectés portent, pour chaque taxe, l'assiette telle que la
    source la publie (« CIF + DD + RS + PCS », « CIF+Duty+Fees », « PN (KG) ») ;
  - `services.authentic_tariff_service.COUNTRY_TAX_PROFILES` porte une table
    écrite à la main pour 37 pays, que le moteur de cascade utilise seule.

Le moteur n'interroge que la seconde. Là où elles divergent, le montant servi
est faux — dans les deux sens : la TVA béninoise est sous-évaluée parce que la
table omet RS et PCS de l'assiette, l'ivoirienne sur-évaluée parce que la table
y ajoute un DD que la source n'y met pas.

Ce rapport établit l'état des lieux avant toute correction : pour chaque couple
pays/taxe, ce que la source déclare, ce que la table code, et leur accord. Il
n'invente aucune assiette et ne tranche aucun désaccord — il les nomme.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from tax_coverage_inventory import (  # noqa: E402
    CRAWLED_DIR,
    _repo_helpers,
    declared_base,
    positions,
    tax_entries,
)

#: Statuts de connaissance d'une assiette.
LUE_DANS_LA_SOURCE = "lue_dans_la_source"
TABLE_CODEE_SEULE = "table_codee_seule"
NON_DOCUMENTEE = "non_documentee"

#: Natures d'assiette. Elles n'appellent pas la même mécanique et les fondre
#: dans une cascade valorielle produirait des montants faux.
VALORIELLE = "valorielle"
VALORIELLE_PLAFONNEE = "valorielle_plafonnee"
QUANTITATIVE = "quantitative"
INDETERMINEE = "indeterminee"

#: Mots qui ne désignent pas une taxe dans une expression d'assiette : ils
#: nomment la valeur en douane elle-même, ou l'unité, ou la devise.
_NON_TAXES = {
    "CIF",
    "VAL",
    "VALEUR",
    "DOU",
    "DOUANE",
    "DINARS",
    "GR",
    "SOMME",
    "EXCES",
    "PLAFOND",
    "XAF",
    "KG",
    "PN",
    "QCS",
}

_QUANTITE_RE = re.compile(r"\b(PN|KG|LITRE|LT|TONNE|UNITE|QCS)\b", re.IGNORECASE)
_PLAFOND_RE = re.compile(r"plafond|ceiling|max", re.IGNORECASE)


def base_kind(expression: str) -> str:
    """Nature de l'assiette, lue dans son expression."""
    if _PLAFOND_RE.search(expression):
        return VALORIELLE_PLAFONNEE
    if _QUANTITE_RE.search(expression) and "CIF" not in expression.upper():
        return QUANTITATIVE
    if "CIF" in expression.upper() or "VAL" in expression.upper():
        return VALORIELLE
    return INDETERMINEE


def base_dependencies(expression: str) -> list[str]:
    """Taxes entrant dans l'assiette, extraites de son expression.

    « Duty » est l'écriture anglophone du droit de douane : la normaliser évite
    de compter deux assiettes différentes là où il n'y en a qu'une.
    """
    texte = str(expression).upper().replace("DUTY", "DD")
    jetons = re.findall(r"[A-Z]{2,8}", texte)
    return sorted({j for j in jetons if j not in _NON_TAXES})


def _profil_codes() -> Dict[str, dict]:
    from services.authentic_tariff_service import COUNTRY_TAX_PROFILES

    return dict(COUNTRY_TAX_PROFILES)


def _bases_declarees_par_le_jeu(payload: dict, canonical) -> Dict[str, str]:
    """Assiettes que le fichier déclare globalement, hors position.

    Plusieurs jeux portent leurs assiettes une seule fois, sous
    ``calculation_rules.bases``, plutôt que sur chaque ligne. Ne lire que la
    position faisait conclure à une assiette absente là où le fichier la
    déclare — pour Maurice, sur la totalité de ses lignes.
    """
    regles = payload.get("calculation_rules")
    if not isinstance(regles, dict):
        return {}
    bases = regles.get("bases")
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


def _pays_sous_regle_tva() -> dict:
    """Pays dont le moteur remplace l'assiette codée de la TVA par le texte.

    Sans cette lecture, l'inventaire décrirait la table codée en prétendant
    décrire le moteur : il annoncerait « CIF + DD » pour le Kenya là où le
    runtime liquide sur CIF + DD + IDF + RDL. Un rapport qui se réclame du
    comportement réel doit lire la surcharge, pas seulement la table.
    """
    from services.authentic_tariff_service import ASSIETTE_TVA_ETABLIE

    return dict(ASSIETTE_TVA_ETABLIE)


#: Marqueur d'une assiette « valeur en douane + toutes les autres taxes »,
#: que le moteur applique sans énumérer : les dépendances sont, par
#: construction, toutes les autres taxes de la position.
TOUTES_LES_AUTRES_TAXES = "TOUTES_LES_AUTRES_TAXES"

#: Les écritures sous lesquelles la TVA apparaît dans les inventaires.
_ALIAS_TVA_INVENTAIRE = ("TVA", "T.V.A", "VAT", "IVA")


def _base_codee(profil: Optional[dict], taxe: str) -> Optional[list[str]]:
    """Dépendances d'assiette que la table codée attribue à cette taxe."""
    if not profil:
        return None
    bases = profil.get("tax_bases") or {}
    for cle in (taxe, taxe.replace(".", ""), "T.V.A" if taxe == "TVA" else taxe):
        if cle in bases:
            entree = bases[cle]
            if isinstance(entree, (list, tuple)) and len(entree) == 2:
                formule, ajouts = entree
                if formule == "DD_AMOUNT":
                    return ["DD_MONTANT"]
                return sorted(str(a).upper() for a in ajouts)
    return None


#: Ce que le moteur applique à un pays sans profil (cf. compute_tax_cascade).
DEFAUT_SANS_PROFIL = {"TVA": ["DD"]}


def inventory(countries: Optional[Iterable[str]] = None) -> dict:
    canonical, _preferential = _repo_helpers()
    profils = _profil_codes()
    regles_tva = _pays_sous_regle_tva()
    filtre = {c.upper() for c in countries} if countries else None

    par_pays: Dict[str, dict] = {}
    desaccords: list[dict] = []
    natures = Counter()
    statuts = Counter()

    for path in sorted(CRAWLED_DIR.glob("*_tariffs.json")):
        iso3 = path.name[:3].upper()
        if filtre and iso3 not in filtre:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        lignes = positions(payload)
        if not lignes:
            continue

        # Une même taxe peut porter plusieurs assiettes dans un même pays : le
        # cas est réel et doit ressortir, pas être écrasé par un « la première
        # rencontrée fait foi ».
        # Assiettes déclarées une fois pour tout le jeu, hors position : un
        # fichier peut porter calculation_rules.bases.DD.basis = « CIF » sans
        # le répéter sur chacune de ses lignes. Les ignorer comptait Maurice
        # comme dépourvue d'assiette sur ses 5 619 lignes.
        bases_du_jeu = _bases_declarees_par_le_jeu(payload, canonical)

        vues: Dict[str, Counter] = defaultdict(Counter)
        for row in lignes:
            # Dédoublonnage PAR POSITION : une même ligne décrit souvent ses
            # taxes deux fois, dans un bloc compact sans assiette et dans un
            # bloc détaillé qui en porte une. Les compter tous deux faisait
            # apparaître autant de positions « sans assiette publiée » que de
            # lignes, alors même que le statut disait « lue dans la source » —
            # deux affirmations qui ne peuvent pas être vraies ensemble.
            par_taxe: Dict[str, str] = {}
            for code, label, valeur in tax_entries(row):
                taxe = canonical(code, label)
                if not taxe:
                    continue
                expression = declared_base(valeur) or bases_du_jeu.get(taxe) or ""
                # L'entrée qui porte une assiette l'emporte sur celle qui n'en
                # porte pas ; entre deux assiettes, la première rencontrée
                # reste retenue, car l'écart réel doit ressortir ailleurs.
                if expression or taxe not in par_taxe:
                    if not par_taxe.get(taxe):
                        par_taxe[taxe] = expression
            for taxe, expression in par_taxe.items():
                vues[taxe][expression] += 1

        profil = profils.get(iso3)
        taxes: Dict[str, dict] = {}
        for taxe, comptes in sorted(vues.items()):
            publiees = {e: n for e, n in comptes.items() if e}
            codee = _base_codee(profil, taxe)
            if codee is None and not profil:
                codee = DEFAUT_SANS_PROFIL.get(taxe)

            # Ce que le MOTEUR applique réellement, qui n'est pas toujours la
            # table codée : pour les pays dont un texte primaire établit
            # l'assiette de la TVA, compute_tax_cascade remplace l'assiette
            # codée par « valeur en douane + toutes les autres taxes ».
            regle_tva = regles_tva.get(iso3) if taxe in _ALIAS_TVA_INVENTAIRE else None
            appliquee = TOUTES_LES_AUTRES_TAXES if regle_tva else codee

            if publiees:
                principale = max(publiees, key=publiees.get)
                statut = LUE_DANS_LA_SOURCE
                depend = base_dependencies(principale)
                nature = base_kind(principale)
            elif codee is not None:
                principale = None
                statut = TABLE_CODEE_SEULE
                depend = None
                nature = INDETERMINEE
            else:
                principale = None
                statut = NON_DOCUMENTEE
                depend = None
                nature = INDETERMINEE

            statuts[statut] += 1
            natures[nature] += 1

            entree = {
                "statut": statut,
                "nature": nature,
                "assiette_publiee": principale,
                "assiette_publiee_verbatim_variantes": (
                    sorted(publiees, key=publiees.get, reverse=True)[1:6] or None
                ),
                "positions_sans_assiette_publiee": comptes.get("", 0),
                "dependances_source": depend,
                "dependances_table_codee": codee,
                "table_codee_origine": (
                    profil.get("source") if profil else "profil par défaut du moteur"
                ),
                "assiette_appliquee_par_le_moteur": appliquee,
                "fondement_de_l_assiette_appliquee": (
                    regle_tva["texte"] if regle_tva else None
                ),
            }

            # Le désaccord se mesure contre ce que le moteur applique. Comparer
            # à la table codée signalerait encore comme litigieux ce que la
            # règle d'assiette a déjà tranché.
            if regle_tva:
                entree["accord"] = True
                entree["accord_note"] = (
                    "assiette remplacée par le texte primaire : « valeur en douane "
                    "+ tous droits et taxes perçus à l'entrée, hors TVA ». Elle "
                    "englobe l'assiette publiée comme l'assiette codée."
                )
            elif depend is not None and codee is not None and set(depend) != set(codee):
                entree["accord"] = False
                desaccords.append(
                    {
                        "pays": iso3,
                        "taxe": taxe,
                        "assiette_publiee": principale,
                        "dependances_source": depend,
                        "dependances_table_codee": codee,
                        "profil_present": bool(profil),
                    }
                )
            elif depend is not None and codee is not None:
                entree["accord"] = True
            else:
                entree["accord"] = None

            taxes[taxe] = entree

        par_pays[iso3] = {
            "lignes": len(lignes),
            "profil_de_cascade_code": bool(profil),
            "taxes": taxes,
        }

    return {
        "genere_le": datetime.now(timezone.utc).isoformat(),
        "methode": {
            "source_assiettes": "backend/data/crawled/*_tariffs.json, champ base/assiette",
            "source_table_codee": (
                "services.authentic_tariff_service.COUNTRY_TAX_PROFILES, "
                "seule consultée par compute_tax_cascade()"
            ),
            "canonisation": "services.authentic_tariff_service._canonical_tax_code",
            "note": (
                "Aucune assiette n'est inventée et aucun désaccord n'est tranché. "
                "Le rapport nomme, pays par pays et taxe par taxe, ce que la "
                "source déclare, ce que la table code, et leur accord."
            ),
            "limite": (
                "Une assiette absente du fichier n'est pas réputée inexistante : "
                "beaucoup d'administrations ne répètent pas dans leur nomenclature "
                "une convention qu'elles publient ailleurs. Le statut "
                f"« {NON_DOCUMENTEE} » dit que le dépôt l'ignore, pas qu'elle n'existe pas."
            ),
        },
        "synthese": {
            "pays": len(par_pays),
            "couples_pays_taxe": sum(len(v["taxes"]) for v in par_pays.values()),
            "par_statut": dict(statuts),
            "par_nature": dict(natures),
            "desaccords": len(desaccords),
            "pays_sans_profil_code": sorted(
                iso for iso, v in par_pays.items() if not v["profil_de_cascade_code"]
            ),
        },
        "desaccords": sorted(desaccords, key=lambda d: (d["pays"], d["taxe"])),
        "par_pays": par_pays,
    }


def main(argv: Optional[list] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rapport = inventory([a for a in argv if not a.startswith("-")] or None)
    sortie = REPO_ROOT / "reports" / "ASSIETTES_ET_METHODES.json"
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    s = rapport["synthese"]
    print(f"pays                   : {s['pays']}")
    print(f"couples pays/taxe      : {s['couples_pays_taxe']}")
    print(f"statuts                : {s['par_statut']}")
    print(f"natures d'assiette     : {s['par_nature']}")
    print(f"DÉSACCORDS source/table: {s['desaccords']}")
    print(f"pays sans profil codé  : {len(s['pays_sans_profil_code'])}")
    print(f"\nrapport écrit : {sortie.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
