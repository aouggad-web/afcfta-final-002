from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional, List
from pydantic import BaseModel
import logging
import os
import csv
import json
import io

from services.tariff_data_collector import get_collector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tariff-data", tags=["Tariff Data Collection"])

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exports")
TARIFFS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tariffs")


class CollectRequest(BaseModel):
    country_codes: Optional[List[str]] = None
    all_countries: bool = False


@router.post("/collect")
async def collect_tariff_data(request: CollectRequest):
    collector = get_collector()

    if request.all_countries:
        result = await collector.collect_all_countries()
    elif request.country_codes:
        result = await collector.collect_all_countries(country_codes=request.country_codes)
    else:
        raise HTTPException(status_code=400, detail="Provide country_codes or set all_countries=true")

    return result


@router.post("/collect/{country_code}")
async def collect_single_country(country_code: str):
    collector = get_collector()
    try:
        result = await collector.collect_and_save_country(country_code.upper())
        return result
    except Exception as e:
        logger.error(f"Error collecting tariff data for {country_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/countries")
async def list_collected_countries():
    collector = get_collector()
    available = collector.get_available_countries()
    return {
        "collected_countries": available,
        "count": len(available),
    }


@router.get("/{country_code}")
async def get_country_tariff_data(
    country_code: str,
    chapter: Optional[str] = Query(None, description="Filter by HS chapter (2 digits)"),
    hs6: Optional[str] = Query(None, description="Get specific HS6 code"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
):
    collector = get_collector()
    data = collector.load_country_tariffs(country_code.upper())

    if not data:
        data = collector.collect_country_tariffs(country_code.upper())
        collector.save_country_tariffs(country_code.upper(), data)

    tariff_lines = data.get("tariff_lines", [])

    if hs6:
        tariff_lines = [l for l in tariff_lines if l["hs6"] == hs6.zfill(6)]
        return {
            "country_code": data["country_code"],
            "generated_at": data["generated_at"],
            "results": tariff_lines,
            "count": len(tariff_lines),
        }

    if chapter:
        chapter = chapter.zfill(2)
        tariff_lines = [l for l in tariff_lines if l["chapter"] == chapter]

    total = len(tariff_lines)
    start = (page - 1) * page_size
    end = start + page_size
    page_lines = tariff_lines[start:end]

    return {
        "country_code": data["country_code"],
        "generated_at": data["generated_at"],
        "summary": data["summary"],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "tariff_lines": page_lines,
    }


@router.get("/monitoring/stats")
async def get_monitoring_stats():
    collector = get_collector()
    available = collector.get_available_countries()
    stats = {"countries": [], "total_tariff_lines": 0, "total_sub_positions": 0, "total_positions": 0}
    for cc in sorted(available):
        data = collector.load_country_tariffs(cc)
        if data:
            summary = data.get("summary", {})
            tl = summary.get("total_tariff_lines", 0)
            sp = summary.get("total_sub_positions", 0)
            tp = summary.get("total_positions", tl + sp)
            stats["countries"].append({
                "code": cc,
                "tariff_lines": tl,
                "sub_positions": sp,
                "total_positions": tp,
                "lines_with_sub_positions": summary.get("lines_with_sub_positions", 0),
                "vat_rate": summary.get("vat_rate_pct", 0),
                "dd_avg": summary.get("dd_rate_range", {}).get("avg", 0),
                "chapters": summary.get("chapters_covered", 0),
                "generated_at": data.get("generated_at", ""),
            })
            stats["total_tariff_lines"] += tl
            stats["total_sub_positions"] += sp
            stats["total_positions"] += tp
    stats["country_count"] = len(stats["countries"])
    return stats


@router.get("/{country_code}/summary")
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
    "DZA": "Algerie", "EGY": "Egypte", "LBY": "Libye", "MAR": "Maroc",
    "TUN": "Tunisie", "SDN": "Soudan", "MRT": "Mauritanie",
    "BEN": "Benin", "BFA": "Burkina_Faso", "CPV": "Cap_Vert", "CIV": "Cote_Ivoire",
    "GMB": "Gambie", "GHA": "Ghana", "GIN": "Guinee", "GNB": "Guinee_Bissau",
    "LBR": "Liberia", "MLI": "Mali", "NER": "Niger", "NGA": "Nigeria",
    "SEN": "Senegal", "SLE": "Sierra_Leone", "TGO": "Togo",
    "CMR": "Cameroun", "CAF": "Centrafrique", "TCD": "Tchad", "COG": "Congo",
    "GAB": "Gabon", "GNQ": "Guinee_Equatoriale", "COD": "RD_Congo", "STP": "Sao_Tome",
    "KEN": "Kenya", "TZA": "Tanzanie", "UGA": "Ouganda", "RWA": "Rwanda",
    "BDI": "Burundi", "SSD": "Soudan_Sud",
    "ZAF": "Afrique_Sud", "BWA": "Botswana", "NAM": "Namibie", "LSO": "Lesotho",
    "SWZ": "Eswatini", "MWI": "Malawi", "ZMB": "Zambie", "ZWE": "Zimbabwe",
    "MOZ": "Mozambique", "AGO": "Angola", "MDG": "Madagascar", "MUS": "Maurice",
    "COM": "Comores", "SYC": "Seychelles",
    "ETH": "Ethiopie", "ERI": "Erythree", "DJI": "Djibouti", "SOM": "Somalie",
}

