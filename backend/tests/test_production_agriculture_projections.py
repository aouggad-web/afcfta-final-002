"""Backend regression tests for the Production/Agriculture module after the
PR #428 merge. Focus on the /api/faostat/country-detail/{iso3} endpoint which
must now expose the enriched crops list plus the `projections` and
`has_projections` keys while keeping the existing keys intact.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://commerce-viewer.preview.emergentagent.com").rstrip("/")

COUNTRIES = ["NGA", "GHA", "DZA", "CIV", "SEN"]

EXISTING_KEYS = ["cultures", "evolution", "elevage", "peche_aquaculture", "key_indicators"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.mark.parametrize("iso3", COUNTRIES)
def test_country_detail_status_and_shape(session, iso3):
    r = session.get(f"{BASE_URL}/api/faostat/country-detail/{iso3}?language=fr", timeout=30)
    assert r.status_code == 200, f"{iso3} => {r.status_code} body={r.text[:300]}"
    data = r.json()
    # Endpoint may wrap under "data" or expose directly
    payload = data.get("data", data)
    # Existing keys still present (non-regression)
    for k in EXISTING_KEYS:
        assert k in payload, f"{iso3} missing existing key '{k}'. Keys present: {list(payload.keys())[:20]}"
    # New keys
    assert "projections" in payload, f"{iso3} missing 'projections' key"
    assert "has_projections" in payload, f"{iso3} missing 'has_projections' key"
    assert isinstance(payload["has_projections"], bool)


@pytest.mark.parametrize("iso3", COUNTRIES)
def test_projections_structure_when_available(session, iso3):
    r = session.get(f"{BASE_URL}/api/faostat/country-detail/{iso3}?language=fr", timeout=30)
    assert r.status_code == 200
    payload = r.json().get("data", r.json())
    projections = payload.get("projections")
    has_p = payload.get("has_projections")
    if has_p:
        assert projections, f"{iso3} has_projections=True but projections empty"
        # Accept dict (grouped by sector) or list
        if isinstance(projections, dict):
            # Expect keys like Crops/Cultures/Elevage/Livestock
            assert len(projections.keys()) >= 1
            for sector, items in projections.items():
                assert isinstance(items, list), f"{iso3} sector {sector} is not a list"
                if items:
                    sample = items[0]
                    assert isinstance(sample, dict)
        elif isinstance(projections, list):
            assert len(projections) > 0
        else:
            pytest.fail(f"{iso3} unexpected projections type: {type(projections)}")


def test_cultures_no_fr_en_duplicates_and_no_animals(session):
    """PR #428 dedup FR/EN and excludes animal products from Crops list."""
    r = session.get(f"{BASE_URL}/api/faostat/country-detail/NGA?language=fr", timeout=30)
    assert r.status_code == 200
    payload = r.json().get("data", r.json())
    cultures = payload.get("cultures", [])
    assert isinstance(cultures, list)
    names = []
    for c in cultures:
        n = (c.get("nom") or c.get("name") or c.get("product") or "").strip().lower()
        if n:
            names.append(n)
    # No duplicates
    assert len(names) == len(set(names)), f"Duplicate cultures found: {[n for n in names if names.count(n) > 1][:5]}"
    # No obvious animal products
    banned = ["meat", "viande", "milk", "lait", "eggs", "oeufs", "cattle", "poulet", "chicken", "bovine"]
    hits = [n for n in names if any(b in n for b in banned)]
    assert not hits, f"Animal products leaked into cultures: {hits[:5]}"


def test_language_switch_fr_en(session):
    r_fr = session.get(f"{BASE_URL}/api/faostat/country-detail/NGA?language=fr", timeout=30)
    r_en = session.get(f"{BASE_URL}/api/faostat/country-detail/NGA?language=en", timeout=30)
    assert r_fr.status_code == 200 and r_en.status_code == 200
    fr = r_fr.json().get("data", r_fr.json())
    en = r_en.json().get("data", r_en.json())
    assert "projections" in fr and "projections" in en
    assert "has_projections" in fr and "has_projections" in en
