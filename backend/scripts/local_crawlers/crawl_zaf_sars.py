#!/usr/bin/env python3
"""
Crawler SARS — Afrique du Sud (ZAF)
=====================================
Source : https://tariff.sars.gov.za  (Schedule 1 Part 1 — Customs Tariff)
Couvre aussi : NAM, BWA, LSO, SWZ (même CET SACU)

Prérequis sur votre machine :
    pip install requests beautifulsoup4 openpyxl

Usage :
    python crawl_zaf_sars.py
    python crawl_zaf_sars.py --chapters 01 02 03   # chapitres spécifiques
    python crawl_zaf_sars.py --out zaf_raw.json

Sortie : zaf_raw.json  (à uploader sur Replit)
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

BASE_URL = "https://tariff.sars.gov.za"
SEARCH_URL = f"{BASE_URL}/TariffSearch/TariffSearch"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-ZA,en;q=0.9",
    "Referer": BASE_URL,
}

# Chapitres HS (01-97)
ALL_CHAPTERS = [f"{i:02d}" for i in range(1, 98)]


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    # Charger la page d'accueil pour récupérer les cookies/tokens
    r = s.get(BASE_URL, timeout=20)
    r.raise_for_status()
    return s


def search_chapter(session: requests.Session, chapter: str) -> List[Dict]:
    """Recherche toutes les positions d'un chapitre HS."""
    positions = []

    # Chercher par préfixe de chapitre (ex: "01" → toutes les positions 01xxxx)
    payload = {
        "SearchText": chapter,
        "SearchType": "Chapter",
        "Schedule": "1",
        "Part": "1",
    }

    try:
        r = session.post(SEARCH_URL, data=payload, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  Erreur chapitre {chapter}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    # Chercher le tableau de résultats
    table = soup.find("table", {"class": re.compile(r"tariff|result|grid", re.I)})
    if not table:
        # Essayer de trouver n'importe quel tableau avec des données HS
        tables = soup.find_all("table")
        for t in tables:
            headers = [th.get_text(strip=True).lower() for th in t.find_all("th")]
            if any(h in headers for h in ["tariff heading", "hs code", "code", "heading"]):
                table = t
                break

    if not table:
        print(f"  Chapitre {chapter}: aucun tableau trouvé")
        return []

    rows = table.find_all("tr")[1:]  # skip header
    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cells) < 3:
            continue

        # Structure typique SARS: Code | Description | General Rate | EU | EFTA | ...
        code = cells[0].replace(".", "").replace(" ", "")
        if not re.match(r"^\d{6,10}$", code):
            continue

        description = cells[1] if len(cells) > 1 else ""
        general_rate_raw = cells[2] if len(cells) > 2 else ""

        # Parser le taux
        dd_rate = parse_sars_rate(general_rate_raw)

        positions.append({
            "code": code,
            "description_en": description,
            "dd_rate_raw": general_rate_raw,
            "dd_rate": dd_rate,
            "chapter": chapter,
            "digits": len(code),
        })

    return positions


def parse_sars_rate(raw: str) -> Optional[float]:
    """Parse un taux SARS: '20%', 'Free', '10% or R5/kg', 'No Change', etc."""
    raw = raw.strip()
    if not raw or raw.lower() in ("free", "no change", "—", "-", ""):
        return 0.0
    # Extraire le premier pourcentage
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", raw)
    if m:
        return float(m.group(1))
    # Taux spécifique en Rand uniquement (pas de %)
    return None


def crawl_all(chapters: List[str], delay: float = 1.5) -> Dict:
    """Crawler principal."""
    print(f"=== Crawler SARS ZAF — {len(chapters)} chapitres ===")
    session = get_session()
    print(f"Session établie: {BASE_URL}")

    all_positions = []
    for i, ch in enumerate(chapters, 1):
        print(f"[{i:02d}/{len(chapters)}] Chapitre {ch}...", end=" ")
        positions = search_chapter(session, ch)
        print(f"{len(positions)} positions")
        all_positions.extend(positions)
        time.sleep(delay)

    print(f"\nTotal: {len(all_positions)} positions")

    return {
        "country_code": "ZAF",
        "country_name": "South Africa",
        "source": "SARS — South African Revenue Service",
        "source_url": BASE_URL,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "Schedule 1 Part 1 — Customs Tariff (General Rate)",
            "SACU CET: mêmes taux pour NAM, BWA, LSO, SWZ",
            "VAT: 15% (Value-Added Tax Act 89/1991)",
        ],
        "positions": all_positions,
        "total": len(all_positions),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawler SARS ZAF")
    parser.add_argument("--chapters", nargs="+", default=ALL_CHAPTERS)
    parser.add_argument("--out", default="zaf_raw.json")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Délai entre requêtes en secondes (défaut: 1.5)")
    args = parser.parse_args()

    data = crawl_all(args.chapters, args.delay)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Sauvegardé: {args.out} ({len(data['positions'])} positions)")
    print(f"   Uploader ce fichier sur Replit dans: backend/data/raw_crawls/")


if __name__ == "__main__":
    main()
