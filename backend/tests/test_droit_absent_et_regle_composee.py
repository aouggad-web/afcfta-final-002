"""Une absence se déclare, un barème écrit se lit, une règle muette se refuse.

Trois corrections d'un même défaut de fond : le socle ne liquide que ce qu'il
porte, donc une position dépourvue de ligne de droit se servait COMPLÈTE, sans
droit de douane. Mesuré le 2026-09-18 : 2 915 positions sur douze pays, dont
12 444,00 servis « COMPLET » pour DZA/2710122400 avec accise, TVA et zéro droit.

En remontant aux sources, ce n'était pas UN défaut mais cinq, et l'un d'eux n'en
était pas un :
  - 786 droits tunisiens SECTORIELS (« DD/VEH.AU », « DD/PET.BR »…) existaient,
    étaient liquidés, mais n'étaient pas reconnus comme droits de douane ;
  - 1 368 zéros éthiopiens avaient été supprimés à la collecte ;
  - 273 barèmes de l'EAC étaient écrits dans la DÉSIGNATION, pas dans la colonne ;
  - le reste est une lacune de source réelle, qui doit se dire.
"""

import importlib.util
import json
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE_PRESENT = os.path.exists(socle.MANIFESTE)
besoin_socle = pytest.mark.skipif(
    not SOCLE_PRESENT, reason="socle absent : python3 scripts/build_socle.py"
)


