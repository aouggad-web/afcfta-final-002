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


CHAPTER_GROUPS = [
    ("01", "10"), ("11", "20"), ("21", "30"), ("31", "40"), ("41", "50"),
    ("51", "60"), ("61", "70"), ("71", "80"), ("81", "90"), ("91", "99"),
]

CHAPTER_DESCRIPTIONS_FR = {
    "01": "Animaux vivants", "02": "Viandes et abats comestibles",
    "03": "Poissons et crustacés", "04": "Lait, oeufs, miel",
    "05": "Autres produits d'origine animale", "06": "Plantes vivantes et fleurs",
    "07": "Légumes, plantes, racines", "08": "Fruits comestibles, agrumes",
    "09": "Café, thé, épices", "10": "Céréales",
    "11": "Produits de la minoterie", "12": "Graines et fruits oléagineux",
    "13": "Gommes, résines", "14": "Matières à tresser",
    "15": "Graisses et huiles", "16": "Préparations de viandes/poissons",
    "17": "Sucres et sucreries", "18": "Cacao et préparations",
    "19": "Préparations de céréales", "20": "Préparations de légumes/fruits",
    "21": "Préparations alimentaires diverses", "22": "Boissons, liquides alcooliques",
    "23": "Résidus des industries alimentaires", "24": "Tabacs",
    "25": "Sel, soufre, terres, pierres", "26": "Minerais, scories, cendres",
    "27": "Combustibles minéraux, huiles", "28": "Produits chimiques inorganiques",
    "29": "Produits chimiques organiques", "30": "Produits pharmaceutiques",
    "31": "Engrais", "32": "Extraits tannants, peintures",
    "33": "Huiles essentielles, parfumerie", "34": "Savons, cires, bougies",
    "35": "Matières albuminoïdes, colles", "36": "Poudres, explosifs, allumettes",
    "37": "Produits photographiques", "38": "Produits chimiques divers",
    "39": "Matières plastiques", "40": "Caoutchouc",
    "41": "Peaux et cuirs", "42": "Ouvrages en cuir",
    "43": "Pelleteries et fourrures", "44": "Bois et ouvrages en bois",
    "45": "Liège", "46": "Ouvrages de sparterie/vannerie",
    "47": "Pâtes de bois, papier recyclé", "48": "Papiers et cartons",
    "49": "Produits de l'édition, presse", "50": "Soie",
    "51": "Laine, poils fins", "52": "Coton",
    "53": "Autres fibres textiles végétales", "54": "Filaments synthétiques",
    "55": "Fibres synthétiques discontinues", "56": "Ouates, feutres, cordages",
    "57": "Tapis et revêtements de sol", "58": "Tissus spéciaux, broderies",
    "59": "Tissus imprégnés, enduits", "60": "Étoffes de bonneterie",
    "61": "Vêtements en bonneterie", "62": "Vêtements (hors bonneterie)",
    "63": "Autres articles textiles confectionnés", "64": "Chaussures, guêtres",
    "65": "Coiffures", "66": "Parapluies, cannes",
    "67": "Plumes, fleurs artificielles", "68": "Ouvrages en pierres, ciment",
    "69": "Produits céramiques", "70": "Verre et ouvrages en verre",
    "71": "Perles, pierres précieuses, métaux précieux",
    "72": "Fonte, fer et acier", "73": "Ouvrages en fonte, fer, acier",
    "74": "Cuivre", "75": "Nickel", "76": "Aluminium",
    "78": "Plomb", "79": "Zinc", "80": "Étain",
    "81": "Autres métaux communs", "82": "Outils, coutellerie",
    "83": "Ouvrages divers en métaux communs",
    "84": "Machines, appareils mécaniques", "85": "Machines, appareils électriques",
    "86": "Véhicules ferroviaires", "87": "Voitures automobiles, tracteurs",
    "88": "Navigation aérienne", "89": "Navigation maritime",
    "90": "Instruments d'optique, médecine", "91": "Horlogerie",
    "92": "Instruments de musique", "93": "Armes et munitions",
    "94": "Meubles, literie, éclairage", "95": "Jouets, jeux, articles de sport",
    "96": "Ouvrages divers", "97": "Objets d'art, antiquités",
    "99": "Codes spéciaux",
}


