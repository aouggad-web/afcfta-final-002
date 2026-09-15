"""
Moteur de liquidation — chantier L2.

Une fonction, cinq primitives d'assiette, un modificateur. Aucune connaissance
par pays : tout ce que le moteur sait d'un pays lui vient du socle.

Les cinq primitives, et rien d'autre :

===========================  ================================================
``CIF``                      la valeur en douane
``CIF+<CODES>``              la valeur en douane augmentée du montant des
                             droits nommés (``CIF+DD+TCI``), ou de tous les
                             prélèvements d'entrée (``CIF+TOUS_SAUF_TVA``,
                             ``CIF+TOUS_SAUF_SOI``)
``SOMME(TOUS_SAUF_SOI)``     la somme des autres droits, **sans** la valeur
``%DD``                      un pourcentage du *montant* du droit de douane
``xQTE``                     droit spécifique : montant unitaire × quantité
===========================  ================================================

Plus un modificateur, ``plafond``, qui borne l'assiette.

Trois règles gouvernent tout le reste :

1. **Un élément manquant ne vaut pas zéro.** Une ligne sans taux, sans assiette
   ou sans quantité ne produit pas de montant : elle produit un manque nommé, et
   le total est marqué ``PARTIEL``.
2. **Un total partiel se dit.** Un total qui omet une accise n'est pas prudent,
   il est faux — il doit annoncer ce qu'il omet.
3. **La préférence ne réduit que le droit de douane.** TVA, accises, redevances
   et prélèvements communautaires restent dus : c'est ce que liquide la douane.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

#: Familles dont un prélèvement relève, dans l'ordre de liquidation. Le socle
#: livre déjà ses droits dans cet ordre ; le moteur ne le recalcule pas.
FAMILLE_TVA = "tva"

COMPLET = "COMPLET"
PARTIEL = "PARTIEL"
INDISPONIBLE = "INDISPONIBLE"

CALCULE = "CALCULE"
MANQUE_TAUX = "TAUX_INDISPONIBLE"
MANQUE_ASSIETTE = "ASSIETTE_INDISPONIBLE"
MANQUE_QUANTITE = "QUANTITE_REQUISE"
MANQUE_CHANGE = "TAUX_DE_CHANGE_REQUIS"


def _montant_unitaire(specifique: Any) -> Optional[float]:
    """Rendre le montant unitaire d'un droit spécifique, déjà ramené à l'unité
    monétaire principale par le socle (« 8c/kg » vaut 0,08 et non 8).

    La forme héritée — une chaîne — est refusée plutôt que devinée : en lire le
    seul nombre multiplierait le droit par cent sur les tarifs publiés en
    centimes, ce qui est toute la SACU.
    """
    if isinstance(specifique, dict):
        montant = specifique.get("montant")
        return float(montant) if isinstance(montant, (int, float)) else None
    return None


def _codes_de_l_assiette(assiette: str) -> List[str]:
    """« CIF+DD+TCI » → ['DD', 'TCI']. Les formes globales rendent []."""
    reste = assiette.split("+", 1)[1] if "+" in assiette else ""
    return [c for c in reste.split("+") if c and not c.startswith("TOUS_")]


def _assiette_de(
    droit: Dict[str, Any],
    cif: float,
    calcules: List[Dict[str, Any]],
    quantite: Optional[float],
    taux_de_change: Optional[float],
):
    """Rendre (assiette, manque). Une assiette introuvable ne vaut jamais CIF."""
    assiette = droit.get("assiette")
    if not assiette:
        return None, MANQUE_ASSIETTE

    montants = {d["code"]: d["montant"] for d in calcules}

    if assiette == "xQTE":
        if quantite is None:
            return None, MANQUE_QUANTITE
        return quantite, None

    if assiette == "%DD":
        return montants.get("DD", 0.0), None

    if assiette == "SOMME(TOUS_SAUF_SOI)":
        base = sum(montants.values())
    elif assiette == "CIF":
        base = cif
    elif assiette.startswith("CIF+"):
        if "TOUS_SAUF_TVA" in assiette:
            base = cif + sum(d["montant"] for d in calcules if d["famille"] != FAMILLE_TVA)
        elif "TOUS_SAUF_SOI" in assiette:
            base = cif + sum(montants.values())
        else:
            base = cif + sum(montants.get(c, 0.0) for c in _codes_de_l_assiette(assiette))
    else:
        return None, MANQUE_ASSIETTE

    plafond = droit.get("plafond")
    if plafond:
        montant_max, devise = plafond.get("montant"), plafond.get("devise")
        if taux_de_change is None and devise:
            # Un plafond exprimé dans une autre devise que la valeur déclarée
            # exige une conversion. Sans elle, la borne est inconnue : on ne
            # l'ignore pas, on le dit.
            return None, MANQUE_CHANGE
        borne = montant_max * (taux_de_change or 1.0)
        base = min(base, borne)
    return base, None


def _liquider(
    droits: List[Dict[str, Any]],
    cif: float,
    quantite: Optional[float],
    taux_de_change: Optional[float],
    remise_dd_pct: Optional[float],
) -> Dict[str, Any]:
    lignes: List[Dict[str, Any]] = []
    calcules: List[Dict[str, Any]] = []
    manques: List[Dict[str, str]] = []

    for droit in droits:
        code = droit.get("code", "?")
        ligne = {
            "code": code,
            "libelle": droit.get("libelle", code),
            "famille": droit.get("famille", "autre"),
            "assiette": droit.get("assiette"),
            "taux_pct": droit.get("taux"),
            "source": droit.get("source"),
        }
        for champ in ("note", "classification_source", "assiette_non_traduite"):
            if droit.get(champ):
                ligne[champ] = droit[champ]

        taux = droit.get("taux")
        specifique = droit.get("specifique")
        if taux is None and specifique is not None:
            # Garde-fou : un droit spécifique se liquide toujours à la quantité.
            # Quelle que soit l'assiette déclarée, la lire comme ad valorem
            # transformerait « 8c/kg » en « 8 % » — un montant faux, et
            # crédible. Le socle pose déjà « xQTE » ; le moteur ne s'en remet
            # pas à lui sur ce point.
            droit = dict(droit, assiette="xQTE", plafond=None)
            ligne["assiette"] = "xQTE"
            taux = _montant_unitaire(specifique)
            ligne["montant_unitaire"] = taux
            ligne["specifique"] = (
                specifique.get("brut") if isinstance(specifique, dict) else specifique
            )
            if isinstance(specifique, dict):
                if specifique.get("unite_quantite"):
                    ligne["unite_quantite"] = specifique["unite_quantite"]
                if specifique.get("sous_unite_source"):
                    ligne["conversion"] = (
                        f"publié en {specifique['sous_unite_source']}, "
                        "ramené à l'unité monétaire principale"
                    )

        assiette, manque = _assiette_de(droit, cif, calcules, quantite, taux_de_change)
        if manque is None and taux is None:
            manque = MANQUE_TAUX

        if manque:
            ligne["statut"] = manque
            ligne["montant"] = None
            manques.append({"code": code, "motif": manque})
            lignes.append(ligne)
            continue

        if code == "DD" and remise_dd_pct is not None:
            ligne["taux_npf_pct"] = taux
            taux = remise_dd_pct
            ligne["taux_pct"] = taux
            ligne["regime_applique"] = "preference"

        # « xQTE » multiplie une quantité par un montant unitaire ; partout
        # ailleurs — « %DD » compris, où l'assiette est le montant du droit de
        # douane — le taux est un pourcentage.
        if droit.get("assiette") == "xQTE":
            montant = assiette * taux
        else:
            montant = assiette * taux / 100.0

        ligne.update({"base": round(assiette, 4), "montant": round(montant, 4), "statut": CALCULE})
        lignes.append(ligne)
        calcules.append({"code": code, "montant": montant, "famille": ligne["famille"]})

    total = sum(d["montant"] for d in calcules)
    return {
        "lignes": lignes,
        "manques": manques,
        "total_droits": round(total, 2),
        "total_a_payer": round(cif + total, 2),
        "taux_effectif_pct": round(total / cif * 100, 4) if cif else None,
        "etat": COMPLET if not manques else (INDISPONIBLE if not calcules else PARTIEL),
    }


def calculer(
    position: Dict[str, Any],
    valeur_cif: float,
    *,
    quantite: Optional[float] = None,
    taux_de_change: Optional[float] = None,
    preference_dd_pct: Optional[float] = None,
) -> Dict[str, Any]:
    """Liquider une position du socle, en NPF et — s'il y a lieu — en préférence.

    ``preference_dd_pct`` n'est passé que lorsque le régime préférentiel a été
    autorisé en amont : le moteur applique un taux, il ne décide pas du droit à
    la préférence. Il ne l'applique qu'au droit de douane.
    """
    if valeur_cif is None or valeur_cif < 0:
        raise ValueError("valeur_cif doit être un nombre positif")

    droits = position.get("droits") or []
    resultat = {
        "position": {
            "designation": position.get("designation"),
            "unite": position.get("unite"),
            "source": position.get("source"),
        },
        "valeur_cif": valeur_cif,
        "npf": _liquider(droits, valeur_cif, quantite, taux_de_change, None),
    }
    if preference_dd_pct is not None:
        resultat["preference"] = _liquider(
            droits, valeur_cif, quantite, taux_de_change, preference_dd_pct
        )
        economie = resultat["npf"]["total_droits"] - resultat["preference"]["total_droits"]
        resultat["economie"] = round(economie, 2)
    return resultat
