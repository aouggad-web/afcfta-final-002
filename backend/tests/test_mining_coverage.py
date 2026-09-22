"""
Tests de l'explication de couverture minière.

Treize pays africains n'ont aucun enregistrement minier. Leur servir un onglet
vide laisse le lecteur conclure ce qu'il veut — le plus souvent que la
plateforme a perdu la donnée. La réponse porte désormais un bloc ``coverage``
qui dit ce qui a été consulté et ce que la source en rapporte.

Ce que ces tests verrouillent :
  • tout pays reçoit une couverture, aucun n'est muet ;
  • le statut porte sur NOS SOURCES, jamais sur le pays — un pays absent
    d'USGS n'est pas déclaré sans extraction, la nuance est écrite et testée ;
  • un pays recensé par USGS mais non ingéré est signalé comme une lacune de
    collecte, pas confondu avec une absence.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import production_data as pd  # noqa: E402
from etl.usgs_world_coverage import USGS_LISTED_PRODUCERS_AFRICA  # noqa: E402

_VALID_STATUSES = {"COVERED", "LISTED_BY_USGS_NOT_INGESTED", "NOT_LISTED_BY_SOURCES"}


def test_every_country_gets_a_coverage_block():
    countries = pd.load_production_data().get("countries", [])
    assert countries
    for iso3 in countries:
        coverage = pd.get_mining_by_country(iso3).get("coverage")
        assert coverage, iso3
        assert coverage["status"] in _VALID_STATUSES, (iso3, coverage["status"])


def test_countries_with_records_are_covered():
    for iso3 in ("ZAF", "COD", "MAR"):
        result = pd.get_mining_by_country(iso3)
        assert result["total_records"] > 0, iso3
        assert result["coverage"]["status"] == "COVERED", iso3


def test_countries_without_records_are_explained_not_silent():
    # Les treize sans donnée minière : chacun doit porter une explication
    # nommant les sources, pas un objet vide.
    empty = [
        iso3
        for iso3 in pd.load_production_data().get("countries", [])
        if pd.get_mining_by_country(iso3)["total_records"] == 0
    ]
    assert empty, "aucun pays vide — le cas testé a disparu, revoir ce test"
    for iso3 in empty:
        coverage = pd.get_mining_by_country(iso3)["coverage"]
        assert coverage["status"] != "COVERED", iso3
        assert coverage["sources_consulted"], iso3
        assert coverage["note"], iso3


def test_absence_is_never_stated_as_absence_of_extraction():
    # Le point le plus important : USGS ne recense pas la production
    # artisanale ni les volumes sous son seuil. Dire « ce pays n'extrait
    # rien » serait une affirmation sur le monde que la source ne porte pas.
    coverage = pd.get_mining_by_country("BEN")["coverage"]
    assert coverage["status"] == "NOT_LISTED_BY_SOURCES"
    note = coverage["note"].lower()
    assert "ne signifie pas" in note
    assert "artisanale" in note


def test_coverage_names_its_sources_and_edition():
    coverage = pd.get_mining_by_country("SYC")["coverage"]
    joined = " ".join(coverage["sources_consulted"])
    for expected in ("USGS", "EIA", "OPEC", "World Nuclear Association"):
        assert expected in joined, expected
    assert "2025" in coverage["usgs_edition"]
    assert coverage["usgs_source_url"].startswith("https://www.sciencebase.gov/")


def test_listed_flag_matches_the_published_usgs_list():
    for iso3 in ("ZAF", "GHA", "BEN", "SYC"):
        coverage = pd.get_mining_by_country(iso3)["coverage"]
        assert coverage["listed_by_usgs"] == (iso3 in USGS_LISTED_PRODUCERS_AFRICA), iso3


def test_a_covered_country_absent_from_usgs_is_not_mislabelled():
    # Le Niger est couvert chez nous par la World Nuclear Association
    # (uranium) alors qu'USGS ne le recense pas : la couverture doit dire
    # COVERED, et le drapeau USGS rester faux sans contredire le statut.
    coverage = pd.get_mining_by_country("NER")["coverage"]
    assert coverage["status"] == "COVERED"
    assert coverage["listed_by_usgs"] is False


def test_ingestion_gap_is_distinguished_from_absence():
    # Un pays recensé par USGS mais sans enregistrement chez nous est une
    # lacune de collecte. Le statut dédié doit exister et être atteignable.
    gap = pd.get_mining_coverage("GHA", has_records=False)
    assert gap["status"] == "LISTED_BY_USGS_NOT_INGESTED"
    assert "lacune" in gap["note"].lower()


def test_usgs_list_is_plausible_and_scoped_to_africa():
    countries = set(pd.load_production_data().get("countries", []))
    assert 25 <= len(USGS_LISTED_PRODUCERS_AFRICA) <= 54
    assert USGS_LISTED_PRODUCERS_AFRICA <= countries
