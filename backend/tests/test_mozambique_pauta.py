"""Mozambique — la cascade de la Pauta Aduaneira, et ce qu'une colonne vide dit.

Le socle servait 5 388 moyennes SH6 de la Banque mondiale, SANS AUCUNE
désignation. La Pauta Aduaneira en porte 5 822 à huit chiffres, avec leur
libellé portugais, leur unité et six colonnes de prélèvements.

La Lei n.º 11/2016 énonce la cascade article par article ; le Código do IVA
(Lei n.º 32/2007, art. 9) donne le sens d'une colonne d'IVA laissée vide. Ces
tests tiennent les deux, et les trois choses que le tarif ne dit pas.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

SOCLE = RACINE / "socle" / "MOZ.json"
CRAWL = RACINE / "data" / "crawled" / "MOZ_tariffs.json"

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


def test_les_positions_sont_nationales_et_portent_leur_libelle_portugais(socle):
    positions = socle["positions"]
    assert len(positions) > 5500
    assert all(len(code) == 8 for code in positions)
    sans = [
        code for code, p in positions.items()
        if not (p.get("designation") or {}).get("pt", "").strip()
    ]
    assert not sans, f"{len(sans)} positions sans libellé portugais"


@pytest.mark.parametrize(
    "code_taxe,assiette,article",
    [
        ("DD", "CIF", "art. 15 §2"),
        ("SOBRETX", "CIF", "art. 15 §5"),
        ("ICE", "CIF+DD", "art. 15 §6"),
        ("TVA", "CIF+DD+ICE+SOBRETX", "art. 15 §7"),
    ],
)
def test_chaque_assiette_est_celle_que_la_loi_enonce(socle, code_taxe, assiette, article):
    """Lei n.º 11/2016, Instruções Preliminares, artigo 15 — quatre assiettes
    énoncées l'une après l'autre."""
    trouves = [
        d
        for p in socle["positions"].values()
        for d in _droits(p, code_taxe)
    ]
    assert trouves, f"{code_taxe} absent du socle"
    assiettes = {d.get("assiette") for d in trouves}
    assert assiettes == {assiette}, f"{code_taxe} ({article}) : {assiettes}"
    assert {d.get("assiette_origine") for d in trouves} == {"source"}


def test_la_cascade_se_liquide_dans_l_ordre_de_la_loi(socle):
    """Vérifié sur une position portant droit, accise et TVA : chaque assiette
    inclut ce que la précédente a produit."""
    from services.calcul import calculer

    cible = next(
        (code, p)
        for code, p in socle["positions"].items()
        if _droits(p, "ICE") and _droits(p, "DD") and _droits(p, "TVA")
    )
    npf = calculer(cible[1], 10000.0)["npf"]
    lignes = {x["code"]: x for x in npf["lignes"]}
    assert lignes["DD"]["base"] == 10000.0
    # L'accise porte sur la valeur en douane AUGMENTÉE du droit payé.
    assert lignes["ICE"]["base"] == 10000.0 + lignes["DD"]["montant"]
    # La TVA porte sur la valeur en douane augmentée du droit ET de l'accise.
    assert lignes["TVA"]["base"] == 10000.0 + lignes["DD"]["montant"] + lignes["ICE"]["montant"]
    assert npf["etat"] == "COMPLET"


def test_une_colonne_de_tva_vide_est_une_exoneration_et_le_dit(crawl):
    """Código do IVA art. 9 : les exonérations sont définies par renvoi au tarif.
    Une cellule vide est donc l'expression de l'exonération, pas une lacune."""
    exonerees = [
        t
        for p in crawl["sub_positions"]
        for t in p["taxes"]
        if t["code"] == "IVA" and t.get("exoneration_au_tarif")
    ]
    assert len(exonerees) == crawl["stats"]["iva_exoneree"] > 400
    assert all(t["rate_pct"] == 0.0 for t in exonerees)
    assert all(t.get("exoneration_source") for t in exonerees), "exonération sans source"
    assert all("32/2007" in t["exoneration_source"] for t in exonerees)


def test_les_produits_pharmaceutiques_sont_tous_exoneres_de_tva(crawl):
    """Le chapitre 30 en entier — c'est ce qui rend la lecture « vide =
    exonération » vérifiable plutôt que vraisemblable."""
    ch30 = [p for p in crawl["sub_positions"] if p["chapter"] == "30"]
    assert ch30
    for p in ch30:
        iva = next(t for t in p["taxes"] if t["code"] == "IVA")
        assert iva["exoneration_au_tarif"], f"{p['national_code']} non exonérée"


def test_la_virgule_decimale_est_lue_comme_une_decimale(crawl):
    """Le fichier écrit « 2,5 » : le lire au point rendrait 25, dix fois le
    droit dû."""
    from crawlers.countries.mozambique_pauta_scraper import lire_taux

    assert lire_taux("2,5")[0] == 2.5
    assert lire_taux("7,5")[0] == 7.5
    assert lire_taux("0.0099")[0] == 0.0099
    taux = {
        t["rate_pct"]
        for p in crawl["sub_positions"]
        for t in p["taxes"]
        if t["code"] == "DD"
    }
    assert 2.5 in taux and 7.5 in taux
    assert max(x for x in taux if x is not None) <= 100


def test_une_valeur_minimale_n_est_pas_servie_comme_un_taux(socle, crawl):
    """« 475 MZN Per 1 L » est un plancher d'assiette, pas un pourcentage."""
    from crawlers.countries.mozambique_pauta_scraper import lire_taux

    taux, brut, motif = lire_taux("475 MZN Per 1 L")
    assert taux is None and motif == "VALEUR_MINIMALE_PAR_UNITE" and brut

    minima = [
        d
        for p in socle["positions"].values()
        for d in p.get("droits") or []
        if d.get("code") == "ICEVALMIN"
    ]
    assert minima, "le tarif en porte"
    assert all(not d.get("assiette") for d in minima)


def test_la_colonne_non_identifiee_reste_sans_assiette(socle):
    """La loi assoit la « sobretaxa » ; elle n'explique pas TXSOBVAL. La
    rattacher par ressemblance de nom serait une supposition."""
    inconnues = [
        d
        for p in socle["positions"].values()
        for d in p.get("droits") or []
        if d.get("code") == "TXSOBVAL"
    ]
    assert inconnues
    assert all(not d.get("assiette") for d in inconnues)


def test_l_absence_des_colonnes_preferentielles_est_nommee(crawl):
    """Le barème publié porte SADC et UE ; l'extrait ne les a pas. C'est une
    lacune de collecte, pas l'absence d'un régime."""
    assert all(not p["preferential_rates"] for p in crawl["sub_positions"])
    reserve = crawl.get("provenance_reserve") or ""
    assert "Lei n.º 11/2016" in reserve
    assert "1 131" in reserve or "1131" in reserve


def test_la_provenance_de_l_extrait_est_declaree_avec_sa_reserve(crawl):
    """C'est un export de base de données, pas un document publié : le dire
    est la condition pour s'en servir."""
    reserve = crawl.get("provenance_reserve") or ""
    assert "base de données" in reserve
    assert crawl.get("source_legal") and "11/2016" in crawl["source_legal"]
    assert crawl.get("source_sha256")
