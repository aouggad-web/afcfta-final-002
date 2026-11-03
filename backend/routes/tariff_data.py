import csv
import io
import json
import logging
import os
import re
import zipfile
from typing import Optional

from entitlement_guard import get_optional_subscriber, require_admin_illimite, require_module
from entitlements import admin_acces_illimite
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
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
# cap by hitting it. Tariff files are downloadable by no plan (product
# decision of 2026-11-03): only the admin account can download them, when
# ADMIN_ACCES_ILLIMITE is on (entitlements.admin_acces_illimite).
_tools_metered = [Depends(require_module("tools"))]
_admin_illimite = [Depends(require_admin_illimite())]

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


# Le tarif est l'export du socle de calcul (scripts/exporter_tarifs_socle.py) :
# le tarif tel que le calculateur l'applique, archivé avec son manifeste, qui
# donne aussi le nombre de positions de chaque pays. Les fichiers ne sont
# servis qu'au compte admin (voir _admin_illimite).
SOCLE_EXPORTS_DIR = os.path.join(EXPORTS_DIR, "socle")


def _fichiers(entree):
    return [entree["fichier"], entree["fichier_notes"]]


def _exports_socle():
    path = os.path.join(SOCLE_EXPORTS_DIR, "MANIFESTE.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("pays", {})


@router.get("/download/list")
async def list_downloads(user: Optional[dict] = Depends(get_optional_subscriber)):
    # Aucun téléchargement de tarif n'est proposé, quelle que soit la formule
    # (décision du responsable produit, 03/11/2026) : la liste ne donne que le
    # nombre de positions tarifaires nationales de chaque pays. Seul le compte
    # admin, si ADMIN_ACCES_ILLIMITE est activé, reçoit les liens.
    telechargement = admin_acces_illimite(user)
    countries = []
    for cc, entree in _exports_socle().items():
        country = {
            "code": cc,
            "name": COUNTRY_NAMES.get(cc, cc),
            "positions": entree["positions"],
            "collecte": entree.get("collecte"),
            "devise": entree.get("devise"),
        }
        if telechargement:
            size = sum(os.path.getsize(os.path.join(SOCLE_EXPORTS_DIR, f)) for f in _fichiers(entree))
            country.update(
                total_size_kb=round(size / 1024),
                download_url=f"/tariff-data/download-zip/{cc}",
                json_download_url=f"/tariff-data/download-json/{cc}",
            )
        countries.append(country)
    return {
        "telechargement": telechargement,
        "countries": countries,
        "count": len(countries),
        "regions": {k: v for k, v in REGIONS.items()},
    }


@router.get("/download-zip/{country_code}", dependencies=_admin_illimite)
async def download_country_zip(country_code: str):
    # Le code pays est lu sur le manifeste : le chemin ne reprend jamais
    # l'entrée brute de l'utilisateur.
    exports = _exports_socle()
    cc = next((k for k in exports if k == country_code.upper()), None)
    if cc is None:
        raise HTTPException(status_code=404, detail=f"No tariff export for {country_code}")

    name = _safe_filename_part(COUNTRY_NAMES.get(cc, cc))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fichier in _fichiers(exports[cc]):
            zf.write(os.path.join(SOCLE_EXPORTS_DIR, fichier), fichier)
    buf.seek(0)
    filename = f"Tarifs_NPF_{name}_{cc}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _safe_filename_part(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name)


def _valeur(cellule):
    """Un taux s'écrit en nombre ; une forme publiée (« 8c/kg ») ou « n.d. »
    reste du texte."""
    try:
        return float(cellule)
    except ValueError:
        return cellule


def _liste(cellule, separateur=" | "):
    return cellule.split(separateur) if cellule else []


def _tarif_json(cc, entree):
    """Le tarif du pays en JSON, lu sur le CSV archivé et ses notes : il suit
    donc chaque réexport du socle, sans copie qui pourrait diverger."""
    codes = [c["code"] for c in entree["colonnes"]]
    with open(os.path.join(SOCLE_EXPORTS_DIR, entree["fichier"]), encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.reader(f, delimiter=";"))[1:]
    with open(os.path.join(SOCLE_EXPORTS_DIR, entree["fichier_notes"]), encoding="utf-8-sig", newline="") as f:
        notes = {n[0]: {"prelevement": n[1], "texte": n[2]} for n in list(csv.reader(f, delimiter=";"))[1:]}

    positions = []
    for ligne in lignes:
        valeurs = ligne[4 : 4 + len(codes)]
        total, etat, manques, restrictions, renvois = ligne[4 + len(codes) :]
        positions.append(
            {
                "position": ligne[0],
                "designation": ligne[1],
                "chapitre": ligne[2],
                "unite": ligne[3] or None,
                "droits": {code: _valeur(v) for code, v in zip(codes, valeurs) if v != ""},
                "total_pour_100_caf": float(total) if total else None,
                "etat": etat,
                "manques": _liste(manques),
                "restrictions": _liste(restrictions),
                "notes": _liste(renvois, " "),
            }
        )
    return {
        "pays": cc,
        "nom": COUNTRY_NAMES.get(cc, cc),
        "devise": entree.get("devise"),
        "date_reference": entree.get("date_reference"),
        "collecte": entree.get("collecte"),
        "socle_sha256": entree["socle_sha256"],
        "prelevements": entree["colonnes"],
        "positions": positions,
        "notes": notes,
    }


@router.get("/download-json/{country_code}", dependencies=_admin_illimite)
async def download_country_json(country_code: str):
    exports = _exports_socle()
    cc = next((k for k in exports if k == country_code.upper()), None)
    if cc is None:
        raise HTTPException(status_code=404, detail=f"No tariff export for {country_code}")

    name = _safe_filename_part(COUNTRY_NAMES.get(cc, cc))
    filename = f"Tarifs_NPF_{name}_{cc}.json"
    return JSONResponse(
        _tarif_json(cc, exports[cc]),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/download-region-zip/{region_key}", dependencies=_admin_illimite)
async def download_region_zip(region_key: str):
    region = REGIONS.get(region_key)
    if not region:
        raise HTTPException(status_code=404, detail=f"Unknown region: {region_key}")

    exports = _exports_socle()
    region_name = region["name"].replace(" / ", "_").replace(" ", "_")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for cc in region["countries"]:
            if cc not in exports:
                continue
            name = _safe_filename_part(COUNTRY_NAMES.get(cc, cc))
            for fichier in _fichiers(exports[cc]):
                zf.write(os.path.join(SOCLE_EXPORTS_DIR, fichier), f"{region_name}/{name}_{cc}/{fichier}")
    buf.seek(0)
    filename = f"Tarifs_NPF_{region_name}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
