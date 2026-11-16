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


def _colonne_de_la_position(
    position: Dict[str, Any], colonne: str = COLONNE_ZLECAF
) -> Optional[Dict[str, Any]]:
    """Rendre la colonne ZLECAf telle que le socle la porte : un taux ad
    valorem, ou un montant spécifique. Les deux formes existent — l'Afrique du
    Sud oppose « 8c/kg » en NPF à « 3,2c/kg » sous ZLECAf."""
    valeur = (position.get("preferentiels") or {}).get(colonne)
    if isinstance(valeur, (int, float)):
        return {"taux": float(valeur)}
    if isinstance(valeur, dict):
        if (
            valeur.get("cumulatif")
            and valeur.get("taux") is not None
            and valeur.get("specifique") is not None
        ):
            # « 7%+SCR5/kg » : les deux composantes sont dues ; le moteur les
            # additionne.
            return {
                "taux": float(valeur["taux"]),
                "specifique": valeur["specifique"],
                "cumulatif": True,
                "expression_brute": valeur.get("expression_brute") or "",
            }
        if (
            valeur.get("compose")
            and valeur.get("taux") is not None
            and valeur.get("specifique") is not None
        ):
            # Droit composé (« 40% or 240c/kg ») : les deux composantes
            # sortent, avec la règle de départage que le socle porte (SARS,
            # General Notes B.3, qui vaut pour chaque colonne). Sans règle, le
            # moteur refuse de liquider au lieu de servir le seul ad valorem.
            col = {
                "taux": float(valeur["taux"]),
                "specifique": valeur["specifique"],
                "compose": True,
                "expression_brute": valeur.get("expression_brute") or "",
            }
            if valeur.get("regle_composee"):
                col["regle_composee"] = valeur["regle_composee"]
            if valeur.get("deduction_ad_valorem_pct") is not None:
                col["deduction_ad_valorem_pct"] = float(valeur["deduction_ad_valorem_pct"])
            return col
        if valeur.get("taux") is not None:
            return {"taux": float(valeur["taux"])}
        specifique = valeur.get("specifique")
        if isinstance(specifique, dict) and specifique.get("montant") is not None:
            col = {"taux": None, "specifique": specifique}
            # « 180c/kg with a maximum of 38,4 % » : la borne voyage avec la
            # colonne — jamais le plafond du NPF à sa place.
            if valeur.get("plafond_ad_valorem_pct") is not None:
                col["plafond_ad_valorem_pct"] = float(valeur["plafond_ad_valorem_pct"])
                col["expression_brute"] = valeur.get("expression_brute") or ""
            # « 344c/kg less 34% » : la déduction aussi — sans elle, la colonne
            # servirait le spécifique entier.
            if valeur.get("deduction_ad_valorem_pct") is not None:
                col["deduction_ad_valorem_pct"] = float(valeur["deduction_ad_valorem_pct"])
            return col
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


def _perimetre_mar(hs_code: str, origine: str) -> Dict[str, Any]:
    """TPI marocaine démantelée avec le DI (circulaire ADII 6530/223, III).

    Le texte soumet la liste A au démantèlement du droit d'importation ET de
    la taxe parafiscale à l'importation, sur le même calendrier — 5 ans pour
    P1, 10 ans pour P2, à compter du 01/01/2021. La TPI n'est donc pas
    exonérée d'un coup comme le DAPS algérien : elle suit la part restante de
    l'année. Le facteur est rendu ici ; l'appelant l'applique à la TPI que
    porte la position, qu'il est seul à connaître.
    """
    try:
        from services.zlecaf_schedule_mar import (
            REFERENCE_TPI,
            origine_admise,
            part_restante,
        )
    except Exception:  # pragma: no cover - dépendance optionnelle
        return {}
    if not origine_admise(origine):
        return {}
    part = part_restante(origine)
    if part is None or part >= 1.0:
        return {}
    return {"TPI": {"facteur": part, "reference": REFERENCE_TPI}}


