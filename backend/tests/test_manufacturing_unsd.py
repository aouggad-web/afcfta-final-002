"""
Tests de la dimension « manufacturier mesuré » (UNSD, base ODD — source UNIDO).

Le portail UNIDO répond 403 : le détail INDSTAT par division ISIC n'est pas
téléchargeable, et 32 pays sur 54 n'ont chez nous qu'une structure estimée.
L'UNSD republie librement les agrégats NATIONAUX qu'UNIDO lui fournit au titre
de la cible 9.2 — c'est ce que cette dimension porte.

Ce que ces tests verrouillent :
  • la dimension reste SÉPARÉE de manufacturing_unido — fondre du mesuré et de
    l'estimé dans une même série est précisément ce qu'on veut interdire ;
  • aucune valeur n'est fabriquée : unités, sources et natures sont portées ;
  • la route /manufacturing/measured n'est pas capturée par la route paramétrée
    /manufacturing/{country_iso3}, qui la précédait dans une première version.
"""

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import production_data as pd  # noqa: E402

_EXPECTED_SERIES = {"NV_IND_MANFPC", "SL_TLF_MANF", "NV_IND_TECH"}


def test_dimension_is_populated():
    records = pd.get_manufacturing_unsd()
    assert records, "dimension manufacturing_unsd vide"
    countries = {r["country_iso3"] for r in records}
    # La sonde du 2026-09-21 donnait 53 pays ; on garde une marge sous ce
    # chiffre pour ne pas casser au premier pays retiré par l'UNSD, tout en
    # attrapant un effondrement de couverture.
    assert len(countries) >= 45, f"couverture effondrée : {len(countries)} pays"


def test_only_expected_series_are_ingested():
    codes = {r["indicator_code"] for r in pd.get_manufacturing_unsd()}
    assert codes == _EXPECTED_SERIES, codes


def test_small_scale_industry_series_is_not_ingested():
    # NV_IND_SSIS n'est publié que pour 2 pays africains (7 points). L'ingérer
    # donnerait l'illusion d'une dimension couverte : elle est écartée tant que
    # la couverture ne progresse pas.
    codes = {r["indicator_code"] for r in pd.get_manufacturing_unsd()}
    assert "NV_IND_SSIS" not in codes


def test_every_record_carries_unit_and_source():
    for record in pd.get_manufacturing_unsd():
        assert record.get("unit"), record
        assert record.get("source_institution") == "UNSD / UNIDO", record
        assert record.get("source_url", "").startswith("https://unstats.un.org/"), record
        assert record.get("value") is not None, record


def test_units_match_their_series():
    expected = {
        "NV_IND_MANFPC": "USD",
        "SL_TLF_MANF": "percent",
        "NV_IND_TECH": "percent",
    }
    for record in pd.get_manufacturing_unsd():
        assert record["unit"] == expected[record["indicator_code"]], record


def test_per_capita_series_is_flagged_constant_price():
    # Une VAM par habitant en USD constants 2020 comparée à une VAM absolue en
    # USD courants serait une erreur de lecture : la base de prix doit être
    # portée par l'enregistrement, pas déduite du libellé.
    per_capita = pd.get_manufacturing_unsd(indicator_code="NV_IND_MANFPC")
    assert per_capita
    for record in per_capita:
        assert record["price_base_year"] == "constant 2020", record
        assert record["currency"] == "USD", record


def test_percent_series_carry_no_currency():
    for code in ("SL_TLF_MANF", "NV_IND_TECH"):
        for record in pd.get_manufacturing_unsd(indicator_code=code):
            assert record["currency"] is None, record
            assert record["price_base_year"] is None, record


def test_measured_dimension_is_kept_apart_from_estimated_one():
    # L'invariant central : les deux dimensions ne partagent aucun
    # enregistrement, et manufacturing_unido garde ses propres séries.
    data = pd.load_production_data()
    measured = data.get("manufacturing_unsd", [])
    estimated = data.get("manufacturing_unido", [])
    assert measured and estimated
    assert not ({r["indicator_code"] for r in measured} & {r["indicator_code"] for r in estimated})
    # Aucun enregistrement mesuré ne porte le drapeau d'estimation d'UNIDO.
    assert all("is_estimation" not in r for r in measured)


def test_by_country_groups_by_indicator_and_sorts_years():
    profile = pd.get_manufacturing_unsd_by_country("KEN")
    assert profile["country_iso3"] == "KEN"
    assert profile["total_records"] > 0
    assert set(profile["data_by_indicator"]) <= _EXPECTED_SERIES
    for series in profile["data_by_indicator"].values():
        years = [r["year"] for r in series]
        assert years == sorted(years), years


def test_by_country_is_case_insensitive_and_empty_for_unknown():
    assert pd.get_manufacturing_unsd_by_country("ken")["total_records"] > 0
    unknown = pd.get_manufacturing_unsd_by_country("XXX")
    assert unknown["total_records"] == 0
    assert unknown["data_by_indicator"] == {}


def test_statistics_report_the_dimension():
    dimensions = pd.get_production_statistics()["dimensions"]
    assert "manufacturing_unsd" in dimensions
    assert dimensions["manufacturing_unsd"]["total_records"] > 0


def test_data_version_stamp_covers_the_dimension():
    # Le stamp sert à périmer les analyses IA en cache. S'il ignorait cette
    # dimension, un rafraîchissement UNSD servirait des analyses ancrées sur
    # les anciens chiffres.
    import inspect

    source = inspect.getsource(pd.get_production_data_version)
    assert "manufacturing_unsd" in source


def test_measured_route_is_registered_before_the_parameterised_one():
    # FastAPI apparie dans l'ordre d'enregistrement : déclarée après
    # /manufacturing/{country_iso3}, la route /manufacturing/measured serait
    # servie comme un pays nommé « measured ».
    from routes.production import router

    paths = [r.path for r in router.routes]
    assert "/production/manufacturing/measured" in paths
    assert paths.index("/production/manufacturing/measured") < paths.index(
        "/production/manufacturing/{country_iso3}"
    )
