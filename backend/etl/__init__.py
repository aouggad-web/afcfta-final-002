"""
ETL Package - Production Africaine
===================================
Données enrichies pour l'analyse de production:
- Ports africains et logistique maritime
- Production agricole FAOSTAT
- Production industrielle UNIDO
"""

from .faostat_data import (
    AFRICA_TOP_PRODUCERS,
    FAOSTAT_AGRICULTURE_DATA,
    FISHERIES_TOP_PRODUCERS,
    get_africa_top_producers,
    get_all_commodities,
    get_all_faostat_data,
    get_countries_with_data,
    get_faostat_country_data,
    get_faostat_statistics,
    get_fisheries_rankings,
)
from .ports_etl import PortsETL, run_etl
from .trs_official_data import GLOBAL_BENCHMARKS, LPI_2023_DATA, TRS_OFFICIAL_DATA
from .unido_data import (
    ISIC_SECTORS,
    UNIDO_INDUSTRY_DATA,
    get_all_unido_data,
    get_countries_by_mva,
    get_isic_sectors,
    get_sector_analysis,
    get_unido_country_data,
    get_unido_statistics,
)

__all__ = [
    # Ports
    "PortsETL",
    "run_etl",
    "TRS_OFFICIAL_DATA",
    "LPI_2023_DATA",
    "GLOBAL_BENCHMARKS",
    # FAOSTAT
    "FAOSTAT_AGRICULTURE_DATA",
    "AFRICA_TOP_PRODUCERS",
    "FISHERIES_TOP_PRODUCERS",
    "get_faostat_country_data",
    "get_africa_top_producers",
    "get_all_commodities",
    "get_countries_with_data",
    "get_all_faostat_data",
    "get_fisheries_rankings",
    "get_faostat_statistics",
    # UNIDO
    "UNIDO_INDUSTRY_DATA",
    "ISIC_SECTORS",
    "get_unido_country_data",
    "get_all_unido_data",
    "get_isic_sectors",
    "get_countries_by_mva",
    "get_sector_analysis",
    "get_unido_statistics",
]
