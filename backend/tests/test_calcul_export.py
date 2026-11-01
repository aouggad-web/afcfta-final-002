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
    not all(os.path.exists(os.path.join(socle.SOCLE_DIR, f"{iso}.json")) for iso in ("TUN", "CIV", "MDG", "GHA", "SEN", "ZMB", "MLI", "KEN", "TZA", "ZAF")),
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
    assert set(pays) == {"TUN", "CIV", "MDG", "GHA", "SEN", "ZMB", "MLI", "KEN", "TZA", "ZAF", "CMR", "EGY", "COG", "GAB",
                         "COD"}
    # Le Mali n'a pas de droit au tarif : seule la TEOAPM, hors tarif.
    assert pays["MLI"] == 0


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
    assert set(questions) == {"MDG", "MLI", "CMR", "COG", "GAB", "COD"} and questions["MDG"]["champ"] == "produit_minier"
    assert questions["GAB"]["champ"] == "produit_en_bois" and questions["GAB"]["question_en"]
    assert questions["CMR"]["champ"] == questions["COG"]["champ"] == "produit_fini"
    assert questions["COD"]["champ"] == "titulaire_minier"
    # Le CGI malien ne prévoit pas d'abattement : pas de seconde question.
    assert questions["MLI"]["question_transformation"] is None and questions["MLI"]["question_en"]
    # Congo : après un « non », la redevance informatique demande si le produit est brut.
    assert questions["COG"]["champ_si_non"] == "produit_transforme" and questions["COG"]["question_si_non_en"]
    assert questions["CMR"]["champ_si_non"] is None


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


def test_sen_noix_de_cajou_brute_32_francs_le_kilo(client):
    """Loi n° 2025-19, art. 19 : 32 F CFA/kg net sur la noix brute (en coques)."""
    export = _export(client, pays="SEN", code_sh="0801310000", valeur=1_000_000, devise="XOF", quantite=1_000)
    ligne = _ligne(export, "EXPORT")
    assert ligne["montant"] == pytest.approx(32_000)
    assert "2025-19" in ligne["note"]


def test_sen_amandes_de_cajou_non_etablies(client):
    """L'exposé vise la noix brute : les amandes (sans coques) ne sont pas tranchées."""
    ligne = _ligne(_export(client, pays="SEN", code_sh="0801320000", valeur=1_000_000, devise="XOF"), "EXPORT")
    assert ligne["montant"] is None and "noix brutes" in ligne["note"]


def test_sen_arachide_suspension_annoncee_non_etablie(client):
    """Une suspension inscrite à l'annexe d'un projet de LFR ne vaut pas un droit nul établi."""
    ligne = _ligne(_export(client, pays="SEN", code_sh="1202300000", valeur=1_000_000, devise="XOF"), "EXPORT")
    assert ligne["montant"] is None and "suspension" in ligne["note"]


def test_sen_or_sans_recouvrement_ni_taux(client):
    ligne = _ligne(_export(client, pays="SEN", code_sh="7108120000", valeur=1_000_000, devise="XOF"), "EXPORT")
    assert ligne["montant"] is None and "aucun recouvrement" in ligne["note"]



def test_zmb_concentre_de_cuivre_dix_pour_cent(client):
    """Ninth Schedule : 10 % ; la suspension par quotas de 2026 a pris fin le 30 septembre."""
    export = _export(client, pays="ZMB", code_sh="26030021", valeur=1_000_000, devise="ZMW")
    ligne = _ligne(export, "EXPORT")
    assert (export["etat"], ligne["montant"]) == ("COMPLET", pytest.approx(100_000))
    assert "SI n° 43" in ligne["note"]


def test_zmb_en_tete_vaut_pour_ses_lignes(client):
    """« 71.08 … 15% », « 44.01 … 40% » : l'en-tête couvre les positions nationales."""
    assert _ligne(_export(client, pays="ZMB", code_sh="71081200", valeur=1_000, devise="ZMW"),
                  "EXPORT")["montant"] == pytest.approx(150)
    assert _ligne(_export(client, pays="ZMB", code_sh="44011100", valeur=1_000, devise="ZMW"),
                  "EXPORT")["montant"] == pytest.approx(400)


