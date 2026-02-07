import logging
import json
import os
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "tariffs"


class TariffDataCollector:
    def __init__(self):
        self._hs6_db = None
        self._country_tariffs_map = None
        self._vat_rates = None
        self._other_taxes = None
        self._hs6_detailed = None
        self._loaded = False

    def _load_modules(self):
        if self._loaded:
            return
        from etl.hs6_csv_database import HS6_CSV_DATABASE
        from etl.hs6_database import HS6_DATABASE
        from etl.country_tariffs_complete import (
            COUNTRY_TARIFFS_MAP,
            COUNTRY_VAT_RATES,
            COUNTRY_OTHER_TAXES,
            ISO2_TO_ISO3,
            get_tariff_rate_for_country,
            get_zlecaf_tariff_rate,
            get_vat_rate_for_country,
            get_other_taxes_for_country,
            get_product_category,
        )
        from etl.country_hs6_detailed import COUNTRY_HS6_DETAILED

        self._hs6_csv_db = HS6_CSV_DATABASE
        self._hs6_db = HS6_DATABASE
        self._country_tariffs_map = COUNTRY_TARIFFS_MAP
        self._vat_rates = COUNTRY_VAT_RATES
        self._other_taxes = COUNTRY_OTHER_TAXES
        self._iso2_to_iso3 = ISO2_TO_ISO3
        self._hs6_detailed = COUNTRY_HS6_DETAILED
        self._get_tariff_rate = get_tariff_rate_for_country
        self._get_zlecaf_rate = get_zlecaf_tariff_rate
        self._get_vat_rate = get_vat_rate_for_country
        self._get_other_taxes = get_other_taxes_for_country
        self._get_product_category = get_product_category
        self._loaded = True

    def collect_country_tariffs(self, country_code: str) -> Dict[str, Any]:
        self._load_modules()
        country_code = country_code.upper()
        if len(country_code) == 2:
            country_code = self._iso2_to_iso3.get(country_code, country_code)

        vat_rate, vat_source = self._get_vat_rate(country_code)
        other_rate, other_detail = self._get_other_taxes(country_code)
        vat_info = self._vat_rates.get(country_code, {})
        detailed_tariffs = self._hs6_detailed.get(country_code, {})

        tariff_lines = []
        hs6_sources = {**self._hs6_csv_db, **self._hs6_db}

        for hs6_code, hs6_info in hs6_sources.items():
            chapter = hs6_code[:2]
            dd_rate, dd_source = self._get_tariff_rate(country_code, hs6_code)
            zlecaf_rate, zlecaf_source = self._get_zlecaf_rate(country_code, hs6_code)
            product_category = self._get_product_category(hs6_code)

            detailed = detailed_tariffs.get(hs6_code, {})
            if detailed and "default_dd" in detailed:
                dd_rate = detailed["default_dd"]
                dd_source = f"Tarif national détaillé {country_code}"

            sub_positions = []
            if detailed and "sub_positions" in detailed:
                for sp_code, sp_data in detailed["sub_positions"].items():
                    sub_positions.append({
                        "code": sp_code,
                        "dd": sp_data.get("dd", dd_rate),
                        "description_fr": sp_data.get("description_fr", ""),
                        "description_en": sp_data.get("description_en", ""),
                    })

            line = {
                "hs6": hs6_code,
                "chapter": chapter,
                "description_fr": hs6_info.get("description_fr", ""),
                "description_en": hs6_info.get("description_en", ""),
                "category": hs6_info.get("category", ""),
                "sensitivity": hs6_info.get("sensitivity", product_category),
                "dd_rate": round(dd_rate * 100, 2),
                "dd_source": dd_source,
                "zlecaf_rate": round(zlecaf_rate * 100, 2),
                "zlecaf_source": zlecaf_source,
                "vat_rate": round(vat_rate * 100, 2),
                "other_taxes_rate": round(other_rate * 100, 2),
                "total_import_taxes": round((dd_rate + vat_rate + other_rate) * 100, 2),
                "zlecaf_total_taxes": round((zlecaf_rate + vat_rate + other_rate) * 100, 2),
            }
            if sub_positions:
                line["sub_positions"] = sub_positions
                line["has_sub_positions"] = True
            else:
                line["has_sub_positions"] = False

            tariff_lines.append(line)

        tariff_lines.sort(key=lambda x: x["hs6"])

        result = {
            "country_code": country_code,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_tariff_lines": len(tariff_lines),
                "lines_with_sub_positions": sum(1 for l in tariff_lines if l.get("has_sub_positions")),
                "vat_rate_pct": round(vat_rate * 100, 2),
                "vat_source": vat_source,
                "other_taxes_pct": round(other_rate * 100, 2),
                "other_taxes_detail": {k: v for k, v in other_detail.items() if k != "other"},
                "dd_rate_range": {
                    "min": min(l["dd_rate"] for l in tariff_lines) if tariff_lines else 0,
                    "max": max(l["dd_rate"] for l in tariff_lines) if tariff_lines else 0,
                    "avg": round(sum(l["dd_rate"] for l in tariff_lines) / len(tariff_lines), 2) if tariff_lines else 0,
                },
                "chapters_covered": len(set(l["chapter"] for l in tariff_lines)),
            },
            "tariff_lines": tariff_lines,
        }

        return result

    def save_country_tariffs(self, country_code: str, data: Dict[str, Any]) -> str:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        filepath = DATA_DIR / f"{country_code.upper()}_tariffs.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data.get('tariff_lines', []))} tariff lines for {country_code} to {filepath}")
        return str(filepath)

    def load_country_tariffs(self, country_code: str) -> Optional[Dict[str, Any]]:
        filepath = DATA_DIR / f"{country_code.upper()}_tariffs.json"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_available_countries(self) -> List[str]:
        if not DATA_DIR.exists():
            return []
        return [f.stem.replace("_tariffs", "") for f in DATA_DIR.glob("*_tariffs.json")]

    async def collect_and_save_country(self, country_code: str) -> Dict[str, Any]:
        data = self.collect_country_tariffs(country_code)
        filepath = self.save_country_tariffs(country_code, data)
        return {
            "country_code": country_code,
            "success": True,
            "tariff_lines": data["summary"]["total_tariff_lines"],
            "lines_with_sub_positions": data["summary"]["lines_with_sub_positions"],
            "filepath": filepath,
        }

    async def collect_all_countries(self, country_codes: Optional[List[str]] = None, max_concurrency: int = 5) -> Dict[str, Any]:
        self._load_modules()

        if not country_codes:
            country_codes = list(self._country_tariffs_map.keys())

        results = []
        errors = []
        sem = asyncio.Semaphore(max_concurrency)

        async def process_country(code):
            async with sem:
                try:
                    result = await self.collect_and_save_country(code)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error collecting tariffs for {code}: {e}")
                    errors.append({"country_code": code, "error": str(e)})

        tasks = [process_country(code) for code in country_codes]
        await asyncio.gather(*tasks)

        return {
            "total_countries": len(country_codes),
            "succeeded": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
            "total_tariff_lines": sum(r["tariff_lines"] for r in results),
        }


_collector = None

def get_collector() -> TariffDataCollector:
    global _collector
    if _collector is None:
        _collector = TariffDataCollector()
    return _collector
