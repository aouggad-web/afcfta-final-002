"""Malawi — neuf colonnes sans en-tête, et une grille qui se déplace sous elles.

Le socle servait 5 388 moyennes SH6 de WITS, SANS AUCUNE désignation. Le
Customs and Excise (Tariffs) (No. 3) Order, 2022 — Gazette Supplement du
29 juillet 2022, Government Notice No. 30, 642 pages, le TEXTE RÉGLEMENTAIRE
lui-même — en porte 7 373 à huit chiffres, avec neuf colonnes de prélèvements.

CE QUE CES TESTS TIENNENT.

1. LA CARTE DES COLONNES EST DANS LE DÉCRET, pas déduite de la mise en page :
   le paragraphe 4, page 22, définit chacune des neuf.

2. LES COLONNES 5 ET 6 NE SONT PAS DEUX DROITS CÔTE À CÔTE. Elles diffèrent sur
   4 409 des 7 373 positions — plus de la moitié du tarif — et le paragraphe 5
   tranche : la 5 est le PLEIN DROIT, les 6 à 9 en sont des REMISES par origine.
   La 6 vaut pour « a Contracting Party of the GATT », donc pour tout membre de
   l'OMC : c'est elle qui est servie comme droit de douane.

3. L'ASSIETTE EST LE PRIX NORMAL DE LA SCHEDULE A, non la valeur
   transactionnelle de l'OMC. Son contenu économique est le CIF, et c'est ce que
   le socle sert ; sa forme juridique ne l'est pas, et c'est dit.

4. TROIS PRÉLÈVEMENTS SONT PORTÉS SANS ASSIETTE — accise, TVA, Advance Income
   Tax. Le décret donne leur TAUX, aucun texte malawien lu ici ne donne leur
   assiette. Les poser sur le CIF fabriquerait un montant crédible et faux.

5. LE TAUX ZLECAf PORTE DEUX CONDITIONS QUE LE TEXTE ÉNONCE : l'Afrique du Sud
   en est exclue, et il exige un contenu d'origine de 35 %.

6. LA GRILLE DES COLONNES SE DÉPLACE D'UNE LIGNE À L'AUTRE — jusqu'à 24 unités
   sur les pages des véhicules. L'affectation se fait donc sur la FORME de la
   ligne et non sur une abscisse fixe, et elle REFUSE plutôt que d'hésiter.

7. « EXEMPT » N'EST PAS ZÉRO. Une livraison exonérée n'est pas dans le champ de
   la TVA ; une livraison détaxée (« Zero ») est taxée à 0 %. Le VAT Act les
   traite dans deux annexes différentes, et le socle ne les confond pas.
"""

import json
import pathlib
import sys

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

SOCLE = RACINE / "socle" / "MWI.json"
CRAWL = RACINE / "data" / "crawled" / "MWI_tariffs.json"

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


#: Le socle normalise les codes : « DD_PLEIN » y devient « DDPLEIN ».
def _droits(position, code):
    return [d for d in position.get("droits") or [] if d.get("code") == code]


def _taxes(crawl, code):
    return [t for p in crawl["sub_positions"] for t in p["taxes"] if t["code"] == code]


def test_le_socle_ne_sert_plus_une_moyenne_agregee(crawl):
    assert "WITS" not in json.dumps(crawl.get("source"), ensure_ascii=False).upper()
    assert crawl["source_quality"] == "crawled_authentic"
    assert "Government Notice No. 30" in crawl["source"]
    assert crawl["source_sha256"]
    # Le decret est servi depuis une URL citable, non depuis un depot prive.
    assert crawl["source_url"].startswith("https://www.mra.mw/")


def test_les_positions_sont_nationales_et_portent_leur_libelle(socle):
    positions = socle["positions"]
    assert len(positions) > 7000
    assert all(len(code) == 8 for code in positions)