REGIONS = {
    "afrique_nord": {"name": "Afrique du Nord / UMA", "countries": ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN", "MRT"]},
    "cedeao": {"name": "CEDEAO / ECOWAS", "countries": ["BEN", "BFA", "CPV", "CIV", "GMB", "GHA", "GIN", "GNB", "LBR", "MLI", "NER", "NGA", "SEN", "SLE", "TGO"]},
    "cemac": {"name": "CEMAC + RDC + STP", "countries": ["CMR", "CAF", "TCD", "COG", "GAB", "GNQ", "COD", "STP"]},
    "eac": {"name": "EAC", "countries": ["KEN", "TZA", "UGA", "RWA", "BDI", "SSD"]},
    "sadc": {"name": "SADC / SACU", "countries": ["ZAF", "BWA", "NAM", "LSO", "SWZ", "MWI", "ZMB", "ZWE", "MOZ", "AGO", "MDG", "MUS", "COM", "SYC"]},
    "igad": {"name": "IGAD / Corne de l'Afrique", "countries": ["ETH", "ERI", "DJI", "SOM"]},
}


def _generate_csv(country_code: str) -> str:
    json_path = os.path.join(TARIFFS_DIR, f"{country_code}_tariffs.json")
    if not os.path.exists(json_path):
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = data.get("tariff_lines", [])
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    csv_path = os.path.join(EXPORTS_DIR, f"{country_code}_tarifs.csv")

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile, delimiter=";")
        writer.writerow([
            "Code_HS6", "Chapitre", "Description_FR", "Description_EN",
            "Categorie", "Unite", "Sensibilite",
            "DD_Taux_%", "DD_Source", "ZLECAf_Taux_%", "ZLECAf_Source",
            "TVA_%", "Autres_Taxes_%", "Total_Taxes_%",
            "Taxes_Detail", "Avantages_Fiscaux", "Formalites_Administratives",
            "Total_Import_Taxes_%", "ZLECAf_Total_Taxes_%",
            "Nb_Sous_Positions"
        ])
        for line in lines:
            td = line.get("taxes_detail", [])
            taxes_str = " | ".join([f"{t['tax']}:{t['rate']}%" for t in td]) if td else ""
            fa = line.get("fiscal_advantages", [])
            fa_str = " | ".join([f"{a['tax']}:{a['rate']}% {a.get('condition_fr','')}" for a in fa]) if fa else ""
            af = line.get("administrative_formalities", [])
            af_str = " | ".join([f"{f_item['code']} {f_item['document_fr']}" for f_item in af]) if af else ""
            writer.writerow([
                line.get("hs6", ""), line.get("chapter", ""),
                line.get("description_fr", ""), line.get("description_en", ""),
                line.get("category", ""), line.get("unit", ""),
                line.get("sensitivity", ""),
                line.get("dd_rate", 0), line.get("dd_source", ""),
                line.get("zlecaf_rate", 0), line.get("zlecaf_source", ""),
                line.get("vat_rate", 0), line.get("other_taxes_rate", 0),
                line.get("total_taxes_pct", 0),
                taxes_str, fa_str, af_str,
                line.get("total_import_taxes", 0),
                line.get("zlecaf_total_taxes", 0),
                line.get("sub_position_count", 0),
            ])
    return csv_path


@router.get("/download/list")
async def list_downloads():
    collector = get_collector()
    available = sorted(collector.get_available_countries())
    countries = []
    for cc in available:
        csv_path = os.path.join(EXPORTS_DIR, f"{cc}_tarifs.csv")
        exists = os.path.exists(csv_path)
        size_kb = round(os.path.getsize(csv_path) / 1024) if exists else 0
        countries.append({
            "code": cc,
            "name": COUNTRY_NAMES.get(cc, cc),
            "csv_ready": exists,
            "size_kb": size_kb,
            "download_url": f"/api/tariff-data/download/{cc}",
        })
    return {
        "countries": countries,
        "count": len(countries),
        "regions": {k: v for k, v in REGIONS.items()},
    }


@router.get("/download/{country_code}")
async def download_country_csv(country_code: str):
    cc = country_code.upper()
    csv_path = os.path.join(EXPORTS_DIR, f"{cc}_tarifs.csv")

    if not os.path.exists(csv_path):
        csv_path = _generate_csv(cc)
        if not csv_path:
            raise HTTPException(status_code=404, detail=f"No tariff data for {cc}")

    name = COUNTRY_NAMES.get(cc, cc)
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=f"Tarifs_{name}_{cc}.csv",
        headers={"Content-Disposition": f'attachment; filename="Tarifs_{name}_{cc}.csv"'},
    )
