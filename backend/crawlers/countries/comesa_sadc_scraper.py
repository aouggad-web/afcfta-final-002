"""
Scrapers COMESA/SADC — 11 pays ratifiants ZLECAf sans données actuelles
========================================================================

Pays couverts : AGO, COM, DJI, ERI, MDG, MOZ, MRT, MWI, STP, ZMB, ZWE

Sources officielles ciblées (portails réels — accès réseau requis) :

  AGO  Angola          SGA Alfândegas       https://www.sga.gov.ao/
  COM  Comores         AGID Douanes         https://www.douanes.km/
  DJI  Djibouti        Direction Douanes    https://www.douanesdj.gouv.dj/
  ERI  Érythrée        Ministry of Finance  https://www.mof.gov.er/ (accès limité)
  MDG  Madagascar      Douanes Madagascar   https://www.douanes.mg/
  MOZ  Mozambique      AT Moçambique        https://www.at.gov.mz/
  MRT  Mauritanie      DGD Mauritanie       https://www.douanesmauritanie.gov.mr/
  MWI  Malawi          MRA                  https://www.mra.mw/
  STP  São Tomé        Direcção Alfândegas  https://www.alfandegas.st/
  ZMB  Zambie          ZRA                  https://www.zra.org.zm/
  ZWE  Zimbabwe        ZIMRA                https://www.zimra.co.zw/

Exécution :
  python comesa_sadc_scraper.py AGO       # un seul pays
  python comesa_sadc_scraper.py ALL       # tous
  python comesa_sadc_scraper.py ZMB ZWE   # liste

Statut de sortie attendu : PARTIAL/B si portail répond, PENDING sinon.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# HTTP optionnel
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "crawled"

# ---------------------------------------------------------------------------
# Configuration par pays
# ---------------------------------------------------------------------------

COUNTRY_CONFIGS: dict[str, dict] = {

    # ---------------------------------------------------------------- AGO --
    "AGO": {
        "country_code": "AGO",
        "country_name": "Angola",
        "source": "SGA Alfândegas de Angola",
        "source_url": "https://www.sga.gov.ao/tarifa/pesquisa",
        "method": "api_json",          # API JSON SGA
        "endpoint": "https://www.sga.gov.ao/tarifa/api/positions",
        "params": {"format": "json", "version": "2023"},
        "auth": None,
        "fallback": "sadc_schedule",   # Si API indisponible: utiliser SADC Schedule
        "tax_structure": {
            "DD": ("Direito Aduaneiro", "CIF"),
            "IVA": ("Imposto sobre o Valor Acrescentado", "CIF+DD"),
            "IE":  ("Imposto de Exportação", "FOB"),
        },
        "vat_rate": 14.0,
        "notes": "Angola applique l'IVA 14%. Accord de Luanda 2021.",
    },

    # ---------------------------------------------------------------- COM --
    "COM": {
        "country_code": "COM",
        "country_name": "Comores",
        "source": "Agence Nationale des Douanes des Comores (AGID)",
        "source_url": "https://www.douanes.km/",
        "method": "html_scrape",
        "endpoint": "https://www.douanes.km/tarif-douanier/recherche",
        "params": {},
        "auth": None,
        "tax_structure": {
            "DD":  ("Droit de Douane", "CIF"),
            "TPS": ("Taxe sur les Prestations de Services", "CIF"),
            "TVA": ("Taxe sur la Valeur Ajoutée", "CIF+DD"),
        },
        "vat_rate": 10.0,
        "notes": "Comores — TVA 10%. Membre COMESA. Régime insulaire avec exonérations.",
    },

    # ---------------------------------------------------------------- DJI --
    "DJI": {
        "country_code": "DJI",
        "country_name": "Djibouti",
        "source": "Direction Générale des Douanes — Djibouti",
        "source_url": "https://www.douanesdj.gouv.dj/tarif/",
        "method": "html_scrape",
        "endpoint": "https://www.douanesdj.gouv.dj/tarif/recherche.php",
        "params": {"lang": "fr"},
        "auth": None,
        "tax_structure": {
            "DD":  ("Droit de Douane", "CIF"),
            "TIC": ("Taxe Intérieure de Consommation", "CIF"),
        },
        "vat_rate": None,   # Djibouti n'a pas de TVA générale
        "notes": "Djibouti zone franche — pas de TVA générale. DD 0-33%. Membre COMESA+IGAD.",
    },

    # ---------------------------------------------------------------- ERI --
    "ERI": {
        "country_code": "ERI",
        "country_name": "Érythrée",
        "source": "Ministry of Finance — Eritrea",
        "source_url": "https://www.mof.gov.er/",
        "method": "pending",           # Portail très limité, données à obtenir via OMC
        "endpoint": None,
        "params": {},
        "auth": None,
        "tax_structure": {
            "CD":  ("Customs Duty", "CIF"),
            "ST":  ("Sales Tax", "CIF+CD"),
        },
        "vat_rate": None,   # Sales Tax à taux variable
        "notes": "Accès web très limité. Données à obtenir via OMC/ITC MacMap.",
    },

    # ---------------------------------------------------------------- MDG --
    "MDG": {
        "country_code": "MDG",
        "country_name": "Madagascar",
        "source": "Douanes Madagascar — DGD",
        "source_url": "https://www.douanes.mg/tarif/",
        "method": "html_scrape",
        "endpoint": "https://www.douanes.mg/tarif/recherche",
        "params": {"format": "json"},
        "auth": None,
        "tax_structure": {
            "DD":   ("Droit de Douane", "CIF"),
            "RS":   ("Redevance Statistique", "CIF"),
            "TVA":  ("Taxe sur la Valeur Ajoutée", "CIF+DD+RS"),
        },
        "vat_rate": 20.0,
        "notes": "Madagascar — TVA 20%. Membre COMESA + SADC. Bandes DD 0/5/10/20%.",
    },

    # ---------------------------------------------------------------- MOZ --
    "MOZ": {
        "country_code": "MOZ",
        "country_name": "Mozambique",
        "source": "Autoridade Tributária de Moçambique (AT)",
        "source_url": "https://www.at.gov.mz/index.php/aduanas/pauta-aduaneira",
        "method": "pdf_download",
        "endpoint": "https://www.at.gov.mz/index.php/aduanas/pauta-aduaneira/pauta-2025",
        "params": {},
        "auth": None,
        "tax_structure": {
            "DD":  ("Direito Aduaneiro", "CIF"),
            "IVA": ("Imposto sobre o Valor Acrescentado", "CIF+DD"),
            "IS":  ("Imposto de Sisa (sélectif)", "CIF"),
        },
        "vat_rate": 17.0,
        "notes": "Mozambique — IVA 17%. Membre SADC. Bandes 0/2.5/5/7.5/20/25%.",
    },

    # ---------------------------------------------------------------- MRT --
    "MRT": {
        "country_code": "MRT",
        "country_name": "Mauritanie",
        "source": "Direction Générale des Douanes — Mauritanie",
        "source_url": "https://www.douanesmauritanie.gov.mr/tarif/",
        "method": "html_scrape",
        "endpoint": "https://www.douanesmauritanie.gov.mr/tarif/search",
        "params": {},
        "auth": None,
        "tax_structure": {
            "DD":  ("Droit de Douane", "CIF"),
            "TVA": ("Taxe sur la Valeur Ajoutée", "CIF+DD"),
            "IBS": ("Impôt sur les Bénéfices des Sociétés à l'import (si applicable)", "CIF"),
        },
        "vat_rate": 16.0,
        "notes": "Mauritanie — TVA 16%. Ancienne membre CEDEAO (sortie 2000). Membre UMA. Bandes DD 0/5/13/20%.",
    },

    # ---------------------------------------------------------------- MWI --
    "MWI": {
        "country_code": "MWI",
        "country_name": "Malawi",
        "source": "Malawi Revenue Authority (MRA)",
        "source_url": "https://www.mra.mw/customs-excise/tariff",
        "method": "api_json",
        "endpoint": "https://www.mra.mw/api/tariff/search",
        "params": {"year": "2025", "format": "json"},
        "auth": None,
        "tax_structure": {
            "CD":   ("Customs Duty", "CIF"),
            "VAT":  ("Value Added Tax", "CIF+CD"),
            "EXCISE": ("Excise Duty", "CIF"),
        },
        "vat_rate": 16.5,
        "notes": "Malawi — VAT 16.5%. Membre COMESA + SADC. Bandes 0/5/10/15/25%.",
    },

    # ---------------------------------------------------------------- STP --
    "STP": {
        "country_code": "STP",
        "country_name": "São Tomé-et-Príncipe",
        "source": "Direcção das Alfândegas — São Tomé-et-Príncipe",
        "source_url": "https://www.alfandegas.st/",
        "method": "pending",
        "endpoint": None,
        "params": {},
        "auth": None,
        "tax_structure": {
            "DP":  ("Direito de Pauta (Droit de Douane)", "CIF"),
            "IVA": ("Imposto sobre o Valor Acrescentado", "CIF+DP"),
        },
        "vat_rate": 15.0,
        "notes": "STP — IVA 15%. Membre CEEAC (CEMAC étendu). Petit État insulaire — données limitées.",
    },

    # ---------------------------------------------------------------- ZMB --
    "ZMB": {
        "country_code": "ZMB",
        "country_name": "Zambie",
        "source": "Zambia Revenue Authority (ZRA)",
        "source_url": "https://www.zra.org.zm/customs/trade-tariff",
        "method": "api_json",
        "endpoint": "https://www.zra.org.zm/api/tariff",
        "params": {"year": "2025", "lang": "en"},
        "auth": None,
        "tax_structure": {
            "CD":  ("Customs Duty", "CIF"),
            "VAT": ("Value Added Tax", "CIF+CD"),
            "EXC": ("Excise Duty", "CIF"),
            "IDL": ("Import Declaration Fee", "CIF"),
        },
        "vat_rate": 16.0,
        "notes": "Zambie — VAT 16%. Membre COMESA + SADC. Bandes 0/5/15/25%. IDF 0.5% CIF.",
    },

    # ---------------------------------------------------------------- ZWE --
    "ZWE": {
        "country_code": "ZWE",
        "country_name": "Zimbabwe",
        "source": "Zimbabwe Revenue Authority (ZIMRA)",
        "source_url": "https://www.zimra.co.zw/customs/tariff-schedule",
        "method": "html_scrape",
        "endpoint": "https://www.zimra.co.zw/customs/tariff-schedule/download",
        "params": {"year": "2025", "format": "excel"},
        "auth": None,
        "tax_structure": {
            "CD":   ("Customs Duty", "CIF"),
            "VAT":  ("Value Added Tax", "CIF+CD"),
            "SURTAX": ("Surcharge Tax", "CIF"),
        },
        "vat_rate": 15.0,
        "notes": "Zimbabwe — VAT 15%. Membre COMESA + SADC. Bandes 0/5/10/15/20/25/40%.",
    },
}


# ---------------------------------------------------------------------------
# Utilitaires de scraping
# ---------------------------------------------------------------------------

def _fetch_json(url: str, params: dict, timeout: int = 30) -> Optional[dict]:
    if not _HAS_REQUESTS:
        logger.error("Module 'requests' non disponible — pip install requests")
        return None
    try:
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0 ZLECAf-Tariff-Research"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"GET {url}: {e}")
        return None


def _fetch_html(url: str, params: dict, timeout: int = 30) -> Optional[str]:
    if not _HAS_REQUESTS:
        logger.error("Module 'requests' non disponible — pip install requests")
        return None
    try:
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0 ZLECAf-Tariff-Research"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.error(f"GET {url}: {e}")
        return None


def _build_stub(country: str, config: dict, error: str) -> dict:
    """Génère un fichier stub PENDING si le portail n'est pas accessible."""
    return {
        "country_code": country,
        "country_name": config["country_name"],
        "source": config["source"],
        "source_url": config["source_url"],
        "data_status": "PENDING",
        "data_quality": "PARTIAL/B — non encore crawlé",
        "error": error,
        "crawl_attempted": datetime.utcnow().isoformat(),
        "notes": config.get("notes", ""),
        "positions": [],
        "pending_action": (
            f"Crawler le portail {config['source_url']} pour obtenir les taux réels. "
            f"Méthode prévue : {config['method']}. "
            "Ne pas utiliser de données générées par IA/template."
        ),
    }


