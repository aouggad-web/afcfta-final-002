"""
Services/Crawlers sub-package.
North African tariff crawlers service package.

Provides BaseScraper-compatible adapters and orchestration for:
- MAR (Morocco) - douane.gov.ma / ADIL portal
- EGY (Egypt) - egyptariffs.com / customs.gov.eg
- TUN (Tunisia) - douane.finances.tn / tarifweb2025
"""

from .base_north_africa_crawler import NorthAfricaCrawlerBase
from .cross_validator import NorthAfricaCrossValidator
from .egy_tariff_crawler import EGYTariffCrawler
from .mar_tariff_crawler import MARTariffCrawler
from .regional_orchestrator import NorthAfricaOrchestrator, get_north_africa_orchestrator
from .tun_tariff_crawler import TUNTariffCrawler

__all__ = [
    "NorthAfricaCrawlerBase",
    "MARTariffCrawler",
    "EGYTariffCrawler",
    "TUNTariffCrawler",
    "NorthAfricaOrchestrator",
    "get_north_africa_orchestrator",
    "NorthAfricaCrossValidator",
]