def test_zmb_ferrailles_le_plus_eleve_des_deux(client):
    """** : « 25% or KR 1,000 per tonne whichever is greater »."""
    sans = _export(client, pays="ZMB", code_sh="72041000", valeur=100_000, devise="ZMW")
    assert _ligne(sans, "EXPORT")["montant"] is None
    ligne = _ligne(_export(client, pays="ZMB", code_sh="72041000", valeur=100_000, devise="ZMW", quantite=200),
                   "EXPORT")
    assert (ligne["montant"], ligne["composante_retenue"]) == (pytest.approx(200_000), "specifique")
    ligne = _ligne(_export(client, pays="ZMB", code_sh="72041000", valeur=100_000, devise="ZMW", quantite=10),
                   "EXPORT")
    assert (ligne["montant"], ligne["composante_retenue"]) == (pytest.approx(25_000), "ad_valorem")


def test_zmb_ligne_ex_a_etablir(client):
    """« Ex8111.00.00 » : le droit ne vise qu'une partie de la position."""
    ligne = _ligne(_export(client, pays="ZMB", code_sh="81110000", valeur=1_000, devise="ZMW"), "EXPORT")
    assert ligne["montant"] is None and "Ex" in ligne["note"]


def test_zmb_position_mixte_a_etablir(client):
    """Codex : « Cermets waste and scrap » ne vaut pas pour les ouvrages de 8113.00.00."""
    for code in ("81130000", "81061000"):
        ligne = _ligne(_export(client, pays="ZMB", code_sh=code, valeur=1_000, devise="ZMW", quantite=1), "EXPORT")
        assert ligne["montant"] is None and "à établir" in ligne["note"], code


def test_zmb_position_hors_annexe(client):
    corps = client.post("/calcul/export", json={
        "pays": "ZMB", "code_sh": "09011100", "valeur": 1_000, "devise": "ZMW"}).json()
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"


def test_mli_teoapm_deux_pour_cent_de_la_valeur(client):
    """CGI, art. 253-AJ : 2 % de « la valeur du produit à l'exportation »."""
    export = _export(client, pays="MLI", code_sh="7108120000", valeur=1_000_000, devise="XOF", produit_minier=True)
    ligne = _ligne(export, "TEOAPM")
    assert (export["etat"], ligne["montant"]) == ("COMPLET", pytest.approx(20_000))
    assert "253-AG" in ligne["source"] and "2025-006" in ligne["note"]


def test_mli_teoapm_sans_reponse_a_etablir_et_sans_abattement(client):
    sans = _ligne(_export(client, pays="MLI", code_sh="7108120000", valeur=1_000_000, devise="XOF"), "TEOAPM")
    assert sans["montant"] is None and "Code minier" in sans["note"]
    # Le CGI ne prévoit aucun abattement : la case de Madagascar n'a pas d'effet.
    transforme = _export(client, pays="MLI", code_sh="7108120000", valeur=1_000_000, devise="XOF",
                         produit_minier=True, produit_minier_transforme=True)
    assert _ligne(transforme, "TEOAPM")["montant"] == pytest.approx(20_000)


def test_mli_exportateur_regi_par_le_code_minier(client):
    corps = client.post("/calcul/export", json={
        "pays": "MLI", "code_sh": "7108120000", "valeur": 1_000_000, "devise": "XOF",
        "produit_minier": False}).json()
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"
    reponse = client.post("/calcul/export", json={"pays": "CIV", "code_sh": "0101210000", "valeur": 1000})
    corps = reponse.json()
    assert corps["droits_export_publies"] is False
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"
    assert corps["export"]["lignes"] == []



