#!/usr/bin/env python3
"""
Crawler pour le tarif douanier Mozambique (JUE — Janela Única Eletrónica).
Source : https://jue.mcnet.co.mz/mcnet/portal/homepage
API : /mcnet/api/v1/heading → /mcnet/api/v1/subheading → /mcnet/api/v1/hscode

L'API retourne les taxes par sous-position 8-digit avec :
  - Droits Aduaneiros (DD)
  - TaxType (DIREITOS, TVA, etc.)
  - Rate (ad valorem ou spécifique)
  - Dates de validité
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Vérification TLS active (défaut httpx). Elle portait `verify=False` :
# le collecteur acceptait n'importe quel certificat, et un tiers sur le
# chemin pouvait donc lui dicter les taux qu'il liquide. Si la chaîne d'un
# portail se révèle incomplète en production, la réponse est de fournir
# l'intermédiaire manquant — jamais de redésactiver la vérification.

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE = "https://jue.mcnet.co.mz"
BASE_IP = "https://196.11.135.134"
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "crawled"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": f"{BASE}/mcnet/portal/homepage",
    "Host": "jue.mcnet.co.mz",
}

CONCURRENCY = 5


def fetch_json(url: str, params: dict = None, retries: int = 3) -> Optional[dict]:
    # Utiliser l'IP directe avec Host header pour contourner les problèmes DNS
    ip_url = url.replace(BASE, BASE_IP)
    for attempt in range(retries):
        try:
            r = httpx.get(ip_url, params=params, timeout=20, headers=HEADERS)
            if r.status_code == 200:
                return r.json()
            logger.warning(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            logger.warning(f"Error (attempt {attempt+1}) {url}: {e}")
        # Fallback: réessayer avec le nom DNS
        try:
            r = httpx.get(url, params=params, timeout=20, headers=HEADERS)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(2)
    return None


async def fetch_json_async(
    client: httpx.AsyncClient, url: str, params: dict = None
) -> Optional[dict]:
    ip_url = url.replace(BASE, BASE_IP)
    try:
        r = await client.get(ip_url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    # Fallback DNS
    try:
        r = await client.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logger.warning(f"Async error {url}: {e}")
    return None


def crawl_mozambique() -> List[Dict]:
    """Crawl complet du tarif Mozambique via l'API JUE (async, concurrent)."""
    positions = []

    async def _crawl():
        sem = asyncio.Semaphore(CONCURRENCY)
        async with httpx.AsyncClient(headers=HEADERS) as client:
            # 1. Récupérer tous les subheadings par heading (01-97)
            all_subheadings = []
            for i in range(1, 98):
                heading_id = f"{i:02d}"
                sub_data = await fetch_json_async(
                    client, f"{BASE}/mcnet/api/v1/subheading", {"headingId": heading_id}
                )
                if sub_data and sub_data.get("listObj"):
                    all_subheadings.extend(sub_data["listObj"])
                if i % 20 == 0:
                    logger.info(f"Subheadings: {len(all_subheadings)} so far (heading {i})")

            logger.info(f"Total subheadings: {len(all_subheadings)}")

            # 2. Pour chaque subheading, récupérer les hscodes en parallèle
            async def _fetch_one(sub):
                async with sem:
                    sub_id = sub.get("subHeadingId", sub.get("id", ""))
                    hs_data = await fetch_json_async(
                        client, f"{BASE}/mcnet/api/v1/hscode", {"subHeadingId": sub_id}
                    )
                    return hs_data

            # Traiter par lots pour éviter trop de tâches en vol
            batch_size = CONCURRENCY * 4
            for j in range(0, len(all_subheadings), batch_size):
                batch = all_subheadings[j : j + batch_size]
                results = await asyncio.gather(*(_fetch_one(s) for s in batch))

                for hs_data in results:
                    if not hs_data:
                        continue
                    hs_list = hs_data.get("listObj", [])
                    for hs in hs_list:
                        pos = _parse_hs(hs)
                        if pos:
                            positions.append(pos)

                if (j + batch_size) % 200 < batch_size:
                    logger.info(
                        f"  {len(positions)} positions so far ({j+batch_size}/{len(all_subheadings)} subheadings)"
                    )

        return positions

    positions = asyncio.run(_crawl())
    return positions


