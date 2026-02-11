from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime
import requests
import pandas as pd
import asyncio
import json
from country_data import get_country_data, REAL_COUNTRY_DATA
from constants import AFRICAN_COUNTRIES, ZLECAF_RULES_OF_ORIGIN
from models import CountryInfo, TariffCalculationRequest, TariffCalculationResponse, CountryEconomicProfile
from translations import (
    COUNTRY_TRANSLATIONS, REGION_TRANSLATIONS, RULES_TRANSLATIONS,
    translate_country_name, translate_region, translate_rule
)
from gold_reserves_data import GOLD_RESERVES_GAI_DATA
from tax_rates import calculate_all_taxes, get_vat_rate
from data_loader import (
    load_corrections_data, 
    load_commerce_data, 
    get_country_commerce_profile,
    get_all_countries_trade_performance,
    get_enhanced_statistics,
    get_tariff_corrections,
    get_country_customs_info,
    get_country_infrastructure_ranking
)
from logistics_data import (
    get_all_ports,
    get_port_by_id,
    get_ports_by_type,
    get_top_ports_by_teu,
    search_ports
)
from logistics_air_data import (
    get_all_airports,
    get_airport_by_id,
    get_top_airports_by_cargo,
    search_airports
)
from projects_data import get_country_ongoing_projects
from etl.country_tariffs import get_country_tariff_rate, get_available_rates, get_tariff_regime
from free_zones_data import load_free_zones, get_free_zones_by_country
from etl.hs_codes_data import (
    get_hs_chapters,
    get_hs6_codes,
    get_hs6_code,
    search_hs_codes,
    get_codes_by_chapter,
    get_all_hs_data
)
from etl.hs6_tariffs import (
    get_hs6_tariff,
    get_hs6_tariff_rates,
    search_hs6_tariffs,
    get_hs6_tariffs_by_chapter,
    get_hs6_statistics
)
from etl.country_tariffs_complete import (
    get_tariff_rate_for_country,
    get_zlecaf_tariff_rate,
    get_vat_rate_for_country,
    get_other_taxes_for_country,
    get_complete_taxes_for_country,
    get_all_country_rates,
    COUNTRY_VAT_RATES,
    COUNTRY_OTHER_TAXES
)
from etl.country_hs6_tariffs import (
    get_country_hs6_tariff,
    get_country_hs6_dd_rate,
    search_country_hs6_tariffs,
    get_available_country_tariffs,
    COUNTRY_HS6_TARIFFS
)
from etl.country_hs6_detailed import (
    get_detailed_tariff,
    get_sub_position_rate,
    get_all_sub_positions,
    has_varying_rates,
    get_tariff_summary,
    COUNTRY_HS6_DETAILED
)
from etl.hs6_database import (
    HS6_DATABASE,
    SUB_POSITION_TYPES,
    get_hs6_info,
    get_sub_position_suggestions,
    get_rule_of_origin,
    search_hs6_codes,
    get_all_categories,
    get_codes_by_category,
    get_database_stats
)

# Import routes module for modular endpoint registration
from routes import register_routes

from services.tariff_data_service import tariff_service
from services.crawled_data_service import crawled_service

try:
    from backend.notifications import NotificationManager
except ImportError:
    try:
        from notifications import NotificationManager
    except ImportError:
        NotificationManager = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ.get('MONGO_URL', '')
db = None
client = None
if mongo_url:
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'afcfta')]
        logging.info("MongoDB connected successfully")
    except Exception as e:
        logging.warning(f"MongoDB connection failed: {e}. Running without database.")
        db = None
else:
    logging.warning("MONGO_URL not set. Running without database.")

notification_manager = None
if NotificationManager:
    try:
        notification_manager = NotificationManager()
        logging.info(f"Notification manager initialized with channels: {notification_manager.get_enabled_channels()}")
    except Exception as e:
        logging.warning(f"Notification manager initialization failed: {e}")

app = FastAPI(title="Système Commercial ZLECAf - API Complète", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from middlewares import SecurityHeadersMiddleware, CSRFMiddleware, RateLimitMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFMiddleware, exempt_paths=[
        "/api/docs", "/api/openapi.json", "/api/redoc",
        "/api/health", "/api/",
        "/api/tariff-data/collect",
        "/api/crawl",
        "/api/crawl/start",
    ])
    app.add_middleware(RateLimitMiddleware, requests_per_minute=120, burst_limit=20)
    logging.info("Security middlewares loaded: CSP headers, CSRF protection, Rate limiting")
except ImportError as e:
    logging.warning(f"Security middlewares not loaded: {e}")

api_router = APIRouter(prefix="/api")

# Pays membres de la ZLECAf avec données économiques
# AFRICAN_COUNTRIES and ZLECAF_RULES_OF_ORIGIN moved to constants.py

# API Clients pour données externes
class WorldBankAPIClient:
    def __init__(self):
        self.base_url = "https://api.worldbank.org/v2"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ZLECAf-API/1.0'})

    async def get_country_data(self, country_codes: List[str], indicators: List[str] = None) -> Dict[str, Any]:
        """Récupérer les données économiques des pays depuis la Banque Mondiale"""
        if indicators is None:
            indicators = ['NY.GDP.MKTP.CD', 'SP.POP.TOTL', 'NY.GDP.PCAP.CD', 'FP.CPI.TOTL.ZG']
        
        try:
            all_data = {}
            for country in country_codes:
                country_data = {}
                for indicator in indicators:
                    url = f"{self.base_url}/country/{country}/indicator/{indicator}"
                    params = {
                        'format': 'json',
                        'date': '2020:2023',
                        'per_page': 10
                    }
                    
                    response = self.session.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 1 and data[1]:
                            latest_data = data[1][0] if data[1] else None
                            if latest_data and latest_data['value']:
                                country_data[indicator] = {
                                    'value': latest_data['value'],
                                    'date': latest_data['date']
                                }
                
                all_data[country] = country_data
            
            return all_data
        except Exception as e:
            logging.error(f"Erreur World Bank API: {e}")
            return {}

