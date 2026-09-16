"""
Périmètre du régime préférentiel ZLECAf — chantier L3.

Ce module répond à une seule question : **quels prélèvements une préférence
réduit, et à quel taux.** Il rend au moteur une table ``{code: taux}`` ; le
moteur l'applique sans rien en déduire.

Deux verrous, dans cet ordre, et aucun ne se contourne :

1. **Le couloir doit être autorisé.** `zlecaf_implementation_registry` est
   *fail-closed* : il exige un instrument d'application en vigueur, un ensemble
   d'origines admises de façon réciproque et un barème au niveau de la ligne.
   `OFFER_ONLY` et `PARTNER_NOTICE_REQUIRED` n'autorisent rien. Une offre
   publiée n'est pas un droit dû.
2. **Le taux doit être tracé.** Il vient de la colonne préférentielle que la
   position porte, ou du calendrier national de démantèlement. À défaut, la
   préférence n'est pas servie — aucun taux n'est dérivé du NPF par un
   coefficient générique.

Et une règle que le cas algérien impose : **le périmètre est national.** Ce
n'est pas toujours le seul droit de douane. L'Algérie exonère aussi le DAPS
pour les produits des listes (A) et (B) admis sous ZLECAf. Ce périmètre est
déclaré ici, par pays, avec sa référence — jamais deviné, jamais généralisé.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

#: Régimes préférentiels que le socle conserve par position. Seule la colonne
#: ZLECAf vaut pour la ZLECAf : lire une colonne COMESA ou SADC comme telle
#: ferait payer à une origine un taux auquel elle n'a pas droit.
COLONNE_ZLECAF = "AFCFTA"


def _colonne_de_la_position(position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Rendre la colonne ZLECAf telle que le socle la porte : un taux ad
    valorem, ou un montant spécifique. Les deux formes existent — l'Afrique du
    Sud oppose « 8c/kg » en NPF à « 3,2c/kg » sous ZLECAf."""
    valeur = (position.get("preferentiels") or {}).get(COLONNE_ZLECAF)
    if isinstance(valeur, (int, float)):
        return {"taux": float(valeur)}
    if isinstance(valeur, dict):
        if valeur.get("taux") is not None:
            return {"taux": float(valeur["taux"])}
        specifique = valeur.get("specifique")
        if isinstance(specifique, dict) and specifique.get("montant") is not None:
            return {"taux": None, "specifique": specifique}
    return None


def _taux_npf(position: Dict[str, Any], code: str) -> Optional[float]:
    for droit in position.get("droits", []):
        if droit.get("code") == code:
            taux = droit.get("taux")
            return float(taux) if isinstance(taux, (int, float)) else None
    return None


def _perimetre_dza(hs_code: str, origine: str) -> Dict[str, str]:
    """Prélèvements algériens couverts, au-delà du droit de douane.

    Circulaire 482/2024, partie II-2 : « Les produits objet de ces deux listes
    (A) et (B), importés dans le cadre de la ZLECAf, sont exonérés du [DAPS] »,
    conformément à l'article 2 de la loi de finances complémentaire pour 2018.
    L'exonération est distincte du calendrier de démantèlement du droit de
    douane et ne vaut que pour une position effectivement admise.
    """
    try:
        from services.zlecaf_schedule_dza import daps_exempt
    except Exception:  # pragma: no cover - dépendance optionnelle
        return {}
    if daps_exempt(hs_code, origine):
        return {
            "DAPS": (
                "Circulaire 482/2024 partie II-2, art. 2 de la loi de finances "
                "complémentaire 2018 — exonération du DAPS sous ZLECAf"
            )
        }
    return {}


#: Périmètres nationaux au-delà du droit de douane. Une entrée absente signifie
#: « seul le droit de douane est démantelé », ce qui est la figure courante —
#: pas une règle générale, et surtout pas une déduction du moteur.
PERIMETRES_NATIONAUX = {"DZA": _perimetre_dza}


def taux_preferentiels(
    position: Dict[str, Any],
    destination_iso3: str,
    origine_iso3: str,
    hs_code: str,
) -> Dict[str, Any]:
    """Rendre la table ``{code: taux}`` applicable, et la justification du refus
    quand il n'y en a pas.

    Le résultat porte toujours ``applique``, ``statut`` et ``note`` : une
    préférence refusée doit dire pourquoi, sinon elle est indiscernable d'une
    absence de source.
    """
    from services.zlecaf_implementation_registry import implementation_decision

    decision = implementation_decision(destination_iso3, origine_iso3)
    resultat = {
        "applique": False,
        "statut": decision["status"],
        "note": decision["note"],
        "taux": {},
        "perimetre": {},
    }
    if not decision.get("applied"):
        return resultat

    taux_dd = _colonne_de_la_position(position)
    origine_taux = "colonne préférentielle de la position (socle)"

    if taux_dd is None and destination_iso3.upper() == "DZA":
        try:
            from services.zlecaf_schedule_dza import compute_dza_zlecaf_rate

            npf = _taux_npf(position, "DD")
            if npf is not None:
                # Signature : (hs_code, origin_iso3, normal_rate_pct). L'ordre
                # est significatif — origin_iso3 fait `.upper()` sur son
                # argument, un taux passé à sa place lève immédiatement.
                taux, origine_taux = compute_dza_zlecaf_rate(hs_code, origine_iso3, npf)
                taux_dd = {"taux": taux}
        except Exception as exc:  # pragma: no cover - dépendance optionnelle
            logger.warning("Calendrier ZLECAf DZA indisponible : %s", exc)

    if taux_dd is None:
        resultat["statut"] = "PREFERENCE_NON_TRACEE"
        resultat["note"] = (
            "Le couloir est autorisé, mais aucun taux préférentiel n'est tracé "
            "pour cette position — ni colonne ZLECAf au socle, ni calendrier "
            "national. Aucun taux n'est dérivé du NPF : régime NPF appliqué."
        )
        return resultat

    table = {"DD": taux_dd}
    perimetre = {"DD": origine_taux}

    etendue = PERIMETRES_NATIONAUX.get(destination_iso3.upper())
    if etendue:
        for code, reference in etendue(hs_code, origine_iso3).items():
            if _taux_npf(position, code) is not None:
                table[code] = {"taux": 0.0}
                perimetre[code] = reference

    resultat.update({"applique": True, "taux": table, "perimetre": perimetre})
    return resultat