def test_ken_melasse_vingt_pour_cent(client):
    """First Schedule : molasses, « 20% of the customs value »."""
    export = _export(client, pays="KEN", code_sh="17031000", valeur=1_000_000, devise="KES")
    assert (export["etat"], _ligne(export, "EXPORT")["montant"]) == ("COMPLET", pytest.approx(200_000))


def test_ken_minerai_de_fer_en_dollars_la_tonne(client):
    """« USD 175 per tonne » : en USD, aucun change ; en KES, la paire est dite."""
    usd = _export(client, pays="KEN", code_sh="26011100", valeur=100_000, devise="USD", quantite=10)
    assert _ligne(usd, "EXPORT")["montant"] == pytest.approx(1_750)
    corps = client.post("/calcul/export", json={
        "pays": "KEN", "code_sh": "26011100", "valeur": 10_000_000, "devise": "KES", "quantite": 10}).json()
    assert corps["change_requis"] == [{"devise_droit": "USD", "devise_valeur": "KES"}]


def test_ken_peaux_unite_du_specifique_non_publiee(client):
    """« 50% or USD 0.32 whichever is higher » : sans unité, le plus élevé ne se calcule pas."""
    ligne = _ligne(_export(client, pays="KEN", code_sh="41012000", valeur=1_000_000, devise="KES"), "EXPORT")
    assert ligne["montant"] is None and "unité" in ligne["note"]


def test_ken_hors_annexe_aucun_droit(client):
    corps = client.post("/calcul/export", json={
        "pays": "KEN", "code_sh": "72042100", "valeur": 1_000, "devise": "KES"}).json()
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"


def test_tza_peaux_brutes_le_plus_eleve_des_deux(client):
    """« 80% FOB Value or USD 0.52 / Kg whichever is greater »."""
    gros = _ligne(_export(client, pays="TZA", code_sh="41012000", valeur=10_000, devise="USD", quantite=1_000),
                  "EXPORT")
    assert (gros["montant"], gros["composante_retenue"]) == (pytest.approx(8_000), "ad_valorem")
    petit = _ligne(_export(client, pays="TZA", code_sh="41012000", valeur=100, devise="USD", quantite=1_000),
                   "EXPORT")
    assert (petit["montant"], petit["composante_retenue"]) == (pytest.approx(520), "specifique")



def test_tza_wet_blue_d_ovins_couvert_par_la_regle():
    """Codex : 4105.10 (peaux d'ovins « in the wet state (including wet-blue) ») porte les 10 % ; la
    position manque à la collecte tarifaire TZA, d'où un test sur la règle elle-même."""
    sys.path.insert(0, os.path.join(os.path.dirname(BACKEND), "scripts"))
    from build_socle import droits_export_par_texte

    droit = droits_export_par_texte("TZA", {"41051000": {}})["41051000"][0]
    assert droit["taux"] == 10.0 and "wet-blue" in droit["note"]

def test_tza_placages_en_shillings(client):
    """Finance Act 2025, item 6 : 30 % ou TZS 150/kg, sans taux de change sur une valeur en TZS."""
    ligne = _ligne(_export(client, pays="TZA", code_sh="44081000", valeur=1_000_000, devise="TZS", quantite=1_000),
                   "EXPORT")
    assert ligne["montant"] == pytest.approx(300_000)


def test_tza_tourteaux_loi_de_finances_2026(client):
    """Finance Act 2026, item 8 : TZS 50/kg."""
    ligne = _ligne(_export(client, pays="TZA", code_sh="23061000", valeur=1_000_000, devise="TZS", quantite=1_000),
                   "EXPORT")
    assert ligne["montant"] == pytest.approx(50_000) and "2026" in ligne["note"]



