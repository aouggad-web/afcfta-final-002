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

from services import socle
from services.calcul import calculer
from services.preference import taux_preferentiels

#: Positions réelles où le barème préférentiel dépasse le NPF publié, avec le
#: NPF et le taux préférentiel écarté.
CAS_MESURES = [
    # (destination, origine, position, NPF publié, taux préférentiel écarté)
    # Maurice plutôt que l'Égypte : pour une origine arabe, la franchise GZALE
    # (0 %) l'emporte sur cette position sans DAPS (fiche DZA_GZALE).
    ("DZA", "MUS", "0201101100", 5.0, 24.0),  # bovins, base 2019 à 30 %
    ("DZA", "KEN", "0201101100", 5.0, 26.25),  # la même, calendrier réciprocité
    ("DZA", "EGY", "0207121000", 5.0, 24.0),  # volailles — et un DAPS de 70 %
]


def _calcul(destination, origine, code):
    """Le calcul de POST /calcul : préférence résolue, puis liquidation."""
    try:
        position = socle.charger(destination)["positions"][code]
    except socle.SocleIndisponible:
        pytest.skip(f"socle {destination} absent : python3 scripts/build_socle.py")
    preference = taux_preferentiels(position, destination, origine, code)
    table = preference["taux"] if preference.get("applique") else None
    return preference, calculer(position, 1000.0, taux_preferentiels=table)


def _ligne(resultat, regime, code):
    return next(ligne for ligne in resultat[regime]["lignes"] if ligne["code"] == code)


@pytest.mark.parametrize(
    "destination,origine,position,npf,ecarte",
    CAS_MESURES,
    ids=[f"{d}<-{o}:{p}" for d, o, p, _, _ in CAS_MESURES],
)
def test_le_npf_est_servi_quand_la_preference_coute_plus_cher(
    destination, origine, position, npf, ecarte
):
    """Le montant servi, et pas seulement le drapeau, doit retomber sur le NPF."""
    preference, resultat = _calcul(destination, origine, position)
    assert preference["taux"]["DD"]["taux"] == ecarte

    dd = _ligne(resultat, "preference", "DD")
    assert dd["taux_pct"] == npf, f"{destination}<-{origine} {position} : le taux servi doit être le NPF"
    assert dd["regime_applique"] == "npf_plancher", "le plancher doit être déclaré, pas silencieux"


def test_le_plancher_ne_rabote_que_le_droit_de_douane():
    """Une préférence ne se résume pas au droit de douane.

    Les positions algériennes que le plancher touche sont exonérées de DAPS
    par la circulaire 482/2024 — un droit de 70 % que la préférence retire
    réellement. Annoncer « aucune préférence » ferait renoncer l'opérateur à
    son certificat d'origine, et payer le plein tarif.
    """
    _, resultat = _calcul("DZA", "EGY", "0207121000")

    assert _ligne(resultat, "preference", "DD")["regime_applique"] == "npf_plancher"
    daps = _ligne(resultat, "preference", "DAPS")
    assert daps["taux_pct"] == 0.0 and daps["regime_applique"] == "preference"
    assert resultat["preference"]["total_a_payer"] < resultat["npf"]["total_a_payer"]


def test_une_preference_reellement_avantageuse_n_est_pas_touchee():
    """Le garde-fou ne doit mordre QUE sur l'anomalie."""
    _, resultat = _calcul("DZA", "EGY", "2901101000")

    dd = _ligne(resultat, "preference", "DD")
    assert dd["regime_applique"] == "preference"
    assert dd["taux_pct"] < _ligne(resultat, "npf", "DD")["taux_pct"]
