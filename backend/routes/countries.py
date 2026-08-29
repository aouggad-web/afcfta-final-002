"""
Countries routes - Country profiles, lists and economic data
54 African countries members of the AfCFTA
"""

import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from constants import AFRICAN_COUNTRIES
from country_data import REAL_COUNTRY_DATA, get_country_data
from data_loader import get_country_customs_info
from fastapi import APIRouter, HTTPException, Query
from gold_reserves_data import GOLD_RESERVES_GAI_DATA
from models import CountryEconomicProfile, CountryInfo
from projects_data import get_country_ongoing_projects
from translations import translate_country_name, translate_region

router = APIRouter()


@lru_cache(maxsize=1)
def _gdp_africa_ranks() -> Dict[str, int]:
    """
    Rang PIB intra-africain calculé depuis le PIB nominal BM le PLUS RÉCENT de
    chaque pays (``worldbank_data_latest.json``), afin que le rang reste toujours
    cohérent avec la valeur de PIB affichée — plutôt qu'un rang curé figé qui
    dérive dès qu'une nouvelle année (ex. 2025) rebat les positions (l'Algérie
    passe #3 -> #4 derrière l'Afrique du Sud, l'Égypte et le Nigeria). Repli
    silencieux (dict vide -> on retombe sur le rang curé) si le fichier BM est
    indisponible.
    """
    try:
        path = (
            Path(__file__).resolve().parent.parent.parent
            / "data"
            / "json"
            / "worldbank_data_latest.json"
        )
        data = json.loads(path.read_text(encoding="utf-8")).get("data", {})
        gdp_by_iso: Dict[str, float] = {}
        for iso, info in data.items():
            series = (info.get("indicators", {}) or {}).get("GDP", {})
            # Comparaison NUMÉRIQUE de l'année (pas lexicographique sur des clés
            # string, qui casserait si le format des clés changeait).
            year_keys = [y for y in series if str(y).isdigit()]
            if year_keys:
                latest_year = max(year_keys, key=int)
                if series[latest_year] is not None:
                    gdp_by_iso[iso] = float(series[latest_year])
        ranks: Dict[str, int] = {}
        for i, (iso, _v) in enumerate(
            sorted(gdp_by_iso.items(), key=lambda kv: kv[1], reverse=True), 1
        ):
            ranks[iso] = i
        return ranks
    except Exception:  # pragma: no cover - le profil ne doit jamais casser là-dessus
        return {}


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


