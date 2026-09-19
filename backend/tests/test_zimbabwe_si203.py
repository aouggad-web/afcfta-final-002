"""Zimbabwe — le SI 203 de 2022, et ce qu'un tarif tranche lui-même.

Le socle servait 5 388 moyennes SH6 de la Banque mondiale, SANS AUCUNE
désignation. Le Statutory Instrument 203 of 2022 en porte 6 637 à huit
chiffres, avec leur libellé anglais et deux colonnes de droits.

Deux choses distinguent ce tarif, et ces tests les tiennent l'une et l'autre.

1. IL ÉNONCE SA PROPRE RÈGLE DE DÉPARTAGE. « 40% or US$1.50/kg » est ambigu
   partout ailleurs — le tarif sud-africain publie la même forme sans la
   trancher, et son droit reste donc refusé. Le paragraphe 3(2), page 13, la
   tranche : « the rate of duty yielding the higher amount of duty shall be
   applicable ». Le socle peut donc liquider, et il nomme la composante qui
   l'emporte.

2. IL SE CONTRÔLE LUI-MÊME. Le barème publie DEUX colonnes de droits,
   « General » et « M.F.N. ». Elles concordent sur 6 637 positions sur 6 637 :
   c'est le document qui valide l'extraction, pas une source extérieure.

Et trois choses qu'il ne dit pas, qui doivent le rester : le taux de l'accise,
le titre alcoométrique de onze spiritueux, et une position illisible.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

SOCLE = RACINE / "socle" / "ZWE.json"
CRAWL = RACINE / "data" / "crawled" / "ZWE_tariffs.json"

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
    assert "203 of 2022" in crawl["source"]
    assert crawl.get("source_sha256")


def test_les_positions_sont_nationales_et_portent_leur_libelle_anglais(socle):
    positions = socle["positions"]
    assert len(positions) > 6600
    assert all(len(code) == 8 for code in positions)
    sans = [
        code for code, p in positions.items()
        if not (p.get("designation") or {}).get("en", "").strip()
    ]
    assert not sans, f"{len(sans)} positions sans libellé anglais"


def test_les_deux_colonnes_du_tarif_concordent(crawl):
    """Le contrôle est INTERNE au document : « General » et « M.F.N. » sont
    publiées côte à côte, et leur accord valide l'extraction."""
    assert crawl["stats"]["colonnes_divergentes"] == 0
    divergentes = [
        p for p in crawl["sub_positions"]
        if "COLONNES_GENERAL_ET_MFN_DIVERGENTES" in (p.get("source_gaps") or [])
    ]
    assert not divergentes


def test_l_assiette_du_droit_est_celle_que_la_loi_enonce(socle):
    """Customs and Excise Act s.106(1) et s.113(2)(c) : valeur transactionnelle
    augmentée du fret et de l'assurance jusqu'au lieu d'importation."""
    dd = [d for p in socle["positions"].values() for d in _droits(p, "DD")]
    assert dd
    portant_valeur = [d for d in dd if d.get("taux") is not None or d.get("specifique")]
    assert portant_valeur
    assiettes = {d.get("assiette") for d in portant_valeur}
    assert assiettes <= {"CIF", "xQTE"}, assiettes
    sur_cif = [d for d in portant_valeur if d.get("assiette") == "CIF"]
    assert {d.get("assiette_origine") for d in sur_cif} == {"source"}


def test_un_droit_compose_est_liquide_parce_que_le_texte_enonce_la_regle(socle):
    """SI 203/2022, p. 13 : « the rate of duty yielding the higher amount of
    duty shall be applicable ». C'est ce qui manque au tarif SARS."""
    composes = [
        d for p in socle["positions"].values() for d in _droits(p, "DD")
        if d.get("compose")
    ]
    assert composes, "le tarif en porte"
    assert all(d.get("regle_composee") == "LE_PLUS_ELEVE" for d in composes)
    assert all(d.get("expression_brute") for d in composes)
    assert all(isinstance(d.get("specifique"), dict) for d in composes), (
        "la composante spécifique doit être décomposée, pas laissée en chaîne : "
        "le moteur refuse une chaîne et rendrait QUANTITE_REQUISE à tort"
    )
    assert all(d["specifique"].get("montant") is not None for d in composes)


