"""Une préférence ne peut jamais coûter plus cher que le droit commun.

Une préférence tarifaire est une FACULTÉ, pas une obligation : aucun importateur
n'invoque un régime plus cher que le NPF, et aucune douane ne le lui impose. Le
règlement éthiopien 574/2025 l'écrit à son article 3(5), mais le principe ne lui
est pas propre.

Les trois chemins préférentiels du moteur calculaient pourtant correctement
``preference_applied = taux < NPF`` puis servaient le taux préférentiel QUAND
MÊME : le drapeau disait « pas d'avantage » pendant que le montant facturait
davantage. Mesuré avant correction — 8 positions algériennes, 2 sud-africaines,
3 kényanes, sur trois chemins indépendants.
"""

from __future__ import annotations

import pytest
from services.authentic_tariff_service import resolve_zlecaf_context

#: Les trois cas mesurés, un par chemin préférentiel du moteur. Chacun est une
#: position réelle, avec le NPF que son tarif national publie.
CAS_MESURES = [
    # (destination, origine, position, NPF publié, taux préférentiel écarté)
    ("DZA", "EGY", "0201101100", 5.0, 24.0),  # viande de veau, base 2019 à 30 %
    ("DZA", "KEN", "0201101100", 5.0, 26.25),  # la même, calendrier réciprocité
    ("ZAF", "GHA", "630800", 0.0, 8.0),  # barème SARS
    ("KEN", "BFA", "21069020", 0.0, 4.0),  # chemin générique APPLIED
]


@pytest.mark.parametrize(
    "destination,origine,position,npf,ecarte",
    CAS_MESURES,
    ids=[f"{d}<-{o}:{p}" for d, o, p, _, _ in CAS_MESURES],
)
def test_le_npf_est_servi_quand_la_preference_coute_plus_cher(
    destination, origine, position, npf, ecarte
):
    """Le montant servi, et pas seulement le drapeau, doit retomber sur le NPF."""
    contexte = resolve_zlecaf_context(destination, origine, position, npf, None)

    assert (
        contexte["dd_rate_pct"] == npf
    ), f"{destination}<-{origine} {position} : le taux servi doit être le NPF"
    assert contexte["preference_applied"] is False

    plancher = contexte["plancher_npf"]
    assert plancher is not None, "le plancher doit être déclaré, pas silencieux"
    assert plancher["taux_preferentiel_ecarte_pct"] == ecarte
    assert plancher["taux_retenu_pct"] == npf
    assert plancher["motif"]


@pytest.mark.parametrize(
    "destination,origine,position,npf",
    [(d, o, p, n) for d, o, p, n, _ in CAS_MESURES],
    ids=[f"{d}<-{o}:{p}" for d, o, p, _, _ in CAS_MESURES],
)
def test_l_ecart_est_dit_dans_la_note_servie(destination, origine, position, npf):
    """Un montant corrigé sans explication ne serait pas opposable.

    L'opérateur doit pouvoir lire pourquoi le taux affiché n'est pas celui du
    barème préférentiel qu'il croyait invoquer.
    """
    contexte = resolve_zlecaf_context(destination, origine, position, npf, None)
    note = (contexte.get("trade_regime_note") or "") + (contexte.get("zlecaf_note") or "")

    assert "supérieur au NPF" in note
    assert "NPF servi" in note


def test_une_preference_reellement_avantageuse_n_est_pas_touchee():
    """Le garde-fou ne doit mordre QUE sur l'anomalie.

    Sans ce contrôle, un plancher trop large effacerait des préférences
    légitimes — l'erreur inverse, et plus coûteuse pour l'opérateur.
    """
    contexte = resolve_zlecaf_context("DZA", "EGY", "2901101000", 15.0, None)

    assert contexte["plancher_npf"] is None
    assert contexte["dd_rate_pct"] is not None
    assert contexte["dd_rate_pct"] < 15.0


def test_le_plancher_vaut_pour_tout_chemin_present_et_a_venir():
    """Il est posé dans le constructeur commun, pas dans chaque branche.

    Les trois cas mesurés relèvent de trois chemins distincts du moteur —
    calendrier algérien, barème SARS, résolution générique. Qu'ils soient tous
    couverts atteste que la garde est au bon endroit : un quatrième chemin
    ajouté demain en hérite sans qu'on ait à y penser.
    """
    chemins = {d for d, _, _, _, _ in CAS_MESURES}
    assert chemins == {
        "DZA",
        "ZAF",
        "KEN",
    }, "ce test perd son sens si les cas ne couvrent plus les trois chemins"

    for destination, origine, position, npf, _ in CAS_MESURES:
        contexte = resolve_zlecaf_context(destination, origine, position, npf, None)
        assert contexte["plancher_npf"] is not None, destination
