"""Mesures de la gazette EAC sur le droit de douane du socle.

Les remises de droits du Kenya ne s'appliquent que sur une autorisation datée
qui nomme la ligne ; les sursis d'application changent le taux du TEC pour
l'État partenaire qui les reçoit, et pour lui seul. Les dates sont fixées : les
mesures relevées couvrent l'année budgétaire EAC 2026/27.
"""

import importlib.util
import os
import sys
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine.schemas.legal_override import RemissionEligibility
from services import mesures_eac, socle

LE = date(2026, 10, 14)
AUTORISATION = dict(
    eligibilite=RemissionEligibility.ELIGIBLE_VERIFIED,
    reference="KRA/REM/2026/001",
    debut=date(2026, 7, 1),
    fin=date(2027, 6, 30),
    lignes=["10019910"],
)


def _position(**dd):
    return {
        "designation": "test",
        "droits": [
            {
                "code": "DD",
                "libelle": "Droit de douane",
                "famille": "droit",
                "assiette": "CIF",
                **dd,
            },
            {"code": "TVA", "famille": "tva", "taux": 16.0, "assiette": "CIF+DD"},
        ],
    }


def _dd(position):
    return next(d for d in position["droits"] if d["code"] == "DD")


def test_sans_autorisation_la_remise_n_est_pas_appliquee_et_la_note_le_dit():
    position, bloc = mesures_eac.appliquer(_position(taux=35.0), "KEN", "10019910", le=LE)
    dd = _dd(position)
    assert dd["taux"] == 35.0
    assert "Legal Notice EAC/161/2026" in dd["note"]
    assert "Taux du TEC appliqué" in dd["note"]
    assert bloc["autorisation_requise"] is True
    assert bloc["eligibilite_remise"] == "ELIGIBILITY_UNKNOWN"


def test_une_autorisation_datee_qui_nomme_la_ligne_applique_la_remise():
    position, bloc = mesures_eac.appliquer(
        _position(taux=35.0), "KEN", "10019910", le=LE, **AUTORISATION
    )
    assert _dd(position)["taux"] == 10.0
    assert "10 % au lieu de 35 % (TEC)" in _dd(position)["note"]
    assert bloc["taux_tec"] == 35.0 and bloc["taux_applique"] == 10.0


def test_une_autorisation_qui_ne_nomme_pas_la_ligne_ne_suffit_pas():
    autorisation = {**AUTORISATION, "lignes": ["10019990"]}
    position, bloc = mesures_eac.appliquer(
        _position(taux=35.0), "KEN", "10019910", le=LE, **autorisation
    )
    assert _dd(position)["taux"] == 35.0
    assert bloc["eligibilite_remise"] == "AUTHORIZATION_REQUIRED"


def test_une_autorisation_expiree_ne_suffit_pas():
    autorisation = {**AUTORISATION, "fin": date(2026, 9, 30)}
    position, bloc = mesures_eac.appliquer(
        _position(taux=35.0), "KEN", "10019910", le=LE, **autorisation
    )
    assert _dd(position)["taux"] == 35.0
    assert bloc["eligibilite_remise"] == "NOT_ELIGIBLE"


def test_une_mesure_du_kenya_ne_vaut_pas_pour_un_autre_etat_partenaire():
    position = _position(taux=35.0)
    assert mesures_eac.appliquer(position, "TZA", "10019910", le=LE, **AUTORISATION) == (
        position,
        None,
    )


def test_hors_de_sa_periode_une_mesure_ne_change_rien():
    position = _position(taux=35.0)
    assert mesures_eac.appliquer(
        position, "KEN", "10019910", le=date(2027, 7, 1), **AUTORISATION
    ) == (position, None)


def test_un_sursis_d_application_change_le_taux_sans_condition():
    position, bloc = mesures_eac.appliquer(_position(taux=50.0), "TZA", "52085110", le=LE)
    assert _dd(position)["taux"] == 35.0
    assert "Legal Notice EAC/160/2026" in _dd(position)["note"]
    assert bloc["autorisation_requise"] is False


def test_un_sursis_reserve_a_un_beneficiaire_laisse_le_taux_du_tec():
    """Tanzanie, cartes à puce : 0 % pour la seule National Identification
    Authority. Le bénéficiaire n'est pas établi, le TEC reste dû."""
    position, _ = mesures_eac.appliquer(_position(taux=25.0), "TZA", "85235200", le=LE)
    assert _dd(position)["taux"] == 25.0
    assert "bénéficiaire" in _dd(position)["note"]