class OECAPIClient:
    def __init__(self):
        self.base_url = "https://api-v2.oec.world"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ZLECAf-API/1.0'})

    async def get_top_producers(self, hs_code: str, year: int = 2021) -> List[Dict[str, Any]]:
        """Récupérer le top 5 des pays africains producteurs pour un code SH"""
        try:
            endpoint = "tesseract/data.jsonrecords"
            params = {
                'cube': 'trade_i_hs4_eci',
                'drilldowns': 'Reporter',
                'measures': 'Export Value',
                'Product': hs_code[:4] if len(hs_code) > 4 else hs_code,
                'time': str(year),
                'Trade Flow': '2'  # Exports
            }
            
            response = self.session.get(f"{self.base_url}/{endpoint}", params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    # Filtrer pour les pays africains seulement
                    african_codes = [country['iso3'] for country in AFRICAN_COUNTRIES]
                    african_exports = []
                    
                    for item in data['data']:
                        if item.get('Reporter') in african_codes:
                            african_exports.append({
                                'country_code': item.get('Reporter'),
                                'country_name': next((c['name'] for c in AFRICAN_COUNTRIES if c['iso3'] == item.get('Reporter')), item.get('Reporter')),
                                'export_value': item.get('Export Value', 0),
                                'year': year
                            })
                    
                    # Trier par valeur d'export et prendre le top 5
                    african_exports.sort(key=lambda x: x['export_value'], reverse=True)
                    return african_exports[:5]
            
            return []
        except Exception as e:
            logging.error(f"Erreur OEC API: {e}")
            return []

# Clients API globaux
wb_client = WorldBankAPIClient()
oec_client = OECAPIClient()

# Define Models
# Models moved to models.py

# Routes
@api_router.get("/")
async def root():
    return {"message": "Système Commercial ZLECAf API - Version Complète"}

@api_router.get("/comtrade/health")
async def check_comtrade_health():
    """Check Comtrade API health and configuration"""
    from services.comtrade_service import comtrade_service
    
    try:
        health_status = comtrade_service.health_check()
        return {
            "status": "operational" if health_status["connected"] else "error",
            "using_key": "secondary" if health_status["using_secondary"] else "primary",
            "api_calls_today": health_status["calls_today"],
            "rate_limit_remaining": health_status["rate_limit_remaining"],
            "last_error": health_status["last_error"],
            "primary_key_configured": health_status["primary_key_configured"],
            "secondary_key_configured": health_status["secondary_key_configured"],
            "timestamp": health_status["timestamp"]
        }
    except Exception as e:
        logging.error(f"Error checking Comtrade health: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# NOTE: /health and /health/status endpoints migrated to /routes/health.py

# NOTE: /countries endpoint MIGRATED to /routes/countries.py
# NOTE: /country-profile/{country_code} endpoint MIGRATED to /routes/countries.py

@api_router.get("/rules-of-origin/stats")
async def get_rules_of_origin_statistics():
    """Obtenir les statistiques de la base de données des règles d'origine ZLECAf"""
    from etl.afcfta_rules_of_origin import get_rules_statistics
    return get_rules_statistics()


@api_router.get("/rules-of-origin/{hs_code}")
async def get_rules_of_origin(hs_code: str, lang: str = "fr"):
    """Récupérer les règles d'origine ZLECAf pour un code SH
    
    Basé sur l'Annexe II, Appendice IV de l'Accord ZLECAf
    Source: AfCFTA Protocol on Trade in Goods - Rules of Origin Manual
    """
    from etl.afcfta_rules_of_origin import get_rule_of_origin, ORIGIN_TYPES, CHAPTER_RULES
    
    # Obtenir les règles d'origine officielles
    roo_data = get_rule_of_origin(hs_code, lang)
    
    # Check status - UNKNOWN means no rules exist (404)
    # YTB (Yet to be agreed) is intentionally allowed to return 200 with messaging
    # that negotiations are ongoing, as these headings have complete data structures
    status = roo_data.get("status", "AGREED")
    
    if status == "UNKNOWN":
        error_msg = "Rules of origin not found for this HS code" if lang == "en" else "Règles d'origine non trouvées pour ce code SH"
        raise HTTPException(status_code=404, detail=error_msg)
    
    # YTB headings return complete data with appropriate "under negotiation" messaging
    # This is intentional - users should see that rules exist but are being negotiated
    
    primary_rule = roo_data.get("primary_rule", {})
    alt_rule = roo_data.get("alternative_rule", {})
    regional_content = roo_data.get("regional_content", 40)
    
    # Documentation labels
    if lang == "en":
        docs = [
            "AfCFTA Certificate of Origin",
            "Commercial Invoice",
            "Packing List",
            "Supplier Declaration"
        ]
        validity = "12 months"
        authority = "Competent authority of exporting country"
        status_label = "Agreed" if status == "AGREED" else "Under negotiation"
    else:
        docs = [
            "Certificat d'origine ZLECAf",
            "Facture commerciale",
            "Liste de colisage",
            "Déclaration du fournisseur"
        ]
        validity = "12 mois"
        authority = "Autorité compétente du pays exportateur"
        status_label = "Convenu" if status == "AGREED" else "En négociation"
    
    return {
        "hs_code": hs_code,
        "hs6_code": hs_code[:6] if len(hs_code) >= 6 else hs_code,
        "chapter": roo_data.get("chapter", hs_code[:2]),
        "status": status,
        "status_label": status_label,
        "rules": {
            "primary_rule": {
                "type": primary_rule.get("type", ""),
                "code": primary_rule.get("code", ""),
                "name": primary_rule.get("name", ""),
                "description": primary_rule.get("description", "")
            },
            "alternative_rule": {
                "type": alt_rule.get("type", ""),
                "code": alt_rule.get("code", ""),
                "name": alt_rule.get("name", ""),
                "description": alt_rule.get("description", "")
            } if alt_rule else None,
            "regional_content": regional_content,
            "regional_content_minimum": f"{regional_content}%"
        },
        "chapter_description": roo_data.get("chapter_description", ""),
        "notes": roo_data.get("notes", ""),
        "explanation": {
            "rule_type": primary_rule.get("name", ""),
            "rule_code": primary_rule.get("code", ""),
            "requirement_summary": f"{regional_content}% contenu régional minimum" if lang == "fr" else f"{regional_content}% minimum regional content",
            "documentation_required": docs,
            "validity_period": validity,
            "issuing_authority": authority
        },
        "source": {
            "name": "AfCFTA Protocol on Trade in Goods - Annex II, Appendix IV",
            "url": "https://au.int/sites/default/files/treaties/36437-ax-AfCFTA_RULES_OF_ORIGIN_MANUAL.pdf"
        }
    }

@api_router.get("/tariff-data/status")
async def get_tariff_data_status():
    """Statut du service de données tarifaires collectées"""
    stats = tariff_service.get_stats()
    crawled_stats = crawled_service.get_stats()
    return {
        "status": "active" if stats["loaded"] and stats["countries"] > 0 else "inactive",
        "data_source": "collected_verified" if stats["loaded"] and stats["countries"] > 0 else "etl_fallback",
        "countries_loaded": stats["countries"],
        "total_hs6_lines": stats["total_hs6_lines"],
        "total_sub_positions": stats["total_sub_positions"],
        "total_positions": stats["total_positions"],
        "crawled_data": crawled_stats,
        "description": "Données tarifaires consolidées et vérifiées pour le calculateur" if stats["loaded"] else "Utilisation des modules ETL comme source de données"
    }

@api_router.get("/crawled-data/status")
async def get_crawled_data_status():
    """Statut des données authentiques crawlées depuis les sites officiels"""
    return crawled_service.get_stats()

@api_router.post("/crawled-data/reload")
async def reload_crawled_data():
    """Recharger les données crawlées après un nouveau crawl"""
    crawled_service.load(force=True)
    stats = crawled_service.get_stats()
    return {"status": "reloaded", **stats}

@api_router.get("/crawled-data/lookup/{country_code}/{hs_code}")
async def lookup_crawled_position(country_code: str, hs_code: str):
    """Rechercher une position dans les données crawlées authentiques"""
    if not crawled_service.is_loaded():
        return {"error": "Données crawlées non chargées", "available": False}
    
    result = crawled_service.lookup(country_code.upper(), hs_code)
    if not result:
        sub_positions = crawled_service.lookup_by_hs6(country_code.upper(), hs_code[:6])
        if sub_positions:
            return {
                "exact_match": False,
                "hs6_sub_positions": sub_positions[:20],
                "total_sub_positions": len(sub_positions),
                "message": f"Position exacte non trouvée. {len(sub_positions)} sous-positions disponibles pour le HS6 {hs_code[:6]}"
            }
        return {"exact_match": False, "message": "Position non trouvée dans les données crawlées", "available": False}
    
    return {"exact_match": True, "position": result}

@api_router.get("/crawled-data/search/{country_code}")
async def search_crawled_positions(country_code: str, q: str = Query(..., min_length=2), limit: int = Query(50, le=200)):
    """Rechercher dans les données crawlées par code ou désignation"""
    results = crawled_service.search(country_code.upper(), q, limit=limit)
    return {"query": q, "country": country_code.upper(), "results": results, "count": len(results)}

crawl_jobs = {}

@api_router.post("/crawl/start/{country_code}")
async def start_crawl(country_code: str):
    country_code = country_code.upper()
    supported = {"DZA": "Algérie", "TUN": "Tunisie", "MAR": "Maroc"}
    if country_code not in supported:
        raise HTTPException(status_code=400, detail=f"Crawl non supporté pour {country_code}. Pays supportés: {list(supported.keys())}")
    
    if country_code in crawl_jobs and crawl_jobs[country_code].get("status") == "running":
        return {"status": "already_running", "job": crawl_jobs[country_code]}
    
    crawl_jobs[country_code] = {
        "country": country_code,
        "country_name": supported[country_code],
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "progress": "Démarrage...",
        "sub_positions_found": 0,
    }
    
    async def run_crawl():
        try:
            if country_code == "DZA":
                from crawlers.countries.algeria_conformepro_scraper import AlgeriaConformeproScraper
                scraper = AlgeriaConformeproScraper()
                crawl_jobs[country_code]["progress"] = "Extraction des sections..."
                await scraper.scrape_sections()
                crawl_jobs[country_code]["progress"] = f"{len(scraper.sections)} sections trouvées. Extraction des chapitres..."
                await scraper.scrape_chapters()
                crawl_jobs[country_code]["progress"] = f"{len(scraper.chapters)} chapitres trouvés. Extraction des rangées..."
                await scraper.scrape_headings()
                crawl_jobs[country_code]["progress"] = f"{len(scraper.headings)} rangées trouvées. Extraction des sous-positions..."
                await scraper.scrape_all_sub_positions()
                scraper.save_final()
                crawl_jobs[country_code]["status"] = "completed"
                crawl_jobs[country_code]["finished_at"] = datetime.utcnow().isoformat()
                crawl_jobs[country_code]["sub_positions_found"] = len(scraper.sub_positions)
                crawl_jobs[country_code]["stats"] = scraper.stats
                crawl_jobs[country_code]["progress"] = f"Terminé: {len(scraper.sub_positions)} sous-positions extraites"
            elif country_code == "TUN":
                from crawlers.countries.tunisia_douane_scraper import TunisiaDouaneScraper
                scraper = TunisiaDouaneScraper()
                all_results = []
                data_dir = Path(__file__).parent / "data" / "crawled"
                chapters = [f"{i:02d}" for i in range(1, 98) if i != 77]
                resume_from = 0
                progress_files = sorted(data_dir.glob("TUN_progress_*.json"), key=lambda p: int(p.stem.split("_")[-1]))
                if progress_files:
                    last_progress = progress_files[-1]
                    try:
                        with open(last_progress, "r", encoding="utf-8") as f:
                            prev = json.load(f)
                        all_results = prev.get("sub_positions", [])
                        resume_from = prev.get("chapters_done", 0)
                        crawl_jobs[country_code]["progress"] = f"Reprise au chapitre {resume_from+1}/{len(chapters)} ({len(all_results)} positions récupérées)"
                        crawl_jobs[country_code]["sub_positions_found"] = len(all_results)
                        logging.info(f"TUN: Resuming from chapter {resume_from} with {len(all_results)} positions")
                    except Exception as e:
                        logging.warning(f"TUN: Could not load progress: {e}")
                        resume_from = 0
                        all_results = []
                for ch_idx, ch in enumerate(chapters):
                    if ch_idx < resume_from:
                        continue
                    crawl_jobs[country_code]["progress"] = f"Chapitre {ch} ({ch_idx+1}/{len(chapters)})..."
                    results = await scraper.scrape_chapter(ch)
                    all_results.extend(results)
                    crawl_jobs[country_code]["sub_positions_found"] = len(all_results)
                    if (ch_idx + 1) % 5 == 0 or ch_idx == len(chapters) - 1:
                        progress_path = data_dir / f"TUN_progress_{ch_idx+1}.json"
                        with open(progress_path, "w", encoding="utf-8") as f:
                            json.dump({"country_code": "TUN", "country_name": "Tunisie", "source": "douane.gov.tn/tarifweb2025", "extracted_at": datetime.utcnow().isoformat(), "chapters_done": ch_idx+1, "stats": {"sub_positions": len(all_results)}, "sub_positions": all_results}, f, ensure_ascii=False)
                csv_path = str(data_dir / "TUN_crawled.csv")
                scraper.save_csv(all_results, csv_path)
                json_path = data_dir / "TUN_tariffs.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump({"country_code": "TUN", "country_name": "Tunisie", "source": "douane.gov.tn/tarifweb2025", "extracted_at": datetime.utcnow().isoformat(), "stats": {"sub_positions": len(all_results)}, "sub_positions": all_results}, f, ensure_ascii=False)
                crawl_jobs[country_code]["status"] = "completed"
                crawl_jobs[country_code]["finished_at"] = datetime.utcnow().isoformat()
                crawl_jobs[country_code]["sub_positions_found"] = len(all_results)
                crawl_jobs[country_code]["progress"] = f"Terminé: {len(all_results)} positions extraites"
                await scraper._close_client()
            elif country_code == "MAR":
                from crawlers.countries.morocco_douane_scraper import MoroccoDouaneScraper
                scraper = MoroccoDouaneScraper()
                chapters = [f"{i:02d}" for i in range(1, 98) if i != 77]
                all_results = []
                data_dir = Path(__file__).parent / "data" / "crawled"
                resume_from = 0
                progress_files = sorted(data_dir.glob("MAR_progress_*.json"), key=lambda p: int(p.stem.split("_")[-1]))
                if progress_files:
                    last_progress = progress_files[-1]
                    try:
                        with open(last_progress, "r", encoding="utf-8") as f:
                            prev = json.load(f)
                        all_results = prev.get("sub_positions", [])
                        resume_from = prev.get("chapters_done", 0)
                        crawl_jobs[country_code]["progress"] = f"Reprise au chapitre {resume_from+1}/{len(chapters)} ({len(all_results)} positions récupérées)"
                        crawl_jobs[country_code]["sub_positions_found"] = len(all_results)
                        logging.info(f"MAR: Resuming from chapter {resume_from} with {len(all_results)} positions")
                    except Exception as e:
                        logging.warning(f"MAR: Could not load progress: {e}")
                        resume_from = 0
                        all_results = []
                for ch_idx, ch in enumerate(chapters):
                    if ch_idx < resume_from:
                        continue
                    crawl_jobs[country_code]["progress"] = f"Chapitre {ch} ({ch_idx+1}/{len(chapters)})..."
                    chapter_data = await scraper.scrape_chapter_with_taxes(ch)
                    all_results.extend(chapter_data)
                    crawl_jobs[country_code]["sub_positions_found"] = len(all_results)
                    if (ch_idx + 1) % 5 == 0 or ch_idx == len(chapters) - 1:
                        progress_path = data_dir / f"MAR_progress_{ch_idx+1}.json"
                        with open(progress_path, "w", encoding="utf-8") as f:
                            json.dump({"country_code": "MAR", "country_name": "Maroc", "source": "douane.gov.ma/adil", "extracted_at": datetime.utcnow().isoformat(), "chapters_done": ch_idx+1, "stats": {"sub_positions": len(all_results)}, "sub_positions": all_results}, f, ensure_ascii=False)
                json_path = data_dir / "MAR_tariffs.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump({"country_code": "MAR", "country_name": "Maroc", "source": "douane.gov.ma/adil", "extracted_at": datetime.utcnow().isoformat(), "stats": {"sub_positions": len(all_results)}, "sub_positions": all_results}, f, ensure_ascii=False)
                csv_path = str(data_dir / "MAR_crawled.csv")
                scraper.save_csv(all_results, csv_path)
                crawl_jobs[country_code]["status"] = "completed"
                crawl_jobs[country_code]["finished_at"] = datetime.utcnow().isoformat()
                crawl_jobs[country_code]["sub_positions_found"] = len(all_results)
                crawl_jobs[country_code]["progress"] = f"Terminé: {len(all_results)} positions extraites"
        except Exception as e:
            crawl_jobs[country_code]["status"] = "error"
            crawl_jobs[country_code]["error"] = str(e)
            crawl_jobs[country_code]["progress"] = f"Erreur: {str(e)}"
            logging.error(f"Crawl error for {country_code}: {e}")
    
    asyncio.create_task(run_crawl())
    return {"status": "started", "job": crawl_jobs[country_code]}

@api_router.get("/crawl/status/{country_code}")
async def get_crawl_status(country_code: str):
    country_code = country_code.upper()
    if country_code not in crawl_jobs:
        crawled_path = Path(__file__).parent / "data" / "crawled" / f"{country_code}_tariffs.json"
        if crawled_path.exists():
            with open(crawled_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "status": "completed",
                "country": country_code,
                "sub_positions_found": data.get("stats", {}).get("sub_positions", len(data.get("sub_positions", []))),
                "source": data.get("source", ""),
                "extracted_at": data.get("extracted_at", ""),
            }
        return {"status": "not_found", "country": country_code}
    return {"status": crawl_jobs[country_code]["status"], "job": crawl_jobs[country_code]}

@api_router.get("/crawl/data/{country_code}")
async def get_crawled_data(
    country_code: str,
    chapter: Optional[str] = None,
    heading: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
):
    country_code = country_code.upper()
    crawled_path = Path(__file__).parent / "data" / "crawled" / f"{country_code}_tariffs.json"
    if not crawled_path.exists():
        raise HTTPException(status_code=404, detail=f"Aucune donnée crawlée pour {country_code}")
    
    with open(crawled_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    positions = data.get("sub_positions", [])
    
    if chapter:
        positions = [p for p in positions if p.get("chapter") == chapter.zfill(2)]
    if heading:
        positions = [p for p in positions if p.get("heading", "").startswith(heading)]
    if search:
        search_lower = search.lower()
        positions = [p for p in positions if 
            search_lower in p.get("name", "").lower() or
            search_lower in p.get("designation", "").lower() or
            search_lower in p.get("hs_code", "").lower()]
    
    total = len(positions)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "country": country_code,
        "source": data.get("source", ""),
        "extracted_at": data.get("extracted_at", ""),
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "positions": positions[start:end],
    }

@api_router.get("/crawl/sources")
async def get_crawl_sources():
    crawled_dir = Path(__file__).parent / "data" / "crawled"
    sources = {
        "available_crawlers": {
            "DZA": {
                "name": "Algérie",
                "source": "conformepro.dz (données douane.gov.dz)",
                "data_type": "Sous-positions nationales 10 chiffres",
                "taxes": ["Droit de douane (DD)", "TVA", "TCS", "PRCT", "DAPS"],
                "includes": ["Désignation exacte", "Avantages fiscaux", "Formalités administratives"],
            },
            "TUN": {
                "name": "Tunisie",
                "source": "douane.gov.tn/tarifweb2025",
                "data_type": "Positions nationales NDP 11 chiffres",
                "taxes": ["Droit de Douane (DD)", "TVA", "RPD", "Droit de Consommation (DC)", "FODEC", "Droits spécifiques"],
                "includes": ["Désignation exacte", "Régime import/export", "Préférences tarifaires", "Réglementation", "Groupe d'utilisation"],
            },
            "MAR": {
                "name": "Maroc",
                "source": "douane.gov.ma/adil",
                "data_type": "Positions nationales 10 chiffres",
                "taxes": ["Droit d'Importation (DI)", "Taxe Parafiscale à l'Importation (TPI)", "Taxe sur la Valeur Ajoutée (TVA)", "Taxe Intérieure de Consommation (TIC)"],
                "includes": ["Désignation exacte", "Documents et normes à l'import", "Formalités particulières"],
            },
        },
        "crawled_data": {},
        "planned_crawlers": {
            "CIV": {"name": "Côte d'Ivoire", "source": "guce.gouv.ci", "status": "En développement"},
            "CMR": {"name": "Cameroun", "source": "douanes.cm", "status": "En développement"},
            "SEN": {"name": "Sénégal", "source": "douanes.sn", "status": "Planifié"},
            "ZAF": {"name": "Afrique du Sud", "source": "sars.gov.za", "status": "Planifié"},
            "KEN": {"name": "Kenya", "source": "kra.go.ke", "status": "Planifié"},
        },
    }
    
    if crawled_dir.exists():
        for f in crawled_dir.glob("*_tariffs.json"):
            code = f.stem.replace("_tariffs", "")
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                sources["crawled_data"][code] = {
                    "country_name": meta.get("country_name", code),
                    "source": meta.get("source", ""),
                    "extracted_at": meta.get("extracted_at", ""),
                    "sub_positions": meta.get("stats", {}).get("sub_positions", len(meta.get("sub_positions", []))),
                }
            except:
                pass
    
    return sources

@api_router.get("/crawl/download-sample/{country_code}")
async def download_crawl_sample(country_code: str):
    from starlette.responses import FileResponse
    country_code = country_code.upper()
    sample_path = Path(__file__).parent / "data" / "crawled" / f"{country_code}_sample.csv"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Pas de fichier échantillon pour {country_code}")
    return FileResponse(
        str(sample_path),
        media_type="text/csv",
        filename=f"{country_code}_tarif_douanier_echantillon.csv",
    )

@api_router.post("/calculate-tariff", response_model=TariffCalculationResponse)
async def calculate_comprehensive_tariff(request: TariffCalculationRequest):
    """Calculer les tarifs complets avec données tarifaires collectées et vérifiées
    
    Accepte les codes ISO2 (ex: DZ) ou ISO3 (ex: DZA) pour les pays
    Supporte les codes HS de 6 à 12 chiffres pour plus de précision
    
    SOURCE DES DONNÉES:
    - Principale: Données tarifaires collectées (1.18M positions, 54 pays)
    - Fallback: Modules ETL si données collectées non disponibles
    
    ORDRE DE PRIORITÉ DES TARIFS:
    1. Sous-position nationale (8-12 chiffres) si fournie
    2. Tarif SH6 spécifique au pays
    3. Tarif par chapitre du pays
    """
    
    # Chercher par ISO3 d'abord, puis ISO2 (rétrocompatibilité)
    origin_country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == request.origin_country.upper()), None)
    if not origin_country:
        origin_country = next((c for c in AFRICAN_COUNTRIES if c['code'] == request.origin_country.upper()), None)
    
    dest_country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == request.destination_country.upper()), None)
    if not dest_country:
        dest_country = next((c for c in AFRICAN_COUNTRIES if c['code'] == request.destination_country.upper()), None)
    
    if not origin_country or not dest_country:
        raise HTTPException(status_code=400, detail="L'un des pays sélectionnés n'est pas membre de la ZLECAf")
    
    # Utiliser ISO3 pour les calculs
    dest_iso3 = dest_country['iso3']
    origin_iso3 = origin_country['iso3']
    
    # Nettoyer et normaliser le code HS
    hs_code_clean = request.hs_code.replace(".", "").replace(" ", "")
    hs6_code = hs_code_clean[:6].zfill(6)
    sector_code = hs6_code[:2]
    
    tariff_precision = "chapter"
    sub_position_used = None
    sub_position_description = None
    data_source = "etl_fallback"
    
    collected_taxes_detail = []
    collected_fiscal_advantages = []
    collected_admin_formalities = []
    crawled_raw_taxes = []

    # ============================================================
    # PRIORITÉ 1: Données crawlées authentiques (sites officiels)
    # ============================================================
    if crawled_service.is_loaded():
        crawled_result = crawled_service.lookup(dest_iso3, hs_code_clean)
        if crawled_result:
            data_source = "crawled_authentic"
            sub_position_used = crawled_result["code_raw"]
            sub_position_description = crawled_result["designation"]
            tariff_precision = "national_position"
            crawled_raw_taxes = crawled_result["taxes"]
            raw_advantages = crawled_result.get("fiscal_advantages", [])
            collected_fiscal_advantages = [
                item if isinstance(item, dict) else {"description": item, "source": crawled_result["source"]}
                for item in raw_advantages
            ]
            raw_formalities = crawled_result.get("administrative_formalities", [])
            collected_admin_formalities = [
                item if isinstance(item, dict) else {"description": item, "source": crawled_result["source"]}
                for item in raw_formalities
            ]

            dd_tax = next((t for t in crawled_raw_taxes if t["code"] in ("DD", "DI", "DDDROIT", "Droit d'Importation (DI)")), None)
            if dd_tax and dd_tax.get("rate_pct") is not None:
                normal_rate = dd_tax["rate_pct"] / 100.0
            else:
                normal_rate = 0.0
            npf_source = f"Source officielle: {crawled_result['source']}"

            vat_tax = next((t for t in crawled_raw_taxes if t["code"] in ("TVA", "TVA/APTAXE") or "TVA" in t.get("name", "").upper() or "Valeur Ajoutée" in t.get("name", "")), None)
            if vat_tax and vat_tax.get("rate_pct") is not None:
                vat_rate = vat_tax["rate_pct"] / 100.0
                vat_source = f"{vat_tax['name']} ({crawled_result['source']})"
            else:
                vat_rate, vat_source = get_vat_rate_for_country(dest_iso3)

            other_taxes_rate = 0.0
            other_taxes_detail = {}
            for t in crawled_raw_taxes:
                if t["code"] not in ("DD", "DI", "DDDROIT", "Droit d'Importation (DI)") and "TVA" not in t.get("code", "").upper() and "Valeur Ajoutée" not in t.get("name", ""):
                    if t.get("rate_pct") is not None:
                        other_taxes_rate += t["rate_pct"] / 100.0
                        other_taxes_detail[t["code"]] = t["rate_pct"]

            collected_taxes_detail = [
                {
                    "tax": t["name"],
                    "rate": t["rate_pct"] if t.get("rate_pct") is not None else 0,
                    "raw_value": t.get("raw_value", ""),
                    "observation": f"Source: {t.get('source', crawled_result['source'])}",
                }
                for t in crawled_raw_taxes
            ]

            from etl.country_tariffs_complete import get_product_category, get_zlecaf_reduction_factor
            product_category = get_product_category(hs6_code)
            reduction_factor = get_zlecaf_reduction_factor(dest_iso3, product_category)
            zlecaf_rate = normal_rate * reduction_factor
            zlecaf_source = f"ZLECAf ({product_category})"

    # ============================================================
    # PRIORITÉ 2: Données collectées ETL enrichies
    # ============================================================
    if data_source != "crawled_authentic" and tariff_service.is_loaded():
        tariff_info = tariff_service.get_tariff_precision_info(dest_iso3, hs_code_clean)
        if tariff_info:
            normal_rate = tariff_info["rate"]
            npf_source = tariff_info["source"]
            tariff_precision = tariff_info["precision"]
            sub_position_used = tariff_info.get("sub_position_code")
            sub_position_description = tariff_info.get("sub_position_description")
            data_source = "collected_verified"

            collected_taxes_detail = tariff_info.get("taxes_detail", [])
            collected_fiscal_advantages = tariff_info.get("fiscal_advantages", [])
            collected_admin_formalities = tariff_info.get("administrative_formalities", [])

            zlecaf_rate_val, zlecaf_source = tariff_service.get_zlecaf_rate(dest_iso3, hs6_code)
            if zlecaf_rate_val is not None:
                zlecaf_rate = zlecaf_rate_val
            else:
                from etl.country_tariffs_complete import get_product_category, get_zlecaf_reduction_factor
                product_category = get_product_category(hs6_code)
                reduction_factor = get_zlecaf_reduction_factor(dest_iso3, product_category)
                zlecaf_rate = normal_rate * reduction_factor
                zlecaf_source = f"ZLECAf ({product_category})"

            vat_rate, vat_source = tariff_service.get_vat_rate(dest_iso3)

            if collected_taxes_detail:
                product_other = sum(
                    t["rate"] for t in collected_taxes_detail
                    if t["tax"] not in ("D.D", "T.V.A")
                ) / 100.0
                other_taxes_rate = product_other
                other_taxes_detail = {
                    t["tax"].lower().replace(".", ""): t["rate"]
                    for t in collected_taxes_detail
                    if t["tax"] not in ("D.D", "T.V.A")
                }
                vat_from_detail = next((t["rate"] for t in collected_taxes_detail if t["tax"] == "T.V.A"), None)
                if vat_from_detail is not None:
                    vat_rate = vat_from_detail / 100.0
            else:
                other_taxes_rate, other_taxes_detail = tariff_service.get_other_taxes(dest_iso3)
    
    # ============================================================
    # PRIORITÉ 3: Modules ETL (fallback)
    # ============================================================
    if data_source not in ("crawled_authentic", "collected_verified"):
        if len(hs_code_clean) > 6:
            rate, description, source = get_sub_position_rate(dest_iso3, hs_code_clean)
            if rate is not None:
                normal_rate = rate
                npf_source = f"Sous-position nationale {dest_iso3} ({hs_code_clean})"
                tariff_precision = "sub_position"
                sub_position_used = hs_code_clean
                sub_position_description = description

        if tariff_precision == "chapter":
            hs6_tariff = get_country_hs6_tariff(dest_iso3, hs6_code)
            if hs6_tariff:
                normal_rate = hs6_tariff["dd"]
                npf_source = f"Tarif SH6 {dest_iso3} ({hs6_code})"
                tariff_precision = "hs6_country"
            else:
                normal_rate, npf_source = get_tariff_rate_for_country(dest_iso3, hs6_code)
                tariff_precision = "chapter"

        from etl.country_tariffs_complete import get_product_category, get_zlecaf_reduction_factor
        product_category = get_product_category(hs6_code)
        reduction_factor = get_zlecaf_reduction_factor(dest_iso3, product_category)
        zlecaf_rate = normal_rate * reduction_factor
        zlecaf_source = f"ZLECAf ({product_category})"

        vat_rate, vat_source = get_vat_rate_for_country(dest_iso3)
        other_taxes_rate, other_taxes_detail = get_other_taxes_for_country(dest_iso3)
    
    # Source de tarif pour affichage
    rate_source = f"Tarif officiel {dest_iso3} - {npf_source}"
    
    # Période de transition selon le secteur
    tariff_corrections = get_tariff_corrections()
    transition_periods = tariff_corrections.get('transition_periods', {})
    transition_period = transition_periods.get(sector_code, 'immediate')
    
    # ============================================================
    # CALCULS DES MONTANTS
    # ============================================================
    
    # Droits de douane
    normal_customs = request.value * normal_rate
    zlecaf_customs = request.value * zlecaf_rate
    
    # Autres taxes (sur valeur CIF)
    other_taxes_amount = request.value * other_taxes_rate
    
    # TVA calculée sur (Valeur + DD + Autres taxes)
    normal_vat_base = request.value + normal_customs + other_taxes_amount
    zlecaf_vat_base = request.value + zlecaf_customs + other_taxes_amount
    
    normal_vat_amount = normal_vat_base * vat_rate
    zlecaf_vat_amount = zlecaf_vat_base * vat_rate
    
    # Totaux
    normal_total = request.value + normal_customs + other_taxes_amount + normal_vat_amount
    zlecaf_total = request.value + zlecaf_customs + other_taxes_amount + zlecaf_vat_amount
    
    # Économies
    savings = normal_customs - zlecaf_customs
    savings_percentage = (savings / normal_customs) * 100 if normal_customs > 0 else 0
    total_savings_with_taxes = normal_total - zlecaf_total
    total_savings_percentage = (total_savings_with_taxes / normal_total) * 100 if normal_total > 0 else 0
    
    legal_refs = {
        "cif": {"ref": "Incoterms 2020 - CIF", "url": "https://iccwbo.org/resources-for-business/incoterms-rules/incoterms-2020/"},
        "dd": {"ref": f"Tarif douanier {dest_iso3}", "url": None},
        "rs": {"ref": "Règlement UEMOA 02/97/CM", "url": None},
        "pcs": {"ref": "Règlement UEMOA 01/2019", "url": None},
        "cedeao": {"ref": "Protocole CEDEAO A/P1/1/03", "url": None},
        "tci": {"ref": "Règlement CEMAC 02/01", "url": None},
        "vat": {"ref": f"Code Général des Impôts {dest_iso3}", "url": None},
        "zlecaf": {"ref": "Accord ZLECAf Art. 8", "url": "https://au.int/en/treaties/agreement-establishing-african-continental-free-trade-area"},
        "daps": {"ref": f"Décret exécutif - DAPS {dest_iso3}", "url": None},
        "prct": {"ref": f"Loi de Finances {dest_iso3}", "url": None},
        "tcs": {"ref": f"Réglementation sanitaire {dest_iso3}", "url": None},
    }

    normal_journal = [
        {"step": 1, "component": "Valeur CIF", "base": request.value, "rate": "-", "amount": request.value, "cumulative": request.value, "legal_ref": legal_refs["cif"]["ref"], "legal_ref_url": legal_refs["cif"]["url"]},
    ]
    step = 2
    cumulative = request.value

    if collected_taxes_detail:
        for tax_item in collected_taxes_detail:
            tax_name = tax_item["tax"]
            tax_rate_pct = tax_item["rate"]
            tax_rate_dec = tax_rate_pct / 100.0
            tax_amount = round(request.value * tax_rate_dec, 2) if tax_name != "T.V.A" else round(normal_vat_amount, 2)

            if tax_name == "T.V.A":
                tax_base = round(normal_vat_base, 2)
                cumulative = round(normal_total, 2)
            else:
                tax_base = request.value
                cumulative += tax_amount

            ref_key = tax_name.lower().replace(".", "").replace(" ", "")
            ref = legal_refs.get(ref_key, {"ref": tax_item.get("observation", ""), "url": None})

            normal_journal.append({
                "step": step,
                "component": f"{tax_name} ({tax_item.get('observation', '')})" if tax_item.get("observation") else tax_name,
                "base": tax_base,
                "rate": f"{tax_rate_pct:.1f}%",
                "amount": tax_amount,
                "cumulative": round(cumulative, 2),
                "legal_ref": ref["ref"],
                "legal_ref_url": ref.get("url"),
            })
            step += 1
    else:
        normal_journal.append({"step": step, "component": "Droits de douane (DD)", "base": request.value, "rate": f"{normal_rate*100:.1f}%", "amount": round(normal_customs, 2), "cumulative": round(request.value + normal_customs, 2), "legal_ref": legal_refs["dd"]["ref"], "legal_ref_url": legal_refs["dd"]["url"]})
        step = 3
        cumulative = request.value + normal_customs

        rs_rate = other_taxes_detail.get('rs', 0) / 100 if other_taxes_detail.get('rs') else 0
        pcs_rate = other_taxes_detail.get('pcs', 0) / 100 if other_taxes_detail.get('pcs') else 0
        cedeao_rate = other_taxes_detail.get('cedeao', 0) / 100 if other_taxes_detail.get('cedeao') else 0
        tci_rate = other_taxes_detail.get('tci', 0) / 100 if other_taxes_detail.get('tci') else 0

        if rs_rate > 0:
            rs_amount = round(request.value * rs_rate, 2)
            cumulative += rs_amount
            normal_journal.append({"step": step, "component": "Redevance statistique (RS)", "base": request.value, "rate": f"{rs_rate*100:.1f}%", "amount": rs_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["rs"]["ref"], "legal_ref_url": legal_refs["rs"]["url"]})
            step += 1
        if pcs_rate > 0:
            pcs_amount = round(request.value * pcs_rate, 2)
            cumulative += pcs_amount
            normal_journal.append({"step": step, "component": "PCS UEMOA", "base": request.value, "rate": f"{pcs_rate*100:.1f}%", "amount": pcs_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["pcs"]["ref"], "legal_ref_url": legal_refs["pcs"]["url"]})
            step += 1
        if cedeao_rate > 0:
            cedeao_amount = round(request.value * cedeao_rate, 2)
            cumulative += cedeao_amount
            normal_journal.append({"step": step, "component": "Prélèvement CEDEAO (PC)", "base": request.value, "rate": f"{cedeao_rate*100:.1f}%", "amount": cedeao_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["cedeao"]["ref"], "legal_ref_url": legal_refs["cedeao"]["url"]})
            step += 1
        if tci_rate > 0:
            tci_amount = round(request.value * tci_rate, 2)
            cumulative += tci_amount
            normal_journal.append({"step": step, "component": "TCI CEMAC", "base": request.value, "rate": f"{tci_rate*100:.1f}%", "amount": tci_amount, "cumulative": round(cumulative, 2), "legal_ref": legal_refs["tci"]["ref"], "legal_ref_url": legal_refs["tci"]["url"]})
            step += 1
        normal_journal.append({"step": step, "component": "TVA", "base": round(normal_vat_base, 2), "rate": f"{vat_rate*100:.1f}%", "amount": round(normal_vat_amount, 2), "cumulative": round(normal_total, 2), "legal_ref": legal_refs["vat"]["ref"], "legal_ref_url": legal_refs["vat"]["url"]})
    
    # Créer le journal de calcul détaillé pour ZLECAf avec références légales
    zlecaf_journal = [
        {"step": 1, "component": "Valeur CIF", "base": request.value, "rate": "-", "amount": request.value, "cumulative": request.value, "legal_ref": legal_refs["cif"]["ref"], "legal_ref_url": legal_refs["cif"]["url"]},
        {"step": 2, "component": "Droits de douane ZLECAf (DD)", "base": request.value, "rate": f"{zlecaf_rate*100:.1f}%", "amount": round(zlecaf_customs, 2), "cumulative": round(request.value + zlecaf_customs, 2), "legal_ref": legal_refs["zlecaf"]["ref"], "legal_ref_url": legal_refs["zlecaf"]["url"]},
    ]
    step = 3
    zlecaf_cumulative = request.value + zlecaf_customs
    if other_taxes_rate > 0:
        zlecaf_cumulative += other_taxes_amount
        zlecaf_journal.append({"step": step, "component": "Autres taxes", "base": request.value, "rate": f"{other_taxes_rate*100:.1f}%", "amount": round(other_taxes_amount, 2), "cumulative": round(zlecaf_cumulative, 2), "legal_ref": "Taxes communautaires", "legal_ref_url": None})
        step += 1
    zlecaf_journal.append({"step": step, "component": "TVA", "base": round(zlecaf_vat_base, 2), "rate": f"{vat_rate*100:.1f}%", "amount": round(zlecaf_vat_amount, 2), "cumulative": round(zlecaf_total, 2), "legal_ref": legal_refs["vat"]["ref"], "legal_ref_url": legal_refs["vat"]["url"]})
    
    # Règles d'origine - Utiliser les règles officielles de l'AfCFTA Annex II
    from etl.afcfta_rules_of_origin import get_rule_of_origin, ORIGIN_TYPES
    roo_data = get_rule_of_origin(hs6_code, "fr")
    
    # Construire l'objet rules_of_origin pour le calculateur
    if roo_data.get("status") == "UNKNOWN":
        rules = {
            "rule": "Règle non définie",
            "requirement": "Consulter le Secrétariat ZLECAf",
            "regional_content": 0,
            "status": "UNKNOWN",
            "source": "AfCFTA Annex II - Appendix IV"
        }
    else:
        primary_rule = roo_data.get("primary_rule", {})
        rule_name = primary_rule.get("name", "")
        rule_code = primary_rule.get("code", "")
        regional_content = roo_data.get("regional_content", 40)
        status = roo_data.get("status", "AGREED")
        chapter_desc = roo_data.get("chapter_description", "")
        
        # Construire le requirement basé sur le type de règle
        if rule_code == "WO":
            requirement = "Entièrement obtenu dans la ZLECAf (100%)"
        elif rule_code in ["CTH", "CTSH"]:
            requirement = f"Changement de position tarifaire ({rule_code}) avec {regional_content}% minimum de contenu régional"
        elif rule_code == "VA":
            requirement = f"{regional_content}% minimum de valeur ajoutée africaine"
        elif rule_code == "SP":
            requirement = f"Processus spécifique requis avec {regional_content}% minimum de contenu régional"
        else:
            requirement = f"{regional_content}% valeur ajoutée africaine"
        
        # Ajouter l'alternative si disponible
        alt_rule = roo_data.get("alternative_rule", {})
        if alt_rule:
            requirement += f" OU {alt_rule.get('name', '')}"
        
        rules = {
            "rule": rule_name,
            "rule_code": rule_code,
            "requirement": requirement,
            "regional_content": regional_content,
            "status": status,
            "status_label": "Convenu" if status == "AGREED" else "En négociation",
            "chapter_description": chapter_desc,
            "notes": roo_data.get("notes", ""),
            "source": "AfCFTA Protocol on Trade in Goods - Annex II, Appendix IV",
            "reference_url": "https://au.int/sites/default/files/treaties/36437-ax-AfCFTA_RULES_OF_ORIGIN_MANUAL.pdf"
        }
    
    # Récupérer les top producteurs africains
    top_producers = await oec_client.get_top_producers(request.hs_code)
    
    # Récupérer les données économiques des pays
    wb_data = await wb_client.get_country_data([origin_country['wb_code'], dest_country['wb_code']])
    
    # Vérifier si des sous-positions alternatives existent pour ce HS6
    if tariff_service.is_loaded() and data_source == "collected_verified":
        collected_subs = tariff_service.get_sub_positions_for_hs6(dest_iso3, hs6_code)
        if collected_subs:
            sub_positions_available = collected_subs
            rates = [sp.get("dd", 0) / 100.0 for sp in collected_subs]
            has_varying = len(set(rates)) > 1
            min_rate = min(rates) if rates else 0
            max_rate = max(rates) if rates else 0
        else:
            sub_positions_available = get_all_sub_positions(dest_iso3, hs6_code)
            has_varying, min_rate, max_rate = has_varying_rates(dest_iso3, hs6_code)
    else:
        sub_positions_available = get_all_sub_positions(dest_iso3, hs6_code)
        has_varying, min_rate, max_rate = has_varying_rates(dest_iso3, hs6_code)
    
    # Construire le warning et les détails si taux variables
    rate_warning = None
    sub_positions_details = None
    
    if has_varying and len(sub_positions_available) > 0:
        # Construire le message de warning
        rate_warning = {
            "has_variation": True,
            "message_fr": f"⚠️ Attention: Ce code SH6 ({hs6_code}) a des taux de droits de douane variables selon les sous-positions nationales. Le taux peut varier de {min_rate*100:.1f}% à {max_rate*100:.1f}%.",
            "message_en": f"⚠️ Warning: This HS6 code ({hs6_code}) has varying duty rates depending on national sub-headings. Rates range from {min_rate*100:.1f}% to {max_rate*100:.1f}%.",
            "min_rate": min_rate,
            "max_rate": max_rate,
            "min_rate_pct": f"{min_rate*100:.1f}%",
            "max_rate_pct": f"{max_rate*100:.1f}%",
            "rate_used": normal_rate,
            "rate_used_pct": f"{normal_rate*100:.1f}%",
            "recommendation_fr": "Pour un calcul plus précis, veuillez spécifier la sous-position nationale complète (8-12 chiffres).",
            "recommendation_en": "For a more accurate calculation, please specify the complete national sub-heading (8-12 digits)."
        }
        
        # Détails de chaque sous-position
        sub_positions_details = sub_positions_available
    
    # Création de la réponse complète avec toutes les taxes
    result = TariffCalculationResponse(
        origin_country=request.origin_country,
        destination_country=request.destination_country,
        hs_code=request.hs_code,
        hs6_code=hs6_code,
        value=request.value,
        # Tarifs de douane
        normal_tariff_rate=normal_rate,
        normal_tariff_amount=round(normal_customs, 2),
        zlecaf_tariff_rate=zlecaf_rate,
        zlecaf_tariff_amount=round(zlecaf_customs, 2),
        normal_vat_rate=vat_rate,
        normal_vat_amount=round(normal_vat_amount, 2),
        normal_statistical_fee=round(request.value * other_taxes_detail.get('rs', 0) / 100, 2) if other_taxes_detail.get('rs') else 0,
        normal_community_levy=round(request.value * other_taxes_detail.get('pcs', 0) / 100, 2) if other_taxes_detail.get('pcs') else 0,
        normal_ecowas_levy=round(request.value * other_taxes_detail.get('cedeao', 0) / 100, 2) if other_taxes_detail.get('cedeao') else 0,
        normal_other_taxes_total=round(other_taxes_amount, 2),
        normal_total_cost=round(normal_total, 2),
        zlecaf_vat_rate=vat_rate,
        zlecaf_vat_amount=round(zlecaf_vat_amount, 2),
        zlecaf_statistical_fee=round(request.value * other_taxes_detail.get('rs', 0) / 100, 2) if other_taxes_detail.get('rs') else 0,
        zlecaf_community_levy=round(request.value * other_taxes_detail.get('pcs', 0) / 100, 2) if other_taxes_detail.get('pcs') else 0,
        zlecaf_ecowas_levy=round(request.value * other_taxes_detail.get('cedeao', 0) / 100, 2) if other_taxes_detail.get('cedeao') else 0,
        zlecaf_other_taxes_total=round(other_taxes_amount, 2),
        zlecaf_total_cost=round(zlecaf_total, 2),
        # Économies
        savings=round(savings, 2),
        savings_percentage=round(savings_percentage, 1),
        total_savings_with_taxes=round(total_savings_with_taxes, 2),
        total_savings_percentage=round(total_savings_percentage, 1),
        # Journal de calcul et traçabilité
        normal_calculation_journal=normal_journal,
        zlecaf_calculation_journal=zlecaf_journal,
        computation_order_ref="Codes douaniers nationaux + Directives CEDEAO/UEMOA/CEMAC/EAC/SACU",
        last_verified="2025-01",
        confidence_level="high" if data_source == "collected_verified" or tariff_precision in ["sub_position", "hs6_country", "hs6_collected"] else "medium",
        tariff_precision=tariff_precision,
        sub_position_used=sub_position_used,
        sub_position_description=sub_position_description,
        has_varying_sub_positions=has_varying,
        available_sub_positions_count=len(sub_positions_available),
        rate_warning=rate_warning,
        sub_positions_details=sub_positions_details,
        taxes_detail=collected_taxes_detail if collected_taxes_detail else None,
        fiscal_advantages=collected_fiscal_advantages if collected_fiscal_advantages else None,
        administrative_formalities=collected_admin_formalities if collected_admin_formalities else None,
        data_source=data_source,
        rules_of_origin=rules,
        top_african_producers=top_producers,
        origin_country_data=wb_data.get(origin_country['wb_code'], {}),
        destination_country_data=wb_data.get(dest_country['wb_code'], {})
    )
    
    if db is not None:
        await db.comprehensive_calculations.insert_one(result.dict())
    
    return result

