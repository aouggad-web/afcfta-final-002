"""La quantité d'un droit spécifique : réclamée, nommée, jamais supposée.

Un droit publié « 8c/kg » ne se liquide pas sur la valeur en douane. Le moteur
le dit — `QUANTITE_REQUISE` — et nomme l'unité que la source publie, pour que
l'écran puisse la demander dans CETTE unité plutôt que de supposer un poids.

Deux invariants tiennent l'ensemble :
  1. l'unité vient de la source ou n'est pas affirmée ; la Tunisie publie
     « 0.1 dinars » sans unité de quantité, et ce silence doit rester visible ;
  2. aucune position ne mêle deux unités sur un même code — c'est ce qui rend
     légitime une quantité UNIQUE pour toute la position. Si une source
     changeait, ce test le dirait avant que l'écran ne liquide un droit dans
     la mauvaise unité.
"""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

SOCLE_PRESENT = os.path.exists(socle.MANIFESTE)
besoin_socle = pytest.mark.skipif(
    not SOCLE_PRESENT, reason="socle absent : python3 scripts/build_socle.py"
)


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture
def client():
    import importlib.util

    chemin = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes", "calcul.py"
    )
    spec = importlib.util.spec_from_file_location("routes_calcul_qte_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_qte_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def _ligne(reponse, code):
    return next(l for l in reponse["npf"]["lignes"] if l["code"] == code)


@besoin_socle
def test_sans_quantite_le_moteur_la_reclame_et_nomme_son_unite(client):
    """Premier temps du dialogue : ce qui manque, et dans quelle unité."""
    r = client.post(
        "/calcul", json={"destination": "ZAF", "code_sh": "020830", "valeur_cif": 10000}
    )
    assert r.status_code == 200
    dd = _ligne(r.json(), "DD")

    assert dd["statut"] == "QUANTITE_REQUISE"
    assert dd["montant"] is None
    assert dd["unite_quantite"] == "kg"
    assert dd["specifique"] == "8c/kg"
    assert r.json()["npf"]["etat"] == "INDISPONIBLE"


@besoin_socle
def test_avec_la_quantite_le_droit_se_liquide_et_entre_dans_l_assiette_TVA(client):
    """Second temps : le total devient COMPLET, TVA comprise.

    8c/kg × 200 kg = 16,00. La TVA sud-africaine est assise sur CIF + DD :
    15 % de 10 016,00 = 1 502,40. Le droit spécifique n'est donc pas seulement
    ajouté au total, il déplace l'assiette de la taxe suivante.
    """
    r = client.post(
        "/calcul",
        json={"destination": "ZAF", "code_sh": "020830", "valeur_cif": 10000, "quantite": 200},
    )
    assert r.status_code == 200
    npf = r.json()["npf"]

    dd = _ligne(r.json(), "DD")
    assert dd["statut"] == "CALCULE"
    assert dd["montant"] == pytest.approx(16.0)

    tva = _ligne(r.json(), "TVA")
    assert tva["base"] == pytest.approx(10016.0)
    assert tva["montant"] == pytest.approx(1502.4)

    assert npf["etat"] == "COMPLET"
    assert npf["manques"] == []
    assert npf["total_a_payer"] == pytest.approx(11518.4)


@besoin_socle
def test_une_quantite_nulle_est_refusee_et_non_liquidee_a_zero(client):
    """Une quantité à 0 n'est pas une quantité connue : la route la refuse.

    Acceptée (`ge=0`), elle liquidait le droit spécifique à 0,00 et rendait un
    total COMPLET de 11 500,00 — le droit effacé sans que rien ne le dise.
    L'écart n'est pas un arrondi, c'est le droit entier. Une quantité inconnue
    s'omet : le moteur la réclame alors au lieu de la supposer nulle.
    """
    r = client.post(
        "/calcul",
        json={"destination": "ZAF", "code_sh": "020830", "valeur_cif": 10000, "quantite": 0},
    )
    assert r.status_code == 422


@besoin_socle
def test_une_source_sans_unite_ne_se_voit_pas_attribuer_un_kilo(client):
    """Tunisie, droit sanitaire vétérinaire : « 0.1 dinars », sans unité.

    Le moteur réclame la quantité mais N'AFFIRME PAS d'unité. C'est ce silence
    qui doit remonter à l'écran : y demander un poids produirait un montant
    faux, puisque rien n'établit que le droit se liquide au kilo.
    """
    r = client.post(
        "/calcul",
        json={"destination": "TUN", "code_sh": "01012100015", "valeur_cif": 10000},
    )
    assert r.status_code == 200
    dsv = _ligne(r.json(), "DSV")

    assert dsv["statut"] == "QUANTITE_REQUISE"
    assert dsv["specifique"] == "0.1 dinars"
    assert "unite_quantite" not in dsv


@besoin_socle
def test_aucune_position_ne_mele_deux_unites_de_quantite():
    """L'invariant qui rend légitime une quantité UNIQUE par position.

    Si une collecte future publiait, sur une même position, un droit au kilo et
    un autre au litre, une seule saisie en liquiderait un dans la mauvaise
    unité. Ce test le refuse à la construction plutôt qu'à la liquidation.
    """
    divergentes = []
    for iso3 in socle.pays_servis():
        donnees = socle.charger(iso3)
        for code, position in (donnees.get("positions") or {}).items():
            unites = set()
            for droit in position.get("droits") or []:
                if droit.get("assiette") != "xQTE":
                    continue
                specifique = droit.get("specifique")
                unite = specifique.get("unite_quantite") if isinstance(specifique, dict) else None
                if unite:
                    unites.add(unite)
            if len(unites) > 1:
                divergentes.append((iso3, code, sorted(unites)))

    assert divergentes == [], f"positions à unités divergentes : {divergentes[:5]}"