def test_tza_sables_de_quartz_position_non_etablie(client):
    """« Quartz sands of Heading 25.06 » : ni le 25.05.10 (sables) ni la 25.06 (quartz, quartzite) ne
    répondent exactement au texte ; le feldspath, désigné par son code, est taxé."""
    for code in ("25051000", "25061000", "25062000"):
        ligne = _ligne(_export(client, pays="TZA", code_sh=code, valeur=1_000, devise="TZS", quantite=1), "EXPORT")
        assert ligne["montant"] is None and "25.05.10" in ligne["note"], code
    feldspath = _ligne(_export(client, pays="TZA", code_sh="25291000", valeur=1_000_000, devise="TZS",
                               quantite=1_000), "EXPORT")
    assert feldspath["montant"] == pytest.approx(200_000)

def test_tza_hors_annexe_aucun_droit(client):
    corps = client.post("/calcul/export", json={
        "pays": "TZA", "code_sh": "09011100", "valeur": 1_000, "devise": "TZS"}).json()
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"


def test_zaf_ferrailles_colonne_zlecaf(client):
    """Schedule 1 Part 6 A : colonne AfCFTA ; la note dit les autres destinations."""
    export = _export(client, pays="ZAF", code_sh="720421", valeur=100_000, devise="ZAR")
    ligne = _ligne(export, "EXPORT")
    assert (export["etat"], ligne["montant"]) == ("COMPLET", pytest.approx(15_000))
    assert "SADC" in ligne["note"]
    assert _ligne(_export(client, pays="ZAF", code_sh="74040010", valeur=100_000, devise="ZAR"),
                  "EXPORT")["montant"] == pytest.approx(10_000)

def test_cmr_taux_commun_selon_la_transformation(client):
    """LF 2018 (art. 2) : 2 % ; LF 2020 (art. 5) : produit fini exonéré ; sans réponse, à établir."""
    brut = _export(client, pays="CMR", code_sh="85171200", valeur=1_000_000, devise="XAF", produit_fini=False)
    assert (brut["etat"], _ligne(brut, "EXPORT")["montant"]) == ("COMPLET", pytest.approx(20_000))
    fini = _export(client, pays="CMR", code_sh="85171200", valeur=1_000_000, devise="XAF", produit_fini=True)
    assert _ligne(fini, "EXPORT")["montant"] == pytest.approx(0)
    sans = _ligne(_export(client, pays="CMR", code_sh="85171200", valeur=1_000_000, devise="XAF"), "EXPORT")
    assert sans["montant"] is None and sans["note"].startswith("À établir : Produit fini")


def test_cmr_produits_nommes_independants_de_la_reponse(client):
    """Riz 10 % (LF 2020), grumes 75 % (LF 2024), or 5 % (LF 2023), poivre exonéré (LF 2022)."""
    for code, montant in (("10063090", 100_000), ("44034939", 750_000), ("71081200", 50_000),
                          ("09041100", 0), ("18010011", 100_000), ("76011000", 20_000)):
        for fini in (True, False):
            export = _export(client, pays="CMR", code_sh=code, valeur=1_000_000, devise="XAF", produit_fini=fini)
            assert _ligne(export, "EXPORT")["montant"] == pytest.approx(montant), code


def test_cmr_notes_propres_sans_taux_propre(client):
    """Hévéa (abattement LF 2025) et « autres légumes » (Eru/Okok) : la note le dit, la réponse fixe le taux."""
    for code, mot in (("40012200", "Hévéa"), ("07099090", "Eru/Okok")):
        export = _export(client, pays="CMR", code_sh=code, valeur=1_000_000, devise="XAF", produit_fini=False)
        ligne = _ligne(export, "EXPORT")
        assert ligne["montant"] == pytest.approx(20_000) and mot in ligne["note"], code
    ordinaire = _ligne(_export(client, pays="CMR", code_sh="85171200", valeur=1_000_000, devise="XAF",
                               produit_fini=False), "EXPORT")
    assert "déforestation" not in ordinaire["note"]


def test_cmr_lf2026_positions_ambigues_a_etablir(client):
    for code in ("80011000", "74032100", "71039100", "25231000", "18010020"):
        ligne = _ligne(_export(client, pays="CMR", code_sh=code, valeur=1_000_000, devise="XAF", produit_fini=False),
                       "EXPORT")
        assert ligne["montant"] is None, code


