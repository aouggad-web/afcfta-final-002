import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "tariffs"


class TariffDataService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
            cls._instance._country_data = {}
            cls._instance._hs6_index = {}
            cls._instance._sub_position_index = {}
        return cls._instance

    def is_loaded(self) -> bool:
        return self._loaded and len(self._country_data) > 0

    def load(self, force=False):
        if self._loaded and not force:
            return
        self._country_data = {}
        self._hs6_index = {}
        self._sub_position_index = {}

        if not DATA_DIR.exists():
            logger.warning(f"Tariff data directory not found: {DATA_DIR}")
            return

        files = list(DATA_DIR.glob("*_tariffs.json"))
        if not files:
            logger.warning("No tariff data files found")
            return

        for f in files:
            try:
                country_code = f.stem.replace("_tariffs", "").upper()
                with open(f, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                self._country_data[country_code] = data

                hs6_idx = {}
                sub_idx = {}
                for line in data.get("tariff_lines", []):
                    hs6 = line.get("hs6", "")
                    hs6_idx[hs6] = line
                    for sp in line.get("sub_positions", []):
                        code = sp.get("code", "")
                        sub_idx[code] = {
                            "dd": sp.get("dd", line.get("dd_rate", 0)),
                            "description_fr": sp.get("description_fr", ""),
                            "description_en": sp.get("description_en", ""),
                            "source": sp.get("source", ""),
                            "parent_hs6": hs6,
                            "parent_line": line,
                        }

                self._hs6_index[country_code] = hs6_idx
                self._sub_position_index[country_code] = sub_idx
            except Exception as e:
                logger.error(f"Error loading {f}: {e}")

        self._loaded = True
        logger.info(f"Tariff data loaded: {len(self._country_data)} countries, "
                     f"{sum(len(idx) for idx in self._hs6_index.values())} HS6 lines, "
                     f"{sum(len(idx) for idx in self._sub_position_index.values())} sub-positions")

    def get_country_codes(self) -> List[str]:
        return list(self._country_data.keys())

    def get_tariff_line(self, country_code: str, hs6_code: str) -> Optional[Dict]:
        country_code = country_code.upper()
        idx = self._hs6_index.get(country_code, {})
        return idx.get(hs6_code)

    def get_dd_rate(self, country_code: str, hs6_code: str) -> Tuple[float, str]:
        line = self.get_tariff_line(country_code, hs6_code)
        if line:
            dd_pct = line.get("dd_rate", 0)
            source = line.get("dd_source", f"Tarif national {country_code}")
            return (dd_pct / 100.0, source)
        return (None, "")

    def get_zlecaf_rate(self, country_code: str, hs6_code: str) -> Tuple[float, str]:
        line = self.get_tariff_line(country_code, hs6_code)
        if line:
            zlecaf_pct = line.get("zlecaf_rate", 0)
            source = line.get("zlecaf_source", f"ZLECAf {country_code}")
            return (zlecaf_pct / 100.0, source)
        return (None, "")

    def get_vat_rate(self, country_code: str) -> Tuple[float, str]:
        country_code = country_code.upper()
        data = self._country_data.get(country_code, {})
        summary = data.get("summary", {})
        vat_pct = summary.get("vat_rate_pct", 0)
        source = summary.get("vat_source", f"TVA {country_code}")
        return (vat_pct / 100.0, source)

    def get_other_taxes(self, country_code: str) -> Tuple[float, Dict]:
        country_code = country_code.upper()
        data = self._country_data.get(country_code, {})
        summary = data.get("summary", {})
        other_pct = summary.get("other_taxes_pct", 0)
        detail = summary.get("other_taxes_detail", {})
        return (other_pct / 100.0, detail)

    def get_sub_position_rate(self, country_code: str, full_code: str) -> Tuple[Optional[float], str, str]:
        country_code = country_code.upper()
        full_code = full_code.replace(".", "").replace(" ", "")
        idx = self._sub_position_index.get(country_code, {})

        sp = idx.get(full_code)
        if sp:
            dd_pct = sp.get("dd", 0)
            desc = sp.get("description_fr", sp.get("description_en", ""))
            source = sp.get("source", f"Sous-position {country_code}")
            return (dd_pct / 100.0, desc, source)

        hs6 = full_code[:6]
        line = self.get_tariff_line(country_code, hs6)
        if line:
            dd_pct = line.get("dd_rate", 0)
            desc = line.get("description_fr", "")
            return (dd_pct / 100.0, desc, f"Taux HS6 parent {hs6}")

        return (None, "", "")

    def get_tariff_precision_info(self, country_code: str, hs_code_clean: str) -> Dict:
        country_code = country_code.upper()
        hs6 = hs_code_clean[:6].zfill(6)

        if len(hs_code_clean) > 6:
            rate, desc, source = self.get_sub_position_rate(country_code, hs_code_clean)
            if rate is not None:
                return {
                    "rate": rate,
                    "source": source,
                    "precision": "sub_position",
                    "sub_position_code": hs_code_clean,
                    "sub_position_description": desc,
                    "description_fr": desc,
                }

        line = self.get_tariff_line(country_code, hs6)
        if line:
            dd_pct = line.get("dd_rate", 0)
            return {
                "rate": dd_pct / 100.0,
                "source": line.get("dd_source", f"Tarif national {country_code}"),
                "precision": "hs6_collected",
                "sub_position_code": None,
                "sub_position_description": None,
                "description_fr": line.get("description_fr", ""),
            }

        return None

    def get_sub_positions_for_hs6(self, country_code: str, hs6_code: str) -> List[Dict]:
        line = self.get_tariff_line(country_code.upper(), hs6_code)
        if line and line.get("sub_positions"):
            return line["sub_positions"]
        return []

    def get_country_summary(self, country_code: str) -> Optional[Dict]:
        country_code = country_code.upper()
        data = self._country_data.get(country_code, {})
        return data.get("summary")

    def get_stats(self) -> Dict:
        total_hs6 = sum(len(idx) for idx in self._hs6_index.values())
        total_sub = sum(len(idx) for idx in self._sub_position_index.values())
        return {
            "loaded": self._loaded,
            "countries": len(self._country_data),
            "total_hs6_lines": total_hs6,
            "total_sub_positions": total_sub,
            "total_positions": total_hs6 + total_sub,
        }


tariff_service = TariffDataService()
