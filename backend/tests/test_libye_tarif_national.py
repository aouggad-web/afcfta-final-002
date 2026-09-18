"""Le tarif national libyen : ce qu'il dit, et ce qu'il ne faut pas lui faire dire.

La Libye a été le pays le plus mal servi du socle : un droit issu d'une moyenne
SH6 de la Banque mondiale, aucune désignation, aucune position liquidable. Le
tarif officiel 2022 (customs.gov.ly) l'a remplacé. Ces tests tiennent les cinq
pièges relevés en le lisant.
"""

import importlib.util
import json
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

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _crawler():
    chemin = os.path.join(RACINE, "backend", "crawlers", "countries", "libya_customs_scraper.py")
    spec = importlib.util.spec_from_file_location("libya_scraper_test", chemin)
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
    spec = importlib.util.spec_from_file_location("routes_calcul_lby_test", chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules["routes_calcul_lby_test"] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


# ── Le piège du facteur cent ─────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("cellule", "attendu"),
    [
        ("0.05", 5.0),
        ("5%", 5.0),
        ("0.3", 30.0),
        ("30%", 30.0),
        ("0.1", 10.0),
        ("10%", 10.0),
    ],
    ids=["fraction_5", "pourcent_5", "fraction_30", "pourcent_30", "fraction_10", "pourcent_10"],
)
def test_les_deux_ecritures_du_meme_taux_donnent_le_meme_taux(cellule, attendu):
    """Le tarif écrit le MÊME taux de deux façons, dans la même colonne.

    Relevé sur le XLSX officiel 2022 : 4 382 cellules « 0.05 » et 356 cellules
    « 5% », toutes valant 5 %. Lire « 0.05 » comme 0,05 % liquiderait 73 % du
    tarif à un centième de sa valeur.
    """
    assert _crawler().parse_rate(cellule) == attendu


def test_une_exoneration_publiee_vaut_zero_et_non_un_manque():
    """« معفاة » est un zéro publié par le tarif, pas une donnée absente."""
    assert _crawler().parse_rate("معفاة") == 0.0


def test_une_interdiction_n_est_pas_un_taux():
    """« ممنوع استيراده » n'est ni un taux ni un zéro : la marchandise ne passe pas."""
    module = _crawler()
    taux, interdit = module.lire_cellule_droit("ممنوع استيراده")
    assert taux is None
    assert interdit is True


def test_un_texte_non_reconnu_ne_devient_jamais_zero():
    """Contrôle négatif : aucun zéro de substitution sur ce qu'on ne sait pas lire."""
    assert _crawler().parse_rate("à confirmer") is None


# ── La feuille piégeuse ──────────────────────────────────────────────────────
def test_la_feuille_du_tarif_est_nommee_et_le_decompte_controle():
    """Le classeur porte une feuille de 1 040 896 lignes dont 422 codées.

    La prendre par son RANG marcherait aujourd'hui et casserait en silence si
    la douane réordonnait son classeur. Elle est nommée, et le décompte obtenu
    est contrôlé — une collecte amputée est refusée, pas servie.
    """
    module = _crawler()
    assert module.FEUILLE_TARIF == "ورقة1"
    assert module.POSITIONS_ATTENDUES_MIN >= 5000


# ── Ce que le socle sert ─────────────────────────────────────────────────────
@besoin_socle
def test_le_socle_sert_le_tarif_national_et_non_une_moyenne_SH6():
    donnees = socle.charger("LBY")
    assert "douanes.mr" not in (donnees["source"]["nom"] or "")
    assert "WITS" not in (donnees["source"]["nom"] or "")
    assert donnees["compteurs"]["positions"] > 5500
    # Les désignations arabes du tarif officiel sont portées.
    assert donnees["compteurs"]["sans_designation"] == 0


@besoin_socle
def test_la_libye_n_a_pas_de_tva_et_n_en_recoit_pas_une_fabriquee():
    """Zéro occurrence de la TVA dans la loi libyenne, aucune colonne au tarif.

    D'autres pays de la famille D reçoivent un taux national standard quand leur
    tarif n'en porte pas (Mauritanie 16 %, Madagascar 20 %). Pas la Libye : il
    n'y a pas de TVA à l'importation dans les textes consultés, et en inventer
    une surfacturerait chaque calcul.
    """
    donnees = socle.charger("LBY")
    assert "tva" not in donnees["couverture"]["familles"]
    assert donnees["couverture"]["tva"] is False
    for position in list(donnees["positions"].values())[:200]:
        assert all(d.get("famille") != "tva" for d in position["droits"])


