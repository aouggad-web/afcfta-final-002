"""
Variante GET de /authentic-tariffs/calculate — valeur FOB de la SACU.

Le frontend appelle cette variante GET. Elle n'acceptait pas `fob_value` et ne
le transmettait pas : le paramètre gardait alors son défaut FastAPI (un objet
`Query`, pas `None`), et toute position sud-africaine à droit non nul
répondait 500 (TypeError) au lieu de réclamer la valeur FOB.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.authentic_tariffs import router
from services.authentic_tariff_service import get_tariff_line

CODE = "020110"


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _precondition():
    line = get_tariff_line("ZAF", CODE)
    assert line is not None and (line.get("dd_rate") or 0) > 0, (
        "précondition invalidée : besoin d'une ligne ZAF avec un droit de douane non nul"
    )


def test_sans_fob_le_chemin_historique_reclame_la_valeur_fob(client):
    r = client.get(f"/authentic-tariffs/calculate/ZAF/{CODE}", params={"value": 1000})

    assert r.status_code == 422, r.text
    detail = r.json()["detail"]
    assert detail["code"] == "VALEUR_FOB_REQUISE"
    assert detail["missing_or_non_ad_valorem_taxes"] == ["DD"]


def test_avec_fob_le_droit_est_liquide_sur_la_valeur_fob(client):
    r = client.get(
        f"/authentic-tariffs/calculate/ZAF/{CODE}", params={"value": 1000, "fob_value": 800}
    )

    assert r.status_code == 200, r.text
    etape_dd = next(s for s in r.json()["calculation_steps"] if s["code"] == "DD")
    assert etape_dd["base_formula"] == "FOB"
    assert etape_dd["base_value"] == 800


def test_fob_superieure_a_la_cif_reste_une_erreur_de_saisie(client):
    r = client.get(
        f"/authentic-tariffs/calculate/ZAF/{CODE}", params={"value": 1000, "fob_value": 1200}
    )

    assert r.status_code == 422, r.text
    assert "valeur_fob" in str(r.json()["detail"])


def _bases_fob_reglementaires(reponse):
    return [
        li["base_value"]
        for li in reponse.json()["regulatory_cost"]["line_items"]
        if li.get("calculation_method") == "PERCENTAGE_OF_FOB"
    ]


def test_les_frais_assis_sur_la_fob_utilisent_la_valeur_fob_fournie(client):
    """CMR : frais de prestataire en % de la FOB (verified_provider_fees.json)."""
    sans = client.get("/authentic-tariffs/calculate/CMR/01011010", params={"value": 1000})
    avec = client.get(
        "/authentic-tariffs/calculate/CMR/01011010", params={"value": 1000, "fob_value": 800}
    )

    assert sans.status_code == avec.status_code == 200
    # Sans FOB fournie, l'assiette reste le CIF, comme avant.
    assert _bases_fob_reglementaires(sans) == [1000]
    assert _bases_fob_reglementaires(avec) == [800]


def test_la_route_de_compatibilite_accepte_la_valeur_fob():
    from routes.postgres_tariffs import router as router_postgres

    app = FastAPI()
    app.include_router(router_postgres)
    compat = TestClient(app, raise_server_exceptions=False)
    params = {"country_iso3": "ZAF", "hs6": CODE, "value": 1000}

    sans = compat.post("/postgres-tariffs/calculate", params=params)
    avec = compat.post("/postgres-tariffs/calculate", params={**params, "fob_value": 800})

    assert sans.status_code == 422
    assert sans.json()["detail"]["code"] == "VALEUR_FOB_REQUISE"
    assert avec.status_code == 200, avec.text


def test_poids_et_transport_chiffrent_le_bloc_reglementaire_comme_sur_calcul(client):
    """Même chiffrage que POST /calcul : 2,5 t et un camion au Togo → péage
    600 F (3 tonnes entamées), scanner 20 000 F."""
    r = client.get(
        "/authentic-tariffs/calculate/TGO/0201100000",
        params={"value": 1000, "poids_brut_kg": 2500, "moyen_transport": "CAMION"},
    )

    assert r.status_code == 200, r.text
    montants = {l["measure_name"]: l.get("calculated_amount") for l in r.json()["regulatory_cost"]["line_items"]}
    assert montants["Taxe de péage (TP)"] == 600.0
    assert montants["Droit de passage au scanner (DPS)"] == 20000.0


def test_le_mode_d_acheminement_ecarte_les_frais_portuaires_comme_sur_calcul(client):
    """Guinée : port de Conakry gardé sans mode, écarté pour ROUTE."""

    def frais(**extra):
        r = client.get("/authentic-tariffs/calculate/GIN/0201100000", params={"value": 1000, **extra})
        assert r.status_code == 200, r.text
        return {l["measure_name"] for l in r.json()["regulatory_cost"]["line_items"]}

    port = "Port autonome de Conakry (escales, acconage, magasinage)"
    assert port in frais()
    assert port not in frais(mode_acheminement="ROUTE")
