#!/usr/bin/env python3
"""
Crawler PwC Worldwide Tax Summaries — Accises/TIC par pays.

Source : taxsummaries.pwc.com (cabinet de premier ordre, vérifié annuellement).
Les taux publiés par PwC proviennent des CGI nationaux et lois de finances
— ce sont des REFLEXIONS de sources officielles, pas des extrapolations.

Schéma cible unifié :
  {
    "country_iso3": "SEN",
    "source": "PwC Worldwide Tax Summaries",
    "source_url": "https://taxsummaries.pwc.com/senegal/corporate/other-taxes",
    "source_type": "international_cabinet_verified",
    "last_reviewed": "07 August 2026",
    "excise_taxes": [
      {
        "product": "Tobacco",
        "rate_pct": 70.0,
        "rate_specific": null,
        "raw_text": "Tobacco: 70%.",
        "legal_ref": "CGI Sénégal, Loi de Finances"
      }
    ]
  }

Pays couverts :
  MAR, TUN, EGY, SEN, CIV, GAB, TCD
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled" / "excise_taxes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.5",
}

# Mapping ISO3 → slug PwC
PWC_COUNTRIES = {
    "MAR": {"slug": "morocco", "name": "Maroc"},
    "TUN": {"slug": "tunisia", "name": "Tunisie"},
    "EGY": {"slug": "egypt", "name": "Égypte"},
    "SEN": {"slug": "senegal", "name": "Sénégal"},
    "CIV": {"slug": "ivory-coast", "name": "Côte d'Ivoire"},
    "GAB": {"slug": "gabon", "name": "Gabon"},
    "TCD": {"slug": "chad", "name": "Tchad"},
}

RATE_PCT_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
RATE_SPECIFIC_PATTERN = re.compile(
    r"(?:XOF|XAF|FCFA|EGP|DA|DH|NGN|GHS|KES|TND|MAD)\s*([\d.,]+)"
    r"|([\d.,]+)\s*(?:XOF|XAF|FCFA|EGP|DA|DH|NGN|GHS|KES|TND|MAD)",
    re.IGNORECASE,
)
RATE_PER_UNIT_PATTERN = re.compile(
    r"([\d.,]+)\s*(?:XOF|XAF|FCFA|EGP|DA|DH)\s*(?:per|/)\s*(litre|liter|kg|hectolitre|hl|étui|pack|unit|barrel)",
    re.IGNORECASE,
)


def fetch_page(url: str, retries: int = 3) -> Optional[str]:
    """Fetch page HTML with retries."""
    for attempt in range(retries):
        try:
            resp = httpx.get(url, timeout=60, follow_redirects=True, headers=HEADERS)
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"HTTP {resp.status_code} for {url}")
            if resp.status_code == 429:
                time.sleep(10)
        except Exception as e:
            logger.warning(f"Fetch error (attempt {attempt+1}) for {url}: {e}")
        time.sleep(3)
    return None


def extract_last_reviewed(soup: BeautifulSoup) -> str:
    """Extrait la date de 'Last reviewed'."""
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Last\s+reviewed\s*[-–]\s*(\d{1,2}\s+\w+\s+\d{4})", text)
    return match.group(1) if match else ""


def parse_rate(text: str) -> Dict[str, Any]:
    """Extrait le taux (%) et/ou la valeur spécifique depuis un texte."""
    rate_pct = None
    rate_specific = None
    rate_per_unit = None

    pct_match = RATE_PCT_PATTERN.search(text)
    if pct_match:
        rate_pct = float(pct_match.group(1).replace(",", "."))

    per_unit_match = RATE_PER_UNIT_PATTERN.search(text)
    if per_unit_match:
        rate_per_unit = per_unit_match.group(0)

    spec_match = RATE_SPECIFIC_PATTERN.search(text)
    if spec_match and not rate_pct and not rate_per_unit:
        rate_specific = spec_match.group(0)

    return {
        "rate_pct": rate_pct,
        "rate_specific": rate_specific,
        "rate_per_unit": rate_per_unit,
    }


def extract_excise_taxes(soup: BeautifulSoup) -> List[Dict]:
    """
    Extrait toutes les taxes d'accise depuis la section 'Excise taxes'
    ou 'Other taxes' de la page PwC. Gère plusieurs structures HTML :
    - <h2>Excise taxes</h2> + <li>... (SEN, GAB, TCD)
    - <h2>Excise taxes</h2> + <p>... (MAR, TUN)
    - <h4>Alcoholic beverages</h4> + <p>... sous <h3>Law No. 157</h3> (EGY)
    """
    excise_taxes = []

    # 1. Chercher le heading 'Excise taxes' ou 'Excise duties'
    excise_heading = None
    for tag in soup.find_all(["h2", "h3", "h4"]):
        text = tag.get_text(strip=True).lower()
        if "excise" in text and ("tax" in text or "dut" in text):
            excise_heading = tag
            break

    if excise_heading:
        # Collecter TOUS les éléments suivants jusqu'au prochain heading de même niveau
        elements = []
        current = excise_heading.find_next()
        heading_level = int(excise_heading.name[1])  # h2 → 2
        while current:
            if current.name and current.name.startswith("h"):
                current_level = int(current.name[1])
                if current_level <= heading_level:
                    break
                # Les sous-headings (h3 sous h2) peuvent contenir des produits
                text = current.get_text(strip=True)
                if text and len(text) > 3:
                    elements.append(("heading", text))
            elif current.name in ["li", "p", "div"]:
                text = current.get_text(strip=True)
                if text and len(text) > 5:
                    elements.append((current.name, text))
            current = current.find_next()

        # Parser les éléments
        current_product = None
        for elem_type, text in elements:
            if elem_type == "heading":
                # Sous-heading = nom de produit potentiel
                current_product = text
                # Vérifier s'il contient un taux directement
                rate_info = parse_rate(text)
                if rate_info["rate_pct"] is not None or rate_info["rate_specific"] is not None or rate_info["rate_per_unit"] is not None:
                    excise_taxes.append({
                        "product": text,
                        "rate_pct": rate_info["rate_pct"],
                        "rate_specific": rate_info["rate_specific"],
                        "rate_per_unit": rate_info["rate_per_unit"],
                        "raw_text": text,
                    })
                continue

            # Pour <p> : peut contenir plusieurs produits séparés par des points-virgules
            # ou être une description générale
            if ";" in text:
                parts = text.split(";")
            elif "." in text and len(text) > 200:
                parts = text.split(".")
            else:
                parts = [text]

            for part in parts:
                part = part.strip()
                if not part or len(part) < 5:
                    continue

                # Détecter le produit (première partie avant ':')
                product = current_product or (part.split(":")[0].strip() if ":" in part else part[:50])
                product = re.sub(r"^(For|for|Plus|plus|In addition|However|The)\s+", "", product)

                rate_info = parse_rate(part)

                if rate_info["rate_pct"] is not None or rate_info["rate_specific"] is not None or rate_info["rate_per_unit"] is not None:
                    excise_taxes.append({
                        "product": product,
                        "rate_pct": rate_info["rate_pct"],
                        "rate_specific": rate_info["rate_specific"],
                        "rate_per_unit": rate_info["rate_per_unit"],
                        "raw_text": part,
                    })

    # 2. Si aucune accise trouvée, chercher sous 'Law No.' (EGY)
    if not excise_taxes:
        for tag in soup.find_all(["h3"]):
            text = tag.get_text(strip=True)
            if "Law No." in text or "Decree" in text:
                current = tag.find_next()
                while current:
                    if current.name in ["h2", "h3"]:
                        break
                    if current.name in ["h4", "li", "p"]:
                        ct = current.get_text(strip=True)
                        if ct and len(ct) > 10:
                            rate_info = parse_rate(ct)
                            if rate_info["rate_pct"] is not None or rate_info["rate_specific"] is not None or rate_info["rate_per_unit"] is not None:
                                product = ct.split(":")[0].strip() if ":" in ct else ct[:50]
                                excise_taxes.append({
                                    "product": product,
                                    "rate_pct": rate_info["rate_pct"],
                                    "rate_specific": rate_info["rate_specific"],
                                    "rate_per_unit": rate_info["rate_per_unit"],
                                    "raw_text": ct,
                                })
                    current = current.find_next()

    return excise_taxes


def crawl_country(iso3: str, config: Dict) -> Optional[Dict]:
    """Crawl une page pays PwC."""
    slug = config["slug"]
    url = f"https://taxsummaries.pwc.com/{slug}/corporate/other-taxes"
    logger.info(f"Crawling {iso3} ({config['name']}) → {url}")

    html = fetch_page(url)
    if not html:
        logger.warning(f"Failed to fetch {iso3}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    last_reviewed = extract_last_reviewed(soup)
    excise_taxes = extract_excise_taxes(soup)

    result = {
        "country_iso3": iso3,
        "country_name": config["name"],
        "source": "PwC Worldwide Tax Summaries",
        "source_url": url,
        "source_type": "international_cabinet_verified",
        "last_reviewed": last_reviewed,
        "crawled_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "excise_taxes_count": len(excise_taxes),
        "excise_taxes": excise_taxes,
    }

    # Sauvegarder
    output_path = OUTPUT_DIR / f"{iso3}_excise_pwc.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"  {iso3}: {len(excise_taxes)} excise taxes → {output_path.name}")

    return result


def main():
    logger.info("=== PwC Tax Summaries — Excise Taxes Crawler ===")

    results = {}
    for iso3, config in sorted(PWC_COUNTRIES.items()):
        result = crawl_country(iso3, config)
        if result:
            results[iso3] = result
        time.sleep(2)  # politeness delay

    # Résumé
    print(f"\n{'='*80}")
    print(f"PwC EXCISE TAXES — {len(results)} PAYS")
    print(f"{'='*80}")
    print(f"{'Pays':6s} {'Last reviewed':20s} {'Taxes':>6s}  Détail")
    print("-" * 80)
    for iso3, r in sorted(results.items()):
        detail = ", ".join(
            f"{t['product'][:20]}={t['rate_pct'] or t['rate_per_unit'] or t['rate_specific']}"
            for t in r["excise_taxes"][:5]
        )
        print(f"{iso3:6s} {r['last_reviewed']:20s} {r['excise_taxes_count']:6d}  {detail[:60]}")


if __name__ == "__main__":
    main()