#: Périmètres nationaux au-delà du droit de douane. Une entrée absente signifie
#: « seul le droit de douane est démantelé », ce qui est la figure courante —
#: pas une règle générale, et surtout pas une déduction du moteur.
PERIMETRES_NATIONAUX = {"DZA": _perimetre_dza, "MAR": _perimetre_mar}

#: Destinations dont le taux ZLECAf se calcule depuis le NPF par un calendrier
#: national, faute de colonne préférentielle au socle : DZA (circulaire DGD
#: 482/2024) et EGY (circulaires 38/2024 et 44/2025, liste A seulement — voir
#: services/zlecaf_schedule_egy.py). Une destination absente d'ici ne reçoit
#: aucun taux inventé.
DESTINATIONS_A_CALENDRIER_NATIONAL = frozenset({"DZA", "EGY"})


def _destination_regle_b_eac(destination_iso3: str) -> bool:
    """Règle B (27/09/2026) : destinations EAC dont le taux ZLECAf est servi —
    l'ensemble est défini une seule fois dans zlecaf_implementation_registry."""
    from services.zlecaf_implementation_registry import DESTINATIONS_REGLE_B_EAC

    return destination_iso3.upper() in DESTINATIONS_REGLE_B_EAC


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

    ``regime`` distingue les régimes possibles, parce que les confondre
    serait faux : ``UNION_DOUANIERE`` pour la libre circulation intra-bloc,
    ``GZALE`` pour la zone arabe (importation en Algérie, ou en Tunisie et en
    Libye depuis l'Algérie et ses partenaires arabes) quand elle est plus
    favorable que la ZLECAf, ``ZLECAF`` pour la préférence continentale.
    """
    union = _union_douaniere(destination_iso3, origine_iso3)
    if union:
        return union
    from services.regional_blocs import NOTE_UNION_NON_EFFECTIVE, union_non_effective

    non_effective = union_non_effective(origine_iso3, destination_iso3)
    if non_effective:
        # Union douanière dont l'un des deux pays n'applique pas le régime
        # (RDC dans l'EAC) : pas de libre circulation, et la raison est dite.
        resultat = _taux_preferentiels_hors_union(position, destination_iso3, origine_iso3, hs_code)
        return {**resultat, "union_non_effective": non_effective,
                "note": NOTE_UNION_NON_EFFECTIVE[non_effective] + " " + (resultat.get("note") or "")}
    zlecaf = _taux_preferentiels_hors_union(position, destination_iso3, origine_iso3, hs_code)
    return _choisir_gzale_ou_zlecaf(position, destination_iso3, origine_iso3, zlecaf)


#: Grande zone arabe de libre-échange (GZALE) à l'importation en Algérie —
#: origines AFRICAINES membres de la zone (le calculateur ne sert que
#: l'Afrique). La Mauritanie, les Comores, Djibouti et la Somalie, membres de
#: la Ligue arabe, n'appliquent pas la zone et en sont absents.
GZALE_ORIGINES_DZA = frozenset({"EGY", "LBY", "MAR", "SDN", "TUN"})

#: Membres africains de la GZALE. Pour la colonne libyenne « États de la Ligue
#: des États arabes », seuls ceux-là sont servis : membres de la Ligue ET de la
#: zone, ils relèvent de la colonne quelle que soit la composition que la
#: douane libyenne retient — question que nulle source consultée ne tranche.
GZALE_MEMBRES_AFRICAINS = GZALE_ORIGINES_DZA | {"DZA"}

REFERENCE_GZALE_DZA = (
    "GZALE (adhésion de l'Algérie au 01/01/2009) ; liste négative algérienne "
    "supprimée au 01/01/2022, télex DGD n° 516/DGD/D042.21 du 24/12/2021 — "
    "exonération du seul droit de douane"
)
REFERENCE_ZALE_TUN = (
    "Tarif Web 2026 de la douane tunisienne, taux préférentiel publié pour "
    "« ALGERIE » (code pays 12), zone « ZALE » — droit de douane seulement"
)
REFERENCE_LIGUE_LBY = (
    "Tarif douanier libyen (customs.gov.ly), colonne « التعريفة التفضيلية لدول "
    "جامعة الدول العربية » — droit de douane seulement"
)

CONDITIONS_ORIGINE_ARABE = (
    "Conditions : certificat d'origine arabe (valeur ajoutée locale d'au moins "
    "40 %) et transport direct."
)


def _colonne_publiee(position: Dict[str, Any], colonne: str) -> Optional[float]:
    """Taux ad valorem que la position publie dans ``colonne``, sinon None."""
    valeur = (position.get("preferentiels") or {}).get(colonne)
    if isinstance(valeur, (int, float)):
        return float(valeur)
    if isinstance(valeur, dict) and valeur.get("taux") is not None and not valeur.get("specifique"):
        return float(valeur["taux"])
    return None


def _zone_arabe(position: Dict[str, Any], destination_iso3: str, origine_iso3: str) -> Optional[Dict[str, Any]]:
    """Préférence de la zone arabe ouverte à ce couloir et à cette position.

    Trois destinations, chacune sur sa propre preuve, et le seul droit de
    douane chaque fois :

    - **Algérie** : 0 % sur tout le tarif pour les origines de
      ``GZALE_ORIGINES_DZA`` (fiche DZA_GZALE_2026-11-02.json) ;
    - **Tunisie**, origine algérienne : le taux de la colonne « ALGERIE » que le
      Tarif Web publie ligne par ligne ; une ligne sans colonne reste au NPF ;
    - **Libye**, origine membre africain de la GZALE : la colonne « États de la
      Ligue des États arabes » du tarif libyen ; même règle.

    Fiche DZA_GZALE_export_2026-11-02.json pour les deux dernières.
    """
    destination = (destination_iso3 or "").upper()
    origine = (origine_iso3 or "").upper()
    if destination == "DZA" and origine in GZALE_ORIGINES_DZA:
        daps = ""
        if (_taux_npf(position, "DAPS") or 0) > 0:
            daps = (
                "Le DAPS reste dû : la liste en vigueur (arrêté du 8 avril 2019, "
                "JO n° 26) ne distingue pas l'origine. "
            )
        return {
            "taux": 0.0,
            "code_bloc": "GZALE",
            "libelle_bloc": "Grande zone arabe de libre-échange",
            "reference": REFERENCE_GZALE_DZA,
            "note": (
                "Grande zone arabe de libre-échange (GZALE) : droit de douane 0 % "
                "pour les produits d'origine arabe, la liste négative algérienne "
                "étant supprimée depuis le 1er janvier 2022 (télex DGD "
                f"n° 516/DGD/D042.21). {CONDITIONS_ORIGINE_ARABE} Seul le droit "
                "de douane est exonéré : TVA, TCS et autres taxes restent dues. "
                f"{daps}"
            ),
        }
    if destination == "TUN" and origine == "DZA":
        taux = _colonne_publiee(position, "DZA")
        if taux is None:
            return None
        return {
            "taux": taux,
            "code_bloc": "ZALE",
            "libelle_bloc": "Zone arabe de libre-échange (ZALE) et accord tuniso-algérien",
            "reference": REFERENCE_ZALE_TUN,
            "note": (
                f"Droit de douane {taux:g} % : taux préférentiel que la douane "
                "tunisienne publie pour l'Algérie, zone « ZALE » (Tarif Web 2026). "
                f"{CONDITIONS_ORIGINE_ARABE} "
                "Seul le droit de douane est réduit : les autres droits et taxes "
                "restent dus. "
            ),
        }
    if destination == "LBY" and origine in GZALE_MEMBRES_AFRICAINS:
        taux = _colonne_publiee(position, "LIGUE_ARABE")
        if taux is None:
            return None
        return {
            "taux": taux,
            "code_bloc": "GZALE",
            "libelle_bloc": "Tarif préférentiel des États de la Ligue arabe (Libye)",
            "reference": REFERENCE_LIGUE_LBY,
            "note": (
                f"Droit de douane {taux:g} % : colonne « tarif préférentiel pour les "
                "États de la Ligue des États arabes » du tarif libyen, servie aux "
                f"membres africains de la GZALE. {CONDITIONS_ORIGINE_ARABE} Seul "
                "le droit de douane est réduit : les autres droits et taxes "
                "restent dus. "
            ),
        }
    return None


def _charge_restante(position: Dict[str, Any], table: Dict[str, Any], codes) -> Optional[float]:
    """Somme des taux restant dus sur ``codes`` sous la table ``table``.

    Un code absent de la table reste au NPF ; un taux préférentiel est
    plafonné au NPF, comme le moteur le fait (plancher NPF). ``None`` quand un
    taux manque : la comparaison n'est alors pas faite.
    """
    total = 0.0
    for code in codes:
        npf = _taux_npf(position, code)
        entree = table.get(code)
        taux = entree.get("taux") if isinstance(entree, dict) else npf
        if taux is None:
            return None
        if npf is not None:
            taux = min(float(taux), npf)
        total += float(taux)
    return total


def _choisir_gzale_ou_zlecaf(
    position: Dict[str, Any],
    destination_iso3: str,
    origine_iso3: str,
    zlecaf: Dict[str, Any],
) -> Dict[str, Any]:
    """Retenir le plus favorable de la zone arabe et de la ZLECAf — un seul
    régime par importation, jamais un mélange.

    La zone arabe réduit le seul droit de douane. À l'importation en Algérie,
    le DAPS reste dû : la liste en vigueur (arrêtés du 26 janvier et du 8 avril
    2019) ne distingue pas l'origine, et la loi de finances 2023 (art. 57)
    n'en exonère qu'en vertu d'une disposition particulière d'un accord. La
    ZLECAf, elle, exonère le DAPS des listes (A) et (B) (circulaire
    482/2024). Ni l'un ni l'autre ne l'emporte donc toujours : la comparaison
    porte sur le droit de douane et sur chaque prélèvement que la ZLECAf
    réduit, position par position. À égalité, la ZLECAf est conservée.
    Fiches DZA_GZALE_2026-11-02.json et DZA_GZALE_export_2026-11-02.json.
    """
    zone = _zone_arabe(position, destination_iso3, origine_iso3)
    if zone is None:
        return zlecaf

    table_zone = {"DD": {"taux": zone["taux"]}}
    if zlecaf.get("applique"):
        codes = {"DD"} | set(zlecaf.get("taux") or {})
        charge_zlecaf = _charge_restante(position, zlecaf["taux"], codes)
        charge_zone = _charge_restante(position, table_zone, codes)
        if charge_zlecaf is None or charge_zone is None or charge_zlecaf <= charge_zone:
            note = (
                f"{zlecaf.get('note') or ''} La zone arabe ({zone['code_bloc']}) est "
                f"aussi ouverte à cette origine (droit de douane {zone['taux']:g} %) ; "
                "la ZLECAf, au moins aussi favorable pour cette position, est retenue."
            ).strip()
            return {**zlecaf, "note": note}
        motif_zlecaf = (
            "La ZLECAf s'applique aussi à cette origine, mais elle est moins "
            "favorable pour cette position."
        )
    else:
        motif_zlecaf = "La ZLECAf n'est pas appliquée à cette origine."
    return {
        "applique": True,
        "regime": "GZALE",
        "code_bloc": zone["code_bloc"],
        "libelle_bloc": zone["libelle_bloc"],
        "statut": "FRANCHISE_ZONE_LIBRE_ECHANGE",
        # Affichée telle quelle dans le bandeau « régime sous conditions ».
        "note": f"{zone['note']}{motif_zlecaf}",
        "zlecaf": {"statut": zlecaf.get("statut"), "note": zlecaf.get("note")},
        "taux": table_zone,
        "perimetre": {"DD": zone["reference"]},
    }


def _taux_preferentiels_hors_union(
    position: Dict[str, Any],
    destination_iso3: str,
    origine_iso3: str,
    hs_code: str,
) -> Dict[str, Any]:
    """Préférence ZLECAf (ou refus motivé), hors union douanière."""

    if destination_iso3.upper() == "ZAF":
        # Défaut corrigé (règle ZAF) : le socle portait la colonne AfCFTA de
        # la ZAF sans contrôler l'origine. La liste des partenaires et leurs
        # dates d'entrée viennent de la General Note O du Schedule No. 1 —
        # même contrôle que le chemin historique.
        from services.zlecaf_schedule_zaf import (
            zaf_partner_active,
            zaf_suspension_active,
        )

        origine_zaf = (origine_iso3 or "").upper()
        if zaf_suspension_active(origine_zaf, hs_code):
            # Suspension unilatérale (ex. R.6594 : thé 0902.40 du Kenya, à
            # partir du 12/09/2025) — NPF, avec la notice.
            return {
                "applique": False,
                "regime": "ZLECAF",
                "statut": "PREFERENCE_SUSPENDUE",
                "note": (
                    "Préférence ZLECAf suspendue par l'Afrique du Sud pour "
                    "cette ligne (Notice R.6594, GG 53334 du 12/09/2025) — "
                    "taux NPF appliqué."
                ),
                "taux": {},
                "perimetre": {},
            }
        if not zaf_partner_active(origine_zaf):
            return {
                "applique": False,
                "regime": "ZLECAF",
                "statut": "PENDING_PARTNER",
                "note": (
                    "ZLECAf ratifié mais échanges préférentiels pas encore "
                    "activés avec l'Afrique du Sud pour cette origine "
                    "(General Note O du Schedule No. 1) — taux NPF appliqué."
                ),
                "taux": {},
                "perimetre": {},
            }

    if destination_iso3.upper() == "NAM":
        # Règle SACU (25/10/2026) : origines de la General Note O namibienne
        # (GN 390/2024, GN 229/2025) ; taux de la colonne AfCFTA du tarif
        # commun SACU le plus à jour, celui du socle (décision du 25/10/2026).
        from services.zlecaf_schedule_nam import nam_partner_active

        if not nam_partner_active(origine_iso3):
            return {
                "applique": False,
                "regime": "ZLECAF",
                "statut": "PENDING_PARTNER",
                "note": (
                    "Origine absente de la General Note O du Schedule No. 1 "
                    "namibien (GN 390/2024, GN 229/2025) — taux NPF appliqué."
                ),
                "taux": {},
                "perimetre": {},
            }

    from services.zlecaf_implementation_registry import implementation_decision

    if destination_iso3.upper() in ("ZAF", "NAM"):
        # L'Afrique du Sud et la Namibie échappent au registre : leur
        # application est établie par la General Note O de leur Schedule
        # No. 1, pas par la règle B EAC. La branche ZAF ci-dessous sert le
        # même taux que l'historique.
        decision = None
    else:
        decision = implementation_decision(destination_iso3, origine_iso3)
    resultat = {
        "applique": False,
        "regime": "ZLECAF",
        "statut": decision["status"] if decision else "PENDING_PARTNER",
        "note": decision["note"] if decision else "",
        "taux": {},
        "perimetre": {},
    }
    if decision is not None and not decision.get("applied"):
        if destination_iso3.upper() == "TUN":
            # Algérie, Égypte, Maroc : franchise ZALE publiée, signalée sans
            # être calculée (fiche TUN_origines_servies_2026-10-03.json).
            from services.zlecaf_schedule_tun import note_zale

            note = note_zale(hs_code, origine_iso3)
            # Un taux que la zone arabe sert pour cette ligne n'est plus une
            # simple information (origine algérienne, colonne « ALGERIE »).
            if note and _zone_arabe(position, "TUN", origine_iso3) is None:
                resultat["note"] = f"{resultat['note']} {note}"
        return resultat

    # Pour la ZAF, la colonne socle ne doit JAMAIS être servie sans le
    # contrôle d'origine (effectué ci-dessus) : la branche ZAF sert le même
    # résolveur que l'historique.
    colonne = COLONNE_ZLECAF
    if destination_iso3.upper() == "SYC":
        # S.I. 113 of 2022 : une sous-colonne AfCFTA par année, 2022 à 2026.
        # Hors de cette plage, aucune colonne : rien n'est servi.
        import datetime as _dt

        from services.zlecaf_schedule_syc import colonne_de_l_annee

        colonne = colonne_de_l_annee(_dt.date.today().year)
    taux_dd = _colonne_de_la_position(position, colonne) if colonne else None
    origine_taux = "colonne préférentielle de la position (socle)"

    if taux_dd is None and destination_iso3.upper() in DESTINATIONS_A_CALENDRIER_NATIONAL:
        try:
            npf = _taux_npf(position, "DD")
            if npf is not None:
                # Signature : (hs_code, origin_iso3, normal_rate_pct). L'ordre
                # est significatif — origin_iso3 fait `.upper()` sur son
                # argument, un taux passé à sa place lève immédiatement.
                if destination_iso3.upper() == "DZA":
                    from services.zlecaf_schedule_dza import compute_dza_zlecaf_rate

                    compute_rate = compute_dza_zlecaf_rate
                else:
                    from services.zlecaf_schedule_egy import compute_egy_zlecaf_rate

                    compute_rate = compute_egy_zlecaf_rate
                taux, origine_taux = compute_rate(hs_code, origine_iso3, npf)
                taux_dd = {"taux": taux}
        except Exception as exc:  # pragma: no cover - dépendance optionnelle
            logger.warning("Calendrier ZLECAf %s indisponible : %s", destination_iso3.upper(), exc)

    elif taux_dd is None and _destination_regle_b_eac(destination_iso3):
        # Règle B (27/09/2026). Le tarif kényan ne porte pas de colonne ZLECAf : le barème est publié
        # à part, par la Legal Notice EAC/321/2022. Contrairement au calendrier
        # algérien, celui-ci ne prend PAS le taux NPF — il lit une colonne
        # annuelle, et une position hors barème rend None plutôt que de se
        # déduire du plein droit.
        try:
            from services.zlecaf_schedule_ken import (
                compute_ken_zlecaf_rate,
                reserve_regle_d_origine,
            )
            from services.zlecaf_implementation_registry import application_commencee
            import datetime as _dt

            taux, libelle = None, None
            if application_commencee(destination_iso3, _dt.date.today()):
                taux, libelle = compute_ken_zlecaf_rate(hs_code, origine_iso3)
            if taux is not None:
                # Plancher NPF (règle B, condition d) : une préférence ne doit
                # jamais dépasser le NPF du socle — dérogation nationale
                # éventuelle (ex. 2106.90.20, NPF 0 % pour une base de 10 %).
                npf = _taux_npf(position, "DD")
                if npf is not None and taux > npf:
                    taux = npf
                    libelle = f"{libelle} ; plancher NPF du socle appliqué"
                taux_dd = {"taux": taux}
                origine_taux = libelle
                # Servie, mais pas nécessairement accordée : voir la réserve.
                reserve = reserve_regle_d_origine(hs_code)
                if reserve:
                    resultat["reserve"] = reserve
        except Exception as exc:  # pragma: no cover - dépendance optionnelle
            logger.warning("Barème ZLECAf KEN indisponible : %s", exc)

    elif taux_dd is None and destination_iso3.upper() == "MAR":
        # Le tarif marocain ne porte pas de colonne ZLECAf au socle : le barème
        # vient de l'e-Tariff Book, sélectionné par les listes P1/P2 de la
        # fiche (CARTES_ORIGINES_NATIONALES). C'est le même resolver que le
        # chemin historique — les deux servent donc le même DI.
        try:
            from services.official_preferential_rates import resolve_official_preferential_rate

            officiel = resolve_official_preferential_rate(destination_iso3, hs_code, origine_iso3)
            if officiel and officiel.get("ad_valorem_rate_pct") is not None:
                taux_dd = {"taux": officiel["ad_valorem_rate_pct"]}
                origine_taux = (
                    "Circulaire ADII 6530/223, liste A — e-Tariff Book, "
                    f"barème {officiel.get('schedule')}, {officiel.get('source_column')}"
                )
        except Exception as exc:  # pragma: no cover - dépendance optionnelle
            logger.warning("Barème ZLECAf MAR indisponible : %s", exc)

    elif taux_dd is None and destination_iso3.upper() == "TUN":
        # Texte TA n°016/2023 : coefficient 2026 du Tarif Web × droit de base
        # 2019 (e-Tariff), plafonné au NPF — même résolveur que l'historique.
        from services.zlecaf_schedule_tun import compute_tun_zlecaf_rate

        taux, libelle = compute_tun_zlecaf_rate(hs_code, origine_iso3, _taux_npf(position, "DD"))
        if taux is not None:
            taux_dd = {"taux": taux}
            origine_taux = libelle

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
        dd_npf = _taux_npf(position, "DD")
        dd_servi = taux_dd.get("taux") if isinstance(taux_dd, dict) else None
        for code, definition in etendue(hs_code, origine_iso3).items():
            npf = _taux_npf(position, code)
            if npf is None:
                continue
            if isinstance(definition, dict):
                # Réduction proportionnelle (TPI marocaine) : elle suit le sort
                # du DI. Quand le taux préférentiel du DI atteint ou dépasse le
                # NPF, c'est le NPF qui est servi — la TPI reste alors PLEINE,
                # sinon le calcul mélangerait deux régimes (droit commun pour
                # le DI, préférentiel pour la TPI). Ex. 0901110000 : 4 % contre
                # 2,5 %.
                if dd_npf is not None and (dd_servi is None or dd_servi >= dd_npf):
                    continue
                table[code] = {"taux": round(npf * definition["facteur"], 6)}
                perimetre[code] = definition["reference"]
            else:
                # Exonération binaire (DAPS algérien) : elle ne dépend pas du
                # sort du DI — le plancher ne doit pas l'effacer.
                table[code] = {"taux": 0.0}
                perimetre[code] = definition

    if destination_iso3.upper() == "ZAF":
        # La préférence est servie : le statut reflète l'application, avec la
        # source (General Note O) et la date d'entrée du partenaire.
        from services.zlecaf_schedule_zaf import DATES_ENTREE_ZAF

        resultat["statut"] = "APPLIED"
        # L'origine est normalisée en majuscules une seule fois (origine_zaf,
        # en tête de la branche ZAF) ; si le corridor est actif, sa date
        # existe dans DATES_ENTREE_ZAF — aucune valeur générique n'est inventée.
        resultat["note"] = (
            "Préférence ZLECAf accordée par l'Afrique du Sud à "
            f"{origine_zaf} depuis le {DATES_ENTREE_ZAF[origine_zaf]} "
            "(General Note O du Schedule No. 1, Customs and Excise Act) — "
            "colonne AfCFTA du socle."
        )
    if destination_iso3.upper() == "NAM":
        from services.zlecaf_schedule_nam import DATES_ENTREE_NAM

        resultat["statut"] = "APPLIED"
        resultat["note"] = (
            "Préférence ZLECAf accordée par la Namibie à "
            f"{origine_iso3.upper()} depuis le {DATES_ENTREE_NAM[origine_iso3.upper()]} "
            "(General Note O du Schedule No. 1, Customs and Excise Act, 1998) — "
            "colonne AfCFTA du tarif commun SACU le plus à jour (socle)."
        )
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
    exonération — elles restent au NPF. Seule exception, la zone arabe
    (:func:`_zone_arabe`) : en Algérie, la liste négative est supprimée depuis
    2022 et la franchise couvre tout le tarif ; en Tunisie et en Libye, le
    tarif publie lui-même le taux, ligne par ligne.
    """
    from services.regional_blocs import CUSTOMS_UNION_NAMES, same_customs_union

    bloc = same_customs_union(origine_iso3, destination_iso3)
    if not bloc:
        return None
    libelle = CUSTOMS_UNION_NAMES.get(bloc, bloc)
    # SACU, art. 18.1 : franchise des « customs duties » telles que la
    # législation douanière nationale les définit (art. 1) ; les droits
    # antidumping et de sauvegarde (AD, SAUV) en sont (Schedule 2).
    codes = ("DD", "AD", "SAUV") if bloc == "SACU" else ("DD",)
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
        "taux": {code: {"taux": 0.0} for code in codes},
        "perimetre": {
            code: (
                f"Libre circulation intra-{bloc} (tarif extérieur commun et "
                "franchise intérieure de l'union douanière)"
            )
            for code in codes
        },
    }


