"""Industrie nationale (ONS) et marchés d'export (BACI) — contrat de données et routes.

Les fichiers sont réels (data/json/dza_industrie.json, dza_commerce_baci.json) :
ces tests vérifient qu'aucune valeur n'est servie sans sa nature, que les totaux
retombent sur les chiffres officiels et que les filtres font ce qu'ils disent.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routes.industrie_nationale import router
from services import industrie_nationale_service as ins


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------- industrie ---


def test_industrie_dza_natures_par_annee():
    d = ins.industrie("DZA")
    assert d["available"] is True
    assert len(d["branches"]) == 13
    for b in d["branches"]:
        a = b["annees"]
        assert a["2020"]["nature"] == "calcul_officiel"
        for an in ("2021", "2022", "2023", "2024"):
            assert a[an]["nature"] == "officiel" and a[an]["is_estimation"] is False
        e = a["2025"]
        assert e["nature"] == "estimation" and e["is_estimation"] is True
        # une estimation porte sa fourchette, sa confiance, sa méthode et ses sources
        assert e["croissance_volume_pct"]["bas"] <= e["croissance_volume_pct"]["central"]
        assert e["croissance_volume_pct"]["central"] <= e["croissance_volume_pct"]["haut"]
        assert e["confiance"] in {"B", "C"}
        assert e["indicateurs"] and e["sources"]
        assert all(s in d["sources"] for s in e["sources"])


def test_industrie_dza_totaux_officiels():
    d = ins.industrie("DZA")
    somme_2024 = sum(b["annees"]["2024"]["va_mda"] for b in d["branches"])
    # VA manufacturière 2024 publiée : 3 413,452 Md DA (ONS, reprise par la Banque mondiale)
    assert abs(somme_2024 - 3413.452) < 0.2
    somme_2020 = sum(b["annees"]["2020"]["va_mda"] for b in d["branches"])
    assert abs(somme_2020 - d["total"]["2020"]["va_mda"]) < 0.5
    # 2016-2019 : total seulement, jamais de détail par branche
    for an in ("2016", "2017", "2018", "2019"):
        assert d["total"][an]["nature"] == "officiel"
        assert all(an not in b["annees"] for b in d["branches"])


def test_pays_non_couvert_renvoie_indisponible():
    for fonction in (ins.industrie, ins.exportations):
        r = fonction("MAR")
        assert r["available"] is False and r["covered_countries"] == ["DZA"]
    assert ins.fiche_produit("MAR", "310210")["available"] is False


# ------------------------------------------------------------- exportations ---


def test_exportations_tri_et_parts():
    d = ins.exportations("DZA", limite=400)
    valeurs = [p["exportations_2024_usd"] for p in d["produits"]]
    assert valeurs == sorted(valeurs, reverse=True)
    for p in d["produits"]:
        if p["part_afrique_2024_pct"] is not None:
            assert 0 <= p["part_afrique_2024_pct"] <= 100.05
    afrique = ins.exportations("DZA", region="afrique", limite=400)["produits"]
    assert all(p["exportations_afrique_2024_usd"] > 0 for p in afrique)


def test_hors_hydrocarbures_ecarte_le_chapitre_27():
    tous = ins.exportations("DZA", limite=400)["produits"]
    assert any(p["hs6"].startswith("27") for p in tous)
    hh = ins.exportations("DZA", limite=400, hors_hydrocarbures=True)
    assert hh["hors_hydrocarbures"] is True
    assert hh["produits"] and not any(p["hs6"].startswith("27") for p in hh["produits"])


def test_caroube_libelle_tarifaire_et_non_oec():
    # L'OEC étiquette 121292 « Sugar cane » : le service doit servir le libellé tarifaire.
    fiche = ins.fiche_produit("DZA", "121292", "fr")
    assert fiche["available"] is True
    assert fiche["libelle"].startswith("Caroubes")
    assert "Locust beans" in ins.fiche_produit("DZA", "121292", "en")["libelle"]


def test_marches_absents_respectent_les_seuils():
    fiche = ins.fiche_produit("DZA", "310210", seuil_import_usd=5e6, seuil_part_pct=2.0)
    critere = fiche["marches_absents"]["critere"]
    assert critere["importations_2024_min_usd"] == 5e6 and critere["part_pays_max_pct"] == 2.0
    for zone in ("monde", "afrique"):
        for m in fiche["marches_absents"][zone]:
            assert m["importations_2024_usd"] >= 5e6
            assert (m["part_pays_pct"] or 0) < 2.0
    assert all(m["iso3"] != "DZA" for m in fiche["importateurs_monde_2024"])


def test_produit_hors_champ():
    r = ins.fiche_produit("DZA", "999999")
    assert r["available"] is False and "0,5 M USD" in r["message"]


# ------------------------------------------------------------------ routes ---


def test_routes(client):
    assert client.get("/api/industrie-nationale/pays").json() == {"pays": ["DZA"]}
    r = client.get("/api/industrie-nationale/DZA", params={"lang": "en"}).json()
    assert (
        r["available"] is True
        and r["branches"][0]["libelle"] == "Food products, beverages and tobacco"
    )
    r = client.get("/api/industrie-nationale/DZA/exportations", params={"limite": 3}).json()
    assert len(r["produits"]) == 3
    assert (
        client.get(
            "/api/industrie-nationale/DZA/exportations", params={"region": "asie"}
        ).status_code
        == 422
    )
    r = client.get("/api/industrie-nationale/DZA/exportations/252310").json()
    assert r["available"] is True and r["exportations"][-1]["annee"] == 2024
