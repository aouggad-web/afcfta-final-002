"""
Tariff doctrine enforcement
===========================
Doctrine tarifaire du projet (README §« Doctrine tarifaire : re-collecte officielle uniquement ») :

- refuser les lignes estimées, synthétiques, générées ou répliquées par chapitre ;
- exiger une `source` et une `source_url` vérifiable pour tout fichier pays servi ;
- signaler explicitement les pays non encore recrawlés au lieu de fabriquer des données ;
- priorité aux sources gouvernementales (douanes nationales) puis aux sources
  officielles intergouvernementales (TEC régionaux, Banque mondiale/WITS-TRAINS).

Ce module est le point de contrôle unique (« gate ») partagé par tous les chemins
de service tarifaire (authentic_tariff_service, tariff_provider_service, routes).
Un fichier pays n'est servable que s'il satisfait :

1. `data_format` ∈ SERVABLE_DATA_FORMATS ;
2. `summary.data_status` ∈ SERVABLE_DATA_STATUSES ;
3. `summary.source_name` ET `summary.source_url` présents (base vérifiable).

Les fichiers `enhanced_v2` sans statut (14 pays : sous-positions 10 chiffres
synthétiques « (type: use) ») sont refusés : ces pays restent servis uniquement
via les données crawlées officielles HS6 (WITS/UNCTAD-TRAINS) s'il en existe.
"""

import json
import logging
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Formats publiés pouvant être servis (les autres sont estimés/synthétiques).
SERVABLE_DATA_FORMATS = {"canonical_v4"}

# Statuts de publication conformes à la doctrine (provenance vérifiable).
SERVABLE_DATA_STATUSES = {"VERIFIED", "PARTIAL", "CRAWLED_AUTHENTIC"}

# Codes pays reconnus par la plateforme (54 membres ZLECAf + ESH).
AFRICAN_ISO3 = {
    "DZA",
    "AGO",
    "BEN",
    "BWA",
    "BFA",
    "BDI",
    "CMR",
    "CPV",
    "CAF",
    "TCD",
    "COM",
    "COG",
    "COD",
    "CIV",
    "DJI",
    "EGY",
    "GNQ",
    "ERI",
    "SWZ",
    "ETH",
    "GAB",
    "GMB",
    "GHA",
    "GIN",
    "GNB",
    "KEN",
    "LSO",
    "LBR",
    "LBY",
    "MDG",
    "MWI",
    "MLI",
    "MRT",
    "MUS",
    "MAR",
    "MOZ",
    "NAM",
    "NER",
    "NGA",
    "RWA",
    "ESH",
    "STP",
    "SEN",
    "SYC",
    "SLE",
    "SOM",
    "ZAF",
    "SSD",
    "SDN",
    "TZA",
    "TGO",
    "TUN",
    "UGA",
    "ZMB",
    "ZWE",
}

COUNTRY_NAMES_FR = {
    "AGO": "l'Angola",
    "COM": "les Comores",
    "DJI": "Djibouti",
    "ERI": "l'Érythrée",
    "LBY": "la Libye",
    "MDG": "Madagascar",
    "MOZ": "le Mozambique",
    "MRT": "la Mauritanie",
    "MWI": "le Malawi",
    "SDN": "le Soudan",
    "SSD": "le Soudan du Sud",
    "STP": "Sao Tomé-et-Principe",
    "SYC": "les Seychelles",
    "ZMB": "la Zambie",
    "ZWE": "le Zimbabwe",
}

COUNTRY_NAMES_EN = {
    "AGO": "Angola",
    "COM": "Comoros",
    "DJI": "Djibouti",
    "ERI": "Eritrea",
    "LBY": "Libya",
    "MDG": "Madagascar",
    "MOZ": "Mozambique",
    "MRT": "Mauritania",
    "MWI": "Malawi",
    "SDN": "Sudan",
    "SSD": "South Sudan",
    "STP": "Sao Tomé and Principe",
    "SYC": "Seychelles",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
}

_doctrine_status_cache: Dict[str, dict] = {}

_ISO_CODE_RE = None


def _validate_iso3(country_iso3: str) -> str:
    global _ISO_CODE_RE
    if _ISO_CODE_RE is None:
        import re

        _ISO_CODE_RE = re.compile(r"^[A-Z]{2,3}$")
    code = (country_iso3 or "").upper().strip()
    if not _ISO_CODE_RE.match(code):
        raise ValueError(f"Invalid country code: {country_iso3!r}")
    return code


def evaluate_country_file(data: dict) -> Tuple[bool, str, str]:
    """
    Évalue la servabilité doctrinale d'un fichier pays déjà chargé.

    Returns:
        (servable, reason_code, detail) — reason_code parmi :
        OK, UNSERVABLE_FORMAT, UNSERVABLE_STATUS, MISSING_SOURCE
    """
    data_format = (data.get("data_format") or "").strip()
    if data_format not in SERVABLE_DATA_FORMATS:
        return (
            False,
            "UNSERVABLE_FORMAT",
            f"data_format={data_format or 'absent'} non conforme (attendu: canonical_v4)",
        )
    summary = data.get("summary") or {}
    status = (summary.get("data_status") or "").strip()
    if status not in SERVABLE_DATA_STATUSES:
        return (
            False,
            "UNSERVABLE_STATUS",
            f"data_status={status or 'absent'} non conforme (attendu: VERIFIED/PARTIAL/CRAWLED_AUTHENTIC)",
        )
    if not (summary.get("source_name") or "").strip():
        return False, "MISSING_SOURCE", "summary.source_name absent"
    if not str(summary.get("source_url") or "").strip():
        return False, "MISSING_SOURCE", "summary.source_url absent"
    return True, "OK", status


