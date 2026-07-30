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

_FORMALITY_REPLACEMENT_REASON = (
    "Assertion historique retirée : elle imposait une couverture documentaire ou un "
    "code sans preuve source par ligne. Remplacée par les tests fail-closed et de "
    "provenance dans test_formality_provenance_lot1a.py."
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
    retired = pytest.mark.skip(reason=_FORMALITY_REPLACEMENT_REASON)
    live_server_missing = pytest.mark.skip(
        reason="Aucun serveur backend joignable (REACT_APP_BACKEND_URL / "
        "localhost:8001 / localhost:8000) — test d'intégration live skippé, "
        "pas une régression de code."
    )

    for item in items:
        if item.nodeid in _RETIRED_UNSOURCED_FORMALITY_TESTS:
            item.add_marker(retired)

        if BACKEND_REACHABLE:
            continue

        path = str(item.fspath)
        if path not in _live_module_cache:
            _live_module_cache[path] = _module_needs_live_server(path)
        if _live_module_cache[path]:
            item.add_marker(live_server_missing)