def _generate_country_csvs(country_code: str):
    json_path = os.path.join(TARIFFS_DIR, f"{country_code}_tariffs.json")
    if not os.path.exists(json_path):
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = data.get("tariff_lines", [])
    os.makedirs(EXPORTS_DIR, exist_ok=True)

    generated = []
    for ch_start, ch_end in CHAPTER_GROUPS:
        group_lines = [l for l in lines if ch_start <= l.get("chapter", "00") <= ch_end]
        if not group_lines:
            continue

        csv_name = f"{country_code}_NPF_ch{ch_start}-{ch_end}.csv"
        csv_path = os.path.join(EXPORTS_DIR, csv_name)

        by_chapter = {}
        for l in group_lines:
            ch = l.get("chapter", "00")
            if ch not in by_chapter:
                by_chapter[ch] = []
            by_chapter[ch].append(l)

        with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile, delimiter=";")
            writer.writerow([
                "Code", "Niveau", "Description_FR", "Description_EN",
                "DD_%", "TVA_%", "Autres_Taxes_%",
                "Taxes_Detail", "Formalites",
                "Total_%",
            ])

            for ch in sorted(by_chapter.keys()):
                ch_desc = CHAPTER_DESCRIPTIONS_FR.get(ch, "")
                writer.writerow([f"CHAPITRE {ch}", "---", ch_desc, "", "", "", "", "", "", ""])

                prev_taxes = ""
                prev_formalites = ""
                for line in by_chapter[ch]:
                    td = line.get("taxes_detail", [])
                    taxes_str = " | ".join([f"{t['tax']}:{t['rate']}%" for t in td]) if td else ""
                    af = line.get("administrative_formalities", [])
                    af_str = " | ".join([f"{fi['code']} {fi['document_fr']}" for fi in af]) if af else ""

                    show_taxes = taxes_str if taxes_str != prev_taxes else "="
                    show_form = af_str if af_str != prev_formalites else "="
                    prev_taxes = taxes_str
                    prev_formalites = af_str

                    writer.writerow([
                        line.get("hs6", ""), "HS6",
                        line.get("description_fr", ""), line.get("description_en", ""),
                        line.get("dd_rate", 0), line.get("vat_rate", 0),
                        line.get("other_taxes_rate", 0),
                        show_taxes, show_form,
                        line.get("total_import_taxes", 0),
                    ])

                    for sp in line.get("sub_positions", []):
                        digits = sp.get("digits", len(sp.get("code", "")))
                        writer.writerow([
                            sp.get("code", ""), f"HS{digits}",
                            sp.get("description_fr", ""), sp.get("description_en", ""),
                            sp.get("dd", 0), "", "", "", "", "",
                        ])

        generated.append({
            "group": f"{ch_start}-{ch_end}",
            "file": csv_name,
            "path": csv_path,
            "hs6_count": len(group_lines),
            "total_lines": len(group_lines) + sum(len(l.get("sub_positions", [])) for l in group_lines),
        })

    return generated


@router.get("/download/list")
async def list_downloads():
    collector = get_collector()
    available = sorted(collector.get_available_countries())
    countries = []
    for cc in available:
        files = []
        total_size = 0
        for ch_start, ch_end in CHAPTER_GROUPS:
            csv_path = os.path.join(EXPORTS_DIR, f"{cc}_NPF_ch{ch_start}-{ch_end}.csv")
            if os.path.exists(csv_path):
                size_kb = round(os.path.getsize(csv_path) / 1024)
                files.append({
                    "group": f"{ch_start}-{ch_end}",
                    "size_kb": size_kb,
                    "download_url": f"/tariff-data/download/{cc}/{ch_start}-{ch_end}",
                })
                total_size += size_kb
        countries.append({
            "code": cc,
            "name": COUNTRY_NAMES.get(cc, cc),
            "csv_ready": len(files) > 0,
            "files": files,
            "file_count": len(files),
            "total_size_kb": total_size,
        })
    return {
        "countries": countries,
        "count": len(countries),
        "regions": {k: v for k, v in REGIONS.items()},
    }


@router.get("/download/{country_code}/{chapter_group}")
async def download_country_csv(country_code: str, chapter_group: str):
    cc = country_code.upper()
    csv_path = os.path.join(EXPORTS_DIR, f"{cc}_NPF_ch{chapter_group}.csv")

    if not os.path.exists(csv_path):
        results = _generate_country_csvs(cc)
        if not results:
            raise HTTPException(status_code=404, detail=f"No tariff data for {cc}")
        csv_path = os.path.join(EXPORTS_DIR, f"{cc}_NPF_ch{chapter_group}.csv")
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail=f"No data for chapters {chapter_group}")

    name = COUNTRY_NAMES.get(cc, cc)
    filename = f"Tarifs_NPF_{name}_{cc}_ch{chapter_group}.csv"
    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
