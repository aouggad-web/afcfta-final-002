"""
Conftest des tests backend — résolution de l'URL du serveur live et skip propre.

Problème corrigé : la suite complète produisait des centaines d'échecs
parasites selon l'environnement —
  - `MissingSchema: Invalid URL '/api/...'` quand REACT_APP_BACKEND_URL est
    vide (12 fichiers construisent leur BASE_URL sans repli) ;
  - `ProxyError`/timeouts quand le repli codé en dur pointe vers le serveur
    de préversion distant, injoignable hors d'Emergent.

Principe : un test d'intégration live qui n'a AUCUN serveur joignable doit
être SKIPPÉ (état d'environnement), pas FAILÉ (ce n'est pas une régression
de code). Ici on résout une seule fois la meilleure URL joignable
(REACT_APP_BACKEND_URL explicite, sinon localhost:BACKEND_PORT, 8001, 8000),
on la propage via l'environnement AVANT l'import des modules de test (leurs
BASE_URL calculés à l'import deviennent donc corrects), et si rien ne répond
on skippe les modules qui dépendent d'un serveur live.
"""

import os

import pytest

_PROBE_TIMEOUT_S = 2.0

_RETIRED_UNSOURCED_FORMALITY_TESTS = {
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_mar_data_has_multiple_document_types",
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_tun_data_has_multiple_document_types",
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_dza_data_formalities_unchanged",
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_mar_livestock_lines_have_veterinary_doc",
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_tun_livestock_lines_have_veterinary_doc",
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_mar_pharma_lines_have_health_ministry_doc",
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_tun_pharma_lines_have_health_ministry_doc",
    "backend/tests/test_north_africa_tariff_system.py::TestAdministrativeFormalities::test_every_line_has_at_least_one_formality",
}

_RETIRED_UNSOURCED_AFRICA_TESTS = {
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_every_country_has_multi_doc_formalities",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_pharma_lines_have_pharmauth",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_animal_lines_have_vetcert",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_food_lines_have_phytocert",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_hydro_lines_have_energyauth",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_arms_lines_have_armauth",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_no_country_has_empty_formalities",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_dza_formalities_preserved",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_cod_all_lines_have_occdecl",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_cod_pharma_lines_have_both_pharmauth_and_occdecl",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_cod_animal_lines_have_vetcert_and_occdecl",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_cod_vehicle_lines_have_stdcert_and_occdecl",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_nga_all_lines_have_formm",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_egy_manufactured_lines_have_goeic",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_eth_manufactured_lines_have_ethpermit",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_eth_processed_food_has_ethpermit",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_cemac_countries_have_ectn",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_gab_all_lines_have_ectn",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_caf_all_lines_have_ectn",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_cog_all_lines_have_ectn",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_gnq_all_lines_have_ectn",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_tcd_all_lines_have_ectn",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_eth_sur_observation_descriptive",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_cmr_tci_observation_descriptive",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_mar_tpi_observation_descriptive",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_mar_other_taxes_rate_non_zero",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_ken_other_taxes_rate_reflects_idf",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_eth_sur_rate_is_ten_percent",
    "backend/tests/test_north_africa_tariff_system.py::TestAllAfricaFormalities::test_gab_other_taxes_rate_non_zero",
}

_RETIRED_UNSOURCED_IMPDEC_PLATFORM_TESTS = {
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_eth_crawled_no_mocked_910",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_sdn_crawled_no_mocked_910",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_stp_crawled_no_mocked_910",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_nga_crawled_no_mocked_910",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_ken_crawled_no_mocked_910",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_zaf_crawled_no_mocked_910",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_all_crawled_countries_have_impdec",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_dza_910_is_legitimate",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_mar_910_is_legitimate",
    "backend/tests/test_north_africa_tariff_system.py::TestNoMockedData::test_tun_910_is_legitimate",
    "backend/tests/test_north_africa_tariff_system.py::TestCustomsPlatform::test_formality_codes_are_platform_agnostic",
}

_FORMALITY_REPLACEMENT_REASON = (
    "Assertion historique retirée : elle imposait une couverture documentaire ou un "
    "code sans preuve source par ligne. Remplacée par les tests fail-closed et de "
    "provenance dans test_formality_provenance_lot1a.py."
)

_AFRICA_REPLACEMENT_REASON = (
    "Assertion africaine retirée : elle généralisait un document, une autorité, une "
    "observation ou un taux sans preuve officielle liée à la ligne. Remplacée par les "
    "29 contrats fail-closed de test_formality_provenance_lot1b.py."
)

_IMPDEC_PLATFORM_REPLACEMENT_REASON = (
    "Assertion retirée : elle imposait ou légitimait IMPDEC/910 sur la seule base du "
    "pays ou de la plateforme douanière. Remplacée par les 11 contrats de provenance "
    "de test_formality_provenance_lot1c.py."
)


def _probe(base_url: str) -> bool:
    """Vrai si un serveur HTTP répond (peu importe le code de statut)."""
    import requests

    try:
        requests.get(f"{base_url}/api/", timeout=_PROBE_TIMEOUT_S)
        return True
    except Exception:
        return False


def _resolve_backend_url():
    explicit = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")
    candidates = []
    if explicit:
        candidates.append(explicit)
    port_env = os.environ.get("BACKEND_PORT", "").strip()
    for port in [port_env, "8001", "8000"]:
        if port:
            url = f"http://localhost:{port}"
            if url not in candidates:
                candidates.append(url)
    for base in candidates:
        if _probe(base):
            return base, True
    return explicit, False


BACKEND_URL, BACKEND_REACHABLE = _resolve_backend_url()
if BACKEND_URL:
    # Propagé avant l'import des modules de test : leurs
    # `BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "")` deviennent
    # absolus et pointent sur le serveur réellement joignable.
    os.environ["REACT_APP_BACKEND_URL"] = BACKEND_URL


def _module_needs_live_server(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            return "REACT_APP_BACKEND_URL" in fh.read()
    except OSError:
        return False


_live_module_cache: dict = {}


def pytest_collection_modifyitems(config, items):
    retired_lot1a = pytest.mark.skip(reason=_FORMALITY_REPLACEMENT_REASON)
    retired_lot1b = pytest.mark.skip(reason=_AFRICA_REPLACEMENT_REASON)
    retired_lot1c = pytest.mark.skip(reason=_IMPDEC_PLATFORM_REPLACEMENT_REASON)
    live_server_missing = pytest.mark.skip(
        reason="Aucun serveur backend joignable (REACT_APP_BACKEND_URL / "
        "localhost:8001 / localhost:8000) — test d'intégration live skippé, "
        "pas une régression de code."
    )

    for item in items:
        if item.nodeid in _RETIRED_UNSOURCED_FORMALITY_TESTS:
            item.add_marker(retired_lot1a)
        if item.nodeid in _RETIRED_UNSOURCED_AFRICA_TESTS:
            item.add_marker(retired_lot1b)
        if item.nodeid in _RETIRED_UNSOURCED_IMPDEC_PLATFORM_TESTS:
            item.add_marker(retired_lot1c)

        if BACKEND_REACHABLE:
            continue

        path = str(item.fspath)
        if path not in _live_module_cache:
            _live_module_cache[path] = _module_needs_live_server(path)
        if _live_module_cache[path]:
            item.add_marker(live_server_missing)