def scrape_country(country: str) -> Optional[dict]:
    """
    Tente de scraper le portail officiel du pays.
    Retourne None si non accessible (stub enregistré à la place).
    """
    config = COUNTRY_CONFIGS.get(country)
    if not config:
        logger.error(f"Pas de configuration pour {country}")
        return None

    logger.info(f"[{country}] Tentative de scraping — {config['source_url']}")
    method = config["method"]

    if method == "pending":
        logger.warning(f"[{country}] Méthode PENDING — portail non encore implémenté")
        return None

    if method == "api_json":
        data = _fetch_json(config["endpoint"] or config["source_url"], config["params"])
        if data and isinstance(data, (dict, list)):
            logger.info(f"[{country}] API JSON accessible")
            return data
        logger.warning(f"[{country}] API JSON inaccessible")
        return None

    if method == "html_scrape":
        html = _fetch_html(config["endpoint"] or config["source_url"], config["params"])
        if html:
            logger.info(f"[{country}] HTML accessible ({len(html)} chars)")
            # Parsing spécifique à implémenter par pays
            logger.warning(f"[{country}] Parser HTML non encore implémenté — stub créé")
        return None

    if method == "pdf_download":
        logger.warning(f"[{country}] PDF download non encore implémenté — stub créé")
        return None

    return None


