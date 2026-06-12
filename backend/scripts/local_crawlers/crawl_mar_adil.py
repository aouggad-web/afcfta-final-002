#!/usr/bin/env python3
"""
Crawler ADIL — Maroc (MAR)
============================
Source : https://adil.douane.gov.ma
         Accès en Douane en Ligne — nomenclature nationale (NDP 10 chiffres)

Prérequis :
    pip install requests beautifulsoup4

Usage :
    python crawl_mar_adil.py
    python crawl_mar_adil.py --chapters 01 02
    python crawl_mar_adil.py --out mar_raw.json

Sortie : mar_raw.json  (à uploader sur Replit)
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

BASE_URL = "https://adil.douane.gov.ma"
TARIFF_URL = f"{BASE_URL}/adil/fr/tariff"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "fr-MA,fr;q=0.9,ar;q=0.8",
    "Referer": BASE_URL,
    "Origin": BASE_URL,
}

ALL_CHAPTERS = [f"{i:02d}" for i in range(1, 98)]


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    r = s.get(BASE_URL, timeout=20)
    r.raise_for_status()
    # Récupérer CSRF token si présent
    soup = BeautifulSoup(r.text, "html.parser")
    csrf = soup.find("meta", {"name": re.compile(r"csrf|token", re.I)})
    if csrf:
        s.headers["X-CSRF-Token"] = csrf.get("content", "")
    return s


def fetch_chapter_positions(session: requests.Session, chapter: str) -> List[Dict]:
    """Récupère toutes les positions NDP d'un chapitre."""
    positions = []

    # Essayer l'API JSON d'abord
    for api_url in [
        f"{TARIFF_URL}/positions/{chapter}",
        f"{BASE_URL}/adil/api/tariff/chapter/{chapter}",
        f"{BASE_URL}/adil/fr/recherche?code={chapter}&lang=fr",
    ]:
        try:
            r = session.get(api_url, timeout=25)
            if r.status_code == 200:
                # Tenter JSON
                try:
                    data = r.json()
                    positions = parse_adil_json(data, chapter)
                    if positions:
                        return positions
                except Exception:
                    pass
                # Sinon HTML
                positions = parse_adil_html(r.text, chapter)
                if positions:
                    return positions
        except Exception as e:
            continue

    # Fallback: recherche par chapitre via le moteur de recherche principal
    try:
        r = session.post(
            f"{BASE_URL}/adil/fr/recherche",
            data={"code": chapter, "lang": "fr"},
            timeout=30,
        )
        positions = parse_adil_html(r.text, chapter)
    except Exception as e:
        print(f"  Erreur chapitre {chapter}: {e}")

    return positions


def parse_adil_json(data, chapter: str) -> List[Dict]:
    """Parse la réponse JSON d'ADIL."""
    positions = []
    items = data if isinstance(data, list) else data.get("data", data.get("positions", []))
    for item in items:
        code = str(item.get("code", item.get("ndp", item.get("hs", "")))).replace(".", "")
        if not re.match(r"^\d{6,10}$", code):
            continue
        positions.append({
            "code": code,
            "description_fr": item.get("libelle_fr", item.get("description_fr", item.get("libelle", ""))),
            "description_ar": item.get("libelle_ar", ""),
            "dd_rate": item.get("dd", item.get("droit_douane", item.get("taux_dd", None))),
            "dd_rate_raw": str(item.get("dd_raw", "")),
            "tva_rate": item.get("tva", item.get("taux_tva", None)),
            "tic_rate": item.get("tic", item.get("taux_tic", None)),
            "other_taxes": item.get("autres_taxes", item.get("other_taxes", {})),
            "chapter": chapter,
            "digits": len(code),
            "raw": item,
        })
    return positions


def parse_adil_html(html: str, chapter: str) -> List[Dict]:
    """Parse le HTML d'ADIL pour extraire les positions tarifaires."""
    positions = []
    soup = BeautifulSoup(html, "html.parser")

    # Chercher tableau de résultats
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
        if not any(h in " ".join(headers) for h in ["code", "ndp", "position", "hs"]):
            continue
        # Identifier indices colonnes
        col_code = next((i for i, h in enumerate(headers) if "code" in h or "ndp" in h or "position" in h), 0)
        col_desc = next((i for i, h in enumerate(headers) if "lib" in h or "desc" in h or "désig" in h), 1)
        col_dd = next((i for i, h in enumerate(headers) if "dd" in h or "droit" in h or "import" in h), 2)
        col_tva = next((i for i, h in enumerate(headers) if "tva" in h or "taxe" in h), -1)

        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if not cells or col_code >= len(cells):
                continue
            code = cells[col_code].replace(".", "").replace(" ", "")
            if not re.match(r"^\d{6,10}$", code):
                continue
            desc = cells[col_desc] if col_desc < len(cells) else ""
            dd_raw = cells[col_dd] if col_dd < len(cells) else ""
            tva_raw = cells[col_tva] if col_tva >= 0 and col_tva < len(cells) else ""

            positions.append({
                "code": code,
                "description_fr": desc,
                "dd_rate_raw": dd_raw,
                "dd_rate": parse_rate(dd_raw),
                "tva_rate_raw": tva_raw,
                "tva_rate": parse_rate(tva_raw),
                "chapter": chapter,
                "digits": len(code),
            })

    return positions


def parse_rate(raw: str) -> Optional[float]:
    if not raw or raw.strip().lower() in ("exempt", "exonéré", "—", "-", "free", ""):
        return 0.0
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", raw)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def crawl_all(chapters: List[str], delay: float = 2.0) -> Dict:
    print(f"=== Crawler ADIL MAR — {len(chapters)} chapitres ===")
    session = get_session()
    print(f"Session établie: {BASE_URL}")

    all_positions = []
    for i, ch in enumerate(chapters, 1):
        print(f"[{i:02d}/{len(chapters)}] Chapitre {ch}...", end=" ", flush=True)
        positions = fetch_chapter_positions(session, ch)
        print(f"{len(positions)} positions")
        all_positions.extend(positions)
        time.sleep(delay)

    print(f"\nTotal: {len(all_positions)} positions")
    return {
        "country_code": "MAR",
        "country_name": "Maroc",
        "source": "ADIL — Douanes Maroc",
        "source_url": BASE_URL,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "raw_crawl",
        "notes": [
            "NDP: Nomenclature Douanière des Produits (10 chiffres)",
            "DD: 0/2.5/10/17.5/25/30/40/45/50%",
            "TVA: 20%/14%/10%/7%/exonéré",
            "TIC: Taxe Intérieure de Consommation (produits spécifiques)",
        ],
        "positions": all_positions,
        "total": len(all_positions),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawler ADIL MAR")
    parser.add_argument("--chapters", nargs="+", default=ALL_CHAPTERS)
    parser.add_argument("--out", default="mar_raw.json")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()

    data = crawl_all(args.chapters, args.delay)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Sauvegardé: {args.out}")
    print(f"   Uploader sur Replit dans: backend/data/raw_crawls/")


if __name__ == "__main__":
    main()
