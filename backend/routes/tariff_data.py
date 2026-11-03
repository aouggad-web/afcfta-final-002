import json
import logging
import os

from entitlement_guard import require_module
from fastapi import APIRouter, Depends
from services.tariff_data_collector import get_collector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tariff-data", tags=["Tariff Data Collection"])

# The router as a whole is gated on the tier on/off switch only (see
# routes/__init__.py, require_module_enabled("tools")) — most endpoints here
# just read the export manifest or the in-memory collector cache. The summary
# endpoint below is the exception: on a cache miss it calls
# collector.collect_country_tariffs() (recomputes every HS6 line for the
# country from the loaded tariff modules) and persists it via
# save_country_tariffs() — expensive and a disk write, unlike the rest of
# this router. It keeps the metered require_module("tools") in addition to
# the router-level gate, so a Starter caller can't bypass its 10/day tools
# cap by hitting it. Tariff lines and tariff files are no longer served at
# all (no download for any plan, product decision of 2026-11-03).
_tools_metered = [Depends(require_module("tools"))]

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exports")


@router.get("/countries")
async def list_collected_countries():
    collector = get_collector()
    available = collector.get_available_countries()
    return {
        "collected_countries": available,
        "count": len(available),
    }


@router.get("/monitoring/stats")
async def get_monitoring_stats():
    collector = get_collector()
    available = collector.get_available_countries()
    stats = {
        "countries": [],
        "total_tariff_lines": 0,
        "total_sub_positions": 0,
        "total_positions": 0,
    }
    for cc in sorted(available):
        data = collector.load_country_tariffs(cc)
        if data:
            summary = data.get("summary", {})
            tl = summary.get("total_tariff_lines", 0)
            sp = summary.get("total_sub_positions", 0)
            tp = summary.get("total_positions", tl + sp)
            stats["countries"].append(
                {
                    "code": cc,
                    "tariff_lines": tl,
                    "sub_positions": sp,
                    "total_positions": tp,
                    "lines_with_sub_positions": summary.get("lines_with_sub_positions", 0),
                    "vat_rate": summary.get("vat_rate_pct", 0),
                    "dd_avg": summary.get("dd_rate_range", {}).get("avg", 0),
                    "chapters": summary.get("chapters_covered", 0),
                    "generated_at": data.get("generated_at", ""),
                }
            )
            stats["total_tariff_lines"] += tl
            stats["total_sub_positions"] += sp
            stats["total_positions"] += tp
    stats["country_count"] = len(stats["countries"])
    return stats


@router.get("/{country_code}/summary", dependencies=_tools_metered)
async def get_country_tariff_summary(country_code: str):
    collector = get_collector()
    data = collector.load_country_tariffs(country_code.upper())

    if not data:
        data = collector.collect_country_tariffs(country_code.upper())
        collector.save_country_tariffs(country_code.upper(), data)

    chapters = {}
    for line in data.get("tariff_lines", []):
        ch = line["chapter"]
        if ch not in chapters:
            chapters[ch] = {"count": 0, "dd_rates": [], "descriptions": []}
        chapters[ch]["count"] += 1
        chapters[ch]["dd_rates"].append(line["dd_rate"])
        if len(chapters[ch]["descriptions"]) < 3:
            chapters[ch]["descriptions"].append(line.get("description_fr", ""))

    chapter_summary = {}
    for ch, info in sorted(chapters.items()):
        rates = info["dd_rates"]
        chapter_summary[ch] = {
            "tariff_lines": info["count"],
            "dd_min": min(rates),
            "dd_max": max(rates),
            "dd_avg": round(sum(rates) / len(rates), 2),
            "sample_products": info["descriptions"],
        }

    return {
        "country_code": data["country_code"],
        "generated_at": data["generated_at"],
        "summary": data["summary"],
        "by_chapter": chapter_summary,
    }


