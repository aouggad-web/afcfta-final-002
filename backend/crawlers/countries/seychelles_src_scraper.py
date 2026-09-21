#!/usr/bin/env python3
"""
Crawler pour le Schedule 1 Excise Tax Rates Seychelles (PDF officiel SRC).
Source : https://src.gov.sc/wp-content/uploads/2022/11/SCHEDULE-1-Excise-Tax-Rates.pdf

Le PDF contient les taux d'accise par code HS 8-digit avec :
  - Tariff Item (description)
  - HS Code
  - Description of Excisable Goods
  - Taxable Base
  - Excise Tax Rate
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

# Vérification TLS active (défaut httpx). Elle portait `verify=False` :
# le collecteur acceptait n'importe quel certificat, et un tiers sur le
# chemin pouvait donc lui dicter les taux qu'il liquide. Si la chaîne d'un
# portail se révèle incomplète en production, la réponse est de fournir
# l'intermédiaire manquant — jamais de redésactiver la vérification.

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PDF_URL = "https://src.gov.sc/wp-content/uploads/2022/11/SCHEDULE-1-Excise-Tax-Rates.pdf"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
TEMP_DIR = Path("/tmp/syc_tariff")

HEADERS = {"User-Agent": "Mozilla/5.0"}


def download_pdf() -> Optional[str]:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    filepath = TEMP_DIR / "SYC_excise.pdf"
    if filepath.exists() and filepath.stat().st_size > 100000:
        return str(filepath)
    logger.info("Downloading Seychelles Excise PDF...")
    resp = httpx.get(PDF_URL, timeout=60, follow_redirects=True, headers=HEADERS)
    if resp.status_code == 200 and len(resp.content) > 100000:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        logger.info(f"Downloaded: {len(resp.content) // 1024} KB")
        return str(filepath)
    return None


def extract_positions(filepath: str) -> List[Dict]:
    doc = fitz.open(filepath)
    logger.info(f"PDF: {doc.page_count} pages")

    positions = []

    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        text = page.get_text("text")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Chercher un code HS 8-digit (format: 2105.0010 ou 2203.0083)
            m = re.match(r"^(\d{4}\.\d{4})$", line)
            if not m:
                # Parfois le code est sur la même ligne que la description
                m2 = re.match(r"^(\d{4}\.\d{4})\s+(.+)", line)
                if m2:
                    code_raw = m2.group(1)
                    desc = m2.group(2)
                else:
                    i += 1
                    continue
            else:
                code_raw = m.group(1)
                desc = ""
                # Description = ligne suivante
                if i + 1 < len(lines):
                    desc = lines[i + 1]
                    i += 1

            code_clean = code_raw.replace(".", "")
            if len(code_clean) < 8:
                i += 1
                continue

            # Chercher le taux d'accise dans les lignes suivantes
            excise_rate = None
            excise_raw = ""
            taxable_base = ""

            for j in range(i + 1, min(i + 5, len(lines))):
                val = lines[j]
                # Taux spécifique (SCR/litre, /bot, etc.)
                if (
                    re.search(r"(?:SCR|SR|Rs)\.?\s*\d+", val, re.IGNORECASE)
                    or re.search(r"\d+\.?\d*\s*%", val)
                    or re.search(r"\d+\.?\d*/(?:bot|l|lt|kg|unit)", val, re.IGNORECASE)
                ):
                    excise_raw = val
                    # Parser
                    pct_m = re.search(r"(\d+\.?\d*)\s*%", val)
                    if pct_m:
                        excise_rate = float(pct_m.group(1))
                    break
                # Taxable base (1/bot, kg, etc.)
                if re.match(r"^1/(?:bot|l|lt|kg|unit)", val, re.IGNORECASE):
                    taxable_base = val
                    # Le taux est probablement sur la ligne suivante
                    if j + 1 < len(lines):
                        excise_raw = lines[j + 1]
                        pct_m = re.search(r"(\d+\.?\d*)\s*%", excise_raw)
                        if pct_m:
                            excise_rate = float(pct_m.group(1))
                        break

            if excise_raw or excise_rate is not None:
                taxes = [
                    {
                        "code": "DA",
                        "name": "Excise Tax",
                        "name_fr": "Droit d'Accise",
                        "name_en": "Excise Tax",
                        "rate_pct": excise_rate,
                        "rate_decimal": excise_rate / 100 if excise_rate else None,
                        "raw_value": excise_raw,
                        "specific_value": excise_raw if excise_rate is None else None,
                        "base": taxable_base or "CIF",
                        "source": "src.gov.sc (Schedule 1 Excise Tax Rates)",
                        "legal_ref": "Customs Management Act 2011, Schedule 1",
                        "is_excise": True,
                        "is_customs_duty": False,
                        "is_vat": False,
                    }
                ]

                positions.append(
                    {
                        "national_code": code_clean,
                        "hs6": code_clean[:6],
                        "chapter": code_clean[:2],
                        "heading": code_clean[:4] + "." + code_clean[4:6],
                        "section": "",
                        "statistical_unit": "",
                        "check_digit": "",
                        "designation": {
                            "fr": "",
                            "en": desc,
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
                        "zlecaf_schedule": {
                            "applied": False,
                            "rate_pct": None,
                            "instruction": None,
                        },
                        "source_gaps": [],
                        "lf_provisions": None,
                        "data_status": "crawled_authentic",
                        "source_quality": "crawled_authentic",
                        "source": "src.gov.sc (Schedule 1 Excise Tax Rates)",
                        "source_url": PDF_URL,
                        "raw_data": {
                            "code": code_raw,
                            "desc": desc,
                            "excise_raw": excise_raw,
                            "taxable_base": taxable_base,
                        },
                    }
                )

            i += 1

    doc.close()
    return positions


def save(positions: List[Dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "country": "SYC",
        "country_name": "Seychelles",
        "source": "src.gov.sc (Schedule 1 Excise Tax Rates)",
        "source_url": PDF_URL,
        "source_quality": "crawled_authentic",
        "extracted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "stats": {
            "total_positions": len(positions),
            "chapters_covered": len(set(p["chapter"] for p in positions)),
        },
        "sub_positions": positions,
    }

    output = DATA_DIR / "SYC_tariffs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(positions)} positions to {output}")


def main():
    logger.info("=== Seychelles Excise Tax Scraper ===")
    filepath = download_pdf()
    if not filepath:
        return

    positions = extract_positions(filepath)
    logger.info(f"Extracted {len(positions)} positions")

    if positions:
        save(positions)
        print(f"\nChapters: {len(set(p['chapter'] for p in positions))}")
        print(f"Sample: {positions[0]['national_code']} {positions[0]['designation']['en'][:40]}")


if __name__ == "__main__":
    main()
