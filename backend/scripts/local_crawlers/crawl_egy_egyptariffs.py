#!/usr/bin/env python3
"""
Crawler Egyptariffs — Égypte (EGY)
=====================================
Source : https://egyptariffs.com
         Egyptian Customs Authority — tarif douanier officiel

Prérequis :
    pip install requests beautifulsoup4

Usage :
    python crawl_egy_egyptariffs.py
    python crawl_egy_egyptariffs.py --chapters 01 02 03
    python crawl_egy_egyptariffs.py --out egy_raw.json

Sortie : egy_raw.json  (à uploader sur Replit)
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

BASE_URL = "https://egyptariffs.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "ar-EG,ar;q=0.9,en;q=0.8",
    "Referer": BASE_URL,
}

ALL_CHAPTERS = [f"{i:02d}" for i in range(1, 98)]

# URLs connues pour egyptariffs.com
SEARCH_PATTERNS = [
    "{base}/tariff/search?hs={code}",
    "{base}/search?q={code}",
    "{base}/tariff?chapter={chapter}",
    "{base}/en/tariff/chapter/{chapter}",
    "{base}/ar/tariff/chapter/{chapter}",
    "{base}/tariff/chapter/{chapter}",
]


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    r = s.get(BASE_URL, timeout=20)
    # Récupérer cookies CSRF
    soup = BeautifulSoup(r.text, "html.parser")
    meta = soup.find("meta", {"name": "_token"}) or soup.find("input", {"name": "_token"})
    if meta:
        token = meta.get("content") or meta.get("value", "")
        s.headers["X-CSRF-TOKEN"] = token

    # Identifier quelle URL de recherche fonctionne
    print(f"  Page d'accueil: {r.status_code}")
    return s


def find_working_url(session: requests.Session, chapter: str) -> Optional[str]:
    """Détecter l'URL de recherche qui fonctionne."""
    test_code = f"{chapter}0110"  # ex: "010110"
    for pattern in SEARCH_PATTERNS:
        url = pattern.format(base=BASE_URL, code=test_code, chapter=chapter)
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200 and len(r.text) > 500:
                soup = BeautifulSoup(r.text, "html.parser")
                # Vérifier qu'il y a des données tarifaires
                if soup.find(string=re.compile(r"\d{6,10}", re.I)):
                    return pattern
        except Exception:
            continue
    return None


def fetch_chapter(session: requests.Session, chapter: str, url_pattern: str) -> List[Dict]:
    """Récupère les positions d'un chapitre."""
    positions = []

    # Essai 1: URL du chapitre complet
    urls_to_try = [
        url_pattern.format(base=BASE_URL, code=chapter, chapter=chapter),
        f"{BASE_URL}/tariff/chapter/{chapter}",
        f"{BASE_URL}/tariff?chapter={chapter}",
    ]

    for url in urls_to_try:
        try:
            r = session.get(url, timeout=30)
            if r.status_code != 200:
                continue
            # Essai JSON
            try:
                data = r.json()
                if isinstance(data, (list, dict)):
                    p = parse_json_response(data, chapter)
                    if p:
                        return p
            except Exception:
                pass
            # HTML
            p = parse_html_response(r.text, chapter)
            if p:
                return p
        except Exception:
            continue

    # Fallback: recherche position par position (HS6 → HS10)
    # Pour chaque HS4 du chapitre, chercher les sous-positions
    for heading_suffix in range(100):
        hs4 = f"{chapter}{heading_suffix:02d}"
        url = f"{BASE_URL}/tariff/search?hs={hs4}"
        try:
            r = session.get(url, timeout=20)
            if r.status_code == 200:
                p = parse_html_response(r.text, chapter)
                positions.extend(p)
            time.sleep(0.5)
        except Exception:
            continue
        if len(positions) > 0 and heading_suffix > 20:
            # Assez de positions, probablement en fin de chapitre
            break

    return positions


