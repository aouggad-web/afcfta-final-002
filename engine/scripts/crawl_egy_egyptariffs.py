#!/usr/bin/env python3
"""
Crawler Douanes Égyptiennes — Égypte (EGY)
============================================
Source : https://customs.gov.eg/Services/Tarif
         Moslaha El Gamareg (Egyptian Customs Authority)

Prérequis :
    pip install requests beautifulsoup4

Usage :
    python crawl_egy_egyptariffs.py
    python crawl_egy_egyptariffs.py --chapters 01 02 03
    python crawl_egy_egyptariffs.py --out egy_raw.json

Sortie : egy_raw.json  (à uploader sur Replit)

-----------------------------------------------------------------------
CORRECTIF v2 — mapping de colonnes taxes (bug critique)
-----------------------------------------------------------------------
L'API /Services/TrfDetails retourne une liste "Taxes" de chaînes de la forme
    "NOM_TAXE :  VALEUR"
ex. :
    "الرسم الجمركي :  5%"
    "ضريبة الجدول :  14% (من القيمة + ر.ض.جمركية)"
    "ضريبة القيمة المضافة :  صفر"

Bug v1 : les mots-clés ("وارد", "جمركي", "جمرك") étaient cherchés dans la
chaîne entière. Or la valeur de la taxe de tableau (ضريبة الجدول) contient
"جمركية" (ex. "ر.ض.جمركية"), ce qui déclenchait à tort la branche DD pour
6 091 / 8 274 positions — le taux DD réel était alors écrasé ou absent.

Correctif : séparer label et valeur sur ":" avant toute vérification de
mots-clés, et n'appliquer les mots-clés qu'au LABEL. La taxe de tableau est
capturée dans un champ dédié "table_tax_rate_raw" / "table_tax_rate".
"""

import argparse
import json
import re
import time
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installer: pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://customs.gov.eg"
TARIF_URL = f"{BASE_URL}/Services/Tarif"
DETAILS_URL = f"{BASE_URL}/Services/TrfDetails"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "ar-EG,ar;q=0.9,en;q=0.8",
    "Referer": BASE_URL,
}

ALL_CHAPTERS = [f"{i:02d}" for i in range(1, 98)]


def chapter_to_id(chapter: str) -> int:
    return int(chapter)


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    r = s.get(BASE_URL, timeout=20)
    r.raise_for_status()
    return s


def parse_rate(raw: str) -> Optional[float]:
    """Parse '5%', 'صفر' (zéro), '14% (من القيمة…)' → extrait la partie numérique."""
    raw = raw.strip()
    if not raw or raw in ("صفر", "—", "-", ""):
        return 0.0
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", raw)
    if m:
        return float(m.group(1).replace(",", "."))
    # Montant spécifique (ex. "0.48 جنية لكل لتر") — retourner None, raw préservé
    return None


def parse_taxes(taxes: List[str]) -> Dict:
    """Parse la liste de taxes retournée par l'API TrfDetails.

    L'API retourne ex. :
      ['الرسم الجمركي :  5%',
       'ضريبة الجدول :  14% (من القيمة + ر.ض.جمركية)',
       'ضريبة القيمة المضافة :  صفر']

    IMPORTANT : les mots-clés sont appliqués au LABEL uniquement (avant ':'),
    jamais à la valeur — sinon 'جمركية' dans '(من القيمة + ر.ض.جمركية)'
    déclenche à tort la branche DD pour les entrées de type ضريبة الجدول.
    """
    result = {
        "dd_rate": None,         "dd_rate_raw": "",
        "vat_rate": None,        "vat_rate_raw": "",
        "table_tax_rate": None,  "table_tax_rate_raw": "",  # ضريبة الجدول (excise/schedule)
    }
    for tax in taxes:
        if ":" in tax:
            label, raw = tax.split(":", 1)
        else:
            label = tax
            raw = tax
        label = label.strip()
        raw = raw.strip()

        # Droits de douane — مطابقة sur le LABEL uniquement
        if any(kw in label for kw in ("وارد", "جمركي", "جمرك", "الرسم")):
            result["dd_rate_raw"] = raw
            result["dd_rate"] = parse_rate(raw)
        # TVA / ضريبة القيمة المضافة
        elif any(kw in label for kw in ("مضاف", "قيمة مضافة")) or "vat" in label.lower():
            result["vat_rate_raw"] = raw
            result["vat_rate"] = parse_rate(raw)
        # Taxe de tableau / excise — ضريبة الجدول / ضريبة المبيعات
        elif any(kw in label for kw in ("جدول", "مبيعات", "استهلاك")):
            result["table_tax_rate_raw"] = raw
            result["table_tax_rate"] = parse_rate(raw)

    return result


