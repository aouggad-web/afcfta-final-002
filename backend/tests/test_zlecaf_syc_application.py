"""Seychelles : le S.I. 113 of 2022 porte l'instrument, les origines et le barème.

Fiche : SYC_application_2026-09-28.json. Ce fichier verrouille : les 38
origines de la Schedule VI, le refus d'une origine hors liste, et la lecture
de la sous-colonne AfCFTA de l'année — rien au-delà de 2026.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from services.preference import taux_preferentiels
from services.zlecaf_implementation_registry import APPLIED, RECORDS, implementation_decision
from services.zlecaf_schedule_syc import ORIGINES_SCHEDULE_VI, colonne_de_l_annee

CRAWL = Path(__file__).resolve().parents[1] / "data" / "crawled" / "SYC_tariffs.json"

#: Ligne réelle du S.I. 113 of 2022 : noix de coco, NPF 25 %, AfCFTA
#: 20 / 15 / 10 / 5 / 0 % de 2022 à 2026.
CODE = "08011200"


def _position() -> dict:
    return {
        "droits": [{"code": "DD", "taux": 25.0, "assiette": "CIF", "famille": "droit"}],
        "preferentiels": {
            "AFCFTA_2022": {"taux": 20.0},
            "AFCFTA_2023": {"taux": 15.0},
            "AFCFTA_2024": {"taux": 10.0},
            "AFCFTA_2025": {"taux": 5.0},
            "AFCFTA_2026": {"taux": 0.0},
            "AFCFTA": {"taux": 0.0},
        },
    }


def test_les_38_origines_sont_celles_de_la_schedule_vi():
    assert len(ORIGINES_SCHEDULE_VI) == 38
    crawl = json.loads(CRAWL.read_text(encoding="utf-8"))
    assert len(crawl["notes_legales"]["etats_zlecaf_schedule_vi"]) == 38


def test_le_registre_applique_la_schedule_vi():
    record = RECORDS["SYC"]
    assert record.status == APPLIED
    assert record.accepted_origins == ORIGINES_SCHEDULE_VI
    assert record.effective_from == "2022-11-01"


def test_une_origine_hors_schedule_vi_reste_au_npf():
    # La Tanzanie a ratifié mais ne figure pas à la Schedule VI.
    assert implementation_decision("SYC", "TZA")["applied"] is False
    resultat = taux_preferentiels(_position(), "SYC", "TZA", CODE)
    assert resultat["applique"] is False
    assert resultat["taux"] == {}


def test_la_colonne_servie_est_celle_de_l_annee():
    annee = datetime.date.today().year
    resultat = taux_preferentiels(_position(), "SYC", "KEN", CODE)
    if colonne_de_l_annee(annee) is None:
        assert resultat["applique"] is False
    else:
        assert resultat["applique"] is True
        attendu = _position()["preferentiels"][f"AFCFTA_{annee}"]["taux"]
        assert resultat["taux"] == {"DD": {"taux": attendu}}


@pytest.mark.parametrize(
    "annee, attendu", [(2021, None), (2022, "AFCFTA_2022"), (2026, "AFCFTA_2026"), (2027, None)]
)
def test_aucune_colonne_hors_2022_2026(annee, attendu):
    assert colonne_de_l_annee(annee) == attendu
