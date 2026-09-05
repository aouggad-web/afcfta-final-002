import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
            cls._instance._country_files = {}
            cls._instance._country_loaded = set()
        return cls._instance

    def is_loaded(self) -> bool:
        return self._loaded

    def get_available_countries(self) -> List[str]:
        return list(self._country_files.keys())

    def load(self, force=False):
        """Scan available country files without loading data (lazy loading per country)."""
        if self._loaded and not force:
            return

        self._country_data = {}
        self._code_index = {}
        self._hs6_index = {}
        self._country_files = {}
        self._country_loaded = set()

        if not CRAWLED_DIR.exists():
            logger.warning(f"Crawled data directory not found: {CRAWLED_DIR}")
            return

        files = list(CRAWLED_DIR.glob("*_tariffs.json"))
        if not files:
            logger.warning("No crawled tariff data files found")
            return

        for f in files:
            country_code = f.stem.replace("_tariffs", "").upper()
            self._country_files[country_code] = f

        self._loaded = True
        logger.info(
            f"Crawled data service ready: {len(self._country_files)} countries registered (lazy loading)"
        )

    def _load_country(self, country_code: str) -> bool:
        """Load a single country's tariff data into memory on demand."""
        if country_code in self._country_loaded:
            return True

        f = self._country_files.get(country_code)
        if not f or not f.exists():
            return False

        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)

            data_format = data.get("data_format", "")

            if "sub_positions" in data and not data.get("tariff_lines"):
                # DZA enhanced format with top-level sub_positions
                positions = data.get("sub_positions", [])
            elif "tariff_lines" in data:
                positions = self._convert_tariff_lines_to_positions(data, country_code)
            else:
                positions_key = "positions"
                positions = data.get(positions_key, [])

            if not positions:
                self._country_loaded.add(country_code)
                return False

            self._country_data[country_code] = {
                "source": data.get("source", data.get("data_format", "")),
                "extracted_at": data.get("extracted_at", data.get("generated_at", "")),
                "stats": data.get("stats", data.get("summary", {})),
                "country_name": data.get("country_name", country_code),
                "total_positions": len(positions),
                "data_format": data_format,
            }

            code_idx = {}
            hs6_idx = {}

            file_source_quality = data.get("source_quality", "")

            for pos in positions:
                normalized = self._normalize_position(country_code, pos)
                if not normalized:
                    continue

                normalized["source_quality"] = file_source_quality

                code_clean = normalized["code_clean"]
                code_idx[code_clean] = normalized

                hs6 = code_clean[:6]
                if hs6 not in hs6_idx:
                    hs6_idx[hs6] = []
                hs6_idx[hs6].append(normalized)

            self._code_index[country_code] = code_idx
            self._hs6_index[country_code] = hs6_idx
            self._country_loaded.add(country_code)
            logger.info(f"Lazy-loaded {country_code}: {len(code_idx)} positions indexed")
            return True

        except Exception as e:
            logger.error(f"Error lazy-loading {country_code}: {e}")
            self._country_loaded.add(country_code)
            return False

    def _ensure_country_loaded(self, country_code: str) -> bool:
        """Ensure a country's data is in memory, loading it if needed."""
        if country_code not in self._country_loaded:
            return self._load_country(country_code)
        return country_code in self._code_index

    def _convert_tariff_lines_to_positions(self, data: dict, country_code: str) -> List[dict]:
        """Convert new tariff_lines format to positions format"""
        positions = []
        tariff_lines = data.get("tariff_lines", [])

        for line in tariff_lines:
            hs6 = line.get("hs6", "")
            if not hs6:
                continue

            # Build taxes list from taxes_detail
            taxes = []
            taxes_detail = line.get("taxes_detail", {})
            if isinstance(taxes_detail, dict):
                for tax_code, tax_info in taxes_detail.items():
                    if isinstance(tax_info, dict):
                        taxes.append(
                            {
                                "code": tax_code,
                                "name": tax_info.get("label", tax_code),
                                "rate": tax_info.get("rate", 0),
                                "is_preferential": tax_code.upper()
                                in ("ZLECAF", "AFCFTA", "CEDEAO", "EAC", "SADC", "CEMAC"),
                            }
                        )
                    elif isinstance(tax_info, (int, float)):
                        taxes.append({"code": tax_code, "name": tax_code, "rate": tax_info})

            # Add DD (customs duty) if present
            dd_rate = line.get("dd_rate", 0)
            if dd_rate and not any(t.get("code") == "DD" for t in taxes):
                taxes.insert(0, {"code": "DD", "name": "Droit de Douane", "rate": dd_rate})

            # Add VAT if present
            vat_rate = line.get("vat_rate", 0)
            if vat_rate and not any(t.get("code") in ("TVA", "VAT") for t in taxes):
                taxes.append(
                    {"code": "TVA", "name": "Taxe sur la Valeur Ajoutée", "rate": vat_rate}
                )

            # Create main position for HS6
            main_position = {
                "code_raw": hs6,
                "code_clean": hs6,
                "designation": line.get("description_fr", line.get("description_en", "")),
                "description_fr": line.get("description_fr", ""),
                "description_en": line.get("description_en", ""),
                "chapter": line.get("chapter", hs6[:2] if len(hs6) >= 2 else ""),
                "heading": hs6[:4] if len(hs6) >= 4 else "",
                "statistical_unit": line.get("unit", ""),
                "taxes": taxes,
                "dd_rate": dd_rate,
                "vat_rate": vat_rate,
                "zlecaf_rate": line.get("zlecaf_rate"),
                "zlecaf_source": line.get("zlecaf_source", ""),
                "total_taxes_pct": line.get("total_taxes_pct", 0),
                "zlecaf_total_taxes": line.get("zlecaf_total_taxes"),
                "fiscal_advantages": line.get("fiscal_advantages", []),
                "administrative_formalities": line.get("administrative_formalities", []),
                "source": line.get("dd_source", ""),
                "country": country_code,
                "is_enhanced_format": True,
            }
            positions.append(main_position)

            # Add sub-positions if available
            sub_positions = line.get("sub_positions", [])
            for sp in sub_positions:
                sp_code = sp.get("code", "")
                if not sp_code:
                    continue

                sp_taxes = []
                sp_dd = sp.get("dd", dd_rate)
                if sp_dd:
                    sp_taxes.append({"code": "DD", "name": "Droit de Douane", "rate": sp_dd})
                if vat_rate:
                    sp_taxes.append(
                        {"code": "TVA", "name": "Taxe sur la Valeur Ajoutée", "rate": vat_rate}
                    )

                sub_position = {
                    "code_raw": sp_code,
                    "code_clean": sp_code.replace(".", "").replace(" ", ""),
                    "designation": sp.get("description_fr", sp.get("description_en", "")),
                    "description_fr": sp.get("description_fr", ""),
                    "description_en": sp.get("description_en", ""),
                    "chapter": sp_code[:2] if len(sp_code) >= 2 else "",
                    "heading": sp_code[:4] if len(sp_code) >= 4 else "",
                    "statistical_unit": sp.get("unit", ""),
                    "taxes": sp_taxes,
                    "dd_rate": sp_dd,
                    "vat_rate": vat_rate,
                    "zlecaf_rate": line.get("zlecaf_rate"),
                    "fiscal_advantages": line.get("fiscal_advantages", []),
                    "administrative_formalities": line.get("administrative_formalities", []),
                    "source": sp.get("source", ""),
                    "country": country_code,
                    "parent_hs6": hs6,
                    "is_enhanced_format": True,
                }
                positions.append(sub_position)

        return positions

    # All 54 African countries supported
    EAC_COUNTRIES = {"KEN", "TZA", "UGA", "RWA", "BDI", "SSD", "COD"}
    ECOWAS_TEC_COUNTRIES = {
        "BEN",
        "BFA",
        "MLI",
        "NER",
        "TGO",
        "GIN",
        "SEN",
        "CIV",
        "GHA",
        "NGA",
        "GMB",
        "GNB",
        "LBR",
        "SLE",
        "CPV",
    }
    CEMAC_TEC_COUNTRIES = {"GAB", "COG", "TCD", "CAF", "CMR", "GNQ"}
    SACU_COUNTRIES = {"ZAF", "BWA", "LSO", "SWZ", "NAM"}
    NORTH_AFRICA = {"DZA", "TUN", "MAR", "EGY", "LBY"}
    COMESA_OTHER = {
        "ETH",
        "ERI",
        "DJI",
        "SOM",
        "SDN",
        "MWI",
        "ZMB",
        "ZWE",
        "MUS",
        "SYC",
        "COM",
        "MDG",
        "MOZ",
        "AGO",
        "MRT",
        "STP",
    }
    # Pays sourcés via WITS/TRAINS (wits_source.py) : positions clées "hs_code",
    # taxes en dict {code: {...}} (contrat v2) — même forme que DZA/EGY/ETH,
    # pas la forme "code_raw"/liste de _normalize_standard.
    WITS_COUNTRIES = {
        "AGO",
        "COM",
        "LBY",
        "MDG",
        "MOZ",
        "MRT",
        "MUS",
        "MWI",
        "SDN",
        "STP",
        "SYC",
        "ZMB",
        "ZWE",
    }

    def _normalize_position(self, country_code: str, pos: dict) -> Optional[dict]:
        # Check if it's already in enhanced format (from tariff_lines conversion)
        if pos.get("is_enhanced_format"):
            return self._normalize_enhanced_format(pos, country_code)

        # Original normalization logic for old formats
        if country_code == "DZA":
            return self._normalize_dza(pos)
        elif country_code == "TUN":
            return self._normalize_tun(pos)
        elif country_code == "MAR":
            return self._normalize_mar(pos)
        elif country_code == "NGA":
            return self._normalize_standard(pos, country_code)
        elif country_code in self.SACU_COUNTRIES:
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
        elif country_code == "SEN":
            return self._normalize_sen(pos)
        elif country_code == "CMR":
            return self._normalize_cmr(pos)
        elif country_code in self.ECOWAS_TEC_COUNTRIES:
            return self._normalize_ecowas_member(pos, country_code)
        elif country_code in self.CEMAC_TEC_COUNTRIES:
            return self._normalize_cemac_member(pos, country_code)
        elif country_code in self.WITS_COUNTRIES:
            return self._normalize_wits(pos, country_code)
        # Fallback for any other country - use standard normalization
        return self._normalize_standard(pos, country_code)

    def _normalize_enhanced_format(self, pos: dict, country_code: str) -> Optional[dict]:
        """Normalize positions that are already in enhanced format"""
        code_clean = pos.get("code_clean", "")
        if not code_clean:
            return None

        return {
            "code_raw": pos.get("code_raw", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "description_fr": pos.get("description_fr", ""),
            "description_en": pos.get("description_en", ""),
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "statistical_unit": pos.get("statistical_unit", ""),
            "check_digit": pos.get("check_digit", ""),
            "taxes": pos.get("taxes", []),
            "dd_rate": pos.get("dd_rate", 0),
            "vat_rate": pos.get("vat_rate", 0),
            "zlecaf_rate": pos.get("zlecaf_rate"),
            "zlecaf_source": pos.get("zlecaf_source", ""),
            "total_taxes_pct": pos.get("total_taxes_pct", 0),
            "zlecaf_total_taxes": pos.get("zlecaf_total_taxes"),
            "fiscal_advantages": pos.get("fiscal_advantages", []),
            "administrative_formalities": pos.get("administrative_formalities", []),
            "source": pos.get("source", ""),
            "country": country_code,
            "parent_hs6": pos.get("parent_hs6", ""),
        }

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
        # Prefer hs_code (already clean 10-digit) over raw_code transformation
        code_clean = pos.get("hs_code", "") or raw_code.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        FULL_NAMES = {
            "DD": "Droit de Douane",
            "TVA": "Taxe sur la Valeur Ajoutée",
            "TCS": "Taxe de Contribution de Solidarité",
            "PRCT": "Précompte sur Impôt",
            "DAPS": "Droit Additionnel Provisoire de Sauvegarde",
        }

        taxes_raw = pos.get("taxes", {})
        taxes = []
        dd_rate = 0.0
        daps_rate = 0.0
        vat_rate = 0.0
        total_taxes = 0.0

        # Ordering: DAPS → DD → PRCT → TCS → TVA
        order = ["DAPS", "DD", "PRCT", "TCS", "TVA"]
        taxes_sorted = {k: taxes_raw[k] for k in order if k in taxes_raw}
        # Add any extra taxes not in the ordered list
        for k, v in taxes_raw.items():
            if k not in taxes_sorted:
                taxes_sorted[k] = v

        for tax_code, tax_info in taxes_sorted.items():
            if not isinstance(tax_info, dict):
                continue
            rate = float(tax_info.get("rate", 0) or 0)
            entry = {
                "code": tax_code,
                "name": FULL_NAMES.get(tax_code, tax_info.get("name", tax_code)),
                "rate_pct": rate,
                "raw_value": tax_info.get("raw", f"{rate:.0f}%"),
                "source": tax_info.get("source", "conformepro.dz"),
            }
            taxes.append(entry)
            total_taxes += rate
            if tax_code == "DD":
                dd_rate = rate
            elif tax_code == "DAPS":
                daps_rate = rate
            elif tax_code in ("TVA", "VAT"):
                vat_rate = rate

        return {
            "code_raw": raw_code,
            "code_clean": code_clean,
            "hs_code": code_clean,
            "hs6": code_clean[:6] if len(code_clean) >= 6 else code_clean,
            "designation": pos.get("name", ""),
            "description": pos.get("description", ""),
            "designation_full": pos.get("designation_full", ""),
            "chapter": pos.get("chapter", ""),
            "heading": pos.get("heading", ""),
            "section": pos.get("section", ""),
            "taxes": taxes,
            "taxes_detail": taxes_sorted,
            "dd_rate": dd_rate,
            "daps_rate": daps_rate,
            "vat_rate": vat_rate,
            "zlecaf_rate": None,
            "total_taxes_pct": total_taxes,
            "zlecaf_total_taxes": total_taxes,
            "fiscal_advantages": pos.get("advantages", []),
            "administrative_formalities": pos.get("formalities", []),
            "source": pos.get("source", "conformepro.dz"),
            "source_quality": pos.get("source_quality", ""),
            "source_url": pos.get("source_url", ""),
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
            taxes.append(
                {
                    "code": tax_code,
                    "name": full_names.get(tax_code, tax.get("name", tax_code)),
                    "rate_pct": tax.get("rate_pct"),
                    "raw_value": tax.get("raw_value", ""),
                    "specific_value": tax.get("specific_value", ""),
                    "assiette": tax.get("assiette", ""),
                    "source": "douane.gov.tn",
                }
            )

        formalities = []
        for reg in pos.get("reglementation_import", []):
            if isinstance(reg, dict):
                formalities.append(reg.get("description", "") or str(reg))
            else:
                formalities.append(str(reg))

        fiscal_advantages = []
        for pref in pos.get("preferences", []):
            country_name = (pref.get("country_name") or "").strip()
            rate = (pref.get("rate") or "").strip()
            if not country_name:
                continue
            fiscal_advantages.append(
                {
                    "description": f"Préférence tarifaire {country_name} : {rate}",
                    "country_code": pref.get("country_code", ""),
                    "rate": rate,
                    "source": "douane.gov.tn",
                }
            )

        # Taxes et redevances à l'export (source officielle douane.gov.tn) —
        # incluses quand elles sont présentes, avec leurs assiettes exactes.
        export_taxes = []
        for tax in pos.get("taxes_export", []) or []:
            export_taxes.append(
                {
                    "code": tax.get("code", ""),
                    "name": tax.get("name", tax.get("code", "")),
                    "rate_pct": tax.get("rate_pct"),
                    "raw_value": tax.get("raw_value", ""),
                    "specific_value": tax.get("specific_value", ""),
                    "assiette": tax.get("assiette", ""),
                    "source": "douane.gov.tn",
                }
            )

        return {
            "code_raw": raw_code,
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": pos.get("chapter", ""),
            "taxes": taxes,
            "export_taxes": export_taxes,
            "fiscal_advantages": fiscal_advantages,
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
            taxes.append(
                {
                    "code": tax_name.split("(")[-1].rstrip(")") if "(" in tax_name else tax_name,
                    "name": tax_name,
                    "rate_pct": self._parse_rate(tax_value),
                    "raw_value": tax_value,
                    "source": "douane.gov.ma/adil",
                }
            )

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
            tax_code = self.EAC_GHA_TAX_CODES.get(
                tax_name,
                tax_name.split("(")[-1].rstrip(")").strip() if "(" in tax_name else tax_name,
            )
            taxes.append(
                {
                    "code": tax_code,
                    "name": tax_name,
                    "rate_pct": rate,
                    "raw_value": f"{rate}%" if rate is not None else "",
                    "base": td.get("base", ""),
                    "source": pos.get("source", ""),
                }
            )

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
        # Real crawl schema (customs.gov.eg, see backend/data/crawled/EGY_tariffs.json):
        # {"hs_code": "...", "designation"/"description"/"name": "...",
        #  "taxes": {"ID"/"DD": {"name", "rate", "raw", "source"}, "VAT"/"TVA": {...}, ...},
        #  "official_instructions": [...]}
        # Le scraper officiel customs.gov.eg publie les codes en anglais
        # ("ID" = Import Duty, "VAT" = Value-Added Tax) alors que le reste
        # de la plateforme utilise le libellé canonique francophone
        # ("DD" = Droit de Douane, "TVA"). On normalise ici pour préserver
        # l'homogénéité inter-pays sans altérer la donnée source.
        code_clean = pos.get("code_clean", "") or pos.get("hs_code", "") or pos.get("code", "")
        code_clean = code_clean.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        _CODE_ALIAS = {"ID": "DD", "VAT": "TVA"}

        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        for td in taxes_detail:
            tax_code = td.get("tax_code", "")
            taxes.append(
                {
                    "code": _CODE_ALIAS.get(tax_code, tax_code),
                    "name": td.get("tax_name", tax_code),
                    "rate_pct": td.get("rate"),
                    "raw_value": f"{td.get('rate')}%" if td.get("rate") is not None else "",
                    "source": "customs.gov.eg",
                }
            )

        if not taxes_detail:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                for code, info in raw_taxes.items():
                    canonical = _CODE_ALIAS.get(code, code)
                    if isinstance(info, dict):
                        rate = info.get("rate")
                        taxes.append(
                            {
                                "code": canonical,
                                "name": info.get("name", canonical),
                                "rate_pct": rate,
                                "raw_value": info.get(
                                    "raw", f"{rate}%" if rate is not None else ""
                                ),
                                "source": info.get("source", "customs.gov.eg"),
                            }
                        )
                    else:
                        # legacy flat {code: rate} shape
                        taxes.append(
                            {
                                "code": canonical,
                                "name": canonical,
                                "rate_pct": info,
                                "raw_value": f"{info}%" if info is not None else "",
                                "source": "customs.gov.eg",
                            }
                        )

        designation = pos.get("designation") or pos.get("description") or pos.get("name", "")
        official_instructions = pos.get("official_instructions", []) or []

        return {
            "code_raw": pos.get("hs_code", pos.get("code", code_clean)),
            "code_clean": code_clean,
            "designation": designation,
            "designation_en": pos.get("designation_en", ""),
            "chapter": pos.get("chapter") or (code_clean[:2] if len(code_clean) >= 2 else ""),
            "taxes": taxes,
            "fiscal_advantages": [],
            "administrative_formalities": [
                {"description": instr, "source": "customs.gov.eg"}
                for instr in official_instructions
            ],
            "source": "customs.gov.eg",
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
            taxes.append(
                {
                    "code": tax_code,
                    "name": td.get("tax_name", tax_code),
                    "rate_pct": td.get("rate"),
                    "raw_value": f"{td.get('rate')}%" if td.get("rate") is not None else "",
                    "source": "customs.erca.gov.et",
                }
            )

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
                        taxes.append(
                            {
                                "code": code,
                                "name": eth_tax_names.get(code, code),
                                "rate_pct": rate,
                                "raw_value": f"{rate}%",
                                "source": "customs.erca.gov.et",
                            }
                        )

        comesa_duty = pos.get("comesa_duty")
        fiscal_advantages = []
        if comesa_duty is not None and comesa_duty >= 0:
            fiscal_advantages.append(
                {
                    "name": "COMESA Preferential Rate",
                    "rate_pct": comesa_duty,
                    "description": f"Reduced duty rate of {comesa_duty}% for COMESA member countries",
                }
            )

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

    def _normalize_wits(self, pos: dict, country_code: str) -> Optional[dict]:
        # Positions WITS/TRAINS (wits_source.py) : {"hs_code", "taxes": {code:
        # {name, rate, raw, source?}}, "advantages": [...], "formalities": [...]}.
        code_clean = (pos.get("hs_code") or "").replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        for tax_code, info in (pos.get("taxes") or {}).items():
            if not isinstance(info, dict):
                continue
            rate = info.get("rate")
            taxes.append(
                {
                    "code": tax_code,
                    "name": info.get("name", tax_code),
                    "rate_pct": rate,
                    "raw_value": info.get("raw", f"{rate}%" if rate is not None else ""),
                    "source": info.get("source", pos.get("source", "")),
                    "source_url": info.get("source_url", ""),
                    "note": info.get("note", ""),
                }
            )

        designation = pos.get("name") or pos.get("description") or ""

        return {
            "code_raw": pos.get("hs_code", code_clean),
            "code_clean": code_clean,
            "designation": designation,
            "chapter": pos.get("chapter") or (code_clean[:2] if len(code_clean) >= 2 else ""),
            "taxes": taxes,
            "fiscal_advantages": pos.get("advantages", []),
            "administrative_formalities": pos.get("formalities", []),
            "source": pos.get("source", ""),
            "source_url": pos.get("source_url", ""),
            "country": country_code,
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
            taxes.append(
                {
                    "code": tax_code,
                    "name": td.get("tax_name", tax_code),
                    "rate_pct": rate,
                    "raw_value": (
                        f"{rate}%" if td.get("rate_type") == "ad_valorem" else f"{rate} FCFA"
                    ),
                    "source": "guce.gouv.ci",
                }
            )

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
                        taxes.append(
                            {
                                "code": code,
                                "name": civ_tax_names.get(code, code),
                                "rate_pct": rate,
                                "raw_value": f"{rate}%",
                                "source": "guce.gouv.ci",
                            }
                        )

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

    def _normalize_sen(self, pos: dict) -> Optional[dict]:
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
            taxes.append(
                {
                    "code": tax_code,
                    "name": td.get("tax_name", tax_code),
                    "rate_pct": rate,
                    "raw_value": f"{rate}%",
                    "source": "douanes.sn + TEC CEDEAO",
                }
            )

        if not taxes:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                sen_tax_names = {
                    "DD": "Droit de Douane (TEC CEDEAO)",
                    "RS": "Redevance Statistique",
                    "PCS": "Prélèvement Communautaire de Solidarité (UEMOA)",
                    "PCC": "Prélèvement Communautaire CEDEAO",
                    "PUA": "Prélèvement Union Africaine",
                    "TVA": "Taxe sur la Valeur Ajoutée",
                }
                for code, rate in raw_taxes.items():
                    if rate is not None:
                        taxes.append(
                            {
                                "code": code,
                                "name": sen_tax_names.get(code, code),
                                "rate_pct": rate,
                                "raw_value": f"{rate}%",
                                "source": "douanes.sn",
                            }
                        )

        return {
            "code_raw": pos.get("code", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": code_clean[:2] if len(code_clean) >= 2 else "",
            "statistical_unit": pos.get("unit", ""),
            "taxes": taxes,
            "fiscal_advantages": [],
            "administrative_formalities": [],
            "source": "douanes.sn + TEC CEDEAO",
            "country": "SEN",
            "notes": [
                "Nomenclature TEC CEDEAO identique pour les 15 États membres",
                "Taxes nationales Sénégal: RS (1%), PCS (1%), PCC (0.5%), PUA (0.2%)",
            ],
        }

    def _normalize_cmr(self, pos: dict) -> Optional[dict]:
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
            if tax_code == "DA" and rate == -1:
                taxes.append(
                    {
                        "code": "DA",
                        "name": td.get("tax_name", "Droit d'Accise"),
                        "rate_pct": None,
                        "raw_value": "variable (5-50%)",
                        "source": "CEMAC Tarif des Douanes",
                        "note": td.get("note", ""),
                    }
                )
            else:
                taxes.append(
                    {
                        "code": tax_code,
                        "name": td.get("tax_name", tax_code),
                        "rate_pct": rate,
                        "raw_value": f"{rate}%",
                        "source": "CEMAC Tarif des Douanes",
                    }
                )

        if not taxes:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                cmr_tax_names = {
                    "DD": "Droit de Douane (TEC CEMAC)",
                    "TCI": "Taxe Communautaire d'Intégration",
                    "TVA": "Taxe sur la Valeur Ajoutée (incl. CAC)",
                    "DA": "Droit d'Accise",
                    "RI": "Redevance Informatique",
                }
                for code, rate in raw_taxes.items():
                    if rate is not None and rate != "variable":
                        taxes.append(
                            {
                                "code": code,
                                "name": cmr_tax_names.get(code, code),
                                "rate_pct": rate,
                                "raw_value": f"{rate}%",
                                "source": "CEMAC Tarif des Douanes",
                            }
                        )

        return {
            "code_raw": pos.get("code", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": code_clean[:2] if len(code_clean) >= 2 else "",
            "statistical_unit": "",
            "taxes": taxes,
            "fiscal_advantages": [],
            "administrative_formalities": [],
            "source": "CEMAC Tarif des Douanes",
            "country": "CMR",
            "notes": [
                "TVA Cameroun: 19.25% (17.5% + 10% CAC)",
                "Le TEC CEMAC s'applique aux 6 États membres",
            ],
        }

    ECOWAS_COUNTRY_NAMES = {
        "BEN": "Bénin",
        "BFA": "Burkina Faso",
        "MLI": "Mali",
        "NER": "Niger",
        "TGO": "Togo",
        "GIN": "Guinée",
    }
    CEMAC_COUNTRY_NAMES = {
        "GAB": "Gabon",
        "COG": "Congo (Brazzaville)",
        "TCD": "Tchad",
        "CAF": "République Centrafricaine",
    }

    def _normalize_ecowas_member(self, pos: dict, country_code: str) -> Optional[dict]:
        code_clean = pos.get("code_clean", "")
        if not code_clean:
            code_raw = pos.get("code", "")
            code_clean = code_raw.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        source = pos.get("source", f"TEC CEDEAO + {country_code}")
        for td in taxes_detail:
            tax_code = td.get("tax_code", "")
            rate = td.get("rate")
            if rate is None:
                continue
            taxes.append(
                {
                    "code": tax_code,
                    "name": td.get("tax_name", tax_code),
                    "rate_pct": rate,
                    "raw_value": f"{rate}%",
                    "base": td.get("base", ""),
                    "source": source,
                }
            )

        if not taxes:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                for code, rate in raw_taxes.items():
                    if rate is not None:
                        taxes.append(
                            {
                                "code": code,
                                "name": code,
                                "rate_pct": rate,
                                "raw_value": f"{rate}%",
                                "base": "",
                                "source": source,
                            }
                        )

        return {
            "code_raw": pos.get("code", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": code_clean[:2] if len(code_clean) >= 2 else "",
            "statistical_unit": pos.get("unit", ""),
            "taxes": taxes,
            "fiscal_advantages": [],
            "administrative_formalities": [],
            "source": source,
            "country": country_code,
            "notes": [
                f"Pays: {self.ECOWAS_COUNTRY_NAMES.get(country_code, country_code)}",
                "Nomenclature TEC CEDEAO identique pour les États membres",
            ],
        }

    def _normalize_cemac_member(self, pos: dict, country_code: str) -> Optional[dict]:
        code_clean = pos.get("code_clean", "")
        if not code_clean:
            code_raw = pos.get("code", "")
            code_clean = code_raw.replace(".", "").replace(" ", "")
        if not code_clean:
            return None

        taxes = []
        taxes_detail = pos.get("taxes_detail", [])
        source = pos.get("source", f"TEC CEMAC + {country_code}")
        for td in taxes_detail:
            tax_code = td.get("tax_code", "")
            rate = td.get("rate")
            if rate is None:
                continue
            if tax_code == "DA" and rate == -1:
                taxes.append(
                    {
                        "code": "DA",
                        "name": td.get("tax_name", "Droit d'Accise"),
                        "rate_pct": None,
                        "raw_value": "variable (5-50%)",
                        "source": source,
                        "note": td.get("note", ""),
                    }
                )
            else:
                taxes.append(
                    {
                        "code": tax_code,
                        "name": td.get("tax_name", tax_code),
                        "rate_pct": rate,
                        "raw_value": f"{rate}%",
                        "base": td.get("base", ""),
                        "source": source,
                    }
                )

        if not taxes:
            raw_taxes = pos.get("taxes", {})
            if isinstance(raw_taxes, dict):
                for code, rate in raw_taxes.items():
                    if rate is not None and rate != -1:
                        taxes.append(
                            {
                                "code": code,
                                "name": code,
                                "rate_pct": rate,
                                "raw_value": f"{rate}%",
                                "base": "",
                                "source": source,
                            }
                        )

        return {
            "code_raw": pos.get("code", code_clean),
            "code_clean": code_clean,
            "designation": pos.get("designation", ""),
            "chapter": code_clean[:2] if len(code_clean) >= 2 else "",
            "statistical_unit": "",
            "taxes": taxes,
            "fiscal_advantages": [],
            "administrative_formalities": [],
            "source": source,
            "country": country_code,
            "notes": [
                f"Pays: {self.CEMAC_COUNTRY_NAMES.get(country_code, country_code)}",
                "Le TEC CEMAC s'applique aux 6 États membres",
            ],
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
        self._ensure_country_loaded(country_code)
        hs_code_clean = hs_code.replace(".", "").replace(" ", "")

        idx = self._code_index.get(country_code, {})
        if not idx:
            return None

        result = idx.get(hs_code_clean)
        if result:
            return result

        # Query longer than indexed codes (e.g. 12-digit input vs 10-digit national line):
        # truncate progressively until a national position prefix matches.
        for length in range(len(hs_code_clean) - 1, 5, -1):
            prefix = hs_code_clean[:length]
            matches = [data for code, data in idx.items() if code.startswith(prefix)]
            if matches:
                return matches[0]

        # Query at or below HS6 granularity (e.g. a 6-digit HS6 code, the most common input):
        # national positions are stored at 8-12 digits, so no exact hit is possible and the
        # downward loop above never runs. Expand via the HS6 index to return a representative
        # authentic national position rather than falling through to estimated data.
        if len(hs_code_clean) <= 6:
            hs6_matches = self._hs6_index.get(country_code, {}).get(hs_code_clean.zfill(6))
            if hs6_matches:
                return hs6_matches[0]

        return None

    def lookup_by_hs6(self, country_code: str, hs6_code: str) -> List[dict]:
        country_code = country_code.upper()
        self._ensure_country_loaded(country_code)
        hs6_clean = hs6_code.replace(".", "").replace(" ", "")[:6].zfill(6)
        return self._hs6_index.get(country_code, {}).get(hs6_clean, [])

    def get_export_taxes(self, country_code: str, hs_code: str) -> Optional[dict]:
        """
        Taxes et redevances à l'export d'une position nationale, telles que
        publiées par la source officielle (ex. douane.gov.tn : RPD/EXPOR).
        Retourne None si aucune donnée export n'est disponible pour ce pays.
        """
        country_code = country_code.upper()
        self._ensure_country_loaded(country_code)
        position = self.lookup(country_code, hs_code)
        if not position:
            return None
        export_taxes = position.get("export_taxes") or []
        if not export_taxes:
            return None
        # Frais de prestataires : marquage explicite (redevances de prestations
        # douanières) directement dans la couche de données.
        from services.tariff_doctrine import provider_fee_flags

        for tax in export_taxes:
            tax.update(provider_fee_flags(tax))
        return {
            "country": country_code,
            "code": position.get("code_clean", ""),
            "designation": position.get("designation", ""),
            "export_taxes": export_taxes,
            "source": position.get("source", ""),
        }

    def search(self, country_code: str, query: str, limit: int = 50) -> List[dict]:
        country_code = country_code.upper()
        self._ensure_country_loaded(country_code)
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
            "countries": list(self._country_files.keys()),
            "countries_loaded_in_memory": list(self._country_data.keys()),
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
