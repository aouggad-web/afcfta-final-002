"""Mesures de la gazette EAC portées sur le droit de douane du socle.

Le Tarif extérieur commun publie un taux ; la gazette de la Communauté le
modifie pour un État partenaire et une année budgétaire : sursis d'application
(« stay of application ») et remises de droits (« duty remission »). Les
mesures relevées, et elles seules, sont dans ``data/eac/legal_overrides.json``,
dont la couverture est déclarée partielle.

Ce module ne décide de rien. Le résolveur ``engine.legal_override_engine``
dit si une mesure s'applique (date, ligne tarifaire exacte, conditions, et pour
une remise conditionnelle une autorisation datée qui nomme la ligne) ; ce
module porte sa réponse sur la ligne DD :

- mesure appliquée : le taux de la mesure remplace celui du TEC, et la note
  cite la Legal Notice ;
- mesures contradictoires, ou mesure applicable sans taux calculable : le taux
  n'est pas servi (« à compléter ») ;
- remise subordonnée à une autorisation non établie : le taux du TEC reste dû,
  et la note dit à quelles conditions la remise s'appliquerait.
"""

from __future__ import annotations

import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from engine.legal_override_engine import LegalOverrideResolver, load_legal_measures
from engine.schemas.legal_override import OverrideContext, RemissionEligibility

MESURES = Path(__file__).resolve().parents[2] / "data" / "eac" / "legal_overrides.json"

#: Issues du résolveur qui laissent le taux du TEC dû, avec la raison en clair.
NON_APPLIQUEES = {
    "ELIGIBILITY_UNKNOWN": "éligibilité de l'importateur non déclarée",
    "AUTHORIZATION_REQUIRED": "autorisation officielle couvrant la ligne exacte non établie",
    "NOT_ELIGIBLE": "importateur non bénéficiaire ou autorisation hors validité",
    "CONDITION_UNRESOLVED": "condition de la mesure (bénéficiaire, usage) non établie",
    "MAPPING_REVIEW_REQUIRED": "rattachement de la mesure à la ligne à vérifier",
}


#: Taux mixte d'un sursis, tel que la Legal Notice EAC/160/2026 l'écrit :
#: « 35 % or USD 2/SQM, whichever is higher ».
TAUX_MIXTE = re.compile(r"^% or USD ([\d.]+)/(metre|SQM), whichever is higher$")
UNITES = {"metre": "m", "SQM": "m2"}
#: Champs qui décrivent le taux de la ligne : une mesure qui fixe le taux les
#: remplace tous, sans quoi la part spécifique du TEC survivrait au sursis.
CHAMPS_DU_TAUX = ("taux", "specifique", "compose", "regle_composee", "expression_brute")


def _taux_de_la_mesure(mesure, taux):
    """Les champs de la ligne DD pour le taux qu'une mesure fixe, ou ``None``
    si son unité n'est pas lisible."""
    unite = (mesure.rate_unit or "%").strip()
    if unite == "%":
        return {"taux": taux}
    mixte = TAUX_MIXTE.match(unite)
    if not mixte:
        return None
    brut = f"{taux:g}{unite}"
    return {
        "taux": taux,
        "specifique": {
            "montant": float(mixte.group(1)),
            "unite_monetaire": "USD",
            "unite_quantite": UNITES[mixte.group(2)],
            "brut": brut,
        },
        "compose": True,
        "regle_composee": "LE_PLUS_ELEVE",
        "expression_brute": brut,
    }


@lru_cache(maxsize=1)
def _mesures():
    return load_legal_measures(MESURES)


def aujourdhui() -> date:
    return date.today()


