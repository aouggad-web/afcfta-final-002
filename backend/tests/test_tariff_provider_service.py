import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from services.tariff_provider_service import TariffProviderService


class _StubPostgres:
    def __init__(self):
        self._countries = []
        self._summary = None
        self._line = None
        self._sub_positions = []
        self._search = []

    def get_countries(self):
        return self._countries

    def get_country_summary(self, _country):
        return self._summary

    def get_tariff_line(self, _country, _hs):
        return self._line

    def get_sub_positions(self, _country, _hs6):
        return self._sub_positions

    def search_commodities(self, _country, _query, _limit, _language):
        return self._search


def test_provider_uses_postgres_countries(monkeypatch):
    postgres = _StubPostgres()
    postgres._countries = [
        {"iso3": "MAR", "name_fr": "Maroc", "vat_rate": 20, "total_positions": 100}
    ]

    monkeypatch.setattr(
        "services.tariff_provider_service.authentic_service.get_available_countries",
        lambda: [{"iso3": "FALLBACK"}],
    )

    service = TariffProviderService(postgres_factory=lambda: postgres)
    countries = service.get_available_countries()

    assert len(countries) == 1
    assert countries[0]["iso3"] == "MAR"
    assert countries[0]["source"] == "postgres"


def test_provider_falls_back_when_postgres_unavailable(monkeypatch):
    fallback = [{"iso3": "NGA", "source": "authentic"}]
    monkeypatch.setattr(
        "services.tariff_provider_service.authentic_service.get_available_countries",
        lambda: fallback,
    )

    service = TariffProviderService(postgres_factory=lambda: (_ for _ in ()).throw(RuntimeError("no db")))
    countries = service.get_available_countries()

    assert countries == fallback


def test_provider_prefers_postgres_sub_positions(monkeypatch):
    postgres = _StubPostgres()
    postgres._sub_positions = [
        {"code": "18010010", "digits": 8, "description_fr": "Test", "description_en": "Test", "dd": 10}
    ]
    monkeypatch.setattr(
        "services.tariff_provider_service.authentic_service.get_sub_positions",
        lambda _country, _hs6: [],
    )

    service = TariffProviderService(postgres_factory=lambda: postgres)
    sub_positions = service.get_sub_positions("MAR", "180100")

    assert len(sub_positions) == 1
    assert sub_positions[0]["dd_rate"] == 10
    assert sub_positions[0]["source"] == "postgres"


def test_provider_falls_back_for_tariff_line(monkeypatch):
    postgres = _StubPostgres()
    postgres._line = None
    fallback_line = {"hs6": "180100", "source": "authentic"}
    monkeypatch.setattr(
        "services.tariff_provider_service.authentic_service.get_tariff_line",
        lambda _country, _hs_code: fallback_line,
    )

    service = TariffProviderService(postgres_factory=lambda: postgres)
    result = service.get_tariff_line("MAR", "180100")

    assert result == fallback_line


def test_provider_search_uses_postgres_first(monkeypatch):
    postgres = _StubPostgres()
    postgres._search = [
        {"hs6": "180100", "code": "18010010", "description": "Cacao", "dd_rate": 20, "zlecaf_rate": 0, "savings": 20}
    ]
    monkeypatch.setattr(
        "services.tariff_provider_service.authentic_service.search_tariff_lines",
        lambda *_args, **_kwargs: [],
    )

    service = TariffProviderService(postgres_factory=lambda: postgres)
    results = service.search_tariff_lines("MAR", "cacao", "fr", 20)

    assert len(results) == 1
    assert results[0]["national_code"] == "18010010"
    assert results[0]["source"] == "postgres"
