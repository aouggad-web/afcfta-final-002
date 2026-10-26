"""Droits et taxes à l'exportation (`POST /calcul/export`) : lus au socle et
liquidés par le moteur de `POST /calcul`, avec les mêmes refus — une assiette
non collectée, une quantité ou un taux de change manquant rendent la ligne
indisponible et la nomment, jamais un zéro."""

import importlib.util
import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services import socle

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pytestmark = pytest.mark.skipif(
    not all(os.path.exists(os.path.join(socle.SOCLE_DIR, f"{iso}.json")) for iso in ("TUN", "CIV", "MDG", "GHA", "SEN")),
    reason="socle absent : python3 scripts/build_socle.py",
)


@pytest.fixture(scope="module")
def client():
    nom = "routes_calcul_export_test"
    spec = importlib.util.spec_from_file_location(nom, os.path.join(BACKEND, "routes", "calcul_export.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    app = FastAPI()
    app.include_router(module.router)
    app.include_router(module.router_couverture)
    return TestClient(app)


def _export(client, **demande):
    reponse = client.post("/calcul/export", json=demande)
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["export"]


def _ligne(export, code):
    return next(ligne for ligne in export["lignes"] if ligne["code"] == code)


def test_pays_couverts(client):
    pays = client.get("/calcul/export/pays").json()["pays"]
    assert set(pays) == {"TUN", "CIV", "MDG", "GHA", "SEN"}


def test_tun_dattes_un_pour_cent_de_la_valeur(client):
    export = _export(client, pays="TUN", code_sh="0804100001", valeur=10000, devise="TND")
    assert export["etat"] == "COMPLET"
    assert _ligne(export, "DROIT.EXP.DATTES")["montant"] == pytest.approx(100.0)
    assert "total_a_payer" not in export


def test_tun_ferrailles_droit_specifique_exige_la_quantite(client):
    sans = _export(client, pays="TUN", code_sh="2620110000", valeur=10000, devise="TND")
    # La RPD s'assoit sur la taxe manquante : elle est incomplète, pas nulle.
    assert sans["etat"] == "INDISPONIBLE"
    assert _ligne(sans, "TAXE/FERRAILLES.EXP")["statut"] == "QUANTITE_REQUISE"
    assert _ligne(sans, "RPD/EXPOR")["statut"] == "ASSIETTE_INCOMPLETE"

    avec = _export(client, pays="TUN", code_sh="2620110000", valeur=10000, devise="TND", quantite=5000)
    assert avec["etat"] == "COMPLET"
    assert avec["total_droits"] == pytest.approx(1500.0)


def test_tun_rpd_liquidee_apres_les_droits_quelle_somme(client):
    """La RPD s'assoit sur la somme des autres droits : servie avant eux, sa
    base serait nulle (le moteur liquide dans l'ordre servi)."""
    export = _export(client, pays="TUN", code_sh="8549122000", valeur=1000, devise="TND", quantite=500)
    assert [ligne["code"] for ligne in export["lignes"]][-1] == "RPD/EXPOR"
    assert _ligne(export, "RPD/EXPOR")["base"] == pytest.approx(_ligne(export, "TAXE/FERRAILLES.EXP")["montant"])


def test_change_requis_dit_la_paire_monnaie_du_tarif(client):
    reponse = client.post("/calcul/export", json={
        "pays": "TUN", "code_sh": "2620110000", "valeur": 10_000, "devise": "USD", "quantite": 5_000})
    assert reponse.json()["change_requis"] == [{"devise_droit": "TND", "devise_valeur": "USD"}]


def test_gha_valeur_en_euros_le_droit_reste_en_dollars(client):
    """Codex : une valeur en EUR ne doit pas faire supposer un droit en GHS."""
    reponse = client.post("/calcul/export", json={
        "pays": "GHA", "code_sh": "2710192100", "valeur": 10_000, "devise": "EUR", "quantite": 1_000})
    assert reponse.json()["change_requis"] == [{"devise_droit": "USD", "devise_valeur": "EUR"}]


def test_tun_droit_en_dinars_et_valeur_en_dollars_exige_le_change(client):
    export = _export(client, pays="TUN", code_sh="2620110000", valeur=10000, devise="USD", quantite=5000)
    assert _ligne(export, "TAXE/FERRAILLES.EXP")["statut"] == "TAUX_DE_CHANGE_REQUIS"


def test_civ_karite_dix_francs_le_kilo(client):
    export = _export(client, pays="CIV", code_sh="1207991000", valeur=1000000, devise="XOF", quantite=20000)
    assert export["etat"] == "COMPLET"
    assert _ligne(export, "DUS")["montant"] == pytest.approx(200000.0)


def test_civ_cacao_prix_de_reference_non_collecte(client):
    export = _export(client, pays="CIV", code_sh="1801001100", valeur=1000000, devise="XOF")
    ligne = _ligne(export, "DUS")
    assert ligne["statut"] == "ASSIETTE_INDISPONIBLE"
    assert ligne["montant"] is None
    assert "PRIX CAF DE REFERENCE" in ligne["note"]


def test_mdg_nickel_droit_de_sortie_dix_pour_cent(client):
    """Tarif national 2026, colonne DS : « Valeur 10 » pour le nickel non allié."""
    export = _export(client, pays="MDG", code_sh="75021000", valeur=1_000_000, devise="MGA", produit_minier=False)
    assert export["etat"] == "COMPLET"
    assert _ligne(export, "DS")["montant"] == pytest.approx(100_000)


def test_mdg_ds_non_nul_et_produit_des_mines_le_conflit_est_dit(client):
    """Art. 285 du Code minier contre DS 10 % du tarif : montré, pas tranché."""
    export = _export(client, pays="MDG", code_sh="75021000", valeur=1_000_000, devise="MGA", produit_minier=True)
    assert "art. 285" in _ligne(export, "DS")["note"]
    assert _ligne(export, "DS")["montant"] == pytest.approx(100_000)


def test_mdg_or_droit_de_sortie_exonere(client):
    """« ex » au tarif : exonéré, liquidé à zéro — publié, pas absent."""
    export = _export(client, pays="MDG", code_sh="71081200", valeur=1_000_000, devise="MGA")
    ligne = _ligne(export, "DS")
    assert ligne["statut"] == "CALCULE" and ligne["montant"] == 0
    assert "exonéré" in ligne["note"]


def test_mdg_or_produit_des_mines_doit_les_dtspm(client):
    """Code minier, art. 283 : 2 % de ristourne + 3 % de redevance sur la
    valeur à l'exportation ; le DS du tarif reste exonéré (art. 285)."""
    export = _export(client, pays="MDG", code_sh="71081200", valeur=1_000_000, devise="MGA", produit_minier=True)
    assert export["etat"] == "COMPLET"
    assert _ligne(export, "DS")["montant"] == 0
    assert _ligne(export, "DTSPM.RISTOURNE")["montant"] == pytest.approx(20_000)
    assert _ligne(export, "DTSPM.REDEVANCE")["montant"] == pytest.approx(30_000)
    assert "art. 284" in _ligne(export, "DTSPM.REDEVANCE")["note"]


def test_mdg_substance_transformee_abattement_de_30_pour_cent(client):
    export = _export(
        client, pays="MDG", code_sh="71081200", valeur=1_000_000, devise="MGA",
        produit_minier=True, produit_minier_transforme=True,
    )
    assert export["total_droits"] == pytest.approx(35_000)


def test_mdg_sans_reponse_les_dtspm_restent_a_etablir(client):
    """Sans réponse, le DS exonéré seul ferait lire « rien à payer »."""
    export = _export(client, pays="MDG", code_sh="71081200", valeur=1_000_000, devise="MGA")
    assert export["etat"] == "PARTIEL"
    ligne = _ligne(export, "DTSPM.REDEVANCE")
    assert ligne["montant"] is None and ligne["note"].startswith("À établir")


def test_mdg_hors_produit_des_mines_pas_de_dtspm(client):
    export = _export(client, pays="MDG", code_sh="71081200", valeur=1_000_000, devise="MGA", produit_minier=False)
    assert [ligne["code"] for ligne in export["lignes"]] == ["DS"]


def test_les_questions_hors_tarif_sont_servies(client):
    questions = client.get("/calcul/export/pays").json()["questions"]
    assert set(questions) == {"MDG"} and questions["MDG"]["champ"] == "produit_minier"


def test_gha_quatrieme_annexe_zero_pour_cent_par_defaut(client):
    """Customs Act, Fourth Schedule, 4A.13 : tout autre bien national à 0 %."""
    export = _export(client, pays="GHA", code_sh="0901110000", valeur=10_000, devise="GHS")
    ligne = _ligne(export, "EXPORT")
    assert (export["etat"], ligne["montant"]) == ("COMPLET", 0)
    assert "4A.13" in ligne["note"]


def test_gha_gazole_publie_en_dollars(client):
    """4A.7 : $0.02/litre. En USD, aucun taux ; en GHS, le taux du dollar."""
    usd = _export(client, pays="GHA", code_sh="2710192100", valeur=10_000, devise="USD", quantite=1_000)
    assert _ligne(usd, "EXPORT")["montant"] == pytest.approx(20)
    reponse = client.post("/calcul/export", json={
        "pays": "GHA", "code_sh": "2710192100", "valeur": 10_000, "devise": "GHS", "quantite": 1_000})
    assert _ligne(reponse.json()["export"], "EXPORT")["statut"] == "TAUX_DE_CHANGE_REQUIS"
    # La paire est dite : le droit est publié en USD, pas dans la monnaie du tarif.
    assert reponse.json()["change_requis"] == [{"devise_droit": "USD", "devise_valeur": "GHS"}]
    ghs = _export(
        client, pays="GHA", code_sh="2710192100", valeur=10_000, devise="GHS", quantite=1_000, taux_de_change=15
    )
    assert _ligne(ghs, "EXPORT")["montant"] == pytest.approx(300)


def test_gha_cacao_taux_fixe_par_le_ministre(client):
    """« Cocoa Beans » sans autre précision : fèves brutes, torréfiées et brisures."""
    for code in ("1801001100", "1801002000", "1801003000"):
        ligne = _ligne(_export(client, pays="GHA", code_sh=code, valeur=10_000, devise="USD"), "EXPORT")
        assert ligne["montant"] is None and "Minister" in ligne["note"], code


def test_gha_carbureacteur_usage_a_etablir(client):
    """4A.6 ne vaut que pour les vols internationaux : sans l'usage, ni 0,09 $ ni 0 %."""
    export = _export(client, pays="GHA", code_sh="2710191100", valeur=10_000, devise="USD", quantite=1_000)
    ligne = _ligne(export, "EXPORT")
    assert ligne["montant"] is None and "international flights" in ligne["note"]


def test_gha_sh6_qui_regroupe_des_droits_differents(client):
    """271019 couvre carburéacteur et gazole, taxés, et d'autres huiles à 0 %."""
    ligne = _ligne(_export(client, pays="GHA", code_sh="271019", valeur=10_000, devise="USD"), "EXPORT")
    assert ligne["montant"] is None and "position nationale" in ligne["note"]


def test_sen_noix_de_cajou_32_francs_le_kilo(client):
    """Loi de finances 2026, art. 19 (texte du projet) : 32 F CFA/kg net."""
    export = _export(client, pays="SEN", code_sh="0801310000", valeur=1_000_000, devise="XOF", quantite=1_000)
    ligne = _ligne(export, "EXPORT")
    assert ligne["montant"] == pytest.approx(32_000)
    assert "loi n° 2025-19 promulguée n'a pas été consultée" in ligne["note"]


def test_sen_arachide_et_or_annonces_non_chiffres(client):
    for code in ("1202300000", "7108120000"):
        ligne = _ligne(_export(client, pays="SEN", code_sh=code, valeur=1_000_000, devise="XOF"), "EXPORT")
        assert ligne["montant"] is None and "n'a pas été consulté" in ligne["note"]


def test_position_sans_droit_de_sortie(client):
    reponse = client.post("/calcul/export", json={"pays": "CIV", "code_sh": "0101210000", "valeur": 1000})
    corps = reponse.json()
    assert corps["droits_export_publies"] is False
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"
    assert corps["export"]["lignes"] == []


def test_pays_sans_droit_export_au_socle(client):
    reponse = client.post("/calcul/export", json={"pays": "KEN", "code_sh": "0901110000", "valeur": 1000})
    assert reponse.status_code == 404


def test_sh6_exige_la_position_nationale(client):
    reponse = client.post("/calcul/export", json={"pays": "TUN", "code_sh": "080410", "valeur": 1000})
    assert reponse.status_code == 422
    assert reponse.json()["detail"]["code"] == "POSITION_NATIONALE_REQUISE"


def test_taux_de_change_en_devise_pour_un_dinar(client):
    """Comme pour POST /calcul : unités de `devise` pour UN dinar. 0,3 TND/kg
    × 5 000 kg = 1 500 TND, soit 483,87 USD à 3,1 TND pour 1 USD."""
    export = _export(
        client, pays="TUN", code_sh="2620110000", valeur=10000, devise="USD", quantite=5000, taux_de_change=1 / 3.1
    )
    assert _ligne(export, "TAXE/FERRAILLES.EXP")["montant"] == pytest.approx(1500 / 3.1, rel=1e-6)


def test_civ_chicoree_hors_regle_du_cafe(client):
    """La liste DGD nomme le café, pas la chicorée (2101.30) : la note du
    café ne s'y attache pas."""
    export = _export(client, pays="CIV", code_sh="2101300000", valeur=1000, devise="XOF")
    assert "CAFE" not in _ligne(export, "DUS")["note"]
    assert "CAFE" in _ligne(_export(client, pays="CIV", code_sh="2101110000", valeur=1000), "DUS")["note"]