def test_cog_taux_general_selon_la_transformation(client):
    """LFR 2021, point 42 : 2 % ; produit transformé d'origine congolaise exonéré ; sans réponse, à établir."""
    brut = _export(client, pays="COG", code_sh="85171200", valeur=1_000_000, devise="XAF", produit_fini=False,
                   produit_transforme=False)
    assert (brut["etat"], _ligne(brut, "EXPORT")["montant"]) == ("COMPLET", pytest.approx(20_000))
    transforme = _export(client, pays="COG", code_sh="85171200", valeur=1_000_000, devise="XAF", produit_fini=True)
    assert _ligne(transforme, "EXPORT")["montant"] == pytest.approx(0)
    sans = _ligne(_export(client, pays="COG", code_sh="85171200", valeur=1_000_000, devise="XAF"), "EXPORT")
    assert sans["montant"] is None and sans["note"].startswith("À établir : Produit transformé")


def test_cog_produits_nommes_independants_de_la_reponse(client):
    """Maïs et diamant brut 4 %, grumes d'Afrormosia 10 % et de Doussié 9 %, contreplaqués et panneaux 0,5 %, parquets et
    pétrole brut 0 %."""
    for code, montant in (("10059000", 40_000), ("71021000", 40_000), ("44034903", 100_000),
                          ("44034914", 90_000), ("44129400", 5_000), ("44101100", 5_000), ("44091000", 0), ("44151000", 0),
                          ("27090010", 0)):
        for transforme in (True, False):
            export = _export(client, pays="COG", code_sh=code, valeur=1_000_000, devise="XAF",
                             produit_fini=transforme)
            assert _ligne(export, "EXPORT")["montant"] == pytest.approx(montant), code


def test_cog_positions_ambigues_a_etablir(client):
    """Okoumé mêlé aux autres essences, sciages humides ou séchés, farines de poisson ou de crustacés, platine
    brut ou en poudre, plaquettes que le barème du bois ne nomme pas, menuiseries « autres » qui comprennent les lamellés collés."""
    for code in ("44034939", "44072901", "23012000", "71101100", "44012200", "44189000"):
        ligne = _ligne(_export(client, pays="COG", code_sh=code, valeur=1_000_000, devise="XAF", produit_fini=False),
                       "EXPORT")
        assert ligne["montant"] is None, code


def test_gab_bois_selon_le_degre_de_transformation(client):
    """LF 2026, art. 5 : placages 15 %, panneaux, contreplaqués, profilés et parquets 10 % (valeur mercuriale) ;
    menuiserie, ébénisterie, meubles en bois 3,5 % (valeur FOB) — pour un produit déclaré en bois."""
    for code, montant in (("44083900", 150_000), ("44091000", 100_000), ("44123100", 100_000), ("44119200", 100_000),
                          ("44187200", 100_000), ("44182000", 35_000), ("94013000", 35_000)):
        export = _export(client, pays="GAB", code_sh=code, valeur=1_000_000, devise="XAF", produit_en_bois=True)
        assert (export["etat"], _ligne(export, "EXPORT")["montant"]) == ("COMPLET", pytest.approx(montant)), code