@router.get("/countries/official-stats/{country_iso3}")
async def get_country_official_stats(country_iso3: str):
    """
    Statistiques officielles NATIONALES d'un pays (bulletins des agences
    nationales — ex. EDB Mauritius 2023, valeurs en monnaie locale), avec
    distinction exportations domestiques / réexportations. 404 si aucune
    source officielle n'est intégrée pour ce pays.
    """
    from services import national_official_stats

    stats = national_official_stats.get_official_stats(country_iso3)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune statistique officielle nationale intégrée pour {country_iso3.upper()}",
        )
    return stats


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

    # Récupérer les données réelles du pays (Banque Mondiale WDI 2024, dataset
    # curé Profils Pays) et les indicateurs BM auto-actualisés (API officielle,
    # se rafraîchit via l'ETL update_data_automated.py — cf. donnees.
    # banquemondiale.org). Cascade sur TOUS les indicateurs partagés, sans
    # double emploi avec la PR #234 :
    #   1) dataset BM auto-actualisé (le plus frais, se rafraîchit seul) ;
    #   2) repli sur la valeur curée du dataset Profils Pays (FMI WEO/BM) ;
    #   3) null/valeur par défaut sinon — jamais inventé.
    real_data = get_country_data(iso3_code)

    from services import wb_macro_service

    wb = wb_macro_service.get_macro(iso3_code).get("indicators", {})

    def _wb(key):
        entry = wb.get(key)
        return entry["value"] if entry else None

    gdp_billion = real_data.get("gdp_usd_2024")
    gdp_static = float(gdp_billion) * 1_000_000_000 if gdp_billion is not None else None
    population_static = real_data.get("population_2024", country["population"])

    profile = CountryEconomicProfile(
        country_code=iso3_code,
        country_name=country["name"],
        population=_wb("population") or population_static,
        region=country["region"],
    )

    profile.gdp_usd = _wb("gdp_usd") or gdp_static
    profile.gdp_per_capita = _wb("gdp_per_capita_usd") or real_data.get("gdp_per_capita_2024")
    if profile.population:
        profile.population_millions = round(profile.population / 1_000_000, 2)
    # development_index de REAL_COUNTRY_DATA = IDH (PNUD) — était exposé
    # uniquement dans projections, jamais dans le champ hdi du modèle.
    profile.hdi = real_data.get("development_index")
    profile.hdi_rank = real_data.get("hdi_rank")

    profile.inflation_rate = _wb("inflation_percent") or real_data.get("inflation_rate_2024")
    profile.unemployment_rate = _wb("unemployment_percent") or real_data.get(
        "unemployment_rate_2024"
    )

    # Croissance 2024 : la tuile est labellisée « 2024 ». On préfère la
    # croissance RÉALISÉE BM UNIQUEMENT si son année est bien 2024 ; depuis que
    # l'ETL récupère 2025, ``_wb`` renvoie la dernière année (2025) — l'afficher
    # sous une étiquette 2024 serait faux, on retombe alors sur la valeur curée
    # 2024 (FMI Art. IV). Les projections 2025/2026 restent sur le dataset curé.
    growth_entry = wb.get("gdp_growth_percent")
    growth_2024_wb = (
        growth_entry.get("value")
        if growth_entry and str(growth_entry.get("year")) == "2024"
        else None
    )
    growth_2024_display = (
        f"{growth_2024_wb:.1f}%"
        if growth_2024_wb is not None
        else real_data.get("growth_forecast_2024", "3.0%")
    )

    profile.projections = {
        "gdp_growth_forecast_2024": growth_2024_display,
        "gdp_growth_projection_2025": real_data.get("growth_projection_2025", "3.2%"),
        "gdp_growth_projection_2026": real_data.get("growth_projection_2026", "3.5%"),
        "development_index": real_data.get("development_index", 0.500),
        # Rang PIB recalculé sur le PIB BM le plus récent (cohérent avec le PIB
        # affiché) ; repli sur le rang curé si le calcul est indisponible.
        "africa_rank": _gdp_africa_ranks().get(iso3_code) or real_data.get("africa_rank", 25),
    }

    # Projections FMI (WEO) : croissance + inflation PLURIANNUELLES (que la BM ne
    # publie pas). Les projections de croissance 2025/2026 du FMI priment sur les
    # valeurs curées (source unique, auto-actualisable) ; le bloc complet
    # (jusqu'à ~2031) alimente la vue détaillée « Perspectives FMI » de la fiche.
    from services import imf_projections_service as imf_svc

    imf_proj = imf_svc.get_projections(iso3_code)
    if imf_proj:
        imf_growth = imf_proj.get("gdp_growth") or {}
        imf_inflation = imf_proj.get("inflation") or {}
        if imf_growth.get("2025") is not None:
            profile.projections["gdp_growth_projection_2025"] = f"{imf_growth['2025']:.1f}%"
        if imf_growth.get("2026") is not None:
            profile.projections["gdp_growth_projection_2026"] = f"{imf_growth['2026']:.1f}%"
        profile.projections["imf_gdp_growth"] = imf_growth
        profile.projections["imf_inflation"] = imf_inflation
        profile.projections["imf_source"] = imf_svc.source_label()

    # Indicateurs sociaux. Pour chacun, on prend la DERNIÈRE année réellement
    # disponible à la Banque Mondiale (API auto-actualisée) et on affiche CETTE
    # année réelle — fin des étiquettes d'année figées/inventées. Repli sur la
    # valeur curée (avec son année d'origine) uniquement quand la BM n'a rien.
    #
    # Chaque champ expose deux clés :
    #   <clé>        -> la valeur ;
    #   <clé>_year   -> l'année réelle de cette valeur (BM live, sinon curée).
    #
    # (clé_frontend, clé_BM ou None si curé-seul, année de repli curée)
    social_fields = [
        ("life_expectancy_2023", "life_expectancy_years", 2023),
        ("gini_index_2024", "gini_index", 2024),
        ("poverty_rate_3usd_2024", "poverty_rate_3usd_pct", 2024),
        ("urban_population_pct_2024", "urban_population_pct", 2024),
        ("internet_users_pct_2024", "internet_users_pct", 2024),
        ("electricity_access_2022", "electricity_access_pct", 2022),
        ("female_labor_force_pct_2024", "female_labor_force_pct", 2024),
        # Indicateurs curés uniquement (pas d'équivalent WDI direct branché) —
        # conservés tels quels avec leur année d'origine.
        ("mobile_3g_coverage_2024", None, 2024),
        ("water_stress_2022", None, 2022),
        ("ghg_emissions_mt_2022", None, 2022),
        ("learning_poverty_2023", None, 2023),
    ]
    for field, wb_key, fallback_year in social_fields:
        wb_entry = wb.get(wb_key) if wb_key else None
        if wb_entry and wb_entry.get("value") is not None:
            # BM live : valeur + vraie année.
            profile.projections[field] = wb_entry["value"]
            profile.projections[f"{field}_year"] = wb_entry["year"]
        else:
            # Repli curé : valeur figée + son année d'origine.
            value = real_data.get(field)
            if value is not None:
                profile.projections[field] = value
                profile.projections[f"{field}_year"] = fallback_year

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
        # Catégorie descriptive (un grade-lettre « A » seul, pour un score de
        # 30/100, induisait en erreur) : libellé bilingue « Modérément attractif ».
        profile.projections["gai_2025_category_fr"] = gai_data.get("category_fr")
        profile.projections["gai_2025_category_en"] = gai_data.get("category_en")
        profile.projections["gai_2025_trend"] = gai_data.get("trend")

    # Notations réelles (S&P/Moody's/Fitch/Scope) présentes dans le dataset
    # Profils Pays pour les 54 pays — étaient écrasées par un dict vide.
    profile.risk_ratings = real_data.get("risk_ratings") or {}
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