def parse_json_response(data, chapter: str) -> List[Dict]:
    positions = []
    items = data if isinstance(data, list) else data.get("data", data.get("tariffs", data.get("results", [])))
    for item in items:
        code = str(item.get("hs_code", item.get("code", item.get("tariff_code", "")))).replace(".", "").replace(" ", "")
        if not re.match(r"^\d{4,10}$", code):
            continue
        positions.append({
            "code": code,
            "description_en": item.get("description", item.get("description_en", "")),
            "description_ar": item.get("description_ar", item.get("arabic_description", "")),
            "dd_rate": _to_float(item.get("customs_duty", item.get("cd", item.get("duty_rate")))),
            "dd_rate_raw": str(item.get("duty_raw", "")),
            "additional_customs_duty": _to_float(item.get("additional_duty", item.get("acd"))),
            "vat_rate": _to_float(item.get("vat", item.get("vat_rate", 14.0))),
            "sales_tax": _to_float(item.get("sales_tax", item.get("st"))),
            "chapter": chapter,
            "digits": len(code),
        })
    return positions


def parse_html_response(html: str, chapter: str) -> List[Dict]:
    positions = []
    soup = BeautifulSoup(html, "html.parser")

    # Trouver toutes les lignes tarifaires — chercher des codes HS dans le texte
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        if len(headers) < 2:
            continue

        # Identifier colonnes
        col_code = _find_col(headers, ["hs", "code", "tariff", "heading", "رقم"])
        col_desc = _find_col(headers, ["desc", "description", "البيان", "السلعة", "item"])
        col_dd   = _find_col(headers, ["duty", "dd", "customs", "الجمركي", "rate", "نسبة"])
        col_vat  = _find_col(headers, ["vat", "ضريبة قيمة", "value added"])

        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cells:
                continue
            code = cells[col_code].replace(".", "").replace(" ", "") if col_code is not None and col_code < len(cells) else ""
            if not re.match(r"^\d{4,10}$", code):
                continue
            dd_raw = cells[col_dd] if col_dd is not None and col_dd < len(cells) else ""
            vat_raw = cells[col_vat] if col_vat is not None and col_vat < len(cells) else "14"
            positions.append({
                "code": code,
                "description_en": cells[col_desc] if col_desc is not None and col_desc < len(cells) else "",
                "dd_rate_raw": dd_raw,
                "dd_rate": parse_rate(dd_raw),
                "vat_rate": parse_rate(vat_raw) or 14.0,
                "chapter": chapter,
                "digits": len(code),
            })
    return positions


def _find_col(headers: List[str], keywords: List[str]) -> Optional[int]:
    for kw in keywords:
        for i, h in enumerate(headers):
            if kw in h:
                return i
    return None


def parse_rate(raw: str) -> Optional[float]:
    if not raw or raw.strip().lower() in ("free", "exempt", "معفى", "—", "-", ""):
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


def crawl_all(chapters: List[str], delay: float = 2.0) -> Dict:
    print(f"=== Crawler Egyptariffs EGY — {len(chapters)} chapitres ===")
    session = get_session()

    # Détecter l'URL qui fonctionne
    print("Détection de l'URL de recherche...")
    url_pattern = find_working_url(session, "01")
    if url_pattern:
        print(f"  URL fonctionnelle: {url_pattern}")
    else:
        print("  Aucune URL pré-détectée — essais directs par chapitre")
        url_pattern = "{base}/tariff/chapter/{chapter}"

    all_positions = []
    for i, ch in enumerate(chapters, 1):
        print(f"[{i:02d}/{len(chapters)}] Chapitre {ch}...", end=" ", flush=True)
        positions = fetch_chapter(session, ch, url_pattern)
        print(f"{len(positions)} positions")
        all_positions.extend(positions)
        time.sleep(delay)

    print(f"\nTotal: {len(all_positions)} positions")
    return {
        "country_code": "EGY",
        "country_name": "Egypt",
        "source": "Egyptian Customs Authority — egyptariffs.com",
        "source_url": BASE_URL,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "Customs Duty (CD): 0/2/5/10/20/30/40%",
            "Additional Customs Duty (ACD): variable",
            "VAT: 14% standard",
            "Sales Tax: certains produits",
        ],
        "positions": all_positions,
        "total": len(all_positions),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawler Egyptariffs EGY")
    parser.add_argument("--chapters", nargs="+", default=ALL_CHAPTERS)
    parser.add_argument("--out", default="egy_raw.json")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    data = crawl_all(args.chapters, args.delay)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Sauvegardé: {args.out}")
    print(f"   Uploader sur Replit dans: backend/data/raw_crawls/")


if __name__ == "__main__":
    main()
