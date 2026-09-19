"""Seychelles — un calendrier de démantèlement ZLECAf, et une seule colonne due.

Le socle servait 5 396 moyennes SH6 de WITS. Le Customs Management (Tariff and
Classification of Goods) Regulations, 2022 — S.I. 113 of 2022, Gazette du
28 octobre 2022, 827 pages, le TEXTE RÉGLEMENTAIRE lui-même — en porte 6 019 à
huit chiffres, avec TREIZE colonnes de taux.

CE QUE CES TESTS TIENNENT.

1. UNE SEULE DES TREIZE COLONNES EST UN DROIT DÛ. Les douze autres sont des
   préférences et ne portent aucune assiette. Les confondre ferait réclamer
   treize fois le droit d'une position.

2. LA SADC ET LA ZLECAf ONT CINQ TAUX CHACUNE, un par année civile de 2022 à
   2026. Le règlement publie un CALENDRIER, et le socle le porte : chaque
   millésime sous son nom, celui de l'année en vigueur aussi sous le nom sans
   millésime. Au-delà de 2026 rien n'est reconduit.

3. QUI A DROIT À LA COLONNE ZLECAf EST UNE LISTE, pas une condition à vérifier :
   la Schedule VI nomme 38 États parties. C'est ce qui sépare les Seychelles du
   Malawi, dont le taux ZLECAf dépend d'un contenu d'origine de 35 %.

4. LE TAUX COI SE DÉDUIT, parce que la Schedule II énonce la formule — cinq
   POINTS de moins que le NPF, avec cinq exceptions nommées.

5. L'ASSIETTE EST LE CIF, et c'est la regulation 8(1)(e) de S.I. 42 of 2014 qui
   le dit — pas le VAT Act, dont la rédaction donnait à penser le contraire.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

SOCLE = RACINE / "socle" / "SYC.json"
CRAWL = RACINE / "data" / "crawled" / "SYC_tariffs.json"

pytestmark = pytest.mark.skipif(
    not SOCLE.exists() or not CRAWL.exists(),
    reason="socle non construit dans cet environnement",
)

MILLESIMES = ["2022", "2023", "2024", "2025", "2026"]


@pytest.fixture(scope="module")
def socle():
    return json.loads(SOCLE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def crawl():
    return json.loads(CRAWL.read_text(encoding="utf-8"))


def _droits(position, code):
    return [d for d in position.get("droits") or [] if d.get("code") == code]


def _taxes(crawl, code):
    return [t for p in crawl["sub_positions"] for t in p["taxes"] if t["code"] == code]


def test_le_socle_ne_sert_plus_une_moyenne_agregee(crawl):
    assert "WITS" not in json.dumps(crawl.get("source"), ensure_ascii=False).upper()
    assert crawl["source_quality"] == "crawled_authentic"
    assert "S.I. 113 of 2022" in crawl["source"]
    assert crawl["source_sha256"]
    # Le reglement est servi depuis une URL citable, non depuis un depot prive.
    assert crawl["source_url"].startswith("https://src.gov.sc/")


def test_les_positions_sont_nationales_et_portent_leur_libelle(socle):
    positions = socle["positions"]
    assert len(positions) > 5900
    assert all(len(code) == 8 for code in positions)
    sans_libelle = [c for c, p in positions.items() if not p["designation"]["en"]]
    assert len(sans_libelle) <= 5


def test_une_seule_colonne_sur_treize_est_un_droit_du(socle):
    """Les douze autres sont des REGIMES : elles n'entrent jamais dans la cascade.
    Les y laisser ferait reclamer treize fois le droit d'une position."""
    codes_de_droit = {
        d["code"] for p in socle["positions"].values() for d in (p.get("droits") or [])
    }
    assert codes_de_droit == {"DD"}
    regimes = {
        r for p in socle["positions"].values() for r in (p.get("preferentiels") or {})
    }
    assert "COMESA" in regimes and "EU_UK" in regimes and "COI" in regimes
    for prefixe in ("SADC", "AFCFTA"):
        assert prefixe in regimes
        for annee in MILLESIMES:
            assert f"{prefixe}_{annee}" in regimes, f"{prefixe}_{annee}"


