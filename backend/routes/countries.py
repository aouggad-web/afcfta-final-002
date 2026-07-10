"""
Countries routes - Country profiles, lists and economic data
54 African countries members of the AfCFTA
"""

import json
import logging
import unicodedata
from pathlib import Path
from typing import Optional

from constants import AFRICAN_COUNTRIES
from country_data import REAL_COUNTRY_DATA, get_country_data
from data_loader import get_country_customs_info
from fastapi import APIRouter, HTTPException, Query
from gold_reserves_data import GOLD_RESERVES_GAI_DATA
from models import CountryEconomicProfile, CountryInfo
from projects_data import get_country_ongoing_projects
from translations import translate_country_name, translate_region

router = APIRouter()


@router.get("/countries")
async def get_countries(lang: str = "fr"):
    """Récupérer la liste des pays membres de la ZLECAf avec traduction

    Retourne ISO3 comme code principal, ISO2 conservé pour compatibilité (drapeaux)
    """
    countries = []
    for country in AFRICAN_COUNTRIES:
        translated_country = {
            "code": country["iso3"],
            "iso2": country["code"],
            "iso3": country["iso3"],
            "name": translate_country_name(country["code"], lang),
            "region": translate_region(country["region"], lang),
            "wb_code": country.get("wb_code", country["iso3"]),
            "population": country["population"],
        }
        countries.append(CountryInfo(**translated_country))
    return countries


@router.get("/countries/economic-indicators")
async def get_countries_economic_indicators(lang: str = "fr"):
    """Indicateurs économiques 2024 pour les 54 pays africains.

    Renvoie un tableau compact (code ISO3, PIB, PIB/habitant, population,
    indice de développement, croissance) destiné aux visualisations
    cartographiques et comparatives. Source: Banque Mondiale (WDI 2024).
    """

    def _growth_to_float(g):
        if g is None:
            return None
        try:
            return float(str(g).replace("%", "").strip())
        except (ValueError, TypeError):
            return None

    # COUNTRY_TRANSLATIONS is keyed by ISO2; build an ISO3 -> ISO2 map for EN names
    iso3_to_iso2 = {c["iso3"]: c["code"] for c in AFRICAN_COUNTRIES}

    countries = []
    for iso3, d in REAL_COUNTRY_DATA.items():
        name = d.get("name")
        if lang == "en":
            name = translate_country_name(iso3_to_iso2.get(iso3, ""), "en") or name
        countries.append(
            {
                "iso3": iso3,
                "name": name,
                "gdp_2024_billion_usd": d.get("gdp_usd_2024"),
                "gdp_per_capita_2024_usd": d.get("gdp_per_capita_2024"),
                "population_2024": d.get("population_2024"),
                "development_index": d.get("development_index"),
                "africa_rank": d.get("africa_rank"),
                "growth_forecast_2024_pct": _growth_to_float(d.get("growth_forecast_2024")),
            }
        )

    return {
        "success": True,
        "total": len(countries),
        "year": 2024,
        "source": "Banque Mondiale (WDI 2024)",
        "countries": countries,
    }


