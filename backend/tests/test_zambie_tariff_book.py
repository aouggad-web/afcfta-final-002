"""Zambie — la cascade des trois prélèvements, et trois lettres à la place d'un taux.

Le socle servait 5 388 moyennes SH6 de la Banque mondiale, SANS AUCUNE
désignation. Le Customs and Excise Tariff de ZRA — édition janvier 2026,
682 pages, qui reproduit la PREMIÈRE ANNEXE (section 72) de la Customs and
Excise Act — en porte 6 751 à huit chiffres, avec trois colonnes de prélèvements.

CE QUE CES TESTS TIENNENT.

1. LES TROIS ASSIETTES SONT CELLES QUE LA LOI ÉNONCE, section par section :
   DD sur CIF (Cinquième annexe cl. 2 et 3(1)(a)(vii)-(viii)), accise sur CIF+DD
   (s.88), TVA sur CIF+DD+EXC (VAT Act s.10(3)).

2. LA COLONNE DE TVA NE PORTE PAS UN TAUX MAIS UNE LETTRE, et le document ne
   publie aucune légende : S, E, Z tiennent leur sens du Value Added Tax Act.
   « E » et « Z » sont des ZÉROS PUBLIÉS, pas des lacunes.

3. LE TAUX STANDARD N'EST PAS CELUI DU TEXTE CONSOLIDÉ. La s.9(3) porte 17,5 %
   « unless the Minister, by statutory order, determines a lower rate ». Servir
   17,5 % surfacturerait chaque importation zambienne d'un dixième. Un test
   l'interdit nommément.

4. UN DROIT ALTERNATIF SE LIQUIDE, parce que la règle 2(b) des Additional
   Zambian Rules l'énonce — « the rate which yields the greater amount of duty
   shall apply » — à la différence du tarif sud-africain.

5. L'ASTÉRISQUE N'EST PAS UN TAUX MAIS UN RENVOI, et la note porte le droit.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

SOCLE = RACINE / "socle" / "ZMB.json"
CRAWL = RACINE / "data" / "crawled" / "ZMB_tariffs.json"

pytestmark = pytest.mark.skipif(
    not SOCLE.exists() or not CRAWL.exists(),
    reason="socle non construit dans cet environnement",
)


@pytest.fixture(scope="module")
def socle():
    return json.loads(SOCLE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def crawl():
    return json.loads(CRAWL.read_text(encoding="utf-8"))


def _droits(position, code):
    return [d for d in position.get("droits") or [] if d.get("code") == code]


def test_le_socle_ne_sert_plus_une_moyenne_agregee(crawl):
    assert "WITS" not in json.dumps(crawl.get("source"), ensure_ascii=False).upper()
    assert crawl["source_quality"] == "crawled_authentic"
    assert "janvier 2026" in crawl["source"]
    assert crawl.get("source_sha256")
    # Le tarif est servi depuis une URL citable, non depuis un depot prive.
    assert crawl["source_url"].startswith("https://www.zra.org.zm/")


def test_les_positions_sont_nationales_et_portent_leur_libelle_anglais(socle):
    positions = socle["positions"]
    assert len(positions) > 6700
    assert all(len(code) == 8 for code in positions)


@pytest.mark.parametrize(
    "code_taxe,assiette,article",
    [
        ("DD", "CIF", "Cinquieme annexe cl. 2 et 3(1)(a)(vii)-(viii)"),
        ("EXC", "CIF+DD", "s.88"),
        ("TVA", "CIF+DD+EXC", "VAT Act s.10(3)"),
    ],
)
def test_chaque_assiette_est_celle_que_la_loi_enonce(socle, code_taxe, assiette, article):
    trouves = [
        d for p in socle["positions"].values() for d in _droits(p, code_taxe)
        if d.get("taux") is not None or d.get("specifique")
    ]
    assert trouves, f"{code_taxe} absent du socle"
    assiettes = {d.get("assiette") for d in trouves}
    # « xQTE » est la forme que prend un droit SPECIFIQUE : il se liquide a la
    # quantite, jamais sur la valeur.
    assert assiettes <= {assiette, "xQTE"}, f"{code_taxe} ({article}) : {assiettes}"
    sur_valeur = [d for d in trouves if d.get("assiette") == assiette]
    assert sur_valeur
    assert {d.get("assiette_origine") for d in sur_valeur} == {"source"}


def test_la_cascade_se_liquide_dans_l_ordre_des_trois_textes(socle):
    """Vérifié sur les cigarettes électroniques, où l'accise est de 145 % :
    chaque assiette inclut ce que la précédente a produit."""
    from services.calcul import calculer

    npf = calculer(socle["positions"]["85434000"], 10000.0)["npf"]
    lignes = {x["code"]: x for x in npf["lignes"]}
    assert lignes["DD"]["base"] == 10000.0
    # s.88 : « the customs value […] AND ANY CUSTOMS DUTY PAYABLE ».
    assert lignes["EXC"]["base"] == 10000.0 + lignes["DD"]["montant"]
    # VAT Act s.10(3) : « any duty or other impost payable otherwise than under
    # this Act » — le droit de douane ET l'accise.
    assert lignes["TVA"]["base"] == (
        10000.0 + lignes["DD"]["montant"] + lignes["EXC"]["montant"]
    )
    assert npf["etat"] == "COMPLET"


def test_une_accise_specifique_se_liquide_a_la_quantite_et_entre_dans_la_tva(socle):
    """La bière en vrac porte « K0.25/l » : une accise au litre, pas un
    pourcentage. Elle se liquide sur la quantité — et son MONTANT entre tout de
    même dans l'assiette de la TVA, que la s.10(3) définit par les montants dus."""
    from services.calcul import calculer

    npf = calculer(socle["positions"]["22030010"], 10000.0, quantite=1000.0)["npf"]
    lignes = {x["code"]: x for x in npf["lignes"]}
    assert lignes["EXC"]["montant"] == pytest.approx(250.0)
    assert lignes["DD"]["montant"] == pytest.approx(2500.0)
    assert lignes["TVA"]["base"] == pytest.approx(12750.0)
    assert npf["etat"] == "COMPLET"


