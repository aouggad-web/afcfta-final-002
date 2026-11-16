"""Zone arabe à l'exportation algérienne : la Tunisie et la Libye publient,
ligne par ligne, le taux qu'elles accordent à l'Algérie (fiche
DZA_GZALE_export_2026-11-02.json)."""

import os

import pytest

from services import socle
from services.preference import (
    GZALE_MEMBRES_AFRICAINS,
    _choisir_gzale_ou_zlecaf,
    simulations_regionales,
    taux_preferentiels,
)

besoin_socle = pytest.mark.skipif(
    not os.path.exists(socle.MANIFESTE), reason="socle absent : python3 scripts/build_socle.py"
)

REFUS = {"applique": False, "regime": "ZLECAF", "statut": "NOT_AVAILABLE", "note": "", "taux": {}}


def _position(dd, colonne=None, valeur=None):
    position = {"droits": [{"code": "DD", "taux": dd}, {"code": "TVA", "taux": 19}]}
    if colonne:
        position["preferentiels"] = {colonne: valeur}
    return position


def test_tunisie_sert_la_colonne_algerie_publiee():
    r = _choisir_gzale_ou_zlecaf(_position(36, "DZA", {"taux": 0.0}), "TUN", "DZA", REFUS)
    assert r["applique"] is True and r["regime"] == "GZALE"
    assert r["code_bloc"] == "ZALE"
    assert r["taux"] == {"DD": {"taux": 0.0}}
    assert "Tarif Web 2026" in r["perimetre"]["DD"]


def test_tunisie_sans_colonne_reste_au_npf():
    assert _choisir_gzale_ou_zlecaf(_position(36), "TUN", "DZA", REFUS) is REFUS


@pytest.mark.parametrize("origine", ["EGY", "MAR"])
def test_tunisie_ne_sert_que_l_origine_algerienne(origine):
    # Le Tarif Web publie aussi des taux pour l'Égypte et le Maroc ; ils restent
    # une information (note_zale), hors du périmètre de ce lot.
    position = _position(36, "DZA", {"taux": 0.0})
    assert _choisir_gzale_ou_zlecaf(position, "TUN", origine, REFUS) is REFUS


@pytest.mark.parametrize("origine", sorted(GZALE_MEMBRES_AFRICAINS - {"LBY"}))
def test_libye_sert_la_colonne_ligue_arabe_aux_membres_africains(origine):
    r = _choisir_gzale_ou_zlecaf(_position(30, "LIGUE_ARABE", {"taux": 0.0}), "LBY", origine, REFUS)
    assert r["regime"] == "GZALE"
    assert r["taux"] == {"DD": {"taux": 0.0}}
    assert "جامعة الدول العربية" in r["perimetre"]["DD"]


@pytest.mark.parametrize("origine", ["MRT", "COM", "DJI", "SOM", "NGA"])
def test_libye_ne_sert_pas_les_origines_hors_zone(origine):
    # Membres de la Ligue hors GZALE : la composition de la colonne libyenne
    # n'est établie par aucune source, rien n'est servi.
    position = _position(30, "LIGUE_ARABE", {"taux": 0.0})
    assert _choisir_gzale_ou_zlecaf(position, "LBY", origine, REFUS) is REFUS


@besoin_socle
def test_socle_tunisie_origine_algerie():
    positions = socle.charger("TUN")["positions"]
    code = next(c for c, p in positions.items() if "DZA" in (p.get("preferentiels") or {})
                and next(d["taux"] for d in p["droits"] if d["code"] == "DD"))
    r = taux_preferentiels(positions[code], "TUN", "DZA", code)
    assert r["regime"] == "GZALE" and r["applique"] is True
    assert "n'est pas calculé" not in r["zlecaf"]["note"]
    # Servie, la colonne n'est plus montrée en simulation.
    assert simulations_regionales(positions[code], "TUN", "DZA") == []


@besoin_socle
def test_socle_libye_origine_algerie():
    positions = socle.charger("LBY")["positions"]
    code = next(c for c, p in positions.items() if "LIGUE_ARABE" in (p.get("preferentiels") or {}))
    r = taux_preferentiels(positions[code], "LBY", "DZA", code)
    assert r["regime"] == "GZALE" and r["applique"] is True
