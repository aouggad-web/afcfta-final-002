"""
Tests de la cascade « données Banque Mondiale live » pour les Profils Pays et
le module Statistiques (voir donnees.banquemondiale.org).

Contexte : PIB, PIB/habitant et population des Profils Pays et du module
Statistiques (comparaison, Top 10 PIB) restaient sourcés exclusivement sur le
dataset curé statique (country_data.REAL_COUNTRY_DATA, figé à sa date de
curation), alors que le dataset BM auto-actualisé
(data/json/worldbank_data_latest.json) est rafraîchi par l'ETL et existait déjà
pour inflation/chômage. Seule l'inflation/le chômage suivaient la cascade
« BM live -> curé -> null ». Ces tests verrouillent l'extension de cette même
cascade à GDP/GDP-per-capita/Population/croissance 2024, et la reconstruction
en direct du Top 10 PIB (l'ancienne table figée portait un classement erroné
pour le Maroc).

Le dataset BM est isolé par test (monkeypatch de wb_macro_service._DATASET_PATH
+ reset_cache) pour ne jamais dépendre des valeurs réelles, qui évoluent avec
chaque run de l'ETL.
"""

import json
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from services import wb_macro_service  # noqa: E402


def _write_wb_dataset(path, data):
    payload = {
        "metadata": {
            "source": "World Bank API",
            "updated_at": "2026-07-13T00:00:00",
            "indicators": ["GDP", "GDP_per_capita", "Population", "GDP_growth"],
        },
        "data": data,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def synthetic_wb(tmp_path, monkeypatch):
    """Bascule wb_macro_service sur un fichier BM synthétique et déterministe."""
    dataset = tmp_path / "worldbank_data_latest.json"
    data = {
        # DZA reçoit des valeurs BM volontairement très différentes des
        # valeurs curées (269.31 Md$ / 45 606 000 hab.) pour prouver que la
        # cascade privilégie bien le dataset BM live.
        "DZA": {
            "name": "Algeria",
            "indicators": {
                "GDP": {"2023": 900_000_000_000.0, "2024": 999_000_000_000.0},
                "GDP_per_capita": {"2024": 21000.0},
                "Population": {"2024": 47_500_000},
                "GDP_growth": {"2024": 9.9},
            },
        },
        "NGA": {
            "name": "Nigeria",
            "indicators": {
                "GDP": {"2024": 500_000_000_000.0},
                "GDP_per_capita": {"2024": 2000.0},
                "Population": {"2024": 220_000_000},
                "GDP_growth": {"2024": 3.0},
            },
        },
        "ZAF": {
            "name": "South Africa",
            "indicators": {
                "GDP": {"2024": 300_000_000_000.0},
                "GDP_per_capita": {"2024": 4800.0},
                "Population": {"2024": 60_000_000},
                "GDP_growth": {"2024": 1.0},
            },
        },
        # COM volontairement ABSENT du dataset BM -> doit se rabattre sur le
        # dataset curé (country_data.REAL_COUNTRY_DATA) sans jamais planter.
    }
    _write_wb_dataset(dataset, data)
    monkeypatch.setattr(wb_macro_service, "_DATASET_PATH", dataset)
    wb_macro_service.reset_cache()
    yield dataset
    wb_macro_service.reset_cache()


# ── wb_macro_service : nouveaux helpers ────────────────────────────────────


def test_get_series_returns_full_year_map(synthetic_wb):
    series = wb_macro_service.get_series("DZA", "gdp_usd")
    assert series == {2023: 900_000_000_000.0, 2024: 999_000_000_000.0}


def test_get_series_empty_for_unknown_country_or_indicator(synthetic_wb):
    assert wb_macro_service.get_series("XXX", "gdp_usd") == {}
    assert wb_macro_service.get_series("DZA", "not_a_field") == {}


def test_all_countries_iso3_lists_synthetic_dataset(synthetic_wb):
    assert wb_macro_service.all_countries_iso3() == ["DZA", "NGA", "ZAF"]


# ── build_top_10_gdp_2024 : classement en direct ───────────────────────────


def test_build_top_10_gdp_2024_sorted_by_live_gdp_desc(synthetic_wb):
    from routes.statistics import build_top_10_gdp_2024

    rows = build_top_10_gdp_2024()
    assert [r["iso3"] for r in rows] == ["DZA", "NGA", "ZAF"]
    assert [r["rank"] for r in rows] == [1, 2, 3]
    assert rows[0]["gdp_2024_billion"] == 999.0
    assert rows[0]["gdp_2024_year"] == 2024
    assert rows[0]["growth_2024"] == 9.9


def test_build_top_10_gdp_2024_growth_projection_falls_back_to_curated(synthetic_wb):
    # La BM ne publie pas de projections futures : growth_projection_2025 doit
    # provenir du dataset curé (FMI WEO), jamais inventé.
    from country_data import REAL_COUNTRY_DATA
    from routes.statistics import build_top_10_gdp_2024

    rows = build_top_10_gdp_2024()
    dza = next(r for r in rows if r["iso3"] == "DZA")
    assert dza["growth_projection_2025"] == REAL_COUNTRY_DATA["DZA"].get(
        "growth_projection_2025", "N/A"
    )


# ── /api/country-profile/{iso3} : cascade BM live -> curé ──────────────────


def test_country_profile_prefers_live_wb_over_curated(synthetic_wb):
    from main import app

    client = TestClient(app)
    r = client.get("/api/country-profile/DZA")
    assert r.status_code == 200
    j = r.json()
    assert j["gdp_usd"] == 999_000_000_000.0
    assert j["gdp_per_capita"] == 21000.0
    assert j["population"] == 47_500_000
    assert j["projections"]["gdp_growth_forecast_2024"] == "9.9%"


def test_country_profile_falls_back_to_curated_when_wb_absent(synthetic_wb):
    from country_data import REAL_COUNTRY_DATA
    from main import app

    client = TestClient(app)
    r = client.get("/api/country-profile/COM")
    assert r.status_code == 200
    j = r.json()
    # COM absent du dataset BM synthétique -> repli sur le dataset curé.
    assert j["gdp_usd"] == REAL_COUNTRY_DATA["COM"]["gdp_usd_2024"] * 1_000_000_000
    assert j["gdp_per_capita"] == REAL_COUNTRY_DATA["COM"]["gdp_per_capita_2024"]


# ── /api/statistics/country-comparison/{iso3} : même cascade ───────────────


def test_country_comparison_prefers_live_wb_over_curated(synthetic_wb):
    from main import app

    client = TestClient(app)
    r = client.get("/api/statistics/country-comparison/DZA")
    assert r.status_code == 200
    eco = r.json()["economic_indicators"]
    assert eco["gdp_billion_usd"] == 999.0
    assert eco["gdp_per_capita_usd"] == 21000.0
    assert eco["population_millions"] == 47.5


def test_country_comparison_falls_back_to_curated_when_wb_absent(synthetic_wb):
    from country_data import REAL_COUNTRY_DATA
    from main import app

    client = TestClient(app)
    r = client.get("/api/statistics/country-comparison/COM")
    assert r.status_code == 200
    eco = r.json()["economic_indicators"]
    assert eco["gdp_billion_usd"] == REAL_COUNTRY_DATA["COM"]["gdp_usd_2024"]
    assert eco["gdp_per_capita_usd"] == REAL_COUNTRY_DATA["COM"]["gdp_per_capita_2024"]


# ── /api/statistics/gdp-history-top10 : graphe reconstruit en direct ───────


def test_gdp_history_top10_reflects_live_ranking_and_years(synthetic_wb):
    from main import app

    client = TestClient(app)
    r = client.get("/api/statistics/gdp-history-top10")
    assert r.status_code == 200
    j = r.json()
    assert [c["iso3"] for c in j["countries"]] == ["DZA", "NGA", "ZAF"]
    assert j["years"] == [2023, 2024]
    dza_history = next(s for s in j["countries"] if s["iso3"] == "DZA")
    assert dza_history["gdp_2024_billion"] == 999.0