def test_un_droit_alternatif_se_liquide_parce_que_la_regle_est_enoncee(socle):
    """Additional Zambian Rules, règle 2(b) : « the rate which yields the greater
    amount of duty shall apply ». C'est ce qui manque au tarif SARS."""
    from services.calcul import calculer

    position = socle["positions"]["22030090"]
    droit = _droits(position, "DD")[0]
    assert droit["compose"] is True
    assert droit["regle_composee"] == "LE_PLUS_ELEVE"
    assert isinstance(droit["specifique"], dict)
    assert droit["specifique"]["montant"] == pytest.approx(0.8)

    faible = calculer(position, 10000.0, quantite=1000.0)["npf"]["lignes"][0]
    assert faible["composante_retenue"] == "ad_valorem"
    assert faible["montant"] == pytest.approx(2500.0)

    forte = calculer(position, 10000.0, quantite=50000.0)["npf"]["lignes"][0]
    assert forte["composante_retenue"] == "specifique"
    assert forte["montant"] == pytest.approx(40000.0)


def test_tous_les_droits_composes_portent_la_regle_et_un_specifique_decompose(socle):
    composes = [
        d for p in socle["positions"].values() for d in _droits(p, "DD")
        if d.get("compose")
    ]
    assert len(composes) > 100, f"{len(composes)} droits composes seulement"
    assert all(d.get("regle_composee") == "LE_PLUS_ELEVE" for d in composes)
    assert all(isinstance(d.get("specifique"), dict) for d in composes)
    assert all(d["specifique"].get("montant") is not None for d in composes)
    # Le verbatim de la note reste consultable : c'est lui qui porte la regle.
    assert all("whichever" in (d.get("expression_brute") or "").lower()
               or "which ever" in (d.get("expression_brute") or "").lower()
               for d in composes)


def test_l_asterisque_est_un_renvoi_et_la_note_porte_le_droit(crawl):
    """« * » dans la colonne des droits n'est pas un taux : la note de bas de page
    énonce le droit en entier. La note vit parfois sur la page SUIVANTE."""
    composes = [
        t for p in crawl["sub_positions"] for t in p["taxes"]
        if t["code"] == "DD" and t.get("compound")
    ]
    assert composes
    assert all(t["raw_value"].startswith("*") for t in composes)
    assert all(t["rate_pct"] is not None and t["specific_value"] for t in composes)
    assert all(t["specific_currency"] == "ZMW" for t in composes)


def test_le_taux_de_tva_n_est_pas_celui_du_texte_consolide(socle):
    """La s.9(3) du Value Added Tax Act porte 17,5 %, soumis a un ordre du
    ministre. Le servir surfacturerait chaque importation zambienne d'un
    dixieme. Ce test est la pour qu'on ne le reintroduise pas."""
    taux = {
        d.get("taux") for p in socle["positions"].values() for d in _droits(p, "TVA")
    }
    assert 17.5 not in taux, "le taux perime du texte consolide est servi"
    assert taux <= {0.0, 16.0}, taux


