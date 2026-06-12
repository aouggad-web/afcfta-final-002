#!/usr/bin/env python3
"""
Crawler ERCA — Éthiopie (ETH)
================================
Source : https://customs.erca.gov.et
         Ethiopian Customs Commission (ECC) — tarif douanier officiel

Prérequis :
    pip install requests beautifulsoup4

Usage :
    python crawl_eth_erca.py
    python crawl_eth_erca.py --chapters 01 02 03
    python crawl_eth_erca.py --out eth_raw.json

Sortie : eth_raw.json  (à uploader sur Replit)
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

BASE_URL = "https://customs.erca.gov.et"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.8",
    "Accept-Language": "en-ET,en;q=0.9,am;q=0.8",
    "Referer": BASE_URL,
}

ALL_CHAPTERS = [f"{i:02d}" for i in range(1, 98)]

# URLs ERCA connues — à tester dans l'ordre
ERCA_SEARCH_URLS = [
    "{base}/tariff/search?hs_code={code}",
    "{base}/tariff?chapter={chapter}",
    "{base}/customs/tariff/search?q={code}",
    "{base}/en/tariff/search?hs={code}",
    "{base}/api/tariff?chapter={chapter}",
    "{base}/tariff/chapter/{chapter}",
]


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        r = s.get(BASE_URL, timeout=20, allow_redirects=True)
        print(f"  Page principale: {r.status_code} → {r.url}")
        # Récupérer CSRF si présent
        soup = BeautifulSoup(r.text, "html.parser")
        for sel in [
            soup.find("meta", {"name": "_token"}),
            soup.find("input", {"name": "_token"}),
            soup.find("meta", {"name": "csrf-token"}),
        ]:
            if sel:
                token = sel.get("content") or sel.get("value", "")
                s.headers["X-CSRF-TOKEN"] = token
                break
    except Exception as e:
        print(f"  Avertissement session: {e}")
    return s


def detect_search_url(session: requests.Session) -> Optional[str]:
    """Trouve l'URL de recherche active."""
    test_code = "010121"
    for pattern in ERCA_SEARCH_URLS:
        url = pattern.format(base=BASE_URL, code=test_code, chapter="01")
        try:
            r = session.get(url, timeout=15, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 300:
                # Vérifier présence de données tarifaires
                if re.search(r"\d{4,10}", r.text):
                    print(f"  URL détectée: {url}")
                    return pattern
        except Exception:
            continue
    return None


def fetch_chapter(session: requests.Session, chapter: str, search_pattern: str) -> List[Dict]:
    """Récupère les positions tarifaires d'un chapitre."""
    positions = []

    urls = [
        search_pattern.format(base=BASE_URL, code=chapter, chapter=chapter),
        f"{BASE_URL}/tariff/chapter/{chapter}",
        f"{BASE_URL}/tariff?chapter={chapter}",
    ]

    for url in urls:
        try:
            r = session.get(url, timeout=30, allow_redirects=True)
            if r.status_code != 200:
                continue
            # JSON ?
            try:
                data = r.json()
                p = parse_json(data, chapter)
                if p:
                    return p
            except Exception:
                pass
            # HTML
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
            "description_en": item.get("description", item.get("description_en", "")),
            "description_am": item.get("description_am", ""),
            "dd_rate": _to_float(item.get("customs_duty", item.get("cd", item.get("duty")))),
            "excise_rate": _to_float(item.get("excise", item.get("excise_duty"))),
            "surtax_rate": _to_float(item.get("surtax", item.get("sur_tax"))),
            "vat_rate": _to_float(item.get("vat", 15.0)),
            "withholding_rate": _to_float(item.get("withholding", item.get("wht"))),
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
        if not any(h in " ".join(headers) for h in ["hs", "code", "tariff", "heading"]):
            continue

        col_code    = _col(headers, ["hs code", "hs", "code", "tariff code", "heading"])
        col_desc    = _col(headers, ["description", "commodity", "goods"])
        col_dd      = _col(headers, ["customs duty", "cd", "duty", "dd", "rate"])
        col_excise  = _col(headers, ["excise"])
        col_surtax  = _col(headers, ["surtax", "sur tax"])
        col_vat     = _col(headers, ["vat", "value added"])
        col_wht     = _col(headers, ["withholding", "wht"])

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
                "surtax_rate": parse_rate(cells[col_surtax]) if col_surtax and col_surtax < len(cells) else None,
                "vat_rate": parse_rate(cells[col_vat]) if col_vat and col_vat < len(cells) else 15.0,
                "withholding_rate": parse_rate(cells[col_wht]) if col_wht and col_wht < len(cells) else None,
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
    if not raw or raw.strip().lower() in ("free", "exempt", "—", "-", "0", ""):
        return 0.0
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%?", raw)
    if m:
        val = float(m.group(1).replace(",", "."))
        return val if val <= 100 else val / 100
    return None


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(str(v).replace("%", "").replace(",", ".").strip())
    except Exception:
        return None


def crawl_all(chapters: List[str], delay: float = 2.0) -> Dict:
    print(f"=== Crawler ERCA ETH — {len(chapters)} chapitres ===")
    session = get_session()

    print("Détection URL de recherche ERCA...")
    search_pattern = detect_search_url(session)
    if not search_pattern:
        print("  Aucune URL détectée — utilisation du pattern par défaut")
        search_pattern = "{base}/tariff/chapter/{chapter}"

    all_positions = []
    for i, ch in enumerate(chapters, 1):
        print(f"[{i:02d}/{len(chapters)}] Chapitre {ch}...", end=" ", flush=True)
        positions = fetch_chapter(session, ch, search_pattern)
        print(f"{len(positions)} positions")
        all_positions.extend(positions)
        time.sleep(delay)

    print(f"\nTotal: {len(all_positions)} positions")
    return {
        "country_code": "ETH",
        "country_name": "Ethiopia",
        "source": "Ethiopian Customs Commission (ECC) — customs.erca.gov.et",
        "source_url": BASE_URL,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "Customs Duty (CD): 0/5/10/20/25/30/35%",
            "Excise Duty: 0/10/15/20/25/30/33/40/50/75/100%",
            "Surtax: 10% sur valeur CIF+CD+Excise",
            "VAT: 15% standard",
            "Withholding Tax: 3% à l'importation",
        ],
        "positions": all_positions,
        "total": len(all_positions),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawler ERCA ETH")
    parser.add_argument("--chapters", nargs="+", default=ALL_CHAPTERS)
    parser.add_argument("--out", default="eth_raw.json")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    data = crawl_all(args.chapters, args.delay)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Sauvegardé: {args.out}")
    print(f"   Uploader sur Replit dans: backend/data/raw_crawls/")


if __name__ == "__main__":
    main()