def test_un_sursis_a_taux_mixte_est_porte_avec_sa_part_specifique():
    """« 35 % or USD 2/SQM, whichever is higher » : servir 35 % seul
    sous-estimerait le droit dès que la part au m² l'emporte."""
    base = _position(taux=25.0, specifique={"montant": 1.0, "unite_quantite": "kg"})
    position, _ = mesures_eac.appliquer(base, "TZA", "68021000", le=LE)
    dd = _dd(position)
    assert dd["taux"] == 35.0
    assert dd["compose"] is True and dd["regle_composee"] == "LE_PLUS_ELEVE"
    assert dd["specifique"]["montant"] == 2.0
    assert dd["specifique"]["unite_quantite"] == "m2"
    assert dd["specifique"]["unite_monetaire"] == "USD"


def test_une_remise_non_appliquee_garde_le_taux_compose_du_tec():
    specifique = {"montant": 345.0, "unite_monetaire": "USD", "unite_quantite": "mt"}
    base = _position(taux=35.0, specifique=specifique, compose=True, regle_composee="LE_PLUS_ELEVE")
    position, _ = mesures_eac.appliquer(base, "KEN", "10019910", le=LE)
    dd = _dd(position)
    assert dd["specifique"] == specifique and dd["regle_composee"] == "LE_PLUS_ELEVE"


def test_la_position_du_socle_n_est_pas_modifiee_en_place():
    base = _position(taux=35.0)
    mesures_eac.appliquer(base, "KEN", "10019910", le=LE, **AUTORISATION)
    assert _dd(base)["taux"] == 35.0 and "note" not in _dd(base)


# ── Par la route ─────────────────────────────────────────────────────────────
besoin_socle = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE), reason="socle absent : python3 scripts/build_socle.py"
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mesures_eac, "aujourdhui", lambda: LE)
    chemin = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "routes", "calcul.py"
    )
    spec = importlib.util.spec_from_file_location("routes_calcul_mesures_eac", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_mesures_eac"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    socle.vider_cache()
    yield TestClient(app)
    socle.vider_cache()


def _ligne_dd(reponse):
    return next(l for l in reponse["npf"]["lignes"] if l["code"] == "DD")


@besoin_socle
def test_la_route_applique_la_remise_sur_autorisation(client):
    demande = {"destination": "KEN", "code_sh": "10019910", "valeur_cif": 1000}
    sans = client.post("/calcul", json=demande).json()
    assert _ligne_dd(sans)["taux_pct"] == 35.0
    assert sans["mesures_eac"]["autorisation_requise"] is True

    remise = {
        "eligibilite": "ELIGIBLE_VERIFIED",
        "reference": "KRA/REM/2026/001",
        "debut": "2026-07-01",
        "fin": "2027-06-30",
        "lignes": ["10019910"],
    }
    avec = client.post("/calcul", json={**demande, "remise": remise}).json()
    assert _ligne_dd(avec)["taux_pct"] == 10.0
    assert _ligne_dd(avec)["montant"] == 100.0
    assert avec["mesures_eac"]["taux_applique"] == 10.0


@besoin_socle
def test_une_reference_faite_d_espaces_n_est_pas_une_autorisation(client):
    remise = {
        "eligibilite": "ELIGIBLE_VERIFIED",
        "reference": "   ",
        "debut": "2026-07-01",
        "fin": "2027-06-30",
        "lignes": ["10019910"],
    }
    reponse = client.post(
        "/calcul",
        json={"destination": "KEN", "code_sh": "10019910", "valeur_cif": 1000, "remise": remise},
    ).json()
    assert _ligne_dd(reponse)["taux_pct"] == 35.0
    assert reponse["mesures_eac"]["eligibilite_remise"] == "AUTHORIZATION_REQUIRED"


@besoin_socle
def test_la_route_reclame_la_surface_pour_un_sursis_mixte(client):
    reponse = client.post(
        "/calcul", json={"destination": "TZA", "code_sh": "68021000", "valeur_cif": 1000}
    ).json()
    dd = _ligne_dd(reponse)
    assert dd["statut"] == "QUANTITE_REQUISE"
    assert dd["unite_quantite"] == "m2"