@router.get("/country-profile/{country_code}")
async def get_country_profile(country_code: str) -> CountryEconomicProfile:
    """Récupérer le profil économique complet d'un pays avec données réelles et commerce 2024

    Accepte les codes ISO2 (ex: DZ) ou ISO3 (ex: DZA)
    """
    code_upper = country_code.upper()

    # Chercher par ISO3 d'abord, puis ISO2 (rétrocompatibilité)
    country = next((c for c in AFRICAN_COUNTRIES if c["iso3"] == code_upper), None)
    if not country:
        country = next((c for c in AFRICAN_COUNTRIES if c["code"] == code_upper), None)

    if not country:
        raise HTTPException(status_code=404, detail="Pays non trouvé dans la ZLECAf")

    # Utiliser ISO3 pour toutes les requêtes de données
    iso3_code = country["iso3"]

    # Récupérer les données réelles du pays (Banque Mondiale WDI 2024)
    real_data = get_country_data(iso3_code)

    profile = CountryEconomicProfile(
        country_code=iso3_code,
        country_name=country["name"],
        population=real_data.get("population_2024", country["population"]),
        region=country["region"],
    )

    gdp_billion = real_data.get("gdp_usd_2024")
    profile.gdp_usd = float(gdp_billion) * 1_000_000_000 if gdp_billion is not None else None
    profile.gdp_per_capita = real_data.get("gdp_per_capita_2024")
    profile.inflation_rate = real_data.get("inflation_rate_2024")

    profile.projections = {
        "gdp_growth_forecast_2024": real_data.get("growth_forecast_2024", "3.0%"),
        "gdp_growth_projection_2025": real_data.get("growth_projection_2025", "3.2%"),
        "gdp_growth_projection_2026": real_data.get("growth_projection_2026", "3.5%"),
        "development_index": real_data.get("development_index", 0.500),
        "africa_rank": real_data.get("africa_rank", 25),
    }

    # Social/WB indicators
    wb_fields = [
        "life_expectancy_2023", "gini_index_2024", "poverty_rate_3usd_2024",
        "urban_population_pct_2024", "internet_users_pct_2024",
        "electricity_access_2022", "mobile_3g_coverage_2024",
        "female_labor_force_pct_2024", "water_stress_2022",
        "ghg_emissions_mt_2022", "learning_poverty_2023",
    ]
    for field in wb_fields:
        value = real_data.get(field)
        if value is not None:
            profile.projections[field] = value

    # Gold reserves data
    gold_data = GOLD_RESERVES_GAI_DATA["gold_reserves"].get(country["iso3"], {})
    if gold_data:
        profile.projections["gold_reserves_tonnes"] = gold_data.get("tonnes", 0.0)
        profile.projections["gold_reserves_rank_africa"] = gold_data.get("rank_africa")
        profile.projections["gold_reserves_rank_global"] = gold_data.get("rank_global")

    # Global Attractiveness Index 2025
    gai_data = GOLD_RESERVES_GAI_DATA["global_attractiveness_index_2025"].get(country["iso3"], {})
    if gai_data:
        profile.projections["gai_2025_score"] = gai_data.get("score")
        profile.projections["gai_2025_rank_africa"] = gai_data.get("rank_africa")
        profile.projections["gai_2025_rank_global"] = gai_data.get("rank_global")
        profile.projections["gai_2025_rating"] = gai_data.get("rating")
        profile.projections["gai_2025_trend"] = gai_data.get("trend")

    profile.risk_ratings = {}
    profile.customs = get_country_customs_info(country["name"]) or {}
    profile.ongoing_projects = get_country_ongoing_projects(iso3_code)

    # Infrastructure ranking
    infra_ranking = None
    try:
        infra_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "json"
            / "classement_infrastructure_afrique.json"
        )
        with open(infra_path, "r") as f:
            infra_data = json.load(f)

        def normalize_name(s):
            s = s.replace("\u2019", "'").replace("\u2018", "'")
            return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode("ascii")

        # Exact (accent/case-insensitive) match on the full official country
        # name only. Substring/fuzzy matching is deliberately avoided: country
        # names that contain another country's name (e.g. "République
        # démocratique du Congo" vs "République du Congo", "Niger" vs
        # "Nigeria", "Guinée-Bissau" vs "Guinée") would otherwise silently
        # publish the wrong infrastructure_ranking. Any country absent from
        # the dataset simply gets no ranking rather than an incorrect one.
        search_name = normalize_name(country["name"])
        for entry in infra_data:
            if normalize_name(entry["pays"]) == search_name:
                infra_ranking = {
                    "africa_rank": entry["rang_afrique"],
                    "lpi_infrastructure_score": entry["score_infrastructure_ipl"],
                    "lpi_world_rank": entry["rang_mondial_ipl"],
                    "aidi_transport_score": entry.get(
                        "score_aidi_2024", entry.get("score_transport_aidi", 0)
                    ),
                }
                break
    except Exception as e:
        logging.error(f"Erreur chargement infrastructure: {e}")
    profile.infrastructure_ranking = infra_ranking if infra_ranking else {}

    return profile
