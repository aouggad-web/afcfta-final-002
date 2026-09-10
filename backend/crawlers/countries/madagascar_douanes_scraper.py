#!/usr/bin/env python3
"""
Crawler pour le Tarif des Douanes Madagascar (PDF officiel).
Source : https://www.douanes.gov.mg/tarifs-des-douanes/
Format : PDF 292 pages, structure tabulaire avec colonnes:
  TARIF N° | DESIGNATION | UQN | DD | TVA | DD APEi

Le PDF met toutes les sous-positions d'un chapitre dans une seule
cellule (séparées par \n). Le parser extrait chaque ligne individuellement.
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

PDF_URL = "https://www.douanes.gov.mg/srcs/uploads/2026/07/TARIF-DES-DOUANES-2026-MAJ-LFR.pdf"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
TEMP_DIR = Path("/tmp/mdg_tariff")

HEADERS = {"User-Agent": "Mozilla/5.0"}

CODE_PATTERN = re.compile(r"^\d{4}\.\d{2}(?:\s?\d{2})?$")


def download_pdf() -> Optional[str]:
    """Télécharge le PDF du tarif Madagascar."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    filepath = TEMP_DIR / "MDG_tariff_2026.pdf"

    if filepath.exists() and filepath.stat().st_size > 100000:
        logger.info(f"Using cached PDF: {filepath}")
        return str(filepath)

    logger.info(f"Downloading Madagascar tariff PDF...")
    resp = httpx.get(PDF_URL, timeout=120, follow_redirects=True, headers=HEADERS)
    if resp.status_code == 200 and len(resp.content) > 100000:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        logger.info(f"Downloaded: {len(resp.content) // 1024} KB")
        return str(filepath)
    logger.error(f"Download failed: {resp.status_code}")
    return None


def parse_rate(value: str) -> Optional[float]:
    """Parse un taux ('20' → 20.0, 'ex' → None, 'free' → 0.0)."""
    v = value.strip().lower()
    if v in ("ex", "", "—", "-"):
        return None
    if v in ("free", "0"):
        return 0.0
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None