def test_le_droit_de_douane_se_liquide_sur_le_cif_que_le_reglement_etablit(socle):
    """L'Act ne donne pas l'assiette : sa s.41 la DELEGUE. Le reglement la donne —
    valeur transactionnelle plus transport, manutention et assurance jusqu'au port
    (S.I. 42 of 2014, reg. 5 et reg. 8(1)(e))."""
    trouves = [
        d for p in socle["positions"].values() for d in _droits(p, "DD")
        if d.get("taux") is not None or d.get("specifique")
    ]
    assert len(trouves) > 5900
    assert {d.get("assiette") for d in trouves} <= {"CIF", "xQTE"}
    origine = json.dumps(socle["assiettes"], ensure_ascii=False)
    assert "8(1)(e)" in origine
    assert "port or place of importation" in origine


def test_le_calendrier_de_demantelement_est_porte_annee_par_annee(socle):
    """Le reglement publie CINQ taux ZLECAf, un par annee civile. Ne garder que le
    dernier perdrait le calendrier ; n'en garder qu'un sans dire lequel servirait
    peut-etre celui d'une annee revolue."""
    avec_calendrier = [
        p for p in socle["positions"].values()
        if all(f"AFCFTA_{a}" in (p.get("preferentiels") or {}) for a in MILLESIMES)
    ]
    assert len(avec_calendrier) > 5900
    # Le calendrier n'est pas decoratif : sur certaines positions il DESCEND.
    descendants = [
        p for p in avec_calendrier
        if p["preferentiels"]["AFCFTA_2022"].get("taux") is not None
        and p["preferentiels"]["AFCFTA_2026"].get("taux") is not None
        and p["preferentiels"]["AFCFTA_2026"]["taux"]
        < p["preferentiels"]["AFCFTA_2022"]["taux"]
    ]
    assert descendants, "aucun demantelement : le calendrier n'aurait pas ete lu"


def test_le_millesime_en_vigueur_est_aussi_servi_sans_millesime(socle, crawl):
    """C'est celui que le calculateur applique. Il n'est pas choisi : il vient de
    l'annee que la collecte a inscrite dans le fichier."""
    annee = crawl["stats"]["annee_en_vigueur"]
    assert annee in MILLESIMES, "le calendrier serait epuise : rien ne doit etre reconduit"
    for position in socle["positions"].values():
        prefs = position.get("preferentiels") or {}
        for prefixe in ("SADC", "AFCFTA"):
            if prefixe in prefs and f"{prefixe}_{annee}" in prefs:
                assert prefs[prefixe] == prefs[f"{prefixe}_{annee}"]


def test_la_liste_des_etats_parties_est_celle_de_la_schedule_vi(crawl):
    """38 Etats ENUMERES. Une origine absente de la liste n'a pas droit a la
    colonne ZLECAf, et c'est une liste, non une appreciation."""
    etats = crawl["notes_legales"]["etats_zlecaf_schedule_vi"]
    assert len(etats) == 38
    assert "Republic of South Africa" in etats
    # Les Seychelles ne figurent pas dans leur propre liste d'origines eligibles.
    assert "Republic of Seychelles" not in etats
    zlecaf = _taxes(crawl, "AFCFTA_2026")
    assert len(zlecaf) > 5900
    assert all("Schedule VI" in t["note"] for t in zlecaf)
    # Une preference n'est jamais liquidee sur une assiette supposee.
    assert {t["base"] for t in zlecaf} == {None}