def test_les_lettres_E_et_Z_sont_des_zeros_publies_et_non_des_lacunes(crawl):
    """Le tarif ne publie aucune legende : « E » renvoie a la premiere annexe du
    Value Added Tax Act (exoneration), « Z » a la seconde (taux zero)."""
    lignes = [t for p in crawl["sub_positions"] for t in p["taxes"] if t["code"] == "TVA"]
    par_lettre = {}
    for t in lignes:
        par_lettre.setdefault(t["raw_value"], []).append(t)
    assert set(par_lettre) == {"S", "E", "Z"}
    assert all(t["rate_pct"] == 0.0 for t in par_lettre["E"])
    assert all(t["rate_pct"] == 0.0 for t in par_lettre["Z"])
    assert all(t["rate_pct"] == 16.0 for t in par_lettre["S"])
    assert all("First Schedule" in t["note"] for t in par_lettre["E"])
    assert all("Second Schedule" in t["note"] for t in par_lettre["Z"])
    assert len(par_lettre["E"]) > 500 and len(par_lettre["Z"]) >= 10


def test_une_exoneration_de_tva_se_sert_a_zero_et_non_en_indisponible(socle):
    """Un cheval reproducteur est exonere de TVA. La ligne doit se lire
    « TVA 0 % » — une franchise — et non « assiette indisponible », qui ferait
    croire a une lacune de collecte."""
    from services.calcul import calculer

    npf = calculer(socle["positions"]["01012100"], 10000.0)["npf"]
    lignes = {x["code"]: x for x in npf["lignes"]}
    assert lignes["TVA"]["statut"] == "CALCULE"
    assert lignes["TVA"]["montant"] == 0.0
    assert lignes["TVA"]["base"] is not None
    assert npf["etat"] == "COMPLET"


def test_un_tiret_dans_la_colonne_d_accise_est_un_zero_publie(crawl):
    """« - » dit que la position n'est PAS soumise a l'accise. C'est une donnee :
    la traiter comme une absence ferait disparaitre la ligne."""
    tirets = [
        t for p in crawl["sub_positions"] for t in p["taxes"]
        if t["code"] == "EXC" and t["raw_value"] == "-"
    ]
    assert len(tirets) > 5000, f"{len(tirets)} seulement"
    assert all(t["rate_pct"] == 0.0 for t in tirets)
    assert all("zero publie" in (t["note"] or "") for t in tirets)


def test_une_cellule_non_interpretee_est_declaree_jamais_approchee(crawl):
    """Un droit que la collecte n'a pas su lire est servi SANS TAUX, avec son
    motif — jamais a zero, jamais approche."""
    declarees = [
        p for p in crawl["sub_positions"]
        if any(g.startswith("DD_") or g == "PAGE_NON_CALIBREE" for g in p["source_gaps"])
    ]
    assert declarees
    for p in declarees:
        dd = next(t for t in p["taxes"] if t["code"] == "DD")
        assert dd["rate_pct"] is None or dd.get("specific_value")
        assert dd.get("note")


def test_aucun_droit_ne_porte_un_taux_sans_assiette(socle):
    """L'invariant du socle, verifie sur la Zambie : un taux sans assiette ne se
    liquide pas, et un droit qui en porte un doit donc porter l'autre."""
    orphelins = [
        (code, d["code"]) for code, p in socle["positions"].items()
        for d in p.get("droits") or []
        if d.get("taux") is not None and not d.get("assiette")
    ]
    assert not orphelins, orphelins[:10]


def test_la_fiche_de_provenance_existe_et_est_verifiee():
    fiche = (
        RACINE / "data" / "legal_refs" / "zlecaf_application"
        / "ZMB_cascade_et_lettres_TVA_2026-09-18.json"
    )
    assert fiche.exists()
    contenu = json.loads(fiche.read_text(encoding="utf-8"))
    assert contenu["etabli"] is True
    regle = contenu["regle"]
    assert "88" in regle["assiette_de_l_accise_a_l_importation"]["article"]
    assert "greater amount of duty" in (
        regle["droit_alternatif_la_regle_est_enoncee"]["verbatim"]
    )
    # Le niveau de preuve doit DIRE que le taux de TVA n'est pas primaire.
    assert "SECONDAIRE" in contenu["evidence_level"]
    sources = RACINE / "data" / "legal_refs" / "zlecaf_application" / "sources"
    for nom in (
        "ZMB_customs_excise_act_annexe5_s88_regle2.texte-extrait.txt",
        "ZMB_vat_act_s9_s10_definitions.texte-extrait.txt",
        "ZMB_zra_vat_guide_taux_standard.texte-extrait.txt",
    ):
        assert (sources / nom).exists(), nom
