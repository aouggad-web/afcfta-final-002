"""Tunisie — la colonne algérienne servie, la colonne ZLECAf refusée.

Le tarif tunisien (douane.gov.tn/tarifwebnew, Tarif Web 2026) publie ses
préférences PAR PARTENAIRE — « Code Pays 12 / ALGERIE / Taux Préférentiel » —
et non par bloc. Le socle n'en servait aucune.

CE QUE CES TESTS TIENNENT.

1. L'ALGÉRIE EST SERVIE, ET ELLE SEULE. 13 362 positions, toutes à 0 %, aucune
   au-dessus du droit NPF. Une seule colonne est nommée dans la table du pays ;
   toutes les autres sont écartées et comptées.

2. LA COLONNE ZLECAf N'EST PAS SERVIE, ET C'EST LE CŒUR DU LOT. Elle ne prend
   que quatre valeurs sur 84 712 entrées — 0, 40, 80 et 87,5 — et 69,6 % d'entre
   elles dépassent le droit NPF de leur propre position. Deux captures du
   portail le montrent sur la MÊME valeur : bananes fraîches, droit 50 %,
   colonne 40 % ; huile moteur, droit 0 %, colonne 40 %. Un taux suit le droit
   de sa position, un coefficient de démantèlement ne le suit pas — mais la
   source intitule la colonne « Taux Préférentiel ». La servir ferait payer
   40 % de la valeur CIF sur 20 149 lignes que le tarif laisse en franchise.

3. LA COLONNE EST MONTRÉE, JAMAIS APPLIQUÉE. Comme pour les blocs : le tarif
   de destination publie une colonne au nom du pays d'origine, la franchise
   reste subordonnée aux règles d'origine que ce moteur ne vérifie pas.

4. ELLE N'EST MONTRÉE QU'À L'ORIGINE QU'ELLE NOMME. Une importation marocaine
   ne voit pas la colonne algérienne.
"""

from __future__ import annotations

import json
import pathlib

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[2]
SOCLE = RACINE / "backend" / "socle" / "TUN.json"
CRAWL = RACINE / "backend" / "data" / "crawled" / "TUN_tariffs.json"


@pytest.fixture(scope="module")
def positions():
    if not SOCLE.exists():
        pytest.skip("socle non construit : python3 scripts/build_socle.py")
    return json.loads(SOCLE.read_text(encoding="utf-8"))["positions"]


@pytest.fixture(scope="module")
def position_algerienne(positions):
    """Une position portant la colonne algérienne ET un droit NPF non nul."""
    for code, p in positions.items():
        if not isinstance(p, dict):
            continue
        if (p.get("preferentiels") or {}).get("DZA") and next(
            (d.get("taux") for d in p.get("droits", []) if d.get("code") == "DD"), 0
        ):
            return code, p
    pytest.skip("aucune position algérienne avec droit NPF non nul")


def test_l_algerie_est_le_seul_regime_servi(positions):
    vus = set()
    for p in positions.values():
        if isinstance(p, dict):
            vus.update(p.get("preferentiels") or {})
    assert vus == {"DZA"}


def test_la_colonne_algerienne_est_entierement_a_zero(positions):
    taux = {
        v.get("taux")
        for p in positions.values()
        if isinstance(p, dict)
        for v in (p.get("preferentiels") or {}).values()
    }
    assert taux == {0.0}


def test_aucune_preference_ne_depasse_le_droit_npf(positions):
    fautives = []
    for code, p in positions.items():
        if not isinstance(p, dict):
            continue
        npf = next((d.get("taux") for d in p.get("droits", []) if d.get("code") == "DD"), None)
        for regime, v in (p.get("preferentiels") or {}).items():
            if npf is not None and v.get("taux") is not None and v["taux"] > npf:
                fautives.append((code, regime, npf, v["taux"]))
    # Une « préférence » au-dessus du droit commun n'est pas une préférence.
    assert fautives == []


def test_la_colonne_zlecaf_n_est_pas_servie(positions):
    vus = set()
    for p in positions.values():
        if isinstance(p, dict):
            vus.update(p.get("preferentiels") or {})
    assert "AFCFTA" not in vus and "ZLECAF" not in vus


def test_la_colonne_zlecaf_du_crawl_est_bien_celle_qui_est_refusee():
    """Le motif du refus, mesuré sur la source elle-même.

    Si ce test tombe parce que la colonne est devenue cohérente, c'est que la
    source a changé : il faut alors REVOIR le refus, pas ajuster le test.
    """
    if not CRAWL.exists():
        pytest.skip("crawl absent")
    donnees = json.loads(CRAWL.read_text(encoding="utf-8"))
    valeurs, au_dessus, total = set(), 0, 0
    for ligne in donnees["sub_positions"]:
        npf = next(
            (t.get("rate_pct") for t in ligne.get("taxes_import") or [] if t.get("code") == "DD"),
            None,
        )
        for pref in ligne.get("preferences") or []:
            if pref.get("zone") != "ZLECAf":
                continue
            try:
                v = float(str(pref["rate"]).replace("%", "").strip())
            except (TypeError, ValueError):
                continue
            valeurs.add(v)
            total += 1
            if npf is not None and v > npf:
                au_dessus += 1
    assert valeurs == {0.0, 40.0, 80.0, 87.5}
    assert au_dessus / total > 0.65


def test_la_colonne_est_montree_a_l_origine_qu_elle_nomme(position_algerienne):
    from services.preference import simulations_regionales

    _code, p = position_algerienne
    sims = simulations_regionales(p, "TUN", "DZA")
    assert [s["regime"] for s in sims] == ["DZA"]
    assert sims[0]["taux_publie_pct"] == 0.0
    assert sims[0]["eligibilite"] == "COLONNE_NOMMEE_POUR_CE_PAYS_PAR_LA_SOURCE"


def test_elle_est_montree_jamais_appliquee(position_algerienne):
    from services.preference import simulations_regionales

    _code, p = position_algerienne
    sims = simulations_regionales(p, "TUN", "DZA")
    assert sims[0]["applique"] is False
    assert "règles d'origine" in sims[0]["reserve"]


def test_une_autre_origine_ne_voit_pas_la_colonne_algerienne(position_algerienne):
    """Contrôle négatif : sans lui, la colonne profiterait à tout le monde."""
    from services.preference import simulations_regionales

    _code, p = position_algerienne
    assert simulations_regionales(p, "TUN", "MAR") == []
