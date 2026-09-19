"""Angola — un tarif lu dans un scan, et une colonne ZLECAf vide exprès.

Le socle servait 5 388 moyennes SH6 de WITS. Le Decreto Legislativo Presidencial
n.º 1/24 du 3 janvier 2024 — Diário da República I Série n.º 2, 345 pages, qui
approuve la Pauta Aduaneira et abroge le DLP n.º 10/19 — en porte 5 830 à huit
chiffres. Ce document est un SCAN INTÉGRAL : zéro octet de couche texte.

CE QUE CES TESTS TIENNENT.

1. « LIVRE » EST UN ZÉRO PUBLIÉ, et l'article 43.º n.º 1 des Instruções
   Preliminares le dit entre parenthèses : « taxa Livre (0%) ». C'est un bénéfice
   fiscal nommé, pas une case oubliée. Il y en a plus du tiers du tarif.

2. L'ANGOLA PUBLIE UNE COLONNE ZLECAf ET LA LAISSE VIDE, EXPRÈS. L'article 43.º
   n.º 2 déclare les colonnes 5 (SADC) et 6 (ZCLCA) « reservadas [...] a serem
   definidas em legislação específica ». Servir une préférence angolaise serait
   inventer une exonération que le législateur a lui-même remise à plus tard.

3. DEUX PRÉLÈVEMENTS SUR LA MÊME ASSIETTE : le droit de la colonne 4 et les
   emolumentos gerais aduaneiros de 2 % (art. 58.º n.º 3), tous deux « ad valorem »
   sur le valor aduaneiro (n.º 5), que le Código Aduaneiro art. 117.º n.º 2
   définit comme le CIF.

4. LE PROJET QUI CIRCULE N'EST PAS LA LOI. Un « Projecto da Pauta » avec couche
   texte est publié sur le même serveur ministériel ; il diverge de la loi sur
   730 des 3 058 taux comparables. Aucun de ses taux n'est servi.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

SOCLE = RACINE / "socle" / "AGO.json"
CRAWL = RACINE / "data" / "crawled" / "AGO_tariffs.json"

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


def _taxes(crawl, code):
    return [t for p in crawl["sub_positions"] for t in p["taxes"] if t["code"] == code]


def test_le_socle_ne_sert_plus_une_moyenne_agregee(crawl):
    assert "WITS" not in json.dumps(crawl.get("source"), ensure_ascii=False).upper()
    assert crawl["source_quality"] == "crawled_authentic"
    assert "n.º 1/24" in crawl["source"]
    assert crawl["source_sha256"]
    # Le decret est servi depuis une URL citable du Ministere des Finances angolais.
    assert crawl["source_url"].startswith("https://www.ucm.minfin.gov.ao/")


def test_les_positions_sont_nationales_et_portent_leur_libelle(socle, crawl):
    positions = socle["positions"]
    assert len(positions) > 5700
    assert all(len(code) == 8 for code in positions)
    sans_libelle = [p for p in crawl["sub_positions"] if not p["designation"]["pt"]]
    # Une ligne de points rendait l'OCR aveugle sur les libelles les plus courts —
    # « Outros », « Asininos ». La cellule est desormais rognee sur son texte.
    assert len(sans_libelle) < 300, f"{len(sans_libelle)} designations non lues"


def test_livre_est_un_zero_publie_et_non_une_lacune(crawl):
    """« taxa Livre (0%) » : l'article 43.º n.º 1 donne la valeur entre parentheses.
    Une premiere passe du collecteur ne cherchait que des chiffres et effacait ces
    2 152 positions — un tiers du tarif se serait servi sans droit."""
    livres = [t for t in _taxes(crawl, "DD") if t["raw_value"].lower() == "livre"]
    assert len(livres) > 2000
    assert all(t["rate_pct"] == 0.0 for t in livres)
    assert all("Livre (0%)" in t["note"] for t in livres)
    assert all(t["base"] == "CIF" for t in livres)


def test_la_colonne_zlecaf_est_publiee_et_vide_et_le_texte_dit_pourquoi(crawl):
    """L'article 43.º n.º 2 : « as colunas 5 (SADC) e 6 (ZCLCA) estao reservadas
    [...] a serem definidas em legislacao especifica ». La colonne existe, elle
    attend son texte d'application, et rien n'est invente pour la remplir."""
    for code in ("SADC", "AFCFTA"):
        lignes = _taxes(crawl, code)
        assert len(lignes) > 5700, code
        assert {t["rate_pct"] for t in lignes} == {None}, code
        assert all("LEGISLACAO ESPECIFICA" in t["note"].upper() for t in lignes), code
        assert all(t["base"] is None for t in lignes), code
    assert all("PREFERENCES_RESERVEES_PAR_L_ARTICLE_43" in p["source_gaps"]
               for p in crawl["sub_positions"])


def test_aucune_preference_angolaise_n_entre_dans_le_socle(socle):
    """Une colonne vide ne doit pas devenir un regime a taux nul : ce serait servir
    une franchise que le legislateur n'a pas encore ecrite."""
    for position in socle["positions"].values():
        for regime, valeur in (position.get("preferentiels") or {}).items():
            assert valeur.get("taux") is None, f"{regime} porte un taux"


