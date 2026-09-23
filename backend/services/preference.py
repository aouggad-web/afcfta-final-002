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

    elif taux_dd is None and destination_iso3.upper() == "KEN":
        # Le tarif kényan ne porte pas de colonne ZLECAf : le barème est publié
        # à part, par la Legal Notice EAC/321/2022. Contrairement au calendrier
        # algérien, celui-ci ne prend PAS le taux NPF — il lit une colonne
        # annuelle, et une position hors barème rend None plutôt que de se
        # déduire du plein droit.
        try:
            from services.zlecaf_schedule_ken import (
                compute_ken_zlecaf_rate,
                reserve_regle_d_origine,
            )

            taux, libelle = compute_ken_zlecaf_rate(hs_code, origine_iso3)
            if taux is not None:
                taux_dd = {"taux": taux}
                origine_taux = libelle
                # Servie, mais pas nécessairement accordée : voir la réserve.
                reserve = reserve_regle_d_origine(hs_code)
                if reserve:
                    resultat["reserve"] = reserve
        except Exception as exc:  # pragma: no cover - dépendance optionnelle
            logger.warning("Barème ZLECAf KEN indisponible : %s", exc)

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


#: Régimes régionaux dont le socle porte une colonne ET dont le roster est
#: sourcé dans le dépôt (``regional_blocs``). ``EU_UK``, ``EFTA`` et
#: ``MERCOSUR`` en sont absents : leurs colonnes existent bien au socle
#: sud-africain, mais ce calculateur sert des échanges intra-africains, et
#: aucun roster de ces accords n'est établi ici.
SIMULABLES = ("COMESA", "SADC")

#: États qui appartiennent au BLOC sans participer à sa ZONE DE LIBRE-ÉCHANGE.
#:
#: La distinction n'est pas théorique, et l'ignorer était un défaut réel de la
#: première version de ce lot : ``regional_blocs`` porte les rosters des BLOCS,
#: et les lire comme des rosters de ZLE aurait montré une simulation COMESA à
#: l'Éthiopie et à la RD Congo, qui n'y participent pas.
#:
#: La table ne retient que des EXCLUSIONS, jamais des ajouts, et c'est
#: délibéré : retirer un pays ne peut que faire disparaître une simulation,
#: tandis qu'en ajouter un accorderait une franchise indue. Face à deux sources
#: imparfaites, le sens sûr est celui qui montre moins.
#:
#: SADC — sadc.int, « Integration Milestones / Free Trade Area » (source
#: primaire) : « Thirteen out of fifteen SADC Member States are part of the
#: Free Trade Area, while Angola and Democratic Republic of Congo remain
#: outside. » Réserve : la page n'est pas datée et parle de 2015 au futur ;
#: elle annonce quinze membres quand la SADC en compte seize. L'exclusion peut
#: donc avoir changé — voir sources/SADC_fta_participants.texte-extrait.txt.
#:
#: COMESA — tralac, page régionale (source SECONDAIRE ; comesa.int rend ses
#: pages en JavaScript et n'énonce que le bloc) : la liste des participants à
#: la ZLE, « as of 2026 », ne comprend ni l'Éthiopie ni la RD Congo. Réserve :
#: le texte annonce 18 participants et en énumère 19. C'est l'ABSENCE de ces
#: deux États qui est retenue, non le dénombrement — une absence ne dépend pas
#: de savoir si le total juste est 18 ou 19. Les Seychelles, présentes dans la
#: liste tralac, manquent au roster COMESA du dépôt : elles ne reçoivent donc
#: aucune simulation. C'est une omission assumée, pas une franchise indue.
#: Voir sources/COMESA_fta_participants.texte-extrait.txt.
HORS_ZONE_DE_LIBRE_ECHANGE = {
    "COMESA": frozenset({"ETH", "COD"}),
    "SADC": frozenset({"AGO", "COD"}),
}


def _taux_colonne(position: Dict[str, Any], regime: str) -> Optional[float]:
    """Taux ad valorem publié par la position pour ce régime, sinon ``None``.

    Un montant spécifique n'est pas rendu : une simulation qui afficherait
    « 3,2c/kg » sans quantité ne dirait rien à l'opérateur, et la convertir
    en pourcentage demanderait un poids que la demande ne porte pas toujours.
    """
    valeur = (position.get("preferentiels") or {}).get(regime)
    if isinstance(valeur, (int, float)):
        return float(valeur)
    if isinstance(valeur, dict) and valeur.get("taux") is not None:
        return float(valeur["taux"])
    return None