def run_scraper(countries: Optional[list[str]] = None,
                output_dir: Optional[Path] = None) -> dict[str, str]:
    """
    Lance le scraping pour la liste de pays donnée (ou tous si None).
    Retourne un dict {iso3: "OK"|"PENDING"|"ERROR"}.
    """
    if countries is None:
        countries = list(COUNTRY_CONFIGS.keys())

    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}

    for country in countries:
        config = COUNTRY_CONFIGS.get(country)
        if not config:
            results[country] = "UNKNOWN"
            continue

        out_file = out_dir / f"{country}_tariffs.json"

        # Si fichier déjà présent et non-stub, ne pas écraser
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text(encoding="utf-8"))
                if existing.get("positions") and len(existing["positions"]) > 100:
                    logger.info(f"[{country}] Fichier existant valide — skip")
                    results[country] = "EXISTS"
                    continue
            except Exception:
                pass

        raw = scrape_country(country)

        if raw is None:
            # Écrire un stub PENDING
            stub = _build_stub(country, config,
                                f"Portail {config['source_url']} non accessible ou méthode non implémentée")
            out_file.write_text(json.dumps(stub, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.warning(f"[{country}] → PENDING (stub écrit)")
            results[country] = "PENDING"
        else:
            # Enrichir avec les métadonnées de provenance
            if isinstance(raw, list):
                raw = {"positions": raw}
            raw.update({
                "country_code": country,
                "country_name": config["country_name"],
                "source": config["source"],
                "source_url": config["source_url"],
                "crawled_at": datetime.utcnow().isoformat(),
                "data_status": "PARTIAL",
            })
            out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"[{country}] → OK")
            results[country] = "OK"

        time.sleep(1)  # Politesse envers les portails

    return results


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "ALL":
        targets = list(COUNTRY_CONFIGS.keys())
    else:
        targets = [a.upper() for a in args]

    print(f"\n{'='*60}")
    print(f"  Scrapers COMESA/SADC/autres — {len(targets)} pays")
    print(f"  Portails officiels réels — accès réseau requis")
    print(f"{'='*60}\n")

    results = run_scraper(targets)

    print(f"\n{'='*60}")
    for country, status in sorted(results.items()):
        flag = "✓" if status == "OK" else ("⏳" if status == "PENDING" else "✗")
        print(f"  {flag} {country}: {status}")
    ok = sum(1 for s in results.values() if s == "OK")
    pending = sum(1 for s in results.values() if s == "PENDING")
    print(f"\n  OK: {ok} | PENDING: {pending} | Total: {len(results)}\n")
