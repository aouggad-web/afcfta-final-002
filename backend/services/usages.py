"""Prélèvements que le tarif subordonne à l'usage déclaré de la marchandise.

Le socle porte, sur les positions concernées, la liste ``usages`` : pour
chaque usage, les lignes qu'il ajoute et celles qu'il retire (Égypte : la Taxe
de Table de 5 % d'un pesticide agricole, ou de 5 % au lieu de la TVA à usage
domestique). L'usage n'est pas une donnée que le calcul peut deviner : sans
déclaration, le régime courant est liquidé, et le bloc rendu nomme les autres
cas pour que l'opérateur les déclare.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def appliquer(
    position: Dict[str, Any], usage: Optional[str]
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Rendre (position, bloc) pour l'usage déclaré.

    ``bloc`` vaut ``None`` quand la position ne dépend d'aucun usage. Sinon il
    porte les usages possibles, l'usage déclaré et celui qui a été appliqué
    (``None`` : régime courant). La position du socle n'est pas modifiée.
    """
    possibles = position.get("usages") or []
    if not possibles:
        return position, None
    bloc = {
        "possibles": [
            {cle: u[cle] for cle in ("code", "libelle", "instruction", "texte")} for u in possibles
        ],
        "declare": usage,
        "applique": None,
    }
    choisi = next((u for u in possibles if u["code"] == usage), None)
    if choisi is None:
        bloc["note"] = (
            "Usage non déclaré : régime courant liquidé. Déclarer l'usage pour liquider le prélèvement qui s'y attache."
            if not usage
            else f"Usage « {usage} » sans effet sur cette position : régime courant liquidé."
        )
        return position, bloc

    droits = [dict(d) for d in position.get("droits") or [] if d.get("code") not in choisi["retirer"]]
    # Les lignes ajoutées s'assoient sur les prélèvements qui les précèdent :
    # elles passent avant la TVA, qui s'assied sur elles.
    rang = next((i for i, d in enumerate(droits) if d.get("famille") == "tva"), len(droits))
    droits[rang:rang] = [dict(d) for d in choisi["ajouter"]]
    bloc["applique"] = choisi["code"]
    return {**position, "droits": droits}, bloc