def simulations_regionales(
    position: Dict[str, Any],
    destination_iso3: str,
    origine_iso3: str,
) -> list:
    """Simulations des régimes régionaux que le tarif publie pour ce couloir.

    Distincte de :func:`taux_preferentiels`, et la distinction est le fond du
    sujet. Cette fonction n'APPLIQUE rien : elle rend ce que le tarif national
    **publie** pour un régime dont les deux pays sont membres, en nommant la
    condition que le moteur ne vérifie pas.

    Le module refusait jusqu'ici de toucher aux zones de libre-échange, au
    motif que « les rendre à 0 % serait fabriquer une exonération ». Le motif
    vaut pour un taux SERVI ; il ne vaut pas pour un taux MONTRÉ avec sa
    réserve. Mesuré sur le socle : la position sud-africaine 020110 publie
    40 % en NPF, 40 % sous ZLECAf et **0 % sous SADC**. Un exportateur
    mozambicain — membre SADC au roster sourcé du dépôt — se voyait servir
    140 000 sur un CIF de 100 000, sans que rien ne lui signale la colonne à
    0 % que son tarif de destination publie pourtant. Taire une option n'est
    pas plus neutre que d'en inventer une.

    Trois bornes tenues :

    - **jamais appliqué** — ``applique`` vaut toujours ``False``. Le total
      servi reste celui du régime que :func:`taux_preferentiels` retient ;
    - **éligibilité par roster sourcé** — les deux pays doivent partager la
      zone selon ``regional_blocs``, dont chaque liste cite sa source ;
    - **réserve nommée** — la franchise dépend des règles d'origine et des
      listes sensibles du bloc, que ce moteur n'a pas. C'est une simulation,
      pas un droit acquis.

    Ordre **neutre** : tri alphabétique du code de régime. Classer par
    avantage orienterait l'opérateur vers le taux le plus bas, dont les règles
    d'origine sont précisément ce qui n'est pas vérifié.
    """
    from services.regional_blocs import FTA_NAMES, shared_free_trade_areas

    partages = set(shared_free_trade_areas(origine_iso3, destination_iso3))
    origine = (origine_iso3 or "").strip().upper()
    destination = (destination_iso3 or "").strip().upper()
    simulations = []
    for regime in sorted(SIMULABLES):
        if regime not in partages:
            continue
        # Appartenir au bloc ne suffit pas : il faut participer à sa zone de
        # libre-échange. L'un des deux pays hors zone, et la simulation n'a
        # pas lieu d'être.
        hors = HORS_ZONE_DE_LIBRE_ECHANGE.get(regime, frozenset())
        if origine in hors or destination in hors:
            continue
        taux = _taux_colonne(position, regime)
        if taux is None:
            continue
        simulations.append(
            {
                "regime": regime,
                "libelle": FTA_NAMES.get(regime, regime),
                "taux_publie_pct": taux,
                "prelevement": "DD",
                "applique": False,
                "eligibilite": "ORIGINE_ET_DESTINATION_MEMBRES",
                "source": "colonne préférentielle de la position (socle)",
                "reserve": (
                    "Simulation. La franchise dépend des règles d'origine et "
                    "des listes sensibles du bloc, que ce moteur ne vérifie "
                    "pas : le certificat d'origine reste à produire."
                ),
            }
        )

    # COLONNE NOMMEE POUR LE PAYS D'ORIGINE LUI-MEME.
    #
    # Tous les tarifs ne publient pas leurs préférences par BLOC. Le tarif
    # tunisien les publie par PARTENAIRE : « Code Pays 12 / ALGERIE / Taux
    # Préférentiel 0 % ». Il n'y a alors aucun roster à établir — la source
    # nomme elle-même le pays auquel la colonne s'applique, ce qui est une
    # preuve plus directe qu'une liste de membres reconstituée.
    #
    # La même discipline s'applique qu'aux blocs : la colonne est MONTRÉE,
    # jamais appliquée, avec la réserve d'origine nommée.
    bilaterale = _taux_colonne(position, origine)
    if bilaterale is not None and origine not in SIMULABLES:
        simulations.append(
            {
                "regime": origine,
                "libelle": f"Colonne préférentielle publiée pour {origine}",
                "taux_publie_pct": bilaterale,
                "prelevement": "DD",
                "applique": False,
                "eligibilite": "COLONNE_NOMMEE_POUR_CE_PAYS_PAR_LA_SOURCE",
                "source": "colonne préférentielle de la position (socle)",
                "reserve": (
                    "Simulation. Le tarif de destination publie cette colonne au "
                    "nom du pays d'origine ; la franchise reste subordonnée aux "
                    "règles d'origine de l'accord, que ce moteur ne vérifie pas. "
                    "Le certificat d'origine reste à produire."
                ),
            }
        )
    return simulations