def extract_positions(filepath: str) -> List[Dict]:
    """Extrait toutes les positions tarifaires du PDF Madagascar."""
    doc = fitz.open(filepath)
    logger.info(f"PDF: {doc.page_count} pages")

    positions = []
    current_chapter = ""
    current_heading_desc = ""

    for page_idx in range(6, doc.page_count):  # Skip intro pages
        page = doc[page_idx]
        tables = list(page.find_tables())

        for tab in tables:
            rows = tab.extract()
            if not rows:
                continue

            # Trouver l'en-tête (TARIF N° | DESIGNATION | UQN | DD | TVA | DD APEi)
            header_row = None
            for r in rows:
                cells = [str(c).strip() if c else "" for c in r]
                if "TARIF" in cells[0].upper() or "DESIGNATION" in " ".join(cells).upper():
                    header_row = r
                    break

            if not header_row:
                continue

            # Les données sont dans la rangée suivante : chaque cellule
            # contient toutes les valeurs séparées par \n
            data_row = None
            for r in rows:
                if r is header_row:
                    continue
                cells = [str(c) if c else "" for c in r]
                if len(cells) >= 6 and "\n" in cells[0]:
                    data_row = cells
                    break

            if not data_row:
                # Essayer les autres rangées
                for r in rows[1:]:
                    cells = [str(c) if c else "" for c in r]
                    if len(cells) >= 6 and any("\n" in c for c in cells):
                        data_row = cells
                        break

            if not data_row:
                continue

            # Séparer chaque cellule par \n
            codes = data_row[0].split("\n") if data_row[0] else []
            designations = data_row[1].split("\n") if len(data_row) > 1 and data_row[1] else []
            units = data_row[2].split("\n") if len(data_row) > 2 and data_row[2] else []
            dd_values = data_row[3].split("\n") if len(data_row) > 3 and data_row[3] else []
            tva_values = data_row[4].split("\n") if len(data_row) > 4 and data_row[4] else []
            apei_values = data_row[5].split("\n") if len(data_row) > 5 and data_row[5] else []

            # Nettoyer les listes
            codes = [c.strip() for c in codes if c.strip()]
            designations = [d.strip() for d in designations if d.strip()]
            units = [u.strip() for u in units if u.strip()]
            dd_values = [d.strip() for d in dd_values if d.strip()]
            tva_values = [t.strip() for t in tva_values if t.strip()]
            apei_values = [a.strip() for a in apei_values if a.strip()]

            # Filtrer les codes (ignorer les en-têtes de chapitre comme "01.01")
            tariff_codes = []
            for c in codes:
                c_clean = c.replace(" ", "")
                if re.match(r"^\d{4}\.\d{2}\d{2}$", c_clean):
                    # Format: 0101.21 00 → 8-digit
                    tariff_codes.append(c_clean.replace(".", ""))
                elif re.match(r"^\d{4}\.\d{2}$", c_clean):
                    # 6-digit heading, skip
                    continue
                elif re.match(r"^\d{2}\.\d{2}$", c_clean):
                    # Chapter heading, skip
                    continue

            if not tariff_codes:
                continue

            # Le nombre de codes tarifaires devrait correspondre au nombre
            # de désignations, unités, DD, TVA, APEi
            n = len(tariff_codes)

            for i in range(n):
                code = tariff_codes[i]
                chapter = code[:2]
                hs6 = code[:6]

                # Désignation
                desc = designations[i] if i < len(designations) else ""
                desc = re.sub(r"^-+\s*", "", desc).strip()
                desc = re.sub(r"-+$", "", desc).strip()

                # Unité
                unit = units[i] if i < len(units) else ""

                # DD
                dd_raw = dd_values[i] if i < len(dd_values) else ""
                dd_rate = parse_rate(dd_raw)

                # TVA
                tva_raw = tva_values[i] if i < len(tva_values) else ""
                tva_rate = parse_rate(tva_raw)

                # APEi (préférence)
                apei_raw = apei_values[i] if i < len(apei_values) else ""
                apei_rate = parse_rate(apei_raw)

                # Construire les taxes
                taxes = []
                if dd_rate is not None:
                    taxes.append({
                        "code": "DD",
                        "name": "Droit de Douane",
                        "rate_pct": dd_rate,
                        "raw_value": dd_raw,
                        "base": "CIF",
                        "source": "douanes.gov.mg",
                    })
                if tva_rate is not None:
                    taxes.append({
                        "code": "TVA",
                        "name": "Taxe sur la Valeur Ajoutée",
                        "rate_pct": tva_rate,
                        "raw_value": tva_raw,
                        "base": "CIF+DD",
                        "source": "douanes.gov.mg",
                    })

                # Préférence APEi
                preferential_rates = []
                if apei_rate is not None:
                    preferential_rates.append({
                        "regime": "APEi",
                        "rate_pct": apei_rate,
                        "raw_value": apei_raw,
                        "source": "douanes.gov.mg",
                    })

                positions.append({
                    "national_code": code,
                    "hs6": hs6,
                    "chapter": chapter,
                    "heading": code[:4] + "." + code[4:6],
                    "section": "",
                    "statistical_unit": unit,
                    "check_digit": "",
                    "designation": {
                        "fr": desc,
                        "en": "",
                        "ar": "",
                        "full_fr": "",
                        "verbatim": "",
                    },
                    "taxes": taxes,
                    "export_taxes": [],
                    "preferential_rates": preferential_rates,
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
                    "source": "douanes.gov.mg (Tarif des Douanes 2026)",
                    "source_url": PDF_URL,
                    "raw_data": {
                        "code": code,
                        "designation": desc,
                        "unit": unit,
                        "dd_raw": dd_raw,
                        "tva_raw": tva_raw,
                        "apei_raw": apei_raw,
                    },
                })

        if (page_idx + 1) % 50 == 0:
            logger.info(f"Page {page_idx+1}/{doc.page_count}: {len(positions)} positions")

    doc.close()
    return positions


def save(positions: List[Dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Tax codes
    all_tax_codes = set()
    for p in positions:
        for t in p.get("taxes", []):
            all_tax_codes.add(t.get("code", ""))

    result = {
        "country": "MDG",
        "country_name": "Madagascar",
        "source": "douanes.gov.mg (Tarif des Douanes 2026, après LFR 2026)",
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

    output = DATA_DIR / "MDG_tariffs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(positions)} positions to {output}")


def main():
    logger.info("=== Madagascar Tariff Scraper ===")
    filepath = download_pdf()
    if not filepath:
        return

    positions = extract_positions(filepath)
    logger.info(f"Extracted {len(positions)} positions")

    if positions:
        save(positions)

        # Stats
        from collections import Counter
        dd_dist = Counter()
        for p in positions:
            for t in p["taxes"]:
                if t["code"] == "DD":
                    dd_dist[t["rate_pct"]] += 1
        print(f"\nDD distribution: {dict(sorted(dd_dist.items(), key=lambda x: -x[1]))}")
        print(f"Chapters: {len(set(p['chapter'] for p in positions))}")
        print(f"Sample: {positions[0]['national_code']} {positions[0]['designation']['fr'][:40]}")


if __name__ == "__main__":
    main()