def test_deux_prelevements_portent_sur_le_valor_aduaneiro(socle):
    """Le droit de la colonne 4 et les emolumentos gerais de 2 % (art. 58.º n.º 3),
    tous deux « ad valorem » sur le valor aduaneiro (n.º 5) — le CIF."""
    dd = [d for p in socle["positions"].values() for d in _droits(p, "DD")
          if d.get("taux") is not None]
    ega = [d for p in socle["positions"].values() for d in _droits(p, "EGA")]
    assert len(dd) > 5700 and len(ega) > 5700
    assert {d.get("assiette") for d in dd} == {"CIF"}
    assert {d.get("assiette") for d in ega} == {"CIF"}
    assert {d.get("taux") for d in ega} == {2.0}
    origine = json.dumps(socle["assiettes"], ensure_ascii=False)
    assert "117" in origine


def test_les_emoluments_survivent_aux_exonerations(crawl):
    """L'article 43.º n.º 4 exempte « os direitos aduaneiros, com excepcao da taxa
    devida pela prestacao de servicos » : une position a Livre doit donc quand meme
    porter ses 2 %."""
    exonerees = [p for p in crawl["sub_positions"]
                 if any(t["code"] == "DD" and t["rate_pct"] == 0.0 for t in p["taxes"])]
    assert exonerees
    for position in exonerees:
        ega = next((t for t in position["taxes"] if t["code"] == "EGA"), None)
        assert ega is not None and ega["rate_pct"] == 2.0
    # Les deux taux sectoriels ne sont pas appliques, et la ligne le dit.
    assert all("0,1 %" in t["note"] for t in _taxes(crawl, "EGA"))


def test_une_cellule_non_lue_est_declaree_jamais_approchee(crawl):
    """Le document est un SCAN : une lecture abimee est possible, et elle est
    nommee. Rien n'est rattrape a la devinette — « ivre » n'est pas converti en
    « Livre », meme si l'on devine ce qu'il voulait dire."""
    sans_droit = [p for p in crawl["sub_positions"]
                  if not any(t["code"] == "DD" for t in p["taxes"])]
    assert len(sans_droit) < 100
    for position in sans_droit:
        assert any(g.startswith("DD_") for g in position["source_gaps"])


def test_la_methode_de_lecture_est_declaree_dans_la_donnee(crawl):
    """Un tarif lu par OCR doit dire qu'il l'a ete : c'est une reserve qui suit la
    donnee, pas une note de bas de page."""
    assert "OCR" in crawl["methode"] or "optique" in crawl["methode"].lower()
    assert "scan" in crawl["methode"].lower()
    assert crawl["stats"]["pages_lues"] > 200


def test_la_taxe_est_ad_valorem_et_le_taux_est_plausible(crawl):
    """Un tarif ad valorem ne porte pas de taux au-dela de 100 % : un « 5 » lu
    « 55 » se verrait, un « 500 » aussi."""
    taux = [t["rate_pct"] for t in _taxes(crawl, "DD") if t["rate_pct"] is not None]
    assert taux
    assert max(taux) <= 100.0
    assert set(taux) <= {0.0, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 55.0}


def test_la_tva_absente_du_tarif_est_completee_par_la_table_nationale():
    """Le tarif angolais ne porte AUCUNE TVA. Elle vient de la table que ce depot
    reserve aux familles entierement absentes de leur source, avec l'article de loi
    qui l'enonce — et la reserve sur le vehicule par lequel il a ete lu."""
    table = json.loads((RACINE / "socle" / "tva_nationale.json").read_text(
        encoding="utf-8"))
    entree = table["pays"]["AGO"]
    assert entree["taux"] == 14.0
    assert "art. 19" in entree["source"]
    assert "lex.ao" in entree["source"]
    assert entree["fiche"].endswith("AGO_taux_TVA_2026-09-19.json")


@pytest.mark.parametrize(
    "fiche",
    ["AGO_assiette_droit_de_douane_2026-09-19.json", "AGO_taux_TVA_2026-09-19.json"],
)
def test_les_fiches_de_provenance_existent_et_sont_verifiees(fiche):
    import subprocess

    chemin = RACINE / "data" / "legal_refs" / "zlecaf_application" / fiche
    assert chemin.exists()
    rendu = subprocess.run(
        [sys.executable, str(RACINE.parent / "scripts" / "verifier_fiche.py"),
         str(chemin)],
        capture_output=True, text=True,
    )
    assert rendu.returncode == 0, rendu.stdout + rendu.stderr
