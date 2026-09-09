#!/usr/bin/env python3
"""
Crawler pour le Tarif des Douanes Mauritanie 2020 (PDF Soa Transit).
Source : https://assets.zyrosite.com/YrD48kPMbMc5la0W/tarif-des-douanes-2020-AoP4o0poknSZEDBE.pdf
Statut : source secondaire (transitaire) — à vérifier avec le Code des Douanes officiel.

Structure : code HS 10-digit, désignation, unité, puis taux sur lignes séparées :
  DD (Droit de Douane), RS (Redevance Statistique), TVA,
  PCS (Prélèvement Communautaire de Solidarité), PSC, IMF.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import fitz
import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PDF_URL = "https://assets.zyrosite.com/YrD48kPMbMc5la0W/tarif-des-douanes-2020-AoP4o0poknSZEDBE.pdf"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
TEMP_DIR = Path("/tmp/mrt_tariff")

HEADERS = {"User-Agent": "Mozilla/5.0"}

CODE_PATTERN = re.compile(r"^(\d{4}\.\d{2}\.\d{2}\.\d{2})\s*(.*)$")


def download_pdf() -> Optional[str]:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    filepath = TEMP_DIR / "MRT_tariff_2020.pdf"
    if filepath.exists() and filepath.stat().st_size > 100000:
        return str(filepath)
    logger.info("Downloading Mauritania tariff PDF...")
    resp = httpx.get(PDF_URL, timeout=60, follow_redirects=True, verify=False, headers=HEADERS)
    if resp.status_code == 200 and len(resp.content) > 100000:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        logger.info(f"Downloaded: {len(resp.content) // 1024} KB")
        return str(filepath)
    return None


def parse_rate(val) -> Optional[float]:
    if val is None:
        return None
    s = str(val).strip()
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def extract_positions(filepath: str) -> List[Dict]:
    doc = fitz.open(filepath)
    logger.info(f"PDF: {doc.page_count} pages")

    positions = []

    for page_idx in range(doc.page_count):
        text = doc[page_idx].get_text("text")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Détecter un code HS 10-digit
            m = CODE_PATTERN.match(line)
            if not m:
                i += 1
                continue

            code_raw = m.group(1)
            desc = m.group(2).strip()
            desc = re.sub(r"^--\s*", "", desc)
            code_clean = code_raw.replace(".", "")

            # Les taux suivent sur les lignes suivantes
            # Ordre: U, DD, RS, TVA, PCS, PSC, IMF
            rates = []
            for j in range(i + 1, min(i + 8, len(lines))):
                val = lines[j]
                # Si on rencontre un autre code, stop
                if CODE_PATTERN.match(val):
                    break
                # Unité (u, kg, l, etc.)
                if re.match(r"^[a-zA-Z]{1,3}$", val) and len(rates) == 0:
                    rates.append(("unit", val))
                # Taux numérique
                elif re.match(r"^\d+(?:\.\d+)?$", val):
                    rates.append(("rate", float(val)))
                else:
                    break

            # Extraire les taxes: skip unit, puis DD, RS, TVA, PCS, PSC, IMF
            rate_values = [v for t, v in rates if t == "rate"]
            unit = next((v for t, v in rates if t == "unit"), "")

            tax_order = ["DD", "RS", "TVA", "PCS", "PSC", "IMF"]
            taxes = []
            for ti, tax_code in enumerate(tax_order):
                if ti < len(rate_values):
                    rate = rate_values[ti]
                    canonical = tax_code
                    if tax_code == "TVA":
                        canonical = "TVA"
                    elif tax_code == "RS":
                        canonical = "RS"
                    elif tax_code == "PCS":
                        canonical = "PCS"
                    elif tax_code == "PSC":
                        canonical = "PCC"
                    taxes.append({
                        "code": canonical,
                        "name": tax_code,
                        "name_fr": tax_code,
                        "name_en": "",
                        "rate_pct": rate,
                        "rate_decimal": rate / 100,
                        "raw_value": str(rate),
                        "base": "CIF",
                        "source": "Soa Transit (tarif des douanes 2020)",
                        "legal_ref": None,
                        "is_customs_duty": tax_code == "DD",
                        "is_vat": tax_code == "TVA",
                        "is_excise": False,
                    })

            positions.append({
                "national_code": code_clean,
                "hs6": code_clean[:6],
                "chapter": code_clean[:2],
                "heading": code_clean[:4] + "." + code_clean[4:6],
                "section": "",
                "statistical_unit": unit,
                "check_digit": "",
                "designation": {
                    "fr": desc,
                    "en": "",
                    "ar": "",
                    "full_fr": "",
                    "verbatim": code_raw,
                },
                "taxes": taxes,
                "export_taxes": [],
                "preferential_rates": [],
                "fiscal_advantages": [],
                "formalities": [],
                "restrictions": [],
                "legal_refs": [],
                "reglementation": {"import": [], "export": []},
                "quotas": {"qcs": None, "qci": None},
                "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
                "source_gaps": [],
                "lf_provisions": None,
                "data_status": "secondary_to_verify",
                "source_quality": "secondary_source_to_verify",
                "source": "Soa Transit (tarif des douanes 2020) — source secondaire, à vérifier",
                "source_url": PDF_URL,
                "raw_data": {"code": code_raw, "desc": desc, "rates": rate_values, "unit": unit},
            })
            i += 1

        if (page_idx + 1) % 50 == 0:
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
        "country": "MRT",
        "country_name": "Mauritanie",
        "source": "Soa Transit (tarif des douanes 2020) — source secondaire",
        "source_url": PDF_URL,
        "source_quality": "secondary_source_to_verify",
        "source_type": "secondary",
        "extracted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "edition": "Tarif des Douanes 2020 (09/01/2020)",
        "application_period": "2020-01-01 to next amendment",
        "validation_status": "to_verify",
        "warning": "Source secondaire (transitaire). Présenté comme indicatif. Modifications 2021-2026 non confirmées. Statut 'à vérifier' jusqu'à corroboration avec le Code des Douanes officiel.",
        "stats": {
            "total_positions": len(positions),
            "unique_tax_codes": sorted(all_tax_codes),
            "chapters_covered": len(set(p["chapter"] for p in positions)),
            "tax_columns": ["DD", "RS", "TVA", "PCS", "PSC", "IMF"],
        },
        "sub_positions": positions,
    }

    output = DATA_DIR / "MRT_tariffs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(positions)} positions to {output}")


def main():
    logger.info("=== Mauritania Tariff Scraper (Soa Transit, source secondaire) ===")
    filepath = download_pdf()
    if not filepath:
        return

    positions = extract_positions(filepath)
    logger.info(f"Extracted {len(positions)} positions")

    if positions:
        save(positions)

        from collections import Counter
        dd_dist = Counter()
        for p in positions:
            for t in p["taxes"]:
                if t["code"] == "DD":
                    dd_dist[t["rate_pct"]] += 1
        print(f"\nDD distribution: {dict(sorted(dd_dist.items(), key=lambda x: -x[1]))}")
        print(f"Chapters: {len(set(p['chapter'] for p in positions))}")
        print(f"Sample: {positions[0]['national_code']} {positions[0]['designation']['fr'][:40]}")
        print(f"\nWARNING: Source secondaire — statut 'à vérifier'")


if __name__ == "__main__":
    main()
