#!/usr/bin/env python3
"""
Export CSV du tarif NPF de chaque pays, lu sur le socle de calcul.

Le socle (``backend/socle/<ISO>.json``) est un artefact de construction, exclu
du dépôt. Cet export en est l'archive versionnée : un fichier par pays, une
ligne par position nationale, le taux de chaque prélèvement et le total que
le moteur liquide pour 100 de valeur CAF, en devise nationale. La position
est préparée comme ``POST /api/calcul`` la prépare sans origine déclarée
(mesures de la gazette EAC en vigueur à la date de référence, TVA nationale
documentée quand la source n'en porte aucune) : l'export est le tarif que le
calculateur applique. Le SaaS le sert tel quel
(``GET /api/tariff-data/download-socle/<ISO>``).

``backend/data/exports/socle/MANIFESTE.json`` relie chaque fichier à
l'empreinte du socle dont il est tiré (``socle_sha256`` de
``backend/socle/MANIFESTE.json``). Un socle reconstruit sans réexport fait
échouer ``backend/tests/test_exports_socle.py``.

Règles :

- **rien de recalculé hors du moteur** : le total vient de ``calculer`` ; il
  reste vide quand la liquidation n'est pas complète (quantité requise, taux
  indisponible…) et la colonne « Manques » dit pourquoi ;
- un taux absent du socle s'écrit ``n.d.``, jamais ``0`` ;
- un droit spécifique ou composé s'écrit dans sa forme publiée ;
- une restriction ou une interdiction d'importation a sa colonne
  (« Importation interdite ») : elle ne se confond pas avec un taux manquant ;
- les notes du socle vont dans ``<ISO>_NPF_notes.csv`` : la ligne porte leurs
  renvois (``N1 N3``) plutôt que de répéter le même texte sur des milliers de
  positions.

Usage (après ``python3 scripts/build_socle.py``) :
    python3 scripts/exporter_tarifs_socle.py              # tous les pays
    python3 scripts/exporter_tarifs_socle.py COG TUN      # une sélection
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOCLE_DIR = os.path.join(REPO, "backend", "socle")
EXPORT_DIR = os.path.join(REPO, "backend", "data", "exports", "socle")
MANIFESTE_EXPORT = os.path.join(EXPORT_DIR, "MANIFESTE.json")

sys.path.insert(0, os.path.join(REPO, "backend"))
sys.path.insert(0, REPO)
from routes.calcul import _completer_famille_absente  # noqa: E402
from services import mesures_eac, socle  # noqa: E402
from services.calcul import calculer  # noqa: E402
from services.designation import texte_designation  # noqa: E402

ETATS_TOTAL = ("COMPLET", "INDICATIF")


def _nombre(valeur):
    return f"{valeur:g}"


def _cellule(droit):
    """La valeur d'un prélèvement, dans la forme où le socle la porte."""
    if droit.get("expression_brute"):
        return droit["expression_brute"]
    specifique = droit.get("specifique")
    if specifique:
        # La notation publiée (« 8c/kg ») plutôt que les champs normalisés,
        # dont l'unité monétaire peut être un marqueur interne
        # (« unite_principale »). La Tunisie publie le montant sans l'unité
        # de quantité (« 0.1 dinars ») : elle lui est ajoutée.
        forme = specifique.get("brut") or ""
        if not forme:
            if specifique.get("montant") is None:
                return "n.d."
            forme = f"{_nombre(specifique['montant'])} {specifique.get('unite_monetaire') or ''}".strip()
        unite = specifique.get("unite_quantite")
        if unite and "/" not in forme and " per " not in forme:
            forme = f"{forme}/{unite}"
        if droit.get("taux") is not None:
            forme = f"{_nombre(droit['taux'])} % + {forme}"
        return forme.strip()
    if droit.get("taux") is None:
        return "n.d."
    return _nombre(droit["taux"])