COUNTRY_NAMES = {
    "DZA": "Algerie",
    "EGY": "Egypte",
    "LBY": "Libye",
    "MAR": "Maroc",
    "TUN": "Tunisie",
    "SDN": "Soudan",
    "MRT": "Mauritanie",
    "BEN": "Benin",
    "BFA": "Burkina_Faso",
    "CPV": "Cap_Vert",
    "CIV": "Cote_Ivoire",
    "GMB": "Gambie",
    "GHA": "Ghana",
    "GIN": "Guinee",
    "GNB": "Guinee_Bissau",
    "LBR": "Liberia",
    "MLI": "Mali",
    "NER": "Niger",
    "NGA": "Nigeria",
    "SEN": "Senegal",
    "SLE": "Sierra_Leone",
    "TGO": "Togo",
    "CMR": "Cameroun",
    "CAF": "Centrafrique",
    "TCD": "Tchad",
    "COG": "Congo",
    "GAB": "Gabon",
    "GNQ": "Guinee_Equatoriale",
    "COD": "RD_Congo",
    "STP": "Sao_Tome",
    "KEN": "Kenya",
    "TZA": "Tanzanie",
    "UGA": "Ouganda",
    "RWA": "Rwanda",
    "BDI": "Burundi",
    "SSD": "Soudan_Sud",
    "ZAF": "Afrique_Sud",
    "BWA": "Botswana",
    "NAM": "Namibie",
    "LSO": "Lesotho",
    "SWZ": "Eswatini",
    "MWI": "Malawi",
    "ZMB": "Zambie",
    "ZWE": "Zimbabwe",
    "MOZ": "Mozambique",
    "AGO": "Angola",
    "MDG": "Madagascar",
    "MUS": "Maurice",
    "COM": "Comores",
    "SYC": "Seychelles",
    "ETH": "Ethiopie",
    "ERI": "Erythree",
    "DJI": "Djibouti",
    "SOM": "Somalie",
}

REGIONS = {
    "afrique_nord": {
        "name": "Afrique du Nord / UMA",
        "countries": ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"],
    },
    "cedeao": {
        "name": "CEDEAO / ECOWAS",
        "countries": [
            "BEN",
            "BFA",
            "CPV",
            "CIV",
            "GMB",
            "GHA",
            "GIN",
            "GNB",
            "LBR",
            "MLI",
            "NER",
            "NGA",
            "SEN",
            "SLE",
            "TGO",
        ],
    },
    "cemac": {
        "name": "CEMAC + RDC + STP",
        "countries": ["CMR", "CAF", "TCD", "COG", "GAB", "GNQ", "COD", "STP"],
    },
    "eac": {"name": "EAC", "countries": ["KEN", "TZA", "UGA", "RWA", "BDI", "SSD"]},
    "sadc": {
        "name": "SADC / SACU",
        "countries": [
            "ZAF",
            "BWA",
            "NAM",
            "LSO",
            "SWZ",
            "MWI",
            "ZMB",
            "ZWE",
            "MOZ",
            "AGO",
            "MDG",
            "MUS",
            "COM",
            "SYC",
        ],
    },
    "igad": {"name": "IGAD / Corne de l'Afrique", "countries": ["ETH", "ERI", "DJI", "SOM"]},
}


# Le nombre de positions de chaque pays est lu sur le manifeste de l'export
# du socle de calcul (scripts/exporter_tarifs_socle.py), archivé dans le
# dépôt. Les fichiers eux-mêmes ne sont plus servis.
SOCLE_EXPORTS_DIR = os.path.join(EXPORTS_DIR, "socle")


def _exports_socle():
    path = os.path.join(SOCLE_EXPORTS_DIR, "MANIFESTE.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("pays", {})


@router.get("/download/list")
async def list_downloads():
    # Aucun téléchargement de tarif n'est proposé, quelle que soit la formule
    # (décision du responsable produit, 03/11/2026) : la liste ne donne que le
    # nombre de positions tarifaires nationales de chaque pays.
    countries = []
    for cc, entree in _exports_socle().items():
        country = {
            "code": cc,
            "name": COUNTRY_NAMES.get(cc, cc),
            "positions": entree["positions"],
            "collecte": entree.get("collecte"),
            "devise": entree.get("devise"),
        }
        countries.append(country)
    return {
        "countries": countries,
        "count": len(countries),
        "regions": {k: v for k, v in REGIONS.items()},
    }
