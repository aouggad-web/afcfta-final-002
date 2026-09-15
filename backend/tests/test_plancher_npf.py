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
    ("DZA", "EGY", "0201101100", 5.0, 24.0),  # bovins, base 2019 à 30 %
    ("DZA", "KEN", "0201101100", 5.0, 26.25),  # la même, calendrier réciprocité
    ("DZA", "EGY", "0207121000", 5.0, 24.0),  # volailles — et un DAPS de 70 %
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


def test_le_plancher_ne_rabote_que_le_droit_de_douane():
    """Une préférence ne se résume pas au droit de douane.

    Première version de ce garde-fou : le plancher éteignait aussi
    ``preference_applied``. Or les huit positions algériennes qu'il touche sont
    TOUTES exonérées de DAPS par la circulaire 482/2024 — un droit de 70 % que
    la cascade retire réellement. Le moteur annonçait donc « aucune préférence »
    en calculant 70 000 DA d'économie sur 100 000 de CIF.

    Pour l'opérateur, c'est la pire des deux erreurs : croyant n'avoir rien à
    gagner, il ne présente pas son certificat d'origine et paie le plein tarif.
    """
    contexte = resolve_zlecaf_context("DZA", "EGY", "0207121000", 5.0, None)

    assert contexte["plancher_npf"] is not None, "le plancher doit bien mordre ici"
    assert contexte["dd_rate_pct"] == 5.0, "le droit de douane retombe au NPF"
    assert contexte["daps_exempt"] is True, "l'exonération de DAPS doit survivre"
    assert contexte["preference_applied"] is True, (
        "une exonération de DAPS EST une préférence : le plancher ne doit pas "
        "l'effacer en rabotant le droit de douane"
    )


def test_sans_autre_avantage_le_plancher_laisse_le_drapeau_a_faux():
    """La contrepartie : le drapeau ne doit pas devenir vrai pour rien.

    Sur les chemins qui n'ont pas de composante hors droit de douane, écarter
    le taux préférentiel ne laisse aucun avantage — et le drapeau, calculé par
    l'appelant comme ``taux < NPF``, est déjà faux. On vérifie qu'il le reste.
    """
    for destination, origine, position, npf in (
        ("ZAF", "GHA", "630800", 0.0),
        ("KEN", "BFA", "21069020", 0.0),
    ):
        contexte = resolve_zlecaf_context(destination, origine, position, npf, None)
        assert contexte["plancher_npf"] is not None, destination
        assert contexte["preference_applied"] is False, destination


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
