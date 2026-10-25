"""Consultation du tarif par le socle : les sous-positions proposées à l'écran
sont celles que POST /calcul sait liquider, et les formalités sont celles que
la source publie pour la position."""

import importlib
import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not all(os.path.exists(os.path.join(socle.SOCLE_DIR, f"{iso}.json")) for iso in ("TUN", "EGY", "DZA", "MAR", "KEN", "ZAF")),
    reason="socle absent : python3 scripts/build_socle.py",
)


def _route(nom):
    spec = importlib.util.spec_from_file_location(f"routes_{nom}_test", os.path.join(BACKEND, "routes", f"{nom}.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"routes_{nom}_test"] = module
    spec.loader.exec_module(module)
    return module.router


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(_route("consultation"))
    app.include_router(_route("calcul"))
    return TestClient(app)


def test_sous_positions_lues_au_socle(client):
    reponse = client.get("/consultation/TUN/sous-positions/870323")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["source"] == "socle"
    assert corps["total"] == len(corps["sub_positions"]) > 1
    premiere = corps["sub_positions"][0]
    assert premiere["code"].startswith("870323") and premiere["digits"] == 10
    assert "cle_controle" in premiere
    assert isinstance(premiere["description_fr"], str) and premiere["description_fr"]


def test_le_droit_de_douane_est_celui_du_socle(client):
    ligne = client.get("/consultation/EGY/sous-positions/220830").json()["sub_positions"][0]
    assert ligne["code"] == "2208300000" and ligne["dd_rate"] == 3000.0


def test_memes_positions_que_le_calcul_en_reclame(client):
    """Un SH6 à plusieurs positions : la liste servie est exactement celle que
    POST /calcul nomme dans son refus POSITION_NATIONALE_REQUISE."""
    refus = client.post("/calcul", json={"destination": "TUN", "code_sh": "870323", "valeur_cif": 1000})
    assert refus.status_code == 422
    attendues = [p["code"] for p in refus.json()["detail"]["positions"]]
    servies = [p["code"] for p in client.get("/consultation/TUN/sous-positions/870323").json()["sub_positions"]]
    assert servies == attendues


def test_pays_hors_socle_et_code_invalide(client):
    assert client.get("/consultation/XXX/sous-positions/010121").status_code == 503
    assert client.get("/consultation/EGY/sous-positions/12").status_code == 422


def _formalites(client, iso, code):
    reponse = client.get(f"/consultation/{iso}/formalites/{code}")
    assert reponse.status_code == 200
    return reponse.json()


def test_algerie_la_fiche_dgd_de_la_position(client):
    corps = _formalites(client, "DZA", "0101.21.11.00")
    assert corps["statut"] == "DOCUMENTEES" and corps["reserve"] is None
    assert [f["code"] for f in corps["formalities"]] == ["160", "180"]
    # Source exhaustive : une fiche sans tableau est un constat, pas une lacune.
    corps = _formalites(client, "DZA", "1520002000")
    assert corps["statut"] == "AUCUNE_FORMALITE_PARTICULIERE" and corps["formalities"] == []


def test_egypte_l_arabe_officiel_et_la_traduction_signalee(client):
    formalite = _formalites(client, "EGY", "0101210000")["formalities"][0]
    assert formalite["texte"].startswith(formalite["code"])
    assert formalite["traduction_non_officielle"] is True
    assert formalite["document_fr"] != formalite["texte"]


def test_maroc_le_constat_n_est_que_celui_de_la_source(client):
    """« Aucun document à présenter » est publié par l'ADIL pour la position ;
    une position sans mention reste « non établies »."""
    assert _formalites(client, "MAR", "2201100090")["statut"] == "AUCUNE_FORMALITE_PARTICULIERE"
    corps = _formalites(client, "MAR", "0201100011")
    assert corps["statut"] == "NON_ETABLIES" and "absence d'obligation" in corps["reserve"]


def test_sans_source_et_position_introuvable(client):
    assert _formalites(client, "KEN", "01012900")["statut"] == "NON_ETABLIES"
    corps = _formalites(client, "MAR", "9999999999")
    assert corps["statut"] == "POSITION_INTROUVABLE" and corps["reserve"]


def _recherche(client, iso3, q, **params):
    reponse = client.get(f"/consultation/{iso3}/recherche", params={"q": q, **params})
    assert reponse.status_code == 200
    return reponse.json()


def test_recherche_par_code_lue_au_socle(client):
    corps = _recherche(client, "TUN", "0902.10")
    assert corps["source"] == "socle"
    codes = [r["code"] for r in corps["results"]]
    assert codes == sorted(codes) and codes and all(c.startswith("090210") for c in codes)
    assert set(codes) <= set(socle.charger("TUN")["positions"])


def test_recherche_par_mots_sans_accents_ni_casse(client):
    assert _recherche(client, "KEN", "café")["results"] == _recherche(client, "KEN", "CAFE")["results"]
    corps = _recherche(client, "MAR", "thé vert")
    assert corps["total"] >= 1 and all(r["code"].startswith("0902") for r in corps["results"])


def test_recherche_un_mot_commence_un_mot_de_la_designation(client):
    """« vert » ne trouve pas « invertebrates », ni « thé » l'article anglais."""
    assert all(r["code"].startswith("0902") for r in _recherche(client, "MAR", "thé vert")["results"])
    the = _recherche(client, "MAR", "thé", limit=100)
    assert the["total"] < 200 and any(r["code"].startswith("0902") for r in the["results"])
    assert _recherche(client, "TUN", "..")["total"] == 0


def test_recherche_un_code_mele_aux_mots_borne_le_code(client):
    corps = _recherche(client, "MAR", "87.03 voiture")
    assert corps["total"] >= 1 and all(r["code"].startswith("8703") for r in corps["results"])


def test_recherche_textes_prepares_une_fois_par_chargement(client):
    module = sys.modules["routes_consultation_test"]
    positions = socle.charger("KEN")["positions"]
    _recherche(client, "KEN", "coffee", langue="en")
    assert module._textes["KEN"][0] is positions
    premier = module._textes["KEN"][2]
    _recherche(client, "KEN", "tea", langue="en")
    assert module._textes["KEN"][2] is premier
    assert module._textes["KEN"][1] == "en"  # KEN publie en anglais


def test_recherche_l_intitule_sh4_situe_une_ligne_sans_designation_propre(client):
    """« Other » sous 2402 : trouvée par « cigarettes », située par l'intitulé SH4."""
    corps = _recherche(client, "ZAF", "cigarettes", limit=2, langue="en")
    assert corps["total"] > len(corps["results"]) == 2
    ligne = corps["results"][0]
    assert ligne["hs6"] == ligne["code"][:6] and ligne["digits"] == len(ligne["code"])
    assert "cigarettes" in ligne["intitule_sh4"].lower()


def test_recherche_ne_sert_que_le_droit_de_douane(client):
    """Ni total ni TVA : le montant des droits et taxes est celui de POST /calcul."""
    ligne = _recherche(client, "KEN", "coffee", langue="en")["results"][0]
    assert set(ligne) == {
        "code", "hs6", "digits", "description_fr", "description_en", "intitule_sh4", "dd_rate", "dd_expression"
    }


def test_recherche_pays_invalide_ou_hors_socle(client):
    assert client.get("/consultation/zz/recherche", params={"q": "cafe"}).status_code == 422
    assert client.get("/consultation/XXX/recherche", params={"q": "cafe"}).status_code == 503
    assert client.get("/consultation/KEN/recherche", params={"q": "a"}).status_code == 422


def test_recherche_les_mots_entiers_d_abord_puis_par_code(client):
    """« thé » : le thé (0902) avant « théophylline » (2939), bien que 2939
    vienne après 0902 et 0302 avant ; dans chaque groupe, l'ordre du code."""
    codes = [r["code"] for r in _recherche(client, "MAR", "thé", limit=100)["results"]]
    the = [c for c in codes if c.startswith("0902")]
    assert codes[: len(the)] == the == sorted(the)
    assert codes.index(next(c for c in codes if c.startswith("2939"))) > len(the)
    reste = codes[len(the):]
    assert any(c < the[0] for c in reste)  # un début de mot classé plus bas que son code


def test_recherche_dans_la_langue_de_l_interface(client):
    """Français : le tarif en français ; anglais : le tarif en anglais."""
    assert _recherche(client, "DZA", "lait")["total"] > 0
    assert _recherche(client, "DZA", "lait", langue="en")["total"] == 0
    assert _recherche(client, "DZA", "milk", langue="en")["total"] > 0  # libellés SH6 anglais
    assert _recherche(client, "KEN", "coffee", langue="en")["total"] > 0
    assert _recherche(client, "KEN", "coffee")["total"] == 0
    assert _recherche(client, "KEN", "café")["total"] > 0  # libellés SH6 français
    corps = _recherche(client, "MAR", "tea", langue="en")
    assert corps["langue"] == "en" and corps["results"][0]["code"].startswith("0902")
    assert client.get("/consultation/KEN/recherche", params={"q": "tea", "langue": "de"}).status_code == 422


@pytest.mark.parametrize(
    "module",
    [
        "services.authentic_tariff_service",
        "services.tariff_provider_service",
        "services.postgres_tariff_service",
        "services.national_legal_calculation_service",
        "services.export_tariff_service",
        "engine.national_customs_calculation",
        "routes.authentic_tariffs",
        "routes.postgres_tariffs",
        "routes.hs6_database",
        "routes.search",
        "search.hs_code_search",
    ],
)
def test_l_ancien_service_est_retire(module):
    """Une seule recherche (celle-ci), une seule consultation, un seul calcul
    (POST /calcul) : l'ancien service et ses routes ne reviennent pas."""
    assert importlib.util.find_spec(module) is None


def test_l_ancienne_table_de_profils_est_retiree():
    from services import tax_profile_data

    assert not hasattr(tax_profile_data, "COUNTRY_TAX_PROFILES")