def appliquer(
    position: dict,
    destination: str,
    code: str,
    *,
    eligibilite: RemissionEligibility = RemissionEligibility.ELIGIBILITY_UNKNOWN,
    reference: Optional[str] = None,
    debut: Optional[date] = None,
    fin: Optional[date] = None,
    lignes: Optional[List[str]] = None,
    le: Optional[date] = None,
):
    """Rendre (position, bloc) : la position dont la ligne DD porte les mesures
    EAC en vigueur, et le relevé de ces mesures (``None`` s'il n'y en a pas)."""
    destination = destination.upper()
    le = le or aujourdhui()
    # Une mesure de la gazette nomme l'État partenaire qui la reçoit : celle du
    # Kenya ne vaut pas pour la Tanzanie, même au sein du même TEC.
    mesures = [m for m in _mesures() if m.jurisdiction.strip().upper() == destination]
    if not any(m.is_effective(le) and m.covers_hs(code) for m in mesures):
        return position, None
    droits = position.get("droits") or []
    dd = next((d for d in droits if d.get("code") == "DD"), None)
    if dd is None or dd.get("taux") is None:
        return position, None

    resolution = LegalOverrideResolver(mesures).resolve(
        hs_code=code,
        on_date=le,
        base_rate=dd["taux"],
        context=OverrideContext(
            jurisdiction=destination,
            regional_blocs=["EAC"],
            remission_eligibility=eligibilite,
            authorization_reference=reference,
            authorization_effective_from=debut,
            authorization_effective_to=fin,
            authorization_hs_codes=list(lignes or []),
        ),
    )
    etapes = [e for e in resolution["trace"] if e.get("measure_id")]
    par_id = {m.measure_id: m for m in mesures}
    # Sans mesure appliquée, la ligne garde son taux tel que le TEC l'écrit.
    notes, champs = [], {k: dd[k] for k in CHAMPS_DU_TAUX if k in dd}
    if resolution["calculation_status"] == "CONFLICT_REVIEW" or any(
        e["outcome"] == "RATE_UNRESOLVED" for e in etapes
    ):
        champs = {"taux": None}
        notes.append(
            "Mesure de la gazette EAC applicable à cette ligne sans taux unique calculable ("
            + ", ".join(sorted({e["measure_id"] for e in etapes}))
            + "). À compléter."
        )
    else:
        for e in etapes:
            mesure = par_id[e["measure_id"]]
            periode = (
                f"du {mesure.effective_from:%d/%m/%Y} au {mesure.effective_to:%d/%m/%Y}"
                if mesure.effective_to
                else f"depuis le {mesure.effective_from:%d/%m/%Y}"
            )
            if e["outcome"] == "APPLIED":
                champs = _taux_de_la_mesure(mesure, e["rate_after"])
                if champs is None:
                    champs = {"taux": None}
                    notes.append(
                        f"{mesure.legal_reference} : taux « {e['rate_after']:g} "
                        f"{mesure.rate_unit} » {periode}, forme non liquidable. À compléter."
                    )
                else:
                    notes.append(
                        f"{mesure.legal_reference} : {e['rate_after']:g} "
                        f"{mesure.rate_unit or '%'} au lieu de {e['rate_before']:g} % (TEC), "
                        f"{periode}."
                    )
            elif e["outcome"] in NON_APPLIQUEES and mesure.override_rate is not None:
                notes.append(
                    f"{mesure.legal_reference} : {mesure.override_rate:g} "
                    f"{mesure.rate_unit or '%'} {periode} "
                    f"pour les importations qui remplissent ses conditions "
                    f"({NON_APPLIQUEES[e['outcome']]}). Taux du TEC appliqué."
                )

    nouveau_dd = {k: v for k, v in dd.items() if k not in CHAMPS_DU_TAUX}
    nouveau_dd.update(champs)
    if notes:
        nouveau_dd["note"] = " ".join(([dd["note"]] if dd.get("note") else []) + notes)
    bloc = {
        "taux_tec": dd["taux"],
        "taux_applique": champs["taux"],
        "eligibilite_remise": resolution["remission_eligibility_status"],
        "autorisation_requise": resolution["requires_eligibility_input"],
        "date": le.isoformat(),
        "mesures": etapes,
    }
    nouveaux = [nouveau_dd if d is dd else d for d in droits]
    return {**position, "droits": nouveaux}, bloc
