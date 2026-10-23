"""Tests des projections FMI (WEO) exposées dans la fiche pays."""

from services import imf_projections_service as imf


def test_projections_loaded_for_all_africa():
    data = imf._load().get("data", {})
    assert len(data) >= 50, "les 54 pays africains doivent être couverts"


def test_dza_has_growth_and_inflation_projections():
    proj = imf.get_projections("DZA")
    assert proj is not None
    growth = proj["gdp_growth"]
    inflation = proj["inflation"]
    # Projections FMI récentes (années futures présentes).
    assert "2026" in growth and "2027" in growth
    assert "2026" in inflation
    # Valeurs plausibles (pourcentages).
    assert -50 < growth["2026"] < 50
    assert -50 < inflation["2026"] < 500


def test_case_insensitive_lookup():
    assert imf.get_projections("dza") == imf.get_projections("DZA")


def test_unknown_country_returns_none():
    assert imf.get_projections("XXX") is None


def test_profile_exposes_imf_projections(monkeypatch):
    """La fiche pays doit exposer le bloc FMI et sourcer les projections
    2025/2026 depuis le FMI (prioritaire sur le curé)."""
    import asyncio

    from routes.countries import _gdp_africa_ranks, get_country_profile

    _gdp_africa_ranks.cache_clear()
    p = asyncio.run(get_country_profile("DZA"))
    pr = p.projections
    assert "imf_gdp_growth" in pr and "imf_inflation" in pr
    assert pr["imf_source"]
    # La projection 2026 affichée doit correspondre au WEO du FMI.
    imf_2026 = imf.get_projections("DZA")["gdp_growth"].get("2026")
    assert pr["gdp_growth_projection_2026"] == f"{imf_2026:.1f}%"


def test_weo_vintage_and_fiscal_series_loaded():
    """Le fichier WEO porte son millésime et les séries dette/solde/compte courant."""
    assert "World Economic Outlook (" in imf.source_label()
    proj = imf.get_projections("DZA")
    for key in ("gov_debt", "fiscal_balance", "current_account"):
        assert proj[key], key
    assert 0 < proj["gov_debt"]["2025"] < 500


def test_profile_exposes_real_years_debt_and_current_projection():
    """Plus d'années figées : chaque valeur affichée porte sa vraie année, la
    dette publique vient du WEO et la projection est celle de l'année en cours."""
    import asyncio
    from datetime import datetime

    from routes.countries import _gdp_africa_ranks, get_country_profile
    from services import wb_macro_service

    _gdp_africa_ranks.cache_clear()
    p = asyncio.run(get_country_profile("DZA"))
    pr = p.projections
    current_year = datetime.now().year
    proj = imf.get_projections("DZA")

    wb_gdp = wb_macro_service.get_macro("DZA")["indicators"]["gdp_usd"]
    assert pr["indicator_years"]["gdp"] == wb_gdp["year"]
    assert pr["gdp_growth_latest_year"] <= current_year
    assert pr["gdp_growth_projection_current_year"] == current_year
    assert pr["gdp_growth_projection_current"] == proj["gdp_growth"][str(current_year)]
    assert pr["debt_year"] == current_year - 1
    assert p.total_debt_pct_gdp == proj["gov_debt"][str(current_year - 1)]
    assert pr["hdi_year"] == 2023 and pr["hdi_source"]
