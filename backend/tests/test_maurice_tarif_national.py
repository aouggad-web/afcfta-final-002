"""Maurice — le socle sert le tarif national MRA, et ce qu'il n'établit pas se dit.

Le socle servait 5 619 positions SH6 issues d'une moyenne WITS/UNCTAD-TRAINS,
SANS AUCUNE désignation. Le tarif national (Customs Tariff Schedules, HS 2022,
807 pages, mra.mu) en porte 6 941 à huit chiffres, avec leur libellé, leur unité
statistique, quinze colonnes de taux et l'organisme délivrant le document exigé.

Ces tests tiennent les pièges qui ont été relevés en lisant le document, et les
deux assiettes établies sur les lois publiées par la même autorité.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

SOCLE = RACINE / "socle" / "MUS.json"
CRAWL = RACINE / "data" / "crawled" / "MUS_tariffs.json"

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


def test_le_socle_ne_sert_plus_une_moyenne_sh6(crawl):
    """Une moyenne agrégée par un tiers n'est pas un tarif national."""
    assert "WITS" not in json.dumps(crawl.get("source"), ensure_ascii=False).upper()
    assert crawl["source_quality"] == "crawled_authentic"
    assert crawl["source_url"].startswith("https://www.mra.mu/")


def test_les_positions_sont_nationales_et_portent_toutes_un_libelle(socle):
    """Le SH6 ne distingue pas ce que le tarif distingue."""
    positions = socle["positions"]
    assert len(positions) > 6000, "le tarif national porte plus de 6 000 positions"
    assert all(len(code) == 8 for code in positions), "codes nationaux à huit chiffres"
    sans_libelle = [
        code
        for code, p in positions.items()
        if not (p.get("designation") or {}).get("en", "").strip()
    ]
    assert not sans_libelle, f"{len(sans_libelle)} positions sans désignation"


def test_le_code_national_survit_a_la_construction_du_socle(socle, crawl):
    """`national_code` doit primer sur `hs6`, sinon les sous-positions
    entrent en collision et le socle en sert moins qu'il n'en a lu."""
    assert len(socle["positions"]) == len(crawl["sub_positions"])


def test_l_assiette_du_droit_vient_de_la_loi_et_non_d_un_profil(socle):
    """Customs Act 1988, s.18(1) et s.18A : valeur transactionnelle + fret +
    assurance, c'est-à-dire le CIF."""
    droits = [
        d
        for p in socle["positions"].values()
        for d in p.get("droits") or []
        if d.get("code") == "DD"
    ]
    assert droits
    assert all(d.get("assiette") == "CIF" for d in droits)
    origines = {d.get("assiette_origine") for d in droits}
    assert "profil_code" not in origines, "l'assiette du droit ne vient pas d'un profil"


def test_l_accise_entre_dans_l_assiette_de_la_tva(socle):
    """VAT Act 1998, s.13 : valeur en douane + droit de douane ET ACCISE.

    Le profil générique posait « CIF+DD », qui omet l'accise : la TVA aurait été
    sous-facturée sur chaque position qui en porte une.
    """
    tva = [
        d
        for p in socle["positions"].values()
        for d in p.get("droits") or []
        if d.get("code") == "TVA"
    ]
    assert tva
    assiettes = {d.get("assiette") for d in tva}
    assert assiettes == {"CIF+DD+EXC"}, assiettes
    assert {d.get("assiette_origine") for d in tva} == {"source"}


def test_l_assiette_de_l_accise_reste_non_etablie_plutot_que_supposee(socle):
    """Aucun des deux textes ne l'énonce : on ne la pose pas de mémoire."""
    accises = [
        d
        for p in socle["positions"].values()
        for d in p.get("droits") or []
        if d.get("code") == "EXC"
    ]
    assert accises, "le tarif publie bien des accises"
    assert all(not d.get("assiette") for d in accises)


def test_une_tva_dont_un_composant_manque_se_declare_incomplete(socle):
    """Plutôt que de servir un montant minoré."""
    from services.calcul import calculer

    cible = next(
        p
        for p in socle["positions"].values()
        if any(d.get("code") == "EXC" for d in p.get("droits") or [])
    )
    lignes = {x["code"]: x for x in calculer(cible, 10000.0)["npf"]["lignes"]}
    assert lignes["EXC"]["statut"] == "ASSIETTE_INDISPONIBLE"
    assert lignes["TVA"]["statut"] == "ASSIETTE_INCOMPLETE"


def test_une_position_sans_accise_se_liquide_entierement(socle):
    from services.calcul import calculer

    npf = calculer(socle["positions"]["01012100"], 10000.0)["npf"]
    lignes = {x["code"]: x for x in npf["lignes"]}
    assert lignes["DD"]["taux_pct"] == 0.0 and lignes["DD"]["montant"] == 0.0
    assert lignes["TVA"]["taux_pct"] == 15.0 and lignes["TVA"]["montant"] == 1500.0
    assert npf["etat"] == "COMPLET"
    assert npf["total_a_payer"] == 11500.0