def _constructeur():
    spec = importlib.util.spec_from_file_location(
        "build_socle_absent_test", os.path.join(RACINE, "scripts", "build_socle.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _cache_propre():
    socle.vider_cache()
    yield
    socle.vider_cache()


@pytest.fixture
def client():
    chemin = os.path.join(RACINE, "backend", "routes", "calcul.py")
    spec = importlib.util.spec_from_file_location("routes_calcul_absent_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_absent_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


# ── Le droit de douane sectoriel tunisien ────────────────────────────────────
@pytest.mark.parametrize(
    ("code", "libelle"),
    [
        ("DD/PET.BR", "DD/PETROLE BRUT"),
        ("DD/VEH.AU", "DD/VEHICULES AUT."),
        ("DD/FUEL", "DD/FUEL"),
        ("DD/MAZOUT", "DD/MAZOUT"),
        ("DD/AUT.CA", "DD/AUTRE CARBURANT"),
    ],
)
def test_un_droit_de_douane_sectoriel_est_reconnu_comme_tel(code, libelle):
    """786 positions tunisiennes portaient un droit rangé en famille « autre ».

    Leurs MONTANTS étaient justes — ces droits étaient bien liquidés, à 0 %,
    15 % ou 30 %. C'est leur nature qui se perdait, et avec elle la possibilité
    de dire que la position porte un droit de douane.
    """
    assert _constructeur().code_canonique(code, libelle) == "DD"


def test_la_reconnaissance_sectorielle_ne_capture_pas_n_importe_quoi():
    """Contrôle négatif : le motif exige le séparateur, pas le simple préfixe."""
    module = _constructeur()
    assert module.code_canonique("DDT", "autre chose") != "DD"
    assert module.code_canonique("RPD/IMPOR", "REDEV.PREST.DOUA/IM") == "RPD"


# ── Le barème écrit dans la désignation ──────────────────────────────────────
def test_un_bareme_ecrit_dans_la_designation_est_lu():
    """« 75% or $345/MT whichever is higher » : les deux composantes ET la règle."""
    droit = _constructeur().droit_compose_depuis_designation(
        "- Rice in the husk (Paddy or rough) 75% or $345/MT whichever is higher", "EAC CET"
    )
    assert droit["taux"] == 75.0
    assert droit["specifique"]["montant"] == 345.0
    assert droit["specifique"]["unite_monetaire"] == "USD"
    assert droit["specifique"]["unite_quantite"] == "mt"
    assert droit["regle_composee"] == "LE_PLUS_ELEVE"
    assert droit["famille"] == "droit"


def test_la_notation_en_dollars_par_kilo_est_lue_aussi():
    """Le tarif écrit « $345/MT » ici et « USD 0.40/kg » là — deux notations."""
    droit = _constructeur().droit_compose_depuis_designation(
        "--- Other worn items 35% or USD 0.40/kg whichever is higher", "EAC CET"
    )
    assert (droit["taux"], droit["specifique"]["montant"]) == (35.0, 0.40)
    assert droit["specifique"]["unite_quantite"] == "kg"


@pytest.mark.parametrize(
    "designation",
    [
        "- True hemp raw or retted",
        "General Customs Duty 40% or 240c/kg",
        "Rice 75% or $345/MT",
        "",
    ],
    ids=["sans_taux", "regle_muette_SARS", "sans_regle", "vide"],
)
def test_une_designation_incomplete_ne_produit_aucun_droit(designation):
    """Contrôle négatif, et le plus important.

    Rien n'est lu tant que les DEUX composantes et la RÈGLE n'y sont pas. En
    particulier « 40% or 240c/kg », la forme sud-africaine, ne dit pas laquelle
    s'applique : elle ne doit surtout pas être happée ici.
    """
    assert _constructeur().droit_compose_depuis_designation(designation, "src") is None


# ── Ce que le socle porte ────────────────────────────────────────────────────
@besoin_socle
def test_plus_aucune_position_ne_se_sert_sans_droit():
    """L'invariant qui résume tout le chantier.

    Dans un pays qui publie des droits, une position qui n'en porte aucun — et
    dont l'importation n'est pas interdite — servirait un total amputé en se
    présentant comme complet.
    """
    muettes = []
    for iso in socle.pays_servis():
        donnees = socle.charger(iso)
        if not (donnees.get("couverture") or {}).get("droit_de_douane"):
            continue
        for code, position in (donnees.get("positions") or {}).items():
            if position.get("restrictions"):
                continue
            if not any(d.get("famille") == "droit" for d in position.get("droits") or []):
                muettes.append(f"{iso}/{code}")
    assert muettes == [], f"positions sans droit : {muettes[:5]} ({len(muettes)} au total)"


@besoin_socle
def test_une_absence_de_droit_se_declare_au_lieu_de_disparaitre(client):
    """Maroc 0405100010 : la source ne publie AUCUNE taxe (`taxes: {}`)."""
    reponse = client.post(
        "/calcul", json={"destination": "MAR", "code_sh": "0405100010", "valeur_cif": 10000}
    )
    assert reponse.status_code == 200
    npf = reponse.json()["npf"]
    ligne = next(l for l in npf["lignes"] if l["code"] == "DD")
    assert ligne["statut"] == "TAUX_INDISPONIBLE"
    assert ligne["montant"] is None
    assert npf["etat"] != "COMPLET"


@besoin_socle
def test_le_bareme_de_l_EAC_se_liquide_selon_sa_propre_regle(client):
    """« Le plus élevé des deux » appliqué, et la composante retenue nommée.

    Riz kényan, 75 % ou 345 $/MT. Sur 10 tonnes et 10 000 de valeur, l'ad
    valorem l'emporte (7 500 contre 3 450) ; sur 100 tonnes, le spécifique
    l'emporte (34 500 contre 7 500). L'opérateur doit pouvoir constater
    laquelle a mordu.
    """

    def dd(quantite):
        r = client.post(
            "/calcul",
            json={
                "destination": "KEN",
                "code_sh": "10061000",
                "valeur_cif": 10000,
                "quantite": quantite,
                "devise_cif": "USD",
            },
        )
        assert r.status_code == 200
        return next(l for l in r.json()["npf"]["lignes"] if l["code"] == "DD")

    petite = dd(10)
    assert petite["montant"] == pytest.approx(7500.0)
    assert petite["composante_retenue"] == "ad_valorem"

    grande = dd(100)
    assert grande["montant"] == pytest.approx(34500.0)
    assert grande["composante_retenue"] == "specifique"
    assert grande["composantes"]["ad_valorem_montant"] == pytest.approx(7500.0)


@besoin_socle
def test_sans_quantite_le_bareme_compose_reclame_la_quantite(client):
    reponse = client.post(
        "/calcul", json={"destination": "KEN", "code_sh": "10061000", "valeur_cif": 10000}
    )
    ligne = next(l for l in reponse.json()["npf"]["lignes"] if l["code"] == "DD")
    assert ligne["statut"] == "QUANTITE_REQUISE"
    assert ligne["montant"] is None


@besoin_socle
def test_deux_devises_ne_se_comparent_pas_sans_taux_de_change(client):
    """La composante spécifique est en dollars ; la comparer à un ad valorem
    calculé sur une valeur en shillings rendrait un droit faux sans le dire."""
    reponse = client.post(
        "/calcul",
        json={
            "destination": "KEN",
            "code_sh": "10061000",
            "valeur_cif": 10000,
            "quantite": 100,
            "devise_cif": "KES",
        },
    )
    ligne = next(l for l in reponse.json()["npf"]["lignes"] if l["code"] == "DD")
    assert ligne["statut"] == "TAUX_DE_CHANGE_REQUIS"
    assert ligne["montant"] is None


@besoin_socle
def test_la_regle_muette_sud_africaine_reste_refusee(client):
    """Non-régression : « 40% or 240c/kg » ne dit pas laquelle s'applique.

    Le départage ajouté ici ne vaut QUE pour les barèmes qui énoncent leur
    règle. Celui-là ne l'énonce pas et doit continuer d'être refusé.
    """
    reponse = client.post(
        "/calcul", json={"destination": "ZAF", "code_sh": "020110", "valeur_cif": 10000}
    )
    ligne = next(l for l in reponse.json()["npf"]["lignes"] if l["code"] == "DD")
    assert ligne["statut"] == "REGLE_COMPOSEE_NON_ETABLIE"
    assert ligne["montant"] is None
