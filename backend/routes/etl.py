"""
ETL routes - Data pipeline administration and monitoring
Handles TRS data updates, coverage reports, and pipeline status
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from logistics_data import get_all_ports

router = APIRouter(prefix="/etl")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent


@router.post("/run")
async def run_etl_pipeline():
    """
    Exécute le pipeline ETL pour mettre à jour les données portuaires.

    Met à jour:
    - Données TRS (Time Release Study) officielles WCO
    - Données LPI (Logistics Performance Index) World Bank 2023
    - Benchmarks globaux UNCTAD

    IMPORTANT: Seules les données officielles sont utilisées.
    Les ports sans données officielles sont marqués "NA".
    """
    try:
        import sys

        sys.path.insert(0, str(ROOT_DIR))
        from etl.ports_etl import run_etl

        result = run_etl()
        return {
            "status": "success",
            "message": "Pipeline ETL exécuté avec succès",
            "details": result,
        }
    except Exception as e:
        logger.error(f"ETL pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_etl_status():
    """
    Retourne le statut du dernier pipeline ETL.
    """
    try:
        log_file = ROOT_DIR / "etl" / "etl_log.json"
        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                log_data = json.load(f)

            # Dernière exécution
            last_entries = log_data[-68:] if len(log_data) >= 68 else log_data
            last_timestamp = last_entries[-1]["timestamp"] if last_entries else None

            return {
                "last_run": last_timestamp,
                "total_updates": len(log_data),
                "ports_with_trs_data": 4,
                "ports_without_trs_data": 64,
                "data_sources": [
                    "WCO Time Release Studies",
                    "World Bank LPI 2023",
                    "World Bank CPPI 2023-2024",
                    "UNCTAD Review of Maritime Transport 2024",
                    "Kenya Ports Authority (KPA)",
                    "Transnet Port Terminals (South Africa)",
                    "Tanger Med Port Authority",
                    "ANP Maroc",
                ],
            }
        else:
            return {"last_run": None, "message": "Aucun pipeline ETL exécuté"}
    except Exception as e:
        logger.error(f"ETL route error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trs-coverage")
async def get_trs_coverage():
    """
    Retourne la couverture des données TRS officielles par port.
    """
    try:
        ports = get_all_ports()

        with_data = []
        without_data = []

        for port in ports:
            trs = port.get("trs_analysis", {})
            dwell = trs.get("container_dwell_time_days")

            port_info = {
                "port_id": port.get("port_id"),
                "port_name": port.get("port_name"),
                "country": port.get("country_name"),
                "country_iso": port.get("country_iso"),
            }

            if dwell and dwell != "NA":
                port_info.update(
                    {
                        "dwell_time_days": dwell,
                        "source": trs.get("source"),
                        "data_year": trs.get("data_year"),
                        "methodology": trs.get("methodology"),
                    }
                )
                with_data.append(port_info)
            else:
                port_info["notes"] = trs.get("notes", "NA")
                without_data.append(port_info)

        return {
            "total_ports": len(ports),
            "ports_with_official_trs": len(with_data),
            "ports_without_trs": len(without_data),
            "coverage_percentage": round(len(with_data) / len(ports) * 100, 1),
            "ports_with_data": with_data,
            "ports_without_data": without_data,
            "note": "Seules les données TRS officielles (WCO, autorités portuaires) sont incluses. Aucune estimation.",
        }
    except Exception as e:
        logger.error(f"ETL route error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