@besoin_socle
def test_la_colonne_preferentielle_ne_tombe_jamais_dans_la_cascade_NPF():
    """La colonne « États de la Ligue des États arabes » est un régime, pas un dû.

    Elle a déjà été servie comme un droit ordinaire, faute d'une clé normalisée
    dans la table des régimes du constructeur : elle entrait alors dans la
    cascade NPF au lieu d'être rangée à part.
    """
    donnees = socle.charger("LBY")
    # Le socle sert désormais le CODE NATIONAL. Il rabattait auparavant les
    # positions libyennes sur six chiffres et en perdait 349 par collision ;
    # l'adresse change, l'assertion non.
    position = donnees["positions"]["01012100"]
    assert "LIGUE_ARABE" in (position.get("preferentiels") or {})
    codes = {d["code"] for d in position["droits"]}
    assert "LIGUEARABE" not in codes
    assert "LIGUE_ARABE" not in codes


@besoin_socle
def test_une_position_interdite_porte_sa_restriction_et_aucun_droit(client):
    """« Interdit » est une RÉPONSE ; sans elle on lit « indisponible ».

    Une position prohibée ne porte aucun droit, et c'est normal. Si le socle
    perd la restriction, elle se présente exactement comme un calcul qui a
    échoué — l'opérateur croit à une lacune sur une marchandise qui ne peut
    pas entrer.
    """
    donnees = socle.charger("LBY")
    position = donnees["positions"]["220300"]
    restrictions = position.get("restrictions")
    assert restrictions, "la restriction a été perdue entre le crawl et le socle"
    assert restrictions[0]["type"] == "IMPORTATION_INTERDITE"
    assert restrictions[0]["verbatim"] == "ممنوع استيراده"
    assert not any(d["code"] == "DD" for d in position["droits"])

    reponse = client.post(
        "/calcul", json={"destination": "LBY", "code_sh": "22030000", "valeur_cif": 10000}
    )
    assert reponse.status_code == 200
    servi = reponse.json().get("restrictions")
    assert servi and servi[0]["type"] == "IMPORTATION_INTERDITE"


@besoin_socle
def test_une_position_ordinaire_ne_porte_aucune_restriction(client):
    """Contrôle négatif : le champ n'apparaît que là où il a un sens."""
    reponse = client.post(
        "/calcul", json={"destination": "LBY", "code_sh": "01012100", "valeur_cif": 10000}
    )
    assert reponse.status_code == 200
    assert "restrictions" not in reponse.json()


@besoin_socle
def test_le_tabac_porte_un_droit_bien_superieur_au_droit_courant(client):
    """Corroboration : PwC écrit « droits abolis en 2005, SAUF TABAC ».

    Le tarif officiel 2022 le confirme sans qu'on ait eu à l'y chercher : la
    cigarette est à 30 % quand la plupart des marchandises sont à 5 %. Ce test
    n'existe pas pour figer un taux, mais pour que la disparition de cet écart
    soit remarquée.
    """
    courant = client.post(
        "/calcul", json={"destination": "LBY", "code_sh": "01012100", "valeur_cif": 10000}
    ).json()
    tabac = client.post(
        "/calcul", json={"destination": "LBY", "code_sh": "24022000", "valeur_cif": 10000}
    ).json()

    def droit(reponse):
        return next(l for l in reponse["npf"]["lignes"] if l["code"] == "DD")

    assert droit(courant)["montant"] == pytest.approx(500.0)
    assert droit(tabac)["montant"] == pytest.approx(3000.0)


@besoin_socle
def test_une_cellule_vide_se_declare_indisponible_au_lieu_de_disparaitre():
    """Une cellule vide n'est ni une exonération ni une interdiction.

    Ne rien émettre ferait servir la position comme si aucun prélèvement
    n'était dû — un total « complet » amputé de son droit. Neuf positions du
    tarif 2022 sont dans ce cas.
    """
    chemin = os.path.join(RACINE, "backend", "data", "crawled", "LBY_tariffs.json")
    with open(chemin, encoding="utf-8") as f:
        collecte = json.load(f)
    positions = collecte["sub_positions"]

    muettes = [p for p in positions if not p["taxes"] and not p["restrictions"]]
    assert muettes == [], "une position sans droit ET sans restriction serait servie pour rien"

    sans_taux = [
        p
        for p in positions
        if any(t["code"] == "DD" and t.get("rate_pct") is None for t in p["taxes"])
    ]
    assert sans_taux, "les cellules vides doivent être déclarées, pas tues"
