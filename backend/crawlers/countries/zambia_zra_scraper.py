#!/usr/bin/env python3
"""
Crawler pour le Customs Tariff Book Zambie (PDF officiel ZRA).
Source : https://www.zra.org.zm/wp-content/uploads/2026/08/Customs-Tariff-Book.pdf

Structure du PDF :
  Code 8-digit → Désignation → Unit (No) → DD rate → Excise (E/-) → VAT

Le PDF ZRA utilise une structure ligne par ligne où chaque position
8-digit est suivie de sa désignation et de ses taux.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz
import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PDF_URL = "https://www.zra.org.zm/wp-content/uploads/2026/08/Customs-Tariff-Book.pdf"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
TEMP_DIR = Path("/tmp/zmb_tariff")

HEADERS = {"User-Agent": "Mozilla/5.0"}

CODE_PATTERN = re.compile(r"^(\d{4}\.\d{2}\.\d{2})$")
RATE_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)\s*%$")


def download_pdf() -> Optional[str]:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    filepath = TEMP_DIR / "ZMB_tariff_book.pdf"

    if filepath.exists() and filepath.stat().st_size > 100000:
        logger.info(f"Using cached PDF: {filepath}")
        return str(filepath)

    logger.info("Downloading Zambia tariff PDF...")
    resp = httpx.get(PDF_URL, timeout=120, follow_redirects=True, verify=False, headers=HEADERS)
    if resp.status_code == 200 and len(resp.content) > 100000:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        logger.info(f"Downloaded: {len(resp.content) // 1024} KB")
        return str(filepath)
    logger.error(f"Download failed: {resp.status_code}")
    return None


def extract_positions(filepath: str) -> List[Dict]:
    doc = fitz.open(filepath)
    logger.info(f"PDF: {doc.page_count} pages")

    positions = []
    current_desc = ""

    for page_idx in range(25, doc.page_count):  # Skip intro pages
        page = doc[page_idx]
        text = page.get_text("text")
        lines = [l.strip() for l in text.split("\n")]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Détecter un code 8-digit
            m = CODE_PATTERN.match(line)
            if m:
                code_raw = m.group(1)
                code_clean = code_raw.replace(".", "")
                hs6 = code_clean[:6]
                chapter = code_clean[:2]

                # Désignation = ligne suivante
                desc = ""
                if i + 1 < len(lines):
                    desc = lines[i + 1]
                    desc = re.sub(r"^[-]+\s*", "", desc).strip()

                # Chercher le taux DD dans les lignes suivantes (No, rate%, ...)
                dd_rate = None
                vat_rate = None
                excise_rate = None

                for j in range(i + 2, min(i + 10, len(lines))):
                    val = lines[j]
                    rate_m = RATE_PATTERN.match(val)
                    if rate_m:
                        rate = float(rate_m.group(1))
                        if dd_rate is None:
                            dd_rate = rate
                        elif excise_rate is None:
                            excise_rate = rate
                        elif vat_rate is None:
                            vat_rate = rate

                # Construire les taxes
                taxes = []
                if dd_rate is not None:
                    taxes.append({
                        "code": "DD",
                        "name": "Customs Duty",
                        "name_fr": "Droit de Douane",
                        "name_en": "Customs Duty",
                        "rate_pct": dd_rate,
                        "rate_decimal": dd_rate / 100,
                        "raw_value": f"{dd_rate}%",
                        "base": "CIF",
                        "source": "zra.org.zm",
                    })
                if excise_rate is not None and excise_rate > 0:
                    taxes.append({
                        "code": "DA",
                        "name": "Excise Duty",
                        "name_fr": "Droit d'Accise",
                        "name_en": "Excise Duty",
                        "rate_pct": excise_rate,
                        "rate_decimal": excise_rate / 100,
                        "raw_value": f"{excise_rate}%",
                        "base": "CIF+DD",
                        "source": "zra.org.zm",
                    })

                # TVA Zambie = 16% (standard, non publié par ligne dans le PDF)
                # On l'ajoute depuis le fallback
                taxes.append({
                    "code": "TVA",
                    "name": "Value Added Tax",
                    "name_fr": "TVA",
                    "name_en": "VAT",
                    "rate_pct": 16.0,
                    "rate_decimal": 0.16,
                    "raw_value": "16%",
                    "base": "CIF+DD+Excise",
                    "source": "zra.org.zm (standard rate)",
                })

                positions.append({
                    "national_code": code_clean,
                    "hs6": hs6,
                    "chapter": chapter,
                    "heading": code_clean[:4] + "." + code_clean[4:6],
                    "section": "",
                    "statistical_unit": "",
                    "check_digit": "",
                    "designation": {
                        "fr": "",
                        "en": desc,
                        "ar": "",
                        "full_fr": "",
                        "verbatim": "",
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
                    "data_status": "crawled_authentic",
                    "source_quality": "crawled_authentic",
                    "source": "zra.org.zm (Customs Tariff Book)",
                    "source_url": PDF_URL,
                    "raw_data": {"code": code_raw, "designation": desc, "dd": dd_rate, "excise": excise_rate},
                })
                i += 2
                continue

            i += 1

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
        "country": "ZMB",
        "country_name": "Zambia",
        "source": "zra.org.zm (Customs Tariff Book)",
        "source_url": PDF_URL,
        "source_quality": "crawled_authentic",
        "extracted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "stats": {
            "total_positions": len(positions),
            "unique_tax_codes": sorted(all_tax_codes),
            "chapters_covered": len(set(p["chapter"] for p in positions)),
        },
        "sub_positions": positions,
    }

    output = DATA_DIR / "ZMB_tariffs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(positions)} positions to {output}")


def main():
    logger.info("=== Zambia Tariff Scraper ===")
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
        print(f"Sample: {positions[0]['national_code']} {positions[0]['designation']['en'][:40]}")


if __name__ == "__main__":
    main()