def test_gab_bois_selon_la_matiere_declaree(client):
    """Chapitre 44, note 6 : « bois » y comprend le bambou et les autres matières ligneuses, que la LF ne taxe pas.
    Sans réponse, à établir ; produit qui n'est pas en bois, aucun droit. Les panneaux « De bois » (4410.1) et les
    meubles en bois du chapitre 94 (qui range à part le bambou) ne dépendent pas de la réponse."""
    for code in ("44083900", "44092100", "44119200", "44190000", "94013000"):
        sans = _ligne(_export(client, pays="GAB", code_sh=code, valeur=1_000_000, devise="XAF"), "EXPORT")
        assert sans["montant"] is None and "Produit en bois" in sans["note"], code
        non = _ligne(_export(client, pays="GAB", code_sh=code, valeur=1_000_000, devise="XAF", produit_en_bois=False),
                     "EXPORT")
        assert non["montant"] == pytest.approx(0), code
    for code, montant in (("44101100", 100_000), ("94036000", 35_000)):
        for reponse in (None, False, True):
            corps = {"pays": "GAB", "code_sh": code, "valeur": 1_000_000, "devise": "XAF"}
            if reponse is not None:
                corps["produit_en_bois"] = reponse
            assert _ligne(_export(client, **corps), "EXPORT")["montant"] == pytest.approx(montant), (code, reponse)


def test_gab_grumes_or_et_produits_non_nommes(client):
    """Grumes (exportation interdite), or (seuls les lingots sont nommés), sciages (bruts ou rabotés), bois non classé :
    à établir, même pour un produit déclaré en bois ; hors des produits nommés, aucun droit de sortie."""
    for code in ("44034914", "71081200", "44021000", "44072914"):
        ligne = _ligne(_export(client, pays="GAB", code_sh=code, valeur=1_000_000, devise="XAF", produit_en_bois=True),
                       "EXPORT")
        assert ligne["montant"] is None, code
    corps = client.post("/calcul/export", json={
        "pays": "GAB", "code_sh": "85171200", "valeur": 1000, "devise": "XAF"}).json()
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"


def test_cog_redevance_informatique_a_l_exportation(client):
    """LF 2026, point 25 : 2 % à l'exportation ; pétrole brut exonéré (LFR 2021, point 41) ; produit transformé
    (0,5 % en 2021, non repris en 2026) ou sans réponse : à établir. La première question ne porte que sur la
    transformation au Congo : après un « non », `produit_transforme` dit si le produit est brut."""
    brut = _export(client, pays="COG", code_sh="85171200", valeur=1_000_000, devise="XAF", produit_fini=False,
                   produit_transforme=False)
    assert (brut["etat"], _ligne(brut, "RI.EXP")["montant"]) == ("COMPLET", pytest.approx(20_000))
    ailleurs = _export(client, pays="COG", code_sh="85171200", valeur=1_000_000, devise="XAF", produit_fini=False,
                       produit_transforme=True)
    assert _ligne(ailleurs, "RI.EXP")["montant"] is None and "0,5 %" in _ligne(ailleurs, "RI.EXP")["note"]
    sans = _export(client, pays="COG", code_sh="85171200", valeur=1_000_000, devise="XAF", produit_fini=False)
    ligne = _ligne(sans, "RI.EXP")
    assert ligne["montant"] is None and "transformé hors du Congo" in ligne["note"]
    assert sans["etat"] != "COMPLET"
    petrole = _export(client, pays="COG", code_sh="27090010", valeur=1_000_000, devise="XAF", produit_fini=False)
    assert _ligne(petrole, "RI.EXP")["montant"] == pytest.approx(0)
    for reponse in (True, None):
        corps = {"pays": "COG", "code_sh": "85171200", "valeur": 1_000_000, "devise": "XAF"}
        if reponse is not None:
            corps["produit_fini"] = reponse
        ligne = _ligne(client.post("/calcul/export", json=corps).json()["export"], "RI.EXP")
        assert ligne["montant"] is None and "0,5 %" in ligne["note"], reponse


def test_cog_redevance_des_grumes_sur_la_valeur_en_douane(client):
    """Grumes : la valeur saisie est la valeur FOT du droit de sortie, la redevance est assise sur la valeur en
    douane : à établir, quelle que soit la réponse."""
    for reponse in (True, False):
        grume = _export(client, pays="COG", code_sh="44034914", valeur=1_000_000, devise="XAF", produit_fini=reponse,
                        produit_transforme=False)
        ligne = _ligne(grume, "RI.EXP")
        assert ligne["montant"] is None and "valeur FOT" in ligne["note"], reponse


