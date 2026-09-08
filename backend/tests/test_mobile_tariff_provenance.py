"""The country summary must not resurrect the previous fictitious cached rate."""

import sys
from types import SimpleNamespace

from api.mobile.lightweight_endpoints import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_mobile_country_tariffs_remain_unknown_across_cache_roundtrip(monkeypatch):
    # Cache double, not a customs data source. The old payload reproduces the
    # literal rate previously shipped by this endpoint.
    entries = {"mobile_country:ZZZ_en": {"basic_tariffs": {"avg_mfn_rate_pct": 12.5}}}
    keys = []

    def build_key(type, key):
        value = f"{type}:{key}"
        keys.append(value)
        return value

    l1 = SimpleNamespace(build_key=build_key, get=entries.get, set=entries.__setitem__)
    monkeypatch.setitem(
        sys.modules,
        "performance.caching.cache_layers",
        SimpleNamespace(get_cache=lambda: SimpleNamespace(l1=l1)),
    )
    app = FastAPI()
    app.include_router(router, prefix="/api")
    with TestClient(app) as client:
        fresh = client.get("/api/mobile/country/summary/ZZZ")
        cached = client.get("/api/mobile/country/summary/ZZZ")
        assert fresh.status_code == cached.status_code == 200
        assert fresh.json() == cached.json()
        tariffs = cached.json()["basic_tariffs"]
        assert tariffs["avg_mfn_rate_pct"] is None
        assert tariffs["afcfta_preference"] is None
        assert tariffs["data_status"] == "NOT_AVAILABLE"
        assert all(key.startswith("mobile_country_verified_v2:") for key in keys)
        unchanged = client.get(
            "/api/mobile/country/summary/ZZZ",
            headers={"If-None-Match": cached.headers["ETag"]},
        )
        assert unchanged.status_code == 304