def test_la_composante_la_plus_elevee_l_emporte_et_la_ligne_la_nomme(socle):
    """À faible quantité l'ad valorem mord ; à forte quantité le spécifique."""
    from services.calcul import calculer

    position = socle["positions"]["02061000"]
    droit = _droits(position, "DD")[0]
    assert droit["taux"] == 40.0 and droit["specifique"]["montant"] == 1.5

    faible = calculer(position, 1000.0, quantite=100.0, devise_cif="usd")["npf"]
    ligne = faible["lignes"][0]
    assert ligne["statut"] == "CALCULE"
    assert ligne["composante_retenue"] == "ad_valorem"
    assert ligne["montant"] == pytest.approx(400.0)

    forte = calculer(position, 1000.0, quantite=500.0, devise_cif="usd")["npf"]
    ligne = forte["lignes"][0]
    assert ligne["statut"] == "CALCULE"
    assert ligne["composante_retenue"] == "specifique"
    assert ligne["montant"] == pytest.approx(750.0)
    assert ligne["regle_composee"] == "LE_PLUS_ELEVE"


def test_sans_quantite_un_droit_compose_refuse_de_liquider(socle):
    """Le départage exige la quantité. Sans elle, on ne retient pas celle qui
    arrange : on le dit."""
    from services.calcul import calculer

    npf = calculer(socle["positions"]["02061000"], 1000.0, devise_cif="usd")["npf"]
    ligne = npf["lignes"][0]
    assert ligne["statut"] == "QUANTITE_REQUISE"
    assert ligne["montant"] is None
    assert npf["etat"] == "INDISPONIBLE"


def test_l_accise_mentionnee_sans_taux_n_herite_jamais_du_droit_de_douane(socle, crawl):
    """« 5% + Excise » : le 5 % est le DROIT DE DOUANE. Laisser l'expression
    entière en valeur brute de l'accise la faisait relire — l'accise servait
    alors 5 %, un montant crédible et faux."""
    accises = [d for p in socle["positions"].values() for d in _droits(p, "EXC")]
    assert len(accises) == crawl["stats"]["accises_sans_taux"] == 116
    assert all(d.get("taux") is None for d in accises), (
        "une accise a hérité d'un taux qui n'est pas le sien"
    )
    assert all(not d.get("assiette") for d in accises)
    assert all("tarif d'accise" in (d.get("note") or "") for d in accises)

    brutes = [
        t for p in crawl["sub_positions"] for t in p["taxes"]
        if t["code"] == "EXC"
    ]
    assert all(t["raw_value"] == "Excise" for t in brutes)
    # L'expression entière de la colonne reste consultable, sans être relue.
    assert any(t.get("expression_colonne", "").startswith("5%") for t in brutes)


def test_une_position_a_accise_reste_partielle_et_le_dit(socle):
    from services.calcul import calculer

    npf = calculer(socle["positions"]["21069010"], 1000.0, quantite=10.0)["npf"]
    lignes = {x["code"]: x for x in npf["lignes"]}
    assert lignes["DD"]["statut"] == "CALCULE"
    assert lignes["DD"]["montant"] == pytest.approx(50.0)
    assert lignes["EXC"]["statut"] != "CALCULE"
    assert lignes["EXC"].get("montant") is None
    assert npf["etat"] == "PARTIEL"


def test_deux_specifiques_dans_des_unites_differentes_ne_sont_pas_departages(crawl):
    """« US$5.00/L or US$10.00/LAA » : par litre de produit, ou par litre
    d'alcool pur. Les comparer exige le titre alcoométrique, que le tarif ne
    porte pas. N'en retenir qu'une servirait un montant crédible et faux."""
    incomparables = [
        p for p in crawl["sub_positions"]
        if "DEUX_COMPOSANTES_SPECIFIQUES_UNITES_DIFFERENTES" in (p.get("source_gaps") or [])
    ]
    assert len(incomparables) == crawl["stats"]["specifiques_incomparables"] == 11
    for p in incomparables:
        assert p["chapter"] == "22"
        dd = next(t for t in p["taxes"] if t["code"] == "DD")
        assert dd["rate_pct"] is None and not dd.get("specific_value")
        assert "LAA" in dd["expression_colonne"]
        # Le « + Excise » de la même ligne reste dû : le taire l'exonérerait.
        assert any(t["code"] == "EXC" for t in p["taxes"])


