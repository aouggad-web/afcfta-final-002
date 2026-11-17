"""Garde-fous DoS du chargement du socle (audit 17/11/2026).

Un défaut de cache rechargeait, re-hachait (socle + source + nomenclature, des
dizaines de Mo) et re-parsait le fichier à chaque requête ; un visiteur anonyme
qui fait tourner le pays sur plus de `_MAX_PAYS_EN_CACHE` défaisait le cache à
chaque appel. L'empreinte n'est désormais vérifiée qu'une fois par processus.
"""

import os

import pytest

from services import socle

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE),
    reason="socle absent : python3 scripts/build_socle.py",
)


def _pays_chargeables(n):
    """Jusqu'à `n` pays que ce socle local sait charger (source présente)."""
    ok = []
    for iso in socle.manifeste().get("pays", {}):
        try:
            socle.charger(iso)
        except socle.SocleIndisponible:
            continue
        ok.append(iso)
        if len(ok) >= n:
            break
    return ok


def test_empreinte_verifiee_une_seule_fois_par_pays(monkeypatch):
    besoin = socle._MAX_PAYS_EN_CACHE + 2
    pays = _pays_chargeables(besoin)
    if len(pays) < besoin:
        pytest.skip("pas assez de pays chargeables en local")

    # Repartir d'un cache et d'un registre de vérification vides.
    socle._cache.clear()
    socle._verifies.clear()

    appels = {"n": 0}
    vrai_sha = socle._sha256

    def _compte(chemin):
        appels["n"] += 1
        return vrai_sha(chemin)

    monkeypatch.setattr(socle, "_sha256", _compte)

    premier = pays[0]
    socle.charger(premier)  # 1er chargement : empreintes vérifiées
    assert appels["n"] >= 1
    assert premier in socle._verifies

    # Charger d'autres pays évince `premier` du cache (taille `_MAX_PAYS_EN_CACHE`).
    for iso in pays[1:]:
        socle.charger(iso)
    assert premier not in socle._cache

    appels["n"] = 0
    donnees = socle.charger(premier)  # rechargé à froid, mais déjà vérifié
    assert appels["n"] == 0  # aucun re-hachage : c'est le correctif
    assert donnees  # les données sont bien servies


def test_le_semaphore_de_chargement_existe_et_est_borne():
    assert socle._MAX_CHARGEMENTS >= 1
    assert socle._CHARGEMENT is not None