def _empreinte(chemin):
    with open(chemin, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _preparer(iso3, code, le, mesures):
    """La position telle que POST /api/calcul la liquide, sans origine ni
    usage déclarés : mesures de la gazette EAC en vigueur le ``le`` et TVA
    nationale documentée quand la source n'en porte aucune."""
    position, provenance = socle.position(iso3, code)
    if mesures:
        position, _ = mesures_eac.appliquer(position, iso3, code, le=le)
    position, _ = _completer_famille_absente(position, iso3, provenance)
    return position, provenance


def exporter(iso3, socle_manifeste, le=None):
    le = le or date.today()
    with open(os.path.join(SOCLE_DIR, f"{iso3}.json"), encoding="utf-8") as f:
        codes = sorted((json.load(f).get("positions") or {}))
    if not codes:
        return None
    # Le filtrage des mesures de la gazette par juridiction coûte ~1 ms par
    # appel : il n'est fait que pour les États qui en reçoivent.
    mesures = any(m.jurisdiction.strip().upper() == iso3 for m in mesures_eac._mesures())
    prepares = {code: _preparer(iso3, code, le, mesures) for code in codes}
    devise = socle.devise_nationale(iso3)

    colonnes = {}
    for position, _ in prepares.values():
        for droit in position["droits"]:
            colonnes.setdefault(droit["code"], droit.get("libelle") or "")

    notes = {}
    fichier = f"{iso3}_NPF.csv"
    chemin = os.path.join(EXPORT_DIR, fichier)
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(
            ["Position", "Désignation", "Chapitre", "Unité"]
            + [f"{code} ({libelle})" if libelle else code for code, libelle in colonnes.items()]
            + [f"Total droits et taxes pour 100 CAF ({devise})" if devise else "Total droits et taxes pour 100 CAF", "État", "Manques", "Restrictions", f"Notes (voir {iso3}_NPF_notes.csv)"]
        )
        for code, (position, provenance) in prepares.items():
            droits = {d["code"]: d for d in position["droits"]}
            npf = calculer(
                position,
                100.0,
                devise_position=provenance.get("devise_nationale"),
                couverture=provenance.get("couverture"),
            )["npf"]
            renvois = []
            for d in position["droits"]:
                if d.get("note"):
                    renvoi = notes.setdefault((d["code"], d["note"]), f"N{len(notes) + 1}")
                    if renvoi not in renvois:
                        renvois.append(renvoi)
            # Une interdiction ou une restriction d'importation n'est pas un
            # taux manquant : elle a sa colonne, et son texte publié sa note.
            restrictions = []
            for r in position.get("restrictions") or []:
                libelle = r.get("libelle_fr") or r.get("type") or r.get("kind") or "Restriction"
                if r.get("portee"):
                    libelle = f"{libelle} ({r['portee']})"
                if r.get("code_verbatim"):
                    libelle = f"{libelle} {r['code_verbatim']}"
                restrictions.append(libelle)
                texte = r.get("verbatim") or r.get("text_verbatim")
                if texte:
                    renvoi = notes.setdefault(("RESTRICTION", f"{texte} — {r.get('source') or ''}".rstrip(" —")), f"N{len(notes) + 1}")
                    if renvoi not in renvois:
                        renvois.append(renvoi)
            w.writerow(
                [code, " ".join((texte_designation(position.get("designation")) or "").split()), position.get("chapitre"), position.get("unite") or ""]
                + [_cellule(droits[c]) if c in droits else "" for c in colonnes]
                + [
                    _nombre(npf["total_droits"]) if npf["etat"] in ETATS_TOTAL else "",
                    npf["etat"],
                    " | ".join(f"{m['code']} ({m['motif']})" for m in npf.get("manques") or []),
                    " | ".join(restrictions),
                    " ".join(renvois),
                ]
            )

    fichier_notes = f"{iso3}_NPF_notes.csv"
    with open(os.path.join(EXPORT_DIR, fichier_notes), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(["Note", "Prélèvement", "Texte"])
        for (code, texte), renvoi in notes.items():
            w.writerow([renvoi, code, texte])

    entree = socle_manifeste["pays"][iso3]
    return {
        "fichier": fichier,
        "fichier_notes": fichier_notes,
        "positions": len(codes),
        "devise": devise,
        "date_reference": le.isoformat(),
        "sha256": _empreinte(chemin),
        "notes_sha256": _empreinte(os.path.join(EXPORT_DIR, fichier_notes)),
        "socle_sha256": entree["socle_sha256"],
        "collecte": entree.get("collecte"),
    }


def main(argv):
    with open(os.path.join(SOCLE_DIR, "MANIFESTE.json"), encoding="utf-8") as f:
        socle_manifeste = json.load(f)
    pays = [a.upper() for a in argv] or sorted(socle_manifeste["pays"])
    os.makedirs(EXPORT_DIR, exist_ok=True)

    manifeste = {"source": "backend/socle (scripts/build_socle.py)", "pays": {}}
    if os.path.exists(MANIFESTE_EXPORT):
        with open(MANIFESTE_EXPORT, encoding="utf-8") as f:
            manifeste = json.load(f)

    for iso3 in pays:
        entree = exporter(iso3, socle_manifeste)
        if entree is None:
            manifeste["pays"].pop(iso3, None)
            print(f"{iso3} : aucune position, pas d'export")
            continue
        manifeste["pays"][iso3] = entree
        print(f"{iso3} : {entree['positions']} positions -> {entree['fichier']}")

    manifeste["pays"] = dict(sorted(manifeste["pays"].items()))
    with open(MANIFESTE_EXPORT, "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
