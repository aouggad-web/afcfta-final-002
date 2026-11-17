"""
Module Logistique : aucune valeur générée n'est servie comme une mesure.

Une valeur de performance portuaire servie par /api/logistics doit venir d'un
bloc qui déclare sa nature (« mesure » ou « estimation ») et sa source. Les
valeurs tirées au hasard (backend/enrich_ports_professional.py), dérivées par
règle (scripts/update_all_ports_precise.py) ou sans source ont été retirées ;
ce test échoue si l'une d'elles revient. Les courriels fabriqués sur le modèle
<iata>.<service>@airport.aero et les séries de fret déduites de la dernière
année par coefficients fixes ne doivent pas revenir non plus.
"""

import json
import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

NATURES = {"mesure", "estimation"}
PERF_PORT = {
    "avg_waiting_time_hours", "avg_port_stay_hours", "berth_productivity",
    "efficiency_grade", "quay_occupancy_rate_2024_pct", "quay_occupancy_rate_2025_pct",
    "median_time_in_port_hours", "average_waiting_time_hours",
    "berth_productivity_moves_per_hour", "performance_grade", "productivity_moves_per_hour",
    "avg_time_in_port_hours", "avg_wait_time", "container_dwell_time_days",
    "vessel_turnaround_hours", "customs_clearance_hours",
}


def _publiee(v):
    return v is not None and str(v).strip() not in ("", "NA")


@pytest.fixture(scope="module")
def client():
    from routes.logistics import router

    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


@pytest.fixture(scope="module")
def ports(client):
    liste = client.get("/api/logistics/ports").json()["ports"]
    return [client.get(f"/api/logistics/ports/{p['port_id']}").json() for p in liste]


def _blocs(port):
    for cle in ("performance_metrics", "latest_stats", "trs_analysis", "performance_indicators"):
        if isinstance(port.get(cle), dict):
            yield cle, port[cle]
    for cle in ("traffic_evolution", "historical_stats"):
        for i, ligne in enumerate(port.get(cle) or []):
            yield f"{cle}[{i}]", ligne


def test_aucune_performance_portuaire_sans_source_servie_comme_mesure(ports):
    fautes = []
    for port in ports:
        for nom, bloc in _blocs(port):
            valeurs = [k for k in PERF_PORT if _publiee(bloc.get(k))]
            if not valeurs:
                continue
            if bloc.get("nature") not in NATURES or not _publiee(bloc.get("source")):
                fautes.append(f"{port['port_id']}.{nom}: {sorted(valeurs)}")
    assert not fautes, "Performances sans nature ni source :\n" + "\n".join(fautes)


def test_aucune_serie_de_trafic_reconstruite(ports):
    # Signature du générateur : navires = EVP / 800, sans source.
    for port in ports:
        for r in port.get("traffic_evolution") or []:
            assert not (r.get("vessels") == int(r.get("teu", 0) / 800) and "source" not in r), port["port_id"]


def test_aucun_courriel_fabrique_ni_bloc_gabarit_aeroport(client):
    aeroports = client.get("/api/logistics/air/airports").json()["airports"]
    texte = json.dumps(aeroports)
    assert not re.search(r"[a-z]{3}\.[a-z_]+@airport\.aero", texte)
    for a in aeroports:
        assert "airport_authority" not in a and "logistics_network" not in a, a["airport_id"]
        assert all("certifications" not in x for x in a.get("actors", [])), a["airport_id"]


def test_aucune_serie_de_fret_deduite_par_coefficients(client):
    coef = {2020: 0.75, 2021: 0.85, 2022: 0.90, 2023: 0.95}
    for a in client.get("/api/logistics/air/airports").json()["airports"]:
        par_an = {h["year"]: h for h in a.get("historical_stats", [])}
        if not par_an:
            continue
        dernier = par_an[max(par_an)]
        for an, c in coef.items():
            if an in par_an and dernier.get("cargo_throughput_tons"):
                assert par_an[an]["cargo_throughput_tons"] != int(dernier["cargo_throughput_tons"] * c), a["airport_id"]
        fret = dernier.get("cargo_throughput_tons")
        assert dernier.get("cargo_aircraft_movements", 0) * 40 != fret, a["airport_id"]
        assert dernier.get("mail_throughput_tons", 0) * 25 != fret, a["airport_id"]


def test_trafic_conteneurs_source_et_rang_lsci(ports):
    for port in ports:
        stats = port.get("latest_stats") or {}
        if stats.get("container_throughput_teu") is not None:
            assert str(stats.get("source") or "").strip().upper() not in ("", "NA", "N/A", "UNKNOWN")
        assert "world_rank" not in (port.get("lsci") or {})
