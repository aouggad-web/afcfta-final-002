"""
COMTRADE API Routes
Provides access to UN COMTRADE v1 trade data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from services.comtrade_service import comtrade_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comtrade", tags=["COMTRADE"])


@router.get("/bilateral/{reporter}")
def get_bilateral_trade(
    reporter: str,
    partner: str = Query("0", description="Partner country code (0 for World)"),
    period: str = Query(None, description="Year (YYYY)"),
    hs_code: str = Query(None, description="HS product code")
):
    """
    Get bilateral trade data from UN COMTRADE v1 API
    
    - **reporter**: ISO3 or M49 country code (e.g., MAR, 504)
    - **partner**: Partner country code (0 for World aggregate)
    - **period**: Year in YYYY format (defaults to previous year)
    - **hs_code**: Optional HS code filter
    """
    try:
        from datetime import datetime
        if not period:
            period = str(datetime.now().year - 1)
            
        result = comtrade_service.get_bilateral_trade(
            reporter_code=reporter.upper(),
            partner_code=partner,
            period=period,
            hs_code=hs_code
        )
        
        if not result:
            return {
                "status": "no_data",
                "message": f"Aucune donnée COMTRADE disponible pour {reporter}",
                "reporter": reporter,
                "source": "UN_COMTRADE"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"COMTRADE bilateral error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-period/{country}")
def get_latest_period(country: str):
    """
    Check the latest available data period for a country
    
    - **country**: ISO3 or M49 country code
    """
    try:
        period = comtrade_service.get_latest_available_period(country.upper())
        
        return {
            "country": country.upper(),
            "latest_period": period,
            "has_data": period is not None,
            "source": "UN_COMTRADE"
        }
        
    except Exception as e:
        logger.error(f"COMTRADE latest period error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def get_service_status():
    """
    Get current status of COMTRADE service
    
    Shows API key configuration, call counts, and availability
    """
    return comtrade_service.get_service_status()


@router.get("/metadata")
def get_metadata(
    type_code: str = Query("C", description="C for commodities, S for services"),
    freq_code: str = Query("A", description="A for annual, M for monthly"),
    cl_code: str = Query("HS", description="Classification: HS, SITC, BEC, EBOPS")
):
    """
    Get metadata for trade classifications
    """
    try:
        result = comtrade_service.get_metadata(type_code, freq_code, cl_code)
        
        if not result:
            return {"status": "no_data", "message": "Métadonnées non disponibles"}
        
        return result
        
    except Exception as e:
        logger.error(f"COMTRADE metadata error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-update")
def get_live_update():
    """
    Get live update information from COMTRADE API
    """
    try:
        result = comtrade_service.get_live_update()
        
        if not result:
            return {"status": "no_data", "message": "Informations non disponibles"}
        
        return result
        
    except Exception as e:
        logger.error(f"COMTRADE live update error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
