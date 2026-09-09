"""
OEC (Observatory of Economic Complexity) Data Service
Fetches REAL, verifiable trade statistics — no AI hallucination for raw numbers.

Data flows into claude_trade_service to ground AI analysis in actual figures.

Sources (all free, no API key needed for basic queries):
  - OEC API v4: https://oec.world/api/olap-proxy/data
  - UN Comtrade bulk files: https://comtrade.un.org/data/bulk
  - World Bank WITS: https://wits.worldbank.org/

Usage:
    svc = OECDataService()
    top_exports = await svc.get_top_exports("DZA", year=2022, n=10)
    top_imports = await svc.get_top_imports("DZA", year=2022, n=10)
    trade_balance = await svc.get_trade_balance_series("DZA", start=2019, end=2023)
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from services.redis_cache_service import cache_service

logger = logging.getLogger(__name__)

# ── OEC country codes (ISO3 → OEC country ID used in their API) ───────────────
# OEC uses its own country IDs derived from ISO numeric codes
# Format: "saXXX" where XXX = 3-char country code they use internally
# Most are straightforward; see https://oec.world/en/profile/country/

# ── Mapping: ISO3 → OEC profile slug ──────────────────────────────────────────
ISO3_TO_OEC_SLUG = {
    "DZA": "dza",
    "AGO": "ago",
    "BEN": "ben",
    "BWA": "bwa",
    "BFA": "bfa",
    "BDI": "bdi",
    "CMR": "cmr",
    "CPV": "cpv",
    "CAF": "caf",
    "TCD": "tcd",
    "COM": "com",
    "COG": "cog",
    "COD": "cod",
    "DJI": "dji",
    "EGY": "egy",
    "GNQ": "gnq",
    "ERI": "eri",
    "SWZ": "swz",
    "ETH": "eth",
    "GAB": "gab",
    "GMB": "gmb",
    "GHA": "gha",
    "GIN": "gin",
    "GNB": "gnb",
    "CIV": "civ",
    "KEN": "ken",
    "LSO": "lso",
    "LBR": "lbr",
    "LBY": "lby",
    "MDG": "mdg",
    "MWI": "mwi",
    "MLI": "mli",
    "MRT": "mrt",
    "MUS": "mus",
    "MAR": "mar",
    "MOZ": "moz",
    "NAM": "nam",
    "NER": "ner",
    "NGA": "nga",
    "RWA": "rwa",
    "STP": "stp",
    "SEN": "sen",
    "SLE": "sle",
    "SOM": "som",
    "ZAF": "zaf",
    "SSD": "ssd",
    "SDN": "sdn",
    "TZA": "tza",
    "TGO": "tgo",
    "TUN": "tun",
    "UGA": "uga",
    "ZMB": "zmb",
    "ZWE": "zwe",
}

# ── HS6 lookup (loaded once from backend/data/hs6_database.json if present) ───
_HS6_NAMES: Dict[str, str] = {}
_HS_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hs6_database.json"


def _load_hs_db():
    global _HS6_NAMES
    if _HS6_NAMES or not _HS_DB_PATH.exists():
        return
    try:
        with open(_HS_DB_PATH, encoding="utf-8") as f:
            db = json.load(f)
        # Support both {code: name} and [{code:, name:}] formats
        if isinstance(db, dict):
            _HS6_NAMES = {str(k).zfill(6): v for k, v in db.items()}
        elif isinstance(db, list):
            for item in db:
                code = str(item.get("code", item.get("hs6", ""))).zfill(6)
                name = item.get("name", item.get("description", ""))
                if code and name:
                    _HS6_NAMES[code] = name
        logger.info(f"OEC service: loaded {len(_HS6_NAMES)} HS6 product names")
    except Exception as e:
        logger.warning(f"OEC service: could not load hs6_database.json: {e}")


_load_hs_db()


class OECDataService:
    """
    Fetches real trade statistics from OEC public API.
    Caches responses with 7-day TTL (data changes slowly).
    Falls back gracefully when OEC API is unavailable.
    """

    OEC_BASE = "https://oec.world/api/olap-proxy/data"
    TIMEOUT = 15.0  # seconds

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.TIMEOUT,
                headers={"User-Agent": "AfCFTA-Trade-Platform/3.0"},
                follow_redirects=True,
            )
        return self._client

    async def _fetch(self, url: str, params: dict) -> Optional[dict]:
        client = await self._get_client()
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.TimeoutException:
            logger.warning(f"OEC API timeout: {url}")
            return None
        except Exception as e:
            logger.warning(f"OEC API error: {e}")
            return None

    def _hs6_name(self, code: str) -> str:
        """Look up HS6 product name from local database."""
        code = str(code).zfill(6)
        return _HS6_NAMES.get(code, f"HS {code}")

    def _hs2_from_hs6(self, code: str) -> tuple:
        code6 = str(code).zfill(6)
        hs2 = code6[:2]
        hs4 = code6[:4]
        hs2_name = _HS6_NAMES.get(hs2.ljust(6, "0"), "")
        hs4_name = _HS6_NAMES.get(hs4.ljust(6, "0"), "")
        return hs2, hs4, code6, hs2_name or f"Chapter {hs2}", hs4_name or f"Heading {hs4}"

    # ── Public methods ─────────────────────────────────────────────────────────

    async def get_top_exports(self, iso3: str, year: int = 2022, n: int = 15) -> List[Dict]:
        """Top N exported products for a country, with value in MUSD."""
        cache_key = f"oec_exports_{iso3}_{year}"
        cached = cache_service.get("oec_data", {"key": cache_key})
        if cached:
            return cached[:n]

        slug = ISO3_TO_OEC_SLUG.get(iso3)
        if not slug:
            return []

        # OEC v4 API — country export profile by HS6
        params = {
            "cube": "trade_i_baci_a_92",
            "drilldowns": "HS6",
            "measures": "Trade Value",
            "Year": str(year),
            "Exporter Country": f"sa{slug}",
        }
        data = await self._fetch(self.OEC_BASE, params)
        if not data or "data" not in data:
            return []

        rows = sorted(data["data"], key=lambda r: r.get("Trade Value", 0), reverse=True)
        result = []
        for row in rows[:n]:
            code = str(row.get("HS6 ID", row.get("HS6", ""))).replace("HS", "").zfill(6)
            value_musd = round(row.get("Trade Value", 0) / 1_000_000, 2)
            hs2, hs4, hs6, hs2_name, hs4_name = self._hs2_from_hs6(code)
            result.append(
                {
                    "hs6Code": hs6,
                    "hs6Name": self._hs6_name(code),
                    "hs4Code": hs4,
                    "hs4Name": hs4_name,
                    "hs2Code": hs2,
                    "hs2Name": hs2_name,
                    "value_musd": value_musd,
                    "year": year,
                    "source": "OEC / UN Comtrade",
                }
            )

        if result:
            cache_service.set("oec_data", {"key": cache_key}, result, "oec_data")
        return result

    async def get_top_imports(self, iso3: str, year: int = 2022, n: int = 15) -> List[Dict]:
        """Top N imported products for a country, with value in MUSD."""
        cache_key = f"oec_imports_{iso3}_{year}"
        cached = cache_service.get("oec_data", {"key": cache_key})
        if cached:
            return cached[:n]

        slug = ISO3_TO_OEC_SLUG.get(iso3)
        if not slug:
            return []

        params = {
            "cube": "trade_i_baci_a_92",
            "drilldowns": "HS6",
            "measures": "Trade Value",
            "Year": str(year),
            "Importer Country": f"sa{slug}",
        }
        data = await self._fetch(self.OEC_BASE, params)
        if not data or "data" not in data:
            return []

        rows = sorted(data["data"], key=lambda r: r.get("Trade Value", 0), reverse=True)
        result = []
        for row in rows[:n]:
            code = str(row.get("HS6 ID", row.get("HS6", ""))).replace("HS", "").zfill(6)
            value_musd = round(row.get("Trade Value", 0) / 1_000_000, 2)
            hs2, hs4, hs6, hs2_name, hs4_name = self._hs2_from_hs6(code)
            result.append(
                {
                    "hs6Code": hs6,
                    "hs6Name": self._hs6_name(code),
                    "hs4Code": hs4,
                    "hs4Name": hs4_name,
                    "hs2Code": hs2,
                    "hs2Name": hs2_name,
                    "value_musd": value_musd,
                    "year": year,
                    "source": "OEC / UN Comtrade",
                }
            )

        if result:
            cache_service.set("oec_data", {"key": cache_key}, result, "oec_data")
        return result

    async def get_trade_balance_series(
        self, iso3: str, start: int = 2019, end: int = 2023
    ) -> List[Dict]:
        """Annual exports, imports, and balance for a country (MUSD)."""
        cache_key = f"oec_balance_{iso3}_{start}_{end}"
        cached = cache_service.get("oec_data", {"key": cache_key})
        if cached:
            return cached

        slug = ISO3_TO_OEC_SLUG.get(iso3)
        if not slug:
            return []

        # Fetch exports and imports separately then combine
        tasks = []
        for direction, param_key in [
            ("exports", "Exporter Country"),
            ("imports", "Importer Country"),
        ]:
            params = {
                "cube": "trade_i_baci_a_92",
                "drilldowns": "Year",
                "measures": "Trade Value",
                param_key: f"sa{slug}",
            }
            tasks.append(self._fetch(self.OEC_BASE, params))

        exp_data, imp_data = await asyncio.gather(*tasks)

        year_exports: Dict[int, float] = {}
        year_imports: Dict[int, float] = {}

        if exp_data and "data" in exp_data:
            for row in exp_data["data"]:
                y = int(row.get("Year", 0))
                if start <= y <= end:
                    year_exports[y] = round(row.get("Trade Value", 0) / 1_000_000, 1)

        if imp_data and "data" in imp_data:
            for row in imp_data["data"]:
                y = int(row.get("Year", 0))
                if start <= y <= end:
                    year_imports[y] = round(row.get("Trade Value", 0) / 1_000_000, 1)

        years = sorted(set(list(year_exports.keys()) + list(year_imports.keys())))
        result = []
        for y in years:
            exp = year_exports.get(y, 0.0)
            imp = year_imports.get(y, 0.0)
            result.append(
                {
                    "year": y,
                    "exports_musd": exp,
                    "imports_musd": imp,
                    "balance_musd": round(exp - imp, 1),
                    "source": "OEC / UN Comtrade (BACI)",
                }
            )

        if result:
            cache_service.set("oec_data", {"key": cache_key}, result, "oec_data")
        return result

    async def get_top_partners(
        self, iso3: str, direction: str = "export", year: int = 2022, n: int = 10
    ) -> List[Dict]:
        """Top N trade partners by direction ('export' or 'import')."""
        cache_key = f"oec_partners_{iso3}_{direction}_{year}"
        cached = cache_service.get("oec_data", {"key": cache_key})
        if cached:
            return cached[:n]

        slug = ISO3_TO_OEC_SLUG.get(iso3)
        if not slug:
            return []

        if direction == "export":
            country_param = {"Exporter Country": f"sa{slug}", "drilldowns": "Importer Country"}
        else:
            country_param = {"Importer Country": f"sa{slug}", "drilldowns": "Exporter Country"}

        params = {
            "cube": "trade_i_baci_a_92",
            "measures": "Trade Value",
            "Year": str(year),
            **country_param,
        }
        data = await self._fetch(self.OEC_BASE, params)
        if not data or "data" not in data:
            return []

        rows = sorted(data["data"], key=lambda r: r.get("Trade Value", 0), reverse=True)
        total = sum(r.get("Trade Value", 0) for r in rows) or 1

        result = []
        for row in rows[:n]:
            value_musd = round(row.get("Trade Value", 0) / 1_000_000, 1)
            partner_field = "Importer Country" if direction == "export" else "Exporter Country"
            partner = row.get(partner_field, "")
            result.append(
                {
                    "country": partner,
                    "value_musd": value_musd,
                    "share_percent": round(row.get("Trade Value", 0) / total * 100, 1),
                    "year": year,
                    "source": "OEC / UN Comtrade",
                }
            )

        if result:
            cache_service.set("oec_data", {"key": cache_key}, result, "oec_data")
        return result

    async def get_country_snapshot(self, iso3: str, year: int = 2022) -> Dict[str, Any]:
        """
        Combined snapshot: top exports, top imports, trade balance series, top partners.
        Used to ground Claude AI analysis in real data.
        """
        cache_key = f"oec_snapshot_{iso3}_{year}"
        cached = cache_service.get("oec_data", {"key": cache_key})
        if cached:
            return cached

        top_exp, top_imp, balance, exp_partners, imp_partners = await asyncio.gather(
            self.get_top_exports(iso3, year, n=10),
            self.get_top_imports(iso3, year, n=10),
            self.get_trade_balance_series(iso3, start=2019, end=year),
            self.get_top_partners(iso3, "export", year, n=5),
            self.get_top_partners(iso3, "import", year, n=5),
        )

        snapshot = {
            "iso3": iso3,
            "year": year,
            "top_exports": top_exp,
            "top_imports": top_imp,
            "trade_balance_series": balance,
            "top_export_partners": exp_partners,
            "top_import_partners": imp_partners,
            "source": "OEC / UN Comtrade (BACI HS92)",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        if any([top_exp, top_imp, balance]):
            cache_service.set("oec_data", {"key": cache_key}, snapshot, "oec_data")

        return snapshot

    async def validate_opportunity(self, opp: Dict, year: int = 2023) -> Dict:
        """
        Enrich an AI-generated opportunity with OEC real trade data.

        Input opp:
          {
            "product": {"hs6Code": "020120", ...},
            "exportingCountry": "DZA",
            "potentialPartner": "KEN",
            "potentialTradeValue": 1234.0,  (AI estimate)
            ...
          }

        Output: opp + {
          "oec_data": {
            "verified_trade_value": float (from OEC if exists),
            "confidence_score": 0.0–1.0,
            "data_quality": "verified|mixed|estimated",
            "source": "OEC BACI HS92",
          }
        }
        """
        hs6 = opp.get("product", {}).get("hs6Code", "").strip()
        exporter = opp.get("exportingCountry", "").strip().upper()[:3]
        importer = opp.get("potentialPartner", "").strip().upper()[:3]

        if not (hs6 and exporter and importer):
            return opp | {
                "oec_data": {
                    "verified_trade_value": None,
                    "confidence_score": 0.3,
                    "data_quality": "estimated",
                    "reason": "Missing HS6, exporter, or importer",
                }
            }

        # Try to find OEC trade flow
        try:
            # Build cache key for this bilateral flow
            cache_key = f"oec_flow_{exporter}_{importer}_{hs6}_{year}"
            cached = cache_service.get("oec_data", {"key": cache_key})
            if cached:
                return opp | {"oec_data": cached}

            # Query OEC API for this specific flow
            params = {
                "cube": "trade_i_baci_a_hs92",
                "drilldowns": "Year",
                "measures": "Trade Value",
                "filters": f"Exporter Country.iso3={exporter},Importer Country.iso3={importer},HS6.hs6={hs6},Year.Year={year}",
                "format": "jsonrecords",
            }

            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    "https://oec.world/api/olap-proxy/data",
                    params=params,
                    headers={"User-Agent": "AfCFTA-analyzer/1.0"},
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("data") and len(data["data"]) > 0:
                    trade_value = float(data["data"][0].get("Trade Value", 0) or 0)
                    value_musd = trade_value / 1_000_000
                    oec_result = {
                        "verified_trade_value": value_musd,
                        "confidence_score": 1.0,
                        "data_quality": "verified",
                        "source": "OEC BACI HS92",
                    }
                    cache_service.set("oec_data", {"key": cache_key}, oec_result, "oec_data")
                    return opp | {"oec_data": oec_result}
                else:
                    # No data in OEC for this flow (exploratory opportunity)
                    oec_result = {
                        "verified_trade_value": None,
                        "confidence_score": 0.5,
                        "data_quality": "estimated",
                        "reason": f"No OEC data for {exporter}→{importer} HS{hs6}",
                        "source": "AI analysis (OEC lookup failed)",
                    }
                    cache_service.set("oec_data", {"key": cache_key}, oec_result, "oec_data")
                    return opp | {"oec_data": oec_result}

        except httpx.TimeoutException:
            logger.warning(f"OEC timeout: {exporter}→{importer} HS{hs6}")
            return opp | {
                "oec_data": {
                    "verified_trade_value": None,
                    "confidence_score": 0.4,
                    "data_quality": "estimated",
                    "reason": "OEC API timeout",
                }
            }
        except Exception as e:
            logger.warning(f"OEC lookup failed ({exporter}→{importer}): {e}")
            return opp | {
                "oec_data": {
                    "verified_trade_value": None,
                    "confidence_score": 0.4,
                    "data_quality": "estimated",
                    "reason": f"OEC error: {str(e)[:50]}",
                }
            }

    async def enrich_opportunities(self, opportunities: List[Dict], year: int = 2023) -> List[Dict]:
        """
        Batch enrich AI opportunities with OEC data in parallel.
        Returns opportunities with oec_data field added to each.
        """
        tasks = [self.validate_opportunity(opp, year) for opp in opportunities]
        enriched = await asyncio.gather(*tasks)
        return enriched


# Singleton
oec_data_service = OECDataService()
