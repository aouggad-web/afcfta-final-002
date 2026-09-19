"""Maurice — douze colonnes préférentielles que le socle jetait.

Le tarif mauricien (mra.mu, Customs Tariff Schedules, HS 2022) publie ses
préférences dans un champ à part, `preferential_rates`, au lieu de les mêler
aux taxes. `build_socle.py` ne lisait que les taxes : **83 176 taux étaient
collectés puis jetés à la construction**, dont la colonne ZLECAf de 6 932
positions. Maurice se servait sans aucune préférence.

CE QUE CES TESTS TIENNENT.

1. LES DOUZE RÉGIMES SONT SERVIS, ZLECAf COMPRISE. C'est le défaut constaté :
   une importation depuis un État partie se liquidait au droit NPF.

2. LES DEUX COLONNES COMESA RESTENT DISTINCTES. Le tarif publie « COMESA
   Group I » et « COMESA Group II », et leurs taux diffèrent. Les ranger sous
   un même nom ferait jouer le garde de collision et retirerait la préférence
   de ces lignes.

3. L'UNION EUROPÉENNE ET LE ROYAUME-UNI RESTENT DEUX COLONNES. Leurs taux
   coïncident aujourd'hui, mais les fondre serait une interprétation : la
   source les sépare.

4. UN RÉGIME QUE LA TABLE DU PAYS NE NOMME PAS N'EST PAS SERVI. C'est la
   garantie qui rend le reste sûr : sans elle, un régime inconnu tomberait
   dans la cascade NPF et une préférence deviendrait un droit DÛ.

5. UN TAUX QUE LA SOURCE DIT NON LIQUIDABLE EST RENDU SANS VALEUR, avec son
   motif — contingent tarifaire, droit spécifique — et non servi à zéro.
"""

from __future__ import annotations

import json
import pathlib

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[2]
SOCLE = RACINE / "backend" / "socle" / "MUS.json"

REGIMES_ATTENDUS = {
    "AFCFTA",
    "SADC",
    "COMESA_I",
    "COMESA_II",
    "COI",
    "UE",
    "UK",
    "INDE",
    "PAKISTAN",
    "CHINE",
    "TURKIYE",
    "EAU",
}


@pytest.fixture(scope="module")
def positions():
    if not SOCLE.exists():
        pytest.skip("socle non construit : python3 scripts/build_socle.py")
    return json.loads(SOCLE.read_text(encoding="utf-8"))["positions"]


def test_les_douze_regimes_sont_servis(positions):
    vus = set()
    for p in positions.values():
        vus.update(p.get("preferentiels") or {})
    assert vus == REGIMES_ATTENDUS


def test_la_zlecaf_est_servie_sur_la_quasi_totalite_du_tarif(positions):
    avec = [c for c, p in positions.items() if "AFCFTA" in (p.get("preferentiels") or {})]
    assert len(avec) > 6900


def test_les_deux_colonnes_comesa_divergent_et_restent_distinctes(positions):
    divergentes = [
        c
        for c, p in positions.items()
        if (pref := p.get("preferentiels") or {})
        and "COMESA_I" in pref
        and "COMESA_II" in pref
        and pref["COMESA_I"].get("taux") != pref["COMESA_II"].get("taux")
    ]
    # Les fondre sous « COMESA » retirerait la préférence de toutes ces lignes.
    assert len(divergentes) > 400


def test_l_union_europeenne_et_le_royaume_uni_sont_deux_colonnes(positions):
    couples = [c for c, p in positions.items() if {"UE", "UK"} <= set(p.get("preferentiels") or {})]
    assert len(couples) > 6900


def test_un_regime_hors_de_la_table_du_pays_n_est_pas_servi():
    """Le garde qui empêche une préférence de devenir un droit dû."""
    import sys

    sys.path.insert(0, str(RACINE / "scripts"))
    from build_socle import preferences_depuis_liste

    compteurs = {"preferentiels_non_nommes": 0}
    sortie = preferences_depuis_liste(
        {"SADC": "SADC"},
        [
            {"regime": "SADC", "rate_pct": 0.0},
            {"regime": "UN_REGIME_QUE_PERSONNE_NE_NOMME", "rate_pct": 0.0},
        ],
        "source de test",
        compteurs,
    )
    assert [d["_preferentiel"] for d in sortie] == ["SADC"]
    assert compteurs["preferentiels_non_nommes"] == 1


def test_un_taux_non_liquidable_est_rendu_sans_valeur(positions):
    sans_taux = [
        (c, regime)
        for c, p in positions.items()
        for regime, v in (p.get("preferentiels") or {}).items()
        if v.get("taux") is None
    ]
    # Contingents tarifaires et droits spécifiques : la source les déclare, ils
    # ne sont pas servis à zéro.
    assert len(sans_taux) > 100
