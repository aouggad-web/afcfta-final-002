"""Un verbatim qui n'est pas un taux ne devient jamais un taux.

« Rs 1,692.50/L Ab alco* » (accise mauricienne, 189 droits) était lu
1,692 % ; « 0.0099 MZN Per 1 KG » (plancher ICE mozambicain, 80 droits)
0,0099 %. Aucun montant n'en sortait — l'assiette manque — mais le
calculateur affichait ces chiffres dans la colonne des taux.
"""

import importlib.util
import json
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOCLE = os.path.join(REPO, "backend", "socle")
spec = importlib.util.spec_from_file_location("build_socle", os.path.join(REPO, "scripts", "build_socle.py"))
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)


@pytest.mark.parametrize(
    "brut,taux",
    [
        ("20", 20.0),
        ("5 %", 5.0),
        ("Free", 0.0),
        ("Rs 1,692.50/L Ab alco*", None),
        ("15 cents per gram of sugar", None),
        ("0.0099 MZN Per 1 KG", None),
    ],
)
def test_seul_un_taux_verbatim_devient_un_taux(brut, taux):
    droit = bs.droits_depuis_liste([{"code": "EXC", "rate_pct": None, "raw_value": brut}], "essai")[0]
    assert droit["taux"] == taux


@pytest.mark.skipif(not os.path.exists(os.path.join(SOCLE, "MUS.json")), reason="socle absent (gitignoré)")
def test_le_socle_ne_porte_plus_ces_faux_taux():
    with open(os.path.join(SOCLE, "MUS.json"), encoding="utf-8") as f:
        accise = [d for d in json.load(f)["positions"]["22082011"]["droits"] if d["code"] == "EXC"][0]
    assert accise.get("taux") is None
    with open(os.path.join(SOCLE, "MOZ.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    planchers = [d for p in positions.values() for d in p["droits"] if d["code_source"] == "ICE_VAL_MIN"]
    assert len(planchers) == 80 and all(d.get("taux") is None for d in planchers)


def test_un_taux_negatif_n_existe_pas():
    """« -1 » marque un taux variable (accise DA, CEMAC) : jamais -1 %."""
    assert bs.lire_taux(-1) is None
    assert bs.lire_taux("-1") is None
    droit = bs.droits_depuis_liste([{"tax_code": "DA", "rate": -1, "base": "CIF"}], "essai")[0]
    assert droit["taux"] is None


def test_un_montant_specifique_n_est_pas_un_pourcentage():
    """Côte d'Ivoire : PSV « 1000 », rate_type specific — pas 1 000 %."""
    droit = bs.droits_depuis_liste(
        [{"tax_code": "PSV", "rate": 1000.0, "rate_type": "specific", "base": "variable"}], "essai"
    )[0]
    assert droit["taux"] is None


@pytest.mark.skipif(not os.path.exists(os.path.join(SOCLE, "CMR.json")), reason="socle absent (gitignoré)")
@pytest.mark.parametrize("iso3", ["CMR", "GNQ", "CAF", "COG", "GAB", "TCD"])
def test_aucune_accise_negative_dans_la_cemac(iso3):
    from services.calcul import COMPLET, calculer

    with open(os.path.join(SOCLE, f"{iso3}.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    negatifs = [d for p in positions.values() for d in p["droits"] if (d.get("taux") or 0) < 0]
    assert negatifs == []
    r = calculer(positions["03026990"], 1000, devise_cif="XAF")
    accise = [ligne for ligne in r["npf"]["lignes"] if ligne["code"] == "DA"][0]
    assert accise["montant"] is None and r["npf"]["etat"] != COMPLET