def test_la_partie_iii_est_bornee_et_l_appendix_des_remises_exclu(crawl):
    """Le decret ne contient pas QUE le tarif : apres la Partie III viennent la
    Deuxieme annexe et une Appendix A de remises par industrie, qui portent des
    positions SH dans des grilles de colonnes DIFFERENTES. Sans borne, 39
    positions de l'Appendix entraient au tarif, leurs trois colonnes tombant sur
    SADC_ZAF, accise et TVA : un droit faux, tire d'un autre bareme."""
    debut, fin = (int(x) for x in crawl["stats"]["part_iii_pages"].split("-"))
    assert debut >= 25, "la table des matieres, page 16, porte aussi « PART III »"
    assert fin <= 570 < crawl["stats"]["pages"]
    assert max(p["page_source"] for p in crawl["sub_positions"]) <= fin


def test_le_droit_servi_est_la_colonne_6_et_le_plein_droit_reste_nomme(socle):
    """Le paragraphe 5 fait de la colonne 6 une REMISE de la colonne 5, ouverte a
    « a Contracting Party of the GATT » — donc a tout membre de l'OMC. C'est elle
    qui est le droit de douane courant ; la colonne 5 est conservee a cote."""
    positions = socle["positions"]
    avec_les_deux = [
        p for p in positions.values()
        if _droits(p, "DD") and _droits(p, "DDPLEIN")
    ]
    assert len(avec_les_deux) > 6000
    differentes = [
        p for p in avec_les_deux
        if _droits(p, "DD")[0]["taux"] != _droits(p, "DDPLEIN")[0]["taux"]
    ]
    # Les deux colonnes divergent sur plus de la moitie du tarif : les confondre
    # donnerait un droit faux sur la majorite des positions.
    assert len(differentes) > 4000
    plein = _droits(positions["02021000"], "DDPLEIN")[0]
    npf = _droits(positions["02021000"], "DD")[0]
    assert (plein["taux"], npf["taux"]) == (15.0, 10.0)
    assert "PLEIN DROIT" in plein["note"]
    assert "GATT" in npf["note"]


@pytest.mark.parametrize("code_taxe", ["DD", "DDPLEIN"])
def test_le_droit_de_douane_se_liquide_sur_le_prix_normal_de_la_schedule_a(socle, code_taxe):
    trouves = [
        d for p in socle["positions"].values() for d in _droits(p, code_taxe)
        if d.get("taux") is not None
    ]
    assert trouves
    assert {d["assiette"] for d in trouves} == {"CIF"}
    assert {d.get("assiette_origine") for d in trouves} == {"source"}
    origine = json.dumps(socle["assiettes"], ensure_ascii=False)
    assert "Schedule A" in origine
    assert "port or place of introduction" in origine


@pytest.mark.parametrize("code_taxe", ["EXC", "TVA", "AIT"])
def test_les_trois_prelevements_sans_assiette_ne_se_liquident_pas(socle, crawl, code_taxe):
    """Le decret donne leurs TAUX, pas leur assiette, et aucun texte malawien lu
    ici ne l'etablit. Les poser sur le CIF parce que c'est l'usage ailleurs
    fabriquerait un montant credible et faux. Le profil generique « TVA sur
    CIF+DD » que portait backend/services/tax_profile_data.py sous la seule
    mention « Malawi Revenue Authority » a ete RETIRE pour cette raison."""
    porte = _taxes(crawl, code_taxe)
    assert porte, f"{code_taxe} absent du tarif collecte"
    assert {t["base"] for t in porte} == {None}
    assert all("ASSIETTE" in t["note"] for t in porte)

    trouves = [d for p in socle["positions"].values() for d in _droits(p, code_taxe)]
    assert trouves, f"{code_taxe} absent du socle"
    assert {d.get("assiette") for d in trouves} == {None}, (
        f"{code_taxe} a recu une assiette qu'aucun texte malawien n'etablit"
    )


def test_une_taxe_sans_assiette_est_declaree_et_non_liquidee(socle):
    from services.calcul import calculer

    resultat = calculer(socle["positions"]["02021000"], 10000.0)["npf"]
    lignes = {x["code"]: x for x in resultat["lignes"]}
    assert lignes["DD"]["montant"] == pytest.approx(1000.0)
    for code in ("TVA", "AIT"):
        if code in lignes:
            assert lignes[code]["montant"] is None
            assert lignes[code]["statut"] == "ASSIETTE_INDISPONIBLE"
    assert resultat["etat"] != "COMPLET"


