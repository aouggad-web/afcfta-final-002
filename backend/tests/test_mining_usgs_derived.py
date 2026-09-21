"""
Minerais dérivés du fichier USGS — ce que la dérivation doit garantir.

Les minerais vivaient dans des dictionnaires Python recopiés à la main depuis
les publications USGS : 30 commodités, là où le fichier machine en publie 46
pour l'Afrique. L'écart ne tenait pas à la disponibilité — le fichier est
public — mais au coût de la recopie, qui porte en plus une classe d'erreur
invisible : un chiffre mal transcrit ne se voit pas.

24 commodités sont désormais DÉRIVÉES de ``MCS2025_World_Data.csv``. Ces tests
verrouillent les trois décisions qui rendent cette dérivation honnête.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402
from etl.mining_extended import (  # noqa: E402
    MINING_EXTENDED,
    MINING_YEAR_2024,
    build_mcs_derived,
)
from etl.mining_usgs_mcs import MCS_DERIVED  # noqa: E402


@pytest.fixture(scope="module")
def records():
    return build_mcs_derived()


def test_the_derivation_brings_real_volume(records):
    assert len(MCS_DERIVED) >= 20, "la dérivation s'est vidée"
    assert len(records) >= 80


def test_no_commodity_competes_with_a_curated_one():
    """Deux séries pour le même minerai, c'est deux classements concurrents.

    Rien à l'écran ne dirait lequel fait foi. Le générateur exclut donc toute
    commodité déjà couverte par les tables écrites à la main — y compris sous
    un autre nom (« Iron Ore » de l'USGS contre notre « Iron ore »).
    """
    curated = set(MINING_EXTENDED) | set(MINING_YEAR_2024)
    assert not (set(MCS_DERIVED) & curated), set(MCS_DERIVED) & curated
    # Les alias, qui ne se voient pas par simple intersection.
    lowered = {c.lower() for c in curated}
    for commodity in MCS_DERIVED:
        assert commodity.lower() not in lowered, commodity


def test_one_measure_per_commodity():
    """« Mine production » et « Refinery production » ne se comparent pas.

    Classer ensemble la production minière d'un pays et la production de
    raffinerie d'un autre donnerait un palmarès faux sans que rien ne le
    signale. Une seule mesure par commodité, et elle est inscrite.
    """
    for commodity, spec in MCS_DERIVED.items():
        assert spec["measure"], commodity
        assert spec["unit"], commodity


def test_the_measure_reaches_each_record(records):
    # La mesure doit survivre jusqu'à l'enregistrement servi : un consommateur
    # qui agrège plusieurs commodités doit pouvoir la lire.
    for rec in records:
        assert rec["usgs_table_name"], rec
        assert "—" in rec["usgs_table_name"], rec["usgs_table_name"]


def test_2024_is_flagged_as_an_estimate(records):
    """MCS 2025 publie 2023 révisé et 2024 ESTIMÉ. Les confondre ferait passer
    une estimation pour une observation."""
    for rec in records:
        assert rec["is_estimate"] is (rec["year"] >= 2024), rec


def test_every_record_carries_its_source(records):
    for rec in records:
        assert rec["source_institution"] == "USGS"
        assert "Mineral Commodity Summaries" in rec["source_dataset"]
        assert rec["source_url"].startswith("https://")
        assert isinstance(rec["value"], (int, float)) and rec["value"] > 0


def test_no_withheld_cell_became_a_zero(records):
    """L'USGS note ``W`` ce qu'il retient par secret statistique.

    C'est une absence de publication, surtout pas un zéro. Une valeur nulle
    dans le jeu signifierait qu'on a lu « pas de chiffre » comme « rien
    produit » — exactement l'inversion que tout ce module combat.
    """
    assert all(rec["value"] > 0 for rec in records)


def test_countries_are_african_iso3(records):
    from etl.iso3_m49 import ISO3_TO_M49

    for rec in records:
        assert rec["country_iso3"] in ISO3_TO_M49, rec["country_iso3"]


def test_each_derived_commodity_is_reachable_by_its_hs_code():
    """Le pont doit répondre, pas seulement exister.

    L'invariant du dépôt exige qu'une commodité ait UN mapping. Il ne vérifie
    pas qu'interroger ce code rende bien cette commodité — or le matcher prend
    le préfixe le plus long, et un HS4 ajouté sur une position déjà occupée
    serait accepté par l'invariant tout en restant inatteignable.
    """
    from services.production_capacity_service import _match_commodity

    expected = {
        "710231": "Gemstones",
        "280530": "Rare earths",
        "2611": "Tungsten",
        "253010": "Vermiculite",
        "720293": "Niobium",
        "252329": "Cement",
        "280480": "Arsenic",
        "2814": "Nitrogen(fixed) - Ammonia",
    }
    for hs, label in expected.items():
        match = _match_commodity(hs)
        assert match and match[1] == label, (hs, match)


def test_no_pre_existing_code_was_masked():
    """Ajouter un HS6 ne doit pas détourner le HS4 voisin.

    Ces cinq codes étaient déjà attribués ; les nouveaux mappings passent
    volontairement par le HS6 pour ne pas les capter. Le vérifier ici évite
    qu'une future addition les masque en silence — l'écran continuerait de
    répondre, mais sur une autre commodité.
    """
    from services.production_capacity_service import _match_commodity

    for hs, label in (
        ("2530", "Perlite"),
        ("2615", "Tantalum"),
        ("7102", "Diamonds"),
        ("7108", "Gold"),
        ("2804", "Manufacture of chemicals"),
    ):
        match = _match_commodity(hs)
        assert match and match[1] == label, (hs, match)
