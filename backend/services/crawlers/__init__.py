"""
Services/Crawlers sub-package.
Provides the DZA async tariff connector, crawler manager, and data validator.

North African tariff crawlers service package.

Provides BaseScraper-compatible adapters and orchestration for:
- DZA (Algeria) - conformepro.dz / douane.gov.dz
- MAR (Morocco) - douane.gov.ma / ADIL portal
- EGY (Egypt) - egyptariffs.com / customs.gov.eg
- TUN (Tunisia) - douane.finances.tn / tarifweb2025
"""

from .base_north_africa_crawler import NorthAfricaCrawlerBase
from .dza_tariff_connector import DZATariffConnector
from .mar_tariff_crawler import MARTariffCrawler
from .egy_tariff_crawler import EGYTariffCrawler
from .tun_tariff_crawler import TUNTariffCrawler
from .regional_orchestrator import NorthAfricaOrchestrator, get_north_africa_orchestrator
from .cross_validator import NorthAfricaCrossValidator

__all__ = [
    "NorthAfricaCrawlerBase",
    "DZATariffConnector",
    "MARTariffCrawler",
    "EGYTariffCrawler",
    "TUNTariffCrawler",
    "NorthAfricaOrchestrator",
    "get_north_africa_orchestrator",
    "NorthAfricaCrossValidator",
]