def test_cog_caoutchouc_naturel_et_plan_de_resilience(client):
    """Latex et gommes naturelles : exsudats d'arbres que le texte ne nomme pas, à établir ; maïs 4 % et charbon de
    bois avec la note des arrêtés n° 26621 et 26622 (plan de résilience 2022-2023)."""
    latex = _ligne(_export(client, pays="COG", code_sh="40011000", valeur=1_000_000, devise="XAF",
                           produit_fini=False), "EXPORT")
    assert latex["montant"] is None and "exsudats" in latex["note"]
    mais = _ligne(_export(client, pays="COG", code_sh="10059000", valeur=1_000_000, devise="XAF", produit_fini=False),
                  "EXPORT")
    assert mais["montant"] == pytest.approx(40_000) and "26622" in mais["note"]
    charbon = _ligne(_export(client, pays="COG", code_sh="44021000", valeur=1_000_000, devise="XAF",
                             produit_fini=False), "EXPORT")
    assert charbon["montant"] is None and "26622" in charbon["note"]


def test_egy_droit_par_tonne_en_livres(client):
    """Circulaires de la douane : ferrailles inox 9 000, zinc 10 000 (décret 273/2026), talc concassé 1 800."""
    for code, montant in (("7204210000", 90_000), ("7903900000", 100_000), ("2526200030", 18_000)):
        export = _export(client, pays="EGY", code_sh=code, valeur=1_000_000, devise="EGP", quantite=10)
        ligne = _ligne(export, "EXPORT")
        assert (export["etat"], ligne["montant"]) == ("COMPLET", pytest.approx(montant)), code
    assert "zones franches" in ligne["note"]


def test_egy_lignes_exclues_par_le_decret(client):
    """Paille de riz, son de riz, rafles de maïs, poudres de caoutchouc : hors du droit."""
    for code in ("1213000010", "2302400010", "2308000010", "4004000090"):
        corps = client.post("/calcul/export", json={
            "pays": "EGY", "code_sh": code, "valeur": 1000, "devise": "EGP"}).json()
        assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE", code


def test_egy_luzerne_en_dollars_et_batteries_sans_exemption(client):
    corps = client.post("/calcul/export", json={
        "pays": "EGY", "code_sh": "1214100000", "valeur": 100_000, "devise": "EGP", "quantite": 2}).json()
    assert corps["change_requis"] == [{"devise_droit": "USD", "devise_valeur": "EGP"}]
    batteries = _ligne(_export(client, pays="EGY", code_sh="8507901000", valeur=1, devise="EGP", quantite=1),
                       "EXPORT")
    assert batteries["montant"] == pytest.approx(3000) and "aussi vers les zones franches" in batteries["note"]


def test_egy_lignes_mixtes_et_sable_blanc_a_etablir(client):
    for code in ("6310100010", "2515110090", "2505100010", "4004000000", "2526200050", "3915900000"):
        ligne = _ligne(_export(client, pays="EGY", code_sh=code, valeur=1000, devise="EGP", quantite=1), "EXPORT")
        assert ligne["montant"] is None, code


def test_cod_minerai_selon_le_titulaire_minier(client):
    """Tarif à l'exportation : concentré de cobalt 10 % ; Code minier, art. 234 : le titulaire en est exonéré."""
    tiers = _export(client, pays="COD", code_sh="26050000", valeur=1_000_000, devise="CDF", titulaire_minier=False)
    assert (tiers["etat"], _ligne(tiers, "EXPORT")["montant"]) == ("COMPLET", pytest.approx(100_000))
    titulaire = _export(client, pays="COD", code_sh="26050000", valeur=1_000_000, devise="CDF", titulaire_minier=True)
    assert _ligne(titulaire, "EXPORT")["montant"] == pytest.approx(0)
    sans = _ligne(_export(client, pays="COD", code_sh="26050000", valeur=1_000_000, devise="CDF"), "EXPORT")
    assert sans["montant"] is None and sans["note"].startswith("À établir : Exportation par le titulaire")