def test_une_cellule_d_accise_vide_n_est_pas_une_accise_a_zero(crawl):
    """Vide = non soumis. Zéro = soumis, au taux nul. Les confondre ferait
    disparaître des taux publiés ou en inventerait des milliers."""
    s = crawl["stats"]
    assert s["accise_non_soumis"] > 5000, "la plupart des positions ne portent pas d'accise"
    porteuses = [
        t
        for p in crawl["sub_positions"]
        for t in p["taxes"]
        if t["code"] == "EXC"
    ]
    assert porteuses
    assert any(t["rate_pct"] == 0.0 for t in porteuses), "des accises sont publiées à 0 %"


def test_le_marqueur_d_exoneration_de_tva_est_lu_comme_tel(crawl):
    """« EXM » au tarif est une exonération : une donnée, pas une lacune."""
    exonerees = [
        t
        for p in crawl["sub_positions"]
        for t in p["taxes"]
        if t["code"] == "TVA" and t.get("exoneration_au_tarif")
    ]
    assert len(exonerees) == crawl["stats"]["tva_exoneree"] > 200
    assert all(t["rate_pct"] == 0.0 for t in exonerees)
    assert all("EX" in t["raw_value"].upper() for t in exonerees)


def test_une_ligne_aux_colonnes_decalees_est_refusee_et_non_devinee(crawl):
    """La TVA mauricienne est ad valorem ou « EXM », jamais un taux spécifique :
    une cellule de TVA portant « 30 cents per kg » dénonce un décalage."""
    decalees = [
        p
        for p in crawl["sub_positions"]
        if "COLONNES_DECALEES_TAUX_NON_LUS" in p["source_gaps"]
    ]
    assert decalees, "le document en contient"
    assert all(not p["taxes"] and not p["preferential_rates"] for p in decalees)
    assert all(p["designation"]["en"] for p in decalees), "le libellé, lui, est gardé"


def test_les_douze_regimes_preferentiels_sont_portes_zlecaf_comprise(crawl):
    """Le tarif publie une colonne par accord — dont la ZLECAf."""
    p = next(x for x in crawl["sub_positions"] if x["national_code"] == "01012100")
    regimes = {r["regime"] for r in p["preferential_rates"]}
    assert "ZLECAF" in regimes
    assert {"COMESA_I", "COMESA_II", "SADC", "IOC", "UE", "UK", "CHINE", "EAU"} <= regimes
    assert len(regimes) == 12


def test_un_contingent_n_est_pas_servi_comme_un_taux(crawl):
    """« 300 tons @ 0% duty » suppose un volume déjà imputé, que le moteur
    ne connaît pas."""
    contingents = [
        r
        for p in crawl["sub_positions"]
        for r in p["preferential_rates"]
        if r.get("non_liquidable") == "TAUX_SOUS_CONTINGENT"
    ]
    assert contingents
    assert all(r["rate_pct"] is None for r in contingents)
    assert all(r["raw_value"] for r in contingents)


def test_la_colonne_agency_est_lue_et_sa_legende_vient_du_document(crawl):
    """L'organisme qui délivre le document exigé est une formalité, pas un taux.
    Sa légende est lue page 11 du tarif, jamais recopiée de mémoire."""
    s = crawl["stats"]
    assert s["organismes_legende"] >= 15
    assert s["positions_avec_formalite"] > 3000
    formalites = [a for p in crawl["sub_positions"] for a in p["formalities"]]
    resolus = {a["organisme"] for a in formalites if a["organisme"]}
    assert "Food Import Unit" in resolus
    assert "Pharmacy Board" in resolus
    assert "Dangerous Chemicals Control Board" in resolus


def test_une_formalite_d_exportation_n_est_pas_servie_comme_une_exigence_d_import(crawl):
    """« MIC for Export under AGOA » vise l'exportation : la présenter comme une
    exigence à l'importation ferait réclamer un document indu."""
    export = [
        a
        for p in crawl["sub_positions"]
        for a in p["formalities"]
        if a["portee"] == "EXPORTATION"
    ]
    assert len(export) > 500
    assert all("export" in a["verbatim"].lower() for a in export)


def test_le_chapitre_des_produits_pharmaceutiques_est_servi(socle):
    """Il était perdu en entier : sur ces pages la ligne s'ouvre directement sur
    le code, sans la colonne « Heading » vide, et un indice fixe se décalait."""
    for chapitre in ("30", "44", "68", "97"):
        assert any(
            code.startswith(chapitre) for code in socle["positions"]
        ), f"chapitre {chapitre} absent du socle"


def test_les_taux_nuls_du_droit_sont_conserves(socle):
    """Maurice exonère largement : 6 475 positions portent un droit à 0 %.
    Les supprimer ferait disparaître la franchise elle-même."""
    nuls = [
        d
        for p in socle["positions"].values()
        for d in p.get("droits") or []
        if d.get("code") == "DD" and d.get("taux") == 0.0
    ]
    assert len(nuls) > 6000
