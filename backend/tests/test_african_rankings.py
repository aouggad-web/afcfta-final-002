"""Tests du classement africain des indices majeurs (fiche pays)."""

import asyncio
import json
from pathlib import Path

from country_data import REAL_COUNTRY_DATA
from services import african_rankings_service as svc
from services import wb_macro_service


def test_rank_shares_ties_and_handles_direction():
    values = {"A": 10.0, "B": 8.0, "C": 8.0, "D": 5.0}
    assert svc._rank(values, "B", True, 2025) == {"rank": 2, "total": 4, "year": 2025}
    assert svc._rank(values, "D", True, 2025)["rank"] == 4
    # Plus faible = mieux (inflation, chômage, dette).
    assert svc._rank(values, "D", False, 2025)["rank"] == 1
    assert svc._rank(values, "C", False, 2025)["rank"] == 2
    assert svc._rank(values, "Z", True, 2025) is None


def test_rankings_compare_same_year_only():
    """Le total d'un indice BM = nombre de pays publiant la même année."""
    r = svc.get_rankings("DZA")["gdp"]
    year = r["year"]
    peers = [
        iso
        for iso in wb_macro_service.all_countries_iso3()
        if wb_macro_service.get_series(iso, "gdp_usd").get(year) is not None
    ]
    assert r["total"] == len(peers)
    assert 1 <= r["rank"] <= r["total"]


def test_lowest_inflation_ranks_first():
    year = svc.get_rankings("DZA")["inflation"]["year"]
    values = {
        iso: wb_macro_service.get_series(iso, "inflation_percent").get(year)
        for iso in wb_macro_service.all_countries_iso3()
    }
    best = min((v, iso) for iso, v in values.items() if v is not None)[1]
    assert svc.get_rankings(best)["inflation"]["rank"] == 1


def test_hdi_is_hdr_2025_and_ranked_in_africa():
    # Valeurs officielles PNUD, RDH 2025 (année 2023).
    official = {"SYC": (0.848, 54), "MUS": (0.806, 73), "DZA": (0.763, 96), "SSD": (0.388, 193)}
    for iso, (hdi, world_rank) in official.items():
        assert REAL_COUNTRY_DATA[iso]["development_index"] == hdi
        assert REAL_COUNTRY_DATA[iso]["hdi_rank"] == world_rank
    assert svc.get_rankings("SYC")["hdi"] == {"rank": 1, "total": 54, "year": 2023}
    assert svc.get_rankings("DZA")["hdi"]["rank"] == 3
    assert svc.get_rankings("SSD")["hdi"]["rank"] == 54


def test_lpi_ranked_on_2023_edition_only():
    path = Path(__file__).resolve().parents[2] / "data" / "json" / "classement_infrastructure_afrique.json"
    entries = json.loads(path.read_text(encoding="utf-8"))
    assert len({e["iso3"] for e in entries}) == len(entries) == 54
    # Plus de valeurs de remplissage (2,0 / rang 120) : scores officiels WDI ou null.
    assert all(e["rang_mondial_ipl"] is None for e in entries)
    assert {e["edition_ipl"] for e in entries} <= {2023, 2018, 2016, None}
    covered_2023 = [e for e in entries if e["edition_ipl"] == 2023]
    assert svc.get_rankings("ZAF")["lpi"] == {"rank": 1, "total": len(covered_2023), "year": 2023}
    # Maroc : dernière édition 2018, non comparable -> pas de rang.
    assert "lpi" not in svc.get_rankings("MAR")


def test_profile_exposes_african_rankings():
    from routes.countries import get_country_profile

    p = asyncio.run(get_country_profile("NGA"))
    assert p.african_rankings["population"]["rank"] == 1
    for key in ("gdp", "hdi", "gov_debt", "gdp_growth_projection"):
        assert key in p.african_rankings, key


def test_external_debt_and_reserves_ranked_same_year():
    """Dette extérieure : 1 = ratio au RNB le plus faible ; réserves : 1 = encours
    le plus élevé ; chaque fois parmi les pays publiant la même année."""
    for key, src, higher in (
        ("external_debt", "external_debt_pct_gni", False),
        ("reserves", "reserves_usd", True),
    ):
        year = svc.get_rankings("DZA")[key]["year"]
        values = {
            iso: wb_macro_service.get_series(iso, src).get(year)
            for iso in wb_macro_service.all_countries_iso3()
        }
        values = {iso: v for iso, v in values.items() if v is not None}
        best = (max if higher else min)(values, key=values.get)
        assert svc.get_rankings(best)[key] == {"rank": 1, "total": len(values), "year": year}


def test_profile_shows_external_debt_and_reserves_not_fiscal_balance():
    from routes.countries import get_country_profile

    pr = asyncio.run(get_country_profile("DZA")).projections
    debt = pr["external_debt"]
    assert debt["year"] >= 2024 and debt["pct_gni"] > 0 and debt["usd"] > 0
    assert pr["reserves"]["usd"] > 0 and pr["reserves"]["year"] >= 2024
    assert "imf_fiscal_balance" not in pr and "imf_current_account" not in pr
    # Seychelles : pays à revenu élevé, hors International Debt Statistics.
    syc = asyncio.run(get_country_profile("SYC"))
    assert "external_debt" not in syc.projections
    assert "external_debt" not in syc.african_rankings
