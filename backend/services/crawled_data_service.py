import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

CRAWLED_DIR = Path(__file__).parent.parent / "data" / "crawled"


class CrawledDataService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
            cls._instance._country_data = {}
            cls._instance._code_index = {}
            cls._instance._hs6_index = {}
        return cls._instance

    def is_loaded(self) -> bool:
        return self._loaded and len(self._country_data) > 0

    def get_available_countries(self) -> List[str]:
        return list(self._country_data.keys())

    def load(self, force=False):
        if self._loaded and not force:
            return
        self._country_data = {}
        self._code_index = {}
        self._hs6_index = {}

        if not CRAWLED_DIR.exists():
            logger.warning(f"Crawled data directory not found: {CRAWLED_DIR}")
            return

        files = list(CRAWLED_DIR.glob("*_tariffs.json"))
        if not files:
            logger.warning("No crawled tariff data files found")
            return

        for f in files:
            try:
                country_code = f.stem.replace("_tariffs", "").upper()
                with open(f, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)

                positions_key = "sub_positions" if "sub_positions" in data else "positions"
                positions = data.get(positions_key, [])

                if not positions:
                    continue

                self._country_data[country_code] = {
                    "source": data.get("source", ""),
                    "extracted_at": data.get("extracted_at", ""),
                    "stats": data.get("stats", {}),
                    "country_name": data.get("country_name", country_code),
                    "total_positions": len(positions),
                }

                code_idx = {}
                hs6_idx = {}

                for pos in positions:
                    normalized = self._normalize_position(country_code, pos)
                    if not normalized:
                        continue

                    code_clean = normalized["code_clean"]
                    code_idx[code_clean] = normalized

                    hs6 = code_clean[:6]
                    if hs6 not in hs6_idx:
                        hs6_idx[hs6] = []
                    hs6_idx[hs6].append(normalized)

                self._code_index[country_code] = code_idx
                self._hs6_index[country_code] = hs6_idx
                logger.info(f"Crawled data loaded for {country_code}: {len(code_idx)} positions indexed")

            except Exception as e:
                logger.error(f"Error loading crawled data {f}: {e}")

        self._loaded = True
        total = sum(len(idx) for idx in self._code_index.values())
        logger.info(f"Crawled data loaded: {len(self._country_data)} countries, {total} total positions")

    EAC_COUNTRIES = {"KEN", "TZA", "UGA", "RWA", "BDI", "SSD", "COD"}

    def _normalize_position(self, country_code: str, pos: dict) -> Optional[dict]:
        if country_code == "DZA":
            return self._normalize_dza(pos)
        elif country_code == "TUN":
            return self._normalize_tun(pos)
        elif country_code == "MAR":
            return self._normalize_mar(pos)
        elif country_code == "NGA":
            return self._normalize_standard(pos, country_code)
        elif country_code in ("ZAF", "BWA", "LSO", "SWZ", "NAM"):
            return self._normalize_standard(pos, country_code)
        elif country_code in self.EAC_COUNTRIES:
            return self._normalize_eac_gha(pos, country_code)
        elif country_code == "GHA":
            return self._normalize_eac_gha(pos, country_code)
        elif country_code == "EGY":
            return self._normalize_egy(pos)
        elif country_code == "ETH":
            return self._normalize_eth(pos)
        elif country_code == "CIV":
            return self._normalize_civ(pos)
        return None

    def _normalize_standard(self, pos: dict, country_code: str) -> Optional[dict]:
        code_raw = pos.get("code_raw", "")
        code_clean = pos.get("code_clean", code_raw.replace(".", "").replace(" ", ""))
        if not code_clean:
            return None

        taxes = pos.get("taxes", [])
        if not isinstance(taxes, list):
            taxes = []

        PREFERENTIAL_CODES = ("EU_UK", "EFTA", "SADC", "MERCOSUR", "AfCFTA")
        for t in taxes:
            if t.get("code") in PREFERENTIAL_CODES:
                t["is_preferential"] = True

        return {
            "code_raw": code_raw,
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "statistical_unit": pos.get("statistical_unit", ""),
            "check_digit": pos.get("check_digit", ""),
            "taxes": taxes,
            "fiscal_advantages": pos.get("fiscal_advantages", []),
            "administrative_formalities": pos.get("administrative_formalities", []),
            "source": pos.get("source", ""),
            "country": country_code,
        }

    def _normalize_dza(self, pos: dict) -> Optional[dict]:
        raw_code = pos.get("raw_code", "")
        code_clean = raw_code.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes_raw = pos.get("taxes", {})
        taxes = []
        for tax_code, tax_info in taxes_raw.items():
            full_names = {
                "DD": "Droit de Douane",
                "TVA": "Taxe sur la Valeur Ajoutée",
                "TCS": "Taxe Conjoncturelle de Sauvegarde",
                "PRCT": "Prélèvement au titre de la Redevance de Conformité Technique",
                "DAPS": "Droit Additionnel Provisoire de Sauvegarde",
            }
            taxes.append({
                "code": tax_code,
                "name": full_names.get(tax_code, tax_info.get("name", tax_code)),
                "rate_pct": tax_info.get("rate"),
                "raw_value": tax_info.get("raw", ""),
                "source": "conformepro.dz",
            })

        return {
            "code_raw": raw_code,
            "code_clean": code_clean,
            "designation": pos.get("name", ""),
            "chapter": pos.get("chapter", ""),
            "taxes": taxes,
            "fiscal_advantages": pos.get("advantages", []),
            "administrative_formalities": pos.get("formalities", []),
            "source": "conformepro.dz",
            "country": "DZA",
        }

    def _normalize_tun(self, pos: dict) -> Optional[dict]:
        raw_code = pos.get("hs_code", "")
        code_clean = raw_code.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        for tax in pos.get("taxes_import", []):
            full_names = {
                "DDDROIT": "Droit de Douane à l'Importation",
                "TVA/APTAXE": "Taxe sur la Valeur Ajoutée",
                "RPD/IMPORREDEV": "Redevance de Prestation Douanière à l'Importation",
                "DC/EXPORTDROIT": "Droit de Consommation",
                "FODEC/IMFODEC": "Fonds de Développement de la Compétitivité Industrielle",
            }
            tax_code = tax.get("code", "")
            taxes.append({
                "code": tax_code,
                "name": full_names.get(tax_code, tax.get("name", tax_code)),
                "rate_pct": tax.get("rate_pct"),
                "raw_value": tax.get("raw_value", ""),
                "specific_value": tax.get("specific_value", ""),
                "assiette": tax.get("assiette", ""),
                "source": "douane.gov.tn",
            })

        regulations = pos.get("regulations", [])
        formalities = []
        for reg in regulations:
            if isinstance(reg, dict):
                formalities.append(reg.get("text", str(reg)))
            else:
                formalities.append(str(reg))

        return {
            "code_raw": raw_code,
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": pos.get("chapter", ""),
            "taxes": taxes,
            "fiscal_advantages": pos.get("preferential_tariffs", []),
            "administrative_formalities": formalities,
            "source": "douane.gov.tn",
            "country": "TUN",
        }

    def _normalize_mar(self, pos: dict) -> Optional[dict]:
        raw_code = pos.get("code", "")
        code_clean = raw_code.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        for tax_name, tax_value in pos.get("taxes", {}).items():
            taxes.append({
                "code": tax_name.split("(")[-1].rstrip(")") if "(" in tax_name else tax_name,
                "name": tax_name,
                "rate_pct": self._parse_rate(tax_value),
                "raw_value": tax_value,
                "source": "douane.gov.ma/adil",
            })

        return {
            "code_raw": raw_code,
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": pos.get("chapter", ""),
            "taxes": taxes,
            "fiscal_advantages": [],
            "administrative_formalities": pos.get("formalities", []),
            "source": "douane.gov.ma/adil",
            "country": "MAR",
        }

    EAC_GHA_TAX_CODES = {
        "CET Import Duty (Droit de Douane)": "CET_ID",
        "Import Declaration Fee (IDF)": "IDF",
        "Railway Development Levy (RDL)": "RDL",
        "Value Added Tax (VAT)": "VAT",
        "Import Duty (ECOWAS CET)": "ID",
        "Import Excise Duty": "EXC",
        "Export Duty": "ED",
        "National Health Insurance Levy (NHIL)": "NHIL",
    }

    def _normalize_eac_gha(self, pos: dict, country_code: str) -> Optional[dict]:
        code_raw = pos.get("hs_code", "") or pos.get("hs_code_display", "")
        code_clean = code_raw.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        for td in taxes_detail:
            tax_name = td.get("tax_name", "")
            rate = td.get("rate")
            tax_code = self.EAC_GHA_TAX_CODES.get(tax_name, tax_name.split("(")[-1].rstrip(")").strip() if "(" in tax_name else tax_name)
            taxes.append({
                "code": tax_code,
                "name": tax_name,
                "rate_pct": rate,
                "raw_value": f"{rate}%" if rate is not None else "",
                "base": td.get("base", ""),
                "source": pos.get("source", ""),
            })

        return {
            "code_raw": pos.get("hs_code_display", pos.get("hs_code", "")),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "statistical_unit": pos.get("unit", ""),
            "taxes": taxes,
            "fiscal_advantages": pos.get("fiscal_advantages", []),
            "administrative_formalities": pos.get("administrative_formalities", []),
            "source": pos.get("source", ""),
            "country": country_code,
        }

    def _normalize_egy(self, pos: dict) -> Optional[dict]:
        code_clean = pos.get("code_clean", "")
        if not code_clean:
            code_raw = pos.get("code", "")
            code_clean = code_raw.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        for td in taxes_detail:
            tax_code = td.get("tax_code", "")
            taxes.append({
                "code": tax_code,
                "name": td.get("tax_name", tax_code),
                "rate_pct": td.get("rate"),
                "raw_value": f"{td.get('rate')}%" if td.get('rate') is not None else "",
                "source": "egyptariffs.com",
            })

        if not taxes_detail:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                tax_names = {
                    "ID": "Import Duty (ضريبة الوارد)",
                    "VAT": "VAT (ضريبة القيمة المضافة)",
                }
                for code, rate in raw_taxes.items():
                    taxes.append({
                        "code": code,
                        "name": tax_names.get(code, code),
                        "rate_pct": rate,
                        "raw_value": f"{rate}%",
                        "source": "egyptariffs.com",
                    })

        return {
            "code_raw": pos.get("code", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "designation_en": pos.get("designation_en", ""),
            "chapter": code_clean[:2] if len(code_clean) >= 2 else "",
            "taxes": taxes,
            "fiscal_advantages": [],
            "administrative_formalities": pos.get("administrative_formalities", []),
            "source": "egyptariffs.com",
            "country": "EGY",
        }

    def _normalize_eth(self, pos: dict) -> Optional[dict]:
        code_clean = pos.get("code_clean", "")
        if not code_clean:
            code_raw = pos.get("code", "")
            code_clean = code_raw.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        for td in taxes_detail:
            tax_code = td.get("tax_code", "")
            taxes.append({
                "code": tax_code,
                "name": td.get("tax_name", tax_code),
                "rate_pct": td.get("rate"),
                "raw_value": f"{td.get('rate')}%" if td.get('rate') is not None else "",
                "source": "customs.erca.gov.et",
            })

        if not taxes_detail:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                eth_tax_names = {
                    "DR": "Customs Duty",
                    "ER": "Excise Tax",
                    "VAT": "Value Added Tax",
                    "WHR": "Withholding Tax",
                    "SR": "Surtax",
                    "EXR": "Export Tax",
                    "D2R": "COMESA Preferential Duty",
                    "DSR": "Development Surcharge",
                    "DAR": "Additional Duty",
                }
                for code, rate in raw_taxes.items():
                    if rate and rate > 0:
                        taxes.append({
                            "code": code,
                            "name": eth_tax_names.get(code, code),
                            "rate_pct": rate,
                            "raw_value": f"{rate}%",
                            "source": "customs.erca.gov.et",
                        })

        comesa_duty = pos.get("comesa_duty")
        fiscal_advantages = []
        if comesa_duty is not None and comesa_duty >= 0:
            fiscal_advantages.append({
                "name": "COMESA Preferential Rate",
                "rate_pct": comesa_duty,
                "description": f"Reduced duty rate of {comesa_duty}% for COMESA member countries"
            })

        return {
            "code_raw": pos.get("code", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "designation_en": pos.get("designation_en", ""),
            "chapter": code_clean[:2] if len(code_clean) >= 2 else "",
            "statistical_unit": pos.get("unit", ""),
            "taxes": taxes,
            "fiscal_advantages": fiscal_advantages,
            "administrative_formalities": [],
            "source": "customs.erca.gov.et",
            "country": "ETH",
        }

    def _normalize_civ(self, pos: dict) -> Optional[dict]:
        code_clean = pos.get("code_clean", "")
        if not code_clean:
            code_raw = pos.get("code", "")
            code_clean = code_raw.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        for td in taxes_detail:
            tax_code = td.get("tax_code", "")
            rate = td.get("rate")
            if rate is None:
                continue
            taxes.append({
                "code": tax_code,
                "name": td.get("tax_name", tax_code),
                "rate_pct": rate,
                "raw_value": f"{rate}%" if td.get("rate_type") == "ad_valorem" else f"{rate} FCFA",
                "source": "guce.gouv.ci",
            })

        if not taxes:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                civ_tax_names = {
                    "DD": "Droit de Douane",
                    "TVA": "Taxe sur la Valeur Ajoutée",
                    "DUS": "Droit Unique de Sortie",
                    "TUB": "Taxe Unique sur les Boissons",
                    "TSB_PT": "Taxe Spéciale Boissons",
                    "PSV": "Prélèvement Spécial de Viabilité",
                    "TUF": "Taxe Unique sur les Fuels",
                    "SPEC": "Montant Spécifique",
                }
                for code, rate in raw_taxes.items():
                    if rate is not None:
                        taxes.append({
                            "code": code,
                            "name": civ_tax_names.get(code, code),
                            "rate_pct": rate,
                            "raw_value": f"{rate}%",
                            "source": "guce.gouv.ci",
                        })

        fiscal_advantages = []
        notes = [
            "PCS (Prélèvement Communautaire de Solidarité): 0.8% sur toutes importations",
            "PUA (Prélèvement Union Africaine): 0.2% sur toutes importations",
            "RS (Redevance Statistique): 1% sur toutes importations",
        ]

        return {
            "code_raw": pos.get("code", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": code_clean[:2] if len(code_clean) >= 2 else "",
            "statistical_unit": pos.get("unit", ""),
            "taxes": taxes,
            "fiscal_advantages": fiscal_advantages,
            "administrative_formalities": [],
            "source": "guce.gouv.ci",
            "country": "CIV",
            "notes": notes,
        }

    def _parse_rate(self, value: str) -> Optional[float]:
        if not value or not isinstance(value, str):
            return None
        cleaned = value.replace("%", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    def lookup(self, country_code: str, hs_code: str) -> Optional[dict]:
        country_code = country_code.upper()
        hs_code_clean = hs_code.replace(".", "").replace(" ", "")

        idx = self._code_index.get(country_code, {})
        if not idx:
            return None

        result = idx.get(hs_code_clean)
        if result:
            return result

        for length in range(len(hs_code_clean) - 1, 5, -1):
            prefix = hs_code_clean[:length]
            for code, data in idx.items():
                if code.startswith(prefix):
                    return data
            matches = [data for code, data in idx.items() if code.startswith(prefix)]
            if len(matches) == 1:
                return matches[0]

        return None

    def lookup_by_hs6(self, country_code: str, hs6_code: str) -> List[dict]:
        country_code = country_code.upper()
        hs6_clean = hs6_code.replace(".", "").replace(" ", "")[:6].zfill(6)
        return self._hs6_index.get(country_code, {}).get(hs6_clean, [])

    def search(self, country_code: str, query: str, limit: int = 50) -> List[dict]:
        country_code = country_code.upper()
        idx = self._code_index.get(country_code, {})
        if not idx:
            return []

        query_lower = query.lower()
        results = []
        for code, data in idx.items():
            if query_lower in code or query_lower in data.get("designation", "").lower():
                results.append(data)
                if len(results) >= limit:
                    break
        return results

    def get_stats(self) -> dict:
        return {
            "loaded": self._loaded,
            "countries": list(self._country_data.keys()),
            "country_details": {
                code: {
                    "positions": info["total_positions"],
                    "source": info["source"],
                    "extracted_at": info["extracted_at"],
                }
                for code, info in self._country_data.items()
            },
            "total_positions": sum(len(idx) for idx in self._code_index.values()),
        }


crawled_service = CrawledDataService()