def test_le_taux_coi_est_deduit_et_ses_exceptions_sont_nommees(crawl):
    """La Schedule II enonce la formule ; la deduire n'est pas extrapoler. Mais la
    ou une exception joue, le taux servi est celui du NPF et la ligne le dit."""
    coi = {p["national_code"]: t
           for p in crawl["sub_positions"] for t in p["taxes"] if t["code"] == "COI"}
    assert len(coi) > 5900
    npf = {p["national_code"]: t
           for p in crawl["sub_positions"] for t in p["taxes"] if t["code"] == "DD"}
    remises = exceptions = 0
    for code, ligne in coi.items():
        base = npf.get(code)
        if base is None or base["rate_pct"] is None:
            assert ligne["rate_pct"] is None
            continue
        if ligne["rate_pct"] == base["rate_pct"] - 5.0:
            remises += 1
            assert base["rate_pct"] > 5.0
            assert code[:2] not in ("22", "24") and code[:4] not in ("2710", "2711")
        else:
            exceptions += 1
            assert ligne["rate_pct"] == base["rate_pct"]
            assert "EXCEPTION_" in ligne["note"]
    assert remises > 400 and exceptions > 4000
    assert all("certificate of origin" in t["note"] for t in coi.values())


def test_un_droit_specifique_ne_se_lit_pas_comme_un_pourcentage(crawl):
    """« SCR60/l » se liquide a la QUANTITE. Et sur un droit COMPOSE, la valeur
    specifique portee ne doit etre QUE sa composante specifique : donner
    « 15%+SCR5.13/kg » au socle lui faisait lire 15 — le taux ad valorem servi
    comme un montant en roupies au kilo."""
    specifiques = [t for p in crawl["sub_positions"] for t in p["taxes"]
                   if t["specific_value"]]
    assert len(specifiques) > 2000
    assert all(t["specific_value"].upper().startswith("SCR") for t in specifiques)
    composes = [t for t in specifiques if "%" in (t["raw_value"] or "")]
    assert composes
    for taxe in composes:
        assert "%" not in taxe["specific_value"]
        assert taxe["rate_pct"] is not None


def test_une_cellule_non_lue_est_declaree_jamais_approchee(crawl):
    """Un taux d'une colonne servi sous le nom d'une autre est un chiffre faux ;
    une cellule declaree illisible n'est qu'un manque nomme."""
    sans_droit = [p for p in crawl["sub_positions"]
                  if not any(t["code"] == "DD" for t in p["taxes"])]
    assert len(sans_droit) < 60
    assert all("DROIT_NPF_NON_LU" in p["source_gaps"] for p in sans_droit)
    motifs = {g.rsplit("_", 1)[0] for p in crawl["sub_positions"] for g in p["source_gaps"]}
    assert any("DEUX_VALEURS_DANS_LA_COLONNE" in m for m in motifs)


def test_les_pages_sans_en_tete_sont_declarees_et_non_devinees(crawl):
    """L'en-tete de chaque page est la carte de ses colonnes. Neuf pages du bareme
    sur 591 n'en portent pas de complet : elles ne sont pas lues sur une grille
    supposee."""
    assert crawl["stats"]["pages_sans_en_tete"] <= 15
    assert crawl["stats"]["lignes_treize_colonnes"] > 5900


def test_la_modification_de_2024_est_portee_avec_sa_source_propre(crawl):
    """S.I. 7 of 2024 insere douze sous-positions que S.I. 113 of 2022 ne contient
    pas. Les porter sans les nommer serait les fabriquer ; la substitution qu'il
    opere au chapitre 22 n'est pas appliquee, et la fiche dit pourquoi."""
    insertions = [p for p in crawl["sub_positions"] if "S.I. 7 of 2024" in p["source"]]
    assert len(insertions) == 10
    assert {p["national_code"] for p in insertions} >= {"87034013", "87089911"}
    for position in insertions:
        assert all("S.I. 7 of 2024" in t["note"] for t in position["taxes"])
    assert "2208.7039" in crawl["notes_legales"]["reserve_si7_2024"]


def test_la_fiche_de_provenance_existe_et_est_verifiee():
    import subprocess

    fiche = (
        RACINE / "data" / "legal_refs" / "zlecaf_application"
        / "SYC_treize_colonnes_calendrier_zlecaf_et_valeur_2026-09-19.json"
    )
    assert fiche.exists()
    rendu = subprocess.run(
        [sys.executable, str(RACINE.parent / "scripts" / "verifier_fiche.py"), str(fiche)],
        capture_output=True, text=True,
    )
    assert rendu.returncode == 0, rendu.stdout + rendu.stderr