def _parse_hs(hs: dict) -> Optional[dict]:
    """Parse une position HS depuis l'API JUE."""
    code = hs.get("code", "")
    if not code or len(code) < 6:
        return None

    code_clean = code.replace(".", "").replace(" ", "")
    hs6 = code_clean[:6]
    chapter = code_clean[:2]

    desc = hs.get("descriptionEng", hs.get("descriptionOth", ""))

    taxes = []
    for rate in hs.get("hsCodeRate", []):
        tax_type = rate.get("hsCodeTaxType", {})
        tax_code = tax_type.get("code", rate.get("taxCode", ""))
        tax_name = tax_type.get("nameEng", tax_type.get("nameOth", tax_code))

        canonical = tax_code
        if "DIREITOS" in tax_code.upper() or "CUSTOMS" in tax_name.upper():
            canonical = "DD"
        elif "VAT" in tax_code.upper() or "TVA" in tax_code.upper() or "VALUE" in tax_name.upper():
            canonical = "TVA"
        elif (
            "EXCISE" in tax_code.upper()
            or "ACCISE" in tax_name.upper()
            or "CONSUMO" in tax_code.upper()
        ):
            canonical = "DA"

        ad_valorem = rate.get("adValoremRate", 0)
        specific = rate.get("specificRateAmount")
        rate_str = rate.get("rate", "")

        taxes.append(
            {
                "code": canonical,
                "name": tax_name,
                "name_fr": "",
                "name_en": tax_name,
                "name_ar": "",
                "rate_pct": float(ad_valorem) if ad_valorem else None,
                "rate_decimal": float(ad_valorem) / 100 if ad_valorem else None,
                "raw_value": rate_str,
                "specific_value": (
                    f"{specific} {rate.get('specificRateCurrency', '')}" if specific else None
                ),
                "base": "CIF",
                "source": "jue.mcnet.co.mz (Alfândegas Moçambique)",
                "legal_ref": None,
                "original_code": tax_code,
                "is_customs_duty": canonical == "DD",
                "is_vat": canonical == "TVA",
                "is_excise": canonical == "DA",
            }
        )

    return {
        "national_code": code_clean,
        "hs6": hs6,
        "chapter": chapter,
        "heading": code_clean[:4] + "." + code_clean[4:6],
        "section": "",
        "statistical_unit": hs.get("uomId", ""),
        "check_digit": "",
        "designation": {
            "fr": "",
            "en": desc,
            "ar": "",
            "full_fr": "",
            "verbatim": "",
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
        "zlecaf_schedule": {"applied": False, "rate_pct": None, "instruction": None},
        "source_gaps": [],
        "lf_provisions": None,
        "data_status": "crawled_authentic",
        "source_quality": "crawled_authentic",
        "source": "jue.mcnet.co.mz (Alfândegas Moçambique)",
        "source_url": f"{BASE}/mcnet/portal/homepage",
        "raw_data": {k: v for k, v in hs.items() if k not in ("hsCodeRate", "hsCodeSc")},
    }


def save(positions: List[Dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_tax_codes = set()
    for p in positions:
        for t in p.get("taxes", []):
            all_tax_codes.add(t.get("code", ""))

    result = {
        "country": "MOZ",
        "country_name": "Moçambique",
        "source": "jue.mcnet.co.mz (Alfândegas Moçambique — JUE)",
        "source_url": f"{BASE}/mcnet/portal/homepage",
        "source_quality": "crawled_authentic",
        "extracted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "stats": {
            "total_positions": len(positions),
            "unique_tax_codes": sorted(all_tax_codes),
            "chapters_covered": len(set(p["chapter"] for p in positions)),
        },
        "sub_positions": positions,
    }

    output = DATA_DIR / "MOZ_tariffs.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(positions)} positions to {output}")


def main():
    logger.info("=== Mozambique Tariff Scraper (JUE API) ===")
    positions = crawl_mozambique()
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
        print(f"Sample: {positions[0]['national_code']} {positions[0]['designation']['en'][:40]}")


if __name__ == "__main__":
    main()
