"""
Tests de la cascade « indicateurs sociaux Banque Mondiale live » du Profil Pays.

Contexte : les indicateurs sociaux (espérance de vie, pauvreté, Gini, accès
électricité/internet, population urbaine, population active féminine) étaient
des valeurs curées FIGÉES, affichées avec une année CODÉE EN DUR dans le
frontend (ex. « pauvreté 0,5 % en 2024 » alors que la dernière enquête BM pour
l'Algérie date de 2011). Ces tests verrouillent la nouvelle démarche :

  • pour chaque indicateur, on prend la DERNIÈRE année réellement disponible à
    la Banque Mondiale (dataset auto-actualisé) ;
  • on expose la valeur ET sa vraie année (clé `<champ>_year`) ;
  • repli sur la valeur curée (avec son année d'origine) uniquement quand la BM
    n'a aucune donnée pour le pays/l'indicateur.

Le dataset BM est isolé par test (monkeypatch de wb_macro_service._DATASET_PATH
+ reset_cache) pour ne jamais dépendre des valeurs réelles, qui évoluent à
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


@pytest.fixture
def synthetic_wb_social(tmp_path, monkeypatch):
    """Bascule wb_macro_service sur un dataset BM synthétique avec indicateurs
    sociaux, dont un (pauvreté) volontairement daté de 2011 pour prouver que la
    vraie année est bien remontée et non une année figée."""
    dataset = tmp_path / "worldbank_data_latest.json"
    payload = {
        "metadata": {
            "source": "World Bank API",
            "updated_at": "2026-07-14T00:00:00",
            "indicators": ["LifeExpectancy", "Poverty3usd"],
        },
        "data": {
            "DZA": {
                "name": "Algeria",
                "indicators": {
                    # dernière année = 2024
                    "LifeExpectancy": {"2022": 77.1, "2023": 77.3, "2024": 76.0},
                    # dernière (et seule) année = 2011
                    "Poverty3usd": {"2011": 0.4},
                    "ElectricityAccess": {"2021": 99.5, "2022": 99.7},
                    "GiniIndex": {"2011": 27.6},
                    "InternetUsers": {"2023": 71.2},
                    "UrbanPopulation": {"2024": 75.3},
                    "FemaleLaborForce": {"2024": 17.4},
                },
            },
            # COM volontairement ABSENT -> repli sur le dataset curé.
        },
    }
    dataset.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(wb_macro_service, "_DATASET_PATH", dataset)
    wb_macro_service.reset_cache()
    yield dataset
    wb_macro_service.reset_cache()


def _profile(iso3):
    from main import app

    r = TestClient(app).get(f"/api/country-profile/{iso3}")
    assert r.status_code == 200, r.text
    return r.json()["projections"]


def test_life_expectancy_uses_latest_year_from_wb(synthetic_wb_social):
    p = _profile("DZA")
    # 2024 est la dernière année disponible -> valeur ET année 2024.
    assert p["life_expectancy_2023"] == 76.0
    assert p["life_expectancy_2023_year"] == 2024


def test_poverty_shows_real_survey_year_not_fabricated_2024(synthetic_wb_social):
    p = _profile("DZA")
    # La seule enquête pauvreté est 2011 : la vraie année doit être 2011,
    # jamais un « 2024 » collé d'office.
    assert p["poverty_rate_3usd_2024"] == 0.4
    assert p["poverty_rate_3usd_2024_year"] == 2011


def test_other_social_indicators_carry_real_years(synthetic_wb_social):
    p = _profile("DZA")
    assert p["electricity_access_2022"] == 99.7
    assert p["electricity_access_2022_year"] == 2022
    assert p["gini_index_2024"] == 27.6
    assert p["gini_index_2024_year"] == 2011
    assert p["internet_users_pct_2024"] == 71.2
    assert p["internet_users_pct_2024_year"] == 2023
    assert p["urban_population_pct_2024"] == 75.3
    assert p["urban_population_pct_2024_year"] == 2024
    assert p["female_labor_force_pct_2024"] == 17.4
    assert p["female_labor_force_pct_2024_year"] == 2024


def test_falls_back_to_curated_when_wb_absent(synthetic_wb_social):
    from country_data import REAL_COUNTRY_DATA

    p = _profile("COM")
    curated = REAL_COUNTRY_DATA.get("COM", {})
    # COM absent du dataset BM synthétique -> valeur curée + année d'origine.
    if curated.get("life_expectancy_2023") is not None:
        assert p["life_expectancy_2023"] == curated["life_expectancy_2023"]
        assert p["life_expectancy_2023_year"] == 2023