def test_le_taux_zlecaf_porte_ses_deux_conditions(crawl):
    """« a State Party to the AfCFTA other than Republic of South Africa »,
    « a specified country content of not less than thirty-five per cent » : les
    deux sont dans le texte, aucune ne se devine, et le calculateur ne verifie
    pas la seconde. Promettre la preference sans elles serait inventer une
    exoneration."""
    zlecaf = _taxes(crawl, "AFCFTA")
    assert len(zlecaf) > 6000
    assert all("thirty-five per cent" in t["note"] for t in zlecaf)
    assert all("other than Republic of South Africa" in t["note"] for t in zlecaf)
    # Une preference n'est jamais liquidee sur une assiette supposee.
    assert {t["base"] for t in zlecaf} == {None}


def test_les_quatre_colonnes_preferentielles_portent_la_condition_d_origine(crawl):
    for code in ("COMESA", "AFCFTA", "SADC", "SADC_ZAF"):
        trouves = _taxes(crawl, code)
        assert trouves, code
        assert all("thirty-five per cent" in t["note"] for t in trouves), code


def test_les_deux_colonnes_sadc_restent_distinctes_dans_le_socle(socle):
    """Le Malawi publie DEUX colonnes SADC — col. 8 hors Afrique du Sud, col. 9
    Afrique du Sud seulement. Les ranger sous un meme regime ferait servir le taux
    de la derniere colonne lue : credible, et faux pour la moitie des origines."""
    regimes = {
        regime
        for p in socle["positions"].values()
        for regime in (p.get("preferentiels") or {})
    }
    assert {"COMESA", "AFCFTA", "SADC", "SADC_ZAF"} <= regimes
    differentes = [
        p for p in socle["positions"].values()
        if (p.get("preferentiels") or {}).get("SADC", {}).get("taux")
        != (p.get("preferentiels") or {}).get("SADC_ZAF", {}).get("taux")
    ]
    assert differentes


def test_exempt_n_est_pas_un_zero_et_zero_n_est_pas_une_lacune(crawl):
    """Le VAT Act traite l'exoneration (premiere annexe) et la detaxation
    (seconde) dans deux annexes differentes : « Exempt » n'est pas dans le champ
    de la taxe, « Zero » y est a 0 %. Les confondre effacerait la distinction que
    la loi etablit."""
    exonerees = [
        t for p in crawl["sub_positions"] for t in p["taxes"]
        if t["code"] == "TVA" and t["raw_value"] == "Exempt"
    ]
    assert len(exonerees) > 1000
    assert {t["rate_pct"] for t in exonerees} == {None}
    detaxees = [
        t for p in crawl["sub_positions"] for t in p["taxes"]
        if t["code"] == "TVA" and t["raw_value"] == "Zero"
    ]
    assert detaxees
    assert {t["rate_pct"] for t in detaxees} == {0.0}


def test_une_ligne_dont_les_colonnes_ne_se_lisent_pas_est_declaree(crawl):
    """Un taux d'accise servi comme droit de douane est un chiffre faux ; une
    colonne declaree illisible n'est qu'un manque nomme. 271 des 274 positions
    sans droit le sont pour un motif STRUCTUREL — colonnes non identifiees, deux
    valeurs dans une meme colonne, aucune valeur lisible. Les trois dernieres
    tiennent a un defaut du document : la couche texte du PDF y rend « Free »
    tronque en « Fre », quatre fois sur 642 pages. Rien n'est deduit de ce
    prefixe, la cellule reste non lue, et la position le declare."""
    sans_droit = [
        p for p in crawl["sub_positions"]
        if not any(t["code"] == "DD" for t in p["taxes"])
    ]
    assert sans_droit
    assert len(sans_droit) < 400
    # Aucune n'est servie a zero : c'est la seule chose qui ne se negocie pas.
    assert all("DROIT_NPF_NON_LU" in p["source_gaps"] for p in sans_droit)
    motifs = {
        "COLONNES_NON_IDENTIFIEES",
        "DEUX_VALEURS_DANS_LA_MEME_COLONNE",
        "AUCUNE_VALEUR_SUR_LA_LIGNE",
    }
    structurelles = [p for p in sans_droit if motifs & set(p["source_gaps"])]
    assert len(structurelles) >= len(sans_droit) - 5