def test_un_taux_non_lu_est_declare_indisponible_jamais_approche(crawl):
    non_lus = [
        p for p in crawl["sub_positions"]
        if "TAUX_NON_LU" in (p.get("source_gaps") or [])
    ]
    assert len(non_lus) == crawl["stats"]["taux_non_lus"]
    for p in non_lus:
        dd = next(t for t in p["taxes"] if t["code"] == "DD")
        assert dd["rate_pct"] is None
        assert "indisponible" in dd["note"]


def test_le_zero_publie_est_une_donnee_et_non_une_absence(crawl):
    """Chapitre 30 — produits pharmaceutiques : les zéros du tarif sont des
    exonérations publiées, et ils sont servis comme tels."""
    zeros = [
        t for p in crawl["sub_positions"] for t in p["taxes"]
        if t["code"] == "DD" and t.get("rate_pct") == 0.0
    ]
    assert len(zeros) > 500, f"{len(zeros)} droits à 0 % seulement"


def test_la_tva_n_est_pas_portee_par_ce_tarif(socle):
    """Le SI 203 ne porte pas la TVA. En inventer une ici serait la fabriquer ;
    elle est sourcée ailleurs, sous son propre instrument."""
    tva = [d for p in socle["positions"].values() for d in _droits(p, "TVA")]
    assert not tva


def test_la_fiche_de_provenance_existe_et_est_verifiee():
    fiche = (
        RACINE / "data" / "legal_refs" / "zlecaf_application"
        / "ZWE_assiette_et_droits_composes_2026-09-18.json"
    )
    assert fiche.exists()
    contenu = json.loads(fiche.read_text(encoding="utf-8"))
    assert contenu["etabli"] is True
    assert "106" in contenu["regle"]["valeur_en_douane"]["article"]
    assert "higher amount of duty" in (
        contenu["regle"]["droit_compose_la_regle_est_enoncee"]["verbatim"]
    )
    sources = (RACINE / "data" / "legal_refs" / "zlecaf_application" / "sources")
    assert (sources / "ZWE_si203_2022_duties_leviable.texte-extrait.txt").exists()
    assert (sources / "ZWE_customs_excise_act_s106_s113_valeur.texte-extrait.txt").exists()


def test_un_code_centre_verticalement_ne_vole_pas_le_droit_de_sa_voisine(socle, crawl):
    """Le code est centré dans sa ligne : quand celle-ci tient sur deux lignes
    de texte, il tombe sur la SECONDE. L'ancrer dessus faisait commencer la
    position une ligne trop bas — et sa première ligne, désignation ET début du
    taux, grossissait la position précédente.

    Relevé sur la page 437, sur deux positions voisines de pneumatiques :
    4011.20.10 se servait « 15% + US$5.00/Kg », qui est le droit de
    4011.20.90 ; et 4011.20.90 se servait sans aucun taux. Un droit faux, et
    silencieux.
    """
    positions = {p["national_code"]: p for p in crawl["sub_positions"]}
    assert positions["40112010"]["colonne_general"] == "15%"
    assert positions["40112090"]["colonne_general"] == "15% + US$5.00/Kg"

    droit = _droits(socle["positions"]["40112010"], "DD")[0]
    assert droit["taux"] == 15.0
    assert not droit.get("specifique"), "le spécifique de la voisine s'est invité"

    voisine = _droits(socle["positions"]["40112090"], "DD")[0]
    assert voisine["taux"] == 15.0
    assert voisine["specifique"]["montant"] == 5.0

    # Et plus aucune position ne se sert sans désignation : une position sans
    # désignation est une ligne que la collecte n'a pas su assembler.
    sans = [
        p["national_code"] for p in crawl["sub_positions"]
        if not p["designation"]["en"].strip()
    ]
    assert not sans, sans[:10]


def test_les_codes_que_la_source_ecrit_de_travers_sont_recuperes(crawl):
    """Neuf positions sur 6 637 omettent un point (« 9608.9900 ») ou intercalent
    une espace (« 5113. 00.00 »). N'accepter que la forme canonique les faisait
    disparaître en silence — et une position absente se lit comme une position
    qu'on n'a pas."""
    codes = {p["national_code"] for p in crawl["sub_positions"]}
    for code in ("96089900", "51130000", "90211000", "73151100", "56031200"):
        assert code in codes, f"{code} perdu par une coquille de la source"
