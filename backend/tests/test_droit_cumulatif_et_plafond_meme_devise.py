"""Deux défauts du moteur, corrigés ensemble.

1. Zimbabwe (SI 203/2022) : « 40% + US$0.50/L » — 356 droits cumulatifs —
   n'étaient liquidés que sur leur part ad valorem, et le total se déclarait
   COMPLET. Les deux composantes sont dues ; sans quantité ou sans taux de
   change, le droit entier reste indisponible. Même forme aux Seychelles
   (« 15%+SCR5.13/kg », 5 droits).
2. CEMAC (Cameroun, Guinée équatoriale) : la redevance informatique plafonnée
   à 15 000 XAF réclamait un taux de change même sur une valeur déclarée en XAF.
"""

import json
import os

import pytest

from services.calcul import (
    COMPLET,
    MANQUE_CHANGE,
    MANQUE_QUANTITE,
    MANQUE_REGLE_COMPOSEE,
    calculer,
)

SOCLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "socle")


def _ligne(resultat, code="DD", regime="npf"):
    return next(l for l in resultat[regime]["lignes"] if l["code"] == code)


def _cumulatif():
    """Yaourt zimbabwéen 0403.20.00 : « 40% + US$0.50/L »."""
    return {
        "designation": "Yogurt",
        "droits": [
            {
                "code": "DD",
                "famille": "droit",
                "taux": 40.0,
                "assiette": "CIF",
                "cumulatif": True,
                "expression_brute": "40% + US$0.50/L",
                "specifique": {"montant": 0.5, "unite_monetaire": "usd", "unite_quantite": "l", "brut": "0.50 USD/L"},
            }
        ],
    }


def test_les_deux_composantes_d_un_droit_cumulatif_sont_dues():
    r = calculer(_cumulatif(), 1000, quantite=100, devise_cif="USD", devise_position="ZWG")
    ligne = _ligne(r)
    assert ligne["montant"] == 450.0  # 40 % × 1 000 + 0,50 × 100
    assert ligne["composantes"]["specifique_montant"] == 50.0
    assert r["npf"]["etat"] == COMPLET


def test_sans_quantite_le_droit_cumulatif_n_est_pas_reduit_a_sa_part_ad_valorem():
    r = calculer(_cumulatif(), 1000, devise_cif="USD", devise_position="ZWG")
    assert _ligne(r)["statut"] == MANQUE_QUANTITE
    assert _ligne(r)["montant"] is None
    assert r["npf"]["etat"] != COMPLET


def test_une_part_specifique_en_dollars_exige_un_change_sur_une_valeur_en_zwg():
    r = calculer(_cumulatif(), 1000, quantite=100, devise_position="ZWG")
    assert _ligne(r)["statut"] == MANQUE_CHANGE
    r = calculer(_cumulatif(), 1000, quantite=100, taux_de_change=27.0, devise_position="ZWG")
    assert _ligne(r)["montant"] == 400.0 + 0.5 * 100 * 27.0


def test_deux_composantes_sans_regle_ne_sont_jamais_reduites_a_l_ad_valorem():
    """Garde-fou : un droit à deux composantes non marqué n'est plus servi
    sur sa seule part ad valorem."""
    position = _cumulatif()
    del position["droits"][0]["cumulatif"]
    r = calculer(position, 1000, quantite=100, devise_cif="USD")
    assert _ligne(r)["statut"] == MANQUE_REGLE_COMPOSEE


def test_une_franchise_remplace_le_droit_cumulatif_entier():
    r = calculer(_cumulatif(), 1000, devise_position="ZWG", taux_preferentiels={"DD": 0})
    assert _ligne(r, regime="preference")["montant"] == 0.0
    assert r["preference"]["etat"] == COMPLET


def _redevance():
    return {
        "designation": "essai",
        "droits": [
            {
                "code": "RI",
                "famille": "communautaire",
                "taux": 0.45,
                "assiette": "CIF",
                "plafond": {"montant": 15000.0, "devise": "XAF"},
            }
        ],
    }


@pytest.mark.parametrize("devises", [{"devise_cif": "XAF"}, {"devise_position": "XAF"}])
def test_un_plafond_en_xaf_sur_une_valeur_en_xaf_ne_reclame_aucun_change(devises):
    r = calculer(_redevance(), 10_000_000, **devises)
    ligne = _ligne(r, "RI")
    assert ligne["base"] == 15000.0
    assert ligne["montant"] == 67.5
    assert r["npf"]["etat"] == COMPLET


def test_un_plafond_en_xaf_sur_une_valeur_en_euros_exige_le_change():
    r = calculer(_redevance(), 10_000, devise_cif="EUR", devise_position="XAF")
    assert _ligne(r, "RI")["statut"] == MANQUE_CHANGE
    r = calculer(_redevance(), 10_000, devise_cif="EUR", devise_position="XAF", taux_de_change=1 / 655.957)
    assert _ligne(r, "RI")["base"] == pytest.approx(15000 / 655.957, abs=1e-3)


besoin_socle = pytest.mark.skipif(
    not os.path.exists(os.path.join(SOCLE, "ZWE.json")),
    reason="socle absent (gitignoré) : reconstruire avec scripts/build_socle.py",
)


@besoin_socle
@pytest.mark.parametrize(("iso3", "attendus"), [("ZWE", 356), ("SYC", 5)])
def test_le_socle_marque_les_droits_cumulatifs_de_la_source(iso3, attendus):
    with open(os.path.join(SOCLE, f"{iso3}.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    cumulatifs = [d for p in positions.values() for d in p["droits"] if d.get("cumulatif")]
    assert len(cumulatifs) == attendus
    assert all("+" in d["expression_brute"] for d in cumulatifs)


@besoin_socle
def test_la_devise_ecrite_avant_le_montant_est_lue():
    """« SCR5.13/kg » (Seychelles) ; « SCR96perpackof200 » reste illisible."""
    with open(os.path.join(SOCLE, "SYC.json"), encoding="utf-8") as f:
        positions = json.load(f)["positions"]
    specifique = positions["02032100"]["droits"][0]["specifique"]
    assert (specifique["montant"], specifique["unite_monetaire"], specifique["unite_quantite"]) == (5.13, "scr", "kg")