def test_une_preference_superieure_au_plein_droit_est_signalee(crawl):
    """Le paragraphe 5 fait des colonnes 6 a 9 des remises du plein droit :
    aucune ne devrait le depasser. Sur 3004.90.90 le barème porte pourtant
    « Free » aux colonnes 5 et 6 et 2 % au COMESA. Verifie page a page, c'est le
    DOCUMENT qui est ainsi : le taux est servi tel quel, et la ligne porte
    l'anomalie pour que personne ne l'applique sans l'avoir vue."""
    anomalies = [
        p for p in crawl["sub_positions"]
        if "PREFERENCE_SUPERIEURE_AU_PLEIN_DROIT" in p["source_gaps"]
    ]
    assert anomalies
    for position in anomalies:
        taux = {t["code"]: t["rate_pct"] for t in position["taxes"]}
        plein = taux["DD_PLEIN"]
        assert any(
            taux.get(code) is not None and taux[code] > plein
            for code in ("DD", "COMESA", "AFCFTA", "SADC", "SADC_ZAF")
        )
    # L'inverse doit tenir : hors de cette liste, le plein droit est le maximum.
    for position in crawl["sub_positions"]:
        if "PREFERENCE_SUPERIEURE_AU_PLEIN_DROIT" in position["source_gaps"]:
            continue
        taux = {t["code"]: t["rate_pct"] for t in position["taxes"]}
        if taux.get("DD_PLEIN") is None:
            continue
        for code in ("DD", "COMESA", "AFCFTA", "SADC", "SADC_ZAF"):
            if taux.get(code) is not None:
                assert taux[code] <= taux["DD_PLEIN"], position["national_code"]


def test_l_unite_de_quantite_de_la_colonne_4_est_collectee(crawl):
    """Elle est PUBLIEE et elle compte : c'est elle qui dit en quoi une quantite
    se declare. Le vocabulaire est ferme ; ailleurs rien n'est suppose."""
    unites = [p["statistical_unit"] for p in crawl["sub_positions"] if p["statistical_unit"]]
    assert len(unites) > 6000
    assert set(unites) >= {"kg", "U"}
    assert all(len(u) <= 8 for u in unites)


def test_la_reserve_sur_la_date_de_la_consolidation_est_portee_sur_chaque_droit(socle):
    """La consolidation lue s'arrete au 30 juin 2018 et malawilii.org refuse son
    PDF (403). La reserve n'est pas dans un coin de la documentation : elle est
    sur la ligne — sur chaque droit qui porte un taux. Les 274 droits que le socle
    declare INDISPONIBLES portent, eux, le motif de leur absence : ils ne se
    liquident pas, il n'y a pas d'assiette a reserver."""
    droits = [
        d for p in socle["positions"].values()
        for code in ("DD", "DDPLEIN") for d in _droits(p, code)
    ]
    assert droits
    avec_taux = [d for d in droits if d.get("taux") is not None]
    assert len(avec_taux) > 13000
    assert all("30 juin 2018" in d["note"] for d in avec_taux)
    sans_taux = [d for d in droits if d.get("taux") is None]
    assert all("indisponible" in d["note"] or "supposé" in d["note"] for d in sans_taux)


def test_la_fiche_de_provenance_existe_et_est_verifiee():
    import subprocess

    fiche = (
        RACINE.parent / "backend" / "data" / "legal_refs" / "zlecaf_application"
        / "MWI_colonnes_remises_et_prix_normal_2026-09-19.json"
    )
    assert fiche.exists()
    rendu = subprocess.run(
        [sys.executable, str(RACINE.parent / "scripts" / "verifier_fiche.py"), str(fiche)],
        capture_output=True, text=True,
    )
    assert rendu.returncode == 0, rendu.stdout + rendu.stderr
