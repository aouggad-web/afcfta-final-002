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

    Le résultat porte toujours ``applique``, ``statut``, ``note`` et
    ``regime`` : une préférence refusée doit dire pourquoi, sinon elle est
    indiscernable d'une absence de source.

    ``regime`` distingue les deux régimes possibles, parce que les confondre
    serait faux : ``UNION_DOUANIERE`` pour la libre circulation intra-bloc,
    ``ZLECAF`` pour la préférence continentale.
    """
    union = _union_douaniere(destination_iso3, origine_iso3)
    if union:
        return union

    from services.zlecaf_implementation_registry import implementation_decision

    decision = implementation_decision(destination_iso3, origine_iso3)
    resultat = {
        "applique": False,
        "regime": "ZLECAF",
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


def _union_douaniere(destination_iso3: str, origine_iso3: str) -> Optional[Dict[str, Any]]:
    """Libre circulation intra-union douanière — prioritaire sur la ZLECAf.

    Deux pays d'une même union douanière (SACU, EAC, CEMAC, UEMOA) échangent
    sous le régime de leur union, pas sous la ZLECAf : le droit de douane
    intra-bloc est nul par définition du marché unique, indépendamment de la
    nomenclature du produit et de l'état de ratification de la ZLECAf. La
    newsletter dtic/SARS « Update on the AfCFTA » (mars 2026, FAQ Q1) le dit
    sans détour pour l'Afrique du Sud : elle « n'échangera pas de façon
    préférentielle avec les États membres de la SACU et de la SADC sous la
    ZLECAf ».

    Le périmètre est le seul droit de douane. La franchise intra-union porte
    sur lui, pas sur la fiscalité interne : TVA et accises restent dues, et
    les y étendre ferait disparaître des taxes réellement perçues.

    Les zones de libre-échange (CEDEAO, SADC, COMESA) ne sont **pas** traitées
    ici : leur franchise dépend des règles d'origine et des listes sensibles
    du bloc, que ce moteur n'a pas. Les rendre à 0 % serait fabriquer une
    exonération — elles restent au NPF.
    """
    from services.regional_blocs import CUSTOMS_UNION_NAMES, same_customs_union

    bloc = same_customs_union(origine_iso3, destination_iso3)
    if not bloc:
        return None
    libelle = CUSTOMS_UNION_NAMES.get(bloc, bloc)
    return {
        "applique": True,
        "regime": "UNION_DOUANIERE",
        "code_bloc": bloc,
        "libelle_bloc": libelle,
        "statut": "LIBRE_CIRCULATION",
        # Cette note est ce que l'interface affiche : le bandeau « union
        # douanière » de `CalculatorTab` rend `trade_regime_note` telle quelle.
        # Elle dit donc les trois choses que l'importateur doit savoir — le
        # droit est nul, ce régime prime sur la ZLECAf et lui est plus
        # favorable, et la fiscalité interne reste due.
        "note": (
            f"Ces deux pays sont membres de la même union douanière ({libelle}) : "
            "leurs échanges se font en libre circulation, droit de douane 0 %, "
            "sans passer par la ZLECAf. Ce régime est plus avantageux que le "
            "démantèlement progressif de la ZLECAf, et s'applique indépendamment "
            "d'elle. La franchise porte sur le seul droit de douane : TVA, accises "
            "et autres taxes intérieures restent dues."
        ),
        "taux": {"DD": {"taux": 0.0}},
        "perimetre": {
            "DD": (
                f"Libre circulation intra-{bloc} (tarif extérieur commun et "
                "franchise intérieure de l'union douanière)"
            )
        },
    }
