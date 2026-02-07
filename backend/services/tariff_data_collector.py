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
        self._sub_position_types = None
        self._country_tax_modules = {}
        self._loaded = False

    def _load_modules(self):
        if self._loaded:
            return
        from etl.hs6_csv_database import HS6_CSV_DATABASE
        from etl.hs6_database import HS6_DATABASE, SUB_POSITION_TYPES
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
        self._sub_position_types = SUB_POSITION_TYPES
        self._get_tariff_rate = get_tariff_rate_for_country
        self._get_zlecaf_rate = get_zlecaf_tariff_rate
        self._get_vat_rate = get_vat_rate_for_country
        self._get_other_taxes = get_other_taxes_for_country
        self._get_product_category = get_product_category

        try:
            from etl.country_taxes_algeria import get_dza_taxes_for_hs6
            self._country_tax_modules["DZA"] = get_dza_taxes_for_hs6
        except ImportError:
            pass

        self._loaded = True

    def _get_country_taxes(self, country_code: str, hs6_code: str, default_dd: float, default_vat: float, default_other: float, default_other_detail: dict) -> dict:
        tax_func = self._country_tax_modules.get(country_code)
        if tax_func:
            return tax_func(hs6_code)

        chapter = hs6_code[:2].zfill(2)
        taxes = []
        taxes.append({"tax": "D.D", "rate": default_dd, "observation": "Droit de Douane"})

        named_taxes = {k: v for k, v in default_other_detail.items() if k != "other" and isinstance(v, (int, float)) and v > 0}
        for tax_name, rate in named_taxes.items():
            taxes.append({"tax": tax_name.upper(), "rate": rate, "observation": ""})

        taxes.append({"tax": "T.V.A", "rate": default_vat, "observation": "Taxe sur la Valeur Ajoutée"})

        total = default_dd + default_vat + default_other
        advantages = [{
            "tax": "D.D",
            "rate": 0.0,
            "condition_fr": "Certificat d'Origine dans le cadre ZLECAf - Exonération DD",
            "condition_en": "Certificate of Origin under AfCFTA - DD Exemption",
        }]

        formalities = [
            {"code": "910", "document_fr": "Déclaration d'Importation du Produit", "document_en": "Product Import Declaration"},
        ]

        return {
            "dd_rate": default_dd,
            "daps_rate": 0.0,
            "prct_rate": 0.0,
            "tcs_rate": 0.0,
            "tva_rate": default_vat,
            "taxes_detail": taxes,
            "total_taxes_pct": total,
            "fiscal_advantages": advantages,
            "administrative_formalities": formalities,
        }

    def _generate_sub_positions(self, hs6_code: str, hs6_info: dict, dd_rate: float, country_code: str, detailed: dict) -> List[dict]:
        if detailed and "sub_positions" in detailed:
            subs = []
            for sp_code, sp_data in detailed["sub_positions"].items():
                sp_dd = sp_data.get("dd", dd_rate)
                if isinstance(sp_dd, float) and sp_dd < 1:
                    sp_dd = round(sp_dd * 100, 2)
                subs.append({
                    "code": sp_code,
                    "digits": len(sp_code),
                    "dd": sp_dd,
                    "description_fr": sp_data.get("description_fr", ""),
                    "description_en": sp_data.get("description_en", ""),
                    "source": f"Tarif national détaillé {country_code}",
                })
            return subs

        sp_types = hs6_info.get("typical_sub_position_types", [])
        if not sp_types or not hs6_info.get("has_sub_positions", False):
            return []

        subs = []
        for sp_type in sp_types:
            type_def = self._sub_position_types.get(sp_type)
            if not type_def:
                continue
            for opt in type_def.get("options", []):
                suffix = opt.get("code_suffix", "")
                full_code = hs6_code + suffix
                desc_fr = hs6_info.get("description_fr", "")
                desc_en = hs6_info.get("description_en", "")
                opt_fr = opt.get("fr", "")
                opt_en = opt.get("en", "")
                subs.append({
                    "code": full_code,
                    "digits": len(full_code),
                    "dd": dd_rate,
                    "description_fr": f"{desc_fr} - {opt_fr}" if opt_fr else desc_fr,
                    "description_en": f"{desc_en} - {opt_en}" if opt_en else desc_en,
                    "source": f"Nomenclature nationale {country_code} (type: {sp_type})",
                })
            break

        return subs

    def collect_country_tariffs(self, country_code: str) -> Dict[str, Any]:
        self._load_modules()
        country_code = country_code.upper()
        if len(country_code) == 2:
            country_code = self._iso2_to_iso3.get(country_code, country_code)

        vat_rate, vat_source = self._get_vat_rate(country_code)
        other_rate, other_detail = self._get_other_taxes(country_code)
        detailed_tariffs = self._hs6_detailed.get(country_code, {})

        vat_pct = round(vat_rate * 100, 2)
        other_pct = round(other_rate * 100, 2)

        tariff_lines = []
        hs6_sources = {**self._hs6_csv_db, **self._hs6_db}

        for hs6_code, hs6_info in hs6_sources.items():
            chapter = hs6_code[:2]
            dd_rate, dd_source = self._get_tariff_rate(country_code, hs6_code)
            zlecaf_rate, zlecaf_source = self._get_zlecaf_rate(country_code, hs6_code)
            product_category = self._get_product_category(hs6_code)

            detailed = detailed_tariffs.get(hs6_code, {})
            if detailed and "default_dd" in detailed:
                raw_dd = detailed["default_dd"]
                dd_rate_pct = raw_dd if raw_dd >= 1 else raw_dd * 100
                dd_rate_pct = round(dd_rate_pct, 2)
                dd_source = f"Tarif national détaillé {country_code}"
            else:
                dd_rate_pct = round(dd_rate * 100, 2)

            zlecaf_rate_pct = round(zlecaf_rate * 100, 2)

            country_taxes = self._get_country_taxes(
                country_code, hs6_code,
                dd_rate_pct, vat_pct, other_pct, other_detail
            )

            final_dd = country_taxes["dd_rate"]
            if final_dd != dd_rate_pct and country_code in self._country_tax_modules:
                dd_rate_pct = final_dd
                dd_source = f"Tarif national détaillé {country_code}"

            sub_positions = self._generate_sub_positions(
                hs6_code, hs6_info, dd_rate_pct, country_code, detailed
            )

            unit = hs6_info.get("unit", "KG")
            usage_group = hs6_info.get("category", hs6_info.get("usage_group", ""))

            line = {
                "hs6": hs6_code,
                "chapter": chapter,
                "description_fr": hs6_info.get("description_fr", ""),
                "description_en": hs6_info.get("description_en", ""),
                "category": usage_group,
                "unit": unit,
                "sensitivity": hs6_info.get("sensitivity", product_category),
                "dd_rate": dd_rate_pct,
                "dd_source": dd_source,
                "zlecaf_rate": zlecaf_rate_pct,
                "zlecaf_source": zlecaf_source,
                "vat_rate": country_taxes["tva_rate"],
                "other_taxes_rate": round(
                    country_taxes.get("daps_rate", 0) +
                    country_taxes.get("prct_rate", 0) +
                    country_taxes.get("tcs_rate", 0), 2
                ),
                "taxes_detail": country_taxes["taxes_detail"],
                "total_taxes_pct": country_taxes["total_taxes_pct"],
                "fiscal_advantages": country_taxes["fiscal_advantages"],
                "administrative_formalities": country_taxes["administrative_formalities"],
                "total_import_taxes": country_taxes["total_taxes_pct"],
                "zlecaf_total_taxes": round(zlecaf_rate_pct + country_taxes["tva_rate"] +
                    country_taxes.get("daps_rate", 0) +
                    country_taxes.get("prct_rate", 0) +
                    country_taxes.get("tcs_rate", 0), 2),
            }

            if sub_positions:
                line["sub_positions"] = sub_positions
                line["has_sub_positions"] = True
                line["sub_position_count"] = len(sub_positions)
            else:
                line["has_sub_positions"] = False
                line["sub_position_count"] = 0

            tariff_lines.append(line)

        tariff_lines.sort(key=lambda x: x["hs6"])

        total_sub_positions = sum(l.get("sub_position_count", 0) for l in tariff_lines)

        dd_rates = [l["dd_rate"] for l in tariff_lines]
        other_taxes_summary = {}
        if tariff_lines:
            sample = tariff_lines[0].get("taxes_detail", [])
            for t in sample:
                if t["tax"] not in ("D.D", "T.V.A"):
                    other_taxes_summary[t["tax"].lower().replace(".", "")] = t["rate"]

        result = {
            "country_code": country_code,
            "generated_at": datetime.utcnow().isoformat(),
            "data_format": "enhanced_v2",
            "summary": {
                "total_tariff_lines": len(tariff_lines),
                "total_sub_positions": total_sub_positions,
                "total_positions": len(tariff_lines) + total_sub_positions,
                "lines_with_sub_positions": sum(1 for l in tariff_lines if l.get("has_sub_positions")),
                "vat_rate_pct": country_taxes["tva_rate"] if tariff_lines else vat_pct,
                "vat_source": vat_source,
                "other_taxes_pct": round(other_rate * 100, 2),
                "other_taxes_detail": other_taxes_summary if other_taxes_summary else {k: v for k, v in other_detail.items() if k != "other"},
                "dd_rate_range": {
                    "min": min(dd_rates) if dd_rates else 0,
                    "max": max(dd_rates) if dd_rates else 0,
                    "avg": round(sum(dd_rates) / len(dd_rates), 2) if dd_rates else 0,
                },
                "chapters_covered": len(set(l["chapter"] for l in tariff_lines)),
                "has_detailed_taxes": country_code in self._country_tax_modules,
            },
            "tariff_lines": tariff_lines,
        }

        return result

    def save_country_tariffs(self, country_code: str, data: Dict[str, Any]) -> str:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        filepath = DATA_DIR / f"{country_code.upper()}_tariffs.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(data.get('tariff_lines', []))} tariff lines + {data['summary'].get('total_sub_positions', 0)} sub-positions for {country_code}")
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
            "total_sub_positions": data["summary"]["total_sub_positions"],
            "total_positions": data["summary"]["total_positions"],
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
            "total_sub_positions": sum(r.get("total_sub_positions", 0) for r in results),
            "total_positions": sum(r.get("total_positions", 0) for r in results),
        }


_collector = None

def get_collector() -> TariffDataCollector:
    global _collector
    if _collector is None:
        _collector = TariffDataCollector()
    return _collector