def fetch_chapter_page(session: requests.Session, chapter_id: int, page: int) -> tuple:
    """Retourne (codes, max_page)."""
    params = {"page": page, "type": 1, "chapterId": chapter_id}
    r = session.get(TARIF_URL, params=params, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    codes = []
    table = soup.find("table")
    if table:
        for row in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if cells and re.match(r"^\d{2}/\d{2}/\d{2}/\d{2}/\d{2}$", cells[0]):
                codes.append(cells[0])

    page_links = soup.find_all("a", href=lambda h: h and "page=" in str(h))
    page_nums = [int(re.search(r"page=(\d+)", a["href"]).group(1))
                 for a in page_links if re.search(r"page=(\d+)", a["href"])]
    max_page = max(page_nums) if page_nums else page

    return codes, max_page


def format_code(trf_number: str) -> str:
    """'01/01/21/00/00' -> '0101210000'"""
    return trf_number.replace("/", "")


def get_details(session: requests.Session, trf_number: str, delay: float) -> Dict:
    """Récupère les taxes et instructions pour un code tarifaire."""
    try:
        r = session.get(DETAILS_URL, params={"trfNumber": trf_number, "trfType": 1}, timeout=20)
        r.raise_for_status()
        data = r.json()
        time.sleep(delay)
        return data
    except Exception:
        return {}


def fetch_chapter(session: requests.Session, chapter: str, detail_delay: float) -> List[Dict]:
    chapter_id = chapter_to_id(chapter)
    all_codes = []

    page = 1
    while True:
        try:
            codes, max_page = fetch_chapter_page(session, chapter_id, page)
            all_codes.extend(codes)
        except Exception as e:
            print(f"  Erreur page {page}: {e}")
            break
        if page >= max_page:
            break
        page += 1
        time.sleep(0.3)

    positions = []
    for trf_number in all_codes:
        details = get_details(session, trf_number, detail_delay)
        code = format_code(trf_number)
        taxes = parse_taxes(details.get("Taxes", []))

        positions.append({
            "code": code,
            "trf_number": trf_number,
            "description_ar": details.get("ShortDesc", ""),
            "dd_rate_raw":        taxes["dd_rate_raw"],
            "dd_rate":            taxes["dd_rate"],
            "table_tax_rate_raw": taxes["table_tax_rate_raw"],  # ضريبة الجدول
            "table_tax_rate":     taxes["table_tax_rate"],
            "vat_rate_raw":       taxes["vat_rate_raw"],
            "vat_rate":           taxes["vat_rate"],
            "instructions": details.get("Instructions", []),
            "chapter": chapter,
            "digits": len(code),
        })

    return positions


def crawl_all(chapters: List[str], detail_delay: float = 0.3) -> Dict:
    print(f"=== Crawler Douanes EGY v2 — {len(chapters)} chapitres ===")
    session = get_session()
    print(f"Session établie: {BASE_URL}")

    all_positions = []
    for i, ch in enumerate(chapters, 1):
        print(f"[{i:02d}/{len(chapters)}] Chapitre {ch}...", end=" ", flush=True)
        positions = fetch_chapter(session, ch, detail_delay)
        print(f"{len(positions)} positions")
        all_positions.extend(positions)
        time.sleep(0.5)

    print(f"\nTotal: {len(all_positions)} positions")
    return {
        "country_code": "EGY",
        "country_name": "Egypt",
        "source": "Moslaha El Gamareg — Egyptian Customs Authority",
        "source_url": TARIF_URL,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "crawler_version": "2",
        "notes": [
            "Customs Duty (الرسم الجمركي / ضريبة الوارد): variable → dd_rate_raw / dd_rate",
            "Schedule/Excise Tax (ضريبة الجدول): CIF+DD basis → table_tax_rate_raw / table_tax_rate",
            "VAT (ضريبة القيمة المضافة): 14% standard → vat_rate_raw / vat_rate",
            "Source: customs.gov.eg official tariff",
        ],
        "positions": all_positions,
        "total": len(all_positions),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawler Douanes EGY v2")
    parser.add_argument("--chapters", nargs="+", default=ALL_CHAPTERS)
    parser.add_argument("--out", default="egy_raw.json")
    parser.add_argument("--delay", type=float, default=0.3,
                        help="Délai entre appels détails en secondes (défaut: 0.3)")
    args = parser.parse_args()

    data = crawl_all(args.chapters, args.delay)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSauvegardé: {args.out} ({len(data['positions'])} positions)")
    print(f"   Uploader sur Replit dans: backend/data/raw_crawls/")


if __name__ == "__main__":
    main()
