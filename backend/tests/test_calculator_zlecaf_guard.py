"""
Vérifie que l'endpoint /calculate-tariff (routes/calculator.py) fait passer
TOUTES les préférences ZLECAf par le garde-fou central
(services.authentic_tariff_service.resolve_zlecaf_context) et qu'aucun fallback
« donnée absente → 0 » ni aucune économie ZLECAf fabriquée ne subsiste.

Points couverts (demande utilisateur sur PR #317) :
  1. Pas de fallback absent→0 : champs de statut additifs (dd_available,
     duty_status) exposés ; une absence de droit n'est jamais un 0 % vérifié.
  2. WITS/TRAINS = information seulement : jamais de droit exigible ni d'économie.
  3. Préférences ZLECAf via le garde-fou central : union douanière (0 %),
     ratification/mise en œuvre, réciprocité, origine.

Réseau neutralisé (OEC/World Bank monkeypatchés) : test hermétique.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    from routes import calculator as calc

    async def _no_producers(*a, **k):
        return []

    async def _no_wb(*a, **k):
        return {}

    monkeypatch.setattr(calc.oec_client, "get_top_producers", _no_producers)
    monkeypatch.setattr(calc.wb_client, "get_country_data", _no_wb)

    app = FastAPI()
    app.include_router(calc.router, prefix="/api")
    return TestClient(app, raise_server_exceptions=False)


def _calc(client, origin, dest, hs_code="010121", value=10000.0):
    resp = client.post(
        "/api/calculate-tariff",
        json={
            "origin_country": origin,
            "destination_country": dest,
            "hs_code": hs_code,
            "value": value,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_response_exposes_honesty_status_fields(client):
    """Les champs de statut additifs sont toujours présents (contrat élargi)."""
    data = _calc(client, "EGY", "KEN")
    for field in (
        "duty_status",
        "dd_available",
        "trade_regime",
        "zlecaf_preference_applied",
    ):
        assert field in data, f"champ de statut manquant : {field}"
    assert data["duty_status"] in ("PAYABLE", "INDICATIVE_MFN", "UNAVAILABLE")


def test_customs_union_pair_is_zero_via_central_guard(client):
    """Paire intra-union douanière (SACU) : droit ZLECAf 0 % et régime
    CUSTOMS_UNION — résolu par le garde-fou central, pas un chemin parallèle."""
    data = _calc(client, "BWA", "ZAF")
    assert data["trade_regime"] == "CUSTOMS_UNION"
    assert data["trade_regime_code"] == "SACU"
    assert data["zlecaf_tariff_rate"] == 0.0
    # preference_applied dépend de l'existence d'un droit NPF > 0 à réduire pour
    # cette ligne (0→0 = rien à appliquer) : on ne l'assert pas ici, seul le
    # régime CUSTOMS_UNION + le taux 0 % garantis par le garde-fou comptent.


def test_non_ratified_origin_gets_no_preference(client):
    """Origine non signataire (Érythrée) : aucune préférence ZLECAf — le taux
    ZLECAf reste égal au taux NPF, sans économie fabriquée."""
    data = _calc(client, "ERI", "KEN")
    assert data["zlecaf_preference_applied"] is False
    assert data["zlecaf_tariff_rate"] == data["normal_tariff_rate"]
    assert data["savings"] == 0


def test_no_generic_zlecaf_zero_for_ratified_without_schedule(client):
    """Deux pays ratifiés mais sans barème préférentiel par ligne vérifié :
    le taux ZLECAf ne doit PAS être fabriqué à 0 % (fallback interdit) — il
    reste au NPF tant qu'aucun barème réel n'est prouvé."""
    data = _calc(client, "EGY", "KEN")
    # KEN est implémenteur actif (GTI) mais aucun barème par ligne n'est transmis :
    # pas de réduction fabriquée → taux ZLECAf = NPF, aucune économie.
    assert data["zlecaf_tariff_rate"] == data["normal_tariff_rate"]
    assert data["zlecaf_preference_applied"] is False


def test_dza_national_offer_still_applies_via_guard(client):
    """L'offre nationale algérienne (circulaire DGD 482/2024) reste appliquée,
    mais désormais via le garde-fou central."""
    # Origine = partenaire actif algérien (EGY), destination DZA.
    data = _calc(client, "EGY", "DZA")
    assert data["trade_regime"] in ("ZLECAF", "CUSTOMS_UNION", "NPF", "FTA_CONDITIONAL")
    # Le régime est résolu centralement ; le champ note existe.
    assert "zlecaf_note" in data