def test_cod_produits_non_miniers_sans_question(client):
    """Grumes tropicales 10 %, électricité et pétrole brut 5 %, café vert exempt (LF 2026, annexe XVI) : la réponse sur le
    titulaire minier n'y change rien."""
    for code, montant in (("44034900", 100_000), ("44034200", 100_000), ("27160000", 50_000), ("27090000", 50_000),
                          ("09011100", 0)):
        for titulaire in (None, True):
            corps = {"pays": "COD", "code_sh": code, "valeur": 1_000_000, "devise": "CDF"}
            if titulaire is not None:
                corps["titulaire_minier"] = titulaire
            export = client.post("/calcul/export", json=corps).json()["export"]
            assert _ligne(export, "EXPORT")["montant"] == pytest.approx(montant), code


def test_cod_liste_consolidee(client):
    """Tarif tel que modifié (liste consolidée, annexe XVI des projets de LF 2025 et 2026) : titane 10 %, hydroxyde de
    cobalt 10 %, déchets de cuivre 5 %, mattes de cuivre 5 %, zinc brut 5 %, étain brut 10 %, chrome brut 5 %,
    ouvrages en chrome 10 % ; LF 2026, annexe XVI : cuivre blister et oxyde de zinc 5 %."""
    for code, montant in (("26140000", 100_000), ("28220000", 100_000), ("74040000", 50_000), ("74010000", 50_000),
                          ("79011100", 50_000), ("80011000", 100_000), ("81122100", 50_000), ("81122900", 100_000),
                          ("72241000", 100_000), ("74032100", 100_000), ("74020000", 50_000), ("28170010", 50_000)):
        export = _export(client, pays="COD", code_sh=code, valeur=1_000_000, devise="CDF", titulaire_minier=False)
        assert _ligne(export, "EXPORT")["montant"] == pytest.approx(montant), code


def test_cod_cafe_decafeine_hors_annexe(client):
    """L'annexe XVI ne vise que le café vert non décaféiné : le décaféiné n'a pas de droit de sortie publié."""
    corps = client.post("/calcul/export", json={"pays": "COD", "code_sh": "09011200", "valeur": 1000,
                                                "devise": "CDF"}).json()
    assert corps["export"]["etat"] == "AUCUN_DROIT_PUBLIE"


def test_cod_positions_a_etablir(client):
    """Or et diamants (artisanal 0,5 %, industriel 3 %), sciages selon l'épaisseur (exempts jusqu'à 150 mm), eau."""
    for code in ("71081200", "71081100", "44072900", "22019000"):
        ligne = _ligne(_export(client, pays="COD", code_sh=code, valeur=1_000_000, devise="CDF",
                               titulaire_minier=False), "EXPORT")
        assert ligne["montant"] is None, code
    or_brut = _ligne(_export(client, pays="COD", code_sh="71081200", valeur=1_000_000, devise="CDF"), "EXPORT")
    assert "0,5 %" in or_brut["note"] and "24/011" in or_brut["note"] and "25/060" in or_brut["note"]


def test_cod_or_et_diamants_exoneres_pour_le_titulaire_minier(client):
    """Taux inconnu (or et diamants selon l'exploitation, positions ambiguës), mais le titulaire minier est exonéré ;
    la réserve sur l'art. 234 (projet de LF 2025) est dite."""
    for code in ("71081200", "71022100", "71023100", "74020000", "28170010", "26140000", "81082000"):
        export = _export(client, pays="COD", code_sh=code, valeur=1_000_000, devise="CDF", titulaire_minier=True)
        ligne = _ligne(export, "EXPORT")
        assert ligne["montant"] == 0 and "24/011" in ligne["note"], code


def test_pays_sans_droit_export_au_socle(client):
    reponse = client.post("/calcul/export", json={"pays": "UGA", "code_sh": "09011100", "valeur": 1000})
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
