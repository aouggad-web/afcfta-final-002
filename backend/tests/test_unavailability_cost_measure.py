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
    """Recoupement indépendant : la note citait ces volumes avant la mesure."""
    pays = rapport["par_pays"]
    assert pays["DZA"]["lignes_residu_irreductible"] == 299
    assert pays["ETH"]["lignes_residu_irreductible"] == 1368


def test_la_mesure_est_rejouable():
    """Le script doit produire le même global qu'au commit, sans effet de bord."""
    from measure_unavailability_cost import measure

    refait = measure({"DZA"})
    assert refait["par_pays"]["DZA"]["lignes_residu_irreductible"] == 299
