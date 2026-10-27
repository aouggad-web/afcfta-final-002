"""Congo : centimes additionnels à la TVA et circulaire n° 0138/MFBPP-CAB
(fiche COG_mesures_nationales_2026-10-27).

- Centimes additionnels : 5 % du montant de la TVA (loi TVA art. 36 B).
- Circulaire 0138 (jusqu'au 31/12/2026) : droit de douane 5 % ; TVA exonérée
  (viandes, poissons, blé, maïs, huile de palme) ou à 5 % (lait, riz, sel) ;
  poissons de luxe soumis aux droits d'accises exclus.
"""

import json
import os

import pytest

from services.calcul import calculer

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "COG.json")), reason="socle absent (gitignoré)"
)


@pytest.fixture(scope="module")
def positions():
    with open(os.path.join(SOCLE, "COG.json"), encoding="utf-8") as f:
        return json.load(f)["positions"]


def _lignes(positions, code):
    r = calculer(positions[code], 100.0)
    return r, {l["code"]: l for l in r["npf"]["lignes"]}


def test_les_centimes_additionnels_valent_5_pourcent_de_la_tva(positions):
    """Chevaux 0101.10.10 : DD 5 %, TVA 18 % sur 105, centimes 5 % de 18,9."""
    r, l = _lignes(positions, "01011010")
    assert l["TVA"]["montant"] == pytest.approx(18.9)
    assert l["CATVA"]["montant"] == pytest.approx(0.945)
    assert r["npf"]["etat"] == "COMPLET"


def test_toute_position_avec_tva_porte_les_centimes(positions):
    assert all(
        any(d["code"] == "CATVA" for d in p["droits"])
        for p in positions.values()
        if any(d["code"] == "TVA" for d in p["droits"])
    )


@pytest.mark.parametrize(
    "code", ["02011000", "03034100", "03055110", "03055999", "10011090", "10059000", "15119000"]
)
def test_premiere_variante_droit_5_et_tva_exoneree(positions, code):
    _, l = _lignes(positions, code)
    assert l["DD"]["taux_pct"] == 5.0 and "0138" in l["DD"]["note"]
    assert l["TVA"]["taux_pct"] == 0.0 and l["CATVA"]["montant"] == 0.0


@pytest.mark.parametrize("code", ["04011000", "04022100", "10062000", "10064000", "25010011"])
def test_seconde_variante_droit_5_et_tva_5(positions, code):
    _, l = _lignes(positions, code)
    assert l["DD"]["taux_pct"] == 5.0
    assert l["TVA"]["taux_pct"] == 5.0 and l["TVA"]["montant"] == pytest.approx(5.25)


@pytest.mark.parametrize("code", ["03031100", "03032200"])
def test_les_poissons_de_luxe_soumis_aux_accises_sont_exclus(positions, code):
    """Saumons : droit d'accises, donc hors circulaire. Celui du 0303.22.00
    vient de la loi de finances, pas du crawl : l'exclusion se lit après."""
    droits = {d["code"]: d for d in positions[code]["droits"]}
    assert "DA" in droits
    assert droits["DD"]["taux"] == 20.0 and "0138" not in (droits["DD"].get("note") or "")
    assert droits["TVA"]["taux"] == 18.0
