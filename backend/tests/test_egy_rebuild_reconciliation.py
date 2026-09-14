# -*- coding: utf-8 -*-
"""Le rapport de réconciliation égyptien doit nommer sa base et mesurer vraiment.

Le rapport a publié 8 793 « différences de taux » là où il n'y en avait aucune.
La cause n'était pas une erreur de données mais une comparaison sur des clés
mortes : le schéma a porté « DD »/« TVA » avant « ID »/« VAT », et la base était
interrogée sur les premières alors qu'elle ne portait plus que les secondes.
Toute position ayant un taux ressortait donc comme modifiée.

Un compteur qui ne dit pas à quoi il compare ne peut pas être contredit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "scripts"))

from build_egy_tariffs_official import (  # noqa: E402
    rates_by_canonical_code,
    reconcile,
)

REPORT = REPO_ROOT / "reports" / "EGY_REBUILD_RECONCILIATION.json"


@pytest.fixture(scope="module")
def rapport() -> dict:
    if not REPORT.exists():
        pytest.skip("rapport de réconciliation absent")
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_les_deux_generations_de_cles_donnent_le_meme_code_canonique():
    ancien = {"taxes": {"DD": {"rate": 5.0}, "TVA": {"rate": 14.0}}}
    courant = {"taxes": {"ID": {"rate": 5.0}, "VAT": {"rate": 14.0}}}
    assert rates_by_canonical_code(ancien) == rates_by_canonical_code(courant)


def test_un_changement_de_vocabulaire_n_est_pas_un_changement_de_taux():
    """Le défaut exact qui produisait 8 793 fausses différences."""
    base = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"DD": {"rate": 5.0}}}]}
    construit = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"ID": {"rate": 5.0}}}]}
    assert reconcile(base, construit)["rates"]["positions_changed"] == 0


def test_un_vrai_changement_de_taux_est_bien_detecte():
    base = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"DD": {"rate": 5.0}}}]}
    construit = {"sub_positions": [{"hs_code": "0101210000", "taxes": {"ID": {"rate": 10.0}}}]}
    resultat = reconcile(base, construit)["rates"]
    assert resultat["positions_changed"] == 1
    assert resultat["sample"][0] == {
        "code": "0101210000",
        "tax": "ID",
        "before": 5.0,
        "after": 10.0,
    }


def test_le_rapport_nomme_et_empreinte_sa_base(rapport):
    base = rapport["comparison_base"]
    assert base.get("origin"), "la base de comparaison doit être qualifiée"
    assert len(base.get("sha256", "")) == 64
    assert base.get("positions")


def test_la_base_est_designee_de_facon_rejouable(rapport):
    """Un chemin temporaire ne prouve rien : personne d'autre ne peut l'ouvrir."""
    ref = rapport["comparison_base"]["ref"]
    assert not ref.startswith("/tmp"), ref
    assert ref.startswith("git:") or (REPO_ROOT / ref).exists(), ref


def test_le_rapport_porte_un_bilan_avant_apres(rapport):
    bilan = rapport["before_after"]
    for bloc in ("positions", "rates", "families", "instruction_texts", "references"):
        assert bloc in bilan, f"bilan incomplet : {bloc} manquant"
    assert bilan["positions"]["before"] == base_count(rapport)


def base_count(rapport: dict) -> int:
    return rapport["comparison_base"]["positions"]


def test_le_compteur_trompeur_n_est_plus_publie(rapport):
    assert "rate_diff_vs_previous" not in json.dumps(rapport), (
        "ce compteur comparait sur des clés que le document ne porte plus"
    )