@api_router.get("/statistics")
async def get_comprehensive_statistics():
    """Récupérer les statistiques complètes ZLECAf avec données enrichies 2024"""
    
    # Charger les statistiques enrichies depuis le JSON 2024
    enhanced_stats = get_enhanced_statistics()
    
    total_calculations = 0
    total_savings = 0
    countries_result = []
    hs_result = []
    sectors_result = []
    if db is not None:
        total_calculations = await db.comprehensive_calculations.count_documents({})
        pipeline_savings = [
            {"$group": {"_id": None, "total_savings": {"$sum": "$savings"}}}
        ]
        savings_result = await db.comprehensive_calculations.aggregate(pipeline_savings).to_list(1)
        total_savings = savings_result[0]["total_savings"] if savings_result else 0
        pipeline_countries = [
            {"$group": {"_id": "$origin_country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        countries_result = await db.comprehensive_calculations.aggregate(pipeline_countries).to_list(10)
        pipeline_hs = [
            {"$group": {"_id": "$hs_code", "count": {"$sum": 1}, "avg_savings": {"$avg": "$savings"}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        hs_result = await db.comprehensive_calculations.aggregate(pipeline_hs).to_list(10)
        pipeline_sectors = [
            {"$addFields": {"sector": {"$substr": ["$hs_code", 0, 2]}}},
            {"$group": {"_id": "$sector", "count": {"$sum": 1}, "total_savings": {"$sum": "$savings"}}},
            {"$sort": {"total_savings": -1}},
            {"$limit": 10}
        ]
        sectors_result = await db.comprehensive_calculations.aggregate(pipeline_sectors).to_list(10)
    
    # Calcul de l'impact économique potentiel
    african_population = sum([country['population'] for country in AFRICAN_COUNTRIES])
    
    # Utiliser les données enrichies 2024 pour l'overview
    overview_enhanced = enhanced_stats.get('overview', {})
    
    # Générer le VRAI Top 10 exportateurs et importateurs depuis les données complètes
    trade_data_all = get_all_countries_trade_performance()
    
    # Top 10 exportateurs (triés par exports décroissants)
    top_10_exporters = sorted(trade_data_all, key=lambda x: x['exports_2024'], reverse=True)[:10]
    total_exports = sum([c['exports_2024'] for c in trade_data_all])
    top_exporters_formatted = [
        {
            "rank": idx + 1,
            "country": country['code'],
            "name": country['country'],
            "exports_2024": country['exports_2024'] * 1e9,  # Convert to USD
            "share_pct": round((country['exports_2024'] / total_exports) * 100, 1) if total_exports > 0 else 0
        }
        for idx, country in enumerate(top_10_exporters)
    ]
    
    # Top 10 importateurs (triés par imports décroissants)
    top_10_importers = sorted(trade_data_all, key=lambda x: x['imports_2024'], reverse=True)[:10]
    total_imports = sum([c['imports_2024'] for c in trade_data_all])
    top_importers_formatted = [
        {
            "rank": idx + 1,
            "country": country['code'],
            "name": country['country'],
            "imports_2024": country['imports_2024'] * 1e9,  # Convert to USD
            "share_pct": round((country['imports_2024'] / total_imports) * 100, 1) if total_imports > 0 else 0
        }
        for idx, country in enumerate(top_10_importers)
    ]
    
    # Top 5 PIB avec comparaison échanges intra-africains vs monde
    top_5_gdp = sorted(trade_data_all, key=lambda x: x['gdp_2024'], reverse=True)[:5]
    top_5_gdp_formatted = []
    
    # Charger les données intra-africaines
    intra_response = await get_trade_performance_intra_african()
    intra_data_dict = {item['code']: item for item in intra_response['countries_intra_african']}
    
    for country in top_5_gdp:
        intra_info = intra_data_dict.get(country['code'], {})
        top_5_gdp_formatted.append({
            "country": country['country'],
            "code": country['code'],
            "gdp_2024": country['gdp_2024'],
            "exports_world": country['exports_2024'],
            "imports_world": country['imports_2024'],
            "exports_intra_african": intra_info.get('exports_2024', 0),
            "imports_intra_african": intra_info.get('imports_2024', 0),
            "intra_african_percentage": intra_info.get('intra_african_percentage', 17)
        })
    
    # Top 10 PIB 2024 avec projections de croissance 2025
    from country_data import REAL_COUNTRY_DATA
    top_10_gdp = sorted(trade_data_all, key=lambda x: x['gdp_2024'], reverse=True)[:10]
    top_10_gdp_formatted = []
    
    # Mapping code ISO2 -> ISO3
    iso2_to_iso3 = {c['code']: c['iso3'] for c in AFRICAN_COUNTRIES}
    
    for idx, country in enumerate(top_10_gdp):
        iso3_code = iso2_to_iso3.get(country['code'], country['code'])
        country_real_data = REAL_COUNTRY_DATA.get(iso3_code, {})
        
        top_10_gdp_formatted.append({
            "rank": idx + 1,
            "country": country['country'],
            "code": country['code'],
            "gdp_2024_billion": round(country['gdp_2024'], 2),
            "growth_2024": country.get('growth_rate_2024', country_real_data.get('growth_forecast_2024', 'N/A')),
            "growth_projection_2025": country_real_data.get('growth_projection_2025', 'N/A'),
            "population_million": round(country_real_data.get('population_2024', 0) / 1e6, 1) if country_real_data.get('population_2024') else 'N/A',
            "gdp_per_capita": country_real_data.get('gdp_per_capita_2024', 'N/A')
        })
    
    
    # Calculer totaux pour trade_evolution
    trade_evolution_data = enhanced_stats.get('trade_evolution', {})
    trade_evolution_data.update({
        "total_exports_2024": round(total_exports, 1),
        "total_imports_2024": round(total_imports, 1),
        "intra_african_trade_2023": trade_evolution_data.get("intra_african_trade_2023", 192.4),
        "intra_african_trade_2024": trade_evolution_data.get("intra_african_trade_2024", 218.7),
        "projected_intra_trade_2030": trade_evolution_data.get("projected_intra_trade_2030", 385.0),
        "growth_rate_2023_2024": trade_evolution_data.get("growth_rate_2023_2024", 13.7)
    })
    
    return {
        "overview": {
            "total_calculations": overview_enhanced.get('total_calculations', total_calculations),
            "total_savings": overview_enhanced.get('total_savings', total_savings),
            "african_countries_members": overview_enhanced.get('african_countries_members', len(AFRICAN_COUNTRIES)),
            "combined_population": overview_enhanced.get('combined_population', african_population),
            "estimated_combined_gdp": overview_enhanced.get('estimated_combined_gdp', 2706000000000),
            "zlecaf_implementation_status": overview_enhanced.get('zlecaf_implementation_status', '')
        },
        "trade_evolution": trade_evolution_data,
        "top_exporters_2024": top_exporters_formatted,
        "top_importers_2024": top_importers_formatted,
        "top_10_gdp_2024": top_10_gdp_formatted,
        "top_5_gdp_trade_comparison": top_5_gdp_formatted,
        "product_analysis": enhanced_stats.get('product_analysis', {}),
        "regional_integration": enhanced_stats.get('regional_integration', {}),
        "sector_performance": enhanced_stats.get('sector_performance', {}),
        "zlecaf_impact_metrics": enhanced_stats.get('zlecaf_impact_metrics', {}),
        "trade_statistics": {
            "most_active_countries": countries_result,
            "popular_hs_codes": hs_result,
            "top_beneficiary_sectors": sectors_result
        },
        "zlecaf_impact": {
            "average_tariff_reduction": "90%",
            "estimated_trade_creation": "52 milliards USD",
            "job_creation_potential": "18 millions d'emplois",
            "intra_african_trade_target": "25% d'ici 2030",
            "current_intra_african_trade": "15.2%",
            "poverty_reduction": "30 millions de personnes d'ici 2035",
            "income_gains_2035": "450 milliards USD",
            "export_increase_2035": "560 milliards USD (forte composante manufacturière)"
        },
        "projections": {
            "2025": enhanced_stats.get('projections_updated', {}).get('2025', {
                "trade_volume_increase": "15%",
                "tariff_eliminations": "90%",
                "new_trade_corridors": 45,
                "gti_active_corridors": "8 corridors prioritaires"
            }),
            "2030": enhanced_stats.get('projections_updated', {}).get('2030', {
                "trade_volume_increase": "52%",
                "gdp_increase": "7%",
                "industrialization_boost": "35%",
                "tariff_revenue_change": "+3% (malgré baisse des taux)"
            }),
            "2035": {
                "income_gains": "450 milliards USD",
                "poverty_reduction": "30 millions de personnes",
                "export_increase": "560 milliards USD",
                "intra_african_trade": "25-30%"
            },
            "2040": {
                "trade_volume_increase_conservative": "15%",
                "trade_volume_increase_median": "20%",
                "trade_volume_increase_ambitious": "25%",
                "estimated_additional_trade": "50-70 milliards USD"
            }
        },
        "scenarios": {
            "conservative": {
                "description": "Mise en œuvre lente, obstacles persistants",
                "trade_increase_2040": "15%",
                "additional_value": "50 milliards USD"
            },
            "median": {
                "description": "Mise en œuvre progressive, réduction graduelle NTB",
                "trade_increase_2040": "20%",
                "additional_value": "60 milliards USD"
            },
            "ambitious": {
                "description": "Mise en œuvre rapide, élimination NTB, infrastructure optimale",
                "trade_increase_2040": "25%",
                "additional_value": "70 milliards USD"
            }
        },
        "key_mechanisms": {
            "digital_trade_protocol": {
                "adoption_date": "2024-02-18",
                "status": "Adopté",
                "focus": "Harmonisation règles, flux transfrontières, confiance numérique"
            },
            "ntb_platform": {
                "url": "https://tradebarriers.africa",
                "status": "Opérationnel",
                "purpose": "Signalement et résolution obstacles non tarifaires"
            },
            "papss_payments": {
                "status": "Déploiement en cours",
                "purpose": "Système panafricain de paiements et règlements"
            },
            "gti": {
                "status": "Actif",
                "purpose": "Guided Trade Initiative - montée en charge progressive"
            }
        },
        "data_sources": [
            {
                "source": "Union Africaine - AfCFTA Secretariat",
                "url": "https://au.int/en/cfta",
                "verified": "2025-01-11"
            },
            {
                "source": "Banque Mondiale - The African Continental Free Trade Area",
                "url": "https://www.worldbank.org/en/topic/trade/publication/the-african-continental-free-trade-area",
                "key_findings": "Gains de 450 Md$, 30M sorties pauvreté (2035)",
                "verified": "2025-01-11"
            },
            {
                "source": "UNECA - Economic Commission for Africa",
                "url": "https://www.uneca.org/",
                "key_findings": "Projections +15-25% échanges intra-africains (2040)",
                "verified": "2025-01-11"
            },
            {
                "source": "UNCTAD - Trade Data",
                "url": "https://unctad.org/",
                "verified": "2025-01-11"
            },
            {
                "source": "tralac - Trade Law Centre",
                "url": "https://www.tralac.org/",
                "focus": "GTI, transposition nationale, suivi juridique",
                "verified": "2025-01-11"
            },
            {
                "source": "AfCFTA NTB Platform",
                "url": "https://tradebarriers.africa",
                "status": "Opérationnel",
                "verified": "2025-01-11"
            }
        ],
        "last_updated": datetime.now().isoformat()
    }

@api_router.get("/trade-performance")
async def get_trade_performance():
    """Récupérer les données de performance commerciale 2024 pour tous les pays"""
    
    # Charger les données de commerce enrichies (COMMERCE MONDIAL)
    trade_data = get_all_countries_trade_performance()
    
    return {
        "countries_global": trade_data,
        "data_source": "Observatory of Economic Complexity (OEC) 2024, World Bank, IMF",
        "last_updated": "2024-09-16",
        "year": 2024,
        "trade_type": "global",
        "description": "Commerce total avec tous les partenaires mondiaux (Europe, Asie, Amériques, etc.)"
    }

@api_router.get("/trade-performance-intra-african")
async def get_trade_performance_intra_african():
    """Récupérer les données de commerce INTRA-AFRICAIN uniquement (entre pays africains)"""
    
    # Charger les données de commerce global
    global_trade_data = get_all_countries_trade_performance()
    
    # Calculer le commerce intra-africain (environ 15-17% du commerce global pour la plupart des pays)
    # Source: UNCTAD, AfDB, CEA - Rapport sur l'intégration africaine 2024
    intra_african_percentages = {
        'ZAF': 0.19,  # Afrique du Sud: 19% (forte intégration régionale SADC)
        'EGY': 0.12,  # Égypte: 12% (orientée vers Europe/Asie)
        'NGA': 0.11,  # Nigeria: 11% (orientée vers Europe/Asie pour pétrole)
        'DZA': 0.04,  # Algérie: 4% (très faible, orientée Europe pour gaz)
        'MAR': 0.09,  # Maroc: 9% (orienté Europe)
        'KEN': 0.34,  # Kenya: 34% (hub régional EAC, très intégré)
        'ETH': 0.28,  # Éthiopie: 28% (forte intégration EAC)
        'TZA': 0.32,  # Tanzanie: 32% (forte intégration EAC)
        'UGA': 0.38,  # Ouganda: 38% (très intégré EAC)
        'GHA': 0.42,  # Ghana: 42% (très intégré CEDEAO)
        'CIV': 0.38,  # Côte d'Ivoire: 38% (hub CEDEAO)
        'SEN': 0.31,  # Sénégal: 31% (intégré CEDEAO)
        'CMR': 0.29,  # Cameroun: 29% (intégré CEMAC)
        'AGO': 0.06,  # Angola: 6% (pétrole vers Asie/Europe)
        'TUN': 0.08,  # Tunisie: 8% (orientée Europe)
        'ZWE': 0.48,  # Zimbabwe: 48% (très intégré SADC)
        'ZMB': 0.52,  # Zambie: 52% (très intégré SADC)
        'BWA': 0.65,  # Botswana: 65% (très intégré SADC)
        'MWI': 0.58,  # Malawi: 58% (intégré SADC)
        'NAM': 0.55,  # Namibie: 55% (intégré SADC)
        'RWA': 0.41,  # Rwanda: 41% (intégré EAC)
        'BDI': 0.44,  # Burundi: 44% (intégré EAC)
        'TCD': 0.35,  # Tchad: 35% (intégré CEMAC)
        'NER': 0.33,  # Niger: 33% (intégré CEDEAO)
        'MLI': 0.36,  # Mali: 36% (intégré CEDEAO)
        'BFA': 0.40,  # Burkina Faso: 40% (intégré CEDEAO)
        'MDG': 0.18,  # Madagascar: 18% (insulaire, moins intégré)
        'BEN': 0.35,  # Bénin: 35% (intégré CEDEAO)
        'TGO': 0.37,  # Togo: 37% (intégré CEDEAO)
    }
    
    # Pourcentage par défaut pour les pays non listés
    default_percentage = 0.17  # 17% moyenne africaine
    
    intra_african_data = []
    for country in global_trade_data:
        code = country['code']
        intra_pct = intra_african_percentages.get(code, default_percentage)
        
        intra_african_data.append({
            'country': country['country'],
            'code': country['code'],
            'exports_2024': round(country['exports_2024'] * intra_pct, 2),
            'imports_2024': round(country['imports_2024'] * intra_pct, 2),
            'trade_balance_2024': round(country['trade_balance_2024'] * intra_pct, 2),
            'intra_african_percentage': round(intra_pct * 100, 1),
            'global_exports_2024': country['exports_2024'],
            'global_imports_2024': country['imports_2024']
        })
    
    # Trier par exports intra-africains
    intra_african_data.sort(key=lambda x: x['exports_2024'], reverse=True)
    
    return {
        "countries_intra_african": intra_african_data,
        "data_source": "Calculé à partir OEC 2024 + UNCTAD/AfDB/CEA pourcentages intra-africains",
        "last_updated": "2024-09-16",
        "year": 2024,
        "trade_type": "intra_african",
        "description": "Commerce uniquement entre pays africains (excluant Europe, Asie, Amériques)",
        "average_intra_african_percentage": 17,
        "note": "Les pourcentages intra-africains varient selon l'intégration régionale (SADC, EAC, CEDEAO, etc.)"
    }

# ==========================================
# LOGISTICS ENDPOINTS - MIGRATED
# ==========================================
# All logistics endpoints migrated to /routes/logistics.py:
# - /logistics/ports/* (Maritime ports)
# - /logistics/air/* (Air cargo airports)
# - /logistics/free-zones (Free trade zones)
# - /logistics/land/* (Land corridors)
# - /logistics/statistics


# ==========================================
# ETL PIPELINE ENDPOINTS
# NOTE: /etl/* endpoints MIGRATED to /routes/etl.py
# Routes: POST /etl/run, GET /etl/status, GET /etl/trs-coverage


# ==========================================
# LAND LOGISTICS ENDPOINTS (TERRESTRIAL)
# ==========================================

from logistics_land_data import (
    get_all_corridors,
    get_corridor_by_id,
    get_corridors_by_country,
    get_all_nodes,
    get_nodes_by_type,
    get_osbp_nodes,
    get_all_operators,
    get_operators_by_type,
    get_corridors_statistics,
    search_corridors
)
from production_data import (
    get_value_added,
    get_value_added_by_country,
    get_agriculture_production,
    get_agriculture_by_country,
    get_manufacturing_production,
    get_manufacturing_by_country,
    get_mining_production,
    get_mining_by_country as get_mining_by_country_data,
    get_production_statistics,
    get_country_production_overview
)

# NOTE: /logistics/land/* endpoints MIGRATED to /routes/logistics.py
# Routes: /land/corridors, /land/corridors/{id}, /land/nodes, 
#         /land/operators, /land/search, /land/statistics


# ==========================================
# PRODUCTION ENDPOINTS - MIGRATED
# ==========================================
# All production endpoints migrated to /routes/production.py:
# - /production/statistics
# - /production/macro, /production/macro/{country_iso3}
# - /production/agriculture, /production/agriculture/{country_iso3}
# - /production/manufacturing, /production/manufacturing/{country_iso3}
# - /production/mining, /production/mining/{country_iso3}
# - /production/overview/{country_iso3}


# ==========================================

# ==========================================
# HS CODES (HARMONIZED SYSTEM) ENDPOINTS
# ==========================================
# MIGRATED TO: /routes/hs_codes.py
# Routes: /hs-codes/chapters, /hs-codes/all, /hs-codes/code/{hs_code},
#         /hs-codes/search, /hs-codes/chapter/{chapter}, /hs-codes/statistics


# =============================================================================
# SH6 TARIFFS ENDPOINTS - Tarifs précis par code SH6
# =============================================================================

@api_router.get("/hs6-tariffs/search")
async def search_hs6_tariffs_endpoint(
    q: str = Query(..., description="Search query"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Rechercher des codes SH6 avec leurs tarifs par mot-clé
    Retourne les taux NPF et ZLECAf avec les économies potentielles
    """
    results = search_hs6_tariffs(q, language, limit)
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@api_router.get("/hs6-tariffs/code/{hs6_code}")
async def get_hs6_tariff_endpoint(hs6_code: str, language: str = Query("fr")):
    """
    Obtenir les tarifs détaillés pour un code SH6 spécifique
    Inclut taux NPF, taux ZLECAf, et économies potentielles
    """
    tariff = get_hs6_tariff(hs6_code)
    if not tariff:
        # Fallback vers les informations du code sans tarif spécifique
        hs_info = get_hs6_code(hs6_code, language)
        if hs_info:
            return {
                "code": hs6_code,
                "has_specific_tariff": False,
                "hs_info": hs_info,
                "message": "Pas de tarif SH6 spécifique - utiliser le taux par chapitre"
            }
        raise HTTPException(status_code=404, detail=f"Code SH6 {hs6_code} non trouvé")
    
    desc_key = f"description_{language}"
    return {
        "code": hs6_code,
        "has_specific_tariff": True,
        "description": tariff.get(desc_key, tariff.get("description_fr")),
        "normal_rate": tariff["normal"],
        "normal_rate_pct": f"{tariff['normal'] * 100:.1f}%",
        "zlecaf_rate": tariff["zlecaf"],
        "zlecaf_rate_pct": f"{tariff['zlecaf'] * 100:.1f}%",
        "savings_pct": round((tariff["normal"] - tariff["zlecaf"]) / tariff["normal"] * 100, 1) if tariff["normal"] > 0 else 0,
        "chapter": hs6_code[:2],
        "chapter_name": get_hs_chapters().get(hs6_code[:2], {}).get(language, "")
    }


@api_router.get("/hs6-tariffs/chapter/{chapter}")
async def get_hs6_tariffs_chapter_endpoint(
    chapter: str,
    language: str = Query("fr")
):
    """
    Obtenir tous les codes SH6 avec tarifs spécifiques pour un chapitre
    """
    results = get_hs6_tariffs_by_chapter(chapter)
    chapter_info = get_hs_chapters().get(chapter.zfill(2), {})
    
    return {
        "chapter": chapter.zfill(2),
        "chapter_name": chapter_info.get(language, chapter_info.get("fr", "")),
        "count": len(results),
        "codes": results
    }


@api_router.get("/hs6-tariffs/statistics")
async def get_hs6_tariffs_statistics_endpoint():
    """
    Obtenir les statistiques sur les tarifs SH6 disponibles
    """
    return get_hs6_statistics()


@api_router.get("/hs6-tariffs/products/african-exports")
async def get_african_export_products(language: str = Query("fr")):
    """
    Obtenir la liste des produits africains clés avec leurs tarifs SH6
    Groupés par catégorie (agriculture, mining, manufactured)
    """
    from etl.hs6_tariffs import HS6_TARIFFS_AGRICULTURE, HS6_TARIFFS_MINING, HS6_TARIFFS_MANUFACTURED
    
    desc_key = f"description_{language}"
    
    def format_products(products_dict, category_name):
        return [
            {
                "code": code,
                "description": data.get(desc_key, data.get("description_fr")),
                "normal_rate_pct": f"{data['normal'] * 100:.1f}%",
                "zlecaf_rate_pct": f"{data['zlecaf'] * 100:.1f}%",
                "savings_pct": round((data["normal"] - data["zlecaf"]) / data["normal"] * 100, 1) if data["normal"] > 0 else 0
            }
            for code, data in sorted(products_dict.items())
        ]
    
    return {
        "agriculture": {
            "name_fr": "Produits Agricoles",
            "name_en": "Agricultural Products",
            "count": len(HS6_TARIFFS_AGRICULTURE),
            "products": format_products(HS6_TARIFFS_AGRICULTURE, "agriculture")
        },
        "mining": {
            "name_fr": "Produits Miniers et Énergétiques",
            "name_en": "Mining and Energy Products",
            "count": len(HS6_TARIFFS_MINING),
            "products": format_products(HS6_TARIFFS_MINING, "mining")
        },
        "manufactured": {
            "name_fr": "Produits Manufacturés",
            "name_en": "Manufactured Products",
            "count": len(HS6_TARIFFS_MANUFACTURED),
            "products": format_products(HS6_TARIFFS_MANUFACTURED, "manufactured")
        },
        "total_products": len(HS6_TARIFFS_AGRICULTURE) + len(HS6_TARIFFS_MINING) + len(HS6_TARIFFS_MANUFACTURED)
    }


# =============================================================================
# COUNTRY TARIFFS ENDPOINTS - Taux par pays
# =============================================================================

@api_router.get("/country-tariffs/{country_code}")
async def get_country_tariffs_endpoint(
    country_code: str,
    hs_code: str = Query("18", description="HS code (2-6 digits)")
):
    """
    Obtenir les tarifs douaniers spécifiques à un pays
    Retourne les taux NPF, ZLECAf, TVA et autres taxes
    """
    # Normaliser le code pays
    from etl.country_tariffs_complete import ISO2_TO_ISO3
    if len(country_code) == 2:
        country_iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        country_iso3 = country_code.upper()
    
    # Obtenir les taux
    npf_rate, npf_source = get_tariff_rate_for_country(country_iso3, hs_code)
    zlecaf_rate, zlecaf_source = get_zlecaf_tariff_rate(country_iso3, hs_code)
    vat_rate, vat_source = get_vat_rate_for_country(country_iso3)
    other_rate, other_detail = get_other_taxes_for_country(country_iso3)
    
    # Trouver le pays
    country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == country_iso3), None)
    country_name = country['name'] if country else country_iso3
    
    return {
        "country_code": country_iso3,
        "country_name": country_name,
        "hs_code": hs_code,
        "chapter": hs_code[:2],
        "tariffs": {
            "npf_rate": npf_rate,
            "npf_rate_pct": f"{npf_rate * 100:.1f}%",
            "zlecaf_rate": zlecaf_rate,
            "zlecaf_rate_pct": f"{zlecaf_rate * 100:.1f}%",
            "potential_savings_pct": round((npf_rate - zlecaf_rate) / npf_rate * 100, 1) if npf_rate > 0 else 0
        },
        "taxes": {
            "vat_rate": vat_rate,
            "vat_rate_pct": f"{vat_rate * 100:.1f}%",
            "other_taxes_rate": other_rate,
            "other_taxes_pct": f"{other_rate * 100:.1f}%",
            "other_taxes_detail": other_detail
        },
        "sources": {
            "tariff": npf_source,
            "zlecaf": zlecaf_source,
            "vat": vat_source
        },
        "last_updated": "2025-01"
    }


@api_router.get("/country-tariffs-comparison")
async def compare_country_tariffs(
    countries: str = Query("NGA,GHA,KEN,ZAF,EGY", description="Comma-separated country codes"),
    hs_code: str = Query("18", description="HS code")
):
    """
    Comparer les tarifs entre plusieurs pays africains
    """
    country_list = [c.strip().upper() for c in countries.split(",")]
    
    results = []
    for cc in country_list:
        from etl.country_tariffs_complete import ISO2_TO_ISO3
        if len(cc) == 2:
            iso3 = ISO2_TO_ISO3.get(cc, cc)
        else:
            iso3 = cc
        
        npf_rate, _ = get_tariff_rate_for_country(iso3, hs_code)
        zlecaf_rate, _ = get_zlecaf_tariff_rate(iso3, hs_code)
        vat_rate, _ = get_vat_rate_for_country(iso3)
        other_rate, _ = get_other_taxes_for_country(iso3)
        
        country = next((c for c in AFRICAN_COUNTRIES if c['iso3'] == iso3), None)
        
        results.append({
            "country_code": iso3,
            "country_name": country['name'] if country else iso3,
            "npf_rate_pct": f"{npf_rate * 100:.1f}%",
            "zlecaf_rate_pct": f"{zlecaf_rate * 100:.1f}%",
            "vat_rate_pct": f"{vat_rate * 100:.1f}%",
            "other_taxes_pct": f"{other_rate * 100:.1f}%",
            "total_cost_factor_npf": round(1 + npf_rate + vat_rate * (1 + npf_rate) + other_rate, 3),
            "total_cost_factor_zlecaf": round(1 + zlecaf_rate + vat_rate * (1 + zlecaf_rate) + other_rate, 3)
        })
    
    # Trier par coût total NPF
    results.sort(key=lambda x: x['total_cost_factor_npf'])
    
    return {
        "hs_code": hs_code,
        "chapter": hs_code[:2],
        "countries_compared": len(results),
        "comparison": results,
        "note": "total_cost_factor = multiplicateur du coût d'importation (1.0 = pas de taxes)"
    }


@api_router.get("/all-country-rates")
async def get_all_rates_endpoint():
    """
    Obtenir un aperçu de tous les taux par pays africain
    Pour validation et vérification des données
    """
    return get_all_country_rates()


# =============================================================================
# SH6 TARIFFS BY COUNTRY ENDPOINTS
# =============================================================================

@api_router.get("/country-hs6-tariffs/{country_code}/search")
async def search_country_hs6_endpoint(
    country_code: str,
    q: str = Query(..., description="Search query"),
    language: str = Query("fr", description="Language: fr or en"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Rechercher des codes SH6 avec tarifs réels dans un pays spécifique
    """
    results = search_country_hs6_tariffs(country_code, q, language, limit)
    
    return {
        "country_code": country_code.upper(),
        "query": q,
        "count": len(results),
        "results": results
    }


@api_router.get("/country-hs6-tariffs/{country_code}/{hs6_code}")
async def get_country_hs6_tariff_endpoint(
    country_code: str,
    hs6_code: str,
    language: str = Query("fr")
):
    """
    Obtenir le tarif SH6 réel pour un pays et un code spécifique
    """
    tariff = get_country_hs6_tariff(country_code, hs6_code)
    
    if not tariff:
        # Fallback vers le taux par chapitre
        from etl.country_tariffs_complete import get_tariff_rate_for_country
        chapter_rate, source = get_tariff_rate_for_country(country_code, hs6_code)
        return {
            "country_code": country_code.upper(),
            "hs6_code": hs6_code,
            "has_hs6_specific_rate": False,
            "dd_rate": chapter_rate,
            "dd_rate_pct": f"{chapter_rate * 100:.1f}%",
            "source": source,
            "note": "Taux par chapitre utilisé (pas de tarif SH6 spécifique disponible)"
        }
    
    desc_key = f"description_{language}"
    return {
        "country_code": country_code.upper(),
        "hs6_code": hs6_code,
        "has_hs6_specific_rate": True,
        "dd_rate": tariff["dd"],
        "dd_rate_pct": f"{tariff['dd'] * 100:.1f}%",
        "description": tariff.get(desc_key, tariff.get("description_fr", "")),
        "source": f"Tarif SH6 officiel {country_code.upper()}"
    }


@api_router.get("/country-hs6-tariffs/available")
async def get_available_hs6_tariffs():
    """
    Obtenir la liste des pays avec tarifs SH6 détaillés disponibles
    """
    available = get_available_country_tariffs()
    return {
        "countries_with_hs6_tariffs": len(available),
        "countries": available,
        "note": "Pour les pays non listés, les taux par chapitre sont utilisés"
    }


@api_router.get("/country-hs6-tariffs/{country_code}/all")
async def get_all_country_hs6_tariffs(country_code: str, language: str = Query("fr")):
    """
    Obtenir tous les tarifs SH6 disponibles pour un pays
    """
    from etl.country_hs6_tariffs import COUNTRY_HS6_TARIFFS, ISO2_TO_ISO3
    
    # Normaliser le code pays
    if len(country_code) == 2:
        iso3 = ISO2_TO_ISO3.get(country_code.upper(), country_code.upper())
    else:
        iso3 = country_code.upper()
    
    tariffs = COUNTRY_HS6_TARIFFS.get(iso3, {})
    
    if not tariffs:
        return {
            "country_code": iso3,
            "has_hs6_tariffs": False,
            "count": 0,
            "tariffs": [],
            "note": "Pas de tarifs SH6 spécifiques pour ce pays - utiliser taux par chapitre"
        }
    
    desc_key = f"description_{language}"
    formatted_tariffs = [
        {
            "hs6_code": code,
            "dd_rate": data["dd"],
            "dd_rate_pct": f"{data['dd'] * 100:.1f}%",
            "description": data.get(desc_key, data.get("description_fr", ""))
        }
        for code, data in sorted(tariffs.items())
    ]
    
    return {
        "country_code": iso3,
        "has_hs6_tariffs": True,
        "count": len(formatted_tariffs),
        "tariffs": formatted_tariffs
    }


# =============================================================================
# SOUS-POSITIONS NATIONALES ENDPOINTS (8-12 chiffres)
# =============================================================================

@api_router.get("/tariffs/detailed/{country_code}/{hs_code}")
async def get_detailed_tariff_endpoint(
    country_code: str, 
    hs_code: str, 
    language: str = Query("fr")
):
    """
    Obtenir le tarif détaillé avec toutes les sous-positions pour un pays et code HS
    
    Args:
        country_code: Code ISO3 du pays (ex: NGA, CIV, ZAF)
        hs_code: Code HS (6-12 chiffres)
        language: Langue (fr ou en)
    
    Returns:
        Informations détaillées incluant taux par défaut et sous-positions
    """
    summary = get_tariff_summary(country_code.upper(), hs_code)
    
    if not summary.get("has_detailed_tariffs"):
        raise HTTPException(
            status_code=404, 
            detail=f"Pas de tarifs détaillés pour {country_code.upper()} / {hs_code}. Utiliser l'endpoint /country-hs6-tariffs/{country_code}/{hs_code[:6]}"
        )
    
    # Adapter les descriptions selon la langue
    desc_key = f"description_{language}"
    if language == "en":
        summary["description"] = summary.get("description_en", summary.get("description_fr", ""))
    else:
        summary["description"] = summary.get("description_fr", "")
    
    # Formater les sous-positions avec la bonne langue
    for sp in summary.get("sub_positions", []):
        sp["description"] = sp.get(desc_key, sp.get("description_fr", ""))
    
    return summary


@api_router.get("/tariffs/sub-position/{country_code}/{full_code}")
async def get_sub_position_tariff_endpoint(
    country_code: str, 
    full_code: str,
    language: str = Query("fr")
):
    """
    Obtenir le taux de droits de douane pour une sous-position nationale spécifique
    
    Args:
        country_code: Code ISO3 du pays
        full_code: Code national complet (8-12 chiffres, ex: 8703231000)
    
    Returns:
        Taux DD spécifique à cette sous-position ou taux par défaut
    """
    rate, description, source = get_sub_position_rate(country_code.upper(), full_code)
    
    hs6 = full_code[:6].zfill(6)
    detailed = get_detailed_tariff(country_code.upper(), hs6)
    
    if rate is None:
        # Pas de tarif détaillé, fallback vers tarif SH6 standard
        hs6_tariff = get_country_hs6_tariff(country_code.upper(), hs6)
        if hs6_tariff:
            rate = hs6_tariff["dd"]
            description = hs6_tariff.get(f"description_{language}", hs6_tariff.get("description_fr", ""))
            source = f"Tarif SH6 standard (pas de sous-position)"
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun tarif trouvé pour {country_code.upper()} / {full_code}"
            )
    
    return {
        "country_code": country_code.upper(),
        "full_code": full_code,
        "hs6_code": hs6,
        "dd_rate": rate,
        "dd_rate_pct": f"{rate * 100:.1f}%",
        "description": description,
        "source": source,
        "has_sub_position_match": source.startswith("Sous-position")
    }


@api_router.get("/tariffs/sub-positions/{country_code}/{hs6_code}")
async def get_all_sub_positions_endpoint(
    country_code: str, 
    hs6_code: str,
    language: str = Query("fr")
):
    """
    Obtenir toutes les sous-positions nationales pour un code HS6 dans un pays
    
    Returns:
        Liste des sous-positions avec leurs taux respectifs
    """
    hs6 = hs6_code[:6].zfill(6)
    sub_positions = get_all_sub_positions(country_code.upper(), hs6)
    
    # Obtenir les infos générales du HS6
    detailed = get_detailed_tariff(country_code.upper(), hs6)
    
    if not sub_positions:
        return {
            "country_code": country_code.upper(),
            "hs6_code": hs6,
            "has_sub_positions": False,
            "count": 0,
            "sub_positions": [],
            "note": "Pas de sous-positions détaillées pour ce code dans ce pays"
        }
    
    # Adapter les descriptions selon la langue
    desc_key = f"description_{language}"
    for sp in sub_positions:
        sp["description"] = sp.get(desc_key, sp.get("description_fr", ""))
    
    has_variations, min_rate, max_rate = has_varying_rates(country_code.upper(), hs6)
    
    return {
        "country_code": country_code.upper(),
        "hs6_code": hs6,
        "hs6_description": detailed.get(f"description_{language}", detailed.get("description_fr", "")) if detailed else "",
        "default_dd_rate": detailed.get("default_dd", 0) if detailed else 0,
        "default_dd_rate_pct": f"{detailed.get('default_dd', 0) * 100:.1f}%" if detailed else "N/A",
        "has_sub_positions": True,
        "has_varying_rates": has_variations,
        "rate_range": {
            "min_pct": f"{min_rate * 100:.1f}%",
            "max_pct": f"{max_rate * 100:.1f}%"
        } if has_variations else None,
        "count": len(sub_positions),
        "sub_positions": sub_positions
    }


@api_router.get("/tariffs/detailed-countries")
async def get_detailed_tariff_countries():
    """
    Obtenir la liste des pays avec tarifs détaillés (sous-positions nationales)
    """
    countries_data = {}
    for iso3, tariffs in COUNTRY_HS6_DETAILED.items():
        total_sub_positions = sum(
            len(hs6_data.get("sub_positions", {}))
            for hs6_data in tariffs.values()
        )
        countries_data[iso3] = {
            "hs6_codes_count": len(tariffs),
            "sub_positions_count": total_sub_positions,
            "hs6_codes": list(tariffs.keys())
        }
    
    return {
        "countries_with_detailed_tariffs": len(countries_data),
        "countries": countries_data,
        "note": "Ces pays ont des tarifs avec sous-positions nationales (8-12 chiffres)"
    }


# =============================================================================
# RECHERCHE INTELLIGENTE HS6 + SOUS-POSITIONS
# =============================================================================

@api_router.get("/hs6/search")
async def search_hs6(
    query: str = Query(..., min_length=2, description="Terme de recherche (code ou description)"),
    language: str = Query("fr"),
    limit: int = Query(20, le=50)
):
    """
    Recherche intelligente dans la base HS6
    - Par code (ex: "8703", "870323")
    - Par mot-clé (ex: "voiture", "café", "riz")
    - Par catégorie (ex: "vehicles", "coffee")
    """
    results = search_hs6_codes(query, language, limit)
    return {
        "query": query,
        "count": len(results),
        "results": results
    }


@api_router.get("/hs6/info/{hs_code}")
async def get_hs6_information(
    hs_code: str,
    language: str = Query("fr")
):
    """
    Obtenir les informations complètes d'un code HS6:
    - Description
    - Catégorie
    - Sensibilité ZLECAf
    - Types de sous-positions disponibles
    - Règle d'origine
    """
    info = get_hs6_info(hs_code, language)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Code HS6 {hs_code[:6]} non trouvé dans la base"
        )
    return info


@api_router.get("/hs6/suggestions/{hs_code}")
async def get_hs6_sub_position_suggestions(
    hs_code: str,
    country_code: str = Query(None, description="Code ISO3 du pays pour obtenir les sous-positions nationales"),
    language: str = Query("fr")
):
    """
    Obtenir les suggestions intelligentes de sous-positions pour un code HS6
    
    Retourne:
    - Types de distinctions possibles (neuf/occasion, âge, qualité, etc.)
    - Options avec suffixes de code
    - Si country_code fourni: sous-positions nationales réelles du pays
    """
    hs6 = hs_code[:6].zfill(6)
    
    # Suggestions génériques basées sur la base HS6
    generic_suggestions = get_sub_position_suggestions(hs6, language)
    
    # Si un pays est spécifié, obtenir les sous-positions nationales réelles
    country_sub_positions = []
    if country_code:
        country_sub_positions = get_all_sub_positions(country_code.upper(), hs6)
    
    # Info de base sur le HS6
    hs6_info = get_hs6_info(hs6, language)
    
    return {
        "hs6_code": hs6,
        "description": hs6_info.get("description") if hs6_info else None,
        "category": hs6_info.get("category") if hs6_info else None,
        "generic_suggestions": generic_suggestions,
        "country_code": country_code.upper() if country_code else None,
        "country_sub_positions": country_sub_positions,
        "has_country_specific_rates": len(country_sub_positions) > 0
    }


@api_router.get("/hs6/rule-of-origin/{hs_code}")
async def get_hs6_rule_of_origin(
    hs_code: str,
    language: str = Query("fr")
):
    """
    Obtenir la règle d'origine ZLECAf pour un code HS6
    """
    hs6 = hs_code[:6].zfill(6)
    rule = get_rule_of_origin(hs6, language)
    
    if not rule:
        # Règle par défaut si non trouvée
        return {
            "hs6_code": hs6,
            "type": "substantial_transformation",
            "requirement": "Transformation substantielle - 40% valeur ajoutée africaine" if language == "fr" else "Substantial transformation - 40% African value added",
            "regional_content": 40,
            "note": "Règle par défaut - vérifier auprès des autorités compétentes"
        }
    
    return rule


@api_router.get("/hs6/categories")
async def get_hs6_categories():
    """
    Obtenir toutes les catégories de produits disponibles
    """
    categories = get_all_categories()
    return {
        "count": len(categories),
        "categories": categories
    }


@api_router.get("/hs6/category/{category}")
async def get_hs6_by_category(
    category: str,
    language: str = Query("fr")
):
    """
    Obtenir tous les codes HS6 d'une catégorie
    """
    codes = get_codes_by_category(category, language)
    if not codes:
        raise HTTPException(
            status_code=404,
            detail=f"Catégorie '{category}' non trouvée"
        )
    return {
        "category": category,
        "count": len(codes),
        "codes": codes
    }


@api_router.get("/hs6/statistics")
async def get_hs6_database_statistics():
    """
    Obtenir les statistiques de la base HS6
    """
    stats = get_database_stats()
    
    # Ajouter les stats des sous-positions nationales
    country_stats = {}
    for iso3, tariffs in COUNTRY_HS6_DETAILED.items():
        total_sub = sum(len(hs6_data.get("sub_positions", {})) for hs6_data in tariffs.values())
        country_stats[iso3] = {
            "hs6_codes": len(tariffs),
            "sub_positions": total_sub
        }
    
    total_country_hs6 = sum(v["hs6_codes"] for v in country_stats.values())
    total_country_sub = sum(v["sub_positions"] for v in country_stats.values())
    
    return {
        "hs6_base": {
            "total_codes": stats["total_codes"],
            "with_sub_positions": stats["with_sub_positions"],
            "categories": stats["categories"],
            "sensitivities": stats["sensitivities"]
        },
        "national_sub_positions": {
            "countries_covered": len(country_stats),
            "total_hs6_with_national_rates": total_country_hs6,
            "total_sub_positions": total_country_sub,
            "by_country": country_stats
        }
    }


@api_router.get("/hs6/smart-search")
async def smart_search_with_suggestions(
    query: str = Query(..., min_length=2),
    country_code: str = Query(None),
    language: str = Query("fr"),
    include_sub_positions: bool = Query(True)
):
    """
    Recherche intelligente avec suggestions de sous-positions
    
    Combine:
    - Recherche HS6 par mot-clé
    - Suggestions de sous-positions
    - Sous-positions nationales si pays spécifié
    - Règles d'origine
    """
    # Rechercher les codes HS6
    hs6_results = search_hs6_codes(query, language, limit=10)
    
    # Enrichir chaque résultat avec les sous-positions
    enriched_results = []
    for result in hs6_results:
        enriched = result.copy()
        
        if include_sub_positions and result["has_sub_positions"]:
            # Suggestions génériques
            enriched["sub_position_suggestions"] = get_sub_position_suggestions(result["code"], language)
            
            # Sous-positions nationales si pays fourni
            if country_code:
                country_subs = get_all_sub_positions(country_code.upper(), result["code"])
                enriched["country_sub_positions"] = country_subs
                enriched["has_varying_rates"] = len(country_subs) > 1
        
        # Règle d'origine
        rule = get_rule_of_origin(result["code"], language)
        if rule:
            enriched["rule_of_origin"] = rule
        
        enriched_results.append(enriched)
    
    return {
        "query": query,
        "country_code": country_code.upper() if country_code else None,
        "count": len(enriched_results),
        "results": enriched_results
    }


# FAOSTAT ENRICHED DATA ENDPOINTS
# ==========================================

from etl import (
    get_faostat_country_data,
    get_africa_top_producers,
    get_all_commodities,
    get_all_faostat_data,
    get_fisheries_rankings,
    get_faostat_statistics,
    get_unido_country_data,
    get_all_unido_data,
    get_isic_sectors,
    get_countries_by_mva,
    get_sector_analysis,
    get_unido_statistics
)

@api_router.get("/production/faostat/statistics")
async def get_faostat_stats():
    """
    Get global FAOSTAT statistics for all African countries
    """
    return get_faostat_statistics()

@api_router.get("/production/faostat/commodities")
async def get_faostat_commodities():
    """
    Get list of all agricultural commodities available in FAOSTAT data
    """
    return {"commodities": get_all_commodities()}

@api_router.get("/production/faostat/top-producers/{commodity}")
async def get_commodity_top_producers(commodity: str):
    """
    Get top African producers for a specific commodity
    """
    producers = get_africa_top_producers(commodity)
    if not producers:
        return {"message": f"No ranking data available for '{commodity}'", "commodity": commodity, "producers": []}
    return {"commodity": commodity, "producers": producers}

@api_router.get("/production/faostat/fisheries")
async def get_fisheries_data():
    """
    Get fisheries and aquaculture rankings for Africa
    """
    return get_fisheries_rankings()

@api_router.get("/production/faostat/{country_iso3}")
async def get_faostat_country(country_iso3: str):
    """
    Get detailed FAOSTAT agricultural data for a specific country
    Includes: main crops, production, evolution, livestock, fisheries, key indicators
    """
    data = get_faostat_country_data(country_iso3.upper())
    if not data:
        return {"message": f"No FAOSTAT data available for country '{country_iso3}'", "country_iso3": country_iso3}
    return data

@api_router.get("/production/faostat")
async def get_all_faostat():
    """
    Get all FAOSTAT data for all African countries
    """
    return get_all_faostat_data()


# ==========================================
# UNIDO ENRICHED DATA ENDPOINTS
# ==========================================

@api_router.get("/production/unido/statistics")
async def get_unido_stats():
    """
    Get global UNIDO industrial statistics for Africa
    """
    return get_unido_statistics()

@api_router.get("/production/unido/isic-sectors")
async def get_unido_isic_sectors():
    """
    Get ISIC Rev.4 sector classification
    """
    return {"sectors": get_isic_sectors()}

@api_router.get("/production/unido/ranking")
async def get_unido_mva_ranking():
    """
    Get countries ranked by Manufacturing Value Added (MVA)
    """
    return {"ranking": get_countries_by_mva()}

@api_router.get("/production/unido/sector-analysis/{isic_code}")
async def get_unido_sector(isic_code: str):
    """
    Get analysis of a specific ISIC sector across all African countries
    """
    analysis = get_sector_analysis(isic_code)
    sectors = get_isic_sectors()
    sector_name = sectors.get(isic_code, "Unknown")
    return {
        "isic_code": isic_code,
        "sector_name": sector_name,
        "countries": analysis
    }

@api_router.get("/production/unido/{country_iso3}")
async def get_unido_country(country_iso3: str):
    """
    Get detailed UNIDO industrial data for a specific country
    Includes: MVA, top sectors, growth rate, key products, industrial zones
    """
    data = get_unido_country_data(country_iso3.upper())
    if not data:
        return {"message": f"No UNIDO data available for country '{country_iso3}'", "country_iso3": country_iso3}
    return data

@api_router.get("/production/unido")
async def get_all_unido():
    """
    Get all UNIDO industrial data for all African countries
    """
    return get_all_unido_data()


# ==========================================
# TRADE PRODUCTS ENDPOINTS (TOP 20)
# ==========================================

from etl.trade_products_data import (
    get_top_imports_from_world,
    get_top_exports_to_world,
    get_top_intra_african_imports,
    get_top_intra_african_exports,
    get_all_trade_products_data,
    get_trade_summary
)
from etl.translations import translate_product, translate_country_list

def translate_products_list(products: list, language: str = 'fr') -> list:
    """Translate product names and country names in a products list"""
    if language == 'fr':
        return products
    
    translated = []
    for product in products:
        translated_product = product.copy()
        translated_product['product'] = translate_product(product['product'], language)
        if 'top_importers' in product:
            translated_product['top_importers'] = translate_country_list(product['top_importers'], language)
        if 'top_exporters' in product:
            translated_product['top_exporters'] = translate_country_list(product['top_exporters'], language)
        if 'main_origins' in product:
            translated_product['main_origins'] = translate_country_list(product['main_origins'], language)
        translated.append(translated_product)
    return translated

@api_router.get("/statistics/trade-products/summary")
async def get_trade_products_summary():
    """
    Get summary of trade products data
    """
    return get_trade_summary()

@api_router.get("/statistics/trade-products/imports-world")
async def get_imports_from_world(lang: str = 'fr'):
    """
    Get Top 20 products imported by Africa from the world
    """
    titles = {
        'fr': "Top 20 Produits Importés par l'Afrique du Monde",
        'en': "Top 20 Products Imported by Africa from the World"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/ITC Trade Map 2023",
        "year": 2023,
        "products": translate_products_list(get_top_imports_from_world(), lang)
    }

@api_router.get("/statistics/trade-products/exports-world")
async def get_exports_to_world(lang: str = 'fr'):
    """
    Get Top 20 products exported by Africa to the world
    """
    titles = {
        'fr': "Top 20 Produits Exportés par l'Afrique vers le Monde",
        'en': "Top 20 Products Exported by Africa to the World"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/ITC Trade Map 2023",
        "year": 2023,
        "products": translate_products_list(get_top_exports_to_world(), lang)
    }

@api_router.get("/statistics/trade-products/intra-imports")
async def get_intra_imports(lang: str = 'fr'):
    """
    Get Top 20 products imported in intra-African trade
    """
    titles = {
        'fr': "Top 20 Produits Importés en Commerce Intra-Africain",
        'en': "Top 20 Products Imported in Intra-African Trade"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/AfCFTA Secretariat 2023",
        "year": 2023,
        "products": translate_products_list(get_top_intra_african_imports(), lang)
    }

@api_router.get("/statistics/trade-products/intra-exports")
async def get_intra_exports(lang: str = 'fr'):
    """
    Get Top 20 products exported in intra-African trade
    """
    titles = {
        'fr': "Top 20 Produits Exportés en Commerce Intra-Africain",
        'en': "Top 20 Products Exported in Intra-African Trade"
    }
    return {
        "title": titles.get(lang, titles['fr']),
        "source": "UNCTAD/AfCFTA Secretariat 2023",
        "year": 2023,
        "products": translate_products_list(get_top_intra_african_exports(), lang)
    }

@api_router.get("/statistics/trade-products")
async def get_all_trade_products():
    """
    Get all trade products data (imports, exports, intra-African)
    """
    return get_all_trade_products_data()


# =============================================================================
# UNCTAD DATA ENDPOINTS
# =============================================================================

from etl.unctad_data import (
    get_unctad_port_statistics,
    get_unctad_trade_flows,
    get_unctad_lsci,
    get_all_unctad_data
)

@api_router.get("/statistics/unctad/ports")
async def get_unctad_ports():
    """
    Get UNCTAD port statistics for African ports
    Source: UNCTAD Review of Maritime Transport 2023
    """
    return get_unctad_port_statistics()

@api_router.get("/statistics/unctad/trade-flows")
async def get_unctad_flows():
    """
    Get UNCTAD trade flow statistics
    Source: UNCTAD COMTRADE 2023
    """
    return get_unctad_trade_flows()

@api_router.get("/statistics/unctad/lsci")
async def get_unctad_liner_connectivity():
    """
    Get UNCTAD Liner Shipping Connectivity Index for Africa
    Source: UNCTAD 2023
    """
    return get_unctad_lsci()

@api_router.get("/statistics/unctad")
async def get_all_unctad():
    """
    Get all UNCTAD data (ports, trade flows, LSCI)
    """
    return get_all_unctad_data()


# =====================================================
# ENDPOINTS ACTUALITÉS ÉCONOMIQUES AFRICAINES
# =====================================================
# MIGRATED TO: /routes/news.py
# Routes: /news, /news/by-region, /news/by-category


# =====================================================
# ENDPOINTS STATISTIQUES COMMERCIALES OEC
# =====================================================
# MIGRATED TO: /routes/oec.py  
# Routes: /oec/countries, /oec/years, /oec/exports/{country_iso3},
#         /oec/imports/{country_iso3}, /oec/product/{hs_code},
#         /oec/product/{hs_code}/africa, /oec/bilateral/{exporter_iso3}/{importer_iso3}


# =============================================================================
# REGISTER MODULAR ROUTES
# =============================================================================
# Routes migrated to /routes/ module:
# - /health, /health/status (health.py)
# - /news, /news/by-region, /news/by-category (news.py)
# - /oec/* (oec.py) - OEC Trade Statistics endpoints
# - /hs-codes/* (hs_codes.py) - HS Code browser and search
# - /substitution/* (substitution.py) - Trade substitution analysis
# 
# Note: Legacy routes in this file will be migrated progressively
# =============================================================================

from routes.substitution import register_routes as register_substitution_routes

try:
    from routers.export_router import init_db as init_export_db
    init_export_db(db)
except ImportError:
    pass

try:
    from services.crawl_orchestrator import init_orchestrator
    init_orchestrator(
        db_client=client,
        notification_manager=notification_manager,
        max_concurrency=5,
    )
    logging.info("Crawl orchestrator initialized")
except Exception as e:
    logging.warning(f"Crawl orchestrator initialization failed: {e}")

@app.on_event("startup")
async def startup_load_tariff_data():
    """Load collected tariff data on startup for the calculator"""
    try:
        crawled_service.load()
        crawled_stats = crawled_service.get_stats()
        if crawled_stats["total_positions"] > 0:
            logging.info(f"Crawled data service ready: {crawled_stats['countries']} countries, "
                         f"{crawled_stats['total_positions']:,} authentic positions")
        else:
            logging.info("No crawled data found yet.")
    except Exception as e:
        logging.warning(f"Crawled data service startup: {e}")

    try:
        tariff_service.load()
        stats = tariff_service.get_stats()
        if stats["countries"] > 0:
            logging.info(f"Tariff data service ready: {stats['countries']} countries, "
                         f"{stats['total_positions']:,} positions loaded")
        else:
            logging.info("No pre-collected tariff data found. Running initial collection...")
            from services.tariff_data_collector import TariffDataCollector
            collector = TariffDataCollector()
            result = collector.collect_all_countries()
            logging.info(f"Initial collection complete: {result['total_tariff_lines']} lines for {result['countries_processed']} countries")
            tariff_service.load(force=True)
            stats = tariff_service.get_stats()
            logging.info(f"Tariff data service ready after collection: {stats['countries']} countries")
    except Exception as e:
        logging.warning(f"Tariff data service startup: {e}. Calculator will use ETL fallback.")

register_routes(api_router)
register_substitution_routes(api_router)

# Include the router in the main app
app.include_router(api_router)

from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

build_dir = Path(__file__).parent.parent / "frontend" / "build"
if build_dir.exists():
    app.mount("/static", StaticFiles(directory=str(build_dir / "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        file_path = build_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(build_dir / "index.html"))