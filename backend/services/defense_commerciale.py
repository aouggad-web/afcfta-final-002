"""Mesures de défense commerciale (sauvegarde, antidumping) dues selon
l'origine déclarée et, pour l'antidumping, selon le producteur.

Le socle porte chaque mesure en ligne à taux non établi, marquée
« defense_commerciale » (scripts/build_socle.py, données dans
data/defense_commerciale/<ISO3>.json). La route la résout ici :

- hors de sa période (avant « debut » ou après « fin », date du calcul) ou pour
  une origine qu'elle ne vise pas ou qu'elle exempte, la ligne est retirée ;
- une sauvegarde qui vise l'origine porte son taux, sauf si la position couvre
  aussi des produits que la mesure ne vise pas (« condition_produit ») : la
  ligne reste alors à établir, avec la condition en note ;
- un antidumping qui vise l'origine porte le taux du producteur déclaré, celui
  des « autres producteurs » pour un producteur non nommé, et reste à établir
  si le producteur n'est pas déclaré alors que le taux en dépend ;
- sans origine, une mesure qui ne vise pas toutes les origines reste à établir.

Une origine africaine ou une préférence ZLECAf n'écarte pas, à elle seule, une
mesure : seule la liste d'exemption de la mesure le fait."""

from __future__ import annotations

from datetime import date
from typing import Optional


def _normaliser(nom: str) -> str:
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in nom).split())


def _taux_producteur(regle_origine: dict, producteur: Optional[str]):
    """(taux, motif) pour l'origine visée ; taux None si le producteur manque."""
    if "taux" in regle_origine:
        return regle_origine["taux"], "taux unique pour l'origine"
    if not producteur:
        return None, None
    cherche = _normaliser(producteur)
    for groupe in regle_origine.get("producteurs", []):
        for nom in groupe["noms"]:
            n = _normaliser(nom)
            if n and (n in cherche or cherche in n):
                return groupe["taux"], f"producteur nommé : {nom}"
    if regle_origine.get("autres") is not None:
        return regle_origine["autres"], "producteur non nommé : taux des autres producteurs"
    return None, None


def _bareme(regle_origine: dict) -> str:
    morceaux = [
        f"{' ; '.join(g['noms'])} : {g['taux']:g} %" for g in regle_origine.get("producteurs", [])
    ]
    if regle_origine.get("autres") is not None:
        morceaux.append(f"autres producteurs : {regle_origine['autres']:g} %")
    return " ; ".join(morceaux)


def appliquer(position: dict, origine: Optional[str], producteur: Optional[str] = None,
              le: Optional[date] = None):
    """Rendre (position, mesures) : la position aux lignes de défense
    commerciale résolues, et ce qui a été appliqué ou retiré."""
    le = le or date.today()
    origine = (origine or "").strip().upper() or None
    droits, compte_rendu = [], []
    modifie = False
    for droit in position.get("droits") or []:
        regle = droit.get("defense_commerciale")
        if not regle:
            droits.append(droit)
            continue
        modifie = True
        debut = date.fromisoformat(regle["debut"]) if regle.get("debut") else None
        fin = date.fromisoformat(regle["fin"]) if regle.get("fin") else None
        trace = {"code": droit.get("code"), "mesure": regle.get("id"), "type": regle.get("type")}
        if (debut and le < debut) or (fin and le > fin):
            compte_rendu.append({**trace, "statut": "HORS_PERIODE"})
            continue
        if regle.get("type") == "sauvegarde":
            if origine and origine in (regle.get("exemptees") or []):
                compte_rendu.append({**trace, "statut": "ORIGINE_EXEMPTEE", "origine": origine})
                continue
            if regle.get("origines") != "TOUTES" and origine and origine not in (regle.get("origines") or []):
                compte_rendu.append({**trace, "statut": "ORIGINE_NON_VISEE", "origine": origine})
                continue
            if regle.get("origines") != "TOUTES" and not origine:
                droits.append({**droit, "note": "À établir : dépend de l'origine. " + droit.get("note", "")})
                compte_rendu.append({**trace, "statut": "ORIGINE_NON_FOURNIE"})
                continue
            if regle.get("condition_produit"):
                note = (f"À établir : {regle['taux']:g} % pour les seules {regle['condition_produit']} ; la "
                        f"position couvre d'autres produits. {droit.get('note', '')}")
                droits.append({**droit, "note": note.strip()})
                compte_rendu.append({**trace, "statut": "CONDITION_PRODUIT", "taux": regle["taux"]})
                continue
            droits.append({**droit, "taux": regle["taux"], "assiette": regle["assiette"],
                           "assiette_origine": "regle_de_pays"})
            compte_rendu.append({**trace, "statut": "APPLIQUEE", "taux": regle["taux"]})
            continue
        # Antidumping : par origine, puis par producteur.
        par_origine = regle.get("par_origine") or {}
        if not origine:
            note = (f"À établir : dû sur les importations de {', '.join(sorted(par_origine))} ; préciser "
                    f"l'origine. {droit.get('note', '')}")
            droits.append({**droit, "note": note.strip()})
            compte_rendu.append({**trace, "statut": "ORIGINE_NON_FOURNIE"})
            continue
        if origine not in par_origine:
            compte_rendu.append({**trace, "statut": "ORIGINE_NON_VISEE", "origine": origine})
            continue
        taux, motif = _taux_producteur(par_origine[origine], producteur)
        if taux is None:
            note = (f"À établir : le taux dépend du producteur ({_bareme(par_origine[origine])}) ; préciser "
                    f"le producteur. {droit.get('note', '')}")
            droits.append({**droit, "note": note.strip()})
            compte_rendu.append({**trace, "statut": "PRODUCTEUR_NON_FOURNI", "origine": origine})
            continue
        droits.append({**droit, "taux": taux, "assiette": regle["assiette"], "assiette_origine": "regle_de_pays",
                       "note": f"{motif}. {droit.get('note', '')}".strip()})
        compte_rendu.append({**trace, "statut": "APPLIQUEE", "origine": origine, "taux": taux, "motif": motif})
    if not modifie:
        return position, []
    return {**position, "droits": droits}, compte_rendu
