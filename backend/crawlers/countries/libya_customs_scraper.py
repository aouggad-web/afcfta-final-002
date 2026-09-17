#!/usr/bin/env python3
"""
Crawler pour le tarif douanier Libye (XLSX officiel customs.gov.ly).
Source : https://customs.gov.ly/wp-content/uploads/2023/12/التعريفة-الجمركية-.2022-.xlsx
Format : XLSX avec colonnes en arabe :
  - رقم البند (numéro de position)
  - رمز النظام المنسق (code SH)
  - بيان المنتجات (désignation produit)
  - فئة الضريبة (taux DD)
  - التعريفة التفضيلية لدول جامعة الدول العربية (préférence Ligue Arabe)
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import openpyxl

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

XLSX_URL = "https://customs.gov.ly/wp-content/uploads/2023/12/التعريفة-الجمركية-.2022-.xlsx"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"
TEMP_DIR = Path("/tmp/lby_tariff")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "ar,en-US;q=0.9",
}


def download_xlsx() -> Optional[str]:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    filepath = TEMP_DIR / "LBY_tariff.xlsx"
    if filepath.exists() and filepath.stat().st_size > 100000:
        logger.info(f"Using cached XLSX: {filepath}")
        return str(filepath)
    logger.info("Downloading Libya tariff XLSX...")
    resp = httpx.get(XLSX_URL, timeout=120, follow_redirects=True, verify=False, headers=HEADERS)
    if resp.status_code == 200 and len(resp.content) > 100000:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        logger.info(f"Downloaded: {len(resp.content) // 1024} KB")
        return str(filepath)
    logger.error(f"Download failed: {resp.status_code}")
    return None


#: « ممنوع استيراده » — importation interdite. Ce n'est PAS un taux absent :
#: la marchandise ne peut pas entrer. La confondre avec une donnée manquante
#: ferait lire « droit indisponible » là où la réponse est « interdit », et
#: la traiter comme 0 % ferait liquider une importation prohibée.
MENTION_INTERDIT = "ممنوع استيراده"

#: « معفاة » — exonéré. Un zéro réellement publié par le tarif.
MENTION_EXONERE = "معفاة"


def parse_rate(val) -> Optional[float]:
    """Rend un taux en POURCENTS, ou ``None`` si la cellule n'en porte pas.

    Le tarif libyen mélange deux écritures dans la même colonne, relevé sur
    le XLSX officiel 2022 : une fraction décimale (``0.05``, 4 379 lignes) et
    un pourcentage littéral (``5%``, 356 lignes) — les deux valant 5 %. Une
    première version rendait ``float(s)`` pour les deux, soit ``0.05`` pris
    pour 0,05 % (cent fois trop bas) et une exception sur ``5%`` (taux
    perdu). Sa docstring annonçait pourtant la bonne conversion.

    La règle de lecture est donnée par les valeurs elles-mêmes : le tarif ne
    porte aucun droit inférieur à 1 %, et ``0.05``/``0.1``/``0.3`` se lisent
    5 %, 10 % et 30 % — ce que confirme la coexistence de ``5%``, ``10%`` et
    ``30%`` pour les mêmes marchandises. Une valeur ``≤ 1`` sans signe pour
    cent est donc une fraction ; au-delà, un pourcentage déjà écrit comme tel.

    ``None`` est rendu pour une cellule vide, pour une mention d'interdiction
    (traitée séparément par :func:`lire_cellule_droit`) et pour tout texte non
    reconnu — jamais un zéro de substitution.
    """
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    if MENTION_EXONERE in s or "exempt" in s.lower() or "free" in s.lower():
        return 0.0
    if MENTION_INTERDIT in s:
        return None
    pourcent = s.endswith("%")
    nombre = s.rstrip("%").strip()
    try:
        valeur = float(nombre)
    except ValueError:
        return None
    if pourcent:
        return valeur
    # Fraction décimale (0.05 → 5 %). Une valeur > 1 sans signe pour cent est
    # déjà un pourcentage : on la rend telle quelle plutôt que de la
    # multiplier par cent, ce qui produirait des droits de plusieurs milliers.
    return valeur * 100 if valeur <= 1 else valeur


def lire_cellule_droit(val):
    """Rend ``(taux_pct, interdit)`` pour une cellule de la colonne des droits.

    Sépare les trois réponses possibles du tarif — un taux, une interdiction
    d'importation, ou rien — pour qu'aucune ne soit lue pour une autre.
    """
    interdit = val is not None and MENTION_INTERDIT in str(val)
    return (None if interdit else parse_rate(val)), interdit


def extract_positions(filepath: str) -> List[Dict]:
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    logger.info(f"XLSX: {ws.max_row} rows x {ws.max_column} cols")

    positions = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 4:
            continue

        # Colonne 1 = code SH (رمز النظام المنسق)
        hs_code = str(row[1] or "").strip() if row[1] else ""
        if not hs_code or len(hs_code) < 6:
            continue

        code_clean = re.sub(r"[^0-9]", "", hs_code)
        if len(code_clean) < 6:
            continue

        # Colonne 2 = désignation (بيان المنتجات)
        designation = str(row[2] or "").strip() if row[2] else ""

        # Colonne 3 = taux DD (فئة الضريبة)
        dd_raw = row[3]
        dd_rate, dd_interdit = lire_cellule_droit(dd_raw)

        # Colonne 4 = préférence GZALE (Grande Zone arabe de libre-échange)
        arab_pref_raw = row[4] if len(row) > 4 else None
        arab_pref_rate, arab_interdit = lire_cellule_droit(arab_pref_raw)

        # Construire les taxes
        taxes = []
        if dd_rate is not None:
            taxes.append({
                "code": "DD",
                "name": "Droit de Douane",
                "name_fr": "Droit de Douane",
                "name_en": "Customs Duty",
                "name_ar": "ضريبة الوارد",
                "rate_pct": dd_rate,
                "rate_decimal": dd_rate / 100,
                "raw_value": str(dd_raw),
                "base": "CIF",
                "source": "customs.gov.ly",
                "legal_ref": None,
                "is_customs_duty": True,
                "is_vat": False,
                "is_excise": False,
            })

        # Préférence GZALE. Le tarif la PUBLIE position par position : ce
        # n'est pas une franchise déduite d'une appartenance à un bloc, mais
        # un taux national, au même titre que le droit NPF de la colonne
        # précédente. L'appartenance de l'origine à la GZALE reste, elle, une
        # condition que ce fichier ne tranche pas.
        preferential_rates = []
        if arab_pref_rate is not None:
            preferential_rates.append({
                "regime": "GZALE",
                "regime_name_fr": "Grande Zone arabe de libre-échange (GZALE/GAFTA)",
                "rate_pct": arab_pref_rate,
                "raw_value": str(arab_pref_raw),
                "source": "customs.gov.ly",
                "colonne_source": "التعريفة التفضيلية لدول جامعة الدول العربية",
            })

        # Une interdiction d'importation n'est pas un droit : elle est portée
        # comme restriction de la position, et le prélèvement correspondant
        # reste absent plutôt que fixé à zéro.
        restrictions = []
        if dd_interdit or arab_interdit:
            restrictions.append({
                "type": "IMPORTATION_INTERDITE",
                "portee": "NPF et GZALE" if (dd_interdit and arab_interdit) else (
                    "NPF" if dd_interdit else "GZALE"
                ),
                "verbatim": MENTION_INTERDIT,
                "libelle_fr": "Importation interdite",
                "source": "customs.gov.ly (التعريفة الجمركية 2022)",
            })

        positions.append({
            "national_code": code_clean,
            "hs6": code_clean[:6],
            "chapter": code_clean[:2],
            "heading": code_clean[:4] + "." + code_clean[4:6],
            "section": "",
            "statistical_unit": "",
            "check_digit": "",
            "designation": {
                "fr": "",
                "en": "",
                "ar": designation,
                "full_fr": "",
                "verbatim": hs_code,
            },
            "taxes": taxes,
            "export_taxes": [],
            "preferential_rates": preferential_rates,
            "fiscal_advantages": [],
            "formalities": [],
            "restrictions": restrictions,
            "legal_refs": [],
            "reglementation": {"import": [], "export": []},
            "quotas": {"qcs": None, "qci": None},
            "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
            "source_gaps": [],
            "lf_provisions": None,
            "data_status": "crawled_authentic",
            "source_quality": "crawled_authentic",
            "source": "customs.gov.ly (التعريفة الجمركية 2022)",
            "source_url": XLSX_URL,
            "raw_data": {"hs_code": hs_code, "designation_ar": designation, "dd_raw": str(dd_raw), "arab_pref_raw": str(arab_pref_raw)},
        })

    wb.close()
    return positions


def save(positions: List[Dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_tax_codes = set()
    for p in positions:
        for t in p.get("taxes", []):
            all_tax_codes.add(t.get("code", ""))

    result = {
        "country": "LBY",
        "country_name": "Libya",
        "source": "customs.gov.ly (التعريفة الجمركية 2022)",
        "source_url": XLSX_URL,
        "source_quality": "crawled_authentic",
        "extracted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "stats": {
            "total_positions": len(positions),
            "unique_tax_codes": sorted(all_tax_codes),
            "chapters_covered": len(set(p["chapter"] for p in positions)),
        },
        "sub_positions": positions,
    }

    output = DATA_DIR / "LBY_tariffs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(positions)} positions to {output}")


def main():
    logger.info("=== Libya Tariff Scraper ===")
    filepath = download_xlsx()
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
        print(f"Sample: {positions[0]['national_code']} {positions[0]['designation']['ar'][:40]}")


if __name__ == "__main__":
    main()
