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
``%<CODE>``                  un pourcentage du *montant* d'un autre droit,
                             désigné par son code (``%DD``)
``xQTE``                     droit spécifique : montant unitaire × quantité
===========================  ================================================

Plus un modificateur, ``plafond``, qui borne l'assiette.

Trois règles gouvernent tout le reste :

1. **Un élément manquant ne vaut pas zéro.** Une ligne sans taux, sans assiette
   ou sans quantité ne produit pas de montant : elle produit un manque nommé, et
   le total est marqué ``PARTIEL``.
2. **Un total partiel se dit.** Un total qui omet une accise n'est pas prudent,
   il est faux — il doit annoncer ce qu'il omet.
3. **La préférence ne réduit que les prélèvements qu'on lui désigne.** Lesquels
   relève du droit national, pas du moteur : l'Algérie exonère aussi le DAPS
   pour les produits des listes (A) et (B) admis sous ZLECAf (circulaire
   482/2024, partie II-2, citant l'art. 2 de la loi de finances complémentaire
   2018), quand ailleurs seul le droit de douane est démantelé. Le moteur reçoit
   donc la liste des taux préférentiels ; il ne la déduit jamais. Tout ce qui
   n'y figure pas reste dû au taux NPF.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

#: Le seul code que le moteur connaisse, et il lui vient de la grammaire des
#: assiettes : « CIF + tous les droits **sauf la TVA** » doit savoir laquelle
#: exclure. Tout le reste — quels prélèvements existent, dans quel ordre ils se
#: liquident, sur quelle assiette, et lesquels une préférence remise — vient du
#: socle ou de l'appelant. Aucune méthode nationale n'est figée ici.
FAMILLE_TVA = "tva"

COMPLET = "COMPLET"
PARTIEL = "PARTIEL"
INDISPONIBLE = "INDISPONIBLE"

CALCULE = "CALCULE"
MANQUE_TAUX = "TAUX_INDISPONIBLE"
MANQUE_ASSIETTE = "ASSIETTE_INDISPONIBLE"
MANQUE_QUANTITE = "QUANTITE_REQUISE"
MANQUE_CHANGE = "TAUX_DE_CHANGE_REQUIS"
MANQUE_COMPOSANT = "ASSIETTE_INCOMPLETE"


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


def _composants(
    codes: List[str],
    montants: Dict[str, float],
    codes_de_la_position: set,
):
    """Additionner les droits nommés par une assiette.

    Un code que l'assiette nomme peut manquer pour deux raisons opposées, et
    les confondre fausse le montant sans le dire :

    - il **n'existe pas sur cette position** : le prélèvement ne s'y applique
      pas, il ne contribue à rien, et c'est normal ;
    - il **existe mais n'a pas été liquidé** : l'assiette est alors amputée de
      sa part. Le compter pour zéro rendrait un montant trop faible, crédible
      et faux. On refuse de le faire.

    Retourne ``(somme, manquants, sans_objet)``.
    """
    somme = 0.0
    manquants, sans_objet = [], []
    for code in codes:
        if code in montants:
            somme += montants[code]
        elif code in codes_de_la_position:
            manquants.append(code)
        else:
            sans_objet.append(code)
    return somme, manquants, sans_objet


def _assiette_de(
    droit: Dict[str, Any],
    cif: float,
    calcules: List[Dict[str, Any]],
    quantite: Optional[float],
    taux_de_change: Optional[float],
    codes_de_la_position: set,
):
    """Rendre (assiette, manque, détail). Une assiette introuvable ne vaut
    jamais CIF, et une assiette amputée ne se complète jamais par un zéro."""
    assiette = droit.get("assiette")
    detail: Dict[str, Any] = {}
    if not assiette:
        return None, MANQUE_ASSIETTE, detail

    montants = {d["code"]: d["montant"] for d in calcules}

    if assiette == "xQTE":
        if quantite is None:
            return None, MANQUE_QUANTITE, detail
        return quantite, None, detail

    if assiette.startswith("%"):
        # Pourcentage du montant d'un autre droit, quel qu'il soit : le code est
        # dans l'assiette, il n'est pas connu du moteur.
        reference = assiette[1:]
        base, manquants, sans_objet = _composants([reference], montants, codes_de_la_position)
        if manquants or sans_objet:
            return None, MANQUE_COMPOSANT, {"composants_absents": [reference]}
        return base, None, detail

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
            part, manquants, sans_objet = _composants(
                _codes_de_l_assiette(assiette), montants, codes_de_la_position
            )
            if manquants:
                return None, MANQUE_COMPOSANT, {"composants_absents": manquants}
            if sans_objet:
                detail["composants_sans_objet"] = sans_objet
            base = cif + part
    else:
        return None, MANQUE_ASSIETTE, detail

    plafond = droit.get("plafond")
    if plafond:
        montant_max, devise = plafond.get("montant"), plafond.get("devise")
        if taux_de_change is None and devise:
            # Un plafond exprimé dans une autre devise que la valeur déclarée
            # exige une conversion. Sans elle, la borne est inconnue : on ne
            # l'ignore pas, on le dit.
            return None, MANQUE_CHANGE, detail
        borne = montant_max * (taux_de_change or 1.0)
        base = min(base, borne)
    return base, None, detail


def _liquider(
    droits: List[Dict[str, Any]],
    cif: float,
    quantite: Optional[float],
    taux_de_change: Optional[float],
    taux_preferentiels: Optional[Dict[str, float]],
) -> Dict[str, Any]:
    lignes: List[Dict[str, Any]] = []
    calcules: List[Dict[str, Any]] = []
    manques: List[Dict[str, Any]] = []
    codes_de_la_position = {d.get("code") for d in droits}

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

        assiette, manque, detail = _assiette_de(
            droit, cif, calcules, quantite, taux_de_change, codes_de_la_position
        )
        ligne.update(detail)
        if manque is None and taux is None:
            manque = MANQUE_TAUX

        if manque:
            ligne["statut"] = manque
            ligne["montant"] = None
            manque_detail = {"code": code, "motif": manque}
            if detail.get("composants_absents"):
                manque_detail["composants"] = detail["composants_absents"]
            manques.append(manque_detail)
            lignes.append(ligne)
            continue

        if taux_preferentiels and code in taux_preferentiels:
            ligne["taux_npf_pct"] = taux
            taux = taux_preferentiels[code]
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
    taux_preferentiels: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Liquider une position du socle, en NPF et — s'il y a lieu — en préférence.

    ``taux_preferentiels`` est une table ``{code: taux}`` établie en amont :
    le moteur applique des taux, il ne décide ni du droit à la préférence ni de
    son périmètre. Elle vaut souvent ``{"DD": 0}``, mais pas toujours — sous
    ZLECAf l'Algérie exonère aussi le DAPS, et l'y oublier surestimerait de
    70 points le droit liquidé sur les positions concernées. Tout prélèvement
    absent de la table reste dû à son taux NPF.
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
    if taux_preferentiels:
        resultat["preference"] = _liquider(
            droits, valeur_cif, quantite, taux_de_change, taux_preferentiels
        )
        resultat["preference"]["prelevements_remises"] = sorted(taux_preferentiels)
        economie = resultat["npf"]["total_droits"] - resultat["preference"]["total_droits"]
        resultat["economie"] = round(economie, 2)
    return resultat
