"""
Invariants du socle de calcul — chantier L1.

Ce que ces tests protègent n'est pas la forme du fichier, c'est la doctrine :
aucun taux fabriqué, aucune assiette supposée, aucune colonne préférentielle
versée dans la cascade NPF. Un socle qui viole l'un de ces trois points rend un
montant faux qui a l'air juste — le défaut le plus coûteux du calculateur.
"""

import importlib.util
import json
import os
import shutil

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "scripts", "build_socle.py")
CRAWL = os.path.join(REPO, "backend", "data", "crawled")


def _module():
    spec = importlib.util.spec_from_file_location("build_socle", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bs = _module()


# ── Lecture des taux : ne jamais fabriquer ────────────────────────────────────
@pytest.mark.parametrize(
    "valeur,attendu",
    [
        (5, 5.0),
        (0, 0.0),
        ("12,5 %", 12.5),
        ("free", 0.0),
        ("exonéré", 0.0),
        (None, None),
        ("", None),
        ("sur devis", None),
        (True, None),
    ],
)
def test_un_taux_illisible_reste_indisponible(valeur, attendu):
    assert bs.lire_taux(valeur) == attendu


def test_un_taux_absent_ne_devient_jamais_zero():
    """`or 0` était la source de vingt fabrications dans l'ancien service."""
    droits = bs.droits_depuis_liste([{"code": "DD", "rate": None}], "src")
    assert droits[0]["taux"] is None


# ── Codes : le sigle officiel prime sur la forme de la clé ────────────────────
@pytest.mark.parametrize(
    "code,libelle,attendu",
    [
        ("D.D", "", "DD"),
        ("GENERAL", "General Customs Duty", "DD"),
        ("Droit d'Importation (DI)", "", "DD"),
        ("Taxe Parafiscale à l'Importation (TPI)", "", "TPI"),
        ("Taxe sur la Valeur Ajoutée (TVA)", "", "TVA"),
        ("IVA", "Imposto sobre o Valor Acrescentado", "TVA"),
        ("", "Value Added Tax (VAT)", "TVA"),
        ("", "Import Declaration Fee (IDF)", "IDF"),
        ("GETFL", "", "GETFUND"),
        ("RPD/IMPOR", "", "RPD"),
    ],
)
def test_code_canonique(code, libelle, attendu):
    assert bs.code_canonique(code, libelle) == attendu


def test_d2r_n_est_pas_une_colonne_zlecaf():
    """`D2R` est la colonne COMESA éthiopienne. La confondre avec la ZLECAf
    ferait payer un taux COMESA à une origine qui n'y a pas droit."""
    assert bs.PREFERENTIELS["D2R"] == "COMESA"
    assert bs.PREFERENTIELS["AFCFTA"] == "AFCFTA"
    assert "GENERAL" not in bs.PREFERENTIELS  # côté SACU, c'est le droit NPF


# ── Assiettes : traduire, ou dire qu'on ne sait pas ───────────────────────────
@pytest.mark.parametrize(
    "brut,assiette",
    [
        ("CIF", "CIF"),
        ("CIF + DD", "CIF+DD"),
        ("CIF + DD + RS + PCS", "CIF+DD+RS+PCS"),
        ("CIF+Duty+Fees", "CIF+TOUS_SAUF_TVA"),
        ("VALEUR DOUANE DINARS", "CIF"),
        ("VAL.DOU(D)+R(DT) GR.0", "CIF+DD"),
        ("SOMME D.T (G=0.1.2.3.4.", "SOMME(TOUS_SAUF_SOI)"),
        ("QCS", "xQTE"),
    ],
)
def test_assiette_traduite(brut, assiette):
    assert bs.assiette_depuis_source(brut)[0] == assiette


@pytest.mark.parametrize("brut", ["variable", "PN(KG)/100 EXCES", "charabia"])
def test_une_assiette_non_traduite_reste_indisponible_et_motivee(brut):
    assiette, _, motif = bs.assiette_depuis_source(brut)
    assert assiette is None
    assert motif, "une assiette écartée doit dire pourquoi"


def test_le_plafond_cemac_est_conserve():
    assiette, plafond, _ = bs.assiette_depuis_source("CIF (plafond 15 000 XAF)")
    assert assiette == "CIF"
    assert plafond == {"montant": 15000.0, "devise": "XAF"}


def test_un_prelevement_non_classe_est_liquide_avant_la_tva():
    """Sinon il sortirait d'une assiette « CIF + tous les droits sauf TVA »."""
    ordre = bs.ORDRE_FAMILLES
    assert ordre.index("autre") < ordre.index("tva") < ordre.index("post_tva")


# ── Lecture des six schémas ───────────────────────────────────────────────────
def test_schema_taxes_detail_avec_assiette():
    donnees = {
        "source": "douanes.ci",
        "positions": [
            {
                "code_clean": "7612900000",
                "designation": "Réservoirs en aluminium",
                "taxes": {"DD": 20.0, "TVA": 18.0},
                "taxes_detail": [
                    {"tax_code": "DD", "rate": 20.0, "base": "CIF"},
                    {"tax_code": "TVA", "rate": 18.0, "base": "CIF + DD"},
                ],
            }
        ],
    }
    lignes = list(bs.lignes_du_fichier(donnees))
    assert len(lignes) == 1
    code, _, _, droits, _ = lignes[0]
    assert code == "7612900000"
    # taxes_detail porte l'assiette : il prime sur le dict `taxes` qui ne l'a pas
    assert [(d["code"], d["assiette"]) for d in droits] == [
        ("DD", "CIF"),
        ("TVA", "CIF+DD"),
    ]


def test_schema_tariff_lines_le_droit_de_l_enfant_prime():
    """Ghana et Somalie : les codes nationaux étaient perdus à la normalisation."""
    donnees = {
        "tariff_lines": [
            {
                "hs6": "010121",
                "description_fr": "Chevaux",
                "dd_rate": 5.0,
                "taxes_detail": [
                    {"tax": "DD", "rate": 5.0},
                    {"tax": "VAT", "rate": 15.0},
                ],
                "sub_positions": [{"code": "0101210000", "dd": 10.0}],
            }
        ]
    }
    lignes = {c: d for c, _, _, d, _ in bs.lignes_du_fichier(donnees)}
    assert "010121" in lignes and "0101210000" in lignes
    enfant = {d["code"]: d["taux"] for d in lignes["0101210000"]}
    assert enfant["DD"] == 10.0, "le droit national prime sur celui du parent"
    assert enfant["TVA"] == 15.0, "les autres prélèvements du parent restent dus"


def test_schema_tunisien_droit_specifique_sans_taux():
    donnees = {
        "sub_positions": [
            {
                "hs_code": "01012100015",
                "designation": "Chevaux de course",
                "taxes_import": [
                    {
                        "code": "D.S.V.",
                        "name": "DROIT SANIT.VETERINA",
                        "raw_value": "0.1 dinars",
                        "rate_pct": None,
                        "specific_value": "0.1 dinars",
                        "assiette": "QCS",
                    },
                ],
            }
        ]
    }
    ((_, _, _, droits, _),) = bs.lignes_du_fichier(donnees)
    assert droits[0]["taux"] is None, "un droit spécifique n'a pas de taux ad valorem"
    assert droits[0]["specifique"] == "0.1 dinars"
    assert droits[0]["assiette"] == "xQTE"


# ── Le socle construit ────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def socle_civ(tmp_path_factory):
    chemin = os.path.join(CRAWL, "CIV_tariffs.json")
    if not os.path.exists(chemin):
        pytest.skip("crawl CIV absent de ce clone")
    assiettes = bs.charger_assiettes_pays()
    socle, _ = bs.construire_pays("CIV", chemin, "crawl", assiettes)
    return socle


def test_le_socle_porte_la_provenance_de_sa_source(socle_civ):
    src = socle_civ["source"]
    assert len(src["sha256"]) == 64
    assert src["fichier"].startswith("backend/data/crawled/")
    assert src["origine"] == "crawl"


def test_aucune_colonne_preferentielle_dans_la_cascade():
    """Une préférence décrit un autre régime : jamais un prélèvement dû."""
    chemin = os.path.join(CRAWL, "ZAF_tariffs.json")
    if not os.path.exists(chemin):
        pytest.skip("crawl ZAF absent de ce clone")
    socle, _ = bs.construire_pays("ZAF", chemin, "crawl", bs.charger_assiettes_pays())
    position = socle["positions"]["010121"]
    codes = {d["code"] for d in position["droits"]}
    assert codes == {"DD"}
    assert set(position["preferentiels"]) >= {"AFCFTA", "SADC", "EU_UK"}


def test_un_pays_sans_tva_est_marque_partiel():
    """Le crawl SARS ne porte aucune TVA : le total est incomplet, et le dit."""
    chemin = os.path.join(CRAWL, "ZAF_tariffs.json")
    if not os.path.exists(chemin):
        pytest.skip("crawl ZAF absent de ce clone")
    socle, _ = bs.construire_pays("ZAF", chemin, "crawl", bs.charger_assiettes_pays())
    assert socle["couverture"]["tva"] is False
    assert socle["couverture"]["etat"] == "PARTIEL"


def test_un_pays_sans_position_est_declare_vide_jamais_estime():
    chemin = os.path.join(CRAWL, "DJI_tariffs.json")
    if not os.path.exists(chemin):
        pytest.skip("crawl DJI absent de ce clone")
    socle, c = bs.construire_pays("DJI", chemin, "crawl", bs.charger_assiettes_pays())
    assert c["positions"] == 0
    assert socle["couverture"]["etat"] == "VIDE"
    assert socle["positions"] == {}


def test_une_couverture_complete_exige_des_droits_liquidables():
    """Annoncer COMPLET sur la seule présence des familles reproduirait les
    « 100 % de couverture » déduits de listes non vides que l'audit
    reprochait au module : l'Angola porte un droit et une TVA, mais aucune
    assiette pour la seconde."""
    chemin = os.path.join(CRAWL, "AGO_tariffs.json")
    if not os.path.exists(chemin):
        pytest.skip("crawl AGO absent de ce clone")
    socle, c = bs.construire_pays("AGO", chemin, "crawl", bs.charger_assiettes_pays())
    couverture = socle["couverture"]
    assert couverture["droit_de_douane"] and couverture["tva"]
    assert couverture["etat"] == "PARTIEL"
    assert "non liquidables" in couverture["motif"]
    assert c["droits_liquidables"] < c["droits"]


def test_un_droit_preferentiel_specifique_est_conserve():
    """181 lignes sud-africaines opposent « 8c/kg » en NPF à « 3,2c/kg » sous
    ZLECAf. Ne garder que le taux les priverait de leur droit préférentiel."""
    chemin = os.path.join(CRAWL, "ZAF_tariffs.json")
    if not os.path.exists(chemin):
        pytest.skip("crawl ZAF absent de ce clone")
    socle, c = bs.construire_pays("ZAF", chemin, "crawl", bs.charger_assiettes_pays())
    afcfta = socle["positions"]["020830"]["preferentiels"]["AFCFTA"]
    assert afcfta["taux"] is None
    assert afcfta["specifique"]["montant"] == 0.032  # 3,2 centimes, pas 3,2 %
    assert afcfta["specifique"]["unite_quantite"] == "kg"
    assert c["preferentiels_specifiques"] > 0


def test_une_construction_partielle_n_ampute_pas_le_manifeste(tmp_path, monkeypatch):
    """`build_socle.py CIV` laisse les autres pays sur disque : les retirer de
    l'index les rendrait introuvables alors qu'ils sont servables."""
    manifeste = os.path.join(REPO, "backend", "socle", "MANIFESTE.json")
    if not os.path.exists(manifeste):
        pytest.skip("socle absent : python3 scripts/build_socle.py")
    with open(manifeste, encoding="utf-8") as f:
        avant = json.load(f)
    if "CIV" not in avant["pays"] or len(avant["pays"]) < 2:
        pytest.skip("manifeste trop réduit pour ce test")
    sauvegarde = tmp_path / "MANIFESTE.json"
    shutil.copy(manifeste, sauvegarde)
    try:
        bs.main(["build_socle.py", "CIV"])
        with open(manifeste, encoding="utf-8") as f:
            apres = json.load(f)
        assert set(apres["pays"]) == set(avant["pays"])
        assert apres["totaux"]["positions"] == avant["totaux"]["positions"]
    finally:
        shutil.copy(sauvegarde, manifeste)


def test_la_table_d_assiettes_conserve_ses_references_legales():
    with open(os.path.join(REPO, "backend", "socle", "assiettes_pays.json"), encoding="utf-8") as f:
        table = json.load(f)
    pays = table["pays"]
    assert len(pays) >= 37
    # Les dix assiettes de TVA établies sur texte primaire citent leur texte.
    etablies = [
        (iso, t)
        for iso, v in pays.items()
        for code, t in v["taxes"].items()
        if t["origine_assiette"] == "texte_primaire"
    ]
    assert len(etablies) == 10
    for iso, t in etablies:
        assert t["assiette"] == "CIF+TOUS_SAUF_TVA"
        assert t.get("texte"), f"{iso} : une assiette établie doit citer son texte"
