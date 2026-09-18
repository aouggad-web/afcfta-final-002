#!/usr/bin/env python3
"""Construire la table des libellés SH6 en français et en anglais.

POURQUOI CE FICHIER EXISTE. Plusieurs tarifs nationaux ne publient leur
désignation que dans UNE langue — le portugais pour le Mozambique et São Tomé,
l'arabe pour l'Égypte et la Libye. L'opérateur qui lit le calculateur doit
pouvoir reconnaître la marchandise ; mais TRADUIRE NOUS-MÊMES un libellé
tarifaire produirait un texte qui a l'air officiel sans l'être.

CE QUE FAIT CE SCRIPT. Il n'invente ni ne traduit rien : il EMPRUNTE les
libellés que d'autres tarifs nationaux, déjà collectés et servis par le socle,
publient dans ces langues — le tarif extérieur commun de l'EAC (anglais), le
tarif extérieur commun de la CEDEAO (français), et d'autres. Chaque libellé
retenu porte le pays dont il vient.

CE QU'IL NE FAIT PAS. Il ne descend pas sous le SH6. Une sous-position
NATIONALE à huit ou dix chiffres n'a pas de libellé officiel dans une autre
langue : la table reste donc au niveau du parent SH6, et le socle le déclare
(`niveau: "SH6"`). Le libellé national, lui, n'est jamais remplacé.

UNE TABLE VOLONTAIREMENT ÉCARTÉE. `backend/data/hs6_database.json` porte bien
`description_fr` et `description_en`, mais les deux NE SE CORRESPONDENT PAS :
sur 010129 elle donne « Autres » en français et « Horses » en anglais, sur
300490 « Autres » et « Medicaments ». Les servir produirait deux libellés
contradictoires sur la même ligne.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

RACINE = Path(__file__).resolve().parent.parent
CRAWLED = RACINE / "backend" / "data" / "crawled"
SORTIE = RACINE / "backend" / "data" / "hs6_designations_fr_en.json"

#: Tarifs nationaux dont la désignation est publiée EN ANGLAIS, par ordre de
#: préférence. Le premier qui porte un libellé pour un SH6 l'emporte.
SOURCES_EN = (
    ("KEN", "EAC Common External Tariff (kra.go.ke)"),
    ("TZA", "EAC Common External Tariff"),
    ("UGA", "EAC Common External Tariff"),
    ("ZMB", "Zambia Revenue Authority customs tariff"),
    ("MUS", "Mauritius Revenue Authority — Customs Tariff Schedules"),
    ("GHA", "Ghana Customs tariff"),
    ("NGA", "Nigeria Customs tariff"),
    ("ZAF", "South African Revenue Service tariff"),
)

#: Tarifs nationaux dont la désignation est publiée EN FRANÇAIS.
SOURCES_FR = (
    ("SEN", "Tarif extérieur commun CEDEAO (Sénégal)"),
    ("CIV", "Tarif extérieur commun CEDEAO (Côte d'Ivoire)"),
    ("BEN", "Tarif extérieur commun CEDEAO (Bénin)"),
    ("BFA", "Tarif extérieur commun CEDEAO (Burkina Faso)"),
    ("TGO", "Tarif extérieur commun CEDEAO (Togo)"),
    ("MLI", "Tarif extérieur commun CEDEAO (Mali)"),
    ("MRT", "Tarif des douanes de Mauritanie"),
    ("MAR", "Tarif des douanes du Maroc"),
    ("TUN", "Tarif douanier tunisien"),
)

CHAMPS_CODE = ("code_clean", "hs_code", "code", "code_raw", "national_code", "hs6")
CHAMPS_DESIGNATION = ("designation", "description_fr", "description_en", "name",
                      "description")


def _texte(valeur, langue: str) -> Optional[str]:
    """Extraire un libellé lisible, quelle que soit la forme du champ."""
    if isinstance(valeur, str):
        t = " ".join(valeur.split())
        return t if len(t) > 2 else None
    if isinstance(valeur, dict):
        for cle in (langue, "verbatim", "en", "fr"):
            t = valeur.get(cle)
            if isinstance(t, str):
                t = " ".join(t.split())
                if len(t) > 2:
                    return t
    return None


def _lignes(donnees):
    for cle in ("sub_positions", "positions", "tariff_lines"):
        for ligne in donnees.get(cle, []) or []:
            if isinstance(ligne, dict):
                yield ligne


def libelles_d_un_pays(iso: str, langue: str) -> Dict[str, str]:
    """Rendre {SH6: libellé} pour un tarif national déjà collecté."""
    chemin = CRAWLED / f"{iso}_tariffs.json"
    if not chemin.exists():
        return {}
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("%s illisible, ignoré", chemin.name)
        return {}
    out: Dict[str, str] = {}
    for ligne in _lignes(donnees):
        code = ""
        for champ in CHAMPS_CODE:
            brut = "".join(c for c in str(ligne.get(champ) or "") if c.isdigit())
            if len(brut) >= 6:
                code = brut[:6]
                break
        if not code:
            continue
        for champ in CHAMPS_DESIGNATION:
            t = _texte(ligne.get(champ), langue)
            if t:
                out.setdefault(code, t)
                break
    return out


def construire() -> Dict:
    table: Dict[str, Dict[str, str]] = {}
    couverture = {"fr": {}, "en": {}}
    for langue, sources in (("en", SOURCES_EN), ("fr", SOURCES_FR)):
        for iso, nom in sources:
            trouves = libelles_d_un_pays(iso, langue)
            neufs = 0
            for code, libelle in trouves.items():
                entree = table.setdefault(code, {})
                if langue not in entree:
                    entree[langue] = libelle
                    entree[f"{langue}_source"] = f"{iso} — {nom}"
                    neufs += 1
            if neufs:
                couverture[langue][iso] = neufs
                logger.info("  %s (%s) : %s libellés retenus", iso, langue, neufs)
    return {
        "schema_version": 1,
        "objet": (
            "Libellés SH6 en français et en anglais, EMPRUNTÉS aux tarifs nationaux "
            "déjà collectés — aucune traduction produite ici. Chaque libellé porte "
            "le pays et le tarif dont il vient."
        ),
        "niveau": "SH6",
        "avertissement": (
            "Ces libellés décrivent la sous-position SH6, PAS la subdivision "
            "nationale à huit ou dix chiffres. Le libellé national publié par le "
            "tarif du pays servi n'est jamais remplacé : il reste le verbatim qui "
            "fait foi."
        ),
        "table_ecartee": (
            "backend/data/hs6_database.json n'est PAS utilisée : ses colonnes "
            "description_fr et description_en ne se correspondent pas (010129 → "
            "« Autres » / « Horses » ; 300490 → « Autres » / « Medicaments »)."
        ),
        "couverture": {
            "sh6_total": len(table),
            "avec_fr": sum(1 for v in table.values() if "fr" in v),
            "avec_en": sum(1 for v in table.values() if "en" in v),
            "par_pays": couverture,
        },
        "libelles": table,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    donnees = construire()
    SORTIE.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )
    c = donnees["couverture"]
    logger.info(
        "%s SH6 — %s avec libellé français, %s avec libellé anglais → %s",
        c["sh6_total"], c["avec_fr"], c["avec_en"],
        os.path.relpath(SORTIE, RACINE),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
