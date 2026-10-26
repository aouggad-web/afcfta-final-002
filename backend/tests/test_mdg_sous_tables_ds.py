"""Madagascar, tarif national 2026 : les sous-tables à droit de sortie (`UQN DD
TVA [APEi] UQN DS`) sont lues par `scripts/parse_tarif_mdg_2026.py`. Écartées
avec les TPP/TVP, elles faisaient perdre 308 positions à l'import aussi (sel,
minerais, pierres et métaux précieux, chapitres 75 et 81)."""

import json
from pathlib import Path

import pytest

FICHIER = Path(__file__).resolve().parents[1] / "data" / "crawled" / "MDG_tariffs.json"


@pytest.fixture(scope="module")
def tarif():
    donnees = json.loads(FICHIER.read_text(encoding="utf-8"))
    return donnees, {p["hs_code"]: p for p in donnees["sub_positions"]}


def test_plus_aucune_sous_table_ds_ecartee(tarif):
    donnees, _ = tarif
    assert not [e for e in donnees["non_collected"] if "DS" in e["reason"]]


def test_position_recuperee_a_ses_droits_d_import(tarif):
    _, positions = tarif
    sel = positions["25010011"]
    assert (sel["taxes"]["DD"]["rate"], sel["taxes"]["TVA"]["rate"]) == (20.0, 20.0)


def test_droit_de_sortie_lu_avec_son_assiette(tarif):
    _, positions = tarif
    (ds,) = positions["75021000"]["taxes_export"]
    assert (ds["code"], ds["rate"], ds["assiette_publiee"]) == ("DS", 10.0, "Valeur")


def test_ds_en_blanc_n_est_pas_servi(tarif):
    """Bijouterie (7113) : la colonne DS est vide au tarif — rien n'est servi."""
    _, positions = tarif
    assert "taxes_export" not in positions["71131100"]
