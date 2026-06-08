"""
Tariff provider facade.

Priority order for app-facing tariff data:
1. PostgreSQL service
2. Authentic tariff service orchestration
3. Legacy ETL dictionaries/files as fallback through authentic service
"""

from typing import Callable, Dict, List, Optional
import logging

from services import authentic_tariff_service as authentic_service

logger = logging.getLogger(__name__)


class TariffProviderService:
    """Provider abstraction with PostgreSQL-first runtime policy."""

    def __init__(self, postgres_factory: Optional[Callable] = None):
        self._postgres_factory = postgres_factory
        self._postgres_service = None
        self._postgres_attempted = False

    def _get_postgres(self):
        if self._postgres_attempted:
            return self._postgres_service
        self._postgres_attempted = True

        try:
            factory = self._postgres_factory
            if factory is None:
                from services.postgres_tariff_service import get_postgres_tariff_service
                factory = get_postgres_tariff_service
            self._postgres_service = factory()
        except Exception as exc:
            logger.info("PostgreSQL tariff provider unavailable, using authentic fallback: %s", exc)
            self._postgres_service = None
        return self._postgres_service

    def get_available_countries(self) -> List[Dict]:
        postgres = self._get_postgres()
        if postgres:
            countries = postgres.get_countries()
            if countries:
                return [
                    {
                        "iso3": row.get("iso3"),
                        "name": row.get("name_fr") or row.get("name_en") or row.get("iso3"),
                        "total_lines": row.get("total_positions") or 0,
                        "total_positions": row.get("total_positions") or 0,
                        "vat_rate": row.get("vat_rate") or 0,
                        "data_format": "postgres_v1",
                        "source": "postgres",
                    }
                    for row in countries
                ]
        return authentic_service.get_available_countries()

    def get_country_summary(self, country_iso3: str) -> Optional[Dict]:
        country = country_iso3.upper()
        postgres = self._get_postgres()
        if postgres:
            summary = postgres.get_country_summary(country)
            if summary:
                return summary
        return authentic_service.get_country_summary(country)

    def get_tariff_line(self, country_iso3: str, hs_code: str) -> Optional[Dict]:
        country = country_iso3.upper()
        postgres = self._get_postgres()
        if postgres:
            tariff_line = postgres.get_tariff_line(country, hs_code)
            if tariff_line:
                return tariff_line
        return authentic_service.get_tariff_line(country, hs_code)

    def get_sub_positions(self, country_iso3: str, hs6: str) -> List[Dict]:
        country = country_iso3.upper()
        hs6_code = hs6[:6]
        postgres = self._get_postgres()
        if postgres:
            sub_positions = postgres.get_sub_positions(country, hs6_code)
            if sub_positions:
                return [
                    {
                        "code": sp.get("code"),
                        "national_code": sp.get("code"),
                        "digits": sp.get("digits"),
                        "description_fr": sp.get("description_fr"),
                        "description_en": sp.get("description_en"),
                        "dd": sp.get("dd", 0),
                        "dd_rate": sp.get("dd", 0),
                        "zlecaf_rate": sp.get("zlecaf_rate", 0),
                        "savings": sp.get("savings", 0),
                        "unit": sp.get("unit"),
                        "source": "postgres",
                    }
                    for sp in sub_positions
                ]
        return authentic_service.get_sub_positions(country, hs6_code)

    def search_tariff_lines(self, country_iso3: str, query: str, language: str = "fr", limit: int = 20) -> List[Dict]:
        country = country_iso3.upper()
        postgres = self._get_postgres()
        if postgres:
            results = postgres.search_commodities(country, query, limit, language)
            if results:
                return [
                    {
                        "hs6": row.get("hs6"),
                        "national_code": row.get("code"),
                        "description_fr": row.get("description"),
                        "description_en": row.get("description"),
                        "dd_rate": row.get("dd_rate"),
                        "zlecaf_rate": row.get("zlecaf_rate"),
                        "savings": row.get("savings"),
                        "source": "postgres",
                    }
                    for row in results
                ]
        return authentic_service.search_tariff_lines(country, query, language, limit)


_tariff_provider = None


def get_tariff_provider_service() -> TariffProviderService:
    """Get singleton TariffProviderService instance."""
    global _tariff_provider
    if _tariff_provider is None:
        _tariff_provider = TariffProviderService()
    return _tariff_provider
