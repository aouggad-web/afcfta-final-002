"""
North Africa (UMA/AMU) Regional Crawlers Package.

Covers all 7 UMA/AMU + extended North African countries:
  MAR - Morocco (reference country)
  EGY - Egypt
  TUN - Tunisia
  DZA - Algeria
  LBY - Libya
  SDN - Sudan
  MRT - Mauritania
"""

from .uma_constants import UMA_COUNTRIES, UMA_TRADE_BLOCS, NORTH_AFRICA_EXTENDED
from .tariff_structures import MOROCCO_TARIFFS, get_country_tariff_profile
from .investment_zones import get_investment_zones, get_all_sez_data

__all__ = [
    "UMA_COUNTRIES",
    "UMA_TRADE_BLOCS",
    "NORTH_AFRICA_EXTENDED",
    "MOROCCO_TARIFFS",
    "get_country_tariff_profile",
    "get_investment_zones",
    "get_all_sez_data",
]
