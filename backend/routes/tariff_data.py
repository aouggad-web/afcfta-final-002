from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import logging

from services.tariff_data_collector import get_collector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tariff-data", tags=["Tariff Data Collection"])


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
