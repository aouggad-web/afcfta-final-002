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
- un antidumping vise les marchandises « imported from or originating in » les
  pays qu'il nomme (R.7991) : l'origine ET le pays d'expédition comptent. Il
  porte le taux du producteur déclaré, celui des « autres producteurs » pour un
  producteur non nommé, et reste à établir si le producteur n'est pas déclaré
  alors que le taux en dépend. Il n'est retiré que si ni l'origine ni le pays
  d'expédition, tous deux connus, ne sont visés ; une origine non visée dont
  l'expédition est inconnue (ou « AUTRE ») le laisse à établir, comme une
  origine et une expédition visées toutes deux mais différentes ;
- sans origine, une mesure qui ne vise pas toutes les origines reste à établir.

Une origine africaine ou une préférence ZLECAf n'écarte pas, à elle seule, une
mesure : seule la liste d'exemption de la mesure le fait."""

from __future__ import annotations

from datetime import date
from typing import Optional


#: Formes sociales ignorées pour comparer les noms (« Co. Ltd », « Corporation »).
FORMES_SOCIALES = frozenset({"co", "ltd", "limited", "corp", "corporation", "company", "inc", "sa", "plc", "the"})


def _normaliser(nom: str) -> str:
    """Nom sans casse, ponctuation ni forme sociale : « Nippon Steel Corporation »
    et « NIPPON STEEL CORP. » donnent tous deux « nippon steel »."""
    mots = "".join(c.lower() if c.isalnum() else " " for c in nom).split()
    return " ".join(m for m in mots if m not in FORMES_SOCIALES)


def _taux_producteur(regle_origine: dict, producteur: Optional[str]):
    """(taux, motif) pour l'origine visée ; taux None si le producteur manque."""
    if "taux" in regle_origine:
        return regle_origine["taux"], "taux unique pour l'origine"
    cherche = _normaliser(producteur or "")
    if not cherche:
        return None, None
    # Identité exacte (hors casse, ponctuation et forme sociale) : un fragment
    # (« Steel ») n'obtient jamais le taux réduit d'un producteur nommé.
    for groupe in regle_origine.get("producteurs", []):
        for nom in groupe["noms"]:
            if _normaliser(nom) == cherche:
                return groupe["taux"], f"producteur nommé : {nom}"
    if regle_origine.get("autres") is not None:
        return regle_origine["autres"], "producteur non nommé : taux des autres producteurs"
    return None, None


def _bareme(regle_origine: dict) -> str:
    if "taux" in regle_origine:
        return f"{regle_origine['taux']:g} %"
    morceaux = [
        f"{' ; '.join(g['noms'])} : {g['taux']:g} %" for g in regle_origine.get("producteurs", [])
    ]
    if regle_origine.get("autres") is not None:
        morceaux.append(f"autres producteurs : {regle_origine['autres']:g} %")
    return " ; ".join(morceaux)


def appliquer(position: dict, origine: Optional[str], producteur: Optional[str] = None,
              le: Optional[date] = None, expedition: Optional[str] = None):
    """Rendre (position, mesures) : la position aux lignes de défense
    commerciale résolues, et ce qui a été appliqué ou retiré."""
    le = le or date.today()
    origine = (origine or "").strip().upper() or None
    # « AUTRE » : expédiée d'un pays non précisé, autre que l'origine.
    expedition = (expedition or "").strip().upper() or None
    expedition_connue = expedition if expedition != "AUTRE" else None
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
        if origine in par_origine and expedition_connue in par_origine and expedition_connue != origine:
            note = (f"À établir : origine {origine} et expédition {expedition_connue} toutes deux visées "
                    f"({origine} : {_bareme(par_origine[origine])} ; {expedition_connue} : "
                    f"{_bareme(par_origine[expedition_connue])}). {droit.get('note', '')}")
            droits.append({**droit, "note": note.strip()})
            compte_rendu.append({**trace, "statut": "ORIGINE_PROVENANCE_DIVERGENTES", "origine": origine,
                                 "expedition": expedition_connue})
            continue
        if origine in par_origine:
            cle, motif_pays = origine, None
        elif expedition_connue in par_origine:
            cle, motif_pays = expedition_connue, f"expédiée de {expedition_connue}"
        elif expedition_connue:
            compte_rendu.append({**trace, "statut": "ORIGINE_NON_VISEE", "origine": origine,
                                 "expedition": expedition_connue})
            continue
        else:
            note = (f"À établir : dû aussi sur les marchandises expédiées de {', '.join(sorted(par_origine))} "
                    f"(« imported from or originating in ») ; préciser le pays d'expédition. "
                    f"{droit.get('note', '')}")
            droits.append({**droit, "note": note.strip()})
            compte_rendu.append({**trace, "statut": "EXPEDITION_NON_FOURNIE", "origine": origine})
            continue
        taux, motif = _taux_producteur(par_origine[cle], producteur)
        if taux is not None and motif_pays:
            motif = f"{motif_pays} ; {motif}"
        if taux is None:
            note = (f"À établir : le taux dépend du producteur ({_bareme(par_origine[cle])}) ; préciser "
                    f"le producteur. {droit.get('note', '')}")
            droits.append({**droit, "note": note.strip()})
            compte_rendu.append({**trace, "statut": "PRODUCTEUR_NON_FOURNI", "origine": origine,
                                 "pays_vise": cle})
            continue
        droits.append({**droit, "taux": taux, "assiette": regle["assiette"], "assiette_origine": "regle_de_pays",
                       "note": f"{motif}. {droit.get('note', '')}".strip()})
        compte_rendu.append({**trace, "statut": "APPLIQUEE", "origine": origine, "pays_vise": cle,
                                 "taux": taux, "motif": motif})
    if not modifie:
        return position, []
    return {**position, "droits": droits}, compte_rendu
