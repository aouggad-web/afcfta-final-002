# -*- coding: utf-8 -*-
"""La mesure du coût d'indisponibilité doit rester rejouable et cohérente.

Les chiffres qui arbitrent la note de décision ont d'abord vécu hors du dépôt :
mesurés en session, cités dans la note et dans la demande de fusion, portés par
aucun fichier. Ils sont devenus faux sans que rien ne le signale le jour où
l'inventaire fiscal a été corrigé.

Ces tests ferment cette porte : le rapport existe, ses trois lectures sont
emboîtées, et sa méthode est déclarée.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

RAPPORT = REPO_ROOT / "reports" / "COUT_INDISPONIBILITE.json"


@pytest.fixture(scope="module")
def rapport() -> dict:
    # Ce rapport est l'entrée chiffrée d'une décision produit. Sauter quand il
    # manque rendrait son absence indolore, alors que c'est précisément ce que
    # ce fichier existe pour empêcher.
    assert RAPPORT.exists(), (
        f"{RAPPORT.relative_to(REPO_ROOT)} est un livrable versionné et doit "
        "exister. Le régénérer avec scripts/measure_unavailability_cost.py."
    )
    return json.loads(RAPPORT.read_text(encoding="utf-8"))


def test_les_trois_lectures_sont_emboitees(rapport):
    """Restreindre la définition ne peut qu'abaisser le compte, jamais l'élever."""
    g = rapport["global"]
    stricte = g["lignes_total_indisponible"]
    restreinte = g["lecture_restreinte"]["lignes_total_indisponible"]
    residu = g["lecture_restreinte"]["residu_apres_taux_national"]["lignes"]
    assert residu <= restreinte <= stricte <= g["lignes"]


def test_la_methode_est_declaree(rapport):
    """Un chiffre dont la méthode n'est pas écrite n'est pas opposable."""
    methode = rapport["methode"]
    assert methode["source"]
    assert methode["canonisation"] == ("services.authentic_tariff_service._canonical_tax_code")
    assert methode["limite"], "le périmètre non couvert doit être nommé"


def test_les_etats_couvrent_toutes_les_lignes(rapport):
    """Chaque ligne reçoit un état et un seul, pour chaque taxe décisive."""
    g = rapport["global"]
    for tax, bloc in g["par_taxe"].items():
        assert sum(bloc["etats"].values()) == g["lignes"], tax


def test_le_residu_retrouve_les_cas_cites_par_la_note(rapport):
    """Recoupement indépendant : la note citait ces volumes avant la mesure.

    LE CHIFFRE ALGÉRIEN A BAISSÉ, ET C'EST UNE CORRECTION, PAS UNE DÉRIVE. Il
    valait 299 tant que la collecte passait par le miroir `conformepro.dz`, qui
    ne publie aucun bloc « Droit de douane » quand celui-ci vaut zéro. Les 299
    positions ont été relues sur l'e-service officiel de la DGD : 296 y portent
    un droit publié à 0,00 %, et trois n'en portent aucun. Ces trois-là relèvent
    du chapitre 98, que le tarif intitule « Effets personnels » : hors
    importation commerciale, aucun droit de douane n'y est perçu. Le résidu
    algérien est donc de 3 LIGNES NON LIQUIDABLES, mais de ZÉRO lacune à
    combler — la mesure compte ce qui ne se liquide pas, et ces lignes n'ont
    pas à se liquider. Elles sont laissées dans le compte plutôt que retirées
    par une exclusion « chapitre 98 » qui serait fausse ailleurs : d'un tarif à
    l'autre, ce numéro ne désigne pas la même chose.

    L'éthiopien, lui, reste à 1 368 : son collecteur a été corrigé le
    18/09/2026, mais la collecte n'a pas été refaite. Ce chiffre baissera quand
    elle le sera — et ce test le signalera.
    """
    pays = rapport["par_pays"]
    assert pays["DZA"]["lignes_residu_irreductible"] == 3
    assert pays["ETH"]["lignes_residu_irreductible"] == 1368


def test_la_mesure_est_rejouable():
    """Le script doit produire le même global qu'au commit, sans effet de bord."""
    from measure_unavailability_cost import measure

    refait = measure({"DZA"})
    assert refait["par_pays"]["DZA"]["lignes_residu_irreductible"] == 3


def test_les_deux_lectures_du_residu_sont_publiees(rapport):
    """Un seul résidu se lirait comme un constat ; il n'en est pas un.

    Servir le taux de TVA national là où le tarif est muet fait passer le
    résidu de 17,44 % à 1,25 %. Cette substitution n'a pas d'assiette
    documentée : c'est la sous-décision suspendue. Publier le seul chiffre
    optimiste donnerait pour acquis ce qui reste à trancher — et dans le sens
    qui rend la décision facile.
    """
    restreinte = rapport["global"]["lecture_restreinte"]
    admise = restreinte["residu_apres_taux_national"]
    refusee = restreinte["residu_sans_substitution"]

    assert admise["lignes"] < refusee["lignes"], (
        "la substitution ne peut qu'améliorer le résidu ; l'inverse signale une "
        "erreur de comptage"
    )
    assert refusee["lignes"] == restreinte["lignes_total_indisponible"], (
        "sans substitution, aucune ligne n'est guérie : le résidu doit égaler le "
        "compte restreint"
    )
    assert admise["hypothese"], "le chiffre optimiste doit dire sur quoi il repose"
    assert restreinte["ce_que_l_ecart_signifie"], "l'écart doit être expliqué"


def test_une_tva_specifique_n_est_pas_guerie_par_un_taux_national(rapport):
    """Le défaut qui minorait le résidu, dans le sens le plus commode.

    Le calcul tenait une TVA spécifique sans quantité pour couverte dès qu'un
    taux national existait pour le pays. Un taux ad valorem ne peut pas
    suppléer un montant unitaire dont la quantité est inconnue : ces lignes
    appartiennent au résidu.
    """
    etats = rapport["global"]["par_taxe"]["TVA"]["etats"]
    specifiques = etats.get("SPECIFIQUE_SANS_QUANTITE", 0)
    assert specifiques > 0, (
        "sans TVA spécifique dans les données, ce test ne garderait rien"
    )

    admise = rapport["global"]["lecture_restreinte"]["residu_apres_taux_national"]
    assert admise["correction_2026-09-14"], (
        "la correction doit rester consignée : elle explique pourquoi le chiffre "
        "publié auparavant était plus flatteur"
    )
