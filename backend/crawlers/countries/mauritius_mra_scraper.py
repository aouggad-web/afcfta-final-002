#!/usr/bin/env python3
"""
Crawler pour le Customs Tariff Schedule Maurice (PDF officiel MRA).
Source : https://www.mra.mu/download/TariffInf130826.pdf
807 pages, HS 2022, 20 colonnes : General, Excise, VAT, COMESA I/II,
SADC, IOC, INDIA, PAKISTAN, EC, TÜRKIYE, UK, CHINA, AfCFTA, UAE, Agency.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import fitz

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PDF_PATH = "/tmp/mus_tariff_full.pdf"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"


def parse_rate(val) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s == "-":
        return None
    if s.lower() in ("free", "exempt", "0"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def extract_positions() -> List[Dict]:
    doc = fitz.open(PDF_PATH)
    logger.info(f"PDF: {doc.page_count} pages")

    positions = []
    # Colonnes: Heading(0) | HS Code(1) | Description(2) | Unit(3) | General(4) |
    # Excise(5) | VAT(6) | COMESA I(7) | COMESA II(8) | SADC(9) | IOC(10) |
    # INDIA(11) | PAKISTAN(12) | EC(13) | TÜRKIYE(14) | UK(15) | CHINA(16) |
    # AfCFTA(17) | UAE(18) | Agency(19)

    COL_HS = 1
    COL_DESC = 2
    COL_UNIT = 3
    COL_GENERAL = 4
    COL_EXCISE = 5
    COL_VAT = 6
    COL_AFCFTA = 17

    for page_idx in range(22, min(doc.page_count, 700)):  # Limiter aux pages valides
        try:
            page = doc[page_idx]
            tables = list(page.find_tables())
        except Exception:
            continue

        for tab in tables:
            try:
                rows = tab.extract()
            except Exception:
                continue

            for row in rows:
                if not row or len(row) <= COL_AFCFTA:
                    continue

                hs_code = str(row[COL_HS] or "").strip() if row[COL_HS] else ""
                if not hs_code or not re.match(r"^\d{4}\.\d{2}\.\d{2}$", hs_code):
                    continue

                code_clean = hs_code.replace(".", "")
                desc = str(row[COL_DESC] or "").strip() if row[COL_DESC] else ""
                desc = re.sub(r"\s+", " ", desc)
                unit = str(row[COL_UNIT] or "").strip() if row[COL_UNIT] else ""

                dd_rate = parse_rate(row[COL_GENERAL] if COL_GENERAL < len(row) else None)
                excise_rate = parse_rate(row[COL_EXCISE] if COL_EXCISE < len(row) else None)
                vat_rate = parse_rate(row[COL_VAT] if COL_VAT < len(row) else None)
                afcfta_rate = parse_rate(row[COL_AFCFTA] if COL_AFCFTA < len(row) else None)

                # Préférences
                preferential_rates = []
                pref_cols = [
                    (7, "COMESA Group I"), (8, "COMESA Group II"),
                    (9, "SADC"), (10, "IOC"), (11, "INDIA"),
                    (12, "PAKISTAN"), (13, "EC"), (14, "TÜRKIYE"),
                    (15, "UK"), (16, "CHINA"), (17, "AfCFTA"), (18, "UAE"),
                ]
                for col_idx, regime in pref_cols:
                    if col_idx < len(row):
                        rate = parse_rate(row[col_idx])
                        if rate is not None:
                            preferential_rates.append({
                                "regime": regime,
                                "rate_pct": rate,
                                "source": "mra.mu (Customs Tariff Schedules)",
                            })

                # Taxes
                taxes = []
                if dd_rate is not None:
                    taxes.append({
                        "code": "DD", "name": "Customs Duty",
                        "name_fr": "Droit de Douane", "name_en": "Customs Duty",
                        "name_ar": "", "rate_pct": dd_rate,
                        "rate_decimal": dd_rate / 100, "raw_value": str(row[COL_GENERAL]),
                        "base": "CIF", "source": "mra.mu",
                        "is_customs_duty": True, "is_vat": False, "is_excise": False,
                    })
                if excise_rate is not None:
                    taxes.append({
                        "code": "DA", "name": "Excise Duty",
                        "name_fr": "Droit d'Accise", "name_en": "Excise Duty",
                        "name_ar": "", "rate_pct": excise_rate,
                        "rate_decimal": excise_rate / 100, "raw_value": str(row[COL_EXCISE]),
                        "base": "CIF+DD", "source": "mra.mu",
                        "is_excise": True, "is_customs_duty": False, "is_vat": False,
                    })
                if vat_rate is not None:
                    taxes.append({
                        "code": "TVA", "name": "Value Added Tax",
                        "name_fr": "TVA", "name_en": "VAT",
                        "name_ar": "", "rate_pct": vat_rate,
                        "rate_decimal": vat_rate / 100, "raw_value": str(row[COL_VAT]),
                        "base": "CIF+DD+Excise", "source": "mra.mu",
                        "is_vat": True, "is_customs_duty": False, "is_excise": False,
                    })

                positions.append({
                    "national_code": code_clean,
                    "hs6": code_clean[:6],
                    "chapter": code_clean[:2],
                    "heading": code_clean[:4] + "." + code_clean[4:6],
                    "section": "", "statistical_unit": unit, "check_digit": "",
                    "designation": {"fr": "", "en": desc, "ar": "", "full_fr": "", "verbatim": hs_code},
                    "taxes": taxes, "export_taxes": [],
                    "preferential_rates": preferential_rates,
                    "fiscal_advantages": [], "formalities": [], "restrictions": [],
                    "legal_refs": [], "reglementation": {"import": [], "export": []},
                    "quotas": {"qcs": None, "qci": None},
                    "zlecaf_schedule": {"applied": afcfta_rate is not None, "rate_pct": afcfta_rate, "instruction": None},
                    "source_gaps": [], "lf_provisions": None,
                    "data_status": "crawled_authentic", "source_quality": "crawled_authentic",
                    "source": "mra.mu (Customs Tariff Schedules HS 2022, 13 August 2026)",
                    "source_url": "https://www.mra.mu/download/TariffInf130826.pdf",
                    "raw_data": {"hs_code": hs_code, "desc": desc, "dd": str(row[COL_GENERAL]), "excise": str(row[COL_EXCISE]), "vat": str(row[COL_VAT]), "afcfta": str(row[COL_AFCFTA]) if COL_AFCFTA < len(row) else ""},
                })

        if (page_idx + 1) % 100 == 0:
            logger.info(f"Page {page_idx+1}/{doc.page_count}: {len(positions)} positions")

    doc.close()
    return positions


def save(positions: List[Dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_tax_codes = set()
    for p in positions:
        for t in p.get("taxes", []):
            all_tax_codes.add(t.get("code", ""))

    result = {
        "country": "MUS",
        "country_name": "Mauritius",
        "source": "mra.mu (Customs Tariff Schedules HS 2022, 13 August 2026)",
        "source_url": "https://www.mra.mu/download/TariffInf130826.pdf",
        "source_quality": "crawled_authentic",
        "extracted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "stats": {
            "total_positions": len(positions),
            "unique_tax_codes": sorted(all_tax_codes),
            "chapters_covered": len(set(p["chapter"] for p in positions)),
            "preferential_regimes": ["COMESA I", "COMESA II", "SADC", "IOC", "INDIA", "PAKISTAN", "EC", "TÜRKIYE", "UK", "CHINA", "AfCFTA", "UAE"],
        },
        "sub_positions": positions,
    }

    output = DATA_DIR / "MUS_tariffs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(positions)} positions to {output}")


def main():
    logger.info("=== Mauritius Tariff Scraper ===")
    positions = extract_positions()
    logger.info(f"Extracted {len(positions)} positions")

    if positions:
        save(positions)

        from collections import Counter
        dd_dist = Counter()
        afcfta_count = 0
        for p in positions:
            for t in p["taxes"]:
                if t["code"] == "DD":
                    dd_dist[t["rate_pct"]] += 1
            if p.get("zlecaf_schedule", {}).get("applied"):
                afcfta_count += 1

        print(f"\nDD distribution: {dict(sorted(dd_dist.items(), key=lambda x: -x[1]))}")
        print(f"Positions with AfCFTA rate: {afcfta_count}")
        print(f"Chapters: {len(set(p['chapter'] for p in positions))}")
        print(f"Sample: {positions[0]['national_code']} {positions[0]['designation']['en'][:40]}")


if __name__ == "__main__":
    main()