def marchandise_dedouanee_sacu(destination_iso3: str) -> Dict[str, Any]:
    """Marchandise d'origine tierce déjà dédouanée dans un autre État de la SACU.

    Accord SACU 2002, art. 19 : un État membre n'impose aucun droit sur une
    marchandise importée de l'extérieur de la zone douanière commune quand
    elle lui arrive d'un autre État membre. Droit de douane, droits antidumping
    et de sauvegarde, et accises (pot commun, art. 32) ont été perçus au
    premier dédouanement ; restent dus la
    TVA du pays de destination et ses prélèvements nationaux, faute de texte
    les rattachant au pot commun. Fiche : SACU_art19_2026-10-14.json.
    """
    from services.regional_blocs import CUSTOMS_UNION_NAMES

    libelle = CUSTOMS_UNION_NAMES["SACU"]
    reference = "Accord SACU 2002, art. 19 (droits perçus au premier dédouanement dans la SACU)"
    return {
        "applique": True,
        "regime": "UNION_DOUANIERE",
        "code_bloc": "SACU",
        "libelle_bloc": libelle,
        "statut": "DEJA_DEDOUANEE_SACU",
        "note": (
            f"Marchandise déjà dédouanée dans un autre État de la {libelle} : "
            f"{destination_iso3.upper()} ne perçoit ni droit de douane ni accise "
            "(accord SACU 2002, art. 19). La TVA du pays de destination et ses "
            "prélèvements nationaux restent dus. Réserve (art. 31.4) : si la "
            "marchandise est entrée dans la SACU à un taux préférentiel, la "
            "différence avec le droit normal est due — elle n'est pas calculée ici."
        ),
        # Droits antidumping et de sauvegarde (AD, SAUV) : droits de douane de
        # la zone douanière commune (Schedule 2), des « duties » de l'art. 19.
        "taux": {code: {"taux": 0.0} for code in ("DD", "EXS", "EXA", "AD", "SAUV")},
        "perimetre": {code: reference for code in ("DD", "EXS", "EXA", "AD", "SAUV")},
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
        if valeur.get("specifique"):
            # « 7%+SCR5/kg » ou « 40% or 240c/kg » : le pourcentage n'est
            # qu'une composante. Le montrer seul — et le chiffrer en
            # remplaçant le droit entier — sous-estimerait le droit.
            return None
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
    # Une colonne que la zone arabe sert déjà (« ALGERIE » au tarif tunisien)
    # n'est pas montrée une seconde fois en simulation.
    servie = _zone_arabe(position, destination, origine) is not None
    if bilaterale is not None and origine not in SIMULABLES and not servie:
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
