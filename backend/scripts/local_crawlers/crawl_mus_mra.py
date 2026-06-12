#!/usr/bin/env python3
"""
Crawler MRA — Maurice (MUS)
==============================
Source : https://www.mra.mu  (Mauritius Revenue Authority)
         Customs Tariff Schedule — HS8 + Customs Duty + VAT 15% + Excise

Prérequis :
    pip install requests beautifulsoup4

Usage :
    python crawl_mus_mra.py
    python crawl_mus_mra.py --chapters 01 02 03
    python crawl_mus_mra.py --out mus_raw.json

Le script tente d'abord le moteur de recherche en ligne,
puis propose de parser le PDF tariff si disponible.

Sortie : mus_raw.json  (à uploader sur Replit)
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

BASE_URL = "https://www.mra.mu"
ESERVICES_URL = "https://eservices.mra.mu"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-MU,en;q=0.9,fr;q=0.8",
    "Referer": BASE_URL,
}

ALL_CHAPTERS = [f"{i:02d}" for i in range(1, 98)]

MRA_SEARCH_PATTERNS = [
    "{base}/index.php/customs-department/tariff-search?hs={code}",
    "{base}/index.php/customs/tariff?code={code}",
    "{eservices}/customs/tariff/search?hs={code}",
    "{eservices}/tariff?chapter={chapter}",
    "{base}/index.php/customs-department/customs-tariff/{chapter}",
]


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    r = s.get(BASE_URL, timeout=20)
    print(f"  MRA: {r.status_code}")
    return s


def detect_url(session: requests.Session) -> Optional[str]:
    test_code = "010121"
    for pattern in MRA_SEARCH_PATTERNS:
        url = pattern.format(base=BASE_URL, eservices=ESERVICES_URL, code=test_code, chapter="01")
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200 and re.search(r"\d{6,8}", r.text):
                print(f"  URL active: {url}")
                return pattern
        except Exception:
            continue
    return None


def fetch_chapter(session: requests.Session, chapter: str, pattern: Optional[str]) -> List[Dict]:
    positions = []
    urls = []
    if pattern:
        urls.append(pattern.format(base=BASE_URL, eservices=ESERVICES_URL, code=chapter, chapter=chapter))
    urls += [
        f"{BASE_URL}/index.php/customs-department/customs-tariff/{chapter}",
        f"{ESERVICES_URL}/tariff/chapter/{chapter}",
    ]

    for url in urls:
        try:
            r = session.get(url, timeout=30)
            if r.status_code != 200:
                continue
            try:
                data = r.json()
                p = parse_json(data, chapter)
                if p:
                    return p
            except Exception:
                pass
            p = parse_html(r.text, chapter)
            if p:
                return p
        except Exception:
            continue
    return positions


def parse_json(data, chapter: str) -> List[Dict]:
    positions = []
    items = data if isinstance(data, list) else data.get("data", data.get("tariffs", []))
    for item in items:
        code = str(item.get("hs_code", item.get("code", ""))).replace(".", "").replace(" ", "")
        if not re.match(r"^\d{4,10}$", code):
            continue
        positions.append({
            "code": code,
            "description_en": item.get("description", ""),
            "dd_rate": _to_float(item.get("customs_duty", item.get("cd", item.get("duty")))),
            "excise_rate": _to_float(item.get("excise", item.get("excise_duty"))),
            "vat_rate": _to_float(item.get("vat", 15.0)),
            "chapter": chapter,
            "digits": len(code),
        })
    return positions


def parse_html(html: str, chapter: str) -> List[Dict]:
    positions = []
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        if not any(h in " ".join(headers) for h in ["hs", "code", "tariff", "heading", "commodity"]):
            continue

        col_code   = _col(headers, ["hs code", "hs", "code", "tariff", "heading"])
        col_desc   = _col(headers, ["description", "commodity", "goods"])
        col_dd     = _col(headers, ["customs duty", "cd", "duty", "rate"])
        col_excise = _col(headers, ["excise"])
        col_vat    = _col(headers, ["vat"])

        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cells:
                continue
            code = cells[col_code].replace(".", "").replace(" ", "") if col_code is not None and col_code < len(cells) else ""
            if not re.match(r"^\d{4,10}$", code):
                continue
            positions.append({
                "code": code,
                "description_en": cells[col_desc] if col_desc and col_desc < len(cells) else "",
                "dd_rate_raw": cells[col_dd] if col_dd and col_dd < len(cells) else "",
                "dd_rate": parse_rate(cells[col_dd]) if col_dd and col_dd < len(cells) else None,
                "excise_rate": parse_rate(cells[col_excise]) if col_excise and col_excise < len(cells) else None,
                "vat_rate": parse_rate(cells[col_vat]) if col_vat and col_vat < len(cells) else 15.0,
                "chapter": chapter,
                "digits": len(code),
            })
    return positions


def _col(headers: List[str], keywords: List[str]) -> Optional[int]:
    for kw in keywords:
        for i, h in enumerate(headers):
            if kw in h:
                return i
    return None


def parse_rate(raw: str) -> Optional[float]:
    if not raw or raw.strip().lower() in ("free", "exempt", "—", "-", ""):
        return 0.0
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%?", raw)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(str(v).replace("%", "").replace(",", ".").strip())
    except Exception:
        return None


def crawl_all(chapters: List[str], delay: float = 1.5) -> Dict:
    print(f"=== Crawler MRA MUS — {len(chapters)} chapitres ===")
    session = get_session()
    print("Détection URL...")
    pattern = detect_url(session)

    all_positions = []
    for i, ch in enumerate(chapters, 1):
        print(f"[{i:02d}/{len(chapters)}] Chapitre {ch}...", end=" ", flush=True)
        positions = fetch_chapter(session, ch, pattern)
        print(f"{len(positions)} positions")
        all_positions.extend(positions)
        time.sleep(delay)

    print(f"\nTotal: {len(all_positions)} positions")
    return {
        "country_code": "MUS",
        "country_name": "Mauritius",
        "source": "MRA — Mauritius Revenue Authority",
        "source_url": BASE_URL,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "Customs Duty: 0/5/15/30% (varies by product)",
            "VAT: 15% standard (Value Added Tax Act)",
            "Excise Duty: alcohol, tobacco, vehicles",
            "No ECOWAS/SACU levy — Maurice standalone",
        ],
        "positions": all_positions,
        "total": len(all_positions),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawler MRA MUS")
    parser.add_argument("--chapters", nargs="+", default=ALL_CHAPTERS)
    parser.add_argument("--out", default="mus_raw.json")
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()

    data = crawl_all(args.chapters, args.delay)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Sauvegardé: {args.out}")
    print(f"   Uploader sur Replit dans: backend/data/raw_crawls/")


if __name__ == "__main__":
    main()