def get_country_file_path(country_iso3: str) -> str:
    return os.path.join(DATA_DIR, f"{_validate_iso3(country_iso3)}_tariffs.json")


def get_country_doctrine_status(country_iso3: str) -> dict:
    """
    Statut doctrinal d'un pays, avec message explicite « non encore recrawlé ».

    Returns:
        {"status": "SERVABLE" | "NOT_RECRALLED" | "NO_FILE",
         "reason_code": str, "detail": str,
         "message_fr": str, "message_en": str}
    """
    iso3 = _validate_iso3(country_iso3)
    if iso3 in _doctrine_status_cache:
        return _doctrine_status_cache[iso3]

    result = {"status": "NO_FILE", "reason_code": "NO_FILE", "detail": ""}
    path = get_country_file_path(iso3)
    if not os.path.exists(path):
        result.update(
            {
                "message_fr": (
                    f"Aucune donnée tarifaire publiée pour {COUNTRY_NAMES_FR.get(iso3, iso3)} "
                    f"({iso3}). Conformément à la doctrine tarifaire, aucune donnée estimée "
                    "n'est servie."
                ),
                "message_en": (
                    f"No published tariff data for {COUNTRY_NAMES_EN.get(iso3, iso3)} ({iso3}). "
                    "Per the tariff doctrine, no estimated data is served."
                ),
            }
        )
    else:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:  # fichier illisible => non servable
            result.update(
                {
                    "reason_code": "UNREADABLE_FILE",
                    "detail": str(e),
                    "message_fr": (
                        f"Fichier tarifaire de {COUNTRY_NAMES_FR.get(iso3, iso3)} ({iso3}) "
                        "illisible — refus de service par la doctrine."
                    ),
                    "message_en": (
                        f"Unreadable tariff file for {COUNTRY_NAMES_EN.get(iso3, iso3)} ({iso3}) "
                        "— service refused per doctrine."
                    ),
                }
            )
            _doctrine_status_cache[iso3] = result
            return result

        servable, reason_code, detail = evaluate_country_file(data)
        if servable:
            result = {
                "status": "SERVABLE",
                "reason_code": "OK",
                "detail": detail,
                "message_fr": "",
                "message_en": "",
            }
        else:
            result.update(
                {
                    "status": "NOT_RECRALLED",
                    "reason_code": reason_code,
                    "detail": detail,
                    "message_fr": (
                        f"Les données tarifaires nationales de "
                        f"{COUNTRY_NAMES_FR.get(iso3, iso3)} ({iso3}) n'ont pas encore été "
                        "re-collectées depuis une base officielle vérifiable "
                        f"({detail}). Conformément à la doctrine tarifaire, aucune donnée "
                        "synthétique ou estimée n'est servie. Les données MFN HS6 "
                        "officielles (WITS/UNCTAD-TRAINS), lorsqu'elles existent, restent "
                        "disponibles via le moteur de calcul."
                    ),
                    "message_en": (
                        f"National tariff data for {COUNTRY_NAMES_EN.get(iso3, iso3)} ({iso3}) "
                        "has not yet been re-collected from a verifiable official source "
                        f"({detail}). Per the tariff doctrine, no synthetic or estimated data "
                        "is served. Official HS6 MFN data (WITS/UNCTAD-TRAINS), when "
                        "available, remains accessible via the calculation engine."
                    ),
                }
            )

    _doctrine_status_cache[iso3] = result
    return result


def clear_doctrine_cache() -> None:
    """Invalide le cache de statut (utile après re-crawl / tests)."""
    _doctrine_status_cache.clear()


def is_country_servable(country_iso3: str) -> bool:
    return get_country_doctrine_status(country_iso3).get("status") == "SERVABLE"


def not_recrawled_http_detail(country_iso3: str) -> dict:
    """
    Charge utile d'erreur HTTP explicite pour un pays non recrawlé
    (utilisée par les routes tarifaires).
    """
    status = get_country_doctrine_status(country_iso3)
    return {
        "error": "COUNTRY_NOT_RECRALLED",
        "country_iso3": _validate_iso3(country_iso3),
        "doctrine_status": status.get("status"),
        "reason_code": status.get("reason_code"),
        "message_fr": status.get("message_fr"),
        "message_en": status.get("message_en"),
    }


def list_servable_countries() -> list:
    """Liste les ISO3 des fichiers pays conformes à la doctrine (pour diagnostics)."""
    servable = []
    try:
        for fname in sorted(os.listdir(DATA_DIR)):
            if not fname.endswith("_tariffs.json") or fname.startswith("."):
                continue
            iso3 = fname.replace("_tariffs.json", "").upper()
            if get_country_doctrine_status(iso3).get("status") == "SERVABLE":
                servable.append(iso3)
    except OSError as e:
        logger.error(f"Error listing data dir: {e}")
    return servable


def provider_fee_flags(tax: dict) -> dict:
    """
    Marque les taxes/redevances correspondant à des frais de prestataires
    (ex. redevances de prestations douanières, frais de dossier) afin de les
    rendre explicites quand ils sont présents.

    Returns:
        {"is_provider_fee": bool, "fee_label_fr": str}
    """
    code = str(tax.get("code") or "").upper()
    name = str(tax.get("name") or "").upper()
    is_fee = any(
        marker in code or marker in name
        for marker in ("RPD", "PREST", "REDEV", "FRAIS DE DOSSIER", "RED.")
    )
    return {
        "is_provider_fee": is_fee,
        "fee_label_fr": (
            "Frais de prestataire (redevance de prestation douanière)" if is_fee else ""
        ),
    }


def get_optional(name: str, default: Optional[dict] = None):
    return globals().get(name, default)
